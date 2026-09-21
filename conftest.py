# conftest.py - optional reference date for tests
#
# Copyright (C) 2026 Ryan Duguid
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see <https://www.gnu.org/licenses/>.

"""Pytest configuration for python-stdnum."""

import datetime
import os
from unittest.mock import patch

import pytest


pytest_plugins = ['pytester']


def pytest_configure(config):
    """Validate the optional reference date before collecting tests."""
    value = os.environ.get('STDNUM_TEST_DATE')
    config._stdnum_reference_date = None
    if value is None:
        return
    try:
        fixed_date = datetime.date.fromisoformat(value)
        if fixed_date.isoformat() != value:
            raise ValueError()
    except ValueError:
        raise pytest.UsageError('STDNUM_TEST_DATE must be a valid date in YYYY-MM-DD format')
    config._stdnum_reference_date = fixed_date


@pytest.fixture(scope='session', autouse=True)
def reference_date(request):
    """Optionally replace date.today() for the duration of the test session."""
    fixed_date = request.config._stdnum_reference_date
    if fixed_date is None:
        yield
        return

    real_date = datetime.date

    class DateMeta(type):
        """Keep isinstance checks compatible with ordinary date objects."""

        def __instancecheck__(cls, instance):
            return isinstance(instance, real_date)

    class ReferenceDate(real_date, metaclass=DateMeta):
        """Return ordinary dates, overriding only the current date."""

        def __new__(cls, *args, **kwargs):
            return real_date(*args, **kwargs)

        @classmethod
        def today(cls):
            return fixed_date

    with patch.object(datetime, 'date', ReferenceDate):
        yield
