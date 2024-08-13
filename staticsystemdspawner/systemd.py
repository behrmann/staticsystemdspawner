"""
Systemd service utilities.

Contains functions to start, stop & poll systemd services.
Probably not very useful outside this spawner.
"""

import asyncio
import subprocess


async def service_running(unit_name):
    """
    Return true if service with given name is running (active).
    """
    proc = await asyncio.create_subprocess_exec(
        "systemctl",
        "is-active",
        unit_name,
        # hide stdout, but don't capture stderr at all
        stdout=asyncio.subprocess.DEVNULL,
    )
    ret = await proc.wait()

    return ret == 0


async def service_failed(unit_name):
    """
    Return true if service with given name is in a failed state.
    """
    proc = await asyncio.create_subprocess_exec(
        "systemctl",
        "is-failed",
        unit_name,
        # hide stdout, but don't capture stderr at all
        stdout=asyncio.subprocess.DEVNULL,
    )
    ret = await proc.wait()

    return ret == 0


async def start_service(unit_name):
    """
    Start service with given name.

    Throws CalledProcessError if starting fails
    """
    proc = await asyncio.create_subprocess_exec("systemctl", "start", unit_name)
    await proc.wait()


async def stop_service(unit_name):
    """
    Stop service with given name.

    Throws CalledProcessError if stopping fails
    """
    proc = await asyncio.create_subprocess_exec("systemctl", "stop", unit_name)
    await proc.wait()


async def reset_service(unit_name):
    """
    Reset service with given name.

    Throws CalledProcessError if resetting fails
    """
    proc = await asyncio.create_subprocess_exec("systemctl", "reset-failed", unit_name)
    await proc.wait()


def fill_template_name(template, instance):
    """
    Fill instance name in unit template.
    """
    cmd = ["systemd-escape", f"--template={template}", instance]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE)
    return proc.stdout.strip()


def escape_name(name):
    """
    Fill instance name in unit template.
    """
    cmd = ["systemd-escape", name]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE)
    return proc.stdout.strip()


async def unit_exists(unit_name):
    """
    Check if a unit exists.
    """
    proc = await asyncio.create_subprocess_exec("systemctl", "cat", unit_name, stdout=asyncio.subprocess.DEVNULL)
    ret = await proc.wait()
    return ret == 0
