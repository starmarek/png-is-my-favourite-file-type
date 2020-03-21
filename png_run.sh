#!/bin/bash

VENV_DIR=venv

if [[ ! -x $VENV_DIR ]]; then
    echo "Installing required packages"
    python3 -m venv --clear $VENV_DIR
    source $VENV_DIR/bin/activate
    
    python3 -m pip install --no-cache-dir --upgrade pip
    pip3 install -r requirements.txt

    deactivate
fi

source $VENV_DIR/bin/activate

echo hello

deactivate