#
# https://github.com/riotkit-org/riotkit-do/issues/5
#
TEST_OPTS=
PYTHONPATH = $(shell echo "$$(pwd)/src:$$(pwd)/../../src")

## Run tests
tests:
	cd src && export PYTHONPATH=${PYTHONPATH} && python3 -u -m unittest discover -s ../test ${TEST_OPTS}

## Release
release: build publish

## Build local package
package:
	./setup.py build
	./setup.py sdist

## Publish to PyPI
publish:
	twine upload --disable-progress-bar --verbose \
		--username=$${QUAY_USERNAME} \
		--password=$${QUAY_PASSWORD} \
		--skip-existing \
		dist/*
