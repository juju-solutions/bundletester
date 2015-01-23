import unittest
import argparse
import os


class TestBundleSpec(unittest.TestCase):
    lb = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      "watcher/bundle.yaml")
    def makeone(self, spec):
        from bundletester.tester import BundleSpec
        return BundleSpec.parse_cli(spec)

    def test_bundle_spec_error(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            self.makeone("/tmp/belching-balrog.yaml")

    def test_bundle_spec_name_only(self):
        spec = self.makeone("devel")
        assert spec.path is None
        assert spec.name == 'devel'

    def test_bundle_spec_path_only(self):
        spec = self.makeone(self.lb)
        assert spec.path.startswith('/')
        assert spec.path.endswith('watcher/bundle.yaml')
        assert spec.name is None

    def test_bundle_spec_path_and_name(self):
        spec = self.makeone(self.lb + ":"  + "wat")
        assert spec.path.startswith('/')
        assert spec.path.endswith('watcher/bundle.yaml')
        assert spec.name == 'wat'
