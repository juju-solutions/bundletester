from bundletester import utils


class FSEntity(dict):
    pass


class Charm(FSEntity):
    @classmethod
    def from_deployer_charm(cls, dcharm):
        c = cls()
        c['name'] = dcharm.name
        c['directory'] = dcharm.path
        c['testdir'] = utils.find_testdir(dcharm.path)

        return c


class Bundle(FSEntity):
    pass


class TestDir(FSEntity):
    """A directory containing tests."""
    pass
