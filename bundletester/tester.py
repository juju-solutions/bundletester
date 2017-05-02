import argparse
import logging
import os
from collections import namedtuple
import shutil
import subprocess
import sys
import tempfile
import textwrap

import pkg_resources

from bundletester import (
    reporter,
    runner,
    spec,
    utils,
    fetchers,
)


def get_juju_major_version():
    return int(subprocess.check_output(
        ["juju", "version"]).split(b'.')[0])


def current_environment():
    return subprocess.check_output(['juju', 'switch']).strip()


def validate():
    # Minimally verify we expect we can continue
    subprocess.check_output(['juju', 'version'])


def configure():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-e', '--environment',
        help=('Juju environment or model name. '
              'For Juju 2 models, must be specified with the '
              '<controller>:<model> notation.'))
    parser.add_argument('-t', '--testdir', default=os.getcwd())
    parser.add_argument('-b', '-c', '--bundle',
                        type=str,
                        help=textwrap.dedent("""
                        Specify a bundle ala
                        {path/to/bundle.yaml}. Relative paths will be
                        mapped within the bundle itself for remote
                        bundles. Explicit local paths to bundles
                        currently not supported.
                        """))
    parser.add_argument('-d', '--deployment')

    parser.add_argument('--no-destroy', action="store_true")

    parser.add_argument('-l', '--log-level', dest="log_level",
                        default='INFO')
    parser.add_argument('-o', '--output', dest="output",
                        type=argparse.FileType('w'))
    parser.add_argument('-n', '--dry-run', action="store_true",
                        dest="dryrun")
    parser.add_argument('-r', '--reporter', default="spec",
                        choices=reporter.FACTORY.keys())
    parser.add_argument('-v', '--verbose', action="store_true")

    parser.add_argument('-F', '--allow-failure', dest="failfast",
                        action="store_false")
    parser.add_argument('-s', '--skip-implicit', action="store_true",
                        help="Don't include automatically generated tests")
    parser.add_argument('-x', '--exclude', dest="exclude", action="append")
    parser.add_argument('-y', '--tests-yaml', dest="tests_yaml",
                        help="Path to a tests.yaml file which will "
                        "override the one in the charm or bundle "
                        "being tested.")
    parser.add_argument('--test-pattern', dest="test_pattern")
    parser.add_argument('--version', action="store_true",
                        help="Print the current version")
    parser.add_argument('tests', nargs="*")

    parser.add_argument('--deploy-plan',
                        help='A plan to deploy charm under')
    parser.add_argument('--deploy-budget',
                        help='Deploy budget and allocation limit')
    parser.add_argument('--no-matrix', action="store_true",
                        help="Skip matrix test run, even if juju-matrix is "
                        "in your path.")
    options = parser.parse_args()

    if options.version:
        sys.stdout.write('{}\n'.format(
            pkg_resources.get_distribution("bundletester").version))
        sys.exit()

    if not options.environment:
        options.environment = current_environment()

    options.juju_major_version = get_juju_major_version()

    # Set the environment variable BUNDLE if the bundle argument was provided.
    if options.bundle:
        os.environ['BUNDLE'] = options.bundle
    logging.basicConfig(level=options.log_level.upper())
    return options


def get_return_data(return_code, suite):
    status = namedtuple('status', ['bundle_yaml', 'charm' 'return_code'])
    status.return_code = return_code
    status.bundle_yaml = None
    status.charm = None
    if suite:
        if suite.model.get('bundle'):
            with open(suite.model["bundle"]) as fp:
                status.bundle_yaml = fp.read()
        elif suite.model.get('metadata'):
            status.charm = suite.model.get('metadata')
    return status


def main(options=None):
    options = options or configure()
    validate()

    if not options.output:
        options.output = sys.stdout

    tmpdir = None
    try:
        try:
            fetcher = fetchers.get_fetcher(options.testdir)
            tmpdir = tempfile.mkdtemp(prefix='bundletester-')
            options.fetcher = fetcher
            options.testdir = fetcher.fetch(tmpdir)
        except fetchers.FetchError as e:
            sys.stderr.write("{}\n".format(e))
            return get_return_data(1, None)

        suite = spec.SuiteFactory(options, options.testdir)

        if not suite:
            sys.stderr.write("No Tests Found\n")
            return get_return_data(3, None)

        report = reporter.get_reporter(options.reporter,
                                       options.output,
                                       options)
        report.set_suite(suite)
        run = runner.Runner(suite, options)
        report.header()
        if len(suite):
            with utils.juju_env(
                    options.environment, options.juju_major_version):
                [report.emit(result) for result in run()]
        report.summary()
        return_code = report.exit()
        status = get_return_data(return_code, suite)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)
    return status


def entrypoint():
    status = main()
    sys.exit(status.return_code)


if __name__ == '__main__':
    entrypoint()
