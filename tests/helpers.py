# -*- coding: utf-8 -*-

# Copyright © 2018
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


import pytest


def dict_parametrize(argnames, paramsdict, indirect=False, scope=None):
    """Decorator to parametrize test functions from a (id, argvalue) dict."""
    ids, argvalues = zip(*paramsdict.items())  # ensure id matches its argvalue
    return pytest.mark.parametrize(argnames, argvalues, indirect, ids, scope)
