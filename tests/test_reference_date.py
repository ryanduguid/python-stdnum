# test_reference_date.py - test the optional reference date
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

"""Check the test reference date in isolated pytest processes."""

from pathlib import Path

import pytest


@pytest.fixture
def clock_suite(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> pytest.Pytester:
    """Install the real configuration in an isolated test directory."""
    # These child suites test pytest configuration, not library coverage.
    monkeypatch.delenv('COV_CORE_DATAFILE', raising=False)
    source = Path(__file__).resolve().parent.parent / 'conftest.py'
    pytester.makeconftest(source.read_text() + """
import datetime
_original_date = datetime.date

def pytest_sessionfinish(session):
    assert datetime.date is _original_date
""")
    pytester.makepyfile("""
import datetime
import os

real_date = datetime.date
real_today = datetime.date.today()

def test_date():
    value = os.environ.get('STDNUM_TEST_DATE')
    expected = real_date.fromisoformat(value) if value is not None else real_today
    assert datetime.date.today() == expected
    assert datetime.date(2000, 2, 29) == real_date(2000, 2, 29)
    assert repr(datetime.date(2000, 2, 29)) == 'datetime.date(2000, 2, 29)'
    assert isinstance(real_date(2000, 2, 29), datetime.date)
    assert isinstance(datetime.datetime.now().date(), datetime.date)
    if value is None:
        assert datetime.date is real_date
""")
    return pytester


def test_default_uses_real_date(clock_suite: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    """No reference date leaves the date class and clock unchanged."""
    monkeypatch.delenv('STDNUM_TEST_DATE', raising=False)
    clock_suite.runpytest_subprocess('-q').assert_outcomes(passed=1)


@pytest.mark.parametrize('value', ['2024-01-01', '2040-04-24', '2024-02-29'])
def test_explicit_reference_date(clock_suite: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """A requested date applies during tests and is restored afterwards."""
    monkeypatch.setenv('STDNUM_TEST_DATE', value)
    clock_suite.runpytest_subprocess('-q').assert_outcomes(passed=1)


@pytest.mark.parametrize('value', ['', 'invalid', '2023-02-29', '20240101'])
def test_invalid_reference_date(clock_suite: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """Invalid dates fail with an actionable configuration error."""
    monkeypatch.setenv('STDNUM_TEST_DATE', value)
    result = clock_suite.runpytest_subprocess('-q')
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert 'STDNUM_TEST_DATE must be a valid date in YYYY-MM-DD format' in result.stderr.str()
