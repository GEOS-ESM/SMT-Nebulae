from typing import Any, Dict

from tcn.py_ftn_interface.base import Function, InterfaceConfig


class Validation(InterfaceConfig):
    def __init__(
        self, candidate: Function, reference_call: str, reference_mod: str
    ) -> None:
        self._candidate = candidate
        self._reference_call = reference_call
        self._reference_mod = reference_mod

    def for_jinja_fortran(self) -> Dict[str, Any]:
        return {
            "reference_call": self._reference_call,
            "reference_mod": self._reference_mod,
            "candidate": self._candidate.name,
            "inputs": Function.fortran_arguments_for_jinja2(self._candidate.inputs),
            "inouts": Function.fortran_arguments_for_jinja2(self._candidate.inouts),
            "outputs": Function.fortran_arguments_for_jinja2(self._candidate.outputs),
        }

    def for_jinja_c(self) -> Dict[str, Any]:
        return {
            "reference_call": self._reference_call,
            "reference_mod": self._reference_mod,
            "candidate": self._candidate.name,
            "inputs": Function.c_arguments_for_jinja2(self._candidate.inputs),
            "inouts": Function.c_arguments_for_jinja2(self._candidate.inouts),
            "outputs": Function.c_arguments_for_jinja2(self._candidate.outputs),
        }

    def for_jinja_python(self) -> Dict[str, Any]:
        return {
            "reference_call": self._reference_call,
            "reference_mod": self._reference_mod,
            "candidate": self._candidate.name,
            "inputs": Function.py_arguments_for_jinja2(self._candidate.inputs),
            "inouts": Function.py_arguments_for_jinja2(self._candidate.inouts),
            "outputs": Function.py_arguments_for_jinja2(self._candidate.outputs),
            "inouts_c": Function.c_arguments_for_jinja2(self._candidate.inouts),
            "outputs_c": Function.c_arguments_for_jinja2(self._candidate.outputs),
        }
