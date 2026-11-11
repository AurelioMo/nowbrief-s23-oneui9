"""Execute the real module shell scripts against a simulated Android environment."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_kernelsu', ROOT / 'scripts/prepare-kernelsu.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

MOCK = r'''
import hashlib, json, os, pathlib, sys
base = pathlib.Path(os.environ['FAKE_ANDROID'])
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with (base / 'calls').open('a') as stream:
    stream.write(name + ' ' + ' '.join(args) + '\n')
if name == 'id': print('0')
elif name == 'getprop':
    if args[0] == 'sys.boot_completed': print('0' if os.getenv('BOOT_INCOMPLETE') else '1')
    else: print('test/rom' if not os.getenv('WRONG_ROM') else 'other/rom')
elif name == 'readlink': print('mnt:1' if not os.getenv('WRONG_NS') or '/proc/1/' in args[0] else 'mnt:2')
elif name == 'sha256sum':
    print(hashlib.sha256(pathlib.Path(args[0]).read_bytes()).hexdigest() + '  ' + args[0])
elif name == 'pm': print('package:' + str(base / 'app.apk'))
elif name == 'settings': print('1' if not os.getenv('WRONG_SETTINGS') else '0')
elif name == 'chcon': sys.exit(1 if os.getenv('FAIL_CONTEXT') else 0)
elif name == 'chown': pass
elif name == 'ls':
    print(('u:object_r:wrong:s0' if os.getenv('WRONG_CONTEXT') else 'u:object_r:system_file:s0') + ' ' + args[-1])
elif name == 'sync': pass
elif name == 'stat':
    path = pathlib.Path(args[-1])
    if path == base / 'target.xml' and (base / 'mountinfo').read_text():
        path = base / 'module/payload/floating_feature.xml'
    result = path.stat()
    print(str(result.st_dev) + ':' + str(result.st_ino))
elif name == 'mount':
    if os.getenv('FAIL_MOUNT'): sys.exit(1)
    source, target = map(pathlib.Path, args[-2:])
    target.write_bytes(source.read_bytes())
    (base / 'mountinfo').write_text('100 50 1:2 ' + str(source) + ' ' + str(target) + ' rw - ext4 test rw\n')
elif name == 'umount':
    if os.getenv('FAIL_UNMOUNT'): sys.exit(1)
    (base / 'target.xml').write_bytes((base / 'module/payload/original.xml').read_bytes())
    (base / 'mountinfo').write_text('')
else: raise RuntimeError('Unexpected mock command: ' + name)
'''


class KernelSUShellTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.module = self.base / 'module'
        shutil.copytree(ROOT / 'kernelsu-module', self.module)
        (self.module / 'payload').mkdir()
        self.original = b'<SecFloatingFeatureSet><keep>1</keep></SecFloatingFeatureSet>'
        self.modified = b'<SecFloatingFeatureSet><keep>2</keep></SecFloatingFeatureSet>'
        (self.base / 'target.xml').write_bytes(self.original)
        (self.base / 'mountinfo').write_text('')
        (self.base / 'app.apk').write_bytes(b'fake APK')
        (self.base / 'calls').write_text('')
        (self.module / 'payload/original.xml').write_bytes(self.original)
        (self.module / 'payload/floating_feature.xml').write_bytes(self.modified)
        apk_hash = hashlib.sha256(b'fake APK').hexdigest()
        config = dict(EXPECTED_FINGERPRINT='test/rom', ORIGINAL_SHA=hashlib.sha256(self.original).hexdigest(),
                      MODIFIED_SHA=hashlib.sha256(self.modified).hexdigest(),
                      APK_SMART=apk_hash, APK_AOD=apk_hash, APK_SYSTEMUI=apk_hash, APK_SETTINGS=apk_hash)
        (self.module / 'payload/profile.sh').write_text(''.join(f'{key}={value}\n' for key, value in config.items()))
        lib = self.module / 'lib.sh'
        lib.write_text(lib.read_text().replace('/system/etc/floating_feature.xml', str(self.base / 'target.xml'))
                       .replace('/proc/self/mountinfo', str(self.base / 'mountinfo')))
        bindir = self.base / 'bin'
        bindir.mkdir()
        mock = bindir / 'mock'
        mock.write_text('#!' + sys.executable + '\n' + MOCK)
        mock.chmod(0o755)
        for command in ('id', 'getprop', 'readlink', 'sha256sum', 'pm', 'settings', 'chcon', 'chown',
                        'ls', 'sync', 'stat', 'mount', 'umount'):
            (bindir / command).symlink_to(mock)
        self.env = dict(os.environ, FAKE_ANDROID=str(self.base), PATH=str(bindir) + os.pathsep + os.environ['PATH'])

    def run_control(self, operation, success=True, **environment):
        result = subprocess.run(['sh', str(self.module / 'control.sh'), operation],
                                env=dict(self.env, **environment), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_install_defaults_to_inert_boot(self):
        self.run_control('boot')
        self.assertEqual((self.base / 'calls').read_text(), '')
        self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)

    def test_early_boot_stage_and_unarmed_service_are_inert(self):
        for script in ('post-fs-data.sh', 'service.sh'):
            result = subprocess.run(['sh', str(self.module / script)], env=self.env,
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0)
        self.assertEqual((self.base / 'calls').read_text(), '')

    def test_authorized_service_runs_once_after_boot(self):
        (self.module / 'armed').touch()
        for _ in range(2):
            result = subprocess.run(['sh', str(self.module / 'service.sh')], env=self.env,
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0)
        self.assertTrue((self.module / 'attempt').exists())
        calls = (self.base / 'calls').read_text().splitlines()
        self.assertEqual(len([line for line in calls if line.startswith('mount ')]), 1)

    def test_apply_is_idempotent_and_rollback_restores_xml(self):
        self.run_control('apply')
        self.assertTrue((self.module / 'attempt').exists())
        self.run_control('apply')
        calls = (self.base / 'calls').read_text().splitlines()
        self.assertEqual(len([line for line in calls if line.startswith('mount ')]), 1)
        self.assertFalse(any('settings --user 0 put' in line or 'pm enable' in line for line in calls))
        self.run_control('rollback')
        self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)
        self.assertFalse((self.module / 'attempt').exists())

    def test_refuses_rom_namespace_settings_and_context_failures(self):
        for environment in ('WRONG_ROM', 'WRONG_NS', 'WRONG_SETTINGS', 'FAIL_CONTEXT', 'WRONG_CONTEXT', 'BOOT_INCOMPLETE'):
            with self.subTest(environment=environment):
                self.run_control('apply', success=False, **{environment: '1'})
                self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)
                self.assertFalse((self.module / 'attempt').exists())

    def test_refuses_corrupt_payload_baseline_or_apk(self):
        for path in (self.module / 'payload/floating_feature.xml', self.module / 'payload/original.xml', self.base / 'app.apk'):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(b'corrupt')
                self.run_control('apply', success=False)
                self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)
                path.write_bytes(original)

    def test_does_not_reuse_changed_active_xml(self):
        (self.base / 'target.xml').write_bytes(b'new ROM XML')
        self.run_control('apply', success=False)
        self.assertFalse((self.module / 'attempt').exists())

    def test_foreign_mount_cannot_be_replaced_or_unmounted(self):
        record = '101 50 1:2 /foreign ' + str(self.base / 'target.xml') + ' rw - ext4 test rw\n'
        (self.base / 'mountinfo').write_text(record)
        self.run_control('apply', success=False)
        self.run_control('rollback', success=False)
        self.assertEqual((self.base / 'mountinfo').read_text(), record)

    def test_failed_mount_blocks_automatic_retry(self):
        (self.module / 'armed').touch()
        self.run_control('boot', success=False, FAIL_MOUNT='1')
        self.assertTrue((self.module / 'attempt').exists())
        self.assertFalse((self.module / 'armed').exists())
        self.run_control('boot')
        self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)

    def test_confirmation_required_and_boot_authorization_consumed_once(self):
        self.run_control('arm', success=False)
        self.run_control('apply')
        self.run_control('arm', success=False)
        self.run_control('confirm')
        self.run_control('arm')
        # Simulate a reboot losing all bind mounts, retaining the module state.
        (self.base / 'target.xml').write_bytes(self.original)
        (self.base / 'mountinfo').write_text('')
        self.run_control('boot')
        self.assertFalse((self.module / 'armed').exists())
        self.assertTrue((self.module / 'attempt').exists())
        self.run_control('boot')

    def test_boot_preflight_failure_also_consumes_authorization(self):
        (self.module / 'armed').touch()
        self.run_control('boot', success=False, WRONG_ROM='1')
        self.assertFalse((self.module / 'armed').exists())

    def test_unmount_failure_retains_transaction_record(self):
        self.run_control('apply')
        self.run_control('rollback', success=False, FAIL_UNMOUNT='1')
        self.assertTrue((self.module / 'mount.record').exists())
        self.run_control('rollback')

    def test_installer_validates_without_activating(self):
        wrapper = self.base / 'install.sh'
        wrapper.write_text('#!/bin/sh\nset -eu\nMODPATH=$1\nabort() { echo "$*" >&2; exit 1; }\nset_perm_recursive() { :; }\nset_perm() { :; }\nui_print() { echo "$*"; }\n. "$MODPATH/customize.sh"\n')
        result = subprocess.run(['sh', str(wrapper), str(self.module)], env=self.env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.module / 'armed').exists())
        self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)
        result = subprocess.run(['sh', str(wrapper), str(self.module)],
                                env=dict(self.env, WRONG_ROM='1'), capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)

    def test_concurrent_operation_does_not_touch_state(self):
        (self.module / 'lock').mkdir()
        self.run_control('apply', success=False)
        self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)


class KernelSUPackageTests(unittest.TestCase):
    def test_public_profile_rejects_unapproved_xml(self):
        profile = json.loads((ROOT / 'profiles/s23-oneui9-tested.json').read_text())
        with self.assertRaises(ValueError):
            builder.validate_xml(b'<SecFloatingFeatureSet/>', profile)

    def test_private_zip_is_reproducible_and_never_contains_activation_flags(self):
        original = b'<SecFloatingFeatureSet><keep>1</keep></SecFloatingFeatureSet>'
        profile = json.loads((ROOT / 'profiles/s23-oneui9-tested.json').read_text())
        profile['floating_sha256'] = hashlib.sha256(original).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            first, second = (Path(directory) / name for name in ('one.zip', 'two.zip'))
            builder.build_zip(original, profile, first)
            builder.build_zip(original, profile, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn('customize.sh', archive.namelist())
                self.assertEqual(archive.read('payload/original.xml'), original)
                self.assertFalse(set(archive.namelist()) & {'armed', 'attempt', 'confirmed', 'mount.record'})
            with self.assertRaises(FileExistsError):
                builder.build_zip(original, profile, first)
