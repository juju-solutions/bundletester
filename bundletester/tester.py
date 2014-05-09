import argparse
import logging
import glob
import os
import subprocess
import sys

import yaml

from bundletester import (config, builder, spec,
                          runner, reporter)


def current_environment():
    return subprocess.check_output(['juju', 'switch']).strip()


def validate():
    # Minimally verify we expect we can continue
    subprocess.check_output(['juju', 'version'])


def configure():
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', '--environment')
    parser.add_argument('-b', '--bundle')
    parser.add_argument('-d', '--deployment')

    parser.add_argument('-l', '--log-level', dest="log_level",
                        default=logging.INFO)
    parser.add_argument('-o', '--output', dest="output",
                        type=argparse.FileType('w'))
    parser.add_argument('-n', '--dry-run', action="store_true",
                        dest="dryrun")
    parser.add_argument('-r', '--reporter', default="spec",
                        choices=reporter.FACTORY.keys())
    parser.add_argument('-v', '--verbose', action="store_true")

    parser.add_argument('-f', '--failfast', action="store_true")
    parser.add_argument('-s', '--skip-implicit', action="store_true",
                        help="Don't include automatically generated tests")
    parser.add_argument('--test-pattern', dest="test_pattern")
    parser.add_argument('-t', '--testdir', default='tests')
    parser.add_argument('tests', nargs="*")
    options = parser.parse_args()

    if not options.environment:
        options.environment = current_environment()
    logging.basicConfig(level=options.log_level)
    return options


def find_testdir(testdir):
    if not testdir:
        if os.path.exists('tests'):
            testdir = os.path.abspath('tests')
        elif os.path.basename(os.getcwd()) == 'tests':
            testdir = os.path.abspath(os.getcwd())
            if not testdir or not os.path.exists(testdir):
                raise OSError("Cannot find tests location")
    return testdir


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
    return result


def find_bundle(testdir=None):
    pat = os.path.join(testdir or os.getcwd(), "*.yaml")
    yamls = glob.glob(pat)
    yamls = filter_yamls(yamls)
    if not yamls:
        return
    if len(yamls) > 1:
        raise OSError("Ambigious bundle options: %s" % yamls)
    return yamls[0]


def main():
    options = configure()
    validate()

    testdir = find_testdir(options.testdir)
    cfg = os.path.join(testdir, 'tests.yaml')
    if not os.path.exists(cfg):
        cfg = None
    testcfg = config.Parser(cfg)

    if not options.bundle:
        options.bundle = find_bundle(testdir)

    deployment_name = None
    if options.bundle:
        deployment_name = os.path.splitext(
            os.path.basename(options.bundle))[0]

    build = builder.Builder(testcfg, options)

    # if we are already in a venv we will assume we
    # can use that
    if testcfg.virtualenv and not os.environ.get("VIRTUAL_ENV"):
        vpath = os.path.join(testdir, '.venv')
        build.build_virtualenv(vpath)
        apath = os.path.join(vpath, 'bin/activate_this.py')
        execfile(apath, dict(__file__=apath))

    build.add_sources(testcfg.sources)
    build.install_packages()

    if not options.output:
        options.output = sys.stdout

    report = reporter.get_reporter(options.reporter, options.output, options)
    suite = spec.Suite(testcfg, options)
    suite.find_tests(testdir, options.tests, suite=deployment_name)
    suite.find_suites()
    report.set_suite(suite)
    run = runner.Runner(suite, build, options)
    report.header()
    if len(suite):
        [report.emit(result) for result in run()]
    report.summary()
    report.exit()


if __name__ == '__main__':
    main()
