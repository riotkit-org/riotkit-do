
PYTHON=python3

unit_test: ## Run unit tests
	cd src && ${PYTHON} -m unittest discover -s ../test

run: ## Test run
	cd src && ${PYTHON} -m rkd --help
