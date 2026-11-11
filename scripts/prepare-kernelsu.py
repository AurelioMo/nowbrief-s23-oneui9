#!/usr/bin/env python3
"""Read-only device validation and private, reproducible KernelSU ZIP preparation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import tempfile
import subprocess
import zipfile

from native import Device, TARGET, component_override, digest, edit_xml

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'profiles/s23-oneui9-tested.json'


def validate_xml(original, profile):
    if digest(original) != profile['floating_sha256']:
        raise ValueError('Original XML differs from the audited profile')
    return edit_xml(original, profile['features'])


def build_zip(original, profile, output):
    modified = validate_xml(original, profile)
    entries = {p.name: p.read_bytes() for p in (ROOT / 'kernelsu-module').iterdir() if p.is_file()}
    packages = profile['apks']
    config = {
        'EXPECTED_FINGERPRINT': profile['identity']['ro.build.fingerprint'],
        'ORIGINAL_SHA': digest(original), 'MODIFIED_SHA': digest(modified),
        'APK_SMART': packages['com.samsung.android.smartsuggestions'],
        'APK_AOD': packages['com.samsung.android.app.aodservice'],
        'APK_SYSTEMUI': packages['com.android.systemui'],
        'APK_SETTINGS': packages['com.android.settings'],
    }
    entries['payload/profile.sh'] = ''.join(
        f'{key}={shlex.quote(value)}\n' for key, value in config.items()).encode()
    entries['payload/original.xml'] = original
    entries['payload/floating_feature.xml'] = modified
    # Publish only a complete archive, preserving an existing destination.
    with tempfile.TemporaryDirectory(prefix='.nowbrief-', dir=output.parent) as temporary:
        prepared = Path(temporary) / 'prepared.zip'
        with zipfile.ZipFile(prepared, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(entries.items()):
                info = zipfile.ZipInfo(name, (2026, 11, 11, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
        prepared.chmod(0o600)
        os.link(prepared, output)


def prepare(device, profile):
    if profile.get('activation_allowed') is not True:
        raise ValueError('Profile is not approved')
    if device.text('id -u') != '0':
        raise ValueError('Existing root access required; this tool does not obtain root')
    for key, value in profile['identity'].items():
        if device.text('getprop ' + shlex.quote(key)) != value:
            raise ValueError('Unsupported identity: ' + key)
    if device.text('readlink /proc/1/ns/mnt') != device.text('readlink /proc/self/ns/mnt'):
        raise ValueError('Not in init mount namespace')
    if device.text("awk '$5 == \"" + TARGET + "\" {print}' /proc/self/mountinfo"):
        raise ValueError('An existing XML mount must be rolled back first')
    original = device.run('cat ' + TARGET)
    validate_xml(original, profile)
    for package, expected in profile['apks'].items():
        paths = device.text('pm path ' + shlex.quote(package)).splitlines()
        if len(paths) != 1 or not paths[0].startswith('package:'):
            raise ValueError('Unexpected APK layout: ' + package)
        if digest(device.run('cat ' + shlex.quote(paths[0][8:]))) != expected:
            raise ValueError('APK differs from profile: ' + package)
    for entry, expected in profile['settings'].items():
        namespace, key = entry.split('/')
        if device.text('settings --user 0 get ' + namespace + ' ' + key) != expected:
            raise ValueError('Complete the audited activation first: ' + key)
    dump = device.text('dumpsys package com.samsung.android.smartsuggestions')
    for component in profile['components']:
        if component_override(dump, component) != 'enabled':
            raise ValueError('Component not explicitly enabled: ' + component)
    return original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New private ZIP outside this repository')
    parser.add_argument('--termux', action='store_true')
    parser.add_argument('--serial', default=os.environ.get('ANDROID_SERIAL'))
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output == ROOT or ROOT in output.parents or output.exists():
        parser.error('Choose a new ZIP outside the repository')
    os.umask(0o077)
    profile = json.loads(PROFILE.read_text())
    original = prepare(Device(args.termux, args.serial), profile)
    build_zip(original, profile, output)
    print('Private ZIP:', output)
    print('SHA256:', hashlib.sha256(output.read_bytes()).hexdigest())
    print('Automatic activation is OFF. Installation and device validation are still required.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
