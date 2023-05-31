#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdbool.h>
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
            pset_boundary_t value = pset_string[index] - '0';
            tmp[index] = index%2 == 0 ? value : value+1;
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
ProcSet_show(ProcSetObject *self, PyObject *Py_UNUSED(ignored))
{
    printf("ProcSet( ");

        for (int index = 0; index < self->nb_boundary; index += 2) {
            printf("%d-%d ", self->_boundaries[index],
            self->_boundaries[index+1]-1);
        }
        printf(")");
        printf("- taille : %d\n", self->nb_boundary);

        Py_RETURN_NONE;
}

static PyTypeObject ProcSetType;

static PyObject *
ProcSet_union(ProcSetObject *self, PyObject *args)
{

    pset_boundary_t *new_boundaries;
    ProcSetObject *other;

    if (!PyArg_ParseTuple(args, "O!", &ProcSetType, &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // union case : alloc a memory having the N+M size of the two objects
    //      with N and M the number of interval in the procset
    int total_intervals = self->nb_boundary + other->nb_boundary;

    new_boundaries = (pset_boundary_t *) malloc(total_intervals * sizeof(pset_boundary_t));
    if (new_boundaries == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate the memory to store the boundaries");
        return NULL;
    }

    bool enbound = false;
    pset_boundary_t sentinel = UINT32_MAX;

    int lbound_index = 0, rbound_index = 0, index = 0;
    pset_boundary_t lhead = self->_boundaries[lbound_index];
    pset_boundary_t rhead = other->_boundaries[rbound_index];

    bool lend = lbound_index%2 != 0;
    bool rend = rbound_index%2 != 0;

    pset_boundary_t head = (pset_boundary_t) fmin(lhead, rhead);

    while (head < sentinel) {
        int inleft = (head < lhead) == lend;
        int inright = (head < rhead) == rend;
        int keep = inleft | inright;

        if (keep ^ enbound) {
            enbound = !enbound;
            new_boundaries[index] = head;
            index++;
        }

        if (head == lhead) {
            lbound_index++;

            if (lbound_index < self->nb_boundary) {
                lend = lbound_index%2 != 0;
                lhead = self->_boundaries[lbound_index];
            } else { // sentinel
                lhead = sentinel;
                lend = false;
            }
        }
        if (head == rhead) {
            rbound_index++;
            if (rbound_index < other->nb_boundary) {
                rend = rbound_index%2 != 0;
                rhead = other->_boundaries[rbound_index];
            } else { // sentinel
                rhead = sentinel;
                rend = false;
            }
        }

        head = (pset_boundary_t) fmin(lhead, rhead);
    }

    ProcSetObject *new_procset = PyObject_New(ProcSetObject, &ProcSetType);
    if (new_procset == NULL) {
        free(new_boundaries);
        return NULL;
    }

    new_procset->_boundaries = new_boundaries;
    new_procset->nb_boundary = index;

    return (PyObject *)new_procset;
}

static PyMethodDef ProcSet_methods[] = {
    {"show", (PyCFunction) ProcSet_show, METH_NOARGS, "Show the boundaries of the ProcSet"},
    {"union", (PyCFunction) ProcSet_union, METH_VARARGS, "Apply the assemblist union operation and return a new ProcSet"},
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
