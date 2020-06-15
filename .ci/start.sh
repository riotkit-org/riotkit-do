#!/bin/bash

cd .ci
cd ../ && docker build ./ -f .ci/Dockerfile -t builder:latest --build-arg PYTHON_VERSION=${TRAVIS_PYTHON_VERSION}
cd .ci && docker-compose -p ci up -d

exit $?
