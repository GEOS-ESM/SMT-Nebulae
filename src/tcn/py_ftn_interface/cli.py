import os
import shutil
import site
import sys
from typing import List

import click
import jinja2
import yaml

from tcn.py_ftn_interface.argument import get_argument_yaml_loader
from tcn.py_ftn_interface.base import Function, InterfaceConfig
from tcn.py_ftn_interface.bridge import Bridge

from argument import Argument

###############
# TODO:
# - Fill Object version of the interface (actually used in GEOS)
# - Use converter (CPU/GPU & Py/Fortran)
# - Add fortran reference validator
#   - Go to python -> deep copy inputs/inouts
#   - Go back to fortran -> execute run
#   - Down to py -> get fortran inouts/ouputs, execute on deep copied data, compare
###############


def _find_templates_dir() -> str:
    # pip install smtn
    candidate = f"{sys.prefix}/smtn/src/py_ftn_interface/templates"
    if os.path.isdir(candidate):
        return candidate
    # pip install --user smtn
    candidate = f"{site.USER_BASE}/smtn/src/py_ftn_interface/templates"
    if os.path.isdir(candidate):
        return candidate
    # pip install -e smtn
    candidate = os.path.join(os.path.dirname(__file__), "./templates")
    if os.path.isdir(candidate):
        return candidate
    raise RuntimeError("Cannot find template directory")


def _find_templates(name: str) -> str:
    directory = _find_templates_dir()
    # pip install smtn
    candidate = f"{directory}/{name}"
    if os.path.isfile(candidate):
        return candidate
    raise RuntimeError(f"Cannot find template: {name} im {directory}")


class Build(InterfaceConfig):
    def __init__(
        self,
        directory_path: str,
        prefix: str,
        function_defines: List[Function],
        template_env: jinja2.Environment,
    ) -> None:
        super().__init__(
            directory_path=directory_path,
            prefix=prefix,
            function_defines=function_defines,
            template_env=template_env,
        )

    def generate_cmake(self):
        template = self._template_env.get_template("cmake.jinja2")
        code = template.render(
            prefix=self._prefix,
            interface_directory=self._directory_path,
        )

        py_source_filepath = f"{self._directory_path}/CMakeLists_partial.txt"
        with open(py_source_filepath, "w+") as f:
            f.write(code)

        return self


@click.command()
@click.argument("definition_json_filepath")
@click.option(
    "--directory",
    help="Directory name to drop interface files in",
)
@click.option("--hook", default="blank")
@click.option("--build", default="cmake")
def cli(definition_json_filepath: str, directory: str, hook: str, build: str):
    with open(definition_json_filepath) as f:
        defs = yaml.load(f, Loader=get_argument_yaml_loader())
    if "type" not in defs.keys() and defs["type"] == "py_ftn_interface":
        raise RuntimeError("Bad definition")

    # Make directory
    os.makedirs(directory, exist_ok=True)

    # Make bridge - this our "translation-only" layer
    # that move data "as-is" between fortran and python (through c)
    prefix = defs["name"]
    functions = []
    # for function in defs["bridge"]:
    for function in defs["functions"]:
        # args = function["arguments"]
        args = defs["functions"][function]
        if args == "None":
            args = None
        else:
            if "inputs" in args.keys():
                inputs = []
                for key, value in args["inputs"].items():
                    # print(key, value)
                    inputs.append(Argument(key, value))
            if "inouts" in args.keys():
                inouts = []
                for key, value in args["inouts"].items():
                    # print(key, value)
                    inouts.append(Argument(key, value))
            if "outputs" in args.keys():
                outputs = []
                for key, value in args["outputs"].items():
                    # print(key, value)
                    outputs.append(Argument(key, value))
        functions.append(
            Function(
                # function["name"],
                function,
                (inputs if "inputs" in args.keys() else []) if args else [],
                (inouts if "inouts" in args.keys() else []) if args else [],
                (outputs if "outputs" in args.keys() else []) if args else [],
            )
        )

    template_loader = jinja2.FileSystemLoader(searchpath=_find_templates_dir())
    template_env = jinja2.Environment(loader=template_loader)

    # Bridge.make_from_yaml(
    #     directory, template_env, defs
    # ).generate_c().generate_fortran().generate_python().generate_hook(hook)

    bridge_construct = Bridge.make_from_yaml(
        directory, template_env, defs
    )
    
    bridge_construct.generate_fortran()
    bridge_construct.generate_c()

    # The build script is not fully functional - it is meant as a hint
    # b = Build(
    #     directory,
    #     prefix,
    #     functions,
    #     template_env,
    # )
    # if build == "cmake":
    #     b.generate_cmake()
    # else:
    #     raise NotImplementedError(f"No build '{build}'")

    # Copy support files
    # shutil.copy(_find_templates("cuda_profiler.py"), directory)
    # shutil.copy(_find_templates("data_conversion.py"), directory)
    # open(directory + "/__init__.py", "a").close()


if __name__ == "__main__":
    cli()
