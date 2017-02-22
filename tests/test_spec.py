import pkg_resources
import os
import unittest

import mock

from bundletester import config
from bundletester import models
from bundletester import spec

TEST_FILES = pkg_resources.resource_filename(__name__, 'files')


class Options(dict):
    def __getattr__(self, key):
        return self[key]


def locate(name):
    return os.path.join(TEST_FILES, name)


class TestSpec(unittest.TestCase):

    def test_spec_missing(self):
        self.assertRaises(OSError, spec.Spec, locate('missing'))

    def test_spec_no_config(self):
        test = spec.Spec(locate('test01'))
        self.assertEqual(test.name, os.path.basename(locate('test01')))
        self.assertEqual(test.executable, [os.path.abspath(locate('test01'))])
        # Verify we got a default config file representation
        self.assertEqual(test.virtualenv, False)

    def test_spec_config(self):
        test = spec.Spec(locate('test02'))
        self.assertEqual(test.name, 'test02')
        self.assertEqual(test.executable, [os.path.abspath(locate('test02'))])
        # Verify we got a default config file representation
        self.assertEqual(test.setup, ['setup02'])

    def test_spec_config_parent(self):
        parent = config.Parser()
        parent['bootstrap'] = False
        test = spec.Spec(locate('test02'), parent)
        self.assertEqual(test.name, 'test02')
        self.assertEqual(test.executable, [os.path.abspath(locate('test02'))])
        self.assertEqual(test.setup,  ['setup02'])
        self.assertEqual(test.bootstrap,  False)
        self.assertEqual(test.reset, True)

    def test_spec_init(self):
        parent = config.Parser()
        parent['bootstrap'] = False
        test = spec.Spec(locate('test02'), parent)
        self.assertEqual(test.name, 'test02')

    def test_spec_arguments(self):
        test = spec.Spec(['ls', '-al'])
        # still found the executable
        self.assertEqual(test.executable,
                         ['/bin/ls', '-al'])


class TestDeployCommand(unittest.TestCase):

    def test_not_bundle(self):
        model = models.Charm({
            'directory': '',
            'testdir': ''
        })

        class options(object):
            tests_yaml = None
        suite = spec.Suite(model, options)
        self.assertIsNone(suite.deploy_cmd())

    def test_bundle_deploy_is_false(self):
        model = models.Bundle({
            'directory': '',
            'testdir': ''
        })

        class options(object):
            tests_yaml = None
        suite = spec.Suite(model, options)
        suite._config = config.Parser(**{
            'bundle_deploy': False,
        })
        self.assertIsNone(suite.deploy_cmd())

    def test_bundle_deploy_is_true_juju_1(self):
        model = fake_model()
        options = FakeOptions(juju_major_version=1)

        suite = spec.Suite(model, options)
        suite._config = config.Parser(**{
            'bundle_deploy': True
        })
        with mock.patch('bundletester.spec.os.path.exists') as exists:
            def _exists(path):
                if path == model['bundle']:
                    return True
                return os.path.exists(path)
            exists.side_effect = _exists
            self.assertEqual(
                suite.deploy_cmd(),
                ['juju-deployer', '-Wvd', '-c', model['bundle']])

    def test_bundle_deploy_is_true(self):
        model = fake_model()
        options = FakeOptions(juju_major_version=2)

        suite = spec.Suite(model, options)
        suite._config = config.Parser(**{
            'bundle_deploy': True
        })
        with mock.patch('bundletester.spec.os.path.exists') as exists:
            def _exists(path):
                if path == model['bundle']:
                    return True
                return os.path.exists(path)
            exists.side_effect = _exists
            self.assertEqual(
                suite.deploy_cmd(),
                ['juju', 'deploy', model['bundle']])

    def test_bundle_deploy_file(self):
        model = fake_model()

        class options(object):
            tests_yaml = None
        suite = spec.Suite(model, options)
        suite._config = config.Parser(**{
            'bundle_deploy': 'mydeployfile'
        })
        with mock.patch('bundletester.spec.os.path.isfile') as isfile, \
                mock.patch('bundletester.spec.os.access') as access:
            fullpath = os.path.join(
                model['testdir'], suite.config.bundle_deploy)

            def _isfile(path):
                if path == fullpath:
                    return True
                return os.path.isfile(path)

            def _access(path, flags):
                if path == fullpath:
                    return True
                return os.access(path, flags)
            isfile.side_effect = _isfile
            access.side_effect = _access
            self.assertEqual(
                suite.deploy_cmd(),
                [fullpath]
            )

    def test_timeout_juju_1(self):
        model = fake_model()
        options = FakeOptions(juju_major_version=1)

        suite = spec.Suite(model, options)
        suite._config = config.Parser(**{
            'bundle_deploy': True,
            'deployment_timeout': 60,
        })
        with mock.patch('bundletester.spec.os.path.exists') as exists:
            def _exists(path):
                if path == model['bundle']:
                    return True
                return os.path.exists(path)
            exists.side_effect = _exists
            self.assertEqual(
                suite.deploy_cmd(),
                ['juju-deployer', '-Wvd', '-c', model['bundle'], '-t', '60']
            )
            cmd = suite.wait_cmd()
            self.assertIsNone(cmd)

    def test_timeout(self):
        model = fake_model()
        options = FakeOptions(juju_major_version=2)

        suite = spec.Suite(model, options)
        suite._config = config.Parser(**{
            'bundle_deploy': True,
            'deployment_timeout': 60,
        })
        with mock.patch('bundletester.spec.os.path.exists') as exists:
            def _exists(path):
                if path == model['bundle']:
                    return True
                return os.path.exists(path)
            exists.side_effect = _exists
            self.assertEqual(
                suite.deploy_cmd(),
                ['juju', 'deploy', 'mybundle.yaml']
            )
            cmd = suite.wait_cmd()
            self.assertEqual(cmd, ['juju-wait', '-v', '-t', '60'])


def fake_model():
    return models.Bundle({
        'directory': '',
        'testdir': '',
        'bundle': 'mybundle.yaml',
    })


class FakeOptions:
    tests_yaml = None
    verbose = True
    deployment = None

    def __init__(self, juju_major_version):
        self.juju_major_version = juju_major_version
