import os
import pkg_resources
import logging
import unittest

from bundletester import builder
from bundletester import config
from bundletester import spec
from bundletester import runner


TEST_FILES = pkg_resources.resource_filename(__name__, 'files')


def locate(name):
    return os.path.join(TEST_FILES, name)


class TestRunner(unittest.TestCase):

    def test_run_suite(self):
        logging.basicConfig(level=logging.CRITICAL)
        parser = config.Parser()
        parser.bootstrap = False
        env = builder.Builder(parser)
        suite = spec.Suite(config=parser)
        suite.spec(locate('test02'))
        self.assertEqual(suite[0].name, 'test02')
        run = runner.Runner(suite, env)
        results = list(run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['returncode'], 0)
