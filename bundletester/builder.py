import os
import subprocess
from deployer.env.go import GoEnvironment


class Builder(object):
    """Build out the system-level environment needed to run tests"""

    def __init__(self, config, environment_name=None):
        self.config = config
        self.env_name = environment_name
        self.environment = None
        if self.env_name:
            self.environment = GoEnvironment(self.env_name)

    def bootstrap(self):
        if not self.environment:
            return
        if self.config.bootstrap:
            ec = subprocess.call(['juju', 'status'],
                                 stdout=open('/dev/null', 'w'),
                                 stderr=subprocess.STDOUT)
            if ec != 0:
                self.environment.bootstrap()
        self.environment.connect()

    def deploy(self, spec):
        if spec.bundle or not os.path.exists(spec.bundle):
            return
        # TODO: use API here
        subprocess.check_call(['juju-deployer', '-vW', self.config.bundle])

    def destroy(self):
        subprocess.check_call(['juju', 'destroy-environment', self.env_name])

    def reset(self):
        if self.environment and self.config.reset:
            self.environment.reset()

    def build_virtualenv(self, path):
        subprocess.check_call(['virtualenv', path])

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
