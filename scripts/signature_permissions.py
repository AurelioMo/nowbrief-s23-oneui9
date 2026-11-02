#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET

from GenUIBridge import certificate
from native import Device, PACKAGE, digest

TARGET = '/system/etc/permissions/signature-permissions-downloadable.xml'
PERMISSION = 'android.permission.SET_BIOMETRIC_DIALOG_ADVANCED'
CERTIFICATE = '34df0e7a9f1cf1892e45c056b4973cd81ccf148a4050d11aea4ac5a65f900a42'
APK_HASH = '9e09fc48d5a85c0f1c98a811e2554255988601c9b6e54865e22b07f12fc1d378'


def patch_allowlist(content):
    root = ET.fromstring(content, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    if root.tag != 'permissions':
        raise ValueError('Unexpected allowlist root')
    matches = root.findall("signature-permissions[@package='" + PACKAGE + "']")
    if len(matches) > 1:
        raise ValueError('Duplicate package allowlist')
    entry = matches[0] if matches else ET.SubElement(root, 'signature-permissions', {'package': PACKAGE})
    if entry.find("permission[@name='" + PERMISSION + "']") is not None:
        raise ValueError('Permission already allowlisted; investigate instead of applying again')
    ET.SubElement(entry, 'permission', {'name': PERMISSION})
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def save_record(state, record):
    temporary = state / 'overlay-state.json.tmp'
    temporary.write_text(json.dumps(record, indent=2) + '\n')
    temporary.replace(state / 'overlay-state.json')


def mountinfo(device):
    return device.text("awk '$5 == \"" + TARGET + "\" {print}' /proc/self/mountinfo")


def check_device(device):
    if device.text('id -u') != '0':
        raise RuntimeError('Root required')
    if device.text('getprop ro.product.model') != 'SM-S911B':
        raise RuntimeError('Only audited SM-S911B supported')
    if device.text('getprop ro.build.version.sdk') != '37':
        raise RuntimeError('Only audited API 37 supported')
    if device.text('readlink /proc/self/ns/mnt') != device.text('readlink /proc/1/ns/mnt'):
        raise RuntimeError('Not in init mount namespace')


def apply(device, state, apksigner):
    state.mkdir(parents=True, exist_ok=False, mode=0o700)
    if mountinfo(device):
        raise RuntimeError('Existing allowlist mount; refusing replacement')
    paths = device.text('pm path ' + PACKAGE).splitlines()
    if len(paths) != 1 or not paths[0].startswith('package:'):
        raise RuntimeError('Unexpected Smart Suggestions APK layout')
    apk = state / 'smartsuggestions.audit.apk'
    apk.write_bytes(device.run('cat ' + shlex.quote(paths[0][8:])))
    if digest(apk.read_bytes()) != APK_HASH:
        raise RuntimeError('Smart Suggestions differs from audited APK')
    platform = state / 'framework-res.audit.apk'
    platform.write_bytes(device.run('cat /system/framework/framework-res.apk'))
    for artifact in (apk, platform):
        signer, report = certificate(apksigner, artifact)
        (state / (artifact.name + '.signing.txt')).write_text(report)
        if signer != CERTIFICATE:
            raise RuntimeError('Platform/app signer mismatch')
    package_dump = device.text('dumpsys package ' + PACKAGE)
    (state / 'package-before.txt').write_text(package_dump)
    active = package_dump.split('Hidden system packages:')[0]
    if PERMISSION not in active or PERMISSION + ': granted=true' in active:
        raise RuntimeError('Permission missing from requests or already granted')
    original = device.run('cat ' + TARGET)
    modified = patch_allowlist(original)
    (state / 'allowlist.original.xml').write_bytes(original)
    (state / 'allowlist.modified.xml').write_bytes(modified)
    record = {
        'target': TARGET, 'package': PACKAGE, 'permission': PERMISSION,
        'boot_id': device.text('cat /proc/sys/kernel/random/boot_id'),
        'fingerprint': device.text('getprop ro.build.fingerprint'),
        'original_sha256': digest(original), 'modified_sha256': digest(modified),
        'source': '/data/local/tmp/sss-signature-' + digest(modified)[:16] + '.xml',
        'mounted': False,
    }
    save_record(state, record)
    source = shlex.quote(record['source'])
    device.run('test ! -e ' + source + ' && cat > ' + source, data=modified)
    device.text('chmod 644 ' + source + ' && chcon u:object_r:system_file:s0 ' + source)
    device.text('mount --bind ' + source + ' ' + TARGET)
    record['mounted'] = True
    record['mount_identity'] = mountinfo(device)
    save_record(state, record)
    if not record['mount_identity'] or digest(device.run('cat /proc/1/root' + TARGET)) != digest(modified):
        raise RuntimeError('Mounted allowlist not visible to init; use rollback')
    print('Targeted signature allowlist mounted. Android restart required to reload SystemConfig.')


def rollback(device, state):
    record = json.loads((state / 'overlay-state.json').read_text())
    if record['target'] != TARGET or device.text('getprop ro.build.fingerprint') != record['fingerprint']:
        raise RuntimeError('Target or ROM identity changed')
    current = digest(device.run('cat ' + TARGET))
    if current != record['original_sha256']:
        if current != record['modified_sha256'] or mountinfo(device) != record.get('mount_identity'):
            raise RuntimeError('Cannot establish mount ownership')
        device.text('umount ' + TARGET)
    if digest(device.run('cat ' + TARGET)) != record['original_sha256']:
        raise RuntimeError('Original allowlist hash not restored')
    record['mounted'] = False
    save_record(state, record)
    print('Original allowlist restored. Android restart required to reevaluate permissions.')


def main():
    parser = argparse.ArgumentParser(description='Audited, reversible biometric signature allowlist overlay')
    parser.add_argument('action', choices=['apply', 'rollback'])
    parser.add_argument('--state', required=True)
    parser.add_argument('--serial')
    parser.add_argument('--termux', action='store_true')
    parser.add_argument('--apksigner', default='apksigner')
    args = parser.parse_args()
    os.umask(0o077)
    device = Device(args.termux, args.serial)
    check_device(device)
    state = Path(args.state)
    if args.action == 'apply':
        apply(device, state, args.apksigner)
    else:
        rollback(device, state)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
