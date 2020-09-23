#!/usr/bin/env micropython

import unittest
import sys

try:
    import os.path
except ImportError:
    print("Error importing os.path: Please install micropython-os.path module from pip")
    sys.exit(-1)

unittest.main('tests.test_templates')
