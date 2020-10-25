# Copyright 2020 Dmitry Petukhov https://github.com/dgpv
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# pylama: ignore=C901

import os.path
import json
import random

try:
    from typing import List
except ImportError:
    pass

import unittest

from bip32template import (
    BIP32TemplateExceptionUnexpectedHardenedMarker,
    BIP32TemplateExceptionUnexpectedSpace,
    BIP32TemplateExceptionUnexpectedCharacter,
    BIP32TemplateExceptionUnexpectedFinish,
    BIP32TemplateExceptionUnexpectedSlash,
    BIP32TemplateExceptionInvalidCharacter,
    BIP32TemplateExceptionIndexTooBig,
    BIP32TemplateExceptionIndexHasLeadingZero,
    BIP32TemplateExceptionPathEmpty,
    BIP32TemplateExceptionPathTooLong,
    BIP32TemplateExceptionPathSectionTooLong,
    BIP32TemplateExceptionRangesIntersect,
    BIP32TemplateExceptionRangeOrderBad,
    BIP32TemplateExceptionRangeEqualsWildcard,
    BIP32TemplateExceptionSingleIndexAsRange,
    BIP32TemplateExceptionRangeStartEqualsEnd,
    BIP32TemplateExceptionRangeStartNextToPrevious,
    BIP32TemplateExceptionGotHardenedAfterUnhardened,
    BIP32TemplateExceptionDigitExpected,
    BIP32TemplateException,
    BIP32Template,
    HARDENED_INDEX_START, HARDENED_INDEX_MASK
)

errors_table = {
    'error_unexpected_hardened_marker':
    BIP32TemplateExceptionUnexpectedHardenedMarker,
    'error_unexpected_space': BIP32TemplateExceptionUnexpectedSpace,
    'error_unexpected_char': BIP32TemplateExceptionUnexpectedCharacter,
    'error_unexpected_finish': BIP32TemplateExceptionUnexpectedFinish,
    'error_unexpected_slash': BIP32TemplateExceptionUnexpectedSlash,
    'error_invalid_char': BIP32TemplateExceptionInvalidCharacter,
    'error_index_too_big': BIP32TemplateExceptionIndexTooBig,
    'error_index_has_leading_zero': BIP32TemplateExceptionIndexHasLeadingZero,
    'error_path_empty': BIP32TemplateExceptionPathEmpty,
    'error_path_too_long': BIP32TemplateExceptionPathTooLong,
    'error_path_section_too_long': BIP32TemplateExceptionPathSectionTooLong,
    'error_ranges_intersect': BIP32TemplateExceptionRangesIntersect,
    'error_range_order_bad': BIP32TemplateExceptionRangeOrderBad,
    'error_range_equals_wildcard': BIP32TemplateExceptionRangeEqualsWildcard,
    'error_single_index_as_range': BIP32TemplateExceptionSingleIndexAsRange,
    'error_range_start_equals_end': BIP32TemplateExceptionRangeStartEqualsEnd,
    'error_range_start_next_to_previous':
    BIP32TemplateExceptionRangeStartNextToPrevious,
    'error_got_hardened_after_unhardened':
    BIP32TemplateExceptionGotHardenedAfterUnhardened,
    'error_digit_expected': BIP32TemplateExceptionDigitExpected,
}


def _extract_path(tpl: BIP32Template, want_nomatch: bool = False) -> List[int]:

    path = []
    have_nomatch = False
    for s in tpl.sections:
        for start, end in s:
            if want_nomatch and not have_nomatch:
                if (start & HARDENED_INDEX_MASK) != 0:
                    path.append(start-1)
                    have_nomatch = True
                    break
                if (end | HARDENED_INDEX_START) != 0xFFFFFFFF:
                    path.append(end+1)
                    have_nomatch = True
                    break
            elif random.choice((True, False)):
                path.append(random.randint(start, end))
                break
        else:
            path.append(s[0][0])

    if want_nomatch and not have_nomatch:
        # Could not put non-matching value in any position, that means that
        # all sections contain wildcard match. To make a non-matching path,
        # just flip the last hardened section to unhardened.
        # If there's no hardened sections, flip first section to hardened
        have_flipped = False
        for i, s in enumerate(tpl.sections):
            assert len(s) == 1
            start, end = s[0]
            assert (start & HARDENED_INDEX_MASK) == 0
            assert (end | HARDENED_INDEX_START) == 0xFFFFFFFF
            if start >= HARDENED_INDEX_START and not have_flipped:
                # Found the hardened section, flip
                path[i] = start ^ HARDENED_INDEX_START
                have_flipped = True
                # do not break so all sections are checked with asserts

        if not have_flipped:
            # All sections were unhardened, make first section hardened
            assert tpl.sections[0][0][0] < HARDENED_INDEX_START
            path[0] = tpl.sections[0][0][0] | HARDENED_INDEX_START

    return path


class Test_templates(unittest.TestCase):
    def test(self) -> None:
        MAX_SECTIONS = 3
        MAX_RANGES = 4

        with open(os.path.dirname(__file__) + '/data/normal_finish') as f:
            for line in f:
                tcase, sections_str = json.loads(line)

                sections = []
                for sec in json.loads(sections_str):
                    new_sec = []
                    for start, stop in sec:
                        new_sec.append((start, stop))
                    sections.append(new_sec)

                tpl = BIP32Template.parse(
                    tcase, max_sections=MAX_SECTIONS,
                    max_ranges_per_section=MAX_RANGES)

                self.assertEqual(tpl.sections, sections)

                self.assertEqual(BIP32Template(tpl.sections,
                                               is_partial=tpl.is_partial),
                                 tpl)

                self.assertTrue(tpl.match(_extract_path(tpl)))
                self.assertFalse(
                    tpl.match(_extract_path(tpl, want_nomatch=True)))

                self.assertEqual(BIP32Template.parse(str(tpl)), tpl)

                try:
                    tpl = BIP32Template.parse(
                        tcase, max_sections=MAX_SECTIONS,
                        max_ranges_per_section=MAX_RANGES,
                        is_format_onlypath=True)
                except BIP32TemplateException:
                    self.assertFalse(tpl.to_path())
                else:
                    path = tpl.to_path()
                    assert path is not None
                    self.assertTrue(tpl.match(path))
                    self.assertEqual(
                        BIP32Template.parse(str(tpl)).to_path(), path)
                    self.assertEqual(tpl,
                                     BIP32Template.from_path(
                                         path, is_partial=tpl.is_partial,
                                         hardened_marker=tpl.hardened_marker))

                try:
                    tpl = BIP32Template.parse(
                        tcase, max_sections=MAX_SECTIONS,
                        max_ranges_per_section=MAX_RANGES,
                        is_format_unambiguous=True)
                except BIP32TemplateExceptionRangeStartNextToPrevious:
                    pass
                else:
                    self.assertEqual(str(tpl), tcase)

        for errcase, expected_exc in errors_table.items():
            is_unambigouos = (
                errcase == "error_range_start_next_to_previous")
            with open(os.path.dirname(__file__) + '/data/' + errcase) as f:
                for tcase in f:
                    if tcase.endswith('\n'):
                        tcase = tcase[:-1]

                    def check(is_onlypath: bool) -> BIP32TemplateException:
                        # micropython's assertRaises is too basic,
                        # catch the expected exception directly
                        try:
                            BIP32Template.parse(
                                tcase, max_sections=MAX_SECTIONS,
                                max_ranges_per_section=MAX_RANGES,
                                is_format_onlypath=is_onlypath,
                                is_format_unambiguous=is_unambigouos)
                        except expected_exc as exc:
                            return exc

                        raise AssertionError('{} is not raised'
                                             .format(expected_exc))

                    exc = check(False)
                    if '[' not in tcase and '*' not in tcase:
                        exc_onlypath = check(True)
                        self.assertEqual(str(exc), str(exc_onlypath))

                    expected_pos = len(tcase)

                    if errcase in ('error_unexpected_finish',
                                   'error_path_empty'):
                        expected_pos += 1
                    elif errcase == 'error_unexpected_slash':
                        if expected_pos > 1 and tcase[expected_pos-2] != '/':
                            expected_pos += 1
                    elif errcase == 'error_path_too_long':
                        if tcase[expected_pos-1] in "'h":
                            expected_pos += 1

                        num_slashes = tcase.count('/')
                        if tcase.startswith('m/'):
                            num_slashes -= 1

                        self.assertEqual(num_slashes, MAX_SECTIONS)

                    # unittest's assertEqual does not print the values,
                    # so we include them in msg
                    self.assertEqual(
                        exc.position, expected_pos,
                        msg=('for error "{}" testcase "{}": {} != {}'
                             .format(errcase, tcase,
                                     exc.position, expected_pos)))
