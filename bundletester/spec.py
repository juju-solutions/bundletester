import glob
import logging
import os
import subprocess
from distutils.spawn import find_executable

from deployer.config import ConfigStack

from bundletester import config


def normalize_path(path, relto):
    dirname = os.path.dirname(relto)
    if not os.path.isabs(path):
        path = os.path.join(dirname, path)
    return path


def Spec(cmd, parent=None, dirname=None, suite=None, name=None):
    testfile = cmd
    if isinstance(cmd, list):
        testfile = find_executable(cmd[0])
        cmd[0] = testfile
    else:
        testfile = os.path.abspath(testfile)

    if not os.path.exists(testfile) or \
            not os.access(testfile, os.X_OK | os.R_OK):
        raise OSError('Expected executable test file: %s' % testfile)

    base, ext = os.path.splitext(testfile)
    control_file = "%s.yaml" % base
    if not os.path.exists(control_file):
        control_file = None
    result = config.Parser(path=control_file, parent=parent)
    result['name'] = name or os.path.basename(testfile)
    result['executable'] = cmd
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

    def __len__(self):
        l = 0
        for s in self:
            if isinstance(s, Suite):
                l += len(s)
            else:
                l += 1
        return l

    def spec(self, testfile, **kwargs):
        self.append(Spec(testfile, self.config, **kwargs))

    def find_tests(self, bundledir, filterset=None,
                   test_pattern=None,
                   dirname=None, suite=None):
        if dirname is None:
            dirname = os.getcwd()
        testpat = test_pattern or \
            self.options.test_pattern or \
            self.config.get('tests', 'test*')
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
                    if not self.options.skip_implicit:
                        charm_suite.find_implicit_tests(charm.path,
                                                        dirname=charm.path,
                                                        suite=charm.name)
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

    def conditional_make(self, target, entitydir, suite=None):
        cwd = os.getcwd()
        os.chdir(entitydir)
        p = subprocess.Popen(['make', '-ns', target],
                             stdout=open('/dev/null', 'w'),
                             stderr=subprocess.STDOUT)
        ec = p.wait()
        if ec == 0:
            # The makefile target exists, add the spec
            self.spec(['make', '-s', target],
                      name="make %s" % target,
                      dirname=entitydir,
                      suite=suite)
        os.chdir(cwd)

    def find_implicit_tests(self, entitydir, dirname=None, suite=None):
        # Look for implicit targets and map these as tests
        # for charms this can include 'charm proof' from
        # charm tools and for bundles and charms with Makefiles
        # common targets will be attempted.
        if suite:
            # This is a charm suite
            self.spec(['charm-proof'],
                      dirname=dirname, suite=suite)
            for target in self.config.makefile:
                self.conditional_make(target, entitydir,
                                      suite=suite)

    def iterate_charms(self, deployment):
        """Iterate charms in a juju-deployer.Deployment"""
        for charm in deployment.get_charms():
            # charm having name/path (see deployer.charm)
            yield charm
