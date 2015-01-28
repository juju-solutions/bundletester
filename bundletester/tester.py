import argparse
import logging
import os
import subprocess
import sys
import tempfile
import textwrap

from bundletester import (
    reporter,
    runner,
    spec,
    utils,
    fetchers,
)


def current_environment():
    return subprocess.check_output(['juju', 'switch']).strip()


def validate():
    # Minimally verify we expect we can continue
    subprocess.check_output(['juju', 'version'])


class BundleSpec(object):
    def __init__(self, path=None, explicit_path=True):
        self.path = path
        self.explicit_path = explicit_path

    @staticmethod
    def validate_path(path):
        if any((path.startswith(x) for x in ('~', '/', '.'))):
            bp = os.path.abspath(os.path.expanduser(path))
            if not os.path.exists(bp):
                raise argparse.\
                    ArgumentTypeError("%s not found on filesystem" % bp)
            return bp, True
        return path, False

    @classmethod
    def parse_cli(cls, spec):
        import pdb;pdb.set_trace()
        if any(spec.endswith(y) for y in ('.yml', '.yaml')):
            candidate = spec
            path, explicit = cls.validate_path(candidate)
            return cls(path, explicit)

        return cls(spec)


def configure():
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', '--environment')
    parser.add_argument('-t', '--testdir', default=os.getcwd())
    parser.add_argument('-b', '-c', '--bundle',
                        type=BundleSpec.parse_cli,
                        default=BundleSpec(),
                        help=textwrap.dedent("""
                        Specify a bundle ala
                        {path/to/bundle.yaml}. Relative paths will be mapped
                        within the bundle itself for remote bundles
                        """))
    parser.add_argument('-d', '--deployment')

    parser.add_argument('--no-destroy', action="store_true")

    parser.add_argument('-l', '--log-level', dest="log_level",
                        default=logging.INFO)
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
    parser.add_argument('--test-pattern', dest="test_pattern")
    parser.add_argument('tests', nargs="*")
    options = parser.parse_args()

    if not options.environment:
        options.environment = current_environment()
    logging.basicConfig(level=options.log_level)
    return options


def main():
    options = configure()
    validate()

    if not options.output:
        options.output = sys.stdout

    try:
        fetcher = fetchers.get_fetcher(options.testdir)
        options.testdir = fetcher.fetch(
            tempfile.mkdtemp(prefix='bundletester-'))
    except fetchers.FetchError as e:
        sys.stderr.write("{}\n".format(e))
        sys.exit(1)

    try:
        suite = spec.SuiteFactory(options, options.testdir)
    except :
        import pdb;pdb.post_mortem(sys.exc_info()[2])

    if not suite:
        sys.stderr.write("No Tests Found\n")
        sys.exit(3)

    report = reporter.get_reporter(options.reporter, options.output, options)
    report.set_suite(suite)
    run = runner.Runner(suite, options)
    report.header()
    if len(suite):
        with utils.juju_env(options.environment):
            [report.emit(result) for result in run()]
    report.summary()
    report.exit()


if __name__ == '__main__':
    main()
