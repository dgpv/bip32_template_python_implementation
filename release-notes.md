# bip32template release notes

## v0.0.4

Make apostrophe (') the default hardened marker, as this is more common default option

## v0.0.3

Remove unnecessary path length checks (removed in the spec, too)

Improve error checks in BIP32Template() direct instantiation

Improve test coverage

## v0.0.2

Use 'h' as default for `hardened_marker` argument of `BIP32Template.__init__()`

Add `BIP32Template.from_path()` classmethod to create BIP32Template from an
iterable of integers

## v0.0.1

Initial release
