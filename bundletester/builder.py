import logging
import os
import subprocess

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
        if self.config.bootstrap:
            ec = subprocess.call(['juju', 'status'],
                                 stdout=open('/dev/null', 'w'),
                                 stderr=subprocess.STDOUT)
            if ec != 0:
                self.environment.bootstrap()
        self.environment.connect()

    def deploy(self, spec):
        if not spec.bundle:
            return
        if not os.path.exists(spec.bundle):
            raise OSError("Missing required bundle file: %s" % spec.bundle)
        if self.options.dryrun:
            return
        subprocess.check_call(['juju-deployer', '-vWc', spec.bundle])

    def destroy(self):
        subprocess.check_call(['juju', 'destroy-environment', self.env_name])

    def reset(self):
        if self.environment and self.config.reset:
            self.environment.reset(terminate_machines=True)

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
