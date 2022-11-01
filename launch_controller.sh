#!/bin/sh

export PYTHONPATH=${WEBOTS_HOME}/lib/controller/python38
export PYTHONIOENCODING=UTF-8

# default internal docker ip
export WEBOTS_CONTROLLER_URL=tcp://172.17.0.1:3005
python3 controllers/edit_me/edit_me.py
