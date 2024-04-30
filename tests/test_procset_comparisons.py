# -*- coding: utf-8 -*-

# Copyright © 2018, 2019
# Contributed by Raphaël Bleuse <cs@research.bleuse.net>
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


import collections
import pytest
from procset import ProcInt, ProcSet


_TestCase = collections.namedtuple(
    '_TestCase',
    ['doc', 'left', 'right', ]
)


class _TestComparison:
    method = None
    valid_types = None
    incompatible_types = None

    def test_comparison(self, testcase):
        left_pset = ProcSet(*testcase.left)
        right_pset = ProcSet(*testcase.right)

        # apply comparison method by name
        comparison = getattr(left_pset, self.method)(right_pset)
        set_comparison = getattr(set(left_pset), self.method)(set(right_pset))

        # check correctness of result
        assert isinstance(comparison, bool)
        assert comparison == set_comparison

    def test_valid_operand_type(self, valid):
        pset = ProcSet()

        # apply comparison method by name
        comparison = getattr(pset, self.method)(valid)

        # check correctness of result
        assert isinstance(comparison, bool)

    def test_incompatible_operand_type(self, incompatible):
        pset = ProcSet()

        # apply comparison method by name
        comparison = getattr(pset, self.method)(incompatible)

        # check correctness of result
        assert comparison is NotImplemented


class _TestComparisonNonOperator(_TestComparison):
    valid_types = (
        # empty iterable
        set(),
        (),
        # Iterable[int]
        ProcSet(0),
        ProcInt(0),
        {0},
        pytest.param((i*i for i in range(4)), id='(i*i for i in range(4))'),
        # Iterable[ProcInt]
        (ProcInt(0), ProcInt(1)),
        # Iterable[ProcSet]
        (ProcSet(0), ProcSet(1)),
        # Iterable[Union[int, ProcInt, ProcSet]]
        (0, ProcInt(1), ProcSet(2)),
    )
    incompatible_types = (
        # not iterable
        None,
        0,
        # iterable of wrong type
        'bad-iterable',
        {None},
        (0, ProcInt(1), None),
    )


class _TestComparisonOperator(_TestComparison):
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


# late-binding of parametrization with class-scope fixtures
# see https://docs.pytest.org/en/latest/example/parametrize.html#parametrizing-test-methods-through-per-class-configuration
def pytest_generate_tests(metafunc):
    if 'testcase' in metafunc.fixturenames:
        paramsdict = COMPARISON_TESTCASES
        ids, argvalues = zip(*paramsdict.items())  # {id: argvalue}, ensure id matches its argvalue
        metafunc.parametrize('testcase', argvalues, ids=ids)
    if 'valid' in metafunc.fixturenames:
        argvalues = metafunc.cls.valid_types
        metafunc.parametrize('valid', argvalues, ids=repr)
    if 'incompatible' in metafunc.fixturenames:
        argvalues = metafunc.cls.incompatible_types
        metafunc.parametrize('incompatible', argvalues, ids=repr)


# definition of test cases

COMPARISON_TESTCASES = {
    'before_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.........[_]....+∞
        """,
        (0, 1, 2, 3, ),
        (5, 6, 7, ),
    ),
    'before_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞...........X....+∞
        """,
        (0, 1, 2, 3, ),
        (7, ),
    ),
    'before_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........[__]....+∞
        """,
        (0, ),
        (4, 5, 6, 7, ),
    ),
    'before_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞........X.......+∞
        """,
        (0, ),
        (4, ),
    ),
    'before_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........[__]....+∞
        """,
        (0, 1, 2, 3, ),
        (4, 5, 6, 7, ),
    ),
    'before_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞........X.......+∞
        """,
        (0, 1, 2, 3, ),
        (4, ),
    ),
    'before_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....[_]........+∞
        """,
        (0, ),
        (1, 2, 3, ),
    ),
    'before_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞.....X..........+∞
        """,
        (0, ),
        (1, ),
    ),
    'meets_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞.......[___]....+∞
        """,
        (0, 1, 2, 3, ),
        (3, 4, 5, 6, 7, ),
    ),
    'overlaps_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[____]......+∞
        right: -∞......[____]....+∞
        """,
        (0, 1, 2, 3, 4, 5, ),
        (2, 3, 4, 5, 6, 7, ),
    ),
    'starts_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[______]....+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
    ),
    'starts_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....[__]........+∞
        """,
        (0, ),
        (0, 1, 2, 3, ),
    ),
    'containedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞....[______]....+∞
        """,
        (2, 3, 4, 5, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
    ),
    'containedby_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[______]....+∞
        """,
        (3, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
    ),
    'finishes_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....[______]....+∞
        """,
        (4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, 6, 7, ),
    ),
    'finishes_pi': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....[__]........+∞
        """,
        (3, ),
        (0, 1, 2, 3, ),
    ),
    'equal_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[__]........+∞
        right: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, ),
        (0, 1, 2, 3, ),
    ),
    'equal_pp': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....X...........+∞
        right: -∞....X...........+∞
        """,
        (0, ),
        (0, ),
    ),
    'finishedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........[__]....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, 5, 6, 7, ),
    ),
    'finishedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞...........X....+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (7, ),
    ),
    'contains_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞......[__]......+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (2, 3, 4, 5, ),
    ),
    'contains_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞........X.......+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (4, ),
    ),
    'startedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....[__]........+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, ),
    ),
    'startedby_ip': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[______]....+∞
        right: -∞....X...........+∞
        """,
        (0, 1, 2, 3, 4, 5, 6, 7, ),
        (0, ),
    ),
    'overlappedby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......[___]....+∞
        right: -∞....[____]......+∞
        """,
        (3, 4, 5, 6, 7, ),
        (0, 1, 2, 3, 4, 5, ),
    ),
    'metby_ii': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞....[___].......+∞
        right: -∞........[__]....+∞
        """,
        (0, 1, 3, 2, 4, ),
        (4, 5, 6, 7, ),
    ),
    'after_ii_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[]........+∞
        """,
        (6, 7, ),
        (2, 3, ),
    ),
    'after_pi_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[__]........+∞
        """,
        (5, ),
        (0, 1, 2, 3, ),
    ),
    'after_ip_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞....X...........+∞
        """,
        (4, 5, 6, 7, ),
        (0, ),
    ),
    'after_pp_notouch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞....X...........+∞
        """,
        (3, ),
        (0, ),
    ),
    'after_ii_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞..........[]....+∞
        right: -∞......[__]......+∞
        """,
        (6, 7, ),
        (2, 3, 4, 5, ),
    ),
    'after_pi_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.........X......+∞
        right: -∞....[___].......+∞
        """,
        (5, ),
        (0, 1, 2, 3, 4, ),
    ),
    'after_ip_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞........[__]....+∞
        right: -∞.......X........+∞
        """,
        (4, 5, 6, 7, ),
        (3, ),
    ),
    'after_pp_touch': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞......X.........+∞
        """,
        (3, ),
        (2, ),
    ),
    'firstempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞......[__]......+∞
        """,
        (),
        (2, 3, 4, 5, ),
    ),
    'firstempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞.......X........+∞
        """,
        (),
        (3, ),
    ),
    'secondempty_i': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞......[__]......+∞
        right: -∞................+∞
        """,
        (2, 3, 4, 5, ),
        (),
    ),
    'secondempty_p': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞.......X........+∞
        right: -∞................+∞
        """,
        (3, ),
        (),
    ),
    'bothempty': _TestCase(
        """
               -∞....01234567....+∞
        left:  -∞................+∞
        right: -∞................+∞
        """,
        (),
        (),
    ),
}


# link test cases to the actual methods

class TestIsDisjoint(_TestComparisonNonOperator):
    method = 'isdisjoint'


class TestIsSubset(_TestComparisonNonOperator):
    method = 'issubset'


class Test__LE__(_TestComparisonOperator):
    method = '__le__'


class Test__LT__(_TestComparisonOperator):
    method = '__lt__'


class TestIsSuperSet(_TestComparisonNonOperator):
    method = 'issuperset'


class Test__GE__(_TestComparisonOperator):
    method = '__ge__'


class Test__GT__(_TestComparisonOperator):
    method = '__gt__'
