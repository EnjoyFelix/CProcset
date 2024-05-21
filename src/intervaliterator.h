#ifndef __PROCSET_INTERVALITER_H_
#define __PROCSET_INTERVALITER_H_

#include "procsetheader.h"

static PyTypeObject IntervalIterType;

typedef struct {
    PyObject_HEAD           // python object boilerplate
    Py_ssize_t i;           // la position actuelle
    Py_ssize_t max;         // position max
    ProcSetObject * obj;
} IntervalIterator;

static PyObject *
IntervalIterator_new (ProcSetObject* self){
    #ifdef PSET_DEBUG
    printf("(IntervalIterator) New iterator object @%p\n", (void *) self);
    #endif
    // a new iterator
    IntervalIterator * iter = (IntervalIterator *) IntervalIterType.tp_alloc(&IntervalIterType, 0);
    if (!iter){
        return NULL;
    }

    // we set the values for the iterator
    iter->i = 0;
    iter->max = self->nb_boundary;
    
    Py_INCREF(self);
    iter->obj = self;

    return (PyObject *) iter;
}

static PyObject *
IntervalIterator_iter(PyObject * self){
    Py_IncRef(self);
    #ifdef PSET_DEBUG
    printf("(IntervalIterator) iterator @%p is held by %li refs\n", (void *) self, Py_REFCNT(self));
    #endif
    return self;
}

static PyObject *
IntervalIterator_next(IntervalIterator* self){
    // if self is null;
    if (!self || !self->obj){
        //TODO: REAL ERROR MESSAGE
        return NULL;
    } 
    
    // early termination if the iteration is over
    else if (self->i >= self->max){
        Py_DECREF(self->obj);   // the iterator holds a strong reference so we have to decref
        self->obj = NULL;
        return NULL;
    }

    // to make it easier to read
    pset_boundary_t a = self->obj->_boundaries[self->i];
    pset_boundary_t b = self->obj->_boundaries[self->i+1] -1 ;

    // we set the values
    PyObject * tuple = PyTuple_New(2);
    PyTuple_SetItem(tuple, 0, PyLong_FromDouble(a));
    PyTuple_SetItem(tuple, 1, PyLong_FromDouble(b));

    self->i +=2;        // on avance
    return tuple;
}

static void
IntervalIterator_dealloc(IntervalIterator * self){
    #ifdef PSET_DEBUG
    printf("(IntervalIterator) Calling dealloc on iterator object @%p\n", (void *) self);
    #endif

    Py_XDECREF(self->obj);
    IntervalIterType.tp_free((PyObject *) self);
}

static PyTypeObject IntervalIterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "interval_iterator",
    .tp_basicsize = sizeof(IntervalIterator),
    .tp_dealloc = (destructor) IntervalIterator_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT /* | Py_TPFLAGS_HAVE_GC */,
    .tp_iter = (getiterfunc) IntervalIterator_iter,
    .tp_iternext = (iternextfunc) IntervalIterator_next,
} 


// PyTypeObject PySetIter_Type = {
//     PyVarObject_HEAD_INIT(&PyType_Type, 0)
//     "set_iterator",                             /* tp_name */
//     sizeof(setiterobject),                      /* tp_basicsize */
//     0,                                          /* tp_itemsize */
//     /* methods */
//     (destructor)setiter_dealloc,                /* tp_dealloc */
//     0,                                          /* tp_vectorcall_offset */
//     0,                                          /* tp_getattr */
//     0,                                          /* tp_setattr */
//     0,                                          /* tp_as_async */
//     0,                                          /* tp_repr */
//     0,                                          /* tp_as_number */
//     0,                                          /* tp_as_sequence */
//     0,                                          /* tp_as_mapping */
//     0,                                          /* tp_hash */
//     0,                                          /* tp_call */
//     0,                                          /* tp_str */
//     PyObject_GenericGetAttr,                    /* tp_getattro */
//     0,                                          /* tp_setattro */
//     0,                                          /* tp_as_buffer */
//     Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,    /* tp_flags */
//     0,                                          /* tp_doc */
//     (traverseproc)setiter_traverse,             /* tp_traverse */
//     0,                                          /* tp_clear */
//     0,                                          /* tp_richcompare */
//     0,                                          /* tp_weaklistoffset */
//     PyObject_SelfIter,                          /* tp_iter */
//     (iternextfunc)setiter_iternext,             /* tp_iternext */
//     setiter_methods,                            /* tp_methods */
//     0,
// };

#endif
;