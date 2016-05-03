import os
from setuptools import setup, find_packages

this_dir = os.path.abspath(os.path.dirname(__file__))
reqs_file = os.path.join(this_dir, 'requirements.txt')
with open(reqs_file) as f:
    reqs = [line for line in f.read().splitlines()
            if not line.startswith('--')]

SETUP = {
    'name': "bundletester",
    'packages': find_packages(),
    'version': "0.6.0",
    'author': "Juju Developers",
    'author_email': "juju@lists.ubuntu.com",
    'url': "https://github.com/juju-solutions/bundletester",
    'license': "Affero GNU Public License v3",
    'long_description': open('README.md').read(),
    'description': 'A juju charm and bundle test runner',
    'entry_points': {
        'console_scripts': [
            'bundletester = bundletester.tester:entrypoint',
            'bundlewatcher = bundletester.watcher:main'
        ]
    },
    'install_requires': reqs,
}


if __name__ == '__main__':
    setup(**SETUP)
