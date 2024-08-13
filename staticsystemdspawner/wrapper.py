import os
import shlex
import sys
from pathlib import Path
from typing import Any, NoReturn


def die(msg: str, rc: int = 1) -> NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(rc)


def wrapped_main() -> Any:
    """Call the main from jupyterhub.singleuser, but set a few environment variables."""
    from jupyterhub.singleuser import main  # type: ignore

    credentials_directory = os.getenv("CREDENTIALS_DIRECTORY")
    if credentials_directory is None:
        die("No CREDENTIALS_DIRECTORY for jupyterhub-singleuser-wrapper!")
    credentials_directory = Path(credentials_directory)

    envfile = credentials_directory / "spawnerconf_envfile"
    if not envfile.exists():
        die("No envfile for jupyterhub-singleuser-wrapper!")

    for line in envfile.read_text().splitlines():
        key, sep, val = line.partition("=")
        try:
            os.environ[key] = shlex.split(val)[0]
        except KeyError:
            die(f"Illegal environment definition in {line=}")

    keyfile = credentials_directory / "spawnerconf_key"
    certfile = credentials_directory / "spawnerconf_cert"
    cafile = credentials_directory / "spawnerconf_cafile"
    if keyfile.exists() and certfile.exists() and cafile.exists():
        os.environ["JUPYTERHUB_SSL_KEYFILE"] = os.fspath(keyfile)
        os.environ["JUPYTERHUB_SSL_CERTFILE"] = os.fspath(certfile)
        os.environ["JUPYTERHUB_SSL_CLIENT_CA"] = os.fspath(cafile)

    return main()
