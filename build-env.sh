#!/bin/bash

source .ansible-venv/bin/activate

# NB the collection is installed outside of the current directory because
#    ansible-test will ignore all files ignored by git.
export ANSIBLE_COLLECTIONS_PATH="/tmp/$USER-ansible-collections"
