from functools import partial
import glob
import os
import unittest

HERE = os.path.abspath(os.path.dirname(__file__))


class TestFindBundleFile(unittest.TestCase):
    lb = os.path.join(HERE, "watcher/bundle.yaml")

    def makeone(self, path=lb, explicit=True, directory=HERE):
        from bundletester.spec import find_bundle_file
        return partial(find_bundle_file,
                       directory,
                       path,
                       filter_yamls=lambda x: x)

    def test_find_bundle_file_rel(self):
        fbf = self.makeone(path="watcher/bundle.yaml", explicit=False)
        out = fbf()
        assert out.startswith('/')
        assert out.endswith('watcher/bundle.yaml')

    def test_find_bundle_file_unspecified_empty(self):
        fbf = self.makeone(path=None)
        assert fbf() is None

    def test_find_bundle_file_unspecified_ambiguous_raises(self):
        fbf = self.makeone(path=None, directory=os.path.join(HERE, 'watcher'))
        with self.assertRaises(OSError):
            fbf()

    def test_find_bundle_file_explicit_raise(self):
        with self.assertRaises(OSError):
            assert self.makeone(path="/wat")()


class TestFilterYamls(unittest.TestCase):
    pat = os.path.join(HERE, 'watcher', "*.yaml")
    yamls = glob.glob(pat)

    def test_v4_recognized(self):
        from bundletester.spec import filter_yamls
        r = filter_yamls(self.yamls)
        self.assertEqual(self.yamls, r)
