from functools import partial
from mock import patch
import os
import unittest


class TestFindBundleFile(unittest.TestCase):
    here = os.path.abspath(os.path.dirname(__file__))
    lb = os.path.join(here, "watcher/bundle.yaml")

    def makeone(self, path=lb, explicit=True, directory=here):
        from bundletester.spec import find_bundle_file
        return partial(find_bundle_file,
                       directory,
                       path,
                       filter_yamls=lambda x:x)

    def test_find_bundle_file_rel(self):
        fbf = self.makeone(path="watcher/bundle.yaml", explicit=False)
        out = fbf()
        assert out.startswith('/')
        assert out.endswith('watcher/bundle.yaml')

    def test_find_bundle_file_unspecified(self):
        fbf = self.makeone(path=None,
                           directory=os.path.join(self.here, 'watcher'))
        out = fbf()
        assert out.startswith('/')
        assert out.endswith('watcher/bundle.yaml')

    def test_find_bundle_file_unspecified_empty(self):
        fbf = self.makeone(path=None)
        assert fbf() is None

    def test_find_bundle_file_unspecified_ambiguous_raises(self):
        with patch('glob.glob', return_value=["a.yaml", "b.yaml"]) as g:
            fbf = self.makeone(path=None)
            with self.assertRaises(OSError):
                fbf()

    def test_find_bundle_file_explicit(self):
        assert self.makeone(path="/wat", explicit=True)() == '/wat'
