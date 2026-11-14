"""Prepare a conservative, device-pinned Home Up gesture transaction."""
import json
import xml.etree.ElementTree as ET

PREFS = ('/data/user/0/com.samsung.android.app.homestar/shared_prefs/'
         'com.samsung.android.app.homestar.v2.preferences.xml')
HOMEUP = 'com.samsung.android.app.homestar'
HELPER = 'com.incconutwo.savememory'


def patch_preferences(original):
    root = ET.fromstring(original)
    if root.tag != 'map':
        raise ValueError('Unexpected Home Up preferences')
    names = [child.get('name') for child in root]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate Home Up preferences')
    if root.find("./int[@name='plugin_[gesture]_version']") is None:
        raise ValueError('Home Up gesture plugin not initialized')
    desired = {
        'master_enabled': True,
        'gesture_gesture-settings': True,
        'gesture_multi-finger-gesture': True,
    }
    key = 'gesture_multi-finger-data'
    entry = root.find(f"./string[@name='{key}']")
    data = json.loads(entry.text) if entry is not None else {}
    if not isinstance(data, dict):
        raise ValueError('Unexpected gesture JSON')
    action = {
        'action': 'OPEN_APP',
        'launch': {'pkg': HELPER, 'cls': HELPER + '.LaunchActivity',
                   'label': 'Save Memory'},
    }
    existing = data.get('key-3-finger-swipe-down')
    if existing and existing.get('action') not in ('NONE', None) and existing != action:
        raise ValueError('Three-finger swipe down already assigned; refusing to overwrite')
    data['key-3-finger-gesture'] = True
    data['key-3-finger-swipe-down'] = action
    for name, value in desired.items():
        item = root.find(f"./boolean[@name='{name}']")
        if item is None:
            item = ET.SubElement(root, 'boolean', name=name)
        item.set('value', str(value).lower())
    if entry is None:
        entry = ET.SubElement(root, 'string', name=key)
    entry.text = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'
