#include "procsetheader.h"
#include <stdio.h>
#include <stdbool.h> // C99
#include "structmember.h" // deprecated, may use descrobject.h
#include <stdint.h> // C99
#include <stdlib.h>
#include <string.h>

#define STR_BUFFER_SIZE 255

// type of the predicate function used in the merge algorithm
typedef bool (*MergePredicate)(bool, bool);

// predicate functions
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

//returns the number of intervals in the set
PyObject *
ProcSet_count(ProcSetObject *self) {
    return PyLong_FromLong((long) (self->nb_boundary/2));
}

//returns true if the number of nb_boundaries == 2 (which means there is only one contiguous interval in the set)
PyObject *
ProcSet_iscontiguous(ProcSetObject *self){
    return (self->nb_boundary == 2 ? Py_True : Py_False);
}


// Deallocation method
static void 
ProcSet_dealloc(ProcSetObject *self)
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
static PyObject * 
ProcSet_new(PyTypeObject *type, PyObject *Py_UNUSED(args), PyObject *Py_UNUSED(kwds))
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
        PyErr_BadArgument();
        return -1;
    }

    // we try to parse the argument as a list 
    if (!PyArg_ParseTuple(args, "O", &liste)){
        printf("Parsing failed !\n");
        //we don't clean the buffer since it's and object
        PyErr_BadArgument();
        return -1;
    }

    printf("Successfully Parsed !\n");

    //is liste a list ?
    if (!PySequence_Check(liste)){
        PyErr_SetString(PyExc_ArithmeticError, "The given argument should be of type 'list' !");
        return -1;
    }

    // we allocate space for the boundaries
    Py_ssize_t length = PySequence_Size(liste);
    printf("number of elements : %li\n", (long) length);
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

static PyObject *
ProcSet_str(ProcSetObject *self)
{ 
    //The object we're going to return;
    PyObject *str_obj = NULL;
  
    // an empty string that will be filled with "a b-c ..."
    char *bounds_string = (char * ) PyMem_Malloc((sizeof(char) * STR_BUFFER_SIZE));
    if (!bounds_string){
        PyErr_SetString(PyExc_BufferError, "Not enough memory !");
        return NULL;
    }
    
    bounds_string[0] = '\0';


    int i = 0;
    // for every pair of boundaries
    while(i < self->nb_boundary){
        // a and b -> [a, b[
        pset_boundary_t a = self->_boundaries[i];
        pset_boundary_t b = (self->_boundaries[i+1]) -1; //b -1 as the interval is half opened 

        if (a == b){
            //single number
            sprintf(bounds_string + strlen(bounds_string), "%u ", a);
        } else {
            //interval
            sprintf(bounds_string + strlen(bounds_string), "%u-%u ",  a,b);
        }

        i+= 2;
    }

    *(bounds_string + strlen(bounds_string)) = '\0';

    // Transform to PyObject Unicode
    str_obj = PyUnicode_FromString(bounds_string);

    //freeing the allocated memory
    PyMem_Free(bounds_string);
    return str_obj;
}

// __len__
static Py_ssize_t
ProcSequence_length(ProcSetObject* self){
    //Si l'objet n'existe pas 
    if (!self || !self->_boundaries){
        PyErr_SetString(PyExc_Exception, "self is null !");
        return -1;
    }

    // somme de la taille de tout les intervals de la structure
    Py_ssize_t res = 0;

    // pour chaque interval
    for (int i = 0; i < self->nb_boundary; i+=2){
        //On ajoute sa taille au résultat
        //La taille n'a pas besoin de +1 car intervals semi ouverts
        res += self->_boundaries[i+1] - self->_boundaries[i]; 
    }

    //On retourne le résultat
    return res;
}

// __getitem__
static PyObject* ProcSequence_getItem(ProcSetObject *self, Py_ssize_t pos){
    //on vérifie que l'objet est atteignable (!NULL, pos < len), pas besoin de vérifier pos > 0 car pos négative -> positive = len + pos
    Py_ssize_t len = ProcSequence_length(self);
    if (len == -1){
        //trying to access null
        PyErr_SetString(PyExc_Exception, "self is NULL !");
        return NULL;
    } else if (len < pos){
        PyErr_SetString(PyExc_Exception, "Trying to access out of bound position !");
        return NULL;
    }

    int i = 0;          //position                
    int itv = 0;        //current interval
    while (i < pos){
        pset_boundary_t a = self->_boundaries[itv];                 // left element of the current interval
        pset_boundary_t b = self->_boundaries[itv+1];               // right element of the current interval

        if ((pos - i) < b-a) { // if the interval we're looking for is inside the current interval
            break;
        }

        i += (b-a);
        itv += 2;
    }

    // ith element
    return PyLong_FromUnsignedLong(self->_boundaries[itv] + (pset_boundary_t) (pos - i));
}

// __contains__
static int ProcSequence_contains(ProcSetObject* self, PyObject* val){
    // conversion of the PyObject to a C object
    pset_boundary_t value = (pset_boundary_t) PyLong_AsUnsignedLong(val);

    // easiest case: the value is greater than the last proc or lower than the first proc
    if (!self->_boundaries || value < *(self->_boundaries) | value >= self->_boundaries[self->nb_boundary - 1]){
        return 0;
    }

    // if not, we're going to need to go through the intervals
    int itv = 0;

    //while we still have intervals and the value is lower than the lower bound of the current interval
    while (itv < self->nb_boundary && self->_boundaries[itv] < value){
        itv += 2;
    }
    return self->_boundaries[itv+1] > value;        // the value is in the set if it's lower than the upper bound
} 

// Liste des methodes qui permettent a procset d'etre utilisé comme un objet sequence
PySequenceMethods ProcSequenceMethods = {
    (lenfunc) ProcSequence_length,               // sq_length    __len__
    0,                                          // sq_concat    __add__
    0,                                          // sq_repeat    __mul__
    (ssizeargfunc) ProcSequence_getItem,        // sq_item      __getitem__
    0,                                          // sq_ass_item   __setitem__ / __delitem__
    0,                                          // sq_inplace_concat
    0,                                          // sq_inplace_repeat
    (objobjproc) ProcSequence_contains,         // sq_contains  __contains__
    0,                                          // ?
    0,                                          // ?
};


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
    {"count", (PyCFunction) ProcSet_count, METH_NOARGS, "Returns the number of disjoint intervals in the ProcSet."},
    {"iscontiguous", (PyCFunction) ProcSet_iscontiguous, METH_NOARGS, "Returns ``True`` if the ProcSet is made of a unique interval."},
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
    .tp_as_sequence = &ProcSequenceMethods,                 //pointer to the sequence object
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
