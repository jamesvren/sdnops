#!/usr/bin/env python3
import asyncio
from util import logger

log = logger(__name__)

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    log.info(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        log.info(f'[stdout]\n{stdout.decode()}')
    if stderr:
        log.error(f'[stderr]\n{stderr.decode()}')
    return stdout, stderr
