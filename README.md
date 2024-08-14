# staticsystemdspawner

The **staticsystemdspawner** enables JupyterHub to spawn single-user notebook
servers using the [systemd](https://www.freedesktop.org/wiki/Software/systemd/)
service manager, that is available on all current major Linux distributions.

This project is a friendly fork of [systemdspawner](https://github.com/jupyterhub/systemdspawner).

## How is this different from systemdspawner?

systemdspawner uses `systemd-run` to start transient units that are constructed
on the fly by systemdspawner itself. This makes it necessary for JupyterHub to
be able to use `systemd-run`.

staticsystemdspawner instead uses pre-generated unit files that only need to be
started, which makes the scope of what to allow JupyterHub to do smaller and
also allows to customise the units to a much greater degree without the need to
pipe all systemd options through the spawner.

## Features

The features of staticsystemdspawner are broadly similar to those of
systemdspawner, but very open-ended. If you can think of it, you can probably
hack it up without having to touch the code of systemdspawner.

You can use everything in the systemd suite, which gets you all sorts of
sandboxing and resource control options, see the man pages
- `man systemd.service`,
- `man systemd.exec`, and
- `man systemd.resource-control`
for details and `man systemd.directives` if need an index.

## Requirements

### Systemd

staticsystemdspawner requires you to use a Linux Distro that ships with at least
systemd v252, which shipped by default in Debian bookworm (released in 2023),
but is also available in Debian bullseye (released in 2021) via Debian
backports. It might also work with systemd v247 available in Debian bullseye,
but this has not been tested, we recommend using at least version v252.

Consult `systemctl --version` for your version information.

### Polkit

To control unit lifecycle staticsystemdspawner uses polkit. A version larger
than polkit 105 is needed. These are available in Debian starting with Debian
bookworm or from the experimental repositories before that.

### Local unit files for all users

You will have to add local unit files for all users.

### Linux Distro compatibility

Anything with a recent systemd (v252 or newer) and polkit (newer than 105),
should work.

#### Debian bookworm

This has been tested to run on Debian bookworm and supports all features without
additional repositories.

#### Debian bullseye

This has not been tested but might work when using the `policykit-1` package
from the experimental repo. It might also need `systemd` from the backports
repository.

#### Ubuntu 24.04 LTS

This has not been tested but should have everything necessary to run
staticsystemdspawner.

#### Ubuntu 22.04 LTS

The polkit version in this Ubuntu release is still 105. If you can backport a
newer version, that might be sufficient.

#### RHEL and derivatives

Sufficient versions should be available starting with RHEL9.

## Installation

You cannot install it from PyPI yet, but need to install it from git

```bash
pip install git+https://<url to the repo>
```

You can enable it for your jupyterhub with the following lines in your
`jupyterhub_config.py` file

```python
c.JupyterHub.spawner_class = 'staticsystemdspawner.StaticSystemdSpawner'
```

Note that to confirm systemdspawner has been installed in the correct jupyterhub
environment, a newly generated config file should list `staticsystemdspawner` as one of the
available spawner classes in the comments above the configuration line.

The Hub itself can be run as an unprivileged user
```ini
# jupyterhub.service
[Unit]
Description=Jupyterhub
After=network.target postgresql.service jupyterhub-httpproxy.service
Wants=network.target postgresql.service
PartOf=jupyterhub.target

[Service]
User=jupyter
Environment="PATH=/opt/jupyter/hubenv/bin:/usr/bin:/usr/local/bin:/bin"
ConfigurationDirectory=jupyterhub
RuntimeDirectory=jupyterhub
StateDirectory=jupyterhub

LoadCredentialEncrypted=jupyterhub.dbpassword
LoadCredentialEncrypted=jupyterhub.authcred
LoadCredentialEncrypted=jupyterhub.cookiesecret
LoadCredentialEncrypted=jupyterhub.proxy.authtoken

ExecStart=/opt/jupyter/hubenv/bin/jupyterhub --config ${CONFIGURATION_DIRECTORY}/jupyterhub_config.py

PrivateTmp=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
WorkingDirectory=/var/lib/jupyterhub
```
and it is recommended to start it as a part of a target, e.g.
```ini
[Unit]
Description=JupyterHub API services
Wants=jupyterhub.service jupyterhub-httpproxy.service nginx.service

[Install]
WantedBy=multi-user.target
```
assuming the existence of a separate `jupyterhub-httpproxy.service` and running the Hub behind Nginx as a proxy.

### Aside: Running the configurable http proxy as dynamic user

```ini
# jupyterhub-httpproxy.service
[Unit]
Description=JupyterHub HTTP proxy
After=network-online.target
PartOf=jupyterhub.target

[Service]
User=jupyterproxy
DynamicUser=yes

LoadCredentialEncrypted=jupyterhub.proxy.authtoken
ExecStart=/opt/jupyter/configurable-http-proxy-wrapper \
        --ip 127.0.0.1 \
        --port 8000 \
        --api-ip 127.0.0.1 \
        --api-port 8001 \
        --host-routing \
        --default-target=http://127.0.0.1:8081 \
        --error-target=http://127.0.0.1:8081/hub/error

SuccessExitStatus=0 2

PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
```

### Polkit

To authorize JupyterHub to start and stop units a polkit rule is used.
```js
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units") {
        polkit.log("action=" + action);
        polkit.log("subject=" + subject);
        if (action.lookup("unit").match(/^jupyterhub-singleuser-[a-z][a-z0-9]{0,30}.service$/) ||
            action.lookup("unit").match(/^jupyterhub-singleuser-[a-z][a-z0-9]{0,30}@[a-zA-Z0-9_\\]+.service$/)) {
            var verb = action.lookup("verb");
            if ((verb == "start" || verb == "stop" || verb == "reset-failed") && subject.user == "jupyter") {
                return polkit.Result.YES;
            }
        }
    }
});
```

If you have a sufficiently new polkit (124 or newer) you could also add
additional checks using `subject.system_unit == "jupyterhub.service"` to check
whether the this is being called from the context of `jupyterhub.service` and
`subject.no_new_privileges == true` that the `NoNewPrivileges=` setting on the
Hub is set.

### Unit files

This package ships with a script `jupyter-staticsystemdspawner-unitgenerator`
that can be used to generate unit files for users. These are meant as examples
and should be changed to fit the needs of your deployment.

They use a wrapper script (`jupyter-singleuser-wrapper`) for environment setup,
since JupyterHub usually reads its configuration from environment files. Since
the hub is running as an unprivileged users and so are the singleuser servers,
systemd credentials are used to pass information from the hub to the singleuser
servers. This wrapper script will therefore be needed to start the singleuser
servers.

An example for such a file:
```ini
[Unit]
Description=Jupyterhub Single-User Server for user foobar

[Service]
Type=simple
User=foobar

Environment="PATH=/opt/jupyter/hubenv/bin:/usr/bin:/usr/local/bin"

LoadCredential=spawnerconf:/run/jupyterhub/spawnerconf/foobar/default
ExecStart=/opt/jupyter/hubenv/bin/jupyter-singleuser-wrapper

WorkingDirectory=/home/foobar
StateDirectory=jupyterhub-foobar

# ensure that one singleuser server going over the memory limit
# does not kill all the user's servers
OOMPolicy=continue
# use the jupyterhub PAM module for session setup (see below)
PAMName=jupyterhub
```

If you want to configure settings for all singleuser servers, it is recommend to use drop in configuration and make use of the dash namespacing of units, e.g.
```ini
# jupyterhub-singleuser-.service.d/30-hardening.conf
[Service]
PrivateTmp=yes
PrivateDevices=yes
ProtectSystem=strict
ProtectKernelTunables=yes
ProtectControlGroups=yes
ReadWritePaths=/home/%j
NoNewPrivileges=yes
```

If you want to configure resource constraints, it is recommend to do that via a
slice unit and configuring `Slice=` for the singleuser unit. For an alternative
approach using PAM see below.

### PAM config

When using the `PAMName` service setting an existing PAM module needs to be
provided that will do session setup. This setting is independent of the used
authenticator.

Using a PAM module one can register JupyterHub singleuser sessions with `loginctl`.

The following example is adapted from the `login` PAM module.
```
#
# The PAM configuration file for the JupyterHub systemd-spawner service
#
# SELinux needs to be the first session rule. This ensures that any
# lingering context has been cleared. Without this it is possible
# that a module could execute code in the wrong domain.
# When the module is present, "required" would be sufficient (When SELinux
# is disabled, this returns success.)
session [success=ok ignore=ignore module_unknown=ignore default=bad] pam_selinux.so close

# Sets the loginuid process attribute
session    required     pam_loginuid.so

# SELinux needs to intervene at login time to ensure that the process
# starts in the proper default security context. Only sessions which are
# intended to run in the user's context should be run after this.
# pam_selinux.so changes the SELinux context of the used TTY and configures
# SELinux in order to transition to the user context with the next execve()
# call.
session [success=ok ignore=ignore module_unknown=ignore default=bad] pam_selinux.so open
# When the module is present, "required" would be sufficient (When SELinux
# is disabled, this returns success.)

# This module parses environment configuration file(s)
# and also allows you to use an extended config
# file /etc/security/pam_env.conf.
#
# parsing /etc/environment needs "readenv=1"
session       required   pam_env.so readenv=1
# locale variables are also kept into /etc/default/locale in etch
# reading this file *in addition to /etc/environment* does not hurt
session       required   pam_env.so readenv=1 envfile=/etc/default/locale

# Sets up user limits according to /etc/security/limits.conf
# (Replaces the use of /etc/limits in old login)
session    required   pam_limits.so

# Prints the last login info upon successful login
# (Replaces the `LASTLOG_ENAB' option from login.defs)
session    optional   pam_lastlog.so

# Create a new session keyring.
session    optional   pam_keyinit.so force revoke

# Standard Un*x account and session
@include common-session
```

When using such a setup the resource constraints for a user can be configured on
their user slice, e.g.
```ini
# user-123456.slice
[Slice]
TasksMax=33%
CPUQuota=400%
MemoryHigh=16G
MemoryMax=17G
```

## Configuration

For the most part configuration besides setting the spawner class should not be
required.

### `default_server_unit_name_template`

The name for the unit that is started by the spawner. It defaults to
`jupyterhub-singleuser-{USERNAME}.service` and the username is interpolated by
the spawner. Since the user is identified by the last part of the name after the
last dash and before the `.service` extension, names not following this format
will probably not work as exptected.

### `named_server_unit_name_template`

The name for the unit that is started by the spawner. It defaults to
`jupyterhub-singleuser-{USERNAME}@.service` and the username is interpolated by
the spawner. Since the user is identified by the last part of the name after the
last dash and before the @, names not following this format will probably not
work as exptected.

The unit instance passed in will be the name of the named server escaped with
`systemd-escape`, i.e. to get the unescaped name you will have to use the `%I`
specifier in the unit file.

### `unit_generator`

The name of a template unit started when a user unit does not exist. It can be
used to generate them. Defaults to `None`, which means unit files will have to
be generated for all users beforehand.

## Getting help

We encourage you to ask questions in the repository.

## License

We use a shared copyright model that enables all contributors to maintain the
copyright on their contributions.

All code is licensed under the terms of the revised BSD license.

## Resources

### JupyterHub and systemdspawner

- [Documentation for JupyterHub](http://jupyterhub.readthedocs.io/en/latest/) | [PDF (latest)](https://media.readthedocs.org/pdf/jupyterhub/latest/jupyterhub.pdf) | [PDF (stable)](https://media.readthedocs.org/pdf/jupyterhub/stable/jupyterhub.pdf)
- [Documentation for JupyterHub's REST API](http://petstore.swagger.io/?url=https://raw.githubusercontent.com/jupyter/jupyterhub/master/docs/rest-api.yml#/default)

### Jupyter

- [Documentation for Project Jupyter](http://jupyter.readthedocs.io/en/latest/index.html) | [PDF](https://media.readthedocs.org/pdf/jupyter/latest/jupyter.pdf)
- [Project Jupyter website](https://jupyter.org)
