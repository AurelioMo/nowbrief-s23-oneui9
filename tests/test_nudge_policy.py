import unittest

from diagnose_nudge import summarize_policy


class NudgePolicyTests(unittest.TestCase):
    def test_explicit_blocks_are_reported_without_modification(self):
        policy = {'version': '1', 'blockPackages': ['com.google.android.apps.messaging'],
                  'blockActivities': ['com.whatsapp/com.whatsapp.Conversation'],
                  'allowInputLocales': ['pt']}
        result = summarize_policy(policy)
        self.assertTrue(result['google_messages_explicitly_blocked'])
        self.assertTrue(result['whatsapp_conversation_explicitly_blocked'])
        self.assertTrue(result['portuguese_prefix_listed'])
        self.assertEqual(len(policy['blockPackages']), 1)

    def test_absent_explicit_entry_is_not_reported_as_blocked(self):
        result = summarize_policy({'blockPackages': [], 'blockActivities': [],
                                   'allowInputLocales': []})
        self.assertFalse(result['google_messages_explicitly_blocked'])
        self.assertIn('runtime policies may differ', result['scope'])

    def test_unrecognized_schema_fails(self):
        with self.assertRaises(ValueError):
            summarize_policy({'blockPackages': 'all'})
