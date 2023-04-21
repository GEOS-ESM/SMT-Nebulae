import subprocess
from typing import Optional, List
import os
import sys
import stat

def print_subprocess(command: str):
    r = subprocess.check_output("id", shell=True)
    print(r)

def run_subprocess(command: str, stdout=None, stderr=None) -> str:
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
        if result.returncode != 0:
            raise RuntimeError(f"Subprocess with command {command}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Subprocess with command {command} failed, throwing error \n{e}"
        )
    return result.stdout.decode(sys.stdout.encoding)


def execute_shell_script(name: str) -> str:
    print(f"> > > Executing {name}")
    st = os.stat(name)
    os.chmod(name, st.st_mode | stat.S_IEXEC)
    return run_subprocess(f"./{name}")


def shell_script(
    name: str,
    shell_commands: List[str],
    modules: Optional[List[str]] = None,
    env_to_source: Optional[List[str]] = None,
    execute=True,
    temporary=False,
) -> Optional[str]:
    script = "#!/bin/sh\n"
    if modules:
        for m in modules:
            script += f"module load {m}\n"
        script += "\n"
    for env in env_to_source or []:
        script += f"source {env}\n"
        script += "\n"
    for c in shell_commands:
        script += f"{c}\n"
    script += "\n"

    script_name = f"{name}.sh"
    with open(script_name, "w") as f:
        f.write(script)

    if execute:
        result = execute_shell_script(script_name)
        if temporary:
            os.remove(script_name)
        return result
