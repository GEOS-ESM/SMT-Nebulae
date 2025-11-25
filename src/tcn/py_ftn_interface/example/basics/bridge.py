# file plugin_build.py
import cffi

ffibuilder = cffi.FFI()

with open("data_to_be_transited.h") as f:
    data = "".join([line for line in f if not line.startswith("#")])
    data = data.replace("CFFI_DLLEXPORT", "")
    ffibuilder.embedding_api(data)

ffibuilder.set_source(
    "bridge",
    r"""#include "data_to_be_transited.h" """,
)

ffibuilder.embedding_init_code(
    """
    from bridge import ffi
    from runtime_code import check_function

    @ffi.def_extern()
    def python_function(data:"data_t", value: "int", array: "int*"):
        check_function(data, value, array)

"""
)

ffibuilder.compile(target="bridge.so", verbose=True)
