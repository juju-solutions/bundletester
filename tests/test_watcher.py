import json
import mock
import pkg_resources
import os
import tempfile
import unittest

from bundletester import watcher


TEST_FILE = pkg_resources.resource_filename(__name__, 'watcher')
BUNDLE_LP = "lp:~cf-charmers/charms/bundles/cloudfoundry/bundle"


def resource(name):
    return os.path.join(TEST_FILE, name)


class TestWatcher(unittest.TestCase):

    def test_normalize_bundle_location(self):
        self.assertRaises(ValueError, watcher.normalize_bundle_location, '')
        self.assertEqual(watcher.normalize_bundle_location(
            "bundle:~user/bundle"),
            "lp:~user/charms/bundles/bundle/bundle")

        self.assertEqual(watcher.normalize_bundle_location(BUNDLE_LP),
                         BUNDLE_LP)

    @mock.patch('subprocess.check_call')
    def test_watcher_get_bundle(self, mcall):
        watcher.get_bundle("bundle:~cf-charmers/cloudfoundry", 'b')
        self.assertListEqual(mcall.call_args[0][0],
                             ['bzr', 'checkout', '--lightweight',
                              BUNDLE_LP, 'b'])

    @mock.patch('subprocess.check_call')
    def test_watcher_get_bundle_lp(self, mcall):
        watcher.get_bundle(BUNDLE_LP, 'b')
        self.assertListEqual(mcall.call_args[0][0],
                             ['bzr', 'checkout', '--lightweight',
                              BUNDLE_LP, 'b'])

    @mock.patch('subprocess.check_output')
    def test_get_bzr_revno(self, mcall):
        watcher.get_bzr_revno('.')
        self.assertEqual(mcall.call_args[0][0], ['bzr', 'revno', '.'])

    def test_watcher_record_revisions(self):
        _, fn = tempfile.mkstemp()
        revisions = {'nats': 1, 'dea': 3}
        watcher.record_revisions(fn, revisions)
        self.assertTrue(os.path.exists(fn))
        data = json.load(open(fn))
        self.assertEqual(revisions, data)
        os.unlink(fn)

    def test_watcher_load_revisions(self):
        revisions = watcher.load_revisions('missing')
        self.assertEqual(revisions, {})
        revisions = watcher.load_revisions(resource('revisions.json'))
        self.assertEqual(revisions['nats'], 1)
        self.assertEqual(revisions['dea'], 5)
