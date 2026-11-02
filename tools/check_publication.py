#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORIES = {'.git', '__pycache__', 'graphify-out'}
SENSITIVE_PATTERNS = {
    'GitHub token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    'AWS access key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'local user path': re.compile(r'(?:/Users/|/home/)[A-Za-z0-9_.-]+/'),
    'device fingerprint identifier': re.compile(r'\b(?:RXCW\w{6,}|IMEI\s*[:=]\s*\d{14,16})\b', re.I),
    'credential assignment': re.compile(r'''(?im)^\s*(?:export\s+)?(?:GITHUB_TOKEN|GH_TOKEN|SAMSUNG_TOKEN|API_KEY|PASSWORD)\s*=\s*["']?[A-Za-z0-9_./+\-]{12,}'''),
}


def verify():
    approved = json.loads((ROOT / 'PUBLIC_FILES.json').read_text())
    if not isinstance(approved, list) or not all(isinstance(item, str) for item in approved):
        raise ValueError('PUBLIC_FILES.json must contain a list of relative paths')
    if len(approved) != len(set(approved)):
        raise ValueError('Duplicate approved path')
    expected = set(approved)
    if not {'PUBLIC_FILES.json', 'SHA256SUMS.json'}.issubset(expected):
        raise ValueError('Publication manifests must be approved')
    for name in expected:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or (ROOT / path).resolve() != ROOT / path:
            raise ValueError('Unsafe approved path: ' + name)
    actual = set()
    for path in ROOT.rglob('*'):
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        if path.name == '.DS_Store':
            continue
        if path.is_symlink():
            raise ValueError('Symlink not allowed: ' + str(relative))
        if path.is_file():
            actual.add(relative.as_posix())
    if actual != expected:
        raise ValueError('Unapproved files: ' + str(sorted(actual - expected)) +
                         '; missing approved files: ' + str(sorted(expected - actual)))
    for name in sorted(expected):
        content = (ROOT / name).read_bytes()
        if len(content) > 1_000_000 or b'\x00' in content:
            raise ValueError('Unexpected large or binary file: ' + name)
        text = content.decode('utf-8')
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                raise ValueError('Potential ' + label + ' in ' + name)
        if name.endswith('.md'):
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if target.startswith(('https://', 'http://', '#', 'mailto:')):
                    continue
                local = (ROOT / name).parent / target.split('#')[0]
                if not local.exists():
                    raise ValueError('Broken local link in ' + name + ': ' + target)
    recorded = json.loads((ROOT / 'SHA256SUMS.json').read_text())
    calculated = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                  for name in sorted(expected - {'SHA256SUMS.json'})}
    if recorded != calculated:
        raise ValueError('SHA256SUMS.json does not match approved files')
    if (ROOT / '.git').exists():
        tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT,
                                 capture_output=True, check=True).stdout.decode().split('\x00')
        unexpected = set(filter(None, tracked)) - expected
        if unexpected:
            raise ValueError('Private/unapproved tracked Git files: ' + str(sorted(unexpected)))
    return sorted(expected)


def main():
    parser = argparse.ArgumentParser(description='Validate only the explicitly approved public package')
    parser.add_argument('--archive', type=Path, help='Optional ZIP outside this project; never uploads')
    args = parser.parse_args()
    try:
        approved = verify()
        if args.archive:
            destination = args.archive.expanduser().resolve()
            if destination == ROOT or ROOT in destination.parents:
                raise ValueError('Archive must be outside project')
            with zipfile.ZipFile(destination, mode='x', compression=zipfile.ZIP_DEFLATED) as archive:
                for name in approved:
                    archive.write(ROOT / name, arcname='NowBrief-S23-OneUI9/' + name)
            print('Local archive created from approved files only.')
        print('PASS:', len(approved), 'approved text files; no unexpected files or common secret patterns.')
        print('Manual privacy and licensing review is still required before publication.')
    except (ValueError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        sys.exit('Publication check failed: ' + str(error))


if __name__ == '__main__':
    main()
