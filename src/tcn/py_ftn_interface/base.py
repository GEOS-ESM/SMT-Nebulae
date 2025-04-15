import textwrap
from typing import Any, Dict, List

import jinja2

from tcn.py_ftn_interface.argument import Argument


class Function:
    def __init__(
        self,
        name: str,
        inputs: List[Argument],
        inouts: List[Argument],
        outputs: List[Argument],
    ) -> None:
        self.name = name
        self._inputs = inputs
        self._inouts = inouts
        self._outputs = outputs

    @property
    def inputs(self) -> List[Argument]:
        return self._inputs

    @property
    def outputs(self) -> List[Argument]:
        return self._outputs

    @property
    def inouts(self) -> List[Argument]:
        return self._inouts

    @property
    def arguments(self) -> List[Argument]:
        return self._inputs + self._inouts + self._outputs

    @staticmethod
    def c_arguments_for_jinja2(arguments: List[Argument], inputOnly=False) -> List[Dict[str, Any],]:
        """Transform yaml input for the template renderer"""
        return [
            {
                "type": argument.c_type if not inputOnly else argument.c_type_input_only,
                "name": argument.name,
                "dims": argument._dims,
            }
            for argument in arguments
        ]
    
    @staticmethod
    def header_arguments_for_jinja2(arguments: List[Argument], inputOnly=False) -> List[Dict[str, Any],]:
        """Transform yaml input for the template renderer"""
        return [
            {
                "type": argument.c_type if not inputOnly else argument.c_type_input_only,
                "name": argument.name,
                "dims": argument._dims,
            }
            for argument in arguments
        ]
    
    @staticmethod
    def c_prototype_for_jinja2(arguments: List[Argument], inputOnly=False) -> List[Dict[str, Any],]:
        """Transform yaml input for the template renderer"""
        return [
            {
                "type": argument.c_prototype if not inputOnly else argument.c_prototype_input_only,
                "name": argument.name,
                "dims": argument._dims,
            }
            for argument in arguments
        ]

    @staticmethod
    def fortran_arguments_for_jinja2(arguments: List[Argument], containsIntentOut=False) -> List[Dict[str, str]]:
        """Transform yaml input for the template renderer"""
        return [
            {
                "name": argument.name,
                "type": argument.f90_type_definition_inputs if not containsIntentOut else argument.f90_type_definition_with_output,
                "dims_f90_defs": argument.f90_dims_definition,
                "size_f90_per_dims": argument.f90_size_per_dims,
                "f90_dims_and_size": argument.f90_dims_and_size,
            }
            for argument in arguments
        ]

    @staticmethod
    def py_arguments_for_jinja2(arguments: List[Argument]) -> List[Dict[str, str]]:
        """Transform yaml input for the template renderer"""
        return [
            {"type": argument.py_type_hint, "name": argument.name_sanitize}
            for argument in arguments
        ]

    def py_init_code(self) -> List[str]:
        code = []
        for argument in self.arguments:
            if argument.yaml_type == "MPI":
                code.append(
                    textwrap.dedent(
                        f"""\
                        # Comm translate to python
                            comm_py = MPI.Intracomm() # new comm, internal MPI_Comm handle is MPI_COMM_NULL
                            comm_ptr = MPI._addressof(comm_py)  # internal MPI_Comm handle
                            comm_ptr = ffi.cast('{{_mpi_comm_t}}*', comm_ptr)  # make it a CFFI pointer
                            comm_ptr[0] = {argument.name}  # assign comm_c to comm_py's MPI_Comm handle
                            {argument.name} = comm_py # Override the symbol name to make life easier for code gen"""  # noqa
                    )
                )
        return code

    def c_init_code(self) -> List[str]:
        prolog_code = []
        for argument in self.arguments:
            if argument.yaml_type == "MPI":
                prolog_code.append(
                    f"MPI_Comm {argument.name}_c = MPI_Comm_f2c({argument.name});"
                )
        return prolog_code

    def arguments_name(self) -> List[str]:
        return [argument.name_sanitize for argument in self.arguments]

    @staticmethod
    def _fortran_type_declaration(def_type: str) -> str:
        if def_type == "int":
            return "integer(kind=c_int), value"
        elif def_type == "float":
            return "real(kind=c_float), value"
        elif def_type == "double":
            return "real(kind=c_double), value"
        elif def_type == "array_int":
            return "integer(kind=c_int), dimension(*)"
        elif def_type == "array_float":
            return "real(kind=c_float), dimension(*)"
        elif def_type == "array_double":
            return "real(kind=c_double), dimension(*)"
        elif def_type == "MPI":
            return "integer(kind=c_int), value"
        else:
            raise RuntimeError(f"ERROR_DEF_TYPE_TO_FORTRAN: {def_type}")


class InterfaceConfig:
    def __init__(
        self,
        directory_path: str,
        prefix: str,
        function_defines: List[Function],
        template_env: jinja2.Environment,
    ) -> None:
        self._directory_path = directory_path
        self._prefix = prefix
        self._hook_obj = prefix
        self._hook_class = prefix.upper()
        self._functions = function_defines
        self._template_env = template_env

class Derived_Type:
    def __init__(
        self,
        name: str,
        variable_list: List[Argument],
    ) -> None:
        self.name = name
        self._variable_list = variable_list