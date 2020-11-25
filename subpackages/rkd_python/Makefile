#
# https://github.com/riotkit-org/riotkit-do/issues/5
#
TEST_OPTS=
PYTHONPATH = $(shell echo "$$(pwd):$$(pwd)/../../")

## Run tests
tests: |
	export PYTHONPATH=${PYTHONPATH}; \
	python3 -u -m unittest discover -s ./test ${TEST_OPTS}

## Release
release: package publish

## Build local package
package:
	./setup.py build
	./setup.py sdist

## Publish to PyPI
publish:
	twine upload --disable-progress-bar --verbose \
		--username=__token__ \
		--password=$${PYPI_TOKEN} \
		--skip-existing \
		dist/*
