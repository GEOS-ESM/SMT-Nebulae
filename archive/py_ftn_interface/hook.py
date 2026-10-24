import subprocess
from typing import List

import jinja2

from tcn.py_ftn_interface.base import Function, InterfaceConfig
from tcn.py_ftn_interface.validation import Validation


class Hook(InterfaceConfig):
    def __init__(
        self,
        directory_path: str,
        prefix: str,
        function_defines: List[Function],
        validations: List[Validation],
        template_env: jinja2.Environment,
    ) -> None:
        super().__init__(
            directory_path=directory_path,
            prefix=prefix,
            function_defines=function_defines,
            template_env=template_env,
        )
        self._validations = validations

    def generate_blank(self):
        functions = []
        for function in self._functions:
            functions.append(
                {
                    "name": function.name,
                    "inputs": Function.py_arguments_for_jinja2(function.inputs),
                    "inouts": Function.py_arguments_for_jinja2(function.inouts),
                    "outputs": Function.py_arguments_for_jinja2(function.outputs),
                }
            )

        validations = []
        for validation in self._validations:
            validations.append(validation.for_jinja_python())

        template = self._template_env.get_template("hook.py.jinja2")
        code = template.render(
            prefix=self._prefix,
            functions=functions,
            validations=validations,
            hook_class=self._hook_class,
            hook_obj=self._hook_obj,
        )

        py_source_filepath = f"{self._directory_path}/{self._prefix}_hook.py"
        with open(py_source_filepath, "w+") as f:
            f.write(code)

        # Format
        subprocess.call(["black", "-q", py_source_filepath])

        return self

    def generate_obj(self):
        raise NotImplementedError("Not implemented")
