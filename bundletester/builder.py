import subprocess


class Builder(object):
    """Build out the system-level environment needed to run tests"""

    def __init__(self, config):
        self.config = config

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
