import yaml


class Parser(dict):
    DEFAULT_MAKE_TARGETS = ['lint', 'test']

    def __defaults__(self):
        return {
            'bootstrap': True,
            'reset': True,
            'reset_timeout': 60 * 3,
            'bundle': None,
            'bundle_deploy': True,
            'deployment_timeout': None,
            'virtualenv': False,
            'virtualenv_python': 'python',
            'tests': "*",
            'excludes': [],
            'sources': [],
            'packages': [],
            'python_packages': [],
            'requirements': [],
            'makefile': list(Parser.DEFAULT_MAKE_TARGETS),
            'setup': [],
            'teardown': []
        }

    def __init__(self, path=None, parent=None, **kwargs):
        if not parent:
            parent = self.__defaults__()

        self.merge(parent)
        if kwargs:
            self.merge(kwargs)

        if path:
            data = yaml.safe_load(open(path, 'r').read())
            self.merge(data)

            # Replace the default makefile targets
            if 'makefile' in data:
                self.update(makefile=data['makefile'])

    def __getattr__(self, key):
        return dict.get(self, key)

    def __setattr__(self, k, v):
        self.__setitem__(k, v)

    def __setitem__(self, k, v):
        if k in self and isinstance(self[k], list):
            if isinstance(v, list):
                self[k].extend(v)
            else:
                self[k].append(v)
        else:
            dict.__setitem__(self, k, v)

    def merge(self, other):
        for k, v in other.items():
            self[k] = v
