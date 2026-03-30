#!/usr/bin/env bash
source windows_ssh_connection_details.env
if [ -n "$DEBUG" ]; then
  pip install Flask Flask-OIDC paramiko
  export FLASK_APP=main.py
  flask run
else
  pip install Flask Flask-OIDC paramiko gunicorn --break-system-packages
  gunicorn -w 1 'main:app' -b 0.0.0.0:80
fi;
