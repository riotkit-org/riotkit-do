#!/bin/sh
set -e

if test -d .venv; then
    echo "source ./.venv/bin/activate"
    exit 0
fi

virtualenv .venv > .venv-setup.log 2>&1
source ./.venv/bin/activate
pip install -r requirements.txt >> .venv-setup.log 2>&1
echo "source ./.venv/bin/activate"
