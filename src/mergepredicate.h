#ifndef MERGE_PREDICATE_H_
#define MERGE_PREDICATE_H_

#include <stdbool.h> // C99

// type of the predicate function used in the merge algorithm
typedef bool (*MergePredicate)(bool, bool);


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


#endif
