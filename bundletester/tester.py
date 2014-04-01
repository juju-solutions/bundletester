import argparse
import logging
import os
import signal
import subprocess
import sys

from bundletester import (config, builder, spec,
                          runner, reporter)


class timeout:
    # This pattern conflicts with jujuclient which uses
    # its own handler on sigalrm
    DEFAULT_TIMEOUT = 45 * 60

    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise OSError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


def current_environment():
    return subprocess.check_output(['juju', 'switch']).strip()


def validate():
    # Minimally verify we expect we can continue
    subprocess.check_output(['juju', 'version'])


def configure():
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', '--environment')
    parser.add_argument('-f', '--failfast', action="store_true")
    parser.add_argument('-l', '--log-level', dest="log_level",
                        default=logging.INFO)
    parser.add_argument('-o', '--output', dest="output")
    parser.add_argument('--dot', action="store_true")
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('--timeout', type=int, default=timeout.DEFAULT_TIMEOUT)
    parser.add_argument('--testdir')
    parser.add_argument('tests', nargs="*")
    options = parser.parse_args()

    if not options.environment:
        options.environment = current_environment()
    logging.basicConfig(level=options.log_level)
    return options


def find_dir(testdir):
    if not testdir:
        if os.path.exists('tests'):
            testdir = os.path.abspath('tests')
        elif os.path.basename(os.getcwd()) == 'tests':
            testdir = os.path.abspath(os.getcwd())
            if not testdir or not os.path.exists(testdir):
                raise OSError("Cannot find tests location")
    return testdir


def main():
    options = configure()
    validate()

    testdir = find_dir(options.testdir)
    cfg = os.path.join(testdir, 'tests.yaml')
    if not os.path.exists(cfg):
        cfg = None
    testcfg = config.Parser(cfg)
    env = builder.Builder(testcfg, options.environment)

    if testcfg.virtualenv:
        vpath = os.path.join(testdir, '.venv')
        env.build_virtualenv(vpath)
        apath = os.path.join(vpath, 'bin/activate_this.py')
        execfile(apath, dict(__file__=apath))

    env.add_sources(testcfg.sources)
    env.install_packages()

    if isinstance(options.output, str):
        fp = open(options.output, 'w')
    else:
        fp = sys.stdout
    if options.dot:
        report = reporter.DotReporter(fp, options)
    else:
        report = reporter.JSONReporter(fp, options)

    suite = spec.Suite(testcfg)
    suite.find_tests(testdir, options.tests)
    if not len(suite):
        report.header()
        report.summary()
        report.exit()

    run = runner.Runner(suite, env, options)
    report.header()
    ## Timeout conflicted with handler in jujuclient
    ## with timeout(options.timeout):
    [report.emit(result) for result in run()]
    report.summary()
    report.exit()


if __name__ == '__main__':
    main()
