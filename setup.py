from setuptools import setup, find_packages

SETUP = {
    'name': "bundletester",
    'packages': find_packages(),
    'version': "0.3.5",
    'author': "Juju Developers",
    'author_email': "juju@lists.ubuntu.com",
    'url': "https://github.com/juju-solutions/bundletester",
    'license': "Affero GNU Public License v3",
    'long_description': open('README.md').read(),
    'entry_points': {
        'console_scripts': [
            'bundletester = bundletester.tester:main',
            'bundlewatcher = bundletester.watcher:main'
        ]
    },
}


if __name__ == '__main__':
    import subprocess
    cmd = 'pip install -r requirements.txt'
    subprocess.call(cmd.split())
    setup(**SETUP)
