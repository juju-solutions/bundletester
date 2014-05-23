import glob
import os
import subprocess
from distutils.spawn import find_executable

import yaml

from bundletester import (config, models, vcs, utils)


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
        cmd = [testfile]

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
    def __init__(self, model, options, parent_config=None):
        # models.Charm||Bundle -- from SuiteFactory
        # options, argparse options
        self.model = model
        self.options = options
        self._config = None
        self._parent_config = parent_config
        self.directory = model['directory']
        self.testdir = model['testdir']
        self.name = model.get('name')
        self.control = model.get('bundle', model.get('metadata'))

    def __len__(self):
        l = 0
        for s in self:
            if isinstance(s, Suite):
                l += len(s)
            else:
                l += 1
        return l

    @property
    def config(self):
        if not self._config:
            testcfg = None
            if self.testdir:
                testcfg = os.path.join(self.testdir, "tests.yaml")
                if not os.path.exists(testcfg):
                    testcfg = None
            self._config = config.Parser(testcfg, parent=self._parent_config)
        return self._config

    def spec(self, testfile, **kwargs):
        self.append(Spec(testfile, self.config, **kwargs))

    def find_tests(self):
        if not self.testdir:
            return
        testpat = self.options.test_pattern or \
            self.config.get('tests', 'test*')
        tests = set(glob.glob(os.path.join(self.testdir, testpat)))
        if self.options.tests:
            filterset = [os.path.join(self.testdir, f) for f
                         in self.options.tests]
            tests = tests.intersection(set(filterset))
        for test in sorted(tests):
            if os.access(test, os.X_OK | os.R_OK):
                self.spec(test, dirname=self.testdir, suite=self.name)

    def find_suite(self):
        """Find and prepend charms tests to our suite of tests.
        bundle: path to bundle file
        deployment: name of deployment in bundle

        If only one target exists and deployment is not specified it will be
        used automatically when searching for tests.
        """
        if isinstance(self.model, models.Charm):
            if not self.options.skip_implicit:
                self.find_implicit_tests()
            self.find_tests()
        elif isinstance(self.model, models.Bundle):
            deployment = utils.fetch_deployment(self.control,
                                                self.options.deployment)
            for charm in deployment.get_charms():
                model = models.Charm.from_deployer_charm(charm)
                charm_suite = Suite(model, self.options,
                                    parent_config=self.config)
                charm_suite.find_suite()
                if len(charm_suite):
                    self.insert(0, charm_suite)
        else:
            self.find_tests()

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

    def find_implicit_tests(self):
        # Look for implicit targets and map these as tests
        # for charms this can include 'charm proof' from
        # charm tools and for bundles and charms with Makefiles
        # common targets will be attempted.
        # This is a charm suite
        self.spec(['charm-proof'],
                  dirname=self.model['directory'], suite=self.name)
        for target in self.config.makefile:
            self.conditional_make(target, self.model['directory'],
                                  suite=self.name)


def filter_yamls(yamls):
    """Look at a series of *.yaml files to see if they
    might be deployer files. Return the filtered list.
    """
    if not yamls:
        return

    result = []
    for yamlfn in yamls:
        data = yaml.safe_load(open(yamlfn))
        if not isinstance(data, dict):
            continue
        for possible in data.values():
            if isinstance(possible, dict) and 'services' in possible:
                result.append(yamlfn)
                break
    return result


def find_bundle_file(directory):
    pat = os.path.join(directory, "*.yaml")
    yamls = glob.glob(pat)
    yamls = filter_yamls(yamls)
    if not yamls:
        return
    if len(yamls) > 1:
        raise OSError("Ambigious bundle options: %s" % yamls)
    return yamls[0]


def BundleClassifier(directory):
    bundle = find_bundle_file(directory)
    if not bundle:
        return None
    result = {'bundle': bundle,
              'testdir': utils.find_testdir(directory)}
    lp = vcs.Launchpad()
    data = lp.infer_bundle(directory)
    if data:
        result.update(data)
        if 'name' not in data:
            metadata = yaml.safe_load(bundle)
            # XXX: ambigious
            result['name'] = metadata.keys(0)
    return models.Bundle(**result)


def CharmClassifier(directory):
    metadata = os.path.join(directory, "metadata.yaml")
    if not os.path.exists(metadata):
        return None
    lp = vcs.Launchpad()
    data = lp.infer_charm(directory)
    testdir = utils.find_testdir(directory)
    metadata = yaml.safe_load(metadata)
    if data:
        data['metadata'] = metadata
        data['testdir'] = testdir
        if 'name' not in data:
            data['name'] = metadata['name']
    return models.Charm(**data)


def TestDirClassifier(directory):
    if not os.path.exists(directory):
        return None
    return models.TestDir({
        'testdir': directory,
        'name': os.path.basename(directory)
    })


def SuiteFactory(options, directory="."):
    """Return a Suite for a given directory.

    This classifies the dir based on a series of tests.
    """
    for classifier in [BundleClassifier, CharmClassifier, TestDirClassifier]:
        model = classifier(directory)
        if model:
            model['directory'] = directory
            suite = Suite(model, options)
            suite.find_suite()
            return suite
    return None
