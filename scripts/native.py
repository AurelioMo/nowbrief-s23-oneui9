#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET

PACKAGE = 'com.samsung.android.smartsuggestions'
TARGET = '/system/etc/floating_feature.xml'
PDE = 'SEC_FLOATING_FEATURE_FRAMEWORK_SUPPORT_PERSONALIZED_DATA_CORE'
WIDGET = PACKAGE + '/.feature.aisuggestion.ui.appwidget.AiSuggestionAppWidgetReceiver'
IMMUTABLE_SNAPSHOT = Path(__file__).resolve().parents[1] / 'snapshots' / 'before'
PACKAGES = [PACKAGE, 'com.samsung.android.app.aodservice', 'com.android.systemui',
            'com.android.settings', 'com.samsung.android.offline.languagemodel']
KEYS = [('global', key) for key in ('sss_enabled', 'nowbrief_enabled',
        'smart_suggestions_enabled', 'now_nudge_enabled', 'now_nudge_setting')]
HIGHLIGHTS = [('secure', 'noti_intelligence_first_time'), ('system', 'ai_info_confirmed'),
              ('secure', 'noti_intelligence_priority_content'),
              ('system', 'noti_intelligence_priority_conversation'),
              ('secure', 'noti_intelligence_summarize_content')]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def edit_xml(data, changes=None):
    root = ET.fromstring(data, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    if root.tag != 'SecFloatingFeatureSet':
        raise ValueError('Unexpected XML root')
    for name, value in (changes if changes is not None else {PDE: 'TRUE'}).items():
        if not name.startswith('SEC_FLOATING_FEATURE_') or not name.replace('_', '').isalnum():
            raise ValueError('Invalid Floating Feature name')
        entries = root.findall(name)
        if len(entries) > 1:
            raise ValueError('Duplicate feature: ' + name)
        if not entries:
            entries = [ET.SubElement(root, name)]
        entries[0].text = str(value)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


class Device:
    def __init__(self, termux, serial):
        self.prefix = [] if termux else ['adb'] + (['-s', serial] if serial else []) + ['exec-out']

    def run(self, command, check=True, data=None):
        arguments = ['su', '-mm', '-c', command]
        if self.prefix:
            transport = self.prefix[:-1] + ['shell', '-T'] if data is not None else self.prefix
            arguments = transport + [shlex.join(arguments)]
        result = subprocess.run(arguments,
                                input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=120)
        if check and result.returncode:
            raise RuntimeError(command + '\n' + result.stderr.decode(errors='replace') +
                               result.stdout.decode(errors='replace'))
        return result.stdout if check else result.stdout + result.stderr

    def text(self, command, check=True):
        return self.run(command, check).decode(errors='replace').strip()


def save(state, content):
    writable_state(state)
    temporary = state / 'state.json.tmp'
    temporary.write_text(json.dumps(content, indent=2) + '\n')
    temporary.replace(state / 'state.json')


def writable_state(state):
    if state.resolve() == IMMUTABLE_SNAPSHOT or IMMUTABLE_SNAPSHOT in state.resolve().parents:
        raise RuntimeError('snapshots/before is immutable; collect a new transaction snapshot')


def component_override(dump, component):
    package, name = component.split('/')
    name = package + name if name.startswith('.') else name
    lines = dump.splitlines()
    if 'Packages:' in lines:
        start = lines.index('Packages:') + 1
        end = next((index for index in range(start, len(lines))
                    if lines[index] and not lines[index].startswith(' ')), len(lines))
        lines = lines[start:end]
        headers = [index for index, line in enumerate(lines) if line.startswith('  Package [')]
        selected = [index for index in headers if lines[index].startswith('  Package [' + package + ']')]
        if len(selected) != 1:
            raise RuntimeError('Cannot identify active package section')
        start = selected[0]
        end = next((index for index in headers if index > start), len(lines))
        lines = lines[start:end]
    users = [index for index, line in enumerate(lines) if line.strip().startswith('User 0:')]
    if len(users) != 1:
        raise RuntimeError('Cannot uniquely identify user 0 component state')
    start = users[0]
    user_indent = len(lines[start]) - len(lines[start].lstrip())
    section = None
    found = []
    for line in lines[start + 1:]:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= user_indent:
            break
        if indent == user_indent + 2:
            section = line.strip()
        elif indent > user_indent + 2 and line.strip() == name:
            if section == 'enabledComponents:':
                found.append('enabled')
            elif section == 'disabledComponents:':
                found.append('disabled')
    if len(found) > 1:
        raise RuntimeError('Conflicting component overrides')
    return found[0] if found else 'default'


def shared_uid_grant(dump, permission):
    header = '  SharedUser [android.uid.systemui]'
    lines = dump.splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith(header)]
    if len(starts) != 1:
        return None
    for line in lines[starts[0] + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= 2:
            break
        if line.strip().startswith(permission + ': granted='):
            return line.strip().split('granted=')[1].split(',')[0] == 'true'
    return None


def collect(device, state):
    writable_state(state)
    state.mkdir(mode=0o700, parents=True, exist_ok=False)
    if 'uid=0' not in device.text('id'):
        raise RuntimeError('su -mm did not return root')
    identity = {key: device.text('getprop ' + key) for key in (
        'ro.product.model', 'ro.product.device', 'ro.build.version.oneui',
        'ro.build.version.release', 'ro.build.version.sdk', 'ro.build.fingerprint',
        'ro.build.version.security_patch', 'ro.product.cpu.abilist', 'ro.build.official.release')}
    boot = device.text('cat /proc/sys/kernel/random/boot_id')
    original = device.run('cat ' + TARGET)
    ET.fromstring(original)
    (state / 'floating_feature.original.xml').write_bytes(original)
    record = dict(identity=identity, boot=boot, original_sha256=digest(original),
                  settings={}, applied_settings=[], components={}, applied_components=[],
                  apks={}, mounted=False, install_attempted=False, snapshot_complete=False, bridge=None)
    save(state, record)
    for namespace, key in KEYS + HIGHLIGHTS:
        record['settings'][namespace + '/' + key] = device.text(
            'settings --user 0 get ' + namespace + ' ' + key)
    for package in PACKAGES:
        dump = device.run('dumpsys package ' + package)
        (state / (package + '.txt')).write_bytes(dump)
        paths = device.text('pm path ' + package).splitlines()
        record['apks'][package] = []
        for index, line in enumerate(paths):
            if not line.startswith('package:'):
                continue
            remote = line[len('package:'):]
            data = device.run('cat ' + shlex.quote(remote))
            filename = package + '.' + str(index) + '.apk'
            (state / filename).write_bytes(data)
            record['apks'][package].append(dict(path=remote, file=filename, sha256=digest(data)))
    for name, command in {
        'getprop': 'getprop', 'packages': 'pm list packages -f -U',
        'root-modules': 'ls -la /data/adb/modules; for f in /data/adb/modules/*/module.prop; do cat "$f"; done',
        'root-tools': 'command -v resetprop; ls -l /data/adb/ksu/bin/resetprop /data/local/tmp/resetprop; su --help',
        'namespaces': 'readlink /proc/1/ns/mnt; readlink /proc/self/ns/mnt; cat /proc/1/mountinfo',
        'root-processes': 'ps -A -o USER,PID,NAME,ARGS',
        'mountinfo': 'cat /proc/self/mountinfo',
        'corepatch-preferences': 'find /data/user_de/0 /data/user/0 -path "*corepatch*/shared_prefs/*.xml" -type f -exec cat {} \\;',
        'logcat-before': 'logcat -d -t 1500 -v threadtime',
    }.items():
        (state / (name + '.txt')).write_bytes(device.run(command, check=False))
    record['snapshot_complete'] = True
    save(state, record)
    return record


def guard(device, state, record):
    writable_state(state)
    for key, expected in record['identity'].items():
        if key == 'ro.build.official.release':
            continue
        if device.text('getprop ' + key) != expected:
            raise RuntimeError('Identity changed: ' + key)
    if device.text('id -u') != '0':
        raise RuntimeError('Not root')


def restart(device):
    device.text('am force-stop --user 0 ' + PACKAGE)
    device.text('am force-stop --user 0 com.android.settings')
    device.text('for pkg in com.android.systemui com.samsung.android.app.aodservice; '
                'do for pid in $(pidof "$pkg"); do kill "$pid" || exit 1; done; done')


def enable(device, state, record, profile):
    if not record.get('snapshot_complete'):
        raise RuntimeError('Incomplete snapshot; collect again into a new directory')
    if device.text('cat /proc/sys/kernel/random/boot_id') != record['boot']:
        raise RuntimeError('Device rebooted after snapshot; collect a new baseline')
    expected = json.loads(Path(profile).read_text())
    if expected.get('activation_allowed') is not True:
        raise RuntimeError('Profile not approved for activation: ' +
                           '; '.join(expected.get('blockers', ['missing compatibility approval'])))
    guard(device, state, record)
    for key, value in expected['identity'].items():
        if record['identity'].get(key) != value:
            raise RuntimeError('Unsupported device/build: ' + key)
    if record['original_sha256'] != expected['floating_sha256']:
        raise RuntimeError('Floating Features do not match audited ROM')
    for package, sha in expected['apks'].items():
        current = device.text('pm path ' + package).splitlines()
        if len(current) != 1 or not current[0].startswith('package:'):
            raise RuntimeError('Unexpected APK layout: ' + package)
        if digest(device.run('cat ' + shlex.quote(current[0][8:]))) != sha:
            raise RuntimeError('Installed APK differs from audited profile: ' + package)
    if device.text('readlink /proc/1/ns/mnt') != device.text('readlink /proc/self/ns/mnt'):
        raise RuntimeError('su -mm is not in init mount namespace')
    if device.text("awk '$5 == \"" + TARGET + "\" {print}' /proc/self/mountinfo"):
        raise RuntimeError('Pre-existing Floating Features mount; not replacing it')
    if digest(device.run('cat ' + TARGET)) != record['original_sha256']:
        raise RuntimeError('Floating Features changed after backup')
    for namespace, key in KEYS + HIGHLIGHTS:
        if device.text('settings --user 0 get ' + namespace + ' ' + key) != record['settings'][namespace + '/' + key]:
            raise RuntimeError('Settings changed after snapshot: ' + namespace + '/' + key)
    components = expected.get('components', [])
    for component in components:
        if not component.startswith(PACKAGE + '/'):
            raise RuntimeError('Unexpected component package')
        record['components'][component] = component_override(
            device.text('dumpsys package ' + PACKAGE), component)
    record['remote_xml'] = '/data/local/tmp/ff_s23_' + record['original_sha256'][:16] + '.xml'
    modified = edit_xml((state / 'floating_feature.original.xml').read_bytes(), expected['features'])
    record['modified_sha256'] = digest(modified)
    (state / 'floating_feature.modified.xml').write_bytes(modified)
    save(state, record)
    remote = shlex.quote(record['remote_xml'])
    device.run('test ! -e ' + remote + ' && cat > ' + remote, data=modified)
    device.text('chmod 644 ' + remote + ' && chcon u:object_r:system_file:s0 ' + remote)
    record['mounted'] = True
    save(state, record)
    device.text('mount --bind ' + remote + ' ' + TARGET)
    record['mount_identity'] = device.text("awk '$5 == \"" + TARGET + "\" {print}' /proc/self/mountinfo")
    if not record['mount_identity']:
        raise RuntimeError('Mount not present in mountinfo; run rollback')
    save(state, record)
    if digest(device.run('cat /proc/1/root' + TARGET)) != record['modified_sha256']:
        raise RuntimeError('Modified file not visible in init namespace; run rollback')
    consumer_views(device, record['modified_sha256'])
    for component in components:
        if record['components'][component] == 'enabled':
            continue
        record['applied_components'].append(component)
        save(state, record)
        device.text('pm enable --user 0 ' + component)
    for key, value in expected.get('settings', {}).items():
        if key not in record['settings']:
            raise RuntimeError('Setting not backed up: ' + key)
        record['applied_settings'].append(key)
        save(state, record)
        namespace, name = key.split('/')
        device.text('settings --user 0 put ' + namespace + ' ' + name + ' ' + shlex.quote(str(value)))
    restart(device)
    print('Applied profile:', expected['goal'], '- functionality NOT yet validated.')


def consumer_views(device, expected_sha):
    for process in ('system_server', 'zygote64', 'zygote', 'com.android.systemui',
                    'com.samsung.android.app.aodservice', PACKAGE, 'com.android.settings'):
        for pid in device.text('pidof ' + process, check=False).split():
            if not pid.isdigit():
                raise RuntimeError('Unexpected pidof output for ' + process)
            if digest(device.run('cat /proc/' + pid + '/root' + TARGET)) != expected_sha:
                raise RuntimeError('Floating Features not visible to ' + process + '; run rollback')


def rollback(device, state, record):
    guard(device, state, record)
    if record.get('install_attempted'):
        raise RuntimeError('APK installation was attempted; restore APK set using installation journal first')
    bridge = record.get('bridge')
    if bridge:
        package = 'com.samsung.android.systemui.genuibridge'
        paths = device.text('pm path ' + package).splitlines()
        if paths:
            if len(paths) != 1 or digest(device.run('cat ' + shlex.quote(paths[0][8:]))) != bridge['sha256']:
                raise RuntimeError('Bridge APK changed; refusing uninstall')
            result = device.text('pm uninstall ' + package)
            if result != 'Success':
                raise RuntimeError('Bridge uninstall failed: ' + result)
        record['bridge'] = None
        save(state, record)
    if record['mounted']:
        same_boot = device.text('cat /proc/sys/kernel/random/boot_id') == record['boot']
        if same_boot:
            if device.text('readlink /proc/1/ns/mnt') != device.text('readlink /proc/self/ns/mnt'):
                raise RuntimeError('Not in init mount namespace')
            current_sha = digest(device.run('cat ' + TARGET))
            if current_sha == record['original_sha256']:
                pass
            elif current_sha != record['modified_sha256']:
                raise RuntimeError('Mount changed; refusing to unmount another modification')
            else:
                mountinfo = device.text("awk '$5 == \"" + TARGET + "\" {print}' /proc/self/mountinfo")
                mount_fields = mountinfo.split()
                owned = (mountinfo == record['mount_identity'] if record.get('mount_identity') else
                         len(mount_fields) > 5 and mount_fields[3].endswith('/' + Path(record['remote_xml']).name))
                if not mountinfo or not owned:
                    raise RuntimeError('Cannot establish ownership of mounted file')
                device.text('umount ' + TARGET)
        if digest(device.run('cat ' + TARGET)) != record['original_sha256']:
            raise RuntimeError('Original Floating Features hash not restored')
        record['mounted'] = False
        save(state, record)
    actions = {'default': 'default-state', 'enabled': 'enable', 'disabled': 'disable',
               'disabled-user': 'disable-user', 'disabled-until-used': 'disable-until-used',
               '0': 'default-state', '1': 'enable', '2': 'disable', '3': 'disable-user',
               '4': 'disable-until-used'}
    for component in record['applied_components']:
        device.text('pm ' + actions[record['components'][component]] + ' --user 0 ' + component)
    for entry in record['applied_settings']:
        namespace, key = entry.split('/')
        old = record['settings'][entry]
        command = ('delete ' + namespace + ' ' + key if old == 'null' else
                   'put ' + namespace + ' ' + key + ' ' + shlex.quote(old))
        device.text('settings --user 0 ' + command)
        if device.text('settings --user 0 get ' + namespace + ' ' + key) != old:
            raise RuntimeError('Settings restore failed: ' + entry)
    restart(device)
    record['applied_settings'] = []
    record['applied_components'] = []
    save(state, record)
    print('Recorded feature changes restored. No packages uninstalled.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['collect', 'enable', 'rollback', 'logs', 'plan'])
    parser.add_argument('--state', required=True)
    parser.add_argument('--termux', action='store_true')
    parser.add_argument('--serial')
    parser.add_argument('--profile')
    args = parser.parse_args()
    os.umask(0o077)
    device = Device(args.termux, args.serial)
    state = Path(args.state)
    if args.action == 'collect':
        collect(device, state)
        print('Snapshot saved:', state)
        return
    record = json.loads((state / 'state.json').read_text())
    if args.action == 'plan':
        if not args.profile:
            parser.error('--profile required')
        profile = json.loads(Path(args.profile).read_text())
        if record['original_sha256'] != profile['floating_sha256']:
            parser.error('Snapshot XML does not match profile')
        for key, value in profile['identity'].items():
            if record['identity'].get(key) != value:
                parser.error('Snapshot identity mismatch: ' + key)
        for package, sha in profile['apks'].items():
            apks = record['apks'].get(package, [])
            if len(apks) != 1 or digest((state / apks[0]['file']).read_bytes()) != sha:
                parser.error('Snapshot APK hash mismatch: ' + package)
        original = (state / 'floating_feature.original.xml').read_bytes()
        if digest(original) != record['original_sha256']:
            parser.error('Snapshot XML hash mismatch')
        changed = edit_xml(original, profile['features'])
        print(json.dumps({'goal': profile['goal'], 'activation_allowed': profile['activation_allowed'],
                          'features': profile['features'], 'components': profile['components'],
                          'settings': profile.get('settings', {}), 'blockers': profile.get('blockers', []),
                          'planned_xml_sha256': digest(changed), 'device_access': 'NOT ATTEMPTED'}, indent=2))
        return
    if args.action == 'enable':
        if not args.profile:
            parser.error('--profile required')
        enable(device, state, record, args.profile)
    elif args.action == 'rollback':
        rollback(device, state, record)
    else:
        guard(device, state, record)
        for name, command in {
            'logcat-after': 'logcat -d -t 4000 -v threadtime',
            'services-after': 'dumpsys activity services ' + PACKAGE,
            'aod-after': 'dumpsys package com.samsung.android.app.aodservice',
            'sss-after': 'dumpsys package ' + PACKAGE,
            'widgets-after': 'dumpsys appwidget',
        }.items():
            (state / (name + '.txt')).write_bytes(device.run(command))
        print('Evidence collected; inspect UI and logs before declaring success.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
