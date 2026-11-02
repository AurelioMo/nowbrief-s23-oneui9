#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def elements(tree):
    output = []
    stack = []
    for line in tree.splitlines():
        indent = len(line) - len(line.lstrip())
        if line.lstrip().startswith('E:'):
            while stack and stack[-1]['indent'] >= indent:
                stack.pop()
            entry = {'type': line.strip().split()[1], 'attributes': {}, 'indent': indent}
            stack.append(entry)
            output.append(entry)
        elif line.lstrip().startswith('A:') and stack:
            attribute = re.search(r'(?:android:)?([A-Za-z][A-Za-z0-9]*)\(0x[0-9a-f]+\)=(.*)', line)
            if attribute:
                value = attribute[2].split(' (Raw:')[0]
                stack[-1]['attributes'][attribute[1]] = value.strip('"')
    return output


def main():
    parser = argparse.ArgumentParser(description='Read-only snapshot APK and manifest audit')
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--aapt2', required=True)
    parser.add_argument('--apksigner', required=True)
    args = parser.parse_args()
    snapshot = Path(args.snapshot)
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=False)
    state = json.loads((snapshot / 'state.json').read_text())
    permission = 'com.samsung.android.smartsuggestions.permission.BIND_GENUI_SERVICE'
    report = {'identity': state['identity'], 'packages': {}}
    baseline = {}
    for file in sorted(snapshot.iterdir()):
        if file.is_file():
            baseline[file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
    for package, apks in state['apks'].items():
        if not apks:
            continue
        if len(apks) != 1:
            raise RuntimeError('Split APK manifest audit not implemented')
        apk = snapshot / apks[0]['file']
        if baseline[apk.name] != apks[0]['sha256']:
            raise RuntimeError('Snapshot hash mismatch: ' + package)
        def command(arguments):
            result = subprocess.run(arguments, capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            return result.stdout + result.stderr
        tree = command([args.aapt2, 'dump', 'xmltree', '--file', 'AndroidManifest.xml', str(apk)])
        signing = command([args.apksigner, 'verify', '--verbose', '--print-certs', str(apk)])
        badging = command([args.aapt2, 'dump', 'badging', str(apk)])
        for label, content in [('manifest', tree), ('signing', signing), ('badging', badging)]:
            (destination / (package + '.' + label + '.txt')).write_text(content)
        parsed = elements(tree)
        relevant = [entry for entry in parsed if any(term in entry['attributes'].get('name', '').lower()
                    for term in ('genui', 'brief', 'nudge', 'suggestionui', 'onboarding'))]
        report['packages'][package] = {'sha256': baseline[apk.name],
            'signer_sha256': re.findall(r'Signer #\d+ certificate SHA-256 digest: (\w+)', signing),
            'manifest': parsed[0], 'relevant_elements': relevant,
            'defines_genui_permission': [entry for entry in parsed if entry['type'] == 'permission'
                                         and entry['attributes'].get('name') == permission],
            'requests_genui_permission': any(entry['type'] == 'uses-permission' and
                entry['attributes'].get('name') == permission for entry in parsed),
            'services': [entry for entry in parsed if entry['type'] == 'service']}
    (destination / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (destination / 'baseline-hashes.json').write_text(json.dumps(baseline, indent=2) + '\n')
    print('Read-only audit complete:', destination)


if __name__ == '__main__':
    main()
