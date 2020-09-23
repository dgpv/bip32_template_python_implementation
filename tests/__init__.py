try:
    import micropython  # type: ignore
    # only needed for micropython's unittest
    from .test_templates import *
except ImportError:
    pass
