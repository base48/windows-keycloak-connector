# Windows to keycloak connector
## What
This is a very simple flask application built to allow users with accounts in Keycloak create and manage accounts on a shared windows box.

## Why
I created this because messing with Active Directory and LDAP was not something I wanted to do, so instead I installed an SSH server onto the windows host and let this manage the accounts.

## How to Install
- acquire a container environment or similar, in my case it's a debian13 LXC container in proxmox
- `cd /root && git clone https://github.com/base48/windows-keycloak-connector/ && cd /root/windows-keycloak-connector/`
- create `client_secrets.json` and `windows_ssh_connection_details.env` by glancing at `.example` files provided, put them into the same directory as the python executable (`/root/windows-keycloak-connector/`)
- ensure pip is installed (`apt install python3-pip`)
- `cp ./gunicorn.service /etc/systemd/system/ && systemctl enable --now gunicorn.service`

## Debug
to see logs in a production environment - `journalctl -xu gunicorn.service --follow`
