import json
import sys


class Reporter(object):
    responses = {
        0: 'PASS',
        -1: 'ERROR',
        1: 'ERROR',
        None: 'FAIL'
    }

    def __init__(self, fp=sys.stdout, options=None):
        self.fp = fp
        self.options = options
        self.messages = []

    def emit(self, msg):
        """Emit a single record to output fp"""
        self.messages.append(msg)

    def summary(self):
        total_seconds = 0
        by_code = {}
        for m in self.messages:
            total_seconds += m.get('total_seconds', 0)
            ec = m['returncode']
            ec_ct = by_code.get(ec,  0)
            by_code[ec] = ec_ct + 1
        for ec, ct in by_code.items():
            self.fp.write("%s: %s " % (self.responses.get(ec), ct))
        self.fp.write("Total: %s (%s sec)\n" % (
            len(self.messages), total_seconds))

    def exit(self):
        for m in self.messages:
            if m['returncode'] != 0:
                sys.exit(1)
        sys.exit(1)


class DotReporter(Reporter):
    responses = {
        0: '.',
        -1: 'E',
        1: 'E',
        None: 'F'
    }

    def emit(self, msg):
        self.messages.append(msg)
        ec = msg.get('returncode', 0)
        self.fp.write(self.responses.get(ec, 'F'))
        self.fp.flush()


class JSONReporter(Reporter):
    def summary(self):
        json.dump(self.messages, self.fp, indent=2)
        self.fp.write('\n')
        self.fp.flush()
