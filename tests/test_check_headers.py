# test_check_headers.py - tests for the source-header checker
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

"""Tests for the standalone source-header checker."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestHeaders(unittest.TestCase):
    """Exercise header validation through the script's command-line interface."""

    def setUp(self) -> None:
        """Read the standard licence header without importing the script."""
        self.checker = Path(__file__).resolve().parents[1] / 'scripts' / 'check_headers.py'
        self.header = self.checker.read_text(encoding='utf-8').split('"""', 1)[0]
        self.assertIn('# check_headers.py - ', self.header)

    def _check(self, filename: str, contents: str) -> subprocess.CompletedProcess[str]:
        """Run the checker against one fixture in an isolated directory."""
        # The checker uses only the standard library, so skip site startup hooks.
        command = [sys.executable, '-S']
        if os.name == 'nt':
            # Disable UTF-8 mode so it cannot hide the locale-decoding failure.
            command.extend(['-X', 'utf8=0'])
        command.append(str(self.checker))
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / filename
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(contents, encoding='utf-8')
            return subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding='utf-8', check=False)

    def test_utf8_header(self) -> None:
        """Read a UTF-8 quote whose final byte is undefined in cp1252."""
        header = self.header.replace('# check_headers.py - ', '# check_headers.py - \u201d ', 1)
        result = self._check('check_headers.py', header)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_relative_path(self) -> None:
        """Accept the portable relative filename used by updater headings."""
        header = self.header.replace('# check_headers.py - ', '# update/check_headers.py - ', 1)
        result = self._check('update/check_headers.py', header)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_native_path(self) -> None:
        """Preserve acceptance of an exact native relative filename."""
        native = str(Path('update') / 'check_headers.py')
        header = self.header.replace('# check_headers.py - ', '# %s - ' % native, 1)
        result = self._check('update/check_headers.py', header)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_basename(self) -> None:
        """Preserve acceptance of a basename in a nested file."""
        result = self._check('update/check_headers.py', self.header)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_wrong_identification(self) -> None:
        """Reject a wrong filename and a wrong directory with the same basename."""
        for name in ('other.py', 'other/check_headers.py'):
            with self.subTest(name=name):
                header = self.header.replace('# check_headers.py - ', '# %s - ' % name, 1)
                result = self._check('update/check_headers.py', header)
                expected = '%s: Incorrect file identification\n' % str(Path('update') / 'check_headers.py')
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, expected, ''))

    def test_missing_identification(self) -> None:
        """Reject a missing identification without raising an exception."""
        header = self.header.replace('# check_headers.py - ', '# ', 1)
        result = self._check('check_headers.py', header)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (1, 'check_headers.py: Incorrect file identification\n', ''))

    def test_wrong_licence(self) -> None:
        """Reject missing and materially altered licence text."""
        for header in (self.header.split('# This library', 1)[0], self.header.replace('version 2.1', 'version 3.0')):
            with self.subTest(header=header):
                result = self._check('check_headers.py', header)
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr),
                    (1, 'check_headers.py: Incorrect license text\n', ''))

    def test_both_errors(self) -> None:
        """Report identification and licence errors in their existing order."""
        result = self._check('other.py', self.header.replace('version 2.1', 'version 3.0'))
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (1, 'other.py: Incorrect file identification\nother.py: Incorrect license text\n', ''))
