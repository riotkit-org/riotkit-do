#
# https://github.com/riotkit-org/riotkit-do/issues/5
#
SHELL=/bin/bash
TEST_OPTS=

## Installs dependencies for all packages
deps:
	pip install -r ./requirements-dev.txt
	BASE_PATH=$$(pwd); \
	for package_directory in $$(ls ./src); do \
	  	echo ">> $${package_directory}"; \
	  	pip install -r $$BASE_PATH/src/$$package_directory/requirements.txt; \
	done

## Run tests
tests:
	set +e; \
	export RKD_BIN="python -m rkd.core" PYTHONPATH="$$(pwd)/src/core:$$(pwd)/src/process:$$(pwd)/src/pythonic"; \
	BASE_PATH=$$(pwd); \
	for package_directory in $$(ls ./src); do \
	  	echo ">> $${package_directory}"; \
	  	mkdir -p $$BASE_PATH/src/$$package_directory/build; \
	  	set -x; \
		cd "$$BASE_PATH/src/$$package_directory"; pytest ./tests --junitxml=build/tests.xml;\
	done

## Release
release: package publish

## Refresh git
refresh_git:
	git fetch --tags
	git status
	git tag -l -n

## Build local package
package: refresh_git
	BASE_PATH=$$(pwd); \
	for package_directory in $$(ls ./src); do \
		cd "$$BASE_PATH/src/$$package_directory"; ./setup.py build; ./setup.py sdist; \
	done

## Publish to PyPI
publish:
	BASE_PATH=$$(pwd); \
	for package_directory in $$(ls ./src); do \
	  	cd "$$BASE_PATH/src/$$package_directory"; \
		twine upload --disable-progress-bar --verbose \
			--username=__token__ \
			--password=${PYPI_TOKEN} \
			--skip-existing \
			dist/*; \
	done

## Build SPHINX docs
documentation:
	cd docs && sphinx-build -M html "source" "build"

## Properly tag project
tag:
	git tag -am "Version ${NUM}" ${NUM}
