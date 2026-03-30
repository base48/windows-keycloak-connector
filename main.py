from flask import Flask, render_template, redirect
from flask_oidc import OpenIDConnect
from flask import g, session
import os
import paramiko
from paramiko.client import AutoAddPolicy

windows_ssh_host = os.getenv('WINDOWS_SSH_HOST', "windows")
windows_ssh_username = os.getenv('WINDOWS_SSH_USERNAME', "admin")
windows_ssh_pass = os.getenv('WINDOWS_SSH_PASS', "admin")

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': "somethingsomething",
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': 'client_secrets.json', # change client_secrets.json.example to fit your keycloak setup
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_SERVER_METADATA_URL': 'https://sso.base48.cz/realms/hackerspace/.well-known/openid-configuration',
    'OIDC_COOKIE_SECURE': False, # Very important when working with server without ssl
    'OIDC_ID_TOKEN_COOKIE_SECURE': False, # Very important when working with server without ssl
})
oidc = OpenIDConnect(app)

def ssh_exec(cmd):
    print("executing:", cmd)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    ssh.connect(windows_ssh_host, username=windows_ssh_username, password=windows_ssh_pass)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    ssh_stdout = ssh_stdout.read().decode()
    ssh.close()
    return ssh_stdout


def generate_password():
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(8))
    return password


def list_users():
    cmd = "wmic UserAccount get Name"
    result = ssh_exec(cmd).split(f'\r\r\n')
    result = [_.rstrip() for _ in result]
    print(result)
    return result


def create_user(username, password=None):
    if password is None:
        password = generate_password()
    cmd = f"net user {username} {password} /add"
    print("[SSH] creating a user", username)
    ssh_exec(cmd)


def reset_password(username, password=None):
    if password is None:
        password = generate_password()
    cmd = f"net user {username} {password}"
    print("[SSH] resetting password for user", username)
    ssh_exec(cmd)



@app.route('/')
def hello():
    if g.oidc_user.logged_in:
        print("KEYCLOAK: user logged in, email:", session["oidc_auth_profile"].get('email'))
        # if the user is not created
        if g.oidc_user.profile.get('preferred_username') not in list_users():
            return render_template('index.html',
                                   logged_in=True,
                                   account_created=False,
                                   username=g.oidc_user.profile.get('preferred_username')
                                   )
        else:
            print("SSH: User exists on target windows host. username:", g.oidc_user.profile.get('preferred_username'))
            return render_template('index.html',
                                   logged_in=True,
                                   account_created=True,
                                   username=g.oidc_user.profile.get('preferred_username'),
                                   )

    return render_template('index.html', logged_in=False)

@app.route('/login')
@oidc.require_login
def login():
    return redirect("/", code=302)

# create a new account and set pass
@app.route('/create')
@oidc.require_login
def create():
    if g.oidc_user.logged_in:
        if g.oidc_user.profile.get('preferred_username') not in list_users():
            password = generate_password()
            create_user(username=session["oidc_auth_profile"]["preferred_username"], password=password)
            return render_template('conninfo.html',
                                   logged_in=True,
                                   username=g.oidc_user.profile.get('preferred_username'),
                                   password=password
                                   )

# there is an account and reset the pass
@app.route('/reset')
@oidc.require_login
def reset():
    if g.oidc_user.logged_in:
        # if the user is not created
        if g.oidc_user.profile.get('preferred_username') not in list_users():
            return redirect("/", code=302)
        else:
            password = generate_password()
            reset_password(username=session["oidc_auth_profile"]["preferred_username"], password=password)
            return render_template('conninfo.html',
                                   logged_in=True,
                                   username=g.oidc_user.profile.get('preferred_username'),
                                   password=password
                                   )
    return redirect("/", code=302)
