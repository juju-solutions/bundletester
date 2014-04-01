import json
import unittest
from StringIO import StringIO


from bundletester import reporter


class TestReporter(unittest.TestCase):
    def make_sample(self, exit=0, output=""):
        return {'returncode': 0,
                'end': '2014-03-31T07:06:43.191730',
                'start': '2014-03-31T07:06:43.189408',
                'test': 'test02',
                'result': exit,
                'duration': 0.002322,
                'output': output}

    def test_dot_reporter(self):
        buf = StringIO()
        r = reporter.DotReporter(fp=buf)
        r.emit(self.make_sample())
        output = buf.getvalue()
        self.assertTrue(output.endswith('.'))

    def test_json_reporter(self):
        buf = StringIO()
        r = reporter.JSONReporter(fp=buf)
        sample1 = self.make_sample()
        sample2 = self.make_sample(1)
        r.emit(sample1)
        r.emit(sample2)
        r.summary()
        output = buf.getvalue()
        self.assertEqual(output,
                         json.dumps([sample1, sample2],
                                    indent=2) + '\n')
