import json
import mock
import unittest
from StringIO import StringIO
from xml.etree import ElementTree

from bundletester import reporter


class TestReporter(unittest.TestCase):
    def make_sample(self, exit=0, output=""):
        return {'returncode': exit,
                'end': '2014-03-31T07:06:43.191730',
                'start': '2014-03-31T07:06:43.189408',
                'suite': 'suite01',
                'test': 'test02',
                'duration': 0.002322,
                'output': output}

    def test_dot_reporter(self):
        buf = StringIO()
        r = reporter.DotReporter(fp=buf)
        r.emit(self.make_sample())
        output = buf.getvalue()
        self.assertTrue(output.endswith('.'))

    def get_report_output(self, report_type):
        buf = StringIO()
        opts = mock.Mock()
        opts.fetcher.get_revision.return_value = '1'
        opts.testdir = '/tmp/test'
        opts.bundle = False
        if report_type == "JSON":
            r = reporter.JSONReporter(fp=buf, options=opts)
        elif report_type == "XML":
            r = reporter.XMLReporter(fp=buf, options=opts)
        sample1 = self.make_sample()
        sample2 = self.make_sample(1)
        r.emit(sample1)
        r.emit(sample2)
        r.summary()
        return buf.getvalue()

    def test_json_reporter(self):
        output = self.get_report_output("JSON")
        result = json.loads(output)
        self.assertEqual(result['revision'], '1')
        self.assertEqual(result['testdir'], '/tmp/test')
        self.assertEqual(result['tests'][0]['returncode'], 0)
        self.assertEqual(result['tests'][1]['returncode'], 1)

    def test_xml_reporter(self):
        output = self.get_report_output("XML")
        tree = ElementTree.fromstring(output)
        self.assertEqual(tree.findall('testsuite')[0].attrib['name'], "/tmp/test-1")
        self.assertEqual(tree.findall('testsuite')[0]
                         .findall("testcase")[1]
                         .find('error').attrib['message'], "Unknown")
