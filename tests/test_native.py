import unittest
import xml.etree.ElementTree as ET

from native import PDE, edit_xml, component_override, shared_uid_grant, writable_state, IMMUTABLE_SNAPSHOT
from audit_installed import elements


class XmlTests(unittest.TestCase):
    def test_absent(self):
        root = ET.fromstring(edit_xml(b'<SecFloatingFeatureSet><other>42</other></SecFloatingFeatureSet>'))
        self.assertEqual(root.findtext(PDE), 'TRUE')
        self.assertEqual(root.findtext('other'), '42')

    def test_false(self):
        source = ('<SecFloatingFeatureSet><' + PDE + '>FALSE</' + PDE + '></SecFloatingFeatureSet>').encode()
        root = ET.fromstring(edit_xml(source))
        self.assertEqual(len(root.findall(PDE)), 1)
        self.assertEqual(root.findtext(PDE), 'TRUE')

    def test_comment(self):
        source = ('<SecFloatingFeatureSet><!-- <' + PDE + '>TRUE</' + PDE + '> --></SecFloatingFeatureSet>').encode()
        edited = edit_xml(source)
        self.assertIn(b'<!--', edited)
        self.assertEqual(len(ET.fromstring(edited).findall(PDE)), 1)

    def test_duplicate(self):
        source = ('<SecFloatingFeatureSet>' + ('<' + PDE + '>FALSE</' + PDE + '>') * 2 + '</SecFloatingFeatureSet>').encode()
        with self.assertRaises(ValueError):
            edit_xml(source)

    def test_wrong_root(self):
        with self.assertRaises(ValueError):
            edit_xml(b'<wrong/>')

    def test_profile_changes(self):
        root = ET.fromstring(edit_xml(b'<SecFloatingFeatureSet><keep>42</keep></SecFloatingFeatureSet>',
            {'SEC_FLOATING_FEATURE_COMMON_CONFIG_AI_VERSION': '20261'}))
        self.assertIsNone(root.find(PDE))
        self.assertEqual(root.findtext('keep'), '42')
        self.assertEqual(root.findtext('SEC_FLOATING_FEATURE_COMMON_CONFIG_AI_VERSION'), '20261')

    def test_snapshot_is_immutable(self):
        with self.assertRaises(RuntimeError):
            writable_state(IMMUTABLE_SNAPSHOT)

    def test_component_overrides(self):
        dump = ('    User 0: enabled=0\n      disabledComponents:\n'
                '        example.Activity\n      enabledComponents:\n        example.Other\n'
                '    User 10: enabled=0\n      disabledComponents:\n        example.Default\n')
        self.assertEqual(component_override(dump, 'example/.Activity'), 'disabled')
        self.assertEqual(component_override(dump, 'example/.Other'), 'enabled')
        self.assertEqual(component_override(dump, 'example/.Default'), 'default')

    def test_shared_grant_is_not_request(self):
        dump = ('Packages:\n  requested permissions:\n    example.perm\nShared users:\n'
                '  SharedUser [android.uid.systemui] (1):\n    appId=10048\n'
                '    install permissions:\n      example.granted: granted=true\n'
                '      example.denied: granted=false\n')
        self.assertIsNone(shared_uid_grant(dump, 'example.perm'))
        self.assertTrue(shared_uid_grant(dump, 'example.granted'))
        self.assertFalse(shared_uid_grant(dump, 'example.denied'))

    def test_active_package_not_hidden_or_queries(self):
        dump = ('Packages:\n  Package [example] (1):\n    User 0: enabled=0\n'
                '      disabledComponents:\n        example.Activity\n'
                'Hidden system packages:\n  Package [example] (2):\n    User 0: enabled=0\n'
                '      enabledComponents:\n        example.Activity\nQueries:\n    User 0:\n')
        self.assertEqual(component_override(dump, 'example/.Activity'), 'disabled')

    def test_manifest_permission_definition(self):
        tree = ('  E: manifest\n    E: permission\n'
                '      A: http://schemas.android.com/apk/res/android:name(0x01010003)="example.permission"\n'
                '      A: http://schemas.android.com/apk/res/android:protectionLevel(0x01010009)=0x00000003\n')
        permission = elements(tree)[1]
        self.assertEqual(permission['type'], 'permission')
        self.assertEqual(permission['attributes']['name'], 'example.permission')
        self.assertEqual(permission['attributes']['protectionLevel'], '0x00000003')


if __name__ == '__main__':
    unittest.main()
