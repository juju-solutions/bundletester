import os
import re

from bzrlib import branch


class Launchpad(object):
    def get_origin(self, directory):
        bzr_controlled = os.path.exists(os.path.join(directory, '.bzr'))
        if not bzr_controlled:
            return None
        b = branch.Branch.open(directory)
        matches = []
        for option in [b.get_parent,
                       b.get_push_location,
                       ]:
            try:
                matches.append(option())
            except AttributeError:
                pass

        if not matches:
            return None
        origin = matches[0]
        return origin

    def infer_charm(self, directory):
        origin = self.get_origin(directory)
        if not origin:
            return None
        # we have a bzr branch, see if its a proper charm
        match = re.search('charms/(?P<series>\w+)/(?P<name>[\w\d\-]+)/',
                          origin)
        if not match:
            return None

        charm = match.groupdict()
        if charm['series'] == 'bundles':
            return None
        if '~charmers' in origin:
            charm['prefix'] = 'cs:'
        return charm

    def infer_bundle(self, directory):
        origin = self.get_origin(directory)
        if not origin:
            return None
        # we have a bzr branch, see if its a proper bundle
        match = re.search('charms/bundles/(?P<name>\w+)/', origin)
        if not match:
            return None
        bundle = match.groupdict()
        return bundle
