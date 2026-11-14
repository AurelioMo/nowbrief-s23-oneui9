import json
import unittest
import xml.etree.ElementTree as ET

from memory_gesture import patch_preferences


class GesturePreferencesTests(unittest.TestCase):
    def original(self, data=None):
        root = ET.Element('map')
        ET.SubElement(root, 'int', name='plugin_[gesture]_version', value='2')
        ET.SubElement(root, 'boolean', name='unrelated', value='true')
        if data is not None:
            ET.SubElement(root, 'string', name='gesture_multi-finger-data').text = json.dumps(data)
        return ET.tostring(root)

    def test_adds_mapping_preserving_other_gestures(self):
        original = {'key-2-finger-swipe-up': {'action': 'HOME_KEY'}}
        root = ET.fromstring(patch_preferences(self.original(original)))
        data = json.loads(root.find("./string[@name='gesture_multi-finger-data']").text)
        self.assertEqual(data['key-2-finger-swipe-up'], original['key-2-finger-swipe-up'])
        self.assertEqual(data['key-3-finger-swipe-down']['action'], 'OPEN_APP')
        self.assertEqual(root.find("./boolean[@name='unrelated']").get('value'), 'true')

    def test_rejects_conflicting_assignment(self):
        with self.assertRaises(ValueError):
            patch_preferences(self.original({'key-3-finger-swipe-down': {'action': 'HOME_KEY'}}))

    def test_requires_initialized_plugin(self):
        with self.assertRaises(ValueError):
            patch_preferences(b'<map/>')

    def test_idempotent(self):
        patched = patch_preferences(self.original())
        self.assertEqual(patched, patch_preferences(patched))

    def test_rejects_duplicate_keys(self):
        with self.assertRaises(ValueError):
            patch_preferences(b'<map><boolean name="same"/><boolean name="same"/></map>')
