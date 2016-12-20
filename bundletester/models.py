import atexit
import os
import shutil
import tempfile

from bundletester import utils


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class FSEntity(dict):
    pass


class Charm(FSEntity):
    @classmethod
    def from_deployer_charm(cls, dcharm):
        """Copy charm source from the deployer cache to a new temp location
        so we can change the charm dir name to match the charm name
        (some tests rely on these matching).

        """
        tmp_dir = tempfile.mkdtemp()
        charm_name = dcharm.name.split('/')[-1]

        # Strip off revision if there is one
        name_parts = charm_name.split('-')
        if is_int(name_parts[-1]):
            charm_name = '-'.join(name_parts[:-1])

        charm_dir = os.path.join(tmp_dir, charm_name)
        shutil.copytree(dcharm.path, charm_dir, symlinks=True)
        atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)

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
