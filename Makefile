PYTHON ?= python
PIP ?= pip

VENV = virtualenv
VENV_ARGS = -p $(PYTHON)3
VENV_DIR = $(CURDIR)/.venv

all: install

$(VENV_DIR): requirements-dev.txt
	$(VENV) $(VENV_ARGS) "$(VENV_DIR)"
	. "$(VENV_DIR)"/bin/activate; export PYTHONPATH="$(VENV_DIR)"; "$(VENV_DIR)"/bin/pip install -r $<

env: $(VENV_DIR)

install:
	$(PYTHON) setup.py install

tox: clean env
	. "$(VENV_DIR)"/bin/activate; tox

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d | xargs rm -fr

distclean: clean
	rm -fr *.egg *.egg-info/ .eggs/ .tox/ .pytest_cache/ build/ dist/

mostlyclean: clean distclean
	rm -rf "$(VENV_DIR)"

run:
	. "$(VENV_DIR)"/bin/activate; python -m flubber

distribution: tox distclean
	. "$(VENV_DIR)"/bin/activate; python setup.py sdist
