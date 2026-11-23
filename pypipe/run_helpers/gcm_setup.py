"""Drive the installed interactive GEOS gcm_setup without input templates."""

import os
import re
import shutil
import tempfile
from pathlib import Path

import pexpect

_ESCAPE = r"\x1b(?:\[[0-?]*[ -/]*[@-~]|[()][0-2A-Z])"
_ANSI = rf"(?:{_ESCAPE})*"


def _prompt(text):
    # Colors may start or end anywhere in a prompt, even inside a phrase.
    return re.compile(r"(?m)^" + _ANSI + _ANSI.join(map(re.escape, text)))


_PROMPTS = {
    "expid": "Enter the Experiment ID:",
    "description": "Enter a 1-line Experiment Description:",
    "clone": "Do you wish to CLONE an old experiment?",
    "atmos_horizontal": "Enter the Atmospheric Horizontal Resolution code:",
    "atmos_vertical": "Enter the Atmospheric Model Vertical Resolution:",
    "microphysics": "Enter Choice for Atmospheric Model Microphysics:",
    "oserver": "Do you wish to IOSERVER?",
    "processor": "Enter the Processor Type you wish to run on:",
    "hydro": "Use Hydrostatic Atmosphere?",
    "coupled": "Do you wish to run the COUPLED Ocean/Sea-Ice Model?",
    "ocean_model": "Choose an Ocean Model:",
    "ocean_latlon": "Enter the Ocean Lat/Lon Horizontal Resolution:",
    "ocean_code": "Enter the Ocean Horizontal Resolution code:",
    "seaice": "Choose a Seaice Model:",
    "ocean_vertical": "Enter the Ocean Model Vertical Resolution:",
    "data_ocean": "Enter the Data_Ocean Horizontal Resolution code:",
    "data_atmos": "Do you wish to run Data Atmosphere?",
    "land_bcs": "Enter the choice of Land Surface Boundary Conditions using:",
    "land_model": "Enter the choice of  Land Surface Model using:",
    "aerosols": "Do you wish to run GOCART with Actual or Climatological Aerosols?",
    "emissions": "Enter the GOCART Emission Files to use:",
    "heartbeat": "Enter HEARTBEAT_DT to use",
    "history": "Enter the filename of the HISTORY template to use",
    "home": "Enter Desired Location for the HOME Directory (to contain scripts and RC files)",
    "experiment": "Enter Desired Location for the EXPERIMENT Directory (to contain model output and restart files)",
    "build": "Enter Location for Build directory containing:",
    "group": "Enter your GROUP ID for Current EXP:",
}
_PATTERNS = [_prompt(text) for text in _PROMPTS.values()]


def _boolean(value):
    return "YES" if value else "NO"


def _set_hydrostatic(exp_dir, enabled):
    """Set the FV3 namelist when gcm_setup does not offer a hydro prompt."""
    path = Path(exp_dir) / "fvcore_layout.rc"
    content = path.read_text()
    pattern = r"(?im)^([ \t]*hydrostatic[ \t]*=[ \t]*)\.(?:true|false)\."
    value = ".true." if enabled else ".false."
    if re.search(pattern, content):
        content = re.sub(pattern, lambda match: match.group(1) + value, content)
    else:
        content, count = re.subn(
            r"(?im)^([ \t]*&fv_core_nml[ \t]*)$",
            lambda match: match.group(1) + f"\n hydrostatic = {value}",
            content,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Cannot find &fv_core_nml in {path}")
    path.write_text(content)


def prepare_gcm_setup(runner):
    """Construct and validate responses before an existing experiment is removed."""
    args = runner.args
    ocean = str(args.ocean).upper()
    coupled = ocean in {"MOM5", "MOM6", "MIT"}
    if not coupled and ocean not in {"O1", "O2", "O3", "CS"}:
        raise ValueError(f"Unsupported ocean: {args.ocean}")
    if args.data_atmo and not coupled:
        raise ValueError("Data atmosphere requires a coupled ocean model.")

    exp_dir = os.path.abspath(runner.exp_dir)
    geos_dir = os.path.abspath(args.geos_dir)
    exp_name = str(runner.exp_name)
    # gcm_setup expands paths unquoted and scans components until it finds EXPID.
    # Reject paths it cannot safely parse, including ambiguous repeated EXPIDs.
    if (
        not exp_name
        or exp_name in {".", ".."}
        or Path(exp_dir).name != exp_name
        or exp_name in Path(exp_dir).parts[:-1]
        or any(re.search(r"[\s*?\[\]{}'\"\\`$!;|&<>]", p) for p in (exp_dir, geos_dir))
    ):
        raise ValueError(
            "Experiment and GEOS paths must be unambiguous and safe for tcsh."
        )

    microphysics = ""
    if args.microphysics is not None:
        microphysics = {
            "GFDL1M": "GFDL_1M",
            "BACM1M": "BACM_1M",
            "MGB22M": "MGB2_2M",
        }.get(str(args.microphysics).upper(), str(args.microphysics))
    responses = {
        "expid": exp_name,
        "description": exp_name,
        "clone": "NO",
        "atmos_horizontal": f"c{str(args.horz).removeprefix('c')}",
        "atmos_vertical": str(args.vert),
        "microphysics": microphysics,
        "oserver": _boolean(args.oserver) if args.oserver is not None else "",
        "processor": str(args.processor) if args.processor is not None else "",
        "hydro": _boolean(args.hydro) if args.hydro is not None else "",
        "coupled": _boolean(coupled),
        "ocean_model": ocean,
        "ocean_latlon": "",  # MOM5: use the script's 360 x 200 default.
        "ocean_code": "",  # MOM6 c180: use the script's o1440 default.
        "seaice": "CICE6" if ocean == "MOM6" else "CICE4",
        "ocean_vertical": "",
        "data_ocean": ocean.lower(),
        "data_atmos": _boolean(args.data_atmo),
        "land_bcs": str(args.land_bcs),
        "land_model": str(args.land_surf),
        "aerosols": str(args.aerosols) if args.aerosols is not None else "",
        "emissions": "",
        "heartbeat": str(args.heartbeat) if args.heartbeat is not None else "",
        "history": "",
        "home": exp_dir,
        "experiment": exp_dir,
        "build": geos_dir,
        "group": str(args.account) if args.account is not None else "",
    }
    if any(
        "\n" in value or "\r" in value or "\x00" in value
        for value in responses.values()
    ):
        raise ValueError("gcm_setup responses must each fit on a single line.")
    return responses


class _Transcript:
    """Keep enough recent output for useful diagnostics without unbounded growth."""

    def __init__(self):
        self.text = ""

    def write(self, text):
        self.text = (self.text + text)[-12000:]

    def flush(self):
        pass


def run_gcm_setup(runner, prompt_timeout=30, completion_timeout=180):
    responses = prepare_gcm_setup(runner)
    script = os.path.abspath(os.path.join(runner.args.geos_dir, "bin", "gcm_setup"))
    cwd = os.path.dirname(script)
    required = {
        "expid",
        "description",
        "clone",
        "atmos_horizontal",
        "atmos_vertical",
        "coupled",
        "history",
        "home",
        "experiment",
        "build",
        "group",
    }
    if responses["coupled"] == "YES":
        required.add("ocean_model")
    else:
        required.add("data_ocean")
    if runner.args.data_atmo:
        required.add("data_atmos")
    else:
        required.update({"land_bcs", "land_model", "aerosols"})
    if runner.args.heartbeat is not None:
        required.add("heartbeat")

    transcript = _Transcript()
    seen = set()
    last_prompt = "(none)"
    child = None
    # Isolate all HOME writes instead of temporarily modifying real dotfiles.
    # Preserve the user's group/color defaults in private copies when present.
    with tempfile.TemporaryDirectory(prefix="pypipe-gcm-home-") as home:
        original_home = runner.env.get("HOME")
        if original_home:
            for name in (".GROUProot", ".GCMSETUP"):
                source = Path(original_home) / name
                if source.is_file():
                    shutil.copyfile(source, Path(home) / name)
        env = dict(runner.env, HOME=home)
        argv = ["--link"] if getattr(runner.args, "link", True) else []
        try:
            print(f"[GEOS PYTHON WRAPPER] gcm_setup arguments: {argv!r}", flush=True)
            print(
                "[GEOS PYTHON WRAPPER] gcm_setup responses (blank uses default):",
                flush=True,
            )
            for key, value in responses.items():
                print(f"  {key}: {value!r}", flush=True)
            child = pexpect.spawn(
                script,
                argv,
                cwd=cwd,
                env=env,
                encoding="utf-8",
                codec_errors="replace",
                echo=False,
                timeout=prompt_timeout,
            )
            child.logfile_read = transcript
            while True:
                timeout = completion_timeout if "group" in seen else prompt_timeout
                index = child.expect(
                    [*_PATTERNS, pexpect.EOF, pexpect.TIMEOUT], timeout=timeout
                )
                if index == len(_PATTERNS):
                    child.close()
                    missing = required - seen
                    if (
                        child.exitstatus != 0
                        or child.signalstatus is not None
                        or missing
                    ):
                        raise RuntimeError(
                            f"unexpected EOF (exit={child.exitstatus}, signal={child.signalstatus}, "
                            f"missing prompts={sorted(missing)})"
                        )
                    break
                if index == len(_PATTERNS) + 1:
                    raise RuntimeError(
                        "timed out waiting for a known prompt or completion"
                    )
                key = list(_PROMPTS)[index]
                if key in seen:
                    raise RuntimeError(
                        f"repeated prompt {key!r}; the previous answer was rejected"
                    )
                seen.add(key)
                last_prompt = key
                child.sendline(responses[key])
            if "hydro" not in seen and runner.args.hydro is not None:
                _set_hydrostatic(runner.exp_dir, runner.args.hydro)
        except (OSError, pexpect.ExceptionPexpect, RuntimeError) as exc:
            output = re.sub(_ESCAPE, "", transcript.text).strip()
            raise RuntimeError(
                f"[GEOS PYTHON WRAPPER] gcm_setup failed: {exc}\n"
                f"script: {script}\ncwd: {cwd}\n"
                f"last prompt: {last_prompt}\n"
                f"recent output:\n{output}"
            ) from exc
        finally:
            if child is not None and not child.closed:
                child.close(force=True)
