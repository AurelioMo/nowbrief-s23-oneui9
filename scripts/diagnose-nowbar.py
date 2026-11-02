#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess


def main():
    parser = argparse.ArgumentParser(description='Read-only Android 17 Now Bar diagnostics; no pm check-permission')
    parser.add_argument('--output', required=True)
    parser.add_argument('--serial')
    parser.add_argument('--termux', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    package = 'com.samsung.android.smartsuggestions'
    component = package + '/.feature.aisuggestion.genui.service.GenUIService'
    commands = {
        'package-help': 'cmd package help',
        'activity-help': 'cmd activity help',
        'permission-registry': 'dumpsys package permissions',
        'sss-package': 'dumpsys package ' + package,
        'systemui-shared-uid': 'dumpsys package com.android.systemui',
        'aod-package': 'dumpsys package com.samsung.android.app.aodservice',
        'service-explicit-including-disabled': 'cmd package query-services --components --user 0 --query-flags 512 -n ' + component,
        'service-intent-including-disabled': 'cmd package query-services --components --user 0 --query-flags 512 -a ' + package + '.feature.aisuggestion.genui.BIND -p ' + package,
        'running-services': 'dumpsys activity services ' + package,
        'current-logcat': 'logcat -d -t 5000 -v threadtime',
        'namespaces': 'readlink /proc/1/ns/mnt; readlink /proc/self/ns/mnt; cat /proc/1/mountinfo',
    }
    journal = []
    for label, command in commands.items():
        arguments = ['su', '-mm', '-c', command]
        if not args.termux:
            arguments = ['adb'] + (['-s', args.serial] if args.serial else []) + ['exec-out', shlex.join(arguments)]
        result = subprocess.run(arguments, capture_output=True, timeout=120)
        (destination / (label + '.stdout.txt')).write_bytes(result.stdout)
        (destination / (label + '.stderr.txt')).write_bytes(result.stderr)
        journal.append({'command': command, 'exit': result.returncode})
        if result.returncode and not args.termux and b'cannot connect to daemon' in result.stderr:
            break
    (destination / 'commands.json').write_text(json.dumps(journal, indent=2) + '\n')
    print('Diagnostic evidence:', destination, '- unknown commands/errors are NOT permission denials.')


if __name__ == '__main__':
    main()
