#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

from native import Device, PACKAGE, digest, guard, save
from GenUIBridge import certificate, run


def main():
    parser = argparse.ArgumentParser(description='Verified same-signer update or snapshot APK restore')
    parser.add_argument('--state', required=True)
    parser.add_argument('--apk')
    parser.add_argument('--sha256')
    parser.add_argument('--source', help='Record source URL; download provenance must be checked separately')
    parser.add_argument('--review', help='Compatibility review JSON for the exact snapshot/candidate hashes')
    parser.add_argument('--reversible-trial', action='store_true', help='Trial with verified private-data backup; not a claim of full migration verification')
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--termux', action='store_true')
    parser.add_argument('--serial')
    parser.add_argument('--apksigner', default='apksigner')
    parser.add_argument('--aapt2', default='aapt2')
    args = parser.parse_args()
    state = Path(args.state)
    record = json.loads((state / 'state.json').read_text())
    device = Device(args.termux, args.serial)
    guard(device, state, record)
    originals = record['apks'][PACKAGE]
    if len(originals) != 1:
        parser.error('Split APK restore needs an audited install-session procedure; not supported here')
    original = state / originals[0]['file']
    if digest(original.read_bytes()) != originals[0]['sha256']:
        parser.error('Snapshot APK hash mismatch')
    if args.restore:
        if not record.get('install_attempted'):
            parser.error('No installation recorded by this tool')
        apk = original
    else:
        if not args.apk or not args.sha256 or not args.source:
            parser.error('--apk, --sha256 and --source required')
        if record.get('install_attempted') or record['mounted']:
            parser.error('Use a fresh snapshot; do not mix APK update with active feature transaction')
        apk = Path(args.apk)
        if digest(apk.read_bytes()) != args.sha256.lower():
            parser.error('APK SHA-256 mismatch')
        if not args.review:
            parser.error('Compatibility/data migration review required before an APK update')
        review = json.loads(Path(args.review).read_text())
        migration_safe = review.get('data_compatibility_verified') is True
        if args.reversible_trial:
            backup = json.loads((state / 'private-data-backup.json').read_text())
            migration_safe = (review.get('room_identities_preserved') is True and
                              backup.get('consistent') is True and
                              digest((state / backup['file']).read_bytes()) == backup['sha256'])
        if (review.get('installed_sha256') != originals[0]['sha256'] or
                review.get('candidate_sha256') != args.sha256.lower() or
                review.get('dependencies_verified') is not True or
                not migration_safe or
                review.get('consistent_data_backup_verified') is not True):
            parser.error('Compatibility review incomplete or hashes do not match')
    candidate_cert, audit = certificate(args.apksigner, apk)
    original_cert, _ = certificate(args.apksigner, original)
    if candidate_cert != original_cert:
        parser.error('Different signer: CorePatch runtime/UID compatibility must be proven first. No bypass assumed.')
    badging = run([args.aapt2, 'dump', 'badging', str(apk)])
    if "package: name='" + PACKAGE + "'" not in badging:
        parser.error('Wrong package')
    minimum = re.search(r"(?:minSdkVersion|sdkVersion):'(\d+)'", badging)
    if not minimum:
        parser.error('Cannot establish minSdk from aapt2 output')
    if minimum and int(minimum[1]) > int(record['identity']['ro.build.version.sdk']):
        parser.error('minSdk exceeds device API')
    abi = re.search(r'native-code: (.+)', badging)
    if abi and not set(re.findall(r"'([^']+)'", abi[1])).intersection(
            record['identity']['ro.product.cpu.abilist'].split(',')):
        parser.error('Incompatible ABI')
    (state / 'install-apk-audit.txt').write_text(audit + '\n' + badging + '\nSource: ' + str(args.source))
    content = apk.read_bytes()
    remote = '/data/local/tmp/sss_' + digest(content) + '.apk'
    device.run('cat > ' + remote + ' && chmod 644 ' + remote, data=content)
    if device.text('sha256sum ' + remote).split()[0] != digest(content):
        parser.error('Transferred APK hash mismatch')
    old_property = device.text('getprop ro.build.official.release')
    if not old_property:
        parser.error('Missing/empty build property; no property change attempted')
    resetprop = device.text('command -v resetprop', check=False)
    if not resetprop and device.text('test -x /data/local/tmp/resetprop && echo yes', check=False) == 'yes':
        resetprop = '/data/local/tmp/resetprop'
    if not resetprop:
        if device.text('test -x /data/adb/ksu/bin/resetprop && echo yes', check=False) == 'yes':
            resetprop = '/data/adb/ksu/bin/resetprop'
        else:
            parser.error('resetprop unavailable')
    record['install_attempted'] = True
    record['install_property_before'] = old_property
    save(state, record)
    command = ('cat ' + remote + ' | pm install -r -d -i com.sec.android.app.samsungapps -S ' + str(len(content)))
    try:
        device.text(shlex.quote(resetprop) + ' ro.build.official.release false')
        result = device.text(command, check=False)
        (state / ('restore-pm.txt' if args.restore else 'install-pm.txt')).write_text(result + '\n')
        if result.strip() != 'Success':
            raise RuntimeError('Package Manager rejected install; inspect journal before continuing: ' + result)
        paths = device.text('pm path ' + PACKAGE).splitlines()
        if len(paths) != 1 or digest(device.run('cat ' + shlex.quote(paths[0][8:]))) != digest(content):
            raise RuntimeError('Installed APK hash not confirmed')
        if args.restore:
            record['install_attempted'] = False
        record['installed_sha256'] = digest(content)
        save(state, record)
    finally:
        device.text(shlex.quote(resetprop) + ' ro.build.official.release ' + shlex.quote(old_property))
        if device.text('getprop ro.build.official.release') != old_property:
            raise RuntimeError('Build property restoration failed')
    print('APK installed and hash verified; feature behavior NOT validated.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
