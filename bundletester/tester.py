import argparse
import os
from bundletester import (config, builder, spec,
                          runner, reporter)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dot', action="store_true")
    parser.add_argument('tests', nargs="*")
    options = parser.parse_args()

    bundledir = os.getcwd()
    cfg = os.path.join(bundledir, 'tests.yaml')
    if not os.path.exists(cfg):
        cfg = None
    testcfg = config.Parser(cfg)
    env = builder.Builder(testcfg)

    if testcfg.virtualenv:
        vpath = os.path.join(bundledir, '.venv')
        env.build_virtualenv(vpath)
        apath = os.path.join(vpath, 'bin/activate_this.py')
        execfile(apath, dict(__file__=apath))

    env.add_sources(testcfg.sources)
    env.install_packages()

    suite = spec.Suite(testcfg)
    suite.find_tests(bundledir, options.tests)

    run = runner.Runner(suite, options)
    if options.dot:
        report = reporter.DotReporter()
    else:
        report = reporter.JSONReporter()

    for result in run():
        report.emit(result)
    report.summary()
    report.exit()


if __name__ == '__main__':
    main()
