#!/bin/bash

export PYTHONPATH=../../src:./src

exec python3 -m rkd "$@"
