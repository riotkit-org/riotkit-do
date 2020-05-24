#
# https://github.com/riotkit-org/riotkit-do/issues/5
#
TEST_OPTS=

## Run tests
tests:
	cd src && python3 -m unittest discover -s ../test ${TEST_OPTS}

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
