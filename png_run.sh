#!/usr/bin/env bash

GREEN="\e[0;32m"
RED="\e[0;31m"
NO_COLOR="\e[0m"

VENV_DIR=venv
CLI_ENTRYPOINT=app/cli.py

python_version_assert=$(python3.8 -V 2>/dev/null)
if [[ -z $python_version_assert ]]; then
    echo -e "${RED}You need python3.8 to run this program!${NO_COLOR}"
    echo -e "Please run:\n"
    echo "sudo add-apt-repository ppa:deadsnakes/ppa"
    echo "sudo apt update"
    echo "sudo apt install python3.8"
    exit 1
fi

declare -a packages_to_assert=("python3-tk"
                               "python3.8-venv"
                               "libmpc-dev"
                               )
for package in "${packages_to_assert[@]}"; do
    dpkg -s "$package" >/dev/null 2>&1 || {
        echo -e "${RED}You need $package package installed!${NO_COLOR}"
        echo -e "Please run:\n"
        echo "sudo apt update"
        echo "sudo apt install $package"
        exit 1
    }
done

if [[ ! -x $VENV_DIR ]]; then
    echo -e "${GREEN}Installing required python packages${NO_COLOR}"
    python3.8 -m venv --clear $VENV_DIR
    source $VENV_DIR/bin/activate
    
    python3.8 -m pip install --no-cache-dir --upgrade pip
    pip3.8 install -r requirements.txt

    deactivate
fi

source $VENV_DIR/bin/activate

# thanks to fire package, we can directly call classes and functions from file $CLI_ENTRYPOINT
python3.8 $CLI_ENTRYPOINT "$@"

deactivate
