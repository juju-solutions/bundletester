import datetime
import logging
import os
import subprocess

log = logging.getLogger('runner')


def find(filenames, basefile):
    """Normalize files relative to basefile turning
    partial names into files in the same dir as basefile
    """
    dirname = os.path.dirname(basefile)
    return [os.path.abspath(os.path.join(dirname, f)) for f in filenames]


class Runner(object):
    def __init__(self, suite, builder, options=None):
        self.suite = suite
        self.builder = builder
        self.options = options

    def _run(self, executable):
        # we use shell=True here to mask
        # OSError if #!/bin/interp isn't used
        # in scripts
        log.debug("call %s" % executable)
        p = subprocess.Popen(executable,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        retcode = p.wait()
        output = p.stdout.read()
        log.debug(output)
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
            if ec != 0:
                result['exit'] = canidate
                break

        end = datetime.datetime.utcnow()
        duration = end - start
        result['returncode'] = ec
        result['output'] = output
        result['start'] = start.isoformat()
        result['end'] = end.isoformat()
        result['duration'] = duration.total_seconds()
        return result

    def __call__(self):
        self.builder.bootstrap()
        for spec in self.suite:
            result = {}
            try:
                self.builder.deploy(spec)
                result.update(self.run(spec, 'setup'))
                if result.get('returncode', None) == 0:
                    result.update(self.run(spec))
            except subprocess.CalledProcessError, e:
                result['returncode'] = e.returncode
                result['output'] = e.output
                result['test'] = 'bundle.deploy'
                result['executable'] = e.cmd
                break
            finally:
                result.update(self.run(spec, 'teardown'))
                self.builder.reset()
                yield result
                if self.options and self.options.failfast:
                    break
