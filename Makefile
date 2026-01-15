.PHONY: install lint test ci

install:
	python -m pip install -e .[dev]

lint:
	ruff check .

test:
	pytest

ci: install lint test
