#ifndef PROCSET_HEADER_H_
#define PROCSET_HEADER_H_


#define PY_SSIZE_T_CLEAN
#include <Python.h>

typedef uint32_t pset_boundary_t;
pset_boundary_t MAX_BOUND_VALUE = UINT32_MAX;

// Definition of the ProcSet struct
typedef struct {
    //Python object boilerplate
    PyObject_HEAD

    //Boundaries of the ProcSet paired two by two as half-opened intervals
    pset_boundary_t *_boundaries;   

    //Number of boundaries, (2x nbr of intervals)
    Py_ssize_t nb_boundary;
} ProcSetObject;


#endif
