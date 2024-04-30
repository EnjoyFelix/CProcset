# -*- coding: utf-8 -*-

# Copyright © 2017—2019
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

import copy
import itertools
import pytest
from procset import ProcInt, ProcSet


# used by {TestNew,TestInsert}::test_incompatible_iter_length
INCOMPATIBLE_ITER_LENGTH_TESTCASES = (
    (),  # length < 2
    '',
    (0, ),
    '1',
    (0, 1, 2, ),  # length > 2
    '1-2',
)
# used by {TestNew,TestInsert}::test_incompatible_iter_type
INCOMPATIBLE_ITER_TYPE_TESTCASES = (
    '12',
    ('0', 1),
    (0, '1'),
)


# pylint: disable=no-self-use,too-many-public-methods,missing-docstring
class TestNew:
    def test_empty(self):
        pset = ProcSet()
        assert list(pset) == []
        assert len(pset) == 0
        assert pset.count() == 0

    def test_empty_iter(self):
        pset = ProcSet(*[])
        assert list(pset) == []
        assert len(pset) == 0
        assert pset.count() == 0

    def test_single_procint(self):
        pset = ProcSet(ProcInt(0, 3))
        assert list(pset) == [0, 1, 2, 3]
        assert len(pset) == 4
        assert pset.count() == 1

    def test_single_tuple(self):
        pset = ProcSet((0, 3))
        assert list(pset) == [0, 1, 2, 3]
        assert len(pset) == 4
        assert pset.count() == 1

    def test_many_procint(self):
        pset = ProcSet(ProcInt(0, 3), ProcInt(2, 3))
        assert list(pset) == [0, 1, 2, 3]
        assert len(pset) == 4
        assert pset.count() == 1

    def test_disjoint_tuple_iter(self):
        itvs = [(0, 1), (4, 7)]
        pset = ProcSet(*itvs)
        assert list(pset) == [0, 1, 4, 5, 6, 7]
        assert len(pset) == 6
        assert pset.count() == 2

    def test_mixed_itvs(self):
        pset = ProcSet(ProcInt(0, 3), (2, 3), [4, 7])
        assert list(pset) == [0, 1, 2, 3, 4, 5, 6, 7]
        assert len(pset) == 8
        assert pset.count() == 1

    def test_single_int(self):
        pset = ProcSet(0)
        assert list(pset) == [0]
        assert len(pset) == 1
        assert pset.count() == 1

    def test_many_ints(self):
        pset = ProcSet(0, 1, 2)
        assert list(pset) == [0, 1, 2]
        assert len(pset) == 3
        assert pset.count() == 1

    def test_mixed_procint_int(self):
        pset = ProcSet(0, (2, 3))
        assert list(pset) == [0, 2, 3]
        assert len(pset) == 3
        assert pset.count() == 2

    def test_single_procset(self):
        pset = ProcSet(ProcSet(0, (2, 3)))
        assert list(pset) == [0, 2, 3]
        assert len(pset) == 3
        assert pset.count() == 2

    def test_many_procsets(self):
        pset = ProcSet(ProcSet(0, (3, 5)), ProcSet((2, 4)))
        assert list(pset) == [0, 2, 3, 4, 5]
        assert len(pset) == 5
        assert pset.count() == 2

    def test_mixed_int_procint_procset(self):
        pset = ProcSet(0, (2, 6), ProcSet(3, (5, 7)))
        assert list(pset) == [0, 2, 3, 4, 5, 6, 7]
        assert len(pset) == 7
        assert pset.count() == 2

    @pytest.mark.parametrize('iterable', INCOMPATIBLE_ITER_LENGTH_TESTCASES, ids=repr)
    def test_incompatible_iter_length(self, iterable):
        pattern = '^Incompatible iterable, expected an iterable of exactly 2 int$'
        with pytest.raises(TypeError, match=pattern):
            ProcSet(iterable)

    @pytest.mark.parametrize('iterable', INCOMPATIBLE_ITER_TYPE_TESTCASES, ids=repr)
    def test_incompatible_iter_type(self, iterable):
        pattern = r'^ProcInt\(\) argument (inf|sup) must be int$'
        with pytest.raises(TypeError, match=pattern):
            ProcSet(iterable)

    def test_bad_noiter(self):
        with pytest.raises(TypeError):
            ProcSet(None)


# pylint: disable=no-self-use,too-many-public-methods,missing-docstring
class TestMisc:
    def test_equal(self):
        pset1 = ProcSet(ProcInt(0, 0))
        pset2 = ProcSet(ProcInt(0, 0))
        assert id(pset1) != id(pset2)
        assert pset1 == pset2

    def test_noequal(self):
        pset1 = ProcSet(ProcInt(0, 0))
        pset2 = ProcSet(ProcInt(0, 1))
        assert id(pset1) != id(pset2)
        assert pset1 != pset2

    def test_aggregate_empty(self):
        pset = ProcSet()
        hull = ProcSet()
        assert pset.aggregate() == hull

    def test_aggregate_point(self):
        pset = ProcSet(0)
        hull = ProcSet(0)
        assert pset.aggregate() == hull

    def test_aggregate_single_interval(self):
        pset = ProcSet((0, 7))
        hull = ProcSet((0, 7))
        assert pset.aggregate() == hull

    def test_aggregate_many_interval(self):
        pset = ProcSet((0, 1), (3, 4), (6, 7))
        hull = ProcSet((0, 7))
        assert pset.aggregate() == hull

    def test_iter_empty(self):
        pset = ProcSet()
        assert list(pset) == []
        assert list(reversed(pset)) == list(reversed(list(pset)))

    def test_iter_point(self):
        pset = ProcSet(0)
        assert list(pset) == [0]
        assert list(reversed(pset)) == list(reversed(list(pset)))

    def test_iter_single_interval(self):
        pset = ProcSet((0, 1))
        assert list(pset) == [0, 1]
        assert list(reversed(pset)) == list(reversed(list(pset)))

    def test_iter_many_interval(self):
        pset = ProcSet((0, 1), (4, 7))
        assert list(pset) == [0, 1, 4, 5, 6, 7]
        assert list(reversed(pset)) == list(reversed(list(pset)))

    def test_in_empty(self):
        assert 0 not in ProcSet()

    def test_in_single_point(self):
        assert 0 in ProcSet(0)
        assert 1 not in ProcSet(0)

    def test_in_single_interval(self):
        pset = ProcSet((0, 7))
        for proc in range(0, 8):
            assert proc in pset
        assert 8 not in pset

    def test_in_many_points(self):
        pset = ProcSet(*range(0, 8, 2))
        for proc in range(0, 8, 2):
            assert proc in pset
        for proc in range(1, 10, 2):
            assert proc not in pset

    def test_in_many_intervals(self):
        pset = ProcSet((0, 3), (8, 11), (16, 19))
        for proc in [*range(0, 4), *range(8, 12), *range(16, 20)]:
            assert proc in pset
        for proc in [*range(4, 8), *range(12, 16), *range(20, 24)]:
            assert proc not in pset

    def test_in_mixed_points_intervals(self):
        pset = ProcSet((0, 3), 8, 10, (16, 19))
        for proc in [*range(0, 4), 8, 10, *range(16, 20)]:
            assert proc in pset
        for proc in [*range(4, 8), 9, 11, *range(12, 16), *range(20, 24)]:
            assert proc not in pset

    def test_min_max_empty(self):
        with pytest.raises(ValueError, match='^Empty ProcSet$'):
            ProcSet().min
        with pytest.raises(ValueError, match='^Empty ProcSet$'):
            ProcSet().max

    def test_min_max_single_point(self):
        pset = ProcSet(0)
        assert pset.min == pset.max == 0

    def test_min_max_single_interval(self):
        pset = ProcSet((0, 7))
        assert pset.min == 0
        assert pset.max == 7

    def test_min_max_many_points(self):
        pset = ProcSet(0, 3, 4, 7)
        assert pset.min == 0
        assert pset.max == 7

    def test_min_max_many_intervals(self):
        pset = ProcSet((12, 25), (0, 7))
        assert pset.min == 0
        assert pset.max == 25

    def test_intervals_empty(self):
        assert list(ProcSet().intervals()) == []

    def test_intervals_single_point(self):
        assert list(ProcSet(0).intervals()) == [(0, 0)]

    def test_intervals_single_interval(self):
        assert list(ProcSet((0, 1)).intervals()) == [(0, 1)]

    def test_intervals_many_points(self):
        assert list(ProcSet(0, 2, 4).intervals()) == [(0, 0), (2, 2), (4, 4)]

    def test_intervals_many_intervals(self):
        assert list(ProcSet((6, 7), (0, 3)).intervals()) == [(0, 3), (6, 7)]

    def test_intervals_mixed_points_intervals(self):
        assert list(ProcSet((6, 7), 12, (0, 3)).intervals()) == [(0, 3), (6, 7), (12, 12)]

    def test_iscontiguous_empty(self):
        assert ProcSet().iscontiguous()

    def test_iscontiguous_single_point(self):
        assert ProcSet(1).iscontiguous()

    def test_iscontiguous_single_interval(self):
        assert ProcSet((0, 2)).iscontiguous()

    def test_iscontiguous_many_points(self):
        assert not ProcSet(0, 4).iscontiguous()

    def test_iscontiguous_many_intervals(self):
        assert not ProcSet((0, 2), (4, 7)).iscontiguous()

    def test_iscontiguous_mixed_points_intervals(self):
        assert not ProcSet(0, (3, 5)).iscontiguous()

    def test_bool_empty(self):
        assert not bool(ProcSet())

    def test_bool_nonempty(self):
        assert bool(ProcSet(0))

    @pytest.mark.parametrize('pset', (ProcSet(), ProcSet(0), ProcSet(0, 2), ), ids=repr)
    def test_clear(self, pset):
        pset.clear()
        assert pset == ProcSet()


# pylint: disable=no-self-use,too-many-public-methods,missing-docstring
class TestStringParsing:
    def test_empty(self):
        pset = ProcSet.from_str('')
        assert pset == ProcSet()

    def test_single_point(self):
        pset = ProcSet.from_str('0')
        assert pset == ProcSet(0)

    def test_contiguous(self):
        pset = ProcSet.from_str('0-3')
        assert pset == ProcSet(ProcInt(0, 3))

    def test_disjoint_pp(self):
        pset = ProcSet.from_str('1 2')
        assert pset == ProcSet(1, 2)

    def test_disjoint_ip(self):
        pset = ProcSet.from_str('0-1 2')
        assert pset == ProcSet(ProcInt(0, 1), 2)

    def test_disjoint_ii(self):
        pset = ProcSet.from_str('0-1 2-3')
        assert pset == ProcSet(ProcInt(0, 3))

    def test_nostring(self):
        with pytest.raises(TypeError, match=r'^from_str\(\) argument 2 must be str, not int$'):
            ProcSet.from_str(42)

    @pytest.mark.parametrize('string', ('-1', '0-', '1-2-3', ))
    def test_invalid_string(self, string):
        pattern = r'^Invalid interval format, parsed string is: \'{}\'$'.format(string)
        with pytest.raises(ValueError, match=pattern):
            ProcSet.from_str(string)


# pylint: disable=no-self-use,too-many-public-methods,missing-docstring
class TestDisplay:
    def test_empty(self):
        pset = ProcSet()
        assert str(pset) == ''
        assert format(pset, ':,') == ''
        assert format(pset) == str(pset)
        assert format(pset, '') == str(pset)
        assert repr(pset) == 'ProcSet()'
        assert pset == eval(repr(pset))

    def test_single_point(self):
        pset = ProcSet(ProcInt(0, 0))
        assert str(pset) == '0'
        assert format(pset, ':,') == '0'
        assert format(pset) == str(pset)
        assert format(pset, '') == str(pset)
        assert repr(pset) == 'ProcSet(0)'
        assert pset == eval(repr(pset))

    def test_small(self):
        pset = ProcSet(ProcInt(0, 1))
        assert str(pset) == '0-1'
        assert format(pset, ':,') == '0:1'
        assert format(pset) == str(pset)
        assert format(pset, '') == str(pset)
        assert repr(pset) == 'ProcSet((0, 1))'
        assert pset == eval(repr(pset))

    def test_contiguous(self):
        pset = ProcSet(ProcInt(0, 7))
        assert str(pset) == '0-7'
        assert format(pset, ':,') == '0:7'
        assert format(pset) == str(pset)
        assert format(pset, '') == str(pset)
        assert repr(pset) == 'ProcSet((0, 7))'
        assert pset == eval(repr(pset))

    def test_disjoint(self):
        pset = ProcSet(ProcInt(0, 3), ProcInt(7, 15))
        assert str(pset) == '0-3 7-15'
        assert format(pset, ':,') == '0:3,7:15'
        assert format(pset) == str(pset)
        assert format(pset, '') == str(pset)
        assert repr(pset) == 'ProcSet((0, 3), (7, 15))'
        assert pset == eval(repr(pset))

    def test_bad_format_spec_short(self):
        with pytest.raises(ValueError, match='^Invalid format specifier$'):
            format(ProcSet(), ';')

    def test_bad_format_spec_long(self):
        with pytest.raises(ValueError, match='^Invalid format specifier$'):
            format(ProcSet(), ':--')


# pylint: disable=no-self-use,protected-access,too-many-public-methods,missing-docstring
class TestCopy:
    def test_copy_empty(self):
        pset = ProcSet()
        copy_pset = copy.copy(pset)
        assert copy_pset == pset
        assert copy_pset is not pset
        assert copy_pset._itvs is not pset._itvs
        pset |= ProcSet(ProcInt(128, 255))
        assert copy_pset != pset

    def test_copy_nonempty(self):
        pset = ProcSet(ProcInt(0, 3))
        copy_pset = copy.copy(pset)
        assert copy_pset == pset
        assert copy_pset is not pset
        assert copy_pset._itvs is not pset._itvs
        pset |= ProcSet(ProcInt(128, 255))
        assert copy_pset != pset

    def test_copy_nested(self):
        pset = ProcSet(ProcInt(0, 3))
        nested = {0: pset, 1: [pset]}
        copy_nested = copy.copy(nested)
        assert copy_nested[0] == pset
        assert copy_nested[0] is pset
        assert copy_nested[0] == copy_nested[1][0]
        assert copy_nested[0] is copy_nested[1][0]
        pset |= ProcSet(ProcInt(128, 255))
        assert copy_nested[0] == pset
        assert copy_nested[0] == copy_nested[1][0]

    def test_deepcopy_empty(self):
        pset = ProcSet()
        dcopy_pset = copy.deepcopy(pset)
        assert dcopy_pset == pset
        assert dcopy_pset is not pset
        assert dcopy_pset._itvs is not pset._itvs
        pset |= ProcSet(ProcInt(128, 255))
        assert dcopy_pset != pset

    def test_deepcopy_nonempty(self):
        pset = ProcSet(ProcInt(0, 3))
        dcopy_pset = copy.deepcopy(pset)
        assert dcopy_pset == pset
        assert dcopy_pset is not pset
        assert dcopy_pset._itvs is not pset._itvs
        pset |= ProcSet(ProcInt(128, 255))
        assert dcopy_pset != pset

    def test_deepcopy_nested(self):
        pset = ProcSet(ProcInt(0, 3))
        nested = {0: pset, 1: [pset]}
        dcopy_nested = copy.deepcopy(nested)
        assert dcopy_nested[0] == pset
        assert dcopy_nested[0] is not pset
        assert dcopy_nested[0] == dcopy_nested[1][0]
        assert dcopy_nested[0] is dcopy_nested[1][0]
        pset |= ProcSet(ProcInt(128, 255))
        assert dcopy_nested[0] != pset
        assert dcopy_nested[0] == dcopy_nested[1][0]


# pylint: disable=no-self-use,too-many-public-methods,missing-docstring
class TestGetItem:
    INT_INDEX_PSETS = (
        ProcSet(ProcInt(0)),
        ProcSet(ProcInt(0, 3)),
        ProcSet(ProcInt(0, 3), ProcInt(8, 11)),
        ProcSet(ProcInt(0, 1), ProcInt(3), ProcInt(6, 7)),
        ProcSet(ProcInt(0, 3), ProcInt(8, 11), ProcInt(14, 15)),
    )
    SLICE_INDEX_PSETS = (  # interval lengths: latin square + relatively prime numbers
        ProcSet(ProcInt(0, 3), ProcInt(5, 11)),
        ProcSet(ProcInt(0, 6), ProcInt(8, 11)),
        ProcSet(ProcInt(0), ProcInt(2, 5), ProcInt(7, 13)),
        ProcSet(ProcInt(0, 3), ProcInt(5, 11), ProcInt(13)),
        ProcSet(ProcInt(0, 6), ProcInt(8), ProcInt(10, 13)),
        ProcSet(ProcInt(0, 2), ProcInt(4, 8), ProcInt(10, 16)),
        ProcSet(ProcInt(0, 4), ProcInt(6, 12), ProcInt(14, 16)),
        ProcSet(ProcInt(0, 6), ProcInt(8, 10), ProcInt(12, 16)),
        ProcSet(ProcInt(0), ProcInt(2, 4), ProcInt(6, 10), ProcInt(12, 18)),
        ProcSet(ProcInt(0, 2), ProcInt(4, 8), ProcInt(10, 16), ProcInt(18)),
        ProcSet(ProcInt(0, 4), ProcInt(6, 12), ProcInt(14), ProcInt(16, 18)),
        ProcSet(ProcInt(0, 6), ProcInt(8), ProcInt(10, 12), ProcInt(14, 18)),
    )


    def test_bad_key_type(self):
        pset = ProcSet()
        with pytest.raises(TypeError):
            pset[None]
        with pytest.raises(ValueError):
            pset[::0]

    def test_empty(self):
        pset = ProcSet()
        with pytest.raises(IndexError):
            pset[0]
        with pytest.raises(IndexError):
            pset[-1]

    @pytest.mark.parametrize('pset', INT_INDEX_PSETS, ids=repr)
    def test_int_index_inrange(self, pset):
        lpset = list(pset)
        for i in range(len(pset)):
            assert pset[i] == lpset[i]

    @pytest.mark.parametrize('pset', INT_INDEX_PSETS, ids=repr)
    def test_int_index_outofrange(self, pset):
        with pytest.raises(IndexError):
            pset[len(pset)]

    @pytest.mark.parametrize('pset', INT_INDEX_PSETS, ids=repr)
    def test_negative_int_index_inrange(self, pset):
        lpset = list(pset)
        for i in range(-len(pset), 0):
            assert pset[i] == lpset[i]

    @pytest.mark.parametrize('pset', INT_INDEX_PSETS, ids=repr)
    def test_negative_int_index_outofrange(self, pset):
        with pytest.raises(IndexError):
            pset[-len(pset) - 1]

    @pytest.mark.parametrize('pset', INT_INDEX_PSETS + SLICE_INDEX_PSETS, ids=repr)
    def test_slice(self, pset):
        starts = (None, ) + tuple(range(-len(pset) - 1, len(pset) + 2))
        stops = starts
        steps = (None, ) + tuple(range(-len(pset) - 1, 0)) + tuple(range(1, len(pset) + 2))

        for start, stop, step in itertools.product(starts, stops, steps):
            assert pset[start:stop:step] == list(pset)[start:stop:step]
