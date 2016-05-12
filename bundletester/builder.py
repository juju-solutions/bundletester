import logging
import subprocess
import sys
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
        cmd = ['juju', 'status']
        if self.options.juju_major_version == 1:
            cmd.append('-e')
        else:
            cmd.append('-m')
        cmd.append(self.env_name)

        ec = subprocess.call(cmd,
                             stdout=open('/dev/null', 'w'),
                             stderr=subprocess.STDOUT)

        if ec != 0:
            if self.config.bootstrap is True:
                if self.options.juju_major_version == 1:
                    logging.info("Bootstrapping Juju Environment...")
                    self.environment.bootstrap()
                    self.environment.connect()
                    return True
                else:
                    sys.exit(
                        "Bootstrapping a Juju {} controller is not supported. "
                        "Please bootstrap before running bundletester.".format(
                            self.options.juju_major_version))
        else:
            self.environment.connect()

    def deploy(self, cmd):
        result = {
            'returncode': 0
        }
        if self.options.dryrun:
            return result

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
        if self.options.no_destroy:
            return

        if self.options.juju_major_version == 1:
            subprocess.check_call(['juju', 'destroy-environment',
                                   '-y', self.env_name, '--force'])
        else:
            # We could call 'destroy-model' here instead, but since
            # bundletester won't create a new one for you, I think
            # it makes more sense to just reset the model instead,
            # at least for now.
            self.reset()

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
        subprocess.check_call(
            ['virtualenv', '-p', self.config.virtualenv_python, path],
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
        if self.config.packages:
            cmd = ['sudo', 'apt-get', 'install', '-qq', '-y']
            cmd.extend(set(self.config.packages))
            if (self.config.python_packages and
                    subprocess.call(['which', 'pip']) != 0):
                cmd.extend('python-pip')
            subprocess.check_call(cmd)

        if self.config.python_packages:
            cmd = ['sudo'] if not self.config.virtualenv else []
            cmd.extend(['pip', 'install', '-U'])
            cmd.extend(set(self.config.python_packages))
            subprocess.check_call(cmd)
