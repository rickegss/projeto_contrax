#!/bin/bash

sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen
locale-gen pt_BR.UTF-8

export LANG=pt_BR.UTF-8
export LANGUAGE=pt_BR.UTF-8
export LC_ALL=pt_BR.UTF-8