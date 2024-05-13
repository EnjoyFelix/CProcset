#ifndef PROCSET_HEADER_H_
#define PROCSET_HEADER_H_


#define PY_SSIZE_T_CLEAN
#include <Python.h>

//#define PSET_DEBUG

typedef uint32_t pset_boundary_t;
pset_boundary_t MAX_BOUND_VALUE = UINT32_MAX;

// Definition of the ProcSet struct
typedef struct {
    // Python object boilerplate
    PyObject_HEAD

    // Boundaries of the ProcSet paired two by two as half-opened intervals
    pset_boundary_t *_boundaries;   

    // pointer to the Number of boundaries, (2x nbr of intervals)
    // --> has to be a pointer because of shallow copies
    Py_ssize_t nb_boundary;
} ProcSetObject;


// a method that resizes and
// nb_elements should always be > 0
static int
pset_resize(ProcSetObject* pset, Py_ssize_t nb_elements){
 
    // if the destination is smaller than the source: we need to allocate more memory
    if (pset->nb_boundary < nb_elements){
        pset_boundary_t * temp = PyMem_Realloc(pset->_boundaries, nb_elements * sizeof(pset_boundary_t));

        if (!temp){
            //we dont check for previous py errors since they would have been caught in the "if !result"
            PyErr_NoMemory();   // set the error message
            return 0;           // return false
        }

        // we replace the adress if the new one is valid
        // it could also be the same but we replace it anyway
        pset->_boundaries = temp;        
    } 

    // if our list is bigger than the result's list
    else if (pset->nb_boundary > nb_elements){
        // we release the allocated memory for self->boundaries
        // we cannot use realloc here because data was written outside of [0, nb_elements], so realloc would fail
        PyMem_Free(pset->_boundaries);

        // we allocate the amount of memory (i don't think this one can fail, we literally just freed more than enough memory)
        pset->_boundaries = (pset_boundary_t * ) PyMem_Malloc(pset->nb_boundary * sizeof(pset_boundary_t));
    }
    //we don't do anything if the sizes are equals

    return 1;
}

static int
pset_copy(ProcSetObject* src, ProcSetObject *destination, Py_ssize_t nb_elements){
    for (Py_ssize_t i = 0; i < nb_elements; i++){
        destination->_boundaries[i] = src->_boundaries[i];
    }

    return 1;
}

#ifdef PSET_DEBUG
static void
debug_printprocset(ProcSetObject * self, Py_ssize_t predicted_elements){
    printf("procset @%p:\n", (void *) self);
    printf("size : %li, predicted: %li\n", self->nb_boundary, predicted_elements);

    for (int i = 0; i < self->nb_boundary; i+=2){
        printf("\t%u - %u\n", self->_boundaries[i], self->_boundaries[i+1]);
    }
}
#endif
#endif
