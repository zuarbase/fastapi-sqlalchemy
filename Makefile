all: flake8 pylint test

flake8: flake8_pkg flake8_tests
.PHONY: flake8

flake8_pkg:
	flake8 fastapi_sqlalchemy
.PHONY: flake8_pkg

flake8_tests:
	flake8 tests
.PHONY: flake8_tests

pylint: pylint_pkg pylint_tests
.PHONY: pylint

pylint_pkg:
	pylint fastapi_sqlalchemy
.PHONY: pylint_pkg

pylint_tests:
	pylint tests  --disable=missing-docstring,unused-argument
.PHONY: pylint_tests

test:
	pytest -xvv tests
.PHONY: test

pyenv:
	virtualenv -p python3 pyenv
	pyenv/bin/pip install -e .[dev,prod]
.PHONY: pyenv
