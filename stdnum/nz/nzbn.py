# nzbn.py - functions for handling New Zealand Business Numbers
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

"""NZBN (New Zealand Business Number).

The New Zealand Business Number (NZBN) identifies a business and links to
its primary business data. It is a 13-digit Global Location Number (GLN)
supplied by GS1 New Zealand, beginning with 942 and ending in a check digit.

This module checks the format, length, prefix and check digit. It does not
check whether a number has been issued as an NZBN.

More information:

* https://www.nzbn.govt.nz/whats-an-nzbn/about/
* https://portal.api.business.govt.nz/api/nzbn
* https://www.companiesoffice.govt.nz/all-registers/insolvency-practitioners/obligations/report-a-serious-problem/

>>> compact(' 9429 0001-06078 ')
'9429000106078'
>>> validate('9429000106078')
'9429000106078'
>>> is_valid('9429000106079')
False
"""

from __future__ import annotations

from stdnum import ean
from stdnum.exceptions import *
from stdnum.util import isdigits


def compact(number: str) -> str:
    """Convert the number to its minimal representation, removing valid
    separators and surrounding whitespace."""
    return ean.compact(number)


def validate(number: str) -> str:
    """Check the number's format, length, prefix and check digit.

    This does not check whether the number has been issued as an NZBN.
    """
    number = compact(number)
    if not isdigits(number):
        raise InvalidFormat()
    if len(number) != 13:
        raise InvalidLength()
    if not number.startswith('942'):
        raise InvalidComponent()
    return ean.validate(number)


def is_valid(number: str) -> bool:
    """Check the number's format, length, prefix and check digit."""
    try:
        return bool(validate(number))
    except ValidationError:
        return False
