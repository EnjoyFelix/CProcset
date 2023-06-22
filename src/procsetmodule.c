#define PY_SSIZE_T_CLEAN
#include <Python.h>
// documenter utilisation stdbool.h
#include <stdbool.h>
#include "structmember.h"

// define the type of the boundaries of the set
typedef uint32_t pset_boundary_t;

// define of the procset type
typedef struct {
    PyObject_HEAD
    pset_boundary_t *_boundaries;
    size_t nb_boundary; // TODO : transform to size_t (or ssize_t si besoin de -1)
} ProcSetObject;

int
create_pset_from_string(ProcSetObject *self, char *pset_string)
{
    pset_boundary_t *tmp;
    int lenght = strlen(pset_string);
    /* calculate the needed space to allocate
     - the input string is like "n-n n-n n-n", with n a digit
    the worse case is when n is one digit, when we need
        - strlen(string)//2 + 1 to have enought place to store all the bounds */
    int needed_space = lenght/2 + 1;

    tmp = (pset_boundary_t *) malloc(needed_space * sizeof(pset_boundary_t));
    if (tmp == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate memory to store the boundaries");
        return -1;
    }

    char* bound;
    size_t index;

    bound = pset_string;
    bound = strtok(bound, " -");
    index = 0;
    while (bound != NULL) {
        // check if bound is a digit
        // printf("bound = %s \n", bound);
        // if (!isdigit(bound)) {
        //     free(tmp);
        //     PyErr_SetString(PyExc_ValueError, "Input boundaries contains non-digits values");
        //     return -1;
        // }
        tmp[index] = index%2 == 0 ? atoi(bound) : atoi(bound) + 1;
        ++index;
        bound = strtok(NULL, " -");
    }
    // printf("\n");

    
    // char *st_result, *st_help;
    // bound = pset_string;
    // bound = strtok_r(bound, " ", &st_result);
    // index = 0;
    // while (bound) {
    //     // printf("[%s]", bound);
    //     // if (!isdigit(bound)) {
    //     //     free(tmp);
    //     //     PyErr_SetString(PyExc_ValueError, "Input boundaries contains non-digits values");
    //     //     return -1;
    //     // }
    //     // tmp[index++] = atoi(bound);

    //     char* help = strtok_r(bound, "-", &st_help);    
    //     while (help) {
    //         printf("<%s>", help);
    //         // if (!isdigit(bound)) {
    //         //     free(tmp);
    //         //     PyErr_SetString(PyExc_ValueError, "Input boundaries contains non-digits values");
    //         //     return -1;
    //         // }
    //         // tmp[index++] = atoi(bound);
    //         help = strtok_r(NULL, "-", &st_help);
    //     }

    //     bound = strtok_r(NULL, " ", &st_result);
    // }

    // if (index%2 != 0) {
    //     free(tmp);
    //     PyErr_SetString(PyExc_ValueError, "The number of boundaries in input must be even");
    //     return -1;
    // }

    free(self->_boundaries);
    self->_boundaries = tmp;
    self->nb_boundary = index;
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
    // TODO : gerer le cas avec aucun argument
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
    printf("ProcSet(");
    if (self->nb_boundary >= 2) {
        printf("%d-%d", self->_boundaries[0], self->_boundaries[1]-1);
        for (size_t index = 2; index < self->nb_boundary; index += 2) {
            printf(" %d-%d", self->_boundaries[index], self->_boundaries[index+1]-1);
        }
    }
    printf(")");
    //printf("- taille : %ld\n", self->nb_boundary);
    printf("\n");

    Py_RETURN_NONE;
}

static PyTypeObject ProcSetType;
// TODO: ecrire en haut

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
    size_t max_needed_bounds = self->nb_boundary + other->nb_boundary;

    new_boundaries = (pset_boundary_t *) malloc(max_needed_bounds * sizeof(pset_boundary_t));
    if (new_boundaries == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate the memory to store the boundaries");
        return NULL;
    }

    bool enbound = false;
    pset_boundary_t sentinel = UINT32_MAX;

    // TODO: changer en size_t
    size_t lbound_index = 0, rbound_index = 0, index = 0;
    pset_boundary_t lhead = self->_boundaries[lbound_index];
    pset_boundary_t rhead = other->_boundaries[rbound_index];

    bool lend = lbound_index%2 != 0;
    bool rend = rbound_index%2 != 0;

    pset_boundary_t head = (pset_boundary_t) fmin(lhead, rhead);

    while (head < sentinel) {
        bool inleft = (head < lhead) == lend;
        bool inright = (head < rhead) == rend;
        bool keep = inleft | inright;

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

        head = (pset_boundary_t) fmin(lhead, rhead); // TODO : operation ternaire
    }

    ProcSetObject *new_procset = PyObject_New(ProcSetObject, &ProcSetType);
    if (new_procset == NULL) {
        free(new_boundaries);
        // TODO: exception de memoire
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
    .tp_doc = "C implementation to represent Procset object ㋡",
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
