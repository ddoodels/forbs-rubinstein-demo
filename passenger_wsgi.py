import os
import sys

INTERP = os.path.expanduser("~/forbsenv/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.getcwd())

from app import app as application
