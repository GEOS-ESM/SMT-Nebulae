# Benchmarker script

Entry point: `bencharmker.py`

All variables between the

```python
# ---- GLOBAL MESS ---- #
```

comments are to be changed to match local URL and bench needs.

This is hardcoded to bench D_SW.

The `xarray_to_quantity` functions only exists because we use Serialized data. In a world where we bench after capturing data, none of the data and/or name manipulation in the NetCDFs is needed.
