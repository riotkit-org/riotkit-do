#!/bin/sh
set -xe

virtualenv .venv
source ./.venv/bin/activate
pip install -r requirements.txt
