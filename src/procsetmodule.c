#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdbool.h> // xxx C99
#include "structmember.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
static PyTypeObject ProcSetType;

// define the type of the boundaries of the set
typedef uint32_t pset_boundary_t;
pset_boundary_t maxBoundValue = UINT32_MAX;
// define a function type for the operator
typedef bool (*OperatorFunction)(bool, bool);

// functions that are making the bitwise operation
bool bitwiseOr(bool inLeft, bool inRight) {
    return inLeft | inRight;
}

bool bitwiseAnd(bool inLeft, bool inRight) {
    return inLeft & inRight;
}

bool bitwiseSubtraction(bool inLeft, bool inRight) {
    return inLeft & (!inRight);
}

bool bitwiseXor(bool inLeft, bool inRight) {
    return inLeft ^ inRight;
}


// define of the procset type
typedef struct {
    PyObject_HEAD
    pset_boundary_t *_boundaries;
    size_t nb_boundary;
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
    int needed_space = (lenght+1)/2;

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

    if (index%2 != 0) {
        free(tmp);
        PyErr_SetString(PyExc_ValueError, "The number of boundaries in input must be even");
        return -1;
    }

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
    // TODO : gérer le cas avec aucun argument
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
ProcSet_repr(ProcSetObject *self)
{ 
    PyObject *repr_obj = NULL;

    // PART I - Calculate the size of the string
    // Calculate the maximum size of a bound
    uint32_t max_bound = self->_boundaries[self->nb_boundary - 1];
    size_t max_bound_size = snprintf(NULL, 0, "%u", max_bound); // As the bounds are supposed to be stored in ascendant way

    // Calculate the size of the string
    size_t repr_string_size = 9;  // "ProcSet(" + ")"
    repr_string_size += (self->nb_boundary - 1);  // Account for the separators "-" qnd " "
    repr_string_size += (self->nb_boundary * max_bound_size);  // Account for the bounds

    // PART II - Create a string representation of the boundaries
    char *repr_string = (char *)malloc(repr_string_size + 1);
    if (repr_string != NULL) {
        repr_string[0] = '\0';  // Initialize the string with an empty string
        strcat(repr_string, "ProcSet(");

        // Iterate over the boundaries and append them to the string
        if (self->nb_boundary > 0) {
            char first_interval[max_bound_size*2+2]; // +2 for "-" and "\0" character
            sprintf(first_interval, "%d-%d", self->_boundaries[0], self->_boundaries[1]);
            strcat(repr_string, first_interval);
            
            for (size_t index = 2; index < self->nb_boundary; index+=2) {
                char interval[max_bound_size*2+3]; // +3 for "-", " " and "\0" character
                sprintf(interval, " %d-%d", self->_boundaries[index], self->_boundaries[index+1]);
                strcat(repr_string, interval);
            }
        }

        strcat(repr_string, ")");
        repr_obj = PyUnicode_FromString(repr_string);
        free(repr_string);
    }

    return repr_obj;
}

PyObject *
_merge(ProcSetObject *lpset, ProcSetObject *rpset, OperatorFunction operator, size_t neededSize) {
    // memory allocating for the neededSize
    pset_boundary_t *newBoundaries = (pset_boundary_t *) malloc(neededSize * sizeof(pset_boundary_t));
    if (newBoundaries == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate the memory to store the new boundaries");
        return NULL;
    }

    bool enbound = false;
    pset_boundary_t sentinel = maxBoundValue;

    size_t lbound_index = 0, rbound_index = 0, index = 0;
    pset_boundary_t lhead = lpset->_boundaries[lbound_index];
    pset_boundary_t rhead = rpset->_boundaries[rbound_index];

    bool lend = lbound_index%2 != 0;
    bool rend = rbound_index%2 != 0;

    pset_boundary_t head = lhead < rhead ? lhead : rhead;;

    while (head < sentinel) {
        bool inleft = (head < lhead) == lend;
        bool inright = (head < rhead) == rend;
        bool keep = operator(inleft, inright);

        if (keep ^ enbound) {
            enbound = !enbound;
            newBoundaries[index] = head;
            index++;
        }

        if (head == lhead) {
            lbound_index++;

            if (lbound_index < lpset->nb_boundary) {
                lend = lbound_index%2 != 0;
                lhead = lpset->_boundaries[lbound_index];
            } else { // sentinel
                lhead = sentinel;
                lend = false;
            }
        }
        if (head == rhead) {
            rbound_index++;
            if (rbound_index < rpset->nb_boundary) {
                rend = rbound_index%2 != 0;
                rhead = rpset->_boundaries[rbound_index];
            } else { // sentinel
                rhead = sentinel;
                rend = false;
            }
        }

        head = lhead < rhead ? lhead : rhead;
    }

    ProcSetObject *new_procset = PyObject_New(ProcSetObject, &ProcSetType);
    if (new_procset == NULL) {
        free(newBoundaries);
        // XXX: Peut-être une autre exception ? (mémoire par exemple)
        PyErr_SetString(PyExc_ValueError, "Failed to create the new ProcSet");
        return NULL;
    }

    new_procset->_boundaries = newBoundaries;
    new_procset->nb_boundary = index;

    return (PyObject *)new_procset;

}

static PyObject *
ProcSet_union(ProcSetObject *self, PyObject *args)
{

    ProcSetObject *other;

    if (!PyArg_ParseTuple(args, "O!", &ProcSetType, &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // union case : alloc a memory having the N+M size of the two objects
    //      with N and M the number of interval in the procset
    size_t neededSize = self->nb_boundary + other->nb_boundary;

    // merge calling
    return _merge(self, other, bitwiseOr, neededSize);

}

static PyObject *
ProcSet_intersection(ProcSetObject *self, PyObject *args)
{

    ProcSetObject *other;

    if (!PyArg_ParseTuple(args, "O!", &ProcSetType, &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // union case : alloc a memory having the N+M size of the two objects
    //      with N and M the number of interval in the procset
    size_t neededSize = self->nb_boundary > other->nb_boundary ?
                        self->nb_boundary : other->nb_boundary;

    // merge calling
    return _merge(self, other, bitwiseAnd, neededSize);

}

static PyObject *
ProcSet_difference(ProcSetObject *self, PyObject *args)
{

    ProcSetObject *other;

    if (!PyArg_ParseTuple(args, "O!", &ProcSetType, &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // union case : alloc a memory having the N+M size of the two objects
    //      with N and M the number of interval in the procset
    size_t neededSize = self->nb_boundary;

    // merge calling
    return _merge(self, other, bitwiseSubtraction, neededSize);

}

static PyObject *
ProcSet_symmetricDifference(ProcSetObject *self, PyObject *args)
{

    ProcSetObject *other;

    if (!PyArg_ParseTuple(args, "O!", &ProcSetType, &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // union case : alloc a memory having the N+M size of the two objects
    //      with N and M the number of interval in the procset
    size_t neededSize = self->nb_boundary + other->nb_boundary;

    // merge calling
    return _merge(self, other, bitwiseXor, neededSize);

}

static PyMethodDef ProcSet_methods[] = {
    {"union", (PyCFunction) ProcSet_union, METH_VARARGS, "Function that perform the assemblist union operation and return a new ProcSet"},
    {"intersection", (PyCFunction) ProcSet_intersection, METH_VARARGS, "Function that perform the assemblist intersection operation and return a new ProcSet"},
    {"difference", (PyCFunction) ProcSet_difference, METH_VARARGS, "Function that perform the assemblist difference operation and return a new ProcSet"},
    {"symmetric_difference", (PyCFunction) ProcSet_symmetricDifference, METH_VARARGS, "Function that perform the assemblist symmetric difference operation and return a new ProcSet"},
    {NULL}
};

static PyTypeObject ProcSetType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "ProcSet.procset",
    .tp_doc = "C implementation to represent Procset object",
    .tp_basicsize = sizeof(ProcSetObject),
    .tp_itemsize = 0,
    .tp_repr = (reprfunc) ProcSet_repr,
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
