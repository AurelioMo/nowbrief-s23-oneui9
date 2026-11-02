#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET


def run(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def certificate(apksigner, apk):
    output = run([apksigner, 'verify', '--verbose', '--print-certs', str(apk)])
    matches = re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]+)', output)
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one signer')
    return matches[0], output


def main():
    parser = argparse.ArgumentParser(description='Native permission-only bridge; real signing, no signature transplantation')
    parser.add_argument('--aod', required=True)
    parser.add_argument('--systemui', required=True)
    parser.add_argument('--key', required=True, help='Matching ROM signing key, PKCS#8 DER')
    parser.add_argument('--cert', required=True, help='Matching X.509 certificate')
    parser.add_argument('--android-jar', required=True)
    parser.add_argument('--aapt2', default='aapt2')
    parser.add_argument('--apksigner', default='apksigner')
    parser.add_argument('--target-sdk', type=int, required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        parser.error('Output already exists')
    cert_aod, audit_aod = certificate(args.apksigner, args.aod)
    cert_ui, audit_ui = certificate(args.apksigner, args.systemui)
    if cert_aod != cert_ui:
        raise RuntimeError('AOD and SystemUI signer mismatch; inspect rotation lineage manually')
    identities = []
    for apk in (args.aod, args.systemui):
        tree = run([args.aapt2, 'dump', 'xmltree', '--file', 'AndroidManifest.xml', apk])
        matches = re.findall(r':sharedUserId[^\n]*?="([^"]+)"', tree)
        if len(matches) != 1:
            raise RuntimeError('Cannot establish shared UID from manifest')
        identities.append(matches[0])
    if identities[0] != identities[1]:
        raise RuntimeError('AOD and SystemUI have different sharedUserId')
    namespace = 'http://schemas.android.com/apk/res/android'
    ET.register_namespace('android', namespace)
    def android(name):
        return '{' + namespace + '}' + name
    manifest = ET.Element('manifest', {'package': 'com.samsung.android.systemui.genuibridge',
        android('sharedUserId'): identities[0], android('versionCode'): '1', android('versionName'): '1.0'})
    ET.SubElement(manifest, 'uses-sdk', {android('minSdkVersion'): '34',
                                     android('targetSdkVersion'): str(args.target_sdk)})
    ET.SubElement(manifest, 'uses-permission', {android('name'):
        'com.samsung.android.smartsuggestions.permission.BIND_GENUI_SERVICE'})
    ET.SubElement(manifest, 'application', {android('hasCode'): 'false', android('label'): 'GenUIBridge'})
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        source = work / 'AndroidManifest.xml'
        source.write_bytes(ET.tostring(manifest, encoding='utf-8', xml_declaration=True))
        unsigned = work / 'unsigned.apk'
        signed = work / 'signed.apk'
        run([args.aapt2, 'link', '-I', args.android_jar, '--manifest', str(source), '-o', str(unsigned)])
        run([args.apksigner, 'sign', '--key', args.key, '--cert', args.cert,
             '--out', str(signed), str(unsigned)])
        cert_bridge, audit_bridge = certificate(args.apksigner, signed)
        if cert_bridge != cert_aod:
            raise RuntimeError('Signing key/certificate does not match AOD; output rejected')
        binary_manifest = run([args.aapt2, 'dump', 'xmltree', '--file', 'AndroidManifest.xml', str(signed)])
        output.write_bytes(signed.read_bytes())
        output.with_suffix('.audit.txt').write_text(audit_aod + '\n' + audit_ui + '\n' + audit_bridge +
            '\n' + binary_manifest + '\nSTATIC ONLY: Package Manager / UID / permission grant NOT tested.\n')
    print('Cryptographically verified bridge:', output)
    print('NOT installed. Shared UID admission and GenUI binding remain unverified.')


if __name__ == '__main__':
    main()
