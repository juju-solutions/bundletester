# BundleTester

A juju-deployer based test runner for bundles and charms.

# Installation

    pip2 install bundletester

# Introduction

This is designed around the fail fast principle. Each bundle is composed of
charms, each of those charms should have tests ranging from unit tests to
integration tests. The bundle itself will have integration tests. Those tests
should run from least expensive to most expensive in terms of time, failing as soon as
possible. The theory is that if tests fail in the charms, the bundle cannot
function. Bundletester will therefore pull all the charms and look for any
tests it can find and run those prior running its own integration tests.

This test runner uses the following pattern. A bundle has a URL. The runner can
be run directly from within a bundle checkout or will pull the branch to which
the bundle url refers. From there it will attempt to look for a 'tests'
directory off the project root. Using the rules described below it will find
and execute each test within that directory and produce a report.

This also includes a bundlewatcher script which can be used as a Jenkins script
trigger.

# Example Usage

From within the top level of a bundle or charm:

    bundletester -r json -o result.json

Using a specific bundle or charm directory:

    bundletester -t ~/charms/trusty/mycharm -l DEBUG

Passing -l/--log-level DEBUG will give additional insight into what steps
bundletester is taking.

## Remote Sources

`bundletester` can fetch and run tests from remote locations:

    bundletester -t cs:trusty/wordpress

The `-t` option accepts a variety of URL types:

### Charm Store

    -t cs:wordpress
    -t cs:precise/wordpress
    -t bundle:mediawiki-single
    -t bundle:mediawiki-single-8
    -t bundle:~charmers/mediawiki-single
    -t bundle:~charmers/mediawiki-single-8

### Launchpad

    -t lp:~charmers/charms/precise/ghost/trunk
    -t launchpad:~charmers/charms/precise/ghost/trunk
    -t https://launchpad.net/~charmers/charms/precise/ghost/trunk

    # Add '@revision' to any Launchpad URL to test a specific revision
    -t lp:~charmers/charms/precise/ghost/trunk@4

    # Test charm or bundle merge proposal
    -t lp:~davidpbritton/charms/precise/apache2/avoid-regen-cert/+merge/221102

### Github

    -t gh:charms/apache2
    -t github:charms/apache2
    -t https://github.com/charms/apache2

    # Add '@revision' to any Github URL to test a specific revision
    -t https://github.com/charms/apache2@52e73d

### Bitbucket

    # For Bitbucket, repos that don't end in '.git' are assumed to be Hg
    -t bb:battlemidget/juju-apache-gunicorn-django.git
    -t bitbucket:battlemidget/juju-apache-gunicorn-django.git
    -t https://bitbucket.org/battlemidget/juju-apache-gunicorn-django.git

    # Add '@revision' to any Bitbucket URL to test a specific revision
    -t bb:battlemidget/juju-apache-gunicorn-django.git@daff5d9

# Test Directory

The driver file `tests/tests.yaml` is used (by default) to control the overall
flow of how tests work. All values in this file (and indeed the file itself) are
optional. When not provided, defaults will be used.

You can override the `tests/tests.yaml` file in a charm or bundle by
using the `-y` argument to bundletester, e.g.:

    bundletester -t cs:meteor -y /path/to/custom/tests.yaml

## tests.yaml

A sample `tests.yaml` file::

    bootstrap: false
    reset: false
    virtualenv: true
    virtualenv_python: python3
    tests: "[0-9]*"
    excludes:
      - `charm-name`
    sources:
      - ppa:ubuntu-lxc/lxd-stable
    packages:
      - lxd
    python_packages:
      - bzr
      - juju-deployer
      - amulet
      - requests
    requirements:
      - test-requirements.txt
      - requirements.txt
    makefile:
      - lint
      - test
    setup: `filename`
    teardown: `filename`
    bundle_deploy: false
    deployment_timeout: 2700

Explanation of keys:

**bootstrap**: Bootstrap the environment if necessary (default: true).

**reset**: Use juju-deployer to reset the model between each test file execution (default: true).

**reset_timeout**: Max time (in seconds) allowed for each of two routines in a model reset:  machine termination, and application removal.  Total wait time can be 2X this value.  This option has no effect if `reset` has any value other than `true` (default: 180).

**virtualenv**: Create and activate a virtualenv in which all tests are run (default: false).

**virtualenv_python**: The version of python with which to create the
virtualenv (if `virtualenv` is `true'). Examples: python, python2.7,
python3.5 (default: python).

**tests**: A glob pattern of executable files in the `tests/` directory to treat as tests (default: "\*"). Only files that match this pattern will be executed.

**excludes**: List of charm names for which tests should be skipped. Useful if executing against a bundle.

**sources**: List of apt package sources to add before installing packages.

**packages**: List of packages to install with apt before running tests.

**python_packages**: List of python packages to install with `pip install -U` before running tests. If `virtualenv` is `true`, the packages will be installed in the virtualenv.

**requirements**: List of pip requirements file names (relative to the
charm or bundle root dir), which will be
passed to `pip install -r`. If `virtualenv` is true, the packages will
be installed in the virtualenv, otherwise they will be installed at the
system level.  (default: [])

**makefile**: List of make targets to execute (default: [lint, test]).

**setup**: Optional name of a script in the `tests/` directory to run before each test.

**teardown**: Optional name of script in the `tests/` directory to run after each test.

**bundle_deploy**: Only applies when testing a bundle. Acceptable values are `true`, `false`, or a file name. If `true` (the default), the bundle will be deployed by juju-deployer before any tests are run. If `false`, the deployment step will be skipped. If a filename is given, it should be an executable file in the `tests/` directory (likely an amulet script). The file will be executed as the deployment step. Useful if you want to deploy the bundle, but need to modify it first. Note that if the `bundle_deploy` filename matches the `tests` glob pattern, it will be executed twice - once in the deploy step, and once as a test. To prevent this, use a `tests` glob pattern that doesn't match the `bundle_deploy` file name.

**deployment_timeout**: Max time (in seconds) allowed for the initial bundle
deploy (before any tests are run).  This option has no effect if `bundle_deploy`
has any value other than `true` (default: 2700).




## Finding Tests

When tests.yaml's test pattern is executed it will yield a test which should be run. Each
of these test files can optionally have a control file of the same name but with a `.yaml`
extension. If present, this file has a similar layout to tests.yaml.

A sample `01-test.yaml` file::

    bundle: bundle.yaml
    setup: script
    teardown: script

Explanation of keys:

bundle: A bundle file name, relative to the tests directory. If bundle isn't
specified <BUNDLE_ROOT>/bundle.yaml will be used by default.

setup: An optional script to be run before this test. This is called after the
tests.yaml setup, if present.

teardown: An optional script to be run after this test. This is called before the
tests.yaml teardown, if present.

## Setup/Teardown

If these scripts fail with a non-zero exit code, the test will be recorded as a
failure with that exit code.

## Test Execution

Each test should be executable. If `virtualenv` is true, each test will be
executed with that environment activated.

Each test will have its stdout and stderr captured.

Each test's exit code will be captured. A non-zero return indicates failure.

## Reporting Results

Any test failures will result in a non-zero exit code.

Using -r json a JSON string will be printed on stdout. This string will
contain, at minimum, the following structure (additional keys are possible):

    [{test result}, ...]

each test result is a dict with at least:

    {'test': test file, result: exit_code,
      'exit': 'script name which returned exit code',
      'returncode': exitcode of process,
      'duration': timedelta in seconds}

`exit` will not be included if result is sucess (0)


# TODO

- Finish Tests, started as TDD and then hulk-smashed the end
- Better runtime streaming
