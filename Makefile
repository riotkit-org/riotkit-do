
PYTHON=python3

unit_test: ## Run unit tests
	cd src && ${PYTHON} -m unittest discover -s ../test
