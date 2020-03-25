#!/bin/bash

GREEN="\e[0;32m"
NO_COLOR="\e[0m"

VENV_DIR=venv
CLI_ENTRYPOINT=app/cli.py

if [[ ! -x $VENV_DIR ]]; then
    echo -e "${GREEN}Installing required packages${NO_COLOR}"
    python3 -m venv --clear $VENV_DIR
    source $VENV_DIR/bin/activate
    
    python3 -m pip install --no-cache-dir --upgrade pip
    pip3 install -r requirements.txt

    deactivate
fi

source $VENV_DIR/bin/activate

# thanks to fire package, we can directly call classes and functions from file $CLI_ENTRYPOINT
python3 $CLI_ENTRYPOINT "$@"

deactivate
