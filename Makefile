
PYTHON=python3

test: ## Run unit tests
	cd src && ${PYTHON} -m unittest discover -s ../test
