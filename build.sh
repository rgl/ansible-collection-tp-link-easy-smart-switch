#!/bin/bash
source build-env.sh
set -euxo pipefail

# build.
rm -rf "$ANSIBLE_COLLECTIONS_PATH/ansible_collections/rgl/tp_link_easy_smart_switch" rgl-tp_link_easy_smart_switch-*.tar.gz
ansible-galaxy collection build --verbose
tar tf rgl-tp_link_easy_smart_switch-*.tar.gz

# install.
ansible-galaxy collection install --verbose rgl-tp_link_easy_smart_switch-*.tar.gz

# sanity test.
pushd "$ANSIBLE_COLLECTIONS_PATH/ansible_collections/rgl/tp_link_easy_smart_switch"
ansible-test sanity --local --python 3.8 #-vvv
popd
