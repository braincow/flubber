#!/bin/bash

# source python virtual environment
source .venv/bin/activate

# init PYTHONPATH to be the location for virtual environment
PYTHONPATH=.venv/

# run pip to install vext stuff
pip install vext
pip install vext.gi