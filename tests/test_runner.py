from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def invoke(self, *arguments):
        return subprocess.run(['sh', str(ROOT / 'run.sh'), *arguments],
                              capture_output=True, text=True, timeout=10)

    def test_help_without_device(self):
        result = self.invoke('help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('activate PASTA_NOVA', result.stdout)

    def test_unknown_command_fails(self):
        self.assertEqual(self.invoke('unknown').returncode, 2)

    def test_missing_state_fails_before_device_access(self):
        for action in ('activate', 'rollback', 'snapshot', 'diagnose',
                       'biometric-fix', 'rollback-biometric', 'backup-data'):
            with self.subTest(action=action):
                self.assertEqual(self.invoke(action).returncode, 2)
