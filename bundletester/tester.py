import argparse
import logging
import os
import subprocess
from bundletester import (config, builder, spec,
                          runner, reporter)


def current_environment():
    return subprocess.check_output(['juju', 'switch']).strip()



def validate():
    # Minimally verify we expect we can continue
    subprocess.check_output(['juju', 'version'])


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', '--environment')
    parser.add_argument('-l', '--log-level', dest="log_level",
                        default=logging.INFO)
    parser.add_argument('--dot', action="store_true")
    parser.add_argument('--testdir')
    parser.add_argument('tests', nargs="*")
    options = parser.parse_args()

    if not options.environment:
        options.environment = current_environment()
    logging.basicConfig(level=options.log_level)

    validate()

    def find_test_dir(testdir):
        if not testdir:
            if os.path.exists('tests'):
                testdir = os.path.abspath('tests')
            elif os.path.basename(os.getcwd()) == 'tests':
                testdir = os.path.abspath(os.getcwd())
                if not testdir or not os.path.exists(testdir):
                    raise OSError("Cannot find tests location")
        return testdir

    testdir = find_test_dir(options.testdir)

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

    if options.dot:
        report = reporter.DotReporter()
    else:
        report = reporter.JSONReporter()

    suite = spec.Suite(testcfg)
    suite.find_tests(testdir, options.tests)
    if not len(suite):
        report.summary()
        report.exit()

    run = runner.Runner(suite, env, options)
    for result in run():
        report.emit(result)
    report.summary()
    report.exit()


if __name__ == '__main__':
    main()
