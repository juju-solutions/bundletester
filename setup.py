from setuptools import setup
import os


version_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            'VERSION'))
with open(version_file) as v:
    VERSION = v.read().strip()


SETUP = {
    'name': "bundletester",
    'packages': ['bundletester'],
    'version': VERSION,
    'author': "Ubuntu Developers",
    'author_email': "ubuntu-devel-discuss@lists.ubuntu.com",
    'url': "https://code.launchpad.net/charm-helpers",
    'license': "Affero GNU Public License v3",
    'long_description': open('README.md').read(),
}


if __name__ == '__main__':
    setup(**SETUP)
