#
# https://github.com/riotkit-org/riotkit-do/issues/5
#
SHELL=/bin/bash
TEST_OPTS=

## Run tests
tests: refresh_git
	export PYTHONPATH="$$(pwd):$$(pwd)/subpackages/rkd_python"; \
	python3 -m unittest discover -s ./test ${TEST_OPTS}

## Release
release: package publish

## Refresh git
refresh_git:
	git fetch --tags
	git status
	git tag -l -n

## Build local package
package: refresh_git
	./setup.py build
	./setup.py sdist

## Publish to PyPI
publish:
	twine upload --disable-progress-bar --verbose \
		--username=__token__ \
		--password=${PYPI_TOKEN} \
		--skip-existing \
		dist/*

## Build SPHINX docs
documentation:
	cd docs && sphinx-build -M html "source" "build"

## Properly tag project
tag:
	git tag -am "Version ${NUM}" ${NUM}

uninstall:
	sudo pip uninstall rkd || true
	pip uninstall rkd || true
	sudo rm -rf /usr/lib/rkd /usr/share/rkd
