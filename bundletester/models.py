import atexit
import os
import shutil
import tempfile

from bundletester import utils


class FSEntity(dict):
    pass


class Charm(FSEntity):
    @classmethod
    def from_deployer_charm(cls, dcharm):
        # Copy charm source from the deployer cache to a new temp location
        # so we can change the charm dir name to match the charm name
        # (some tests rely on these matching).
        tmp_dir = tempfile.mkdtemp()
        charm_dir = os.path.join(tmp_dir, dcharm.name)
        shutil.copytree(dcharm.path, charm_dir, symlinks=True)
        atexit.register(shutil.rmtree, tmp_dir)

        c = cls()
        c['name'] = dcharm.name
        c['directory'] = charm_dir
        c['testdir'] = utils.find_testdir(charm_dir)

        return c


class Bundle(FSEntity):
    pass


class TestDir(FSEntity):
    """A directory containing tests."""
    pass
