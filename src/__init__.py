"""
SRC Package Initialization
This file ensures Python treats 'src' as a package.
It also allows direct imports of key modules.
"""

# Optional: Import key modules to make them accessible directly
from .genesis import create_genesis_block
from .pow import validate_block
