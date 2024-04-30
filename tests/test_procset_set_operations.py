# -*- coding: utf-8 -*-

# Copyright © 2017, 2018
# Contributed by Raphaël Bleuse <raphael.bleuse@uni.lu>
#
# This file is part of procset.py, a pure python module to manage sets of
# closed intervals.
#
#   procset.py is free software: you can redistribute it and/or modify it
#   under the terms of the GNU Lesser General Public License version 3 only
#   as published by the Free Software Foundation.
#
#   procset.py is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License version 3 for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License version 3 along with this program.  If not, see
#   <https://www.gnu.org/licenses/>.


# The naming convention of the tests follows the one in the position paper by
# the IEEE Interval Standard Working Group - P1788.
# See docs/NehmeierM2010Interval.pdf for further informations.


# pylint: disable=too-many-lines


import collections
import itertools
import pytest
from procset import ProcInt, ProcSet


_TestCase = collections.namedtuple(
    '_TestCase',
    ['doc', 'left', 'right', 'expect_len', 'expect_count', 'expect_res']
)


def _powerset(*inputs):
    s = list(inputs)
    return list(
        itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    )


class _TestSetOperations:
    testcases = None
    merge_method = None
    inplace_method = None
    valid_types = None
    incompatible_types = None

    def test_merge(self, testcase):
        left_pset = ProcSet(*testcase.left)
        right_pset = ProcSet(*testcase.right)

        # apply merge method by name
        res_pset = getattr(left_pset, self.merge_method)(right_pset)

        # ensure we did not modify original operands
        assert left_pset == ProcSet(*testcase.left)
        assert right_pset == ProcSet(*testcase.right)

        # check correctness of result
        assert len(res_pset) == testcase.expect_len
        assert res_pset.count() == testcase.expect_count
        assert tuple(res_pset) == testcase.expect_res

    def test_inplace(self, testcase):
        left_pset = ProcSet(*testcase.left)
        left_orig = left_pset
        right_pset = ProcSet(*testcase.right)

        # apply inplace method by name
        left_pset = getattr(left_pset, self.inplace_method)(right_pset)

        # ensure we did not modify right operand
        assert right_pset == ProcSet(*testcase.right)

        # ensure we effectively modified in place the left operand
        assert left_pset is left_orig

        # check correctness of result
        assert len(left_pset) == testcase.expect_len
        assert left_pset.count() == testcase.expect_count
        assert tuple(left_pset) == testcase.expect_res


class _TestSetOperationsNonOperator(_TestSetOperations):
    valid_types = _powerset(
        0,
        ProcInt(1),
        ProcSet(2),
    )
    incompatible_types = (
        # not iterable
        (None, ),
        # iterable of wrong type
        ('bad-iterable', ),
        ((None, ), ),
        ((0, ProcInt(1), None), ),
    )

    def test_valid_operand_type(self, method, valid):
        pset = ProcSet()

        # apply merge method by name
        method = getattr(self, method)
        result = getattr(pset, method)(*valid)

        # check correctness of result
        assert isinstance(result, ProcSet)

    def test_incompatible_operand_type(self, method, incompatible):
        pset = ProcSet()

        # apply comparison method by name
        method = getattr(self, method)

        # check we properly raised
        with pytest.raises(TypeError):
            getattr(pset, method)(*incompatible)


class _TestSetOperationsOperator(_TestSetOperations):
    valid_types = (
        ProcSet(0),
    )
    incompatible_types = (
        # empty iterable
        set(),
        (),
        # Iterable[int]
        ProcInt(0),
        {0},
        pytest.param((i*i for i in range(4)), id='(i*i for i in range(4))'),
        # Iterable[ProcInt]
        (ProcInt(0), ProcInt(1)),
        # Iterable[ProcSet]
        (ProcSet(0), ProcSet(1)),
        # Iterable[Union[int, ProcInt, ProcSet]]
        (0, ProcInt(1), ProcSet(2)),
        # not iterable
        None,
        0,
        # iterable of wrong type
        'bad-iterable',
        {None},
        (0, ProcInt(1), None),
    )

    def test_valid_operand_type(self, method, valid):
        pset = ProcSet()

        # apply merge method by name
        method = getattr(self, method)
        result = getattr(pset, method)(valid)

        # check correctness of result
        assert isinstance(result, ProcSet)

    def test_incompatible_operand_type(self, method, incompatible):
        pset = ProcSet()

        # apply comparison method by name
        method = getattr(self, method)
        result = getattr(pset, method)(incompatible)

        # check correctness of result
        assert result is NotImplemented


# late-binding of parametrization with class-scope fixtures
# see https://docs.pytest.org/en/latest/example/parametrize.html#parametrizing-test-methods-through-per-class-configuration
def pytest_generate_tests(metafunc):
    if 'testcase' in metafunc.fixturenames:
        paramsdict = metafunc.cls.testcases
        ids, argvalues = zip(*paramsdict.items())  # {id: argvalue}, ensure id matches its argvalue
        metafunc.parametrize('testcase', argvalues, ids=ids)
    if 'method' in metafunc.fixturenames:
        argvalues = ('merge_method', 'inplace_method', )
        metafunc.parametrize('method', argvalues)
    if 'valid' in metafunc.fixturenames:
        argvalues = metafunc.cls.valid_types
        metafunc.parametrize('valid', argvalues, ids=repr)
    if 'incompatible' in metafunc.fixturenames:
        argvalues = metafunc.cls.incompatible_types
        metafunc.parametrize('incompatible', argvalues, ids=repr)


# definition of test cases

DIFFERENCE_TESTCASES = {
    'before_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.........[_]....+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, ),
        (5, 6, 7, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'before_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞...........X....+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, ),
        (7, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'before_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........[__]....+∞
        final: -∞....X...........+∞
        """,
        (0, ),
        (4, 5, 6, 7, ),
        1,
        1,
        (0, )
    ),
    'before_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........X.......+∞
        final: -∞....X...........+∞
        """,
        (0, ),
        (4, ),
        1,
        1,
        (0, )
    ),
    'before_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........[__]....+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, ),
        (4, 5, 6, 7, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'before_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........X.......+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, ),
        (4, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'before_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....[_]........+∞
        final: -∞....X...........+∞
        """,
        (0, ),
        (1, 2, 3, ),
        1,
        1,
        (0, )
    ),
    'before_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....X..........+∞
        final: -∞....X...........+∞
        """,
        (0, ),
        (1, ),
        1,
        1,
        (0, )
    ),
    'meets_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.......[___]....+∞
        final: -∞....[_].........+∞
        """,
        (0, 1, 2, 3, ),
        (3, 4, 5, 6, 7, ),
        3,
        1,
        (0, 1, 2, )
    ),
    'overlaps_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[____]......+∞
        right: -∞......[____]....+∞
        final: -∞....[]..........+∞
        """,
        (0, 1, 2, 3, 4, 5, ),
        (2, 3, 4, 5, 6, 7, ),
        2,
        1,
        (0, 1, )
    ),
    'starts_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[______]....+∞
        final: -∞................+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        0,
        0,
        ()
    ),
    'starts_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....[__]........+∞
        final: -∞................+∞
        """,
        (0, ),
        (0, 1, 2, 3, ),
        0,
        0,
        ()
    ),
    'containedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞....[______]....+∞
        final: -∞................+∞
        """,
        (2, 3, 4, 5, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        0,
        0,
        ()
    ),
    'containedby_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[______]....+∞
        final: -∞................+∞
        """,
        (3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        0,
        0,
        ()
    ),
    'finishes_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....[______]....+∞
        final: -∞................+∞
        """,
        (4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        0,
        0,
        ()
    ),
    'finishes_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[__]........+∞
        final: -∞................+∞
        """,
        (3, ),
        (0, 1, 2, 3, ),
        0,
        0,
        ()
    ),
    'equal_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[__]........+∞
        final: -∞................+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, ),
        0,
        0,
        ()
    ),
    'equal_pp': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....X...........+∞
        final: -∞................+∞
        """,
        (0, ),
        (0, ),
        0,
        0,
        ()
    ),
    'finishedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........[__]....+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, 5, 6, 7, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'finishedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞...........X....+∞
        final: -∞....[_____].....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (7, ),
        7,
        1,
        (0, 1, 2, 3, 4, 5, 6, )
    ),
    'contains_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞......[__]......+∞
        final: -∞....[]....[]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (2, 3, 4, 5, ),
        4,
        2,
        (0, 1, 6, 7, )
    ),
    'contains_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........X.......+∞
        final: -∞....[__].[_]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, ),
        7,
        2,
        (0, 1, 2, 3, 5, 6, 7, )
    ),
    'startedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....[__]........+∞
        final: -∞........[__]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, ),
        4,
        1,
        (4, 5, 6, 7, )
    ),
    'startedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....X...........+∞
        final: -∞.....[_____]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, ),
        7,
        1,
        (1, 2, 3, 4, 5, 6, 7, )
    ),
    'overlappedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......[___]....+∞
        right: -∞....[____]......+∞
        final: -∞..........[]....+∞
        """,
        (3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, ),
        2,
        1,
        (6, 7, )
    ),
    'metby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[___].......+∞
        right: -∞........[__]....+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, 4, ),
        (4, 5, 6, 7, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'after_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[]........+∞
        final: -∞..........[]....+∞
        """,
        (6, 7, ),
        (2, 3, ),
        2,
        1,
        (6, 7, )
    ),
    'after_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[__]........+∞
        final: -∞.........X......+∞
        """,
        (5, ),
        (0, 1, 2, 3, ),
        1,
        1,
        (5, )
    ),
    'after_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....X...........+∞
        final: -∞........[__]....+∞
        """,
        (4, 5, 6, 7, ),
        (0, ),
        4,
        1,
        (4, 5, 6, 7, )
    ),
    'after_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....X...........+∞
        final: -∞.......X........+∞
        """,
        (3, ),
        (0, ),
        1,
        1,
        (3, )
    ),
    'after_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[__]......+∞
        final: -∞..........[]....+∞
        """,
        (6, 7, ),
        (2, 3, 4, 5, ),
        2,
        1,
        (6, 7, )
    ),
    'after_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[___].......+∞
        final: -∞.........X......+∞
        """,
        (5, ),
        (0, 1, 2, 3, 4, ),
        1,
        1,
        (5, )
    ),
    'after_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞.......X........+∞
        final: -∞........[__]....+∞
        """,
        (4, 5, 6, 7, ),
        (3, ),
        4,
        1,
        (4, 5, 6, 7, )
    ),
    'after_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞......X.........+∞
        final: -∞.......X........+∞
        """,
        (3, ),
        (2, ),
        1,
        1,
        (3, )
    ),
    'firstempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞......[__]......+∞
        final: -∞................+∞
        """,
        (),
        (2, 3, 4, 5, ),
        0,
        0,
        ()
    ),
    'firstempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞.......X........+∞
        final: -∞................+∞
        """,
        (),
        (3, ),
        0,
        0,
        ()
    ),
    'secondempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞................+∞
        final: -∞......[__]......+∞
        """,
        (2, 3, 4, 5, ),
        (),
        4,
        1,
        (2, 3, 4, 5, )
    ),
    'secondempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞................+∞
        final: -∞.......X........+∞
        """,
        (3, ),
        (),
        1,
        1,
        (3, )
    ),
    'bothempty': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞................+∞
        final: -∞................+∞
        """,
        (),
        (),
        0,
        0,
        ()
    ),
}


INTERSECTION_TESTCASES = {
    'before_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.........[_]....+∞
        final: -∞................+∞
        """,
        (0, 1, 2, 3, ),
        (5, 6, 7, ),
        0,
        0,
        ()
    ),
    'before_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞...........X....+∞
        final: -∞................+∞
        """,
        (0, 1, 2, 3, ),
        (7, ),
        0,
        0,
        ()
    ),
    'before_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........[__]....+∞
        final: -∞................+∞
        """,
        (0, ),
        (4, 5, 6, 7, ),
        0,
        0,
        ()
    ),
    'before_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........X.......+∞
        final: -∞................+∞
        """,
        (0, ),
        (4, ),
        0,
        0,
        ()
    ),
    'before_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........[__]....+∞
        final: -∞................+∞
        """,
        (0, 1, 2, 3, ),
        (4, 5, 6, 7, ),
        0,
        0,
        ()
    ),
    'before_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........X.......+∞
        final: -∞................+∞
        """,
        (0, 1, 2, 3, ),
        (4, ),
        0,
        0,
        ()
    ),
    'before_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....[_]........+∞
        final: -∞................+∞
        """,
        (0, ),
        (1, 2, 3, ),
        0,
        0,
        ()
    ),
    'before_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....X..........+∞
        final: -∞................+∞
        """,
        (0, ),
        (1, ),
        0,
        0,
        ()
    ),
    'meets_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.......[___]....+∞
        final: -∞.......X........+∞
        """,
        (0, 1, 2, 3, ),
        (3, 4, 5, 6, 7, ),
        1,
        1,
        (3, )
    ),
    'overlaps_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[____]......+∞
        right: -∞......[____]....+∞
        final: -∞......[__]......+∞
        """,
        (0, 1, 2, 3, 4, 5, ),
        (2, 3, 4, 5, 6, 7, ),
        4,
        1,
        (2, 3, 4, 5, )
    ),
    'starts_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[______]....+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'starts_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....[__]........+∞
        final: -∞....X...........+∞
        """,
        (0, ),
        (0, 1, 2, 3, ),
        1,
        1,
        (0, )
    ),
    'containedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞....[______]....+∞
        final: -∞......[__]......+∞
        """,
        (2, 3, 4, 5, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        4,
        1,
        (2, 3, 4, 5, )
    ),
    'containedby_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[______]....+∞
        final: -∞.......X........+∞
        """,
        (3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        1,
        1,
        (3, )
    ),
    'finishes_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....[______]....+∞
        final: -∞........[__]....+∞
        """,
        (4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        4,
        1,
        (4, 5, 6, 7, )
    ),
    'finishes_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[__]........+∞
        final: -∞.......X........+∞
        """,
        (3, ),
        (0, 1, 2, 3, ),
        1,
        1,
        (3, )
    ),
    'equal_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[__]........+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'equal_pp': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....X...........+∞
        final: -∞....X...........+∞
        """,
        (0, ),
        (0, ),
        1,
        1,
        (0, )
    ),
    'finishedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........[__]....+∞
        final: -∞........[__]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, 5, 6, 7, ),
        4,
        1,
        (4, 5, 6, 7, )
    ),
    'finishedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞...........X....+∞
        final: -∞...........X....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (7, ),
        1,
        1,
        (7, )
    ),
    'contains_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞......[__]......+∞
        final: -∞......[__]......+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (2, 3, 4, 5, ),
        4,
        1,
        (2, 3, 4, 5, )
    ),
    'contains_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........X.......+∞
        final: -∞........X.......+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, ),
        1,
        1,
        (4, )
    ),
    'startedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....[__]........+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'startedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....X...........+∞
        final: -∞....X...........+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, ),
        1,
        1,
        (0, )
    ),
    'overlappedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......[___]....+∞
        right: -∞....[____]......+∞
        final: -∞.......[_]......+∞
        """,
        (3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, ),
        3,
        1,
        (3, 4, 5, )
    ),
    'metby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[___].......+∞
        right: -∞........[__]....+∞
        final: -∞........X.......+∞
        """,
        (0, 1, 3, 2, 4, ),
        (4, 5, 6, 7, ),
        1,
        1,
        (4, )
    ),
    'after_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[]........+∞
        final: -∞................+∞
        """,
        (6, 7, ),
        (2, 3, ),
        0,
        0,
        ()
    ),
    'after_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[__]........+∞
        final: -∞................+∞
        """,
        (5, ),
        (0, 1, 2, 3, ),
        0,
        0,
        ()
    ),
    'after_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....X...........+∞
        final: -∞................+∞
        """,
        (4, 5, 6, 7, ),
        (0, ),
        0,
        0,
        ()
    ),
    'after_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....X...........+∞
        final: -∞................+∞
        """,
        (3, ),
        (0, ),
        0,
        0,
        ()
    ),
    'after_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[__]......+∞
        final: -∞................+∞
        """,
        (6, 7, ),
        (2, 3, 4, 5, ),
        0,
        0,
        ()
    ),
    'after_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[___].......+∞
        final: -∞................+∞
        """,
        (5, ),
        (0, 1, 2, 3, 4, ),
        0,
        0,
        ()
    ),
    'after_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞.......X........+∞
        final: -∞................+∞
        """,
        (4, 5, 6, 7, ),
        (3, ),
        0,
        0,
        ()
    ),
    'after_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞......X.........+∞
        final: -∞................+∞
        """,
        (3, ),
        (2, ),
        0,
        0,
        ()
    ),
    'firstempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞......[__]......+∞
        final: -∞................+∞
        """,
        (),
        (2, 3, 4, 5, ),
        0,
        0,
        ()
    ),
    'firstempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞.......X........+∞
        final: -∞................+∞
        """,
        (),
        (3, ),
        0,
        0,
        ()
    ),
    'secondempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞................+∞
        final: -∞................+∞
        """,
        (2, 3, 4, 5, ),
        (),
        0,
        0,
        ()
    ),
    'secondempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞................+∞
        final: -∞................+∞
        """,
        (3, ),
        (),
        0,
        0,
        ()
    ),
    'bothempty': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞................+∞
        final: -∞................+∞
        """,
        (),
        (),
        0,
        0,
        ()
    ),
}


SYMMETRIC_DIFFERENCE_TESTCASES = {
    'before_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.........[_]....+∞
        final: -∞....[__] [_]....+∞
        """,
        (0, 1, 2, 3, ),
        (5, 6, 7, ),
        7,
        2,
        (0, 1, 2, 3, 5, 6, 7, )
    ),
    'before_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞...........X....+∞
        final: -∞....[__]...X....+∞
        """,
        (0, 1, 2, 3, ),
        (7, ),
        5,
        2,
        (0, 1, 2, 3, 7, )
    ),
    'before_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........[__]....+∞
        final: -∞....X...[__]....+∞
        """,
        (0, ),
        (4, 5, 6, 7, ),
        5,
        2,
        (0, 4, 5, 6, 7, )
    ),
    'before_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........X.......+∞
        final: -∞....X...X.......+∞
        """,
        (0, ),
        (4, ),
        2,
        2,
        (0, 4, )
    ),
    'before_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........[__]....+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, ),
        (4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'before_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........X.......+∞
        final: -∞....[___].......+∞
        """,
        (0, 1, 2, 3, ),
        (4, ),
        5,
        1,
        (0, 1, 2, 3, 4, )
    ),
    'before_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....[_]........+∞
        final: -∞....[__]........+∞
        """,
        (0, ),
        (1, 2, 3, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'before_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....X..........+∞
        final: -∞....[]..........+∞
        """,
        (0, ),
        (1, ),
        2,
        1,
        (0, 1, )
    ),
    'meets_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.......[___]....+∞
        final: -∞....[_].[__]....+∞
        """,
        (0, 1, 2, 3, ),
        (3, 4, 5, 6, 7, ),
        7,
        2,
        (0, 1, 2, 4, 5, 6, 7, )
    ),
    'overlaps_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[____]......+∞
        right: -∞......[____]....+∞
        final: -∞....[]....[]....+∞
        """,
        (0, 1, 2, 3, 4, 5, ),
        (2, 3, 4, 5, 6, 7, ),
        4,
        2,
        (0, 1, 6, 7, )
    ),
    'starts_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[______]....+∞
        final: -∞........[__]....+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        4,
        1,
        (4, 5, 6, 7, )
    ),
    'starts_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....[__]........+∞
        final: -∞.....[_]........+∞
        """,
        (0, ),
        (0, 1, 2, 3, ),
        3,
        1,
        (1, 2, 3, )
    ),
    'containedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞....[______]....+∞
        final: -∞....[]....[]....+∞
        """,
        (2, 3, 4, 5, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        4,
        2,
        (0, 1, 6, 7, )
    ),
    'containedby_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[______]....+∞
        final: -∞....[_].[__]....+∞
        """,
        (3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        7,
        2,
        (0, 1, 2, 4, 5, 6, 7, )
    ),
    'finishes_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....[______]....+∞
        final: -∞....[__]........+∞
        """,
        (4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'finishes_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[__]........+∞
        final: -∞....[_].........+∞
        """,
        (3, ),
        (0, 1, 2, 3, ),
        3,
        1,
        (0, 1, 2, )
    ),
    'equal_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[__]........+∞
        final: -∞................+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, ),
        0,
        0,
        ()
    ),
    'equal_pp': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....X...........+∞
        final: -∞................+∞
        """,
        (0, ),
        (0, ),
        0,
        0,
        ()
    ),
    'finishedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........[__]....+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, 5, 6, 7, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'finishedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞...........X....+∞
        final: -∞....[_____].....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (7, ),
        7,
        1,
        (0, 1, 2, 3, 4, 5, 6, )
    ),
    'contains_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞......[__]......+∞
        final: -∞....[]....[]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (2, 3, 4, 5, ),
        4,
        2,
        (0, 1, 6, 7, )
    ),
    'contains_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........X.......+∞
        final: -∞....[__].[_]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, ),
        7,
        2,
        (0, 1, 2, 3, 5, 6, 7, )
    ),
    'startedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....[__]........+∞
        final: -∞........[__]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, ),
        4,
        1,
        (4, 5, 6, 7, )
    ),
    'startedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....X...........+∞
        final: -∞.....[_____]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, ),
        7,
        1,
        (1, 2, 3, 4, 5, 6, 7, )
    ),
    'overlappedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......[___]....+∞
        right: -∞....[____]......+∞
        final: -∞....[_]...[]....+∞
        """,
        (3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, ),
        5,
        2,
        (0, 1, 2, 6, 7, )
    ),
    'metby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[___].......+∞
        right: -∞........[__]....+∞
        final: -∞....[__].[_]....+∞
        """,
        (0, 1, 2, 3, 4, ),
        (4, 5, 6, 7, ),
        7,
        2,
        (0, 1, 2, 3, 5, 6, 7, )
    ),
    'after_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[]........+∞
        final: -∞......[]..[]....+∞
        """,
        (6, 7, ),
        (2, 3, ),
        4,
        2,
        (2, 3, 6, 7, )
    ),
    'after_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[__]........+∞
        final: -∞....[__].X......+∞
        """,
        (5, ),
        (0, 1, 2, 3, ),
        5,
        2,
        (0, 1, 2, 3, 5, )
    ),
    'after_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....X...........+∞
        final: -∞....X...[__]....+∞
        """,
        (4, 5, 6, 7, ),
        (0, ),
        5,
        2,
        (0, 4, 5, 6, 7, )
    ),
    'after_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....X...........+∞
        final: -∞....X..X........+∞
        """,
        (3, ),
        (0, ),
        2,
        2,
        (0, 3, )
    ),
    'after_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[__]......+∞
        final: -∞......[____]....+∞
        """,
        (6, 7, ),
        (2, 3, 4, 5, ),
        6,
        1,
        (2, 3, 4, 5, 6, 7, )
    ),
    'after_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[___].......+∞
        final: -∞....[____]......+∞
        """,
        (5, ),
        (0, 1, 2, 3, 4, ),
        6,
        1,
        (0, 1, 2, 3, 4, 5, )
    ),
    'after_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞.......X........+∞
        final: -∞.......[___]....+∞
        """,
        (4, 5, 6, 7, ),
        (3, ),
        5,
        1,
        (3, 4, 5, 6, 7, )
    ),
    'after_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞......X.........+∞
        final: -∞......[]........+∞
        """,
        (3, ),
        (2, ),
        2,
        1,
        (2, 3, )
    ),
    'firstempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞......[__]......+∞
        final: -∞......[__]......+∞
        """,
        (),
        (2, 3, 4, 5, ),
        4,
        1,
        (2, 3, 4, 5, )
    ),
    'firstempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞.......X........+∞
        final: -∞.......X........+∞
        """,
        (),
        (3, ),
        1,
        1,
        (3, )
    ),
    'secondempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞................+∞
        final: -∞......[__]......+∞
        """,
        (2, 3, 4, 5, ),
        (),
        4,
        1,
        (2, 3, 4, 5, )
    ),
    'secondempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞................+∞
        final: -∞.......X........+∞
        """,
        (3, ),
        (),
        1,
        1,
        (3, )
    ),
    'bothempty': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞................+∞
        final: -∞................+∞
        """,
        (),
        (),
        0,
        0,
        ()
    ),
}


UNION_TESTCASES = {
    'before_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.........[_]....+∞
        final: -∞....[__].[_]....+∞
        """,
        (0, 1, 2, 3, ),
        (5, 6, 7, ),
        7,
        2,
        (0, 1, 2, 3, 5, 6, 7, )
    ),
    'before_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞...........X....+∞
        final: -∞....[__]...X....+∞
        """,
        (0, 1, 2, 3, ),
        (7, ),
        5,
        2,
        (0, 1, 2, 3, 7, )
    ),
    'before_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........[__]....+∞
        final: -∞....X...[__]....+∞
        """,
        (0, ),
        (4, 5, 6, 7, ),
        5,
        2,
        (0, 4, 5, 6, 7, )
    ),
    'before_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........X.......+∞
        final: -∞....X...X.......+∞
        """,
        (0, ),
        (4, ),
        2,
        2,
        (0, 4, )
    ),
    'before_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........[__]....+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, ),
        (4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'before_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........X.......+∞
        final: -∞....[___].......+∞
        """,
        (0, 1, 2, 3, ),
        (4, ),
        5,
        1,
        (0, 1, 2, 3, 4, )
    ),
    'before_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....[_]........+∞
        final: -∞....[__]........+∞
        """,
        (0, ),
        (1, 2, 3, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'before_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....X..........+∞
        final: -∞....[]..........+∞
        """,
        (0, ),
        (1, ),
        2,
        1,
        (0, 1, )
    ),
    'meets_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.......[___]....+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, ),
        (3, 4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'overlaps_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[____]......+∞
        right: -∞......[____]....+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, 4, 5, ),
        (2, 3, 4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'starts_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[______]....+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'starts_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....[__]........+∞
        final: -∞....[__]........+∞
        """,
        (0, ),
        (0, 1, 2, 3, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'containedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞....[______]....+∞
        final: -∞....[______]....+∞
        """,
        (2, 3, 4, 5, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'containedby_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[______]....+∞
        final: -∞....[______]....+∞
        """,
        (3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'finishes_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....[______]....+∞
        final: -∞....[______]....+∞
        """,
        (4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'finishes_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[__]........+∞
        final: -∞....[__]........+∞
        """,
        (3, ),
        (0, 1, 2, 3, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'equal_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[__]........+∞
        final: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, ),
        4,
        1,
        (0, 1, 2, 3, )
    ),
    'equal_pp': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....X...........+∞
        final: -∞....X...........+∞
        """,
        (0, ),
        (0, ),
        1,
        1,
        (0, )
    ),
    'finishedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........[__]....+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'finishedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞...........X....+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 3, 2, 4, 5, 6, 7, ),
        (7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'contains_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞......[__]......+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (2, 3, 4, 5, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'contains_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........X.......+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, 4, 6, 5, 7, ),
        (4, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'startedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....[__]........+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'startedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....X...........+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'overlappedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......[___]....+∞
        right: -∞....[____]......+∞
        final: -∞....[______]....+∞
        """,
        (3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'metby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[___].......+∞
        right: -∞........[__]....+∞
        final: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, 4, ),
        (4, 5, 6, 7, ),
        8,
        1,
        (0, 1, 2, 3, 4, 5, 6, 7, )
    ),
    'after_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[]........+∞
        final: -∞......[]..[]....+∞
        """,
        (6, 7, ),
        (2, 3, ),
        4,
        2,
        (2, 3, 6, 7, )
    ),
    'after_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[__]........+∞
        final: -∞....[__].X......+∞
        """,
        (5, ),
        (0, 1, 2, 3, ),
        5,
        2,
        (0, 1, 2, 3, 5, )
    ),
    'after_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....X...........+∞
        final: -∞....X...[__]....+∞
        """,
        (4, 5, 6, 7, ),
        (0, ),
        5,
        2,
        (0, 4, 5, 6, 7, )
    ),
    'after_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....X...........+∞
        final: -∞....X..X........+∞
        """,
        (3, ),
        (0, ),
        2,
        2,
        (0, 3, )
    ),
    'after_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[__]......+∞
        final: -∞......[____]....+∞
        """,
        (6, 7, ),
        (2, 3, 4, 5, ),
        6,
        1,
        (2, 3, 4, 5, 6, 7, )
    ),
    'after_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[___].......+∞
        final: -∞....[____]......+∞
        """,
        (5, ),
        (0, 1, 2, 3, 4, ),
        6,
        1,
        (0, 1, 2, 3, 4, 5, )
    ),
    'after_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞.......X........+∞
        final: -∞.......[___]....+∞
        """,
        (4, 5, 6, 7, ),
        (3, ),
        5,
        1,
        (3, 4, 5, 6, 7, )
    ),
    'after_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞......X.........+∞
        final: -∞......[]........+∞
        """,
        (3, ),
        (2, ),
        2,
        1,
        (2, 3, )
    ),
    'firstempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞......[__]......+∞
        final: -∞......[__]......+∞
        """,
        (),
        (2, 3, 4, 5, ),
        4,
        1,
        (2, 3, 4, 5, )
    ),
    'firstempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞.......X........+∞
        final: -∞.......X........+∞
        """,
        (),
        (3, ),
        1,
        1,
        (3, )
    ),
    'secondempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞................+∞
        final: -∞......[__]......+∞
        """,
        (2, 3, 4, 5, ),
        (),
        4,
        1,
        (2, 3, 4, 5, )
    ),
    'secondempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞................+∞
        final: -∞.......X........+∞
        """,
        (3, ),
        (),
        1,
        1,
        (3, )
    ),
    'bothempty': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞................+∞
        final: -∞................+∞
        """,
        (),
        (),
        0,
        0,
        ()
    ),
}


# link test cases to the actual methods

class TestDifference(_TestSetOperationsNonOperator):
    testcases = DIFFERENCE_TESTCASES
    merge_method = 'difference'
    inplace_method = 'difference_update'


class Test__SUB__(_TestSetOperationsOperator):
    testcases = DIFFERENCE_TESTCASES
    merge_method = '__sub__'
    inplace_method = '__isub__'


class TestIntersection(_TestSetOperationsNonOperator):
    testcases = INTERSECTION_TESTCASES
    merge_method = 'intersection'
    inplace_method = 'intersection_update'


class Test__AND__(_TestSetOperationsOperator):
    testcases = INTERSECTION_TESTCASES
    merge_method = '__and__'
    inplace_method = '__iand__'


class TestSymmetricDifference(_TestSetOperationsNonOperator):
    testcases = SYMMETRIC_DIFFERENCE_TESTCASES
    merge_method = 'symmetric_difference'
    inplace_method = 'symmetric_difference_update'
    # need to redefine valid_types/incompatible_types because of the method signature
    valid_types = (
        (0, ),
        (ProcInt(1), ),
        (ProcSet(2), ),
    )
    incompatible_types = (
        # not iterable
        (None, ),
        # iterable of wrong type
        ('bad-iterable', ),
        ((None, ), ),
        ((0, ProcInt(1), None), ),
    )


class Test__XOR__(_TestSetOperationsOperator):
    testcases = SYMMETRIC_DIFFERENCE_TESTCASES
    merge_method = '__xor__'
    inplace_method = '__ixor__'


class TestUnion(_TestSetOperationsNonOperator):
    testcases = UNION_TESTCASES
    merge_method = 'union'
    inplace_method = 'update'


class Test__OR__(_TestSetOperationsOperator):
    testcases = UNION_TESTCASES
    merge_method = '__or__'
    inplace_method = '__ior__'
