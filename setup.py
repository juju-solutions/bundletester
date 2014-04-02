from setuptools import setup, find_packages
import os


SETUP = {
    'name': "bundletester",
    'packages': find_packages(),
    'version': "0.3.3",
    'author': "Ubuntu Developers",
    'author_email': "ubuntu-devel-discuss@lists.ubuntu.com",
    'url': "https://code.launchpad.net/charm-helpers",
    'license': "Affero GNU Public License v3",
    'long_description': open('README.md').read(),
    'entry_points': {
        'console_scripts': [
            'bundletester = bundletester.tester:main',
            'bundlewatcher = bundletester.watcher:main'
        ]
    }
}


if __name__ == '__main__':
    setup(**SETUP)
