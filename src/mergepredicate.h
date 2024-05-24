#ifndef MERGE_PREDICATE_H_
#define MERGE_PREDICATE_H_

#include <stdbool.h> // C99

#if PYTHON_API_VERSION < 1100
#define Py_ALWAYS_INLINE 
#endif


// type of the predicate function used in the merge algorithm
typedef bool (*MergePredicate)(bool, bool);


static inline Py_ALWAYS_INLINE bool bitwiseUnion(bool inLeft, bool inRight) {
    return inLeft | inRight;
}

static inline Py_ALWAYS_INLINE bool bitwiseIntersection(bool inLeft, bool inRight) {
    return inLeft & inRight;
}

static inline Py_ALWAYS_INLINE bool bitwiseDifference(bool inLeft, bool inRight) {
    return inLeft & (!inRight);
}

static inline Py_ALWAYS_INLINE bool bitwiseSymmetricDifference(bool inLeft, bool inRight) {
    return inLeft ^ inRight;
}


#endif
