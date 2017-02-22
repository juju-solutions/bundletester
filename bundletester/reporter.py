import json
import logging
import sys
import re
from collections import defaultdict
from itertools import repeat
from xml.etree.ElementTree import Element, SubElement, tostring

from blessings import Terminal

log = logging.getLogger('reporter')


class _O(dict):
    def __getattr__(self, k):
        return self[k]


def constants(value):
    return repeat(value).next


class Reporter(object):
    status_flags = defaultdict(constants("FAIL"), {
        0: 'PASS',
        1: 'ERROR',
    })

    def __init__(self, fp=sys.stdout, options=None):
        self.fp = fp
        self.options = options
        self.messages = []
        self.term = Terminal()
        self.suite = None

    def set_suite(self, suite):
        self.suite = suite

    def emit(self, msg):
        """Emit a single record to output fp"""
        self.messages.append(_O(msg))

    def header(self):
        pass

    def _calculate(self):
        total_seconds = 0
        by_code = {}
        for m in self.messages:
            total_seconds += m.get('duration', 0)
            ec = m['returncode']
            ec_ct = by_code.get(ec,  0)
            by_code[ec] = ec_ct + 1
        return total_seconds, by_code

    def write(self, s, *args, **kwargs):
        kwargs['t'] = self.term
        self.fp.write(s.format(*args, **kwargs))

    def report_errors(self, by_code):
        if len(by_code.keys()) > 1 or 0 not in by_code:
            for m in self.messages:
                if m['returncode'] == 0:
                    continue
                self.fp.write('-' * 78 + '\n')
                status = self.status_flags[m['returncode']]
                self.write('{t.bold}{t.red}{}: ', status)
                if m.get('suite'):
                    self.write('{m.suite}{t.normal}::', m=m)
                self.write("{t.bold}{t.red}{m.test}{t.normal}\n",
                           m=m)
                self.write("[{t.cyan}{m.exit:<30}{t.normal} exit"
                           " {t.red}{m.returncode}{t.normal}]\n", m=m)
                self.write("{t.yellow}{m.output}{t.normal}\n", m=m)

    def summary(self):
        total_seconds, by_code = self._calculate()
        if len(self.messages):
            self.write('\n')
        self.report_errors(by_code)

        for ec, ct in by_code.items():
            status = self.status_flags[ec]
            self.write("{t.bold}{}{t.normal}: {t.cyan}{}{t.normal} ",
                       status, ct)
        ct = len(self.messages)
        if self.suite:
            ct = len(self.suite)
            skipped = len(self.suite) - len(self.messages)
            if skipped != 0:
                self.write('SKIP:{t.cyan}{}{t.normal} ', skipped)

        self.write("Total: {t.cyan}{}{t.normal} ({t.cyan}{}{t.normal} sec)\n",
                   ct, total_seconds)

    def exit(self):
        for m in self.messages:
            if m['returncode'] != 0:
                return 1
        return 0


class DotReporter(Reporter):
    responses = defaultdict(constants('F'), {
        0: '.',
        1: 'E',
    })

    def emit(self, msg):
        super(DotReporter, self).emit(msg)
        msg = _O(msg)
        ec = msg.get('returncode', 0)
        if self.options and self.options.verbose:
            self.write("{m.test:<40} ", m=msg)
        self.write(self.responses[ec])
        if self.options and self.options.verbose:
            self.write('\n')
        self.fp.flush()

    def header(self):
        self.write("Running Tests...\n")


class SpecReporter(Reporter):

    def __init__(self, fp=sys.stdout, options=None):
        super(SpecReporter, self).__init__(fp, options)
        self.level = 0
        self.width = 74
        self.current_suite = None

    def emit(self, message):
        super(SpecReporter, self).emit(message)
        message = _O(message)
        suite = message.get('suite')
        if suite != self.current_suite:
            if self.current_suite is not None:
                self.level -= 1
            if suite:
                self.write("{t.bold}{}{t.normal}\n", suite)
                self.level += 1
            self.current_suite = suite

        width = self.width - (4 * self.level)
        color = "green" if message.returncode == 0 else "red"
        fmt = "{:<%s} {t.%s}{}{t.normal}\n" % (width, color)
        cmd = message.test
        self.write(fmt, cmd, self.status_flags[message.returncode])

    def write(self, message, *args, **kwargs):
        if self.level:
            message = "    " * self.level + message
        super(SpecReporter, self).write(message, *args, **kwargs)

    def summary(self):
        self.level = 0
        super(SpecReporter, self).summary()


class JSONReporter(Reporter):
    def summary(self):
        opts = self.options
        d = {
            'tests': self.messages,
            'revision': str(opts.fetcher.get_revision(opts.testdir)).strip(),
            'testdir': opts.testdir,
        }
        if opts.bundle:
            d['bundle'] = self.suite.model['bundle']

        json.dump(d, self.fp, indent=2)
        self.write('\n')
        self.fp.flush()


class XMLReporter(Reporter):
    def summary(self):
        opts = self.options
        top = Element('testsuites')

        testsuitename = "{}-{}".format(
            opts.testdir,
            str(opts.fetcher.get_revision(opts.testdir)).strip())
        testsuite = SubElement(
            top,
            'testsuite',
            {"name": testsuitename, "tests": "{}".format(len(self.messages))})
        for msg in self.messages:
            testcase = SubElement(
                testsuite,
                'testcase',
                {"name": msg.test, "classname": msg.suite, "time": "{}".format(
                    msg.get('duration', 0))})
            if msg.returncode != 0:
                errorelement = SubElement(
                    testcase,
                    'error',
                    {"message": self.get_error(msg)})
                errorelement.text = msg.output

        self.fp.write(tostring(top, encoding="utf-8"))
        self.fp.flush()

    def get_error(self, msg):
        m = re.search('ERROR[A-Za-z\t .]+', msg.output)
        if m:
            found = m.group(0)
            return found
        return "Unknown"


FACTORY = {'json': JSONReporter,
           'dot': DotReporter,
           'spec': SpecReporter,
           'xml': XMLReporter}


def get_reporter(name, fp, options):
    return FACTORY[name](fp, options)
