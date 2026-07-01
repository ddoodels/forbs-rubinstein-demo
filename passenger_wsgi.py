import os
import sys


INTERP = "/var/www/u3565198/data/forbsenv/bin/python"

if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.getcwd())

from hello import application  # noqa: E402

