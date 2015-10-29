import argparse
import glob
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile

from deployer.config import ConfigStack


def normalize_bundle_location(bundle_location):
    if bundle_location.startswith('lp:'):
        return bundle_location

    if bundle_location.startswith('bundle:'):
        bundle = bundle_location[7:]
        owner, project = bundle.split('/', 1)
        return "lp:%s/charms/bundles/%s/bundle" % (owner, project)

    raise ValueError("Expected bundle location")


def get_bundle(bundle_location, target="bundle", devel=False):
    bundle_location = normalize_bundle_location(bundle_location)
    args = ['bzr', 'checkout']
    if not devel:
        args.append('--lightweight')
    args.extend([bundle_location, target])
    subprocess.check_call(args)


def get_bzr_revno(dirname):
    output = subprocess.check_output(['bzr', 'revno', dirname])
    return int(output.strip())


def record_revisions(target, revisions):
    with open(target, "w") as fp:
        json.dump(revisions, fp, indent=2)


def load_revisions(source):
    if not os.path.exists(source):
        return {}
    return json.load(open(source, "r"))


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log-level', dest="log_level",
                        default=logging.INFO)
    parser.add_argument('-d', '--deployment')
    parser.add_argument('-D', '--devel', action="store_true", dest="devel")
    parser.add_argument('-r', '--revisions')
    parser.add_argument('-b', '--bundle-only',
                        action="store_true", dest="bundle_only")
    parser.add_argument('bundle')
    return parser.parse_args()


def main():
    options = setup_parser()
    logging.basicConfig(level=options.log_level)

    curdir = os.getcwd()
    if not options.revisions:
        options.revisions = os.path.join(curdir, 'revisions.json')

    tmpdir = None
    if options.bundle_only is False:
        tmpdir = tempfile.mkdtemp()
        os.chdir(tmpdir)

    logging.info("Fetching Bundle")
    get_bundle(options.bundle, devel=options.devel)
    configs = glob.glob('bundle/*.yaml')
    if not configs:
        raise ValueError("%s missing YAML files" % options.bundle)

    if options.bundle_only:
        return 0

    c = ConfigStack(configs)
    if not options.deployment and len(c.keys()) == 1:
        options.deployment = c.keys()[0]

    if not options.deployment:
        raise ValueError("Ambigious bundle deployment, use -n")
    deployment = c.get(options.deployment)

    logging.info("Fetching Charms from bundle")
    deployment.fetch_charms()

    logging.info("Gathering Revisions")
    current = {}
    for charm in deployment.get_charms():
        current[charm.name] = get_bzr_revno(charm.path)
    existing = load_revisions(options.revisions)

    if tmpdir:
        shutil.rmtree(tmpdir)
    if current != existing:
        logging.debug("Recored revisions: %s" % options.revisions)
        record_revisions(options.revisions, current)
        logging.info("BUILD: exit 0")
        return 0

    logging.info("SKIP: exit 1")
    return 1


if __name__ == '__main__':
    sys.exit(main())
