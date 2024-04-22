// TODO Global : not use the basics allocator functions, but the PyMem equivalent 

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>
#include <stdbool.h> // C99
#include "structmember.h" // deprecated, may use descrobject.h
#include <stdint.h> // C99
#include <stdlib.h>
#include <string.h>

typedef uint32_t pset_boundary_t;
pset_boundary_t MAX_BOUND_VALUE = UINT32_MAX;

// define a function type for the operator
typedef bool (*MergePredicate)(bool, bool);

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


// Definition of the ProcSet struct
typedef struct {
    //Python objet boilerplate
    PyObject_HEAD

    //Boundaries of the ProcSet paired two by two as half-opened intervals
    pset_boundary_t *_boundaries;   

    //Number of boundaries, (2x nbr of intervals)
    Py_ssize_t nb_boundary;
} ProcSetObject;


// Deallocation method
static void ProcSet_dealloc(ProcSetObject *self)
{
    // Debug message
    printf("Calling dealloc on ProcSetObject @%p \n", (void * )self);

    // We free the memory allocated for the boundaries
    // using the integrated py function
    PyMem_Free(self->_boundaries);

    // we call the free function of the type
    Py_TYPE((PyObject *)self)->tp_free((PyObject *) self);
}

// new: Method called when an object is created,
// it does not set values as the ProcSet object is mutable
static PyObject * ProcSet_new(PyTypeObject *type, PyObject *Py_UNUSED(args), PyObject *Py_UNUSED(kwds))
{
    ProcSetObject *self;
    
    // we allocate memory for our new object using its type's allocator (the default one in this case)
    self = (ProcSetObject *) type->tp_alloc(type, 0);

    // nothing to init because the object is mutable and the integer's default value is not null
    return (PyObject *) self;
}

// init: initialization function, called after new
// initializes the procset object from a list of integers (for now);
static int
ProcSet_init(ProcSetObject *self, PyObject *args, PyObject *kwds)
{
    // the object that will be parsed
    // should be like [a,b,c,...] with abc being u_ints
    PyObject* liste;

    // if no args were given or if a keyword was given
    if (!args || kwds){
        //TODO: explicit error message
        PyErr_BadArgument();
        return -1;
    }

    // we parse the list and and check for errors
    if (!PyArg_ParseTuple(args, "O", &liste)){
        printf("Parsing failed !\n");
        //we don't clean the buffer since it's and object
        PyErr_BadArgument();
        return -1;
    }

    printf("Successfully Parsed !\n");

    //we verify that liste can be sequenced !
    if (!PySequence_Check(liste)){
        printf("Parsed object was not a list !\n");
        //TODO: clearer error message
        PyErr_BadArgument();
        return -1;
    }

    // we allocate space for the boundaries
    Py_ssize_t length = PySequence_Size(liste); printf("number of elements : %li\n", (long) length);
    self->_boundaries = (pset_boundary_t * ) PyMem_Malloc(sizeof(pset_boundary_t) * length);

    //side of the interval
    bool opened = false;

    // we parse every element in the list
    for (int i = 0; i < (int) length; i++){
        // The ith object of the list
        PyObject* obj = PySequence_GetItem(liste, i);
        self->_boundaries[i] = PyLong_AsLong(obj);

        //we add one if we're one the opened side of the interval
        if (opened){
            self->_boundaries[i]++;
        }

        opened = !opened;
        self->nb_boundary++;
    }

    Py_DECREF(liste);
    return 0;
}

// repr should return and object that when called inside eval() should create the same object
/* static PyObject *
ProcSet_repr(ProcSetObject *self)
{ 
    PyObject *repr_obj = NULL;
    
    char* bounds_string = bounds_to_string(self);
    if (bounds_string == NULL) {
        return NULL;
    }

    // Allocate the needed memory
    Py_ssize_t repr_string_size = strlen(bounds_string) + 10; // +10 to represent "ProcSet(", ")" and "\0"
    char *p_repr_string = (char *) malloc(repr_string_size);
    if (p_repr_string == NULL) {
        free(bounds_string);
        PyErr_SetString(PyExc_MemoryError, "Failed to alocate memory");
        return NULL;
    }

    // Format the complete representation string
    sprintf(p_repr_string, "ProcSet(%s)", bounds_string);

    // Transform to PyObject Unicode
    repr_obj = PyUnicode_FromString(p_repr_string);

    if (strlen(bounds_string) > 0) {
        free(bounds_string);
    }
    free(p_repr_string);

    return repr_obj;
} */

static PyObject *
ProcSet_str(ProcSetObject *self)
{ 
    //The object we're going to return;
    PyObject *str_obj = NULL;
  
    // an empty string that will be filled with "a b c "
    char *bounds_string = (char * ) PyMem_Malloc((sizeof(char) * 255));
    if (!bounds_string){
        //TODO: pas assez de mem
        return NULL;
    }
    
    bounds_string[0] = '\0';


    int i = 0;
    // for every pair of boundaries
    while(i < self->nb_boundary){
        // i add [a, b-1] to the output string. (b-1) to account for the half opened 
        sprintf(bounds_string + strlen(bounds_string), "[%u, %u] ", self->_boundaries[i] ,(self->_boundaries[i+1]) -1);
        i+= 2;
    }

    *(bounds_string + strlen(bounds_string)) = '\0';

    // Transform to PyObject Unicode
    str_obj = PyUnicode_FromString(bounds_string);
    
    if (strlen(bounds_string) > 0) {
        PyMem_Free(bounds_string);
    }

    return str_obj;
}


static PyMethodDef ProcSet_methods[] = {
/*     {"union", (PyCFunction) ProcSet_union, METH_VARARGS, "Function that perform the assemblist union operation and return a new ProcSet"},
    {"intersection", (PyCFunction) ProcSet_intersection, METH_VARARGS, "Function that perform the assemblist intersection operation and return a new ProcSet"},
    {"difference", (PyCFunction) ProcSet_difference, METH_VARARGS, "Function that perform the assemblist difference operation and return a new ProcSet"},
    {"symmetric_difference", (PyCFunction) ProcSet_symmetricDifference, METH_VARARGS, "Function that perform the assemblist symmetric difference operation and return a new ProcSet"},
    {"aggregate", (PyCFunction) ProcSet_aggregate, METH_NOARGS, 
    "Return a new ProcSet that is the convex hull of the ProcSet.\n"
    "\n"
    "The convex hull of an empty ProcSet is the empty ProcSet.\n"
    "\n"
    "The convex hull of a non-empty ProcSet is the contiguous ProcSet made\n"
    "of the smallest unique interval containing all intervals from the\n"
    "non-empty ProcSet."},  */
    {NULL, NULL, 0, NULL}
};

static PyTypeObject ProcSetType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "procset.ProcSet",                           // __name__
    .tp_doc = "C implementation of the ProcSet datatype",   // __doc__
    .tp_basicsize = sizeof(ProcSetObject),                  // size of the struct
    .tp_itemsize = 0,                                       // additional size values for dynamic objects
/*     .tp_repr = (reprfunc) ProcSet_repr,*/                     // __repr__
    .tp_str = (reprfunc) ProcSet_str,                       // __str__
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   // flags, basetype is optional   
    .tp_new = (newfunc) ProcSet_new,                        // __new__
     .tp_init = (initproc) ProcSet_init,                    // __init__
    .tp_dealloc = (destructor) ProcSet_dealloc,             // Method called when the object is not referenced anymore, frees the memory and calls tp_free 
    .tp_methods = ProcSet_methods,                          // the list of defined methods for this object
    /* .tp_getset = ProcSet_getset, */                  // the list of defined getters and setters
};

// basic Module definition
static PyModuleDef procsetmodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "procset",
    .m_doc = "ProcSet module to manipulate set of processor",
    .m_size = -1,
};



// basic module init function
PyMODINIT_FUNC PyInit_procset(void)
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
