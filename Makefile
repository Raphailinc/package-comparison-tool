.PHONY: install lint test ci

install:
\tpython -m pip install -e .[dev]

lint:
\truff check .

test:
\tpytest

ci: install lint test
