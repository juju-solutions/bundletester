import mock
import unittest

from bundletester import builder
from bundletester import config


class O(object):
    pass


class TestBuilder(unittest.TestCase):

    @mock.patch('subprocess.check_call')
    def test_builder_virtualenv(self, mcall):
        parser = config.Parser()
        b = builder.Builder(parser, None)
        b.build_virtualenv('venv')
        self.assertEqual(mcall.call_args[0][0],
                         ['virtualenv', '-p', 'python', 'venv'])

    @mock.patch('subprocess.check_call')
    def test_builder_sources(self, mcall):
        parser = config.Parser()
        b = builder.Builder(parser, None)

        parser.sources.append('ppa:foo')
        b.add_sources(False)
        self.assertEqual(mcall.call_args,
                         mock.call(['sudo', 'apt-add-repository',
                                    '--yes', 'ppa:foo']))

    @mock.patch('subprocess.check_call')
    def test_builder_packages(self, mcall):
        parser = config.Parser()
        b = builder.Builder(parser,  None)
        parser.packages.extend(['a', 'b'])
        b.install_packages()
        self.assertEqual(mcall.call_args,
                         mock.call(['sudo', 'apt-get', 'install', '-qq', '-y',
                                    'a', 'b'], env=mock.ANY))

    @mock.patch('subprocess.call')
    def test_builder_bootstrap_dryrun(self, mcall):
        parser = config.Parser()
        f = O()
        f.dryrun = True
        f.environment = 'local'
        b = builder.Builder(parser, f)
        b.bootstrap()
        self.assertFalse(mcall.called)
