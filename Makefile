#
# https://github.com/riotkit-org/riotkit-do/issues/5
#
SHELL=/bin/bash
TEST_OPTS=
PYTHONPATH = $(shell echo "$$(pwd)/src:$$(pwd)/subpackages/rkd_python/src")

## Run tests
tests:
	source /home/travis/virtualenv/python${TRAVIS_PYTHON_VERSION}*/bin/activate; \
	export PYTHONPATH=$${PYTHONPATH}:${PYTHONPATH}; cd src && python3 -m unittest discover -s ../test ${TEST_OPTS}

## Release
release: package publish

## Build local package
package:
	source /home/travis/virtualenv/python${TRAVIS_PYTHON_VERSION}*/bin/activate; \
	pip install -r requirements.txt \
	pip install -r ./subpackages/rkd_python/requirements.txt \
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

