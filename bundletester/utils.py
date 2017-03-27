from contextlib import contextmanager
import logging
import os

from deployer.config import ConfigStack

log = logging.getLogger(__name__)


def fetch_deployment(bundle_yaml, deployment=None):
    """Use bundle file to pull relevant charms"""
    if not bundle_yaml or not os.path.exists(bundle_yaml):
        raise OSError("Missing required bundle file: %s" % bundle_yaml)
    c = ConfigStack([bundle_yaml])
    if not deployment and len(c.keys()) == 1:
        deployment = c.get(c.keys()[0])
    elif deployment:
        deployment = c.get(deployment)
    else:
        raise KeyError("Ambigious Deployment, None specified")
    deployment.fetch_charms()  # update=True)
    return deployment


def find_testdir(directory):
    testdir = os.path.join(directory, 'tests')
    if os.path.exists(testdir):
        return os.path.abspath(testdir)
    return None


@contextmanager
def juju_env(env, juju_major_version):
    juju_model = 'JUJU_MODEL'
    if juju_major_version == 1:
        juju_model = 'JUJU_ENV'
    orig_env = os.environ.get(juju_model, '')
    if env != orig_env:
        log.debug('Updating %s: "%s" -> "%s"', juju_model, orig_env, env)
        os.environ[juju_model] = env
    try:
        yield
    finally:
        if env != orig_env:
            log.debug('Updating %s: "%s" -> "%s"', juju_model, env, orig_env)
            os.environ[juju_model] = orig_env
