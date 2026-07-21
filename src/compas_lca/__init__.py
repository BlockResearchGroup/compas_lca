from __future__ import print_function

import os


__author__ = ["Eric Wuite", "Li Chen"]
__copyright__ = "BRG"
__license__ = "MIT License"
__email__ = "e.b.wuite@gmail.com, leochen1990@gmail.com"
__version__ = "1.0.0"


HERE = os.path.dirname(__file__)

HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))


__all__ = ["HOME", "DATA", "DOCS", "TEMP"]
