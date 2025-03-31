import subprocess
import os


def get_git_log_oneline() -> str:
    return (
        subprocess.check_output(["git", "log", "-1", "--oneline", "--decorate"])
        .decode("ascii")
        .strip()
    )


packages = ["ndsl", "gt4py", "dace", "pyFV3", "pyMoist"]

for pkg in packages:
    imported_pkg = __import__(pkg)

    if imported_pkg is not None:
        os.chdir(imported_pkg.__path__[0])
        local = os.getcwd()
        git = get_git_log_oneline()
        print(f"[{pkg}]: {git} (from local {local})")
    else:
        print(f"[{pkg}]: couldn't import py package")
