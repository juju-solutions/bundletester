from functools import partial
from mock import patch
import argparse
import os
import unittest


class TestBundleSpec(unittest.TestCase):
    here = os.path.abspath(os.path.dirname(__file__))
    lb = os.path.join(here, "watcher/bundle.yaml")

    def makeone(self, spec):
        from bundletester.tester import BundleSpec
        return BundleSpec.parse_cli(spec)

    def test_bundle_spec_error(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            self.makeone("/tmp/belching-balrog.yaml")

    def test_bundle_spec_error_not_raised_relative_path(self):
        spec = self.makeone("belching-balrog.yaml")
        assert spec.path == "belching-balrog.yaml"

    def test_bundle_spec_name_only(self):
        spec = self.makeone("devel")
        assert spec.path is "devel"

    def test_bundle_spec_path_only(self):
        spec = self.makeone(self.lb)
        assert spec.path.startswith('/')
        assert spec.path.endswith('watcher/bundle.yaml')


class TestFindBundleFile(unittest.TestCase):
    here = os.path.abspath(os.path.dirname(__file__))

    def makeone(self, path=TestBundleSpec.lb, explicit=True, directory=here):
        from bundletester.tester import BundleSpec
        from bundletester.spec import find_bundle_file
        return partial(find_bundle_file,
                       directory,
                       BundleSpec(path=path, explicit_path=explicit),
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
