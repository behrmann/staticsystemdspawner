#!/usr/bin/env python3

import argparse
import grp
import importlib.resources
import pwd
import subprocess
import sys
from pathlib import Path

DEFAULT_UNIT_PATH = Path("/run/systemd/system")
DEFAULT_UNITS = {
    "user-{uid}.slice.d/50-resource-control.conf": "slice.conf",
    "jupyterhub-singleuser-.service.d/30-hardening.conf": "hardening.conf",
    "jupyterhub-singleuser-{username}.service": "defaultserver.service",
    "jupyterhub-singleuser-{username}@.service": "namedserver.service",
}


def get_single_user(user):
    u = pwd.getpwnam(user)
    return u.pw_name, u.pw_uid


def get_all_users() -> list[tuple[str, int]]:
    return sorted((u.pw_name, u.pw_uid) for u in pwd.getpwall() if u.pw_uid >= 1000)


def get_users_in_group(g) -> list[tuple[str, int]]:
    mem = grp.getgrnam(g).gr_mem
    return sorted((u, uid) for u in mem if (uid := pwd.getpwnam(u).pw_uid) >= 1000)


def reload_units():
    subprocess.run(["systemctl", "daemon-reload"])


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate unit files for JupyterHub",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--outdir",
        help="Directory to output units to",
        default=DEFAULT_UNIT_PATH,
        type=Path,
        metavar="DIR",
    )
    parser.add_argument(
        "--reload-units",
        help="Reload the units in the service manager after generating them",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--memory",
        help="How much memory to give a user in GiB",
        default=1,
        type=int,
    )
    parser.add_argument(
        "--memory-grace",
        help="How many GiB a user may go the maximum without their server getting killed",
        default=1,
        type=int,
    )
    parser.add_argument(
        "--cores",
        help="How many many cores to give to user",
        default=1.0,
        type=float,
    )
    parser.add_argument(
        "--bindir",
        help="Directory where jupyter-singleuser-wrapper is installed to",
        default=Path(sys.executable).parent,
        type=Path,
    )
    usergroup = parser.add_mutually_exclusive_group(required=True)
    usergroup.add_argument(
        "--all-users",
        help="Generate unit files for all users.",
        action="store_true",
    )
    usergroup.add_argument(
        "--user",
        help="Users for which to generate a unit file",
        action="append",
    )
    usergroup.add_argument(
        "--group",
        help="Groups for whose users to generate a unit file",
        action="append",
    )
    args = parser.parse_args()

    if args.all_users:
        args.user = get_all_users()
    elif args.user:
        args.user = sorted(get_single_user(u) for u in args.user)
    elif args.group:
        users = set()
        for g in args.group:
            users |= set(get_users_in_group(g))
        args.user = sorted(users)

    return args


def main():
    args = parse_args()

    if not args.outdir.exists():
        print(f"Output directory {args.outdir:r} does not exist!", file=sys.stderr)
        sys.exit(1)

    for user, uid in args.user:
        for name, resource in DEFAULT_UNITS.items():
            template = importlib.resources.read_text("staticsystemdspawner.resources", resource)
            unitfile = args.outdir / name.format(username=user, uid=uid)
            content = template.format(
                username=user,
                uid=uid,
                bindir=args.bindir,
                cores=f"{args.cores:.0%}",
                memory=args.memory,
                memorymax=(args.memory + args.memory_grace),
            )
            if unitfile.parent.relative_to(args.outdir) != Path("."):
                unitfile.parent.mkdir(parents=True, exist_ok=True)
            unitfile.write_text(content)

    if args.reload_units:
        reload_units()
