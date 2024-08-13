from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="jupyterhub-staticsystemdspawner",
    version="0.1",
    description="JupyterHub Spawner using systemd unit files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jörg Behrmann",
    author_email="behrmann@physik.fu-berlin.de",
    license='3 Clause BSD',
    packages=['staticsystemdspawner'],
    entry_points={
        "jupyterhub.spawners": [
            "staticsystemdspawner = staticsystemdspawner:StaticSystemdSpawner",
        ],
    },
    install_requires=[
        "jupyterhub>=0.9",
        "tornado>=5.0",
    ],
)
