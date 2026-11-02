import unittest
import xml.etree.ElementTree as ET

from signature_permissions import PACKAGE, PERMISSION, patch_allowlist


class SignatureAllowlistTests(unittest.TestCase):
    def test_adds_only_target_permission(self):
        original = b'<permissions><!-- keep --><signature-permissions package="other"><permission name="keep"/></signature-permissions></permissions>'
        modified = patch_allowlist(original)
        root = ET.fromstring(modified)
        self.assertIn(b'<!-- keep -->', modified)
        self.assertEqual(root.find("signature-permissions[@package='other']/permission").get('name'), 'keep')
        target = root.find("signature-permissions[@package='" + PACKAGE + "']")
        self.assertEqual([entry.get('name') for entry in target], [PERMISSION])

    def test_preserves_existing_package_permissions(self):
        original = ('<permissions><signature-permissions package="' + PACKAGE + '"><permission name="keep"/></signature-permissions></permissions>').encode()
        root = ET.fromstring(patch_allowlist(original))
        self.assertEqual(len(root), 1)
        self.assertEqual([entry.get('name') for entry in root[0]], ['keep', PERMISSION])

    def test_rejects_existing_permission(self):
        original = ('<permissions><signature-permissions package="' + PACKAGE + '"><permission name="' + PERMISSION + '"/></signature-permissions></permissions>').encode()
        with self.assertRaises(ValueError):
            patch_allowlist(original)

    def test_rejects_duplicate_package(self):
        entry = '<signature-permissions package="' + PACKAGE + '"/>'
        original = ('<permissions>' + entry * 2 + '</permissions>').encode()
        with self.assertRaises(ValueError):
            patch_allowlist(original)

    def test_rejects_unexpected_root(self):
        with self.assertRaises(ValueError):
            patch_allowlist(b'<invalid/>')
