"""
Nuke Core Utilities
Version: 1.0.0
A comprehensive toolkit for Nuke pipeline development and automation
"""

__version__ = "0.2.1"
__author__ = "Nuke Pipeline Team"

# Core modules
from .core import *
from .data import *
from .graph import *
from .nodes import *
from .project import *
from .render import *
from .selection import *
from .utils import *

# Initialize logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

print(f"Nuke Core Utilities v{__version__} loaded successfully")
