#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import tarfile
import uuid

from native import Device, PACKAGE, digest, guard


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', required=True)
    parser.add_argument('--serial')
    parser.add_argument('--termux', action='store_true')
    args = parser.parse_args()
    state = Path(args.state)
    record = json.loads((state / 'state.json').read_text())
    device = Device(args.termux, args.serial)
    guard(device, state, record)
    remote = '/data/local/tmp/nowbrief-backup-' + uuid.uuid4().hex
    command = '''set -eu
umask 077
mkdir {remote}
pids="$(ps -A -o UID,PID | awk '$1 == 10132 {{print $2}}')"
trap 'for pid in $pids; do kill -CONT "$pid" 2>/dev/null || true; done' EXIT
for pid in $pids; do kill -STOP "$pid"; done
find /data/user/0/{package}/databases -type f -exec sha256sum {{}} \\; | sort > {remote}/before.txt
tar --selinux -cpf {remote}/private-data.tar -C /data user/0/{package} user_de/0/{package}
find /data/user/0/{package}/databases -type f -exec sha256sum {{}} \\; | sort > {remote}/after.txt
cmp {remote}/before.txt {remote}/after.txt
'''.format(remote=remote, package=PACKAGE)
    app_id = device.text('dumpsys package ' + PACKAGE)
    if 'appId=10132' not in app_id:
        raise RuntimeError('Backup UID must match audited Smart Suggestions UID')
    device.text(command)
    content = device.run('cat ' + remote + '/private-data.tar')
    target = state / 'sss-private-data-consistent.tar'
    target.write_bytes(content)
    with tarfile.open(target) as archive:
        members = archive.getmembers()
        if not members or not all(member.name.startswith(('user/0/' + PACKAGE, 'user_de/0/' + PACKAGE)) for member in members):
            raise RuntimeError('Unexpected archive contents')
        labels = any('SCHILY.xattr.security.selinux' in member.pax_headers or
                     'RHT.security.selinux' in member.pax_headers for member in members)
    if not labels:
        raise RuntimeError('SELinux metadata missing from private-data backup')
    (state / 'private-data-backup.json').write_text(json.dumps({
        'file': target.name, 'sha256': digest(content), 'members': len(members),
        'consistent': True, 'database_hashes_stable': True, 'uid_frozen_during_archive': 10132,
        'selinux_metadata': labels, 'device_archive': remote + '/private-data.tar'}, indent=2) + '\n')
    (state / 'database-hashes-before-backup.txt').write_bytes(device.run('cat ' + remote + '/before.txt'))
    (state / 'database-hashes-after-backup.txt').write_bytes(device.run('cat ' + remote + '/after.txt'))
    print('Consistent private-data backup verified:', target)


if __name__ == '__main__':
    main()
