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
elif name == 'settings':
    if os.getenv('SETTINGS_UNAVAILABLE'):
        print('cmd: Failure calling service settings')
        sys.exit(1)
    print('1' if not os.getenv('WRONG_SETTINGS') else '0')
elif name == 'am': pass
elif name == 'chcon': sys.exit(1 if os.getenv('FAIL_CONTEXT') else 0)
elif name == 'chown': pass
elif name == 'ls':
    print(('u:object_r:wrong:s0' if os.getenv('WRONG_CONTEXT') else 'u:object_r:system_file:s0') + ' ' + args[-1])
elif name == 'sync': pass
elif name == 'pidof':
    if not os.getenv('SYSTEM_STOPPED'): print('1234')
    else: sys.exit(1)
elif name == 'sleep':
    if os.getenv('FAIL_SLEEP'): sys.exit(1)
elif name == 'cat':
    if args[0] == '/proc/sys/kernel/random/boot_id': print('test-boot-id')
    else: sys.stdout.write(pathlib.Path(args[0]).read_text())
elif name == 'stat':
    if args[1] in ('%u', '%g'):
        print('0')
        sys.exit(0)
    path = pathlib.Path(args[-1])
    for line in (base / 'mountinfo').read_text().splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[4] == str(path):
            path = pathlib.Path(fields[3])
            break
    result = path.stat()
    print(str(result.st_dev) + ':' + str(result.st_ino))
elif name == 'mount':
    if os.getenv('FAIL_MOUNT'): sys.exit(1)
    source, target = map(pathlib.Path, args[-2:])
    target.write_bytes(source.read_bytes())
    with (base / 'mountinfo').open('a') as stream:
        stream.write('100 50 1:2 ' + str(source) + ' ' + str(target) + ' rw - ext4 test rw\n')
elif name == 'umount':
    if os.getenv('FAIL_UNMOUNT'): sys.exit(1)
    target = pathlib.Path(args[-1])
    original = ('biometric.original.xml' if target.name == 'biometric.xml' else 'original.xml')
    target.write_bytes((base / 'module/payload' / original).read_bytes())
    kept = [line for line in (base / 'mountinfo').read_text().splitlines()
            if len(line.split()) < 5 or line.split()[4] != str(target)]
    (base / 'mountinfo').write_text(''.join(line + '\n' for line in kept))
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
        (self.base / 'framework-res.apk').write_bytes(b'fake platform APK')
        self.bio_original = b'<permissions><signature-permissions package="com.samsung.android.smartsuggestions"><permission name="com.samsung.android.smartsuggestions.permission.BRIEF_LIFECYCLE"/></signature-permissions></permissions>'
        self.bio_modified = b'<permissions><signature-permissions package="com.samsung.android.smartsuggestions"><permission name="com.samsung.android.smartsuggestions.permission.BRIEF_LIFECYCLE"/><permission name="android.permission.SET_BIOMETRIC_DIALOG_ADVANCED"/></signature-permissions></permissions>'
        (self.base / 'biometric.xml').write_bytes(self.bio_original)
        (self.module / 'payload/original.xml').write_bytes(self.original)
        (self.module / 'payload/floating_feature.xml').write_bytes(self.modified)
        (self.module / 'payload/biometric.original.xml').write_bytes(self.bio_original)
        (self.module / 'payload/biometric.xml').write_bytes(self.bio_modified)
        bio = self.module / 'biometric.sh'
        bio.write_text(bio.read_text()
                       .replace('/system/etc/permissions/signature-permissions-downloadable.xml',
                                str(self.base / 'biometric.xml'))
                       .replace('/system/framework/framework-res.apk', str(self.base / 'framework-res.apk')))
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
                        'ls', 'sync', 'stat', 'mount', 'umount', 'pidof', 'sleep', 'cat', 'am'):
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

    def test_settings_wait_is_bounded(self):
        result = subprocess.run(
            ['sh', '-c', 'MODDIR="$1"; . "$MODDIR/lib.sh"; wait_settings 3', 'sh', str(self.module)],
            env=dict(self.env, SETTINGS_UNAVAILABLE='1'), capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        calls = (self.base / 'calls').read_text().splitlines()
        self.assertEqual(sum(line.startswith('settings ') for line in calls), 3)
        self.assertEqual(sum(line.startswith('sleep ') for line in calls), 2)

    def test_service_stops_before_mount_when_settings_unavailable(self):
        (self.module / 'armed').touch()
        result = subprocess.run(['sh', str(self.module / 'service.sh')],
                                env=dict(self.env, SETTINGS_UNAVAILABLE='1'),
                                capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('mount --bind', (self.base / 'calls').read_text())
        self.assertIn('Settings service unavailable', (self.module / 'boot.log').read_text())

    def setup_gesture(self):
        original, modified = b'<map/>', b'<map><boolean name="test" value="true"/></map>'
        self.prefs = self.base / 'prefs.xml'
        self.prefs.write_bytes(original)
        for name, data in (('gesture.original.xml', original), ('gesture.xml', modified)):
            (self.module / 'payload' / name).write_bytes(data)
        script = self.module / 'memory-gesture.sh'
        script.write_text(script.read_text().replace(
            '/data/user/0/com.samsung.android.app.homestar/shared_prefs/'
            'com.samsung.android.app.homestar.v2.preferences.xml', str(self.prefs)))
        apk_hash = hashlib.sha256(b'fake APK').hexdigest()
        (self.module / 'payload/gesture.sh').write_text(
            f'GESTURE_ORIGINAL_SHA={hashlib.sha256(original).hexdigest()}\n'
            f'GESTURE_MODIFIED_SHA={hashlib.sha256(modified).hexdigest()}\n'
            f'GESTURE_HOMEUP_SHA={apk_hash}\nGESTURE_HELPER_SHA={apk_hash}\n'
            'GESTURE_OLD_MEMORY=1\nGESTURE_OLD_HOMEUP=null\n')
        return original, modified

    def run_gesture(self, operation):
        return subprocess.run(['sh', str(self.module / 'memory-gesture.sh'), operation],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def test_gesture_apply_and_rollback_owned_snapshot(self):
        original, modified = self.setup_gesture()
        result = self.run_gesture('apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.prefs.read_bytes(), modified)
        self.assertTrue((self.module / 'gesture.changed').exists())
        result = self.run_gesture('rollback')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.prefs.read_bytes(), original)
        self.assertFalse((self.module / 'gesture.changed').exists())

    def test_gesture_refuses_changed_preferences(self):
        self.setup_gesture()
        self.prefs.write_bytes(b'user edit')
        self.assertNotEqual(self.run_gesture('apply').returncode, 0)
        self.assertEqual(self.prefs.read_bytes(), b'user edit')
        self.assertFalse((self.module / 'gesture.changed').exists())

    def test_gesture_rollback_retains_edited_preferences(self):
        self.setup_gesture()
        self.assertEqual(self.run_gesture('apply').returncode, 0)
        self.prefs.write_bytes(b'user edit')
        self.assertNotEqual(self.run_gesture('rollback').returncode, 0)
        self.assertEqual(self.prefs.read_bytes(), b'user edit')
        self.assertTrue((self.module / 'gesture.changed').exists())

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

    def test_bootstrap_and_rollback_journal(self):
        (self.module / 'payload/activate.sh').write_text(
            'echo applied > "$FAKE_ANDROID/activation"\n')
        (self.module / 'payload/restore.sh').write_text(
            'echo restored > "$FAKE_ANDROID/activation"\n')
        self.run_control('apply')
        self.assertTrue((self.module / 'apps.changed').exists())
        self.assertEqual((self.base / 'activation').read_text().strip(), 'applied')
        self.run_control('rollback')
        self.assertFalse((self.module / 'apps.changed').exists())
        self.assertEqual((self.base / 'activation').read_text().strip(), 'restored')

    def test_persistence_requires_confirmation_and_failed_boot_blocks_retry(self):
        self.run_control('persist', success=False)
        self.run_control('apply')
        self.run_control('persist', success=False)
        self.run_control('confirm')
        self.run_control('persist')
        self.assertTrue((self.module / 'persistent').exists())
        (self.base / 'target.xml').write_bytes(self.original)
        (self.base / 'mountinfo').write_text('')
        self.run_control('boot', success=False, FAIL_MOUNT='1')
        self.assertTrue((self.module / 'attempt').exists())
        self.run_control('boot')
        self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)
        self.run_control('rollback')
        self.assertFalse((self.module / 'persistent').exists())

    def enable_soft_reboot(self):
        with (self.module / 'payload/profile.sh').open('a') as stream:
            stream.write('SOFT_REBOOT_MODE=1\n')
            for name in ('SMART', 'AOD', 'SYSTEMUI', 'SETTINGS', 'MEMORY'):
                stream.write(f'PATH_{name}="{self.base / "app.apk"}"\n')
        (self.module / 'persistent').touch()

    def enable_biometric(self):
        with (self.module / 'payload/profile.sh').open('a') as stream:
            stream.write('BIO_ORIGINAL_SHA=' + hashlib.sha256(self.bio_original).hexdigest() + '\n')
            stream.write('BIO_MODIFIED_SHA=' + hashlib.sha256(self.bio_modified).hexdigest() + '\n')
            stream.write('APK_PLATFORM=' + hashlib.sha256(b'fake platform APK').hexdigest() + '\n')

    def test_biometric_allowlist_preflight_is_read_only_and_rollback_restores(self):
        self.enable_biometric()
        self.run_control('preflight')
        calls = (self.base / 'calls').read_text()
        self.assertNotIn('mount --bind', calls)
        self.assertEqual((self.base / 'biometric.xml').read_bytes(), self.bio_original)
        self.run_control('apply')
        self.assertEqual((self.base / 'biometric.xml').read_bytes(), self.bio_modified)
        self.assertTrue((self.module / 'biometric.record').exists())
        self.run_control('status')
        self.run_control('rollback')
        self.assertEqual((self.base / 'biometric.xml').read_bytes(), self.bio_original)
        self.assertFalse((self.module / 'biometric.record').exists())

    def test_biometric_allowlist_refuses_changed_baseline(self):
        self.enable_biometric()
        (self.base / 'biometric.xml').write_bytes(b'changed')
        self.run_control('preflight', success=False)
        self.run_control('apply', success=False)
        self.assertEqual((self.base / 'biometric.xml').read_bytes(), b'changed')
        self.assertFalse((self.module / 'biometric.record').exists())

    def test_soft_reboot_mounts_biometric_allowlist_before_framework(self):
        self.enable_soft_reboot()
        self.enable_biometric()
        self.run_control('early', BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        calls = (self.base / 'calls').read_text()
        self.assertNotIn('pm ', calls)
        self.assertNotIn('settings ', calls)
        self.assertEqual((self.base / 'biometric.xml').read_bytes(), self.bio_modified)
        self.run_control('finish')
        self.run_control('confirm')
        self.run_control('rollback')
        self.assertEqual((self.base / 'biometric.xml').read_bytes(), self.bio_original)

    def test_android_hash_alias_does_not_break_validation(self):
        wrapper = self.base / 'alias-test.sh'
        wrapper.write_text(
            'alias hash="true"\n'
            'MODDIR=$1\n. "$MODDIR/lib.sh"\nload_profile\ncheck_identity\ncheck_packages\n')
        result = subprocess.run(['sh', str(wrapper), str(self.module)], env=self.env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preflight_validates_without_mount_or_app_writes(self):
        self.run_control('preflight')
        calls = (self.base / 'calls').read_text()
        self.assertNotIn('mount --bind', calls)
        self.assertNotIn('pm enable', calls)
        self.assertNotIn('settings --user 0 put', calls)
        self.assertFalse((self.module / 'attempt').exists())

    def test_soft_reboot_mounts_early_without_package_manager(self):
        self.enable_soft_reboot()
        self.run_control('early', BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        calls = (self.base / 'calls').read_text()
        self.assertNotIn('pm ', calls)
        self.assertNotIn('settings ', calls)
        self.assertEqual((self.base / 'target.xml').read_bytes(), self.modified)
        self.assertTrue((self.module / 'early.pending').exists())
        self.run_control('finish')
        self.run_control('confirm')
        self.assertFalse((self.module / 'attempt').exists())
        self.run_control('early', BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        self.assertTrue((self.module / 'early.pending').exists())

    def test_soft_reboot_refuses_live_framework_and_corrupt_apk(self):
        self.enable_soft_reboot()
        self.run_control('early', success=False)
        self.run_control('early', success=False, BOOT_INCOMPLETE='1')
        self.assertFalse((self.module / 'attempt').exists())
        (self.base / 'app.apk').write_bytes(b'changed')
        self.run_control('early', success=False, BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        self.assertEqual((self.base / 'target.xml').read_bytes(), self.original)
        self.assertTrue((self.module / 'attempt').exists())
        self.run_control('early', success=False, BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')

    def test_soft_reboot_interrupted_attempt_cannot_be_confirmed_by_old_worker(self):
        self.enable_soft_reboot()
        self.run_control('early', BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        self.run_control('early', success=False, BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        self.assertFalse((self.module / 'early.pending').exists())
        self.run_control('finish', success=False)
        self.assertTrue((self.module / 'attempt').exists())

    def test_soft_reboot_boot_completed_callback_finishes_pending_stage(self):
        self.enable_soft_reboot()
        self.run_control('early', BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        result = subprocess.run(['sh', str(self.module / 'boot-completed.sh')],
                                env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.module / 'attempt').exists())
        self.assertFalse((self.module / 'early.pending').exists())
        self.assertTrue((self.module / 'confirmed').exists())

    def test_soft_reboot_stale_worker_cannot_confirm_new_generation(self):
        self.enable_soft_reboot()
        self.run_control('early', BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        result = subprocess.run(['sh', str(self.module / 'control.sh'), 'confirm', 'old-generation'],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.module / 'attempt').exists())
        self.assertFalse((self.module / 'confirmed').exists())

    def test_soft_reboot_service_failure_keeps_crash_interlock(self):
        self.enable_soft_reboot()
        self.run_control('early', BOOT_INCOMPLETE='1', SYSTEM_STOPPED='1')
        result = subprocess.run(['sh', str(self.module / 'service.sh')],
                                env=dict(self.env, FAIL_SLEEP='1'),
                                capture_output=True, text=True, timeout=15)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.module / 'attempt').exists())
        self.assertFalse((self.module / 'confirmed').exists())


class KernelSUPackageTests(unittest.TestCase):
    def test_soft_reboot_zip_pins_paths_without_shipping_runtime_markers(self):
        original = b'<SecFloatingFeatureSet/>'
        profile = json.loads((ROOT / 'profiles/s23-oneui9-tested.json').read_text())
        profile['floating_sha256'] = hashlib.sha256(original).hexdigest()
        profile['apks']['com.samsung.android.app.memory'] = 'test-memory-hash'
        paths = {package: '/data/app/' + package + '/base.apk' for package in profile['apks']}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'soft.zip'
            builder.build_zip(original, profile, output, ('set -eu\n', 'set -eu\n'), paths)
            with zipfile.ZipFile(output) as archive:
                config = archive.read('payload/profile.sh').decode()
                self.assertIn('SOFT_REBOOT_MODE=1', config)
                self.assertIn('PATH_MEMORY=/data/app/com.samsung.android.app.memory/base.apk', config)
                self.assertIn('boot-completed.sh', archive.namelist())
                self.assertNotIn('persistent', archive.namelist())
                self.assertNotIn('attempt', archive.namelist())

    def test_biometric_zip_ships_patched_allowlist_and_original(self):
        original = b'<SecFloatingFeatureSet/>'
        allowlist = b'<permissions><signature-permissions package="com.samsung.android.smartsuggestions"/></permissions>'
        profile = json.loads((ROOT / 'profiles/s23-oneui9-tested.json').read_text())
        profile['floating_sha256'] = hashlib.sha256(original).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'bio.zip'
            builder.build_zip(original, profile, output,
                              biometric={'original': allowlist, 'platform_sha256': 'platform-hash'})
            with zipfile.ZipFile(output) as archive:
                config = archive.read('payload/profile.sh').decode()
                self.assertIn('BIO_ORIGINAL_SHA=' + hashlib.sha256(allowlist).hexdigest(), config)
                self.assertIn('APK_PLATFORM=platform-hash', config)
                self.assertEqual(archive.read('payload/biometric.original.xml'), allowlist)
                self.assertIn(b'SET_BIOMETRIC_DIALOG_ADVANCED', archive.read('payload/biometric.xml'))

    def test_activation_scripts_preserve_settings_and_component_overrides(self):
        class Device:
            def text(self, command):
                if command.startswith('settings'):
                    return 'null'
                if command.endswith('com.samsung.android.app.memory'):
                    return 'android.permission.WRITE_SECURE_SETTINGS'
                return '  User 0: installed=true\n'
        profile = {'settings': {'secure/memory_three_finger_gesture': '1'},
                   'components': ['com.samsung.android.smartsuggestions/.Example']}
        apply, restore = builder.activation_scripts(Device(), profile)
        self.assertIn('put secure memory_three_finger_gesture 1', apply)
        self.assertIn('delete secure memory_three_finger_gesture', restore)
        self.assertIn('pm default-state --user 0', restore)
        self.assertIn('pm grant --user 0', apply)
        self.assertIn('pm revoke --user 0', restore)

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
