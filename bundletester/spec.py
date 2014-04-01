import glob
import os
from bundletester import config


def normalize_path(path, relto):
    dirname = os.path.dirname(relto)
    if not os.path.isabs(path):
        path = os.path.join(dirname, path)
    return path


def loader(testfile, parent=None):
    result = config.Parser()
    if not os.path.exists(testfile) or \
            not os.access(testfile, os.X_OK | os.R_OK):
        raise OSError('Expected executable test file: %s' % testfile)

    result['name'] = os.path.basename(testfile)
    result['executable'] = os.path.abspath(testfile)

    base, ext = os.path.splitext(result['executable'])
    control_file = "%s.yaml" % base
    if not os.path.exists(control_file):
        control_file = None
    result = config.Parser(path=control_file, parent=parent)
    result['name'] = os.path.basename(testfile)
    result['executable'] = os.path.abspath(testfile)
    if result.bundle:
        result.bundle = normalize_path(result.bundle, result.executable)
    return result


def Spec(testfile, parent):
    return loader(testfile, parent)


class Suite(list):
    def __init__(self, config):
        self.config = config

    def spec(self, testfile):
        self.append(Spec(testfile, self.config))

    def find_tests(self, bundledir, filterset=None):
        testpat = self.config.get('tests', 'test*')
        tests = set(glob.glob(os.path.join(bundledir, testpat)))
        if filterset:
            filterset = [os.path.join(bundledir, f) for f in filterset]
            tests = tests.intersection(set(filterset))
        for test in sorted(tests):
            if os.access(test, os.X_OK):
                self.spec(test)
