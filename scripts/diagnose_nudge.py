#!/usr/bin/env python3
import argparse
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import zipfile

from native import Device, PACKAGE, digest


def summarize_policy(policy):
    packages = policy.get('blockPackages')
    activities = policy.get('blockActivities')
    locales = policy.get('allowInputLocales')
    if not all(isinstance(value, list) and all(isinstance(item, str) for item in value)
               for value in (packages, activities, locales)):
        raise ValueError('Unexpected policy schema')
    return {
        'policy_version': policy.get('version'),
        'google_messages_explicitly_blocked': 'com.google.android.apps.messaging' in packages,
        'whatsapp_conversation_explicitly_blocked':
            'com.whatsapp/com.whatsapp.Conversation' in activities,
        'portuguese_prefix_listed': 'pt' in locales,
        'scope': 'Bundled policy only; runtime policies may differ. No functional success inferred.',
    }


def main():
    parser = argparse.ArgumentParser(description='Read-only bundled Nudge policy inspection; no policy bypass')
    parser.add_argument('--termux', action='store_true')
    parser.add_argument('--serial')
    parser.add_argument('--profile', default=str(Path(__file__).resolve().parents[1] /
                                               'profiles/s23-oneui9-tested.json'))
    args = parser.parse_args()
    device = Device(args.termux, args.serial)
    profile = json.loads(Path(args.profile).read_text())
    for key, expected in profile['identity'].items():
        if device.text('getprop ' + key) != expected:
            raise RuntimeError('Device identity mismatch: ' + key)
    paths = device.text('pm path ' + PACKAGE).splitlines()
    if len(paths) != 1 or not paths[0].startswith('package:'):
        raise RuntimeError('Unexpected APK layout')
    content = device.run('cat ' + shlex.quote(paths[0][8:]))
    apk_hash = digest(content)
    if apk_hash != profile['apks'][PACKAGE]:
        raise RuntimeError('Active APK hash differs from audited profile')
    with zipfile.ZipFile(io.BytesIO(content)) as apk:
        policy = json.loads(apk.read('assets/autofill_nudge_allow_policy.json'))
    result = summarize_policy(policy)
    result['active_apk_sha256'] = apk_hash
    result['now_nudge_setting'] = device.text('settings get global now_nudge_setting')
    result['changes_applied'] = False
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError, KeyError, zipfile.BadZipFile,
            subprocess.SubprocessError) as error:
        sys.exit(str(error))
