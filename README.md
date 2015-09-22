# BundleTester

A juju-deployer based test runner for bundles and charms.

# Installation

    pip install bundletester

# Introduction

This is designed around the fail fast principal. Each bundle is composed of
charms, each of those charms should have tests ranging from unit tests to
integration tests. The bundle itself will have integration tests. Those tests
should run from least expensive in terms of time to most failing as soon as
possible. The theory is that if tests fail in the charms the bundle cannot
function. Bundletester will therefore pull all the charms and look for any
tests it can find and run those prior running its own integration tests.

This test runner uses the following pattern. A bundle has a URL. The runner can
be run directly from within a bundle checkout or will pull the branch pointed
at by the bundle url. From there it will attempt to look for a 'tests'
directory off the project root. Using the rules described below it will find
and execute each test within that directory and produce a report.

This also includes a bundlewatcher script that can be used as a Jenkins script
trigger.

# Example Usage

From within the top level of a bundle or charm

    bundletester -r json -o result.json

Using a specific bundle or charm directory

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
    -t bundle:mediawiki/single
    -t bundle:mediawiki/6/single
    -t bundle:~charmers/mediawiki/single
    -t bundle:~charmers/mediawiki/6/single

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

The driver file, 'tests/tests.yaml' is used (by default) to control the overall
flow of how tests work. All values in this file and indeed the file itself are
optional. When not provided defaults will be used.

## tests.yaml

A sample `tests.yaml` file::

    bootstrap: false
    reset: false
    setup: script
    teardown: script
    tests: "[0-9]*"
    virtualenv: true
    sources:
        - ppas, etc
    packages:
        - amulet
        - python-requests
    makefile:
        - lint
        - test

Explanation of keys:

**bootstrap**: Allow bootstrap of current env, default: true

**reset**: Use juju-deployer to reset env between test, default: true

**virtualenv**: create and activate a virtualenv in which all tests are run, default: true

**tests**: glob of executable files in testdir to treat as tests, default: "\*"

**excludes**: list of charm names for which tests should be skipped

**sources**: list of package sources to add automatically

**packages**: list of packages to install automatically with apt

**makefile**: list of make targets to execute, default: [lint, test]

**setup**: optional name of script in test dir to run before each test

**teardown**: optional name of script to run after each test





## Finding Tests

When tests.yaml's test pattern is executed it will yield test that should be run. Each
of these test files can optional have a control file of the same name but with a `.yaml`
extension. If present this file has a similar layout to tests.yaml.

A sample `01-test.yaml` file::

    bundle: bundle.yaml
    setup: script
    teardown: script

Explanation of keys:

bundle: A bundle file in/relative to the tests directory. If bundle isn't
specified <BUNDLE_ROOT>/bundle.yaml will be used by default.

setup: optional script to be run before this test. This is called after the
tests.yaml setup if present.

teardown: optional script to be run after this test. This is called before the
tests.yaml teardown if present.

## Setup/Teardown

If these scripts fail with a non-zero exit code the test will be recorded as a
failure with that exit code.

## Test Execution

Each test should be executable. If `virtualenv` is true each test will be
executed with that environment activated.

Each test will have its stdout and stderr captured.

Each tests exit code will be captured. A non-zero return indicates failure.

## Reporting Results

Any test failures will result in a non-zero exit code.

Using -r json a JSON string will be outputted on stdout. This string will
contain at minimum the following structure (additional keys are possible)

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
