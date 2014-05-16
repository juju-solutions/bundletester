import datetime
import logging
import os
import subprocess

from bundletester.spec import Suite

log = logging.getLogger('runner')


def find(filenames, basefile):
    """Normalize files relative to basefile turning
    partial names into files in the same dir as basefile
    """
    if isinstance(basefile, list):
        basefile = basefile[0]
    dirname = os.path.dirname(basefile)
    for f in filenames:
        if isinstance(f, list):
            f = f[0]
            yield os.path.abspath(os.path.join(dirname, f))


class Runner(object):
    def __init__(self, suite, builder, options=None):
        self.suite = suite
        self.builder = builder
        self.options = options

    def _run(self, executable):
        log.debug("call %s" % executable)
        if self.options.dryrun:
            return 0, ""

        p = subprocess.Popen(executable,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        retcode = p.wait()
        output = p.stdout.read()
        log.debug("OUTPUT\n%s" % output)
        log.debug("Exit Code: %s" % retcode)
        return retcode, output

    def run(self, spec, phase=None):
        """Run a phase of spec.

        If no phase is provided spec's main test will execute.
        """
        result = {
            'test': spec.name,
            'returncode': 0
        }

        if phase == "setup":
            canidates = find(spec.setup, spec.executable)
        elif phase == "teardown":
            canidates = find(reversed(spec.teardown), spec.executable)
        else:
            canidates = [spec.executable]

        if not canidates:
            return result
        start = datetime.datetime.utcnow()
        for canidate in canidates:
            ec, output = self._run(canidate)
            result['returncode'] = ec
            result['output'] = output
            result['executable'] = spec.executable
            if ec != 0:
                if isinstance(canidate, list):
                    canidate = " ".join(canidate)
                result['exit'] = canidate
                break

        end = datetime.datetime.utcnow()
        duration = end - start
        result['duration'] = duration.total_seconds()
        if result['duration'] < 0.1:
            result['duration'] = 0.0
        return result

    def _handle_result(self, result):
        stop = False
        if self.options and self.options.failfast and \
                result.get('returncode', 1) != 0:
            log.debug('Failfast from %s' % result['test'])
            stop = True
        return result, stop

    def __call__(self):
        bootstrapped = False
        for element in self.suite:
            if isinstance(element, Suite):
                for result in self._run_suite(element):
                    result, stop = self._handle_result(result)
                    yield result
                    if stop:
                        raise StopIteration
            else:
                if not bootstrapped and element.bundle:
                    self.builder.bootstrap()
                    bootstrapped = True
                result, stop = self._handle_result(self._run_test(element))
                yield result
                if stop:
                    raise StopIteration

    def _run_suite(self, suite):
        for spec in suite:
            yield self._run_test(spec)

    def _run_test(self, spec):
        result = {}
        cwd = os.getcwd()
        try:
            if spec.bundle:
                deployed = self.builder.deploy(spec)
                if deployed is not True:
                    result.update(deployed)
                    result['returncode'] = 2
                    result['test'] = 'juju-deployer'
                    result['suite'] = 'bundletester'
                    result['exit'] = result['executable']

            if result.get('returncode') is None:
                basedir = spec.get('dirname')
                if basedir:
                    result['dirname'] = basedir
                    os.chdir(basedir)
                result.update(self.run(spec, 'setup'))
                if result.get('returncode', None) == 0:
                    result.update(self.run(spec))
        except subprocess.CalledProcessError, e:
            result['returncode'] = e.returncode
            result['output'] = e.output
            result['executable'] = e.cmd
        finally:
            os.chdir(cwd)
            td = self.run(spec, 'teardown')
            if td.get('returncode') != 0:
                log.error('Failed to teardown test %s' % spec)
                # Only in the event of td failure do we update result
                # otherwise a successful teardown could overwrite
                # the failure code of a main phase test
                result.update(td)
            self.builder.reset()
            result['suite'] = spec.get('suite')
            return result
