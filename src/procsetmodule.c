#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"

// define the type of the boundaries of the set
typedef uint32_t pset_boundary_t;

// define of the procset type
typedef struct {
    PyObject_HEAD
    pset_boundary_t *_boundaries;
    int nb_boundary;
} ProcSetObject;

int
create_pset_from_string(ProcSetObject *self, char *pset_string)
{
    pset_boundary_t *tmp;

    int lenght = strlen(pset_string);

    tmp = (pset_boundary_t *) malloc(lenght * sizeof(pset_boundary_t));
    if (tmp == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate memory to store the boundaries");
        return -1;
    }

    for (int index = 0; index < lenght; index++) {
        if (isdigit(pset_string[index])) {
            tmp[index] = (pset_boundary_t) pset_string[index] - '0';
        } else {
            free(tmp);
            PyErr_SetString(PyExc_ValueError, "Input boundaries contains non-digits values");
            return -1;
        }
    }
  
    if (lenght%2 != 0) {
        free(tmp);
        PyErr_SetString(PyExc_ValueError, "The number of boundaries in input must be even");
        return -1;
    }

    free(self->_boundaries);
    self->_boundaries = tmp;
    self->nb_boundary = lenght;

    return 0;
}


static void
ProcSet_dealloc(ProcSetObject *self)
{
    free(self->_boundaries);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
ProcSet_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    ProcSetObject *self;
    self = (ProcSetObject *) type->tp_alloc(type, 0);

    if (self != NULL) {
        self->nb_boundary = 0;
    }

    return (PyObject *) self;
}

static int
ProcSet_init(ProcSetObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"pset", NULL};
    char *pset_string = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", kwlist,
                                    &pset_string))
        return -1;

    if (pset_string) {

        create_pset_from_string(self, pset_string);


        // free(pset_string); // XXX : not sure if it's usefull tbh
    }

    return 0;

}

static PyObject *
ProcSet_show(ProcSetObject *self, PyObject *Py_UNUSED(ignored)) {
    printf("ProcSet(");

        for (int index = 0; index < self->nb_boundary-2; index += 2) {
            printf("%d-%d ", self->_boundaries[index], self->_boundaries[index+1]);
        }
        // show the last element
        if (self->nb_boundary > 0) 
            printf("%d-%d", self->_boundaries[self->nb_boundary-2], self->_boundaries[self->nb_boundary-1]);

        printf(")\n");

        Py_RETURN_NONE;
}

static PyMethodDef ProcSet_methods[] = {
    {"show", (PyCFunction) ProcSet_show, METH_NOARGS, "Show the boundaries of the ProcSet"},
    {NULL}
};

static PyTypeObject ProcSetType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "ProcSet.procset",
    .tp_doc = "Procset object",
    .tp_basicsize = sizeof(ProcSetObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = ProcSet_new,
    .tp_init = (initproc) ProcSet_init,
    .tp_dealloc = (destructor) ProcSet_dealloc,
    .tp_methods = ProcSet_methods,
};

static PyModuleDef procsetmodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "procset",
    .m_doc = "ProcSet module to manipulate set of processor",
    .m_size = -1,
};

PyMODINIT_FUNC
PyInit_procset(void)
{
    PyObject *m;
    if (PyType_Ready(&ProcSetType) < 0) return NULL;

    m = PyModule_Create(&procsetmodule);
    if (m == NULL) return NULL;

    Py_INCREF(&ProcSetType);
    if (PyModule_AddObject(m, "ProcSet", (PyObject *) &ProcSetType) < 0) {
        Py_DECREF(&ProcSetType);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
