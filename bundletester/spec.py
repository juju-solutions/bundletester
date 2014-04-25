import glob
import logging
import os
from bundletester import config

from deployer.config import ConfigStack


def normalize_path(path, relto):
    dirname = os.path.dirname(relto)
    if not os.path.isabs(path):
        path = os.path.join(dirname, path)
    return path


def Spec(testfile, parent=None, dirname=None, suite=None):
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
    result['dirname'] = dirname
    if suite:
        result['suite'] = suite
    if result.bundle:
        result.bundle = normalize_path(result.bundle, result.executable)
    return result


class Suite(list):
    def __init__(self, config, options):
        self.config = config
        self.options = options

    def spec(self, testfile, dirname=None, suite=None):
        self.append(Spec(testfile, self.config,
                         dirname=dirname,
                         suite=suite))

    def find_tests(self, bundledir, filterset=None, test_pattern="test*",
                   dirname=None, suite=None):
        if dirname is None:
            dirname = os.getcwd()
        testpat = self.config.get('tests', test_pattern)
        tests = set(glob.glob(os.path.join(bundledir, testpat)))
        if filterset:
            filterset = [os.path.join(bundledir, f) for f in filterset]
            tests = tests.intersection(set(filterset))
        for test in sorted(tests):
            if os.access(test, os.X_OK):
                self.spec(test, dirname=dirname, suite=suite)

    def find_suites(self):
        """Find and prepend charms tests to our suite of tests"""
        seen_cache = set()
        for spec in self[:]:
            deployment = self.fetch_deployment(spec)
            if not deployment:
                continue
            bundle_key = (spec.bundle, deployment.name)
            if bundle_key in seen_cache:
                continue
            seen_cache.add(bundle_key)
            for charm in self.iterate_charms(deployment):
                charm_suite = Suite(self.config, self.options)
                charm_test_dir = os.path.join(charm.path, 'tests')
                if os.path.exists(charm_test_dir):
                    charm_suite.find_tests(charm_test_dir,
                                           test_pattern="[0-9]*",
                                           dirname=charm.path,
                                           suite=charm.name)

                    logging.debug("Inspecting %s for tests, found %s" % (
                        charm.name,
                        len(charm_suite)))
                    if len(charm_suite):
                        self.insert(0, charm_suite)

    def fetch_deployment(self, spec):
        """Use bundle file to pull relevant charms"""
        bundle = spec.bundle or self.options.bundle
        if not bundle:
            return
        if not os.path.exists(bundle):
            raise OSError("Missing required bundle file: %s" % bundle)
        c = ConfigStack([bundle])
        if not self.options.deployment and len(c.keys()) == 1:
            self.options.deployment = c.keys()[0]
        deployment = c.get(self.options.deployment)

        logging.debug("Fetching Charms from bundle")
        deployment.fetch_charms()
        return deployment

    def iterate_charms(self, deployment):
        """Iterate charms in a juju-deployer.Deployment"""
        for charm in deployment.get_charms():
            # charm having name/path (see deployer.charm)
            yield charm
