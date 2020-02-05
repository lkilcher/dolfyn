import sys
import io

if sys.version_info >= (3, 0):
    from pathlib import Path
else:
    # Python 2
    from pathlib2 import Path

try:
    file_types = (file, io.IOBase)
except NameError:
    file_types = io.IOBase
