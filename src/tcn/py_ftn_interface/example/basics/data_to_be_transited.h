#pragma once
#include <stdbool.h>

typedef struct
{
    float x;
    int y;
    bool b;
    // Magic number, see Fortran
    int i_am_123456789;
} data_t;

extern void python_function(data_t *, int value, int *array);
