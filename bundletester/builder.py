import logging
import os
import subprocess
import time

import websocket
from deployer.env.go import GoEnvironment


class Builder(object):
    """Build out the system-level environment needed to run tests"""

    def __init__(self, config, options):
        self.config = config
        self.options = options
        self.environment = None
        self.env_name = None
        if options:
            self.env_name = options.environment
            if self.env_name:
                self.environment = GoEnvironment(self.env_name)

    def bootstrap(self):
        if not self.environment:
            return
        logging.debug("Bootstrap environment: %s" % self.env_name)
        if self.options.dryrun:
            return
        ec = subprocess.call(['juju', 'status', '-e', self.env_name],
                             stdout=open('/dev/null', 'w'),
                             stderr=subprocess.STDOUT)

        if ec != 0:
            if self.config.bootstrap is True:
                logging.info("Bootstrapping Juju Environment...")
                self.environment.bootstrap()
                self.environment.connect()
                return True
        else:
            self.environment.connect()

    def deploy(self, bundle):
        result = {
            'returncode': 0
        }
        bundle = bundle or self.options.bundle
        if not bundle:
            return result
        if not os.path.exists(bundle):
            raise OSError("Missing required bundle file: %s" % bundle)
        if self.options.dryrun:
            return result
        cmd = ['juju-deployer']
        if self.options.verbose:
            cmd.append('-Wvd')
        cmd += ['-c', bundle]
        if self.options.deployment:
            cmd.append(self.options.deployment)

        logging.debug("deploy %s", ' '.join(cmd))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

        # Print all output as it comes in to debug
        output = []
        lines = iter(p.stdout.readline, "")
        for line in lines:
            output.append(line)
            logging.debug(str(line.rstrip()))

        p.communicate()
        return {
            'returncode': p.returncode,
            'output': ''.join(output),
            'executable': cmd
        }

    def destroy(self):
        if self.options.no_destroy is not True:
            subprocess.check_call(['juju', 'destroy-environment',
                                   '-y', self.env_name, '--force'])

    def reset(self):
        if self.options.dryrun:
            return
        if self.environment:
            start, timeout = time.time(), 60
            while True:
                try:
                    self.environment.reset(
                        terminate_machines=True,
                        terminate_delay=60,
                        force_terminate=True
                    )
                    break
                except Exception as e:
                    logging.exception(e)

                    if isinstance(
                            e, websocket.WebSocketConnectionClosedException):
                        logging.debug('Reconnectinng to environment...')
                        self.environment.connect()
                        continue

                    if (time.time() - start) > timeout:
                        raise RuntimeError(
                            'Timeout exceeded. Failed to reset environment '
                            ' in %s seconds.' % timeout)
                    time.sleep(1)
                    logging.debug('Retrying environment reset...')

            # wait for all services to be removed
            logging.debug("Waiting for services to be removed...")
            start, timeout = time.time(), 60
            while True:
                status = self.environment.status()
                if not status.get('services', {}):
                    break
                if (time.time() - start) > timeout:
                    raise RuntimeError(
                        'Timeout exceeded. Failed to destroy all services '
                        ' in %s seconds.' % timeout)
                logging.debug(
                    " Remaining services: %s", status.get("services").keys())
                time.sleep(4)

    def build_virtualenv(self, path):
        subprocess.check_call(['virtualenv', path],
                              stdout=open('/dev/null', 'w'))

    def add_source(self, source):
        subprocess.check_call(['sudo', 'apt-add-repository', '--yes', source])

    def add_sources(self, update=True):
        for source in self.config.sources:
            self.add_source(source)
        if self.config.sources and update:
            self.apt_update()

    def apt_update(self):
        subprocess.check_call(['sudo', 'apt-get', 'update', '-qq'])

    def install_packages(self):
        if not self.config.packages:
            return
        cmd = ['sudo', 'apt-get', 'install', '-qq', '-y']
        cmd.extend(self.config.packages)
        subprocess.check_call(cmd)
