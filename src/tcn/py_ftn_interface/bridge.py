import subprocess
from typing import Any, Dict, List

import clang_format as cf
import jinja2

from tcn.py_ftn_interface.base import Function, InterfaceConfig
from tcn.py_ftn_interface.hook import Hook
from tcn.py_ftn_interface.validation import Validation
from tcn.py_ftn_interface.argument import Argument

import fprettify

class Bridge(InterfaceConfig):
    def __init__(
        self,
        directory_path: str,
        prefix: str,
        function_defines: List[Function],
        template_env: jinja2.Environment,
        validations: List[Validation] = [],
    ) -> None:
        super().__init__(
            directory_path=directory_path,
            prefix=prefix,
            function_defines=function_defines,
            template_env=template_env,
        )
        self._validations = validations

    @classmethod
    def make_from_yaml(
        cls,
        directory: str,
        template_env: jinja2.Environment,
        configuration: Dict[str, Any],
    ):
        prefix = configuration["name"]
        functions = []
        validations = []
        # for function in configuration["bridge"]:
        for function_name in configuration["functions"]:
            # args = function["arguments"]
            args = configuration["functions"][function_name]
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
            functions.append(Function(
                # function["name"],
                    function_name,
                    (inputs if "inputs" in args.keys() else []) if args else [],
                    (inouts if "inouts" in args.keys() else []) if args else [],
                    (outputs if "outputs" in args.keys() else []) if args else [],
                )
            )

            # Check for validation
            # # if "validation" in function.keys():
            # if "validation" in configuration["functions"][function].keys():
            #     if not args or (args["inouts"] == [] and args["outputs"] == []):
            #         raise RuntimeError(f"Can't validate {candidate.name}: no outputs.")
            #     validations.append(
            #         Validation(
            #             candidate,
            #             function["validation"]["reference"]["call"],
            #             function["validation"]["reference"]["mod"],
            #         )
            #     )

        return cls(directory, prefix, functions, template_env, validations)

    def generate_c(self) -> "Bridge":
        # Transform data for Jinja2 template
        functions = []
        for function in self._functions:
            functions.append(
                {
                    "name": function.name,
                    "inputs": Function.c_arguments_for_jinja2(function.inputs),
                    "inouts": Function.c_arguments_for_jinja2(function.inouts),
                    "outputs": Function.c_arguments_for_jinja2(function.outputs),
                    "arguments": Function.c_arguments_for_jinja2(function.arguments),
                    "arguments_init": function.c_init_code(),
                }
            )

        validations = []
        for validation in self._validations:
            validations.append(validation.for_jinja_c())

        # Source
        template = self._template_env.get_template("interface.c.jinja2")
        code = template.render(
            prefix=self._prefix,
            functions=functions,
            validations=validations,
        )

        c_source_filepath = f"{self._directory_path}/{self._prefix}_interface.c"
        with open(c_source_filepath, "w+") as f:
            f.write(code)

        subprocess.call([cf._get_executable("clang-format"), "-i", c_source_filepath])

        return self

    def generate_fortran(self) -> "Bridge":
        # Transform data for Jinja2 template
        functions = []
        for function in self._functions:
            functions.append(
                {
                    "name": function.name,
                    "inputs": Function.fortran_arguments_for_jinja2(function.inputs),
                    "inouts": Function.fortran_arguments_for_jinja2(function.inouts, containsIntentOut=True),
                    "outputs": Function.fortran_arguments_for_jinja2(function.outputs, containsIntentOut=True),
                }
            )

        validations = []
        for validation in self._validations:
            validations.append(validation.for_jinja_fortran())

        template = self._template_env.get_template("interface.f90.jinja2")
        code = template.render(
            prefix=self._prefix,
            functions=functions,
            validations=validations,
        )

        ftn_source_filepath = f"{self._directory_path}/{self._prefix}_interface.f90"
        with open(ftn_source_filepath, "w+") as f:
            f.write(code)

        # Format
        # Note: pdoc dies when this is imported at file level. -_o_-
        # import fprettify  # noqa

        fprettify.reformat_inplace(ftn_source_filepath)

        return self

    def generate_python(self) -> "Bridge":
        # Transform data for Jinja2 template
        functions = []
        for function in self._functions:
            functions.append(
                {
                    "name": function.name,
                    "inputs": Function.py_arguments_for_jinja2(function.inputs),
                    "inouts": Function.py_arguments_for_jinja2(function.inouts),
                    "outputs": Function.py_arguments_for_jinja2(function.outputs),
                    "init_code": function.py_init_code(),
                    "all_arguments_name": function.arguments_name(),
                    "c_arguments": Function.c_arguments_for_jinja2(function.arguments),
                }
            )

        validations = []
        for validation in self._validations:
            validations.append(validation.for_jinja_python())

        template = self._template_env.get_template("interface.py.jinja2")
        code = template.render(
            prefix=self._prefix,
            functions=functions,
            validations=validations,
            hook_obj=self._hook_obj,
        )

        py_source_filepath = f"{self._directory_path}/{self._prefix}_interface.py"
        with open(py_source_filepath, "w+") as f:
            f.write(code)

        # Format
        subprocess.call(["black", "-q", py_source_filepath])

        return self

    def generate_hook(self, hook: str):
        # Make hook - this our springboard to the larger python code
        h = Hook(
            self._directory_path,
            self._prefix,
            self._functions,
            self._validations,
            self._template_env,
        )
        if hook == "blank":
            h.generate_blank()
        else:
            raise NotImplementedError(f"No hook '{hook}'")
