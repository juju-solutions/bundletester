import os
import pkg_resources
import logging
import unittest

from bundletester import config
from bundletester import models
from bundletester import spec
from bundletester import runner


TEST_FILES = pkg_resources.resource_filename(__name__, 'files')


def locate(name):
    return os.path.join(TEST_FILES, name)


class O(object):
    pass


class TestRunner(unittest.TestCase):

    def test_run_suite(self):
        self.run_suite(juju_major_version=2)

    def test_run_suite_juju_1(self):
        self.run_suite(juju_major_version=1)

    def run_suite(self, juju_major_version):
        logging.basicConfig(level=logging.CRITICAL)
        parser = config.Parser()
        parser.bootstrap = False
        options = O()
        options.dryrun = True
        options.environment = 'local'
        options.failfast = True
        options.tests_yaml = None
        options.juju_major_version = juju_major_version
        model = models.TestDir({'name': 'testdir',
                                'directory': TEST_FILES,
                                'testdir': TEST_FILES})

        suite = spec.Suite(model, options=options)
        suite.spec(locate('test02'))
        self.assertEqual(suite[0].name, 'test02')
        run = runner.Runner(suite, options)

        results = list(run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['returncode'], 0)
