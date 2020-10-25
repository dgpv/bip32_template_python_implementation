[![Package version](https://img.shields.io/pypi/v/bip32template.svg)](https://pypi.python.org/pypi/bip32template)
[![Package license](https://img.shields.io/pypi/l/bip32template.svg)](https://pypi.python.org/pypi/bip32template)
[![Python versions](https://img.shields.io/pypi/pyversions/bip32template.svg)](https://pypi.python.org/pypi/bip32template)
[![Build Status](https://travis-ci.org/Simplexum/python-bitcointx.svg?branch=master)](https://pypi.python.org/pypi/python-bitcointx)

# Python implementation of BIP32 path template parser finite state machine

(compatible with [micropython](https://micropython.org/))

This repository contains an implementation of specification of the parser for BIP32 path templates
described in [bip-path-templates.mediawiki](https://github.com/dgpv/bip32_template_parse_tplaplus_spec/blob/master/bip-path-templates.mediawiki)
and specified by TLA+ specification at [https://github.com/dgpv/bip32_template_parse_tplaplus_spec](https://github.com/dgpv/bip32_template_parse_tplaplus_spec)

The implementation is in `bip32template/__init__.py`

The tests is in `tests/`

To run tests on micropython, use `micropython_unittest.py` (you will need micropython-os.path module to run the tests)

to run static type checking, use `run_mypy.sh`

Example usage:

```python
>>> from bip32template import BIP32Template
>>> tpl=BIP32Template.parse('m/0h/[1-9,23]/*')
>>> tpl
BIP32Template([[(2147483648, 2147483648)], [(1, 9), (23, 23)], [(0, 2147483647)]], is_partial=False, hardened_marker="h")
>>> tpl.sections
[[(2147483648, 2147483648)], [(1, 9), (23, 23)], [(0, 2147483647)]]
>>> str(tpl)
'm/0h/[1-9,23]/*'
>>> str(BIP32Template(tpl.sections, hardened_marker="'", is_partial=True))
"0'/[1-9,23]/*"
>>> tpl.to_path() is None
True
>>> tpl.match([0x80000000, 3, 33])
True
>>> tpl.match([0x80000000, 99, 33])
False
>>> BIP32Template.parse('m/0/1/[2-3]', is_format_onlypath=True)
...
bip32template.BIP32TemplateExceptionUnexpectedCharacter: unexpected character at position 7
>>> ptpl = BIP32Template.parse('m/0h/1/2', is_format_onlypath=True)
>>> ptpl
BIP32Template([[(2147483648, 2147483648)], [(1, 1)], [(2, 2)]], is_partial=False, hardened_marker="h")
>>> ptpl.to_path()
[2147483648, 1, 2]
>>> tpl.match(ptpl.to_path())
True
>>> str(BIP32Template.from_path(ptpl.to_path(), is_partial=True))
'0h/1/2'
>>> str(BIP32Template.from_path(ptpl.to_path(), is_partial=False, hardened_marker="'"))
"m/0'/1/2"
```

## Authors and contributors

This implementation was created by Dmitry Petukhov (https://github.com/dgpv/)

## License

Released under MIT license.
