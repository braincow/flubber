PYTHON ?= python
PIP ?= pip

VENV = virtualenv
VENV_ARGS = -p $(PYTHON)3
VENV_DIR = $(CURDIR)/.venv

all: install

$(VENV_DIR): requirements-dev.txt
	$(VENV) $(VENV_ARGS) "$(VENV_DIR)"
	. "$(VENV_DIR)"/bin/activate; export PYTHONPATH="$(VENV_DIR)"; "$(VENV_DIR)"/bin/pip install -r $<

.PHONY: env
env: $(VENV_DIR)

.PHONY: install
install:
	$(PYTHON) setup.py install

.PHONY: check
check: clean
	. "$(VENV_DIR)"/bin/activate; tox

.PHONY: clean
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d | xargs rm -fr

.PHONY: distclean
distclean: clean
	rm -fr *.egg *.egg-info/ .eggs/

.PHONY:
mostlyclean: clean distclean
	rm -rf "$(VENV_DIR)"

run:
	. "$(VENV_DIR)"/bin/activate; python -m flubber