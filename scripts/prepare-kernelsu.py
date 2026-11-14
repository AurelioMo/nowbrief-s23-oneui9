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
from GenUIBridge import certificate
from signature_permissions import patch_allowlist, CERTIFICATE, TARGET as BIOMETRIC_TARGET
from memory_gesture import patch_preferences, PREFS, HOMEUP, HELPER

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'profiles/s23-oneui9-tested.json'


def validate_xml(original, profile):
    if digest(original) != profile['floating_sha256']:
        raise ValueError('Original XML differs from the audited profile')
    return edit_xml(original, profile['features'])


def build_zip(original, profile, output, activation=None, apk_paths=None, biometric=None, gesture=None):
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
    if 'com.samsung.android.app.memory' in packages:
        config['APK_MEMORY'] = packages['com.samsung.android.app.memory']
    if apk_paths is not None:
        config['SOFT_REBOOT_MODE'] = '1'
        for key, package in {
            'PATH_SMART': 'com.samsung.android.smartsuggestions',
            'PATH_AOD': 'com.samsung.android.app.aodservice',
            'PATH_SYSTEMUI': 'com.android.systemui',
            'PATH_SETTINGS': 'com.android.settings',
            'PATH_MEMORY': 'com.samsung.android.app.memory',
        }.items():
            config[key] = apk_paths[package]
    if activation is not None:
        entries['payload/activate.sh'] = activation[0].encode()
        entries['payload/restore.sh'] = activation[1].encode()
    if biometric is not None:
        entries['payload/biometric.original.xml'] = biometric['original']
        entries['payload/biometric.xml'] = patch_allowlist(biometric['original'])
        config['BIO_ORIGINAL_SHA'] = digest(biometric['original'])
        config['BIO_MODIFIED_SHA'] = digest(entries['payload/biometric.xml'])
        config['APK_PLATFORM'] = biometric['platform_sha256']
    if gesture is not None:
        entries.update(gesture)
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


def prepare(device, profile, bootstrap=False):
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
        paths = device.text('pm path --user 0 ' + shlex.quote(package)).splitlines()
        if len(paths) != 1 or not paths[0].startswith('package:'):
            raise ValueError('Unexpected APK layout: ' + package)
        if digest(device.run('cat ' + shlex.quote(paths[0][8:]))) != expected:
            raise ValueError('APK differs from profile: ' + package)
    for entry, expected in profile['settings'].items():
        namespace, key = entry.split('/')
        if not bootstrap and device.text('settings --user 0 get ' + namespace + ' ' + key) != expected:
            raise ValueError('Complete the audited activation first: ' + key)
    dump = device.text('dumpsys package com.samsung.android.smartsuggestions')
    for component in profile['components']:
        if not bootstrap and component_override(dump, component) != 'enabled':
            raise ValueError('Component not explicitly enabled: ' + component)
    return original


def activation_scripts(device, profile):
    """Capture exact pre-install overrides; never fake onboarding or consent."""
    apply, restore = ['#!/system/bin/sh', 'set -eu'], ['#!/system/bin/sh', 'set -eu']
    for entry, desired in profile['settings'].items():
        namespace, key = entry.split('/')
        prefix = f'settings --user 0 '
        old = device.text(f'{prefix}get {namespace} {key}')
        apply.append(f'{prefix}put {namespace} {key} {shlex.quote(desired)}')
        undo = (f'{prefix}delete {namespace} {key}' if old == 'null' else
                f'{prefix}put {namespace} {key} {shlex.quote(old)}')
        restore.append(f'[ "$({prefix}get {namespace} {key})" != {shlex.quote(desired)} ] || {undo}')
    dump = device.text('dumpsys package com.samsung.android.smartsuggestions')
    for component in profile['components']:
        old = component_override(dump, component)
        apply.append('pm enable --user 0 ' + shlex.quote(component))
        command = {'enabled': 'enable', 'disabled': 'disable', 'default': 'default-state'}[old]
        restore.append('pm ' + command + ' --user 0 ' + shlex.quote(component))
    permission = 'android.permission.WRITE_SECURE_SETTINGS'
    package = 'com.samsung.android.app.memory'
    dump = device.text('dumpsys package ' + package)
    # Development permission is grantable without replacing or re-signing the APK.
    if permission not in dump:
        raise ValueError('Memory does not request the expected development permission')
    apply.append(f'pm grant --user 0 {package} {permission}')
    if permission + ': granted=true' not in dump:
        restore.append(f'pm revoke --user 0 {package} {permission}')
    return '\n'.join(apply) + '\n', '\n'.join(restore) + '\n'


def audit_biometric(device, profile, apksigner):
    """Verify both real APK signatures before adding one signature permission."""
    with tempfile.TemporaryDirectory(prefix='nowbrief-signatures-') as directory:
        paths = device.text('pm path --user 0 com.samsung.android.smartsuggestions').splitlines()
        if len(paths) != 1 or not paths[0].startswith('package:'):
            raise ValueError('Unexpected Smart Suggestions APK layout')
        for name, remote in (
            ('smart', paths[0][8:]),
            ('platform', '/system/framework/framework-res.apk'),
        ):
            artifact = Path(directory) / (name + '.apk')
            data = device.run('cat ' + shlex.quote(remote))
            artifact.write_bytes(data)
            if name == 'smart' and digest(data) != profile['apks']['com.samsung.android.smartsuggestions']:
                raise ValueError('Smart Suggestions changed during signature audit')
            signer, _ = certificate(apksigner, artifact)
            if signer != CERTIFICATE:
                raise ValueError('Platform/app signer differs from audited Samsung signer')
            if name == 'platform':
                platform_sha = digest(data)
    original = device.run('cat ' + BIOMETRIC_TARGET)
    patch_allowlist(original)
    return {'original': original, 'platform_sha256': platform_sha}


def prepare_gesture(device):
    config = {}
    for package, key in ((HOMEUP, 'GESTURE_HOMEUP_SHA'), (HELPER, 'GESTURE_HELPER_SHA')):
        paths = device.text('pm path --user 0 ' + package).splitlines()
        if len(paths) != 1 or not paths[0].startswith('package:'):
            raise ValueError('Install Home Up and Save Memory first: ' + package)
        config[key] = digest(device.run('cat ' + shlex.quote(paths[0][8:])))
    original = device.run('cat ' + shlex.quote(PREFS))
    modified = patch_preferences(original)
    config['GESTURE_ORIGINAL_SHA'] = digest(original)
    config['GESTURE_MODIFIED_SHA'] = digest(modified)
    for name, key in (('MEMORY', 'memory_three_finger_gesture'),
                      ('HOMEUP', 'home_up_multi_finger_gesture_enabled')):
        value = device.text('settings --user 0 get secure ' + key)
        if value not in ('null', '0', '1'):
            raise ValueError('Unexpected gesture setting: ' + key)
        config['GESTURE_OLD_' + name] = value
    return {
        'payload/gesture.original.xml': original,
        'payload/gesture.xml': modified,
        'payload/gesture.sh': ''.join(
            f'{key}={shlex.quote(value)}\n' for key, value in config.items()).encode(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New private ZIP outside this repository')
    parser.add_argument('--termux', action='store_true')
    parser.add_argument('--serial', default=os.environ.get('ANDROID_SERIAL'))
    parser.add_argument('--with-memory', action='store_true',
                        help='Pin installed Memory APK and package reversible activation commands')
    parser.add_argument('--soft-reboot', action='store_true',
                        help='Authorize early XML mount for ksud soft-reboot; requires --with-memory')
    parser.add_argument('--with-biometric', action='store_true',
                        help='Add audited same-signer biometric signature allowlist')
    parser.add_argument('--apksigner', default='apksigner')
    parser.add_argument('--with-homeup-gesture', action='store_true',
                        help='Map three-finger swipe down through installed Home Up; restarts launcher')
    args = parser.parse_args()
    if args.soft_reboot and not args.with_memory:
        parser.error('--soft-reboot requires --with-memory')
    if args.with_homeup_gesture and not args.with_memory:
        parser.error('--with-homeup-gesture requires --with-memory')
    output = args.output.expanduser().resolve()
    if output == ROOT or ROOT in output.parents or output.exists():
        parser.error('Choose a new ZIP outside the repository')
    os.umask(0o077)
    profile = json.loads(PROFILE.read_text())
    device = Device(args.termux, args.serial)
    if args.with_memory:
        paths = device.text('pm path --user 0 com.samsung.android.app.memory').splitlines()
        if len(paths) != 1 or not paths[0].startswith('package:'):
            raise ValueError('Expected one installed Memory APK')
        profile['apks']['com.samsung.android.app.memory'] = digest(
            device.run('cat ' + shlex.quote(paths[0][8:])))
        conflict = device.text('settings --user 0 get secure home_up_multi_finger_gesture_enabled')
        if conflict not in ('null', '0') and not args.with_homeup_gesture:
            raise ValueError('Home Up owns multi-finger gestures; disable that gesture in its UI first')
        if not args.with_homeup_gesture:
            profile['settings']['secure/memory_three_finger_gesture'] = '1'
    original = prepare(device, profile, bootstrap=args.with_memory)
    activation = activation_scripts(device, profile) if args.with_memory else None
    apk_paths = None
    if args.soft_reboot:
        apk_paths = {}
        for package in profile['apks']:
            paths = device.text('pm path --user 0 ' + shlex.quote(package)).splitlines()
            if len(paths) != 1 or not paths[0].startswith('package:'):
                raise ValueError('Unexpected APK layout: ' + package)
            apk_paths[package] = paths[0][8:]
            if digest(device.run('cat ' + shlex.quote(apk_paths[package]))) != profile['apks'][package]:
                raise ValueError('APK changed during preparation: ' + package)
    biometric = audit_biometric(device, profile, args.apksigner) if args.with_biometric else None
    gesture = prepare_gesture(device) if args.with_homeup_gesture else None
    build_zip(original, profile, output, activation, apk_paths, biometric, gesture)
    print('Private ZIP:', output)
    print('SHA256:', hashlib.sha256(output.read_bytes()).hexdigest())
    print('Early activation on ksud soft-reboot is authorized.' if args.soft_reboot else
          'Automatic activation is OFF.')
    print('Installation and device validation are still required. No reboot performed.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
