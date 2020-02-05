import io

try:
    file_types = (file, io.IOBase)
except NameError:
    file_types = io.IOBase
