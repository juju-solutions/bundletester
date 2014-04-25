import pkg_resources
import os
import unittest

from bundletester import config

TEST_FILES = pkg_resources.resource_filename(__name__, 'files')


def locate(name):
    return os.path.join(TEST_FILES, name)


class TestConfig(unittest.TestCase):

    def test_parser_defaults(self):
        parser = config.Parser()
        self.assertFalse(parser.bootstrap)
        self.assertFalse(parser.reset)
        self.assertTrue(parser.virtualenv)
        self.assertEqual(parser.sources, [])
        self.assertEqual(parser.packages, [])
        self.assertEqual(parser.makefile, ['proof', 'lint', 'test'])
        self.assertEqual(parser.setup, [])

    def test_config_parse(self):
        parser = config.Parser(locate('sample.yaml'))
        self.assertFalse(parser.bootstrap)
        self.assertFalse(parser.reset)
        self.assertTrue(parser.virtualenv)
        self.assertEqual(parser.sources, [])
        self.assertEqual(parser.packages, [])
        self.assertEqual(parser.setup, ['setupAll'])

    def test_config_parent(self):
        parent = config.Parser()
        parent.update({'foo': 'bar', 'alpha': 'beta'})
        parser = config.Parser(parent=parent)
        parser['alpha'] = 'gamma'

        self.assertEqual(parser.alpha, 'gamma')
        self.assertEqual(parser.foo, 'bar')

    def test_merge_bool(self):
        parent = config.Parser(alpha=True)
        parser = config.Parser(alpha=False, parent=parent)
        self.assertFalse(parser.alpha)

    def test_merge_list_single(self):
        parent = config.Parser(source=[1, 2])
        parser = config.Parser(source=3, parent=parent)
        self.assertEqual(parser.source, [1, 2, 3])

    def test_merge_list_list(self):
        parent = config.Parser(source=[1, 2])
        parser = config.Parser(source=[4, 5], parent=parent)
        self.assertEqual(parser.source, [1, 2, 4, 5])
