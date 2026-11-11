#!/bin/sh
set -eu
# Installation is staged by KernelSU Manager, never copied into an active module.
echo 'Prepare a private ZIP with: python3 scripts/prepare-kernelsu.py --output /path/outside/repo/nowbrief-private.zip' >&2
echo 'Then install that ZIP from KernelSU Manager. Automatic activation starts OFF.' >&2
exit 2
