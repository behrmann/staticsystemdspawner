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

## Installation ##

You cannot install it from PyPI yet, but need to install it from git

```bash
pip install <url to the repo>
```

You can enable it for your jupyterhub with the following lines in your
`jupyterhub_config.py` file

```python
c.JupyterHub.spawner_class = 'staticsystemdspawner.StaticSystemdSpawner'
```

Note that to confirm systemdspawner has been installed in the correct jupyterhub
environment, a newly generated config file should list `staticsystemdspawner` as one of the
available spawner classes in the comments above the configuration line.

## Getting help ##

We encourage you to ask questions in the repository.

## License ##

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
