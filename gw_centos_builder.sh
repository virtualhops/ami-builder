#!/bin/sh

if [ -f gw_centos_builder.tar ]; then
       rm -f gw_centos_builder.tar
fi       

tar cvf gw_centos_builder.tar gw_centos_builder.py parser_for_builder.py gw_centos_config.yaml
packer build gw_centos_builder.json
