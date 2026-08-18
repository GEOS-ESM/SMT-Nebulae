import os
import shutil
import subprocess
import sys

from click.testing import CliRunner

from tcn.py_ftn_interface.cli import cli


def test_fortran_python_interface():
    # Setup
    test_dir = os.path.join(os.path.dirname(__file__), "py_ftn_test/")
    definition_yaml = os.path.join(test_dir, "data/test_python_fortran_interface.yaml")
    cmakelist = os.path.join(test_dir, "data/CMakeLists.txt")
    interface_directory = os.path.join(test_dir, "interface")
    build_directory = os.path.join(test_dir, "build")
    install_directory = os.path.join(test_dir, "install")

    # Generate the interface
    assert not os.path.exists(interface_directory)
    result = CliRunner().invoke(
        cli, [definition_yaml, "--directory", interface_directory]
    )
    assert result.exit_code == 0
    assert os.path.isdir(interface_directory)

    # Build
    shutil.rmtree(build_directory, ignore_errors=True)
    os.mkdir(build_directory)
    shutil.copy(cmakelist, build_directory)
    subprocess.run(
        [
            "cmake",
            "--log-level=VERBOSE",
            "-DCMAKE_INSTALL_PREFIX='../install'",
            f"-DPython3_EXECUTABLE={sys.executable}",
        ],
        cwd=build_directory,
        check=True,
    )
    subprocess.run(
        [
            "make",
        ],
        cwd=build_directory,
        check=True,
    )
    assert os.path.isfile(build_directory + "/test")

    # Add user code in Hook
    # This code will change the out array to 11, and that value will be checked
    # by the fortran right after
    hook_file = os.path.join(interface_directory, "py_ftn_test_hook.py")
    hook_code = ""
    with open(hook_file, "r") as f:
        hook_code = f.read()
    hook_code = hook_code.replace(
        'print("My code for py_ftn_test_check_data goes here.")',
        "out = self._f2py.fortran_to_python(out_array, [2, 2]);out[:, :] = 11;self._f2py.python_to_fortran(out, out_array);inout = self._f2py.fortran_to_python(inout_array, [2, 2]);inout[:, :] = 11;self._f2py.python_to_fortran(inout, inout_array)",  # noqa
    )
    with open(hook_file, "w") as f:
        f.write(hook_code)

    # Run the fortran program
    subprocess.run(
        [
            "./test",
        ],
        env=dict(os.environ, PYTHONPATH=os.path.abspath(interface_directory)),
        cwd=build_directory,
        check=True,
    )

    # Clean up
    shutil.rmtree(interface_directory)
    shutil.rmtree(build_directory)
    shutil.rmtree(install_directory)


if __name__ == "__main__":
    test_fortran_python_interface()
