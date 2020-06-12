#
# https://github.com/riotkit-org/riotkit-do/issues/5
#
TEST_OPTS=
PYTHONPATH = $(shell echo "$$(pwd)/src:$$(pwd)/subpackages/rkd_python/src")

## Run tests
tests:
	export PYTHONPATH=${PYTHONPATH}; cd src && python3 -m unittest discover -s ../test ${TEST_OPTS}

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

## Build SPHINX docs
documentation:
	cd docs && sphinx-build -M html "source" "build"

