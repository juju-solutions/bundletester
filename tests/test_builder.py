import mock
import unittest

from bundletester import builder
from bundletester import config


class TestBuilder(unittest.TestCase):

    @mock.patch('subprocess.check_call')
    def test_builder_virtualenv(self, mcall):
        parser = config.Parser()
        b = builder.Builder(parser)
        b.build_virtualenv('venv')
        self.assertEqual(mcall.call_args[0][0], ['virtualenv', 'venv'])

    @mock.patch('subprocess.check_call')
    def test_builder_sources(self, mcall):
        parser = config.Parser()
        b = builder.Builder(parser)

        parser.sources.append('ppa:foo')
        b.add_sources(False)
        self.assertEqual(mcall.call_args,
                         mock.call(['sudo', 'apt-add-repository',
                                    '--yes', 'ppa:foo']))

    @mock.patch('subprocess.check_call')
    def test_builder_packages(self, mcall):
        parser = config.Parser()
        b = builder.Builder(parser)
        parser.packages.extend(['a', 'b'])
        b.install_packages()
        self.assertEqual(mcall.call_args,
                         mock.call(['sudo', 'apt-get', 'install', '-qq', '-y',
                                    'a', 'b']))
