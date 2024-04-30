#include "procsetheader.h"
#include "mergepredicate.h"
#include <stdio.h>
#include "structmember.h" // deprecated, may use descrobject.h
#include <stdint.h> // C99
#include <stdlib.h>
#include <string.h>

#define STR_BUFFER_SIZE 255

// Update type, used by the _update_core function
typedef PyObject * (* InplaceType) (ProcSetObject *, PyObject *);

//returns the number of intervals in the set
PyObject *
ProcSet_count(ProcSetObject *self, void * Py_UNUSED(args)) {
    return PyLong_FromLong((long) (self->nb_boundary/2));
}

//returns true if the number of nb_boundaries == 2 (which means there is only one contiguous interval in the set)
PyObject *
ProcSet_iscontiguous(ProcSetObject *self, void * Py_UNUSED(args)){
    return (self->nb_boundary == 2 ? Py_True : Py_False);
}

// returns an iterator
PyObject *
ProcSet_intervals(ProcSetObject *self, void * Py_UNUSED(args)){
    return PyObject_GetIter((PyObject*) self);
}

// returns a shallow copy of the object
PyObject * 
ProcSet_copy(ProcSetObject *self, void * Py_UNUSED(args)){

    // ProcSet object type
    PyTypeObject* type = Py_TYPE((PyObject *) self);            //pbbly not a ref to a new object

    // another object
    ProcSetObject* copy = (ProcSetObject *) type->tp_alloc(type, 0);

    // we copy the nbr of boundaries
    copy->nb_boundary = self->nb_boundary;

    // we allocate memory for the 
    copy->_boundaries = (pset_boundary_t *) PyMem_Malloc( copy->nb_boundary * sizeof(pset_boundary_t));
    if (!self->_boundaries){
        Py_DECREF((PyObject* )copy);        // we allow the copy to be gc'ed

        PyErr_NoMemory();
        return NULL;
    }

    // we copy every value in the boundary array
    for (int i = 0; i < self->nb_boundary; i++){
        copy->_boundaries[i] = self->_boundaries[i];
    }

    return (PyObject *) copy;
}




// MERGE (Core function)
static PyObject*
merge(ProcSetObject* lpset,ProcSetObject* rpset, MergePredicate operator){
    PyTypeObject * psettype = ((PyObject*) lpset)->ob_type;

    //the potential max nbr of intervals
    Py_ssize_t maxBound = lpset->nb_boundary + rpset->nb_boundary;

    //the resulting
    ProcSetObject* result = (ProcSetObject *) psettype->tp_new(psettype, NULL, NULL);

    //we take more than we should, that's ok
    result->_boundaries = (pset_boundary_t *) PyMem_Malloc(sizeof(pset_boundary_t) * maxBound);
    if (!result->_boundaries){
        PyErr_NoMemory();                 
        Py_DECREF((PyObject*) result);
        return NULL;
    }

    bool side = false;                          //false if lower bound, true if upper

    pset_boundary_t sentinel = UINT32_MAX;

    Py_ssize_t lbound_index = 0, rbound_index = 0;
    pset_boundary_t lhead = lpset->_boundaries[lbound_index];
    pset_boundary_t rhead = rpset->_boundaries[rbound_index];

    //is this list on an upper bound or on a lower bound ?
    bool lside = lbound_index % 2 != 0;
    bool rside = rbound_index % 2 != 0;

    //min of the two intervals 
    pset_boundary_t head = (lhead < rhead) ? lhead : rhead;

    while (head < sentinel) {
        bool inleft = (head < lhead) == lside;
        bool inright = (head < rhead) == rside;

        bool keep = operator(inleft, inright);

        //Black magic implementation
        if (keep ^ side) {
            result->_boundaries[result->nb_boundary] = head;
            result->nb_boundary +=1;

            side = !side;       // we chose a bound for this side
        }

        if (head == lhead) {
            lbound_index++;

            if (lbound_index < lpset->nb_boundary) {
                lside = lbound_index%2 != 0;
                lhead = lpset->_boundaries[lbound_index];
            } else { // sentinel
                lhead = sentinel;
                lside = false;
            }
        }
        if (head == rhead) {
            rbound_index++;
            if (rbound_index < rpset->nb_boundary) {
                rside = rbound_index%2 != 0;
                rhead = rpset->_boundaries[rbound_index];
            } else { // sentinel
                rhead = sentinel;
                rside = false;
            }
        }

        head = (lhead < rhead) ? lhead : rhead;               
    }

    // if we had allocated the right amount of memory
    if (result->nb_boundary == maxBound){
        return (PyObject *) result;
    }

    // we free the excess memory
    pset_boundary_t* bounds = PyMem_Realloc(result->_boundaries, (result->nb_boundary + 1) * sizeof(pset_boundary_t));

    // bounds will be null if realloc failed (yet the previous pointer will remain valid, se we have to check)
    if (bounds){
        result->_boundaries = bounds;
    }

    return (PyObject *) result;
}

static PyObject *
_inplace_core(ProcSetObject * self, PyObject * other, InplaceType fonction){
    // we get the result of the or
    PyObject * result = fonction(self, other);
    
    // you get no result when an error occures, so we check for errors
    if (!result){
        return NULL;
    }
    
    Py_ssize_t nb_elements = ((ProcSetObject * ) result)->nb_boundary;

    // self is probably not the right size
    if (!pset_resize(self, nb_elements)){
        return NULL;    // the error message is already set
    }
    
    // we copy every element of result in self
    pset_copy((ProcSetObject * ) result, self, nb_elements);

    // we set the right size for self
    self->nb_boundary = nb_elements;

    // we return result as it's a copy of self and is not referrenced by anything
    return result;
}

// __bool__
static int
ProcSet_bool(ProcSetObject* self){
    return self->nb_boundary != 0;
}

// __or__ et |
static PyObject*
ProcSet_or(ProcSetObject* self, PyObject* other){

    // other needs to be a procset, self will always be
    if (!Py_IS_TYPE(other, Py_TYPE(self))){
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // we call merge on the two objects and return the result
    return merge(self, (ProcSetObject *) other, bitwiseOr);
}

// __ior__
static PyObject *
ProcSet_ior(ProcSetObject * self, PyObject* other){
    return _inplace_core(self, other, ProcSet_or);
}

// __and__ et &
static PyObject*
ProcSet_and(ProcSetObject* self, PyObject* other){

    // other needs to be a procset, self will always be
    if (!Py_IS_TYPE(other, Py_TYPE(self))){
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // we call merge on the two objects and return the result
    return merge(self, (ProcSetObject *) other, bitwiseAnd);
}

// __iand__
static PyObject *
ProcSet_iand(ProcSetObject * self, PyObject* other){
    return _inplace_core(self, other, ProcSet_and);
}

// __sub__ et -
static PyObject*
ProcSet_sub(ProcSetObject* self, PyObject* other){

    // other needs to be a procset, self will always be
    if (!Py_IS_TYPE(other, Py_TYPE(self))){
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // we call merge on the two objects and return the result
    return merge(self, (ProcSetObject *) other, bitwiseSubtraction);
}

// __isub__
static PyObject *
ProcSet_isub(ProcSetObject * self, PyObject* other){
    return _inplace_core(self, other, ProcSet_sub);
}

// __xor__ et ^
static PyObject*
ProcSet_xor(ProcSetObject* self, PyObject* other){

    // other needs to be a procset, self will always be
    if (!Py_IS_TYPE(other, Py_TYPE(self))){
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // we call merge on the two objects and return the result
    return merge(self, (ProcSetObject *) other, bitwiseXor);
}

// __ixor__
static PyObject *
ProcSet_ixor(ProcSetObject * self, PyObject* other){
    return _inplace_core(self, other, ProcSet_xor);
}

// repertoires des methodes 
static PyNumberMethods ProcSet_number_methods = {
    0, // binaryfunc nb_add;
    (binaryfunc) ProcSet_sub,
    0, // binaryfunc nb_multiply;
    0, // binaryfunc nb_remainder;
    0, // binaryfunc nb_divmod;
    0, // ternaryfunc nb_power;
    0, // unaryfunc nb_negative;
    0, // unaryfunc nb_positive;
    0, // unaryfunc nb_absolute;
    (inquiry) ProcSet_bool,
    0, // unaryfunc nb_invert;
    0, // binaryfunc nb_lshift;
    0, // binaryfunc nb_rshift;
    (binaryfunc) ProcSet_and,
    (binaryfunc) ProcSet_xor,
    (binaryfunc) ProcSet_or,
    0, // unaryfunc nb_int;
    0, // void *nb_reserved;
    0, // unaryfunc nb_float;

    0, // binaryfunc nb_inplace_add;
    (binaryfunc) ProcSet_isub,
    0, // binaryfunc nb_inplace_multiply;
    0, // binaryfunc nb_inplace_remainder;
    0, // ternaryfunc nb_inplace_power;
    0, // binaryfunc nb_inplace_lshift;
    0, // binaryfunc nb_inplace_rshift;
    (binaryfunc) ProcSet_iand,
    (binaryfunc) ProcSet_ixor,
    (binaryfunc) ProcSet_ior,

    0, // binaryfunc nb_floor_divide;
    0, // binaryfunc nb_true_divide;
    0, // binaryfunc nb_inplace_floor_divide;
    0, // binaryfunc nb_inplace_true_divide;

    0, // unaryfunc nb_index;

    0, // binaryfunc nb_matrix_multiply;
    0, // binaryfunc nb_inplace_matrix_multiply;
};

static PyObject *
ProcSet_union(ProcSetObject *self, PyObject *args)
{
    //TODO : this function should allow args to be a list of procset (it should be a list of list but procset are wrappers for list and single values)
    ProcSetObject *other;

    // we try to parse another procset from the args
    if (!PyArg_ParseTuple(args, "O!", ((PyObject *) self)->ob_type , &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }


    // we call merge on the two objects
    return ProcSet_or(self, (PyObject *) other);
}

static PyObject *
ProcSet_intersection(ProcSetObject *self, PyObject *args)
{
    //TODO : this function should allow args to be a list of procset (it should be a list of list but procset are wrappers for list and single values)
    ProcSetObject *other;

    // we try to parse another procset from the args
    if (!PyArg_ParseTuple(args, "O!", ((PyObject *) self)->ob_type, &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // we call merge on the two objects
    return ProcSet_and(self, (PyObject *) other);

}

static PyObject *
ProcSet_difference(ProcSetObject *self, PyObject *args)
{

    //TODO : this function should allow args to be a list of procset (it should be a list of list but procset are wrappers for list and single values)
    ProcSetObject *other;

    // we try to parse another procset from the args
    if (!PyArg_ParseTuple(args, "O!", ((PyObject *) self)->ob_type, &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }


    // Py_ssize_t neededSize = self->nb_boundary;

    // we call merge on the two objects
    return ProcSet_sub(self, (PyObject *) other);

}

static PyObject *
ProcSet_symmetricDifference(ProcSetObject *self, PyObject *args)
{
    //TODO : this function should allow args to be a list of procset (it should be a list of list but procset are wrappers for list and single values)
    ProcSetObject *other;

    // we try to parse another procset from the args
    if (!PyArg_ParseTuple(args, "O!", ((PyObject *) self)->ob_type, &other)) {
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    // we call merge on the two objects
    return ProcSet_xor(self, (PyObject *) other);

}

// factorisation des fonctions d'update
static PyObject * 
_update_core(ProcSetObject *self, PyObject *args, InplaceType UpdateType){
        
    // the previous function does the heavy lifting for that one
    ProcSetObject * result = (ProcSetObject *) UpdateType(self, args);

    // if an error occured
    if (!result){
        return NULL;         // we just break, no need to tĥrow anything since the previous function call already does that
    }

    // if our list is smaller than the result's list
    if (self->nb_boundary < result->nb_boundary){
        pset_boundary_t * temp = PyMem_Realloc(self->_boundaries, result->nb_boundary * sizeof(pset_boundary_t));

        if (!temp){
            //we dont check for previous py errors since they would have been caught in the "if !result"
            PyErr_NoMemory();   // return error
            Py_DECREF(result);  // allow result to be gc'ed
            return NULL;
        }

        self->_boundaries = temp;        
    } 
    // if our list is bigger than the result's list
    else if (self->nb_boundary > result->nb_boundary){
        // we release the allocated memory for self->boundaries
        // we cannot realloc here because data was surely written, so realloc will fail
        PyMem_Free(self->_boundaries);

        // we allocate the amount of memory
        self->_boundaries = (pset_boundary_t * ) PyMem_Malloc(result->nb_boundary * sizeof(pset_boundary_t));
    }
    //we don't do anything if the sizes are equals

    //we copy every interval;
    for (Py_ssize_t i = 0; i < result->nb_boundary; i++){
        self->_boundaries[i] = result->_boundaries[i];
    }

    self->nb_boundary = result->nb_boundary;

    // we can't return self as is since python will think it came out of this function.
    // this would cause a segmentation fault as every reference to self would become null.
    // So we return result here as it's already a copy of result and can be gc'ed without any issue
    return (PyObject *) result;
}

// returns the intersection and updates self
static PyObject *
ProcSet_update(ProcSetObject *self, PyObject *args){
    return _update_core(self, args, ProcSet_union);
}

// returns the intersection and updates self
static PyObject *
ProcSet_update_intersection(ProcSetObject *self, PyObject *args){
    return _update_core(self, args, ProcSet_intersection);
}

// returns the difference and updates self
static PyObject *
ProcSet_update_difference(ProcSetObject *self, PyObject *args){
    return _update_core(self, args, ProcSet_difference);
}

// returns the symetric difference and updates self
static PyObject *
ProcSet_update_symmetricDifference(ProcSetObject *self, PyObject *args){
    return _update_core(self, args, ProcSet_symmetricDifference);
}



// returns the lower bound of the first interval
static PyObject*
ProcSet_min(ProcSetObject *self, void* Py_UNUSED(v)){
    // if null
    if (!self || !self->_boundaries){
        //TODO: set an exception
        return NULL;
    }

    //returns the first element 
    return PyLong_FromLong(*(self->_boundaries));
}

// returns the upper bound of the last interval
static PyObject*
ProcSet_max(ProcSetObject *self, void * Py_UNUSED(v)){
    // if null
    if (!self || !self->_boundaries){
        //TODO: set an exception
        return NULL;
    }

    //returns the first element 
    return PyLong_FromLong(self->_boundaries[self->nb_boundary -1] -1 );    //-1 to account for the half opened
}

// list of the getters and setters
static PyGetSetDef ProcSet_getset[] = {
    //name, get, set, doc, additional
    {"min", (getter) ProcSet_min, NULL ,"The first processor in the ProcSet (in increasing order).", NULL},
    {"max", (getter) ProcSet_max, NULL ,"The last processor in the ProcSet (in increasing order).", NULL},
    {NULL, NULL, NULL, NULL, NULL}
};




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
// initializes the procset object, this function should only receive sequenceable args / intergers in increasing order. 
static int
ProcSet_init(ProcSetObject *self, PyObject *args, PyObject *Py_UNUSED(kwds))
{
    // if no args were given:
    if (!args){
        //return 0 as this can happen in the py implementation
        return 0;
    }

    // we allocate the memory for the list
    self->_boundaries = (pset_boundary_t *) PyMem_Malloc(PySequence_Size(args) * 2 * sizeof(pset_boundary_t));
    if (!self->_boundaries){
        PyErr_NoMemory();
        return -1;
    }


    // an iterator on args (args is a list of objects)
    PyObject * iterator = PyObject_GetIter(args);

    // if args did not return an iterator (iterator protocol)
    if (!iterator){
        PyErr_SetString(PyExc_Exception, "Could not get an iterator on given args");        // we set the error message
        PyMem_Free(self->_boundaries);  // we free the allocated space
        return -1;
    }

    // the current item
    PyObject * currentItem;

    //the position of the interval
    int itv = 0;

    // for every argument
    while ((currentItem = PyIter_Next(iterator))) {
        //if the argument is iterable
        if (PySequence_Check(currentItem) && PySequence_Size(currentItem) == 2){
            // bounds of the interval as PyObjects
            PyObject *_a = PySequence_GetItem(currentItem, 0);
            PyObject *_b = PySequence_GetItem(currentItem, 1);

            // bound on the interval as procset boundaries
            pset_boundary_t a = PyLong_AsLong(_a);
            pset_boundary_t b = PyLong_AsLong(_b);

            // DECREF is called here because getItem gives a pointer to a new object
            Py_DECREF(_a);
            Py_DECREF(_b);

            self->_boundaries[itv] = a;             // lower bound
            self->_boundaries[itv+1] = b+1;         // greater bound, +1 cause half opened
        }
        // else if the argument is a number
        else if (PyNumber_Check(currentItem)){
            //TODO : check for error
            pset_boundary_t val = PyLong_AsLong(currentItem);
            self->_boundaries[itv] = val;          // lower bound
            self->_boundaries[itv+1] = val+1;      // greater bound

        } 
        //bad argument
        else {
            Py_DECREF(currentItem);
            Py_DECREF(iterator);
            PyMem_Free(self->_boundaries);  // we free the allocated space
            PyErr_BadArgument();
            return -1;
        }

        itv += 2;                           // we move on to the next interval
        Py_DECREF(currentItem);             // we allow the current element to be gc'ed 
    };  

    Py_DECREF(iterator);                    // we free the now useless iterator
    self->nb_boundary = PySequence_Size(args) * 2;
    return 0;
}



// __repr__
static PyObject *
ProcSet_repr(ProcSetObject *self){
    //The object we're going to return;
    PyObject *str_obj = NULL;

    // an empty string that will be filled with "ProcSet((a,b), c, (d,e))"
    char bounds_string[STR_BUFFER_SIZE] = "ProcSet(";

    int i = 0;
    // for every pair of boundaries
    while(i < self->nb_boundary){
        if (i != 0){
            strcat(bounds_string + strlen(bounds_string), ", ");
        };

        // a and b -> [a, b[
        pset_boundary_t a = self->_boundaries[i];
        pset_boundary_t b = (self->_boundaries[i+1]) -1; //b -1 as the interval is half opened 

        if (a == b){
            //single number
            sprintf(bounds_string + strlen(bounds_string), "%u", a);
        } else {
            //interval
            sprintf(bounds_string + strlen(bounds_string), "(%u, %u)",  a,b);
        }

        i+= 2;
    }

    strcat(bounds_string + strlen(bounds_string), ")\0");

    // Transform to PyObject Unicode
    str_obj = PyUnicode_FromString(bounds_string);
    return str_obj;
}

// __str__
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
    if (len <= 0L){
        //trying to access null
        //can't throw an error because it doesn't get caught by next :/
        return NULL;
    } else if (len <= pos){
        //PyErr_SetString(PyExc_Exception, "Trying to access out of bound position !");
        //can't throw an error because it doesn't get caught by next :/
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
    if (!self->_boundaries || value < *(self->_boundaries) || value >= self->_boundaries[self->nb_boundary - 1]){
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



// __eq__ and __ne__
static int
ProcSet_eq(ProcSetObject* self, ProcSetObject* other){
    // easiest case: they don't have the same number of element -> not equal
    if (self->nb_boundary != other->nb_boundary){
        return false;
    }

    // we go through the list and check the equality 
    Py_ssize_t i = 0;
    while (i < self->nb_boundary && self->_boundaries[i] == other->_boundaries[i]){
        i++;
    }

    // the intervals are the same if we didn't stop
    return i == self->nb_boundary;
}

static int _sub_super(ProcSetObject * self, ProcSetObject * other){
    PyObject * intersection = ProcSet_and(self, (PyObject * ) other);
    if (!intersection){
        return -1;
    }

    // self is a subset if every element is already in other
    int result = ProcSet_eq((ProcSetObject * ) intersection, self);
    
    ProcSet_dealloc((ProcSetObject *) intersection);    // we released the memory used by the intersection
    return result;
}

// issubset
static PyObject *
ProcSet_issubset(ProcSetObject *self, PyObject * args){
    //TODO: This function should be able to take list and single values as args

    //the other set
    ProcSetObject* other;

    // we try to parse another procset for the list
    if (!PyArg_ParseTuple(args, "O!", Py_TYPE(self), &other)){
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    return PyBool_FromLong(_sub_super(self, other));
}

// issubset
static PyObject *
ProcSet_issuperset(ProcSetObject *self, PyObject * args){
    //TODO: This function should be able to take list and single values as args

    //the other set
    ProcSetObject* other;

    // we try to parse another procset for the list
    if (!PyArg_ParseTuple(args, "O!", Py_TYPE(self), &other)){
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    return PyBool_FromLong(_sub_super(other, self));
}

// isdisjoint
static PyObject *
ProcSet_isdisjoint(ProcSetObject *self, PyObject * args){
    ProcSetObject * other;
    if (!PyArg_ParseTuple(args, "O!", Py_TYPE(self), &other)){
        PyErr_SetString(PyExc_TypeError, "Invalid operand. Expected a ProcSet object.");
        return NULL;
    }

    ProcSetObject * intersection = (ProcSetObject* ) ProcSet_and(self, (PyObject*) other);

    if (!intersection){
        return NULL;
    }

    int result = intersection->nb_boundary == 0;
    ProcSet_dealloc(intersection);          // we release the resulting procset

    return PyBool_FromLong(result);
}

// richcompare function
static PyObject* ProcSet_richcompare(ProcSetObject* self, PyObject* _other, int operation){
    //we compare the types:
    if (!Py_IS_TYPE(_other, Py_TYPE((PyObject*)self))){
        return Py_False;
    }

    //explicit cast
    ProcSetObject* other = (ProcSetObject*) _other;

    switch (operation){
        case Py_LT:{ // <
            // issubset and is different
            return PyBool_FromLong(_sub_super(self, other) & ! ProcSet_eq(self, other));
        };

        case Py_LE:{ // <=
            //is subset
            return PyBool_FromLong(_sub_super(self, other));
        };
     
        case Py_EQ:{ // ==
            return PyBool_FromLong(ProcSet_eq(self, other));
        };

        case Py_NE:{ // !=
            return PyBool_FromLong(!ProcSet_eq(self, other));
        };

        case Py_GT:{ // >
            // is superset and is different
            return PyBool_FromLong(_sub_super(other, self) & ! ProcSet_eq(self, other));
        };

        case Py_GE:{ // >=
            // is subset and is different
            return PyBool_FromLong(_sub_super(other, self));
        };
    }

    return NULL;
}


// methods
static PyMethodDef ProcSet_methods[] = {
    {"union", (PyCFunction) ProcSet_union, METH_VARARGS, "Function that perform the assemblist union operation and return a new ProcSet"},
    {"update", (PyCFunction) ProcSet_update, METH_VARARGS, "Update the ProcSet, adding elements from all others."},
    {"insert", (PyCFunction) ProcSet_update, METH_VARARGS, "Update the ProcSet, adding elements from all others, Alias for 'update()'"},
    {"intersection", (PyCFunction) ProcSet_intersection, METH_VARARGS, "Function that perform the assemblist intersection operation and return a new ProcSet"},
    {"intersection_update", (PyCFunction) ProcSet_update_intersection, METH_VARARGS, "Update the ProcSet, keeping only elements found in the ProcSet and all others."},
    {"difference", (PyCFunction) ProcSet_difference, METH_VARARGS, "Function that perform the assemblist difference operation and return a new ProcSet"},
    {"difference_update", (PyCFunction) ProcSet_update_difference, METH_VARARGS, "Update the ProcSet, removing elements found in others. "},
    {"discard", (PyCFunction) ProcSet_update_difference, METH_VARARGS, "Update the ProcSet, removing elements found in others, Alias for 'difference_update()'"},
    {"symmetric_difference", (PyCFunction) ProcSet_symmetricDifference, METH_VARARGS, "Function that perform the assemblist symmetric difference operation and return a new ProcSet"},
    {"symmetric_difference_update", (PyCFunction) ProcSet_update_symmetricDifference, METH_VARARGS, "Update the ProcSet, keeping only elements found in either the ProcSet or *other*, but not in both."},
    {"issubset", (PyCFunction) ProcSet_issubset, METH_VARARGS, "Test whether every element in the ProcSet is in *other*"},
    {"issuperset", (PyCFunction) ProcSet_issuperset, METH_VARARGS, "Test whether every element in *other* is in the ProcSet."},
    {"isdisjoint", (PyCFunction) ProcSet_isdisjoint, METH_VARARGS, "Return ``True`` if the ProcSet has no processor in common with *other*."},
    /*{"aggregate", (PyCFunction) ProcSet_aggregate, METH_NOARGS, 
    "Return a new ProcSet that is the convex hull of the ProcSet.\n"
    "\n"
    "The convex hull of an empty ProcSet is the empty ProcSet.\n"
    "\n"
    "The convex hull of a non-empty ProcSet is the contiguous ProcSet made\n"
    "of the smallest unique interval containing all intervals from the\n"
    "non-empty ProcSet."},  */
    {"copy", (PyCFunction) ProcSet_copy, METH_NOARGS, "Returns a new ProcSet with a shallow copy of the ProcSet."},
    {"__copy__", (PyCFunction) ProcSet_copy, METH_NOARGS, "Returns a new ProcSet with a shallow copy of the ProcSet."},
    {"__deepcopy__", (PyCFunction) ProcSet_copy, METH_NOARGS, "Returns a new copy of the ProcSet."},
    {"intervals", (PyCFunction) ProcSet_intervals, METH_NOARGS, "Returns an iterator over the intervals of the ProcSet in increasing order."},
    {"count", (PyCFunction) ProcSet_count, METH_NOARGS, "Returns the number of disjoint intervals in the ProcSet."},
    {"iscontiguous", (PyCFunction) ProcSet_iscontiguous, METH_NOARGS, "Returns ``True`` if the ProcSet is made of a unique interval."},
    {NULL, NULL, 0, NULL}
};

// Type definition
static PyTypeObject ProcSetType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "procset.ProcSet",                           // __name__
    .tp_doc = "C implementation of the ProcSet datatype",   // __doc__
    .tp_version_tag = 1,                                    // version
    .tp_basicsize = sizeof(ProcSetObject),                  // size of the struct
    .tp_itemsize = 0,                                       // additional size values for dynamic objects
    .tp_repr = (reprfunc) ProcSet_repr,                     // __repr__
    .tp_str = (reprfunc) ProcSet_str,                       // __str__
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   // flags, basetype is optional   
    .tp_new = (newfunc) ProcSet_new,                        // __new__
    .tp_init = (initproc) ProcSet_init,                     // __init__
    .tp_dealloc = (destructor) ProcSet_dealloc,             // Method called when the object is not referenced anymore, frees the memory and calls tp_free 
    .tp_methods = ProcSet_methods,                          // the list of defined methods for this object
    .tp_getset = ProcSet_getset,                            // the list of defined getters and setters
    .tp_as_sequence = &ProcSequenceMethods,                 // pointer to the sequence object
    .tp_richcompare = (richcmpfunc) ProcSet_richcompare,    // __le__, __eq__...
    .tp_as_number = &ProcSet_number_methods,                // __and__, __or__ ...
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
