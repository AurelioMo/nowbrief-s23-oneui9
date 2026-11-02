#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import shlex

from GenUIBridge import certificate, run
from native import Device, digest, guard, save, shared_uid_grant
from audit_installed import elements


def main():
    parser = argparse.ArgumentParser(description='Install permission-only bridge and verify actual UID/grant')
    parser.add_argument('--state', required=True)
    parser.add_argument('--apk', required=True)
    parser.add_argument('--apksigner', default='apksigner')
    parser.add_argument('--aapt2', default='aapt2')
    parser.add_argument('--termux', action='store_true')
    parser.add_argument('--serial')
    args = parser.parse_args()
    state = Path(args.state)
    record = json.loads((state / 'state.json').read_text())
    device = Device(args.termux, args.serial)
    guard(device, state, record)
    if not record.get('snapshot_complete'):
        parser.error('Incomplete snapshot')
    permission = 'com.samsung.android.smartsuggestions.permission.BIND_GENUI_SERVICE'
    sss_paths = device.text('pm path com.samsung.android.smartsuggestions').splitlines()
    if len(sss_paths) != 1 or not sss_paths[0].startswith('package:'):
        parser.error('Unexpected Smart Suggestions layout')
    installed_sss = state / 'sss.bridge-check.apk'
    installed_sss.write_bytes(device.run('cat ' + shlex.quote(sss_paths[0][8:])))
    manifest = elements(run([args.aapt2, 'dump', 'xmltree', '--file', 'AndroidManifest.xml', str(installed_sss)]))
    if not any(entry['type'] == 'permission' and entry['attributes'].get('name') == permission for entry in manifest):
        parser.error('Permission is undefined in installed SSS. A bridge cannot supply the missing Samsung service.')
    if not any(entry['type'] == 'service' and entry['attributes'].get('name', '').endswith('.GenUIService') for entry in manifest):
        parser.error('Installed SSS has no GenUIService. Do not install a bridge.')
    before_dump = device.text('dumpsys package com.android.systemui')
    if shared_uid_grant(before_dump, permission) is True:
        print('Shared SystemUI UID already has GenUI permission. Bridge not installed.')
        return
    denial_logs = device.text('logcat -d -t 4000 -v threadtime')
    if not any('Permission Denial' in line and 'GenUIService' in line and permission in line
               and re.search(r'uid[= ]10048\b', line) for line in denial_logs.splitlines()):
        parser.error('No specific UID 10048 GenUI permission denial observed; bridge not justified')
    (state / 'bridge-denial-before.txt').write_text(denial_logs)
    package = 'com.samsung.android.systemui.genuibridge'
    if device.text('pm path ' + package):
        parser.error('Bridge already exists; will not replace it')
    content = Path(args.apk).read_bytes()
    cert_bridge, audit = certificate(args.apksigner, args.apk)
    for peer in ('com.android.systemui', 'com.samsung.android.app.aodservice'):
        paths = device.text('pm path ' + peer).splitlines()
        if len(paths) != 1 or not paths[0].startswith('package:'):
            parser.error('Unexpected package layout: ' + peer)
        peer_apk = state / (peer + '.bridge-check.apk')
        peer_apk.write_bytes(device.run('cat ' + shlex.quote(paths[0][8:])))
        cert_peer, _ = certificate(args.apksigner, peer_apk)
        if cert_peer != cert_bridge:
            parser.error('Bridge signer does not match installed ' + peer)
    tree = run([args.aapt2, 'dump', 'xmltree', '--file', 'AndroidManifest.xml', args.apk])
    badging = run([args.aapt2, 'dump', 'badging', args.apk])
    if "package: name='" + package + "'" not in badging or 'android.uid.systemui' not in tree:
        parser.error('Wrong bridge package or sharedUserId')
    remote = '/data/local/tmp/genuibridge_' + digest(content) + '.apk'
    device.run('cat > ' + remote + ' && chmod 644 ' + remote, data=content)
    record['bridge'] = {'sha256': digest(content), 'previously_absent': True}
    save(state, record)
    result = device.text('cat ' + remote + ' | pm install -i com.sec.android.app.samsungapps -S ' + str(len(content)), check=False)
    (state / 'bridge-install.txt').write_text(result + '\n' + audit)
    if result != 'Success':
        raise RuntimeError('Package Manager rejected bridge: ' + result)
    paths = device.text('pm path ' + package).splitlines()
    if len(paths) != 1 or digest(device.run('cat ' + shlex.quote(paths[0][8:]))) != digest(content):
        raise RuntimeError('Installed bridge hash not confirmed')
    uids = []
    for peer in (package, 'com.android.systemui', 'com.samsung.android.app.aodservice'):
        listing = device.text('pm list packages -U ' + peer)
        match = re.search(r'^package:' + re.escape(peer) + r' uid:(\d+)$', listing, re.M)
        if not match:
            raise RuntimeError('UID not established: ' + peer)
        uids.append(match[1])
    after_dump = device.text('dumpsys package com.android.systemui')
    (state / 'bridge-shared-uid-after.txt').write_text(after_dump)
    grant = shared_uid_grant(after_dump, permission)
    (state / 'bridge-uid-grant.json').write_text(json.dumps({'uids': uids, 'permission': grant}, indent=2))
    if len(set(uids)) != 1 or grant is not True:
        raise RuntimeError('Shared UID or permission not confirmed; inspect evidence and roll back')
    device.text('for pid in $(pidof com.samsung.android.app.aodservice); do kill "$pid" || exit 1; done')
    print('UID and permission verified. GenUI binding and lock-screen card still require real UI/log tests.')


if __name__ == '__main__':
    main()
