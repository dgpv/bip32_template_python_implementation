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

# pylama: ignore=C901,E731,E221

try:
    from typing import (
        List, Tuple, Sequence, Iterable, Optional, NoReturn, Type, Any, Union,
        TypeVar, cast
    )
    HAS_TYPING = True
except ImportError:
    HAS_TYPING = False
    # mypy 0.761 does not complain here,
    # but complains if we use `def cast(x,y):`
    cast = lambda x, y: y

HARDENED_INDEX_START = 0x80000000
MAX_INDEX_VALUE = (HARDENED_INDEX_START-1)
HARDENED_INDEX_MASK = MAX_INDEX_VALUE
INVALID_INDEX = HARDENED_INDEX_START
HARDENED_MARKERS = ("h", "'")


class BIP32TemplateException(Exception):
    message = "generic template exception"
    position = None

    def __init__(self, message: Optional[str] = None,
                 position: Optional[int] = None) -> None:
        self.position = position
        if message is not None:
            self.message = message

    def __str__(self) -> str:
        if self.position is None:
            return self.message
        return ('{} at position {}'.format(self.message, self.position))


class BIP32TemplateExceptionUnexpectedHardenedMarker(BIP32TemplateException):
    message = "unexpected hardened marker"


class BIP32TemplateExceptionUnexpectedSpace(BIP32TemplateException):
    message = "unexpected space"


class BIP32TemplateExceptionUnexpectedCharacter(BIP32TemplateException):
    message = "unexpected character"


class BIP32TemplateExceptionUnexpectedFinish(BIP32TemplateException):
    message = "template string finished unexpectedly"


class BIP32TemplateExceptionUnexpectedSlash(BIP32TemplateException):
    message = "unexpected slash character"


class BIP32TemplateExceptionInvalidCharacter(BIP32TemplateException):
    message = "invalid character"


class BIP32TemplateExceptionIndexTooBig(BIP32TemplateException):
    message = "specified index too big"


class BIP32TemplateExceptionIndexHasLeadingZero(BIP32TemplateException):
    message = "specified index has leading zero"


class BIP32TemplateExceptionPathEmpty(BIP32TemplateException):
    message = "template path is empty"


class BIP32TemplateExceptionPathTooLong(BIP32TemplateException):
    message = "template path is too long"


class BIP32TemplateExceptionPathSectionTooLong(BIP32TemplateException):
    message = "template path section is too long"


class BIP32TemplateExceptionRangesIntersect(BIP32TemplateException):
    message = "ranges intersect"


class BIP32TemplateExceptionRangeOrderBad(BIP32TemplateException):
    message = "order of ranges is incorrect"


class BIP32TemplateExceptionRangeEqualsWildcard(BIP32TemplateException):
    message = \
        "specified range equals wildcard, should be specified as wildcard"


class BIP32TemplateExceptionSingleIndexAsRange(BIP32TemplateException):
    message = "range contains just a single index, should not be a range"


class BIP32TemplateExceptionRangeStartEqualsEnd(BIP32TemplateException):
    message = "range start equals range end, should not be a range"


class BIP32TemplateExceptionRangeStartNextToPrevious(BIP32TemplateException):
    message = \
        "range start is next to previous range end, must be a single range"


class BIP32TemplateExceptionGotHardenedAfterUnhardened(BIP32TemplateException):
    message = "hardened derivation specified after unhardened"


class BIP32TemplateExceptionDigitExpected(BIP32TemplateException):
    message = "digit expected"


class BIP32TemplateExceptionInconsistentRange(BIP32TemplateException):
    message = ("inconsistent range encountered (both hardened and unhardened "
               "indexes in one range tuple)")


def _assert_never(x: NoReturn) -> NoReturn:
    raise AssertionError('{} is not handled'.format(x))

# These classes emulate what we could do with Enum
# With good Enum implementation, we could use mypy to check that all
# enum variants are exhaustively checked with _assert_never function:
# (see https://github.com/python/mypy/issues/6366)
#
# But micropyhthon does not have a working Enum implementation,
# so we are emulating this for a time being and _assert_never is not
# active in static typechecks


class State:
    SECTION_START        = cast('State', object())
    NEXT_SECTION         = cast('State', object())
    RANGE_WITHIN_SECTION = cast('State', object())
    SECTION_END          = cast('State', object())
    VALUE                = cast('State', object())


class Success:
    SUCCESS = cast('Success', object())


if HAS_TYPING:
    T_BIP32Template = TypeVar('T_BIP32Template', bound='BIP32Template')


class BIP32Template():

    def __init__(self, _sections: Iterable[Iterable[Tuple[int, int]]], *,
                 is_partial: bool = False, hardened_marker: str = '',
                 _accept_params_as_is: bool = False
                 ) -> None:

        if not _sections:
            raise BIP32TemplateExceptionPathEmpty

        sections = []  # type: List[List[Tuple[int, int]]]

        if _accept_params_as_is:
            sections = _sections  # type: ignore
        else:
            got_hardened = False
            got_unhardened = False
            for s in _sections:
                prev_r = None
                new_ranges = []
                for r in s:
                    start, end = r
                    if start > end:
                        raise BIP32TemplateExceptionRangeOrderBad
                    if prev_r is not None and prev_r[1] >= start:
                        raise BIP32TemplateExceptionRangesIntersect
                    if start >= HARDENED_INDEX_START:
                        got_hardened = True
                        if got_unhardened:
                            raise BIP32TemplateExceptionGotHardenedAfterUnhardened  # noqa
                        if end < HARDENED_INDEX_START:
                            raise BIP32TemplateExceptionInconsistentRange
                    else:
                        if end >= HARDENED_INDEX_START:
                            raise BIP32TemplateExceptionInconsistentRange

                        got_unhardened = True

                    prev_r = r

                    if len(r) != 2 or not isinstance(r[0], int) \
                            or not isinstance(r[1], int):
                        raise ValueError(
                            'ranges must consist of (int, int) tuples')

                    new_ranges.append((r[0], r[1]))

                sections.append(new_ranges)

            assert got_hardened or got_unhardened
            if not got_hardened:
                hardened_marker = ''

        self.sections = sections
        self.is_partial = is_partial

        if hardened_marker and hardened_marker not in HARDENED_MARKERS:
            raise BIP32TemplateExceptionUnexpectedHardenedMarker

        self.hardened_marker = hardened_marker

    @classmethod
    def parse(cls: Type[T_BIP32Template], tpl: Iterable[str], *,
              max_sections: int = 16,
              max_ranges_per_section: int = 8,
              is_format_onlypath: bool = False,
              is_format_unambiguous: bool = False,
              hardened_markers: Tuple[str, str] = HARDENED_MARKERS
              ) -> T_BIP32Template:

        is_partial = True

        state = State.SECTION_START  # type: State
        ret_state = None  # type: Optional[State]
        section_started = True

        index_value = INVALID_INDEX
        range_start = INVALID_INDEX
        range_end = INVALID_INDEX
        accepted_hardened_markers = set(hardened_markers)

        tpl_iter = iter(tpl)

        # structure for 0/[3-6,8]/2:
        # [ [ (0,0) ], [ (3,6), (8,8) ], [ (2,2) ] ]
        sections = []  # type: List[List[Tuple[int, int]]]

        position = 0

        def err(exc: Type[BIP32TemplateException]) -> NoReturn:
            # micropython does not support arguments to exceptions,
            # so we first create an instance of the exception, set the
            # attribute, and then raise
            e_inst = exc()
            e_inst.position = position
            raise e_inst

        def get_num_ranges_in_last_section() -> int:
            if section_started:
                return 0
            return len(sections[-1])

        def raise_unexpected_char_error(c: Optional[str]) -> NoReturn:
            if c is None:
                err(BIP32TemplateExceptionUnexpectedFinish)
            if c in ' \t':
                err(BIP32TemplateExceptionUnexpectedSpace)
            if c in "m/[]-,*h'" or c.isdigit():
                err(BIP32TemplateExceptionUnexpectedCharacter)
            err(BIP32TemplateExceptionInvalidCharacter)

        def process_digit(c: str) -> int:
            assert c.isdigit()

            if index_value == 0:
                err(BIP32TemplateExceptionIndexHasLeadingZero)

            v = ord(c) - ord('0')

            if index_value != INVALID_INDEX:
                v = index_value * 10 + v

            if v > MAX_INDEX_VALUE:
                err(BIP32TemplateExceptionIndexTooBig)

            return v

        def finalize_range() -> bool:
            nonlocal range_start, range_end

            if range_start != INVALID_INDEX:
                if range_end != INVALID_INDEX:
                    # Because we call this funcion from two different
                    # FSM states (RANGE_WITHIN_SECTION and SECTION_END), and
                    # we _change_ range variables here, range can already be
                    # finalized when this function is called. The end of the
                    # range should be the same as the index, though.
                    assert range_end == index_value
                    return False

                range_end = index_value
                return True

            assert range_start == INVALID_INDEX
            assert range_end == INVALID_INDEX
            range_start = index_value
            range_end = index_value

            return False

        def apply_new_range() -> None:
            nonlocal range_start, range_end, section_started

            assert range_start <= MAX_INDEX_VALUE
            assert range_end <= MAX_INDEX_VALUE

            if section_started:
                sections.append([(range_start, range_end)])
                section_started = False
            else:
                prev_range_start, prev_range_end = sections[-1][-1]
                assert prev_range_start <= MAX_INDEX_VALUE
                assert prev_range_end <= MAX_INDEX_VALUE

                if prev_range_end + 1 == range_start:
                    sections[-1][-1] = (prev_range_start, range_end)
                else:
                    sections[-1].append((range_start, range_end))

            range_start = INVALID_INDEX
            range_end = INVALID_INDEX

        def check_range_correctness(was_open: bool, *, is_last: bool) -> None:
            assert range_start <= MAX_INDEX_VALUE
            assert range_end <= MAX_INDEX_VALUE

            if range_start == 0 and range_end == MAX_INDEX_VALUE:
                err(BIP32TemplateExceptionRangeEqualsWildcard)

            num_ranges = get_num_ranges_in_last_section()

            if range_start == range_end:
                if is_last and num_ranges == 0:
                    err(BIP32TemplateExceptionSingleIndexAsRange)
                if was_open:
                    err(BIP32TemplateExceptionRangeStartEqualsEnd)

            if range_start > range_end:
                err(BIP32TemplateExceptionRangeOrderBad)

            if num_ranges > 0:
                prev_range_start, prev_range_end = sections[-1][-1]
                assert prev_range_start <= MAX_INDEX_VALUE
                assert prev_range_end <= MAX_INDEX_VALUE

                if is_format_unambiguous and prev_range_end + 1 == range_start:
                    err(BIP32TemplateExceptionRangeStartNextToPrevious)

                if prev_range_start > range_start:
                    err(BIP32TemplateExceptionRangeOrderBad)

                if prev_range_start <= range_start \
                        and prev_range_end >= range_start:
                    err(BIP32TemplateExceptionRangesIntersect)

        def is_section_hardened(section: Sequence[Tuple[int, int]]) -> bool:
            assert section

            # all ranges should be hardened if first range start is hardened,
            # and should be not hardened otherwise
            is_hardened = section[0][0] >= HARDENED_INDEX_START

            for r_start, r_end in section:
                if r_start >= HARDENED_INDEX_START:
                    assert r_end >= HARDENED_INDEX_START
                    assert is_hardened
                else:
                    assert r_end < HARDENED_INDEX_START
                    assert not is_hardened

            return is_hardened

        def harden_last_section() -> None:
            last_section = sections[-1]
            for idx, (r_start, r_end) in enumerate(last_section):
                assert r_start <= MAX_INDEX_VALUE
                assert r_end <= MAX_INDEX_VALUE
                last_section[idx] = (r_start + HARDENED_INDEX_START,
                                     r_end + HARDENED_INDEX_START)

        def do_fsm(c: Optional[str]) -> Tuple[Union[State, Success],
                                              Optional[State]]:
            nonlocal index_value, range_start, section_started

            if state is State.SECTION_START:
                section_started = True

                if c is None:
                    if not sections:
                        err(BIP32TemplateExceptionPathEmpty)
                    err(BIP32TemplateExceptionUnexpectedSlash)

                if not is_format_onlypath:
                    if c in '[*' and len(sections) == max_sections:
                        err(BIP32TemplateExceptionPathTooLong)
                    if c == '[':
                        index_value = INVALID_INDEX
                        return (State.VALUE, State.RANGE_WITHIN_SECTION)
                    if c == '*':
                        range_start = 0
                        index_value = MAX_INDEX_VALUE
                        return (State.SECTION_END, None)

                if c == '/':
                    err(BIP32TemplateExceptionUnexpectedSlash)

                if c.isdigit():
                    index_value = process_digit(c)
                    if len(sections) == max_sections:
                        # Note that any errors in process_digit
                        # are catched first
                        err(BIP32TemplateExceptionPathTooLong)
                    return (State.VALUE, State.SECTION_END)

                raise_unexpected_char_error(c)

            elif state is State.NEXT_SECTION:
                assert ret_state is None
                assert index_value == INVALID_INDEX

                if c is None:
                    if len(sections) > max_sections:
                        err(BIP32TemplateExceptionPathTooLong)
                    return (Success.SUCCESS, None)

                if c == '/':
                    return (State.SECTION_START, None)

                raise_unexpected_char_error(c)

            elif state is State.RANGE_WITHIN_SECTION:
                assert not is_format_onlypath

                if c is None:
                    err(BIP32TemplateExceptionUnexpectedFinish)

                if index_value == INVALID_INDEX:
                    if c == ' ':
                        err(BIP32TemplateExceptionUnexpectedSpace)
                    err(BIP32TemplateExceptionDigitExpected)

                if c == '-':
                    if range_start != INVALID_INDEX:
                        raise_unexpected_char_error(c)

                    range_start = index_value
                    index_value = INVALID_INDEX
                    return (State.VALUE, State.RANGE_WITHIN_SECTION)

                if c == ',':
                    if get_num_ranges_in_last_section() == \
                            max_ranges_per_section - 1:
                        err(BIP32TemplateExceptionPathSectionTooLong)

                    was_open = finalize_range()
                    check_range_correctness(was_open, is_last=False)
                    apply_new_range()
                    index_value = INVALID_INDEX
                    return (State.VALUE, State.RANGE_WITHIN_SECTION)

                if c == ']':
                    was_open = finalize_range()
                    check_range_correctness(was_open, is_last=True)
                    return (State.SECTION_END, None)

                raise_unexpected_char_error(c)

            elif state is State.SECTION_END:
                assert index_value != INVALID_INDEX

                if c is None and len(sections) == max_sections:
                    err(BIP32TemplateExceptionPathTooLong)

                if c == '/' or c is None:
                    finalize_range()
                    apply_new_range()
                    index_value = INVALID_INDEX
                    return (
                        Success.SUCCESS if c is None else State.SECTION_START,
                        None)

                if c in accepted_hardened_markers:
                    accepted_hardened_markers.clear()
                    accepted_hardened_markers.add(c)
                    finalize_range()
                    apply_new_range()

                    if len(sections) > 1 \
                            and not is_section_hardened(sections[-2]):
                        err(BIP32TemplateExceptionGotHardenedAfterUnhardened)

                    harden_last_section()
                    index_value = INVALID_INDEX
                    return (State.NEXT_SECTION, None)

                if c in hardened_markers:
                    err(BIP32TemplateExceptionUnexpectedHardenedMarker)

                raise_unexpected_char_error(c)

            elif state is State.VALUE:
                assert c is not None
                index_value = process_digit(c)
                return (state, ret_state)

            else:
                # too cumbersome to enforce the static check without
                # Enum implementation so just ignore typing check for now
                _assert_never(state)  # type: ignore

        while True:

            c = None  # type: Optional[str]
            try:
                c = next(tpl_iter)
            except StopIteration:
                c = None
            else:
                if not isinstance(c, str):
                    raise ValueError(
                        'encountered an element in tpl that is not a string')
                if len(c) != 1:
                    raise ValueError(
                        'encountered an element in tpl with len() != 1')

            position += 1

            # PrefixParserFSM logic starts

            if c == 'm' and position == 1:
                is_partial = False
                continue

            if not is_partial and position == 2:
                if c == '/':
                    continue
                raise_unexpected_char_error(c)

            # PrefixParserFSM logic ends

            if state is State.VALUE and (c is None or not c.isdigit()):
                assert ret_state is not None
                state = ret_state
                ret_state = None

            new_state, ret_state = do_fsm(c)
            assert ret_state is not State.VALUE

            if c is None:
                if new_state is not Success.SUCCESS:
                    raise AssertionError(
                        'only success state is permitted when data ends, '
                        'any errors should cause exceptions to be raised')
                break

            if new_state is Success.SUCCESS:
                break

            # When we are not using Enum (because it is unavailable
            # in micropython), mypy 0.761 cannot deduce that SUCCESS case
            # was checked above and new_state can now only contain
            # State values. Therefore we need this cast
            state = cast(State, new_state)

        if len(accepted_hardened_markers) == 1:
            hardened_marker = list(accepted_hardened_markers)[0]
        else:
            hardened_marker = ''

        return cls(sections, is_partial=is_partial,
                   hardened_marker=hardened_marker,
                   _accept_params_as_is=True)

    def match(self, path: Sequence[int]) -> bool:
        if len(self.sections) != len(path):
            return False

        for i, section in enumerate(self.sections):
            for range_start, range_end in section:
                if path[i] < range_start or path[i] > range_end:
                    pass  # so the condition check is the same as in the spec
                else:
                    break  # range match
            else:
                return False  # no breaks: no matching range

        return True

    def to_path(self) -> Optional[List[int]]:
        path = []
        for s in self.sections:
            if len(s) > 1:
                return None

            if s[0][0] != s[0][1]:
                return None

            path.append(s[0][0])

        return path

    def __eq__(self, other: Any) -> bool:
        """Checks for equality of two templates. Note that templates
        with different hardened markers can still be equal"""

        if not isinstance(other, BIP32Template):
            raise ValueError(
                'can only compare with instances of BIP32Template')

        if self.is_partial != other.is_partial:
            return False

        return self.sections == other.sections

    def __repr__(self) -> str:
        hm = ''
        if self.hardened_marker:
            assert self.hardened_marker != '"'
            hm = ', hardened_marker="{}"'.format(self.hardened_marker)

        return '{}({}, is_partial={}{})'.format(
            self.__class__.__name__, self.sections, self.is_partial, hm)

    def __str__(self) -> str:
        s_parts = [] if self.is_partial else ['m']
        for s in self.sections:
            r_parts = []
            is_hardened = None
            got_many = len(s) > 1  # if more than 1 range, will need brackets
            for start_unmasked, end_unmasked in s:
                is_start_hardened = bool(start_unmasked & HARDENED_INDEX_START)
                assert is_start_hardened == \
                    bool(end_unmasked & HARDENED_INDEX_START)
                assert is_hardened is None or is_hardened == is_start_hardened
                is_hardened = is_start_hardened

                start = start_unmasked & HARDENED_INDEX_MASK
                end = end_unmasked & HARDENED_INDEX_MASK
                if start == end:
                    r_parts.append(str(start))
                elif start == 0 and end == MAX_INDEX_VALUE:
                    r_parts.append('*')
                else:
                    r_parts.append('{}-{}'.format(start, end))
                    got_many = True  # will need brackets even if only 1 range

            assert is_hardened is not None

            hm = ''
            if is_hardened:
                assert self.hardened_marker
                hm = self.hardened_marker

            pre = '[' if got_many else ''
            post = ']' if got_many else ''

            s_parts.append('{}{}{}{}'.format(pre, ",".join(r_parts), post, hm))

        return '/'.join(s_parts)


__all__ = (
    'BIP32TemplateException',
    'BIP32TemplateExceptionUnexpectedHardenedMarker',
    'BIP32TemplateExceptionUnexpectedSpace',
    'BIP32TemplateExceptionUnexpectedCharacter',
    'BIP32TemplateExceptionUnexpectedFinish',
    'BIP32TemplateExceptionUnexpectedSlash',
    'BIP32TemplateExceptionInvalidCharacter',
    'BIP32TemplateExceptionIndexTooBig',
    'BIP32TemplateExceptionIndexHasLeadingZero',
    'BIP32TemplateExceptionPathEmpty',
    'BIP32TemplateExceptionPathTooLong',
    'BIP32TemplateExceptionPathSectionTooLong',
    'BIP32TemplateExceptionRangesIntersect',
    'BIP32TemplateExceptionRangeOrderBad',
    'BIP32TemplateExceptionRangeEqualsWildcard',
    'BIP32TemplateExceptionSingleIndexAsRange',
    'BIP32TemplateExceptionRangeStartEqualsEnd',
    'BIP32TemplateExceptionRangeStartNextToPrevious',
    'BIP32TemplateExceptionGotHardenedAfterUnhardened',
    'BIP32TemplateExceptionDigitExpected',
    'BIP32Template'
)
