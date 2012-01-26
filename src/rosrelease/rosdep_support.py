import os
import sys

import rosdep2

def stack_rosdeps(stack_name, platform, rospack, rosstack):
    """
    Calculate dependencies of stack on an 'ubuntu' OS, including both
    ROS stacks and their rosdep dependencies, for the specified
    ubuntu release version.
    
    NOTE: one flaw in this implementation is that it uses the rosdep
    view from the *active environment* to generate the rosdeps. It
    does not generate them from specific versions of stacks. The hope
    is that rosdeps improve monotonically over time, so that this will
    not be a major issue.

    :param platform: platform name (e.g. lucid)

    :returns: list of system package deps, ``str``
    :raises :exc:`rospkg.ResourceNotFound` if stack cannot be found
    :raises :exc:`rosdep2.UnsupportedOs`
    """

    #TODO: should use different lookup backend that loads db from web
    #to prevent issue with inconsistent trees.
    lookup = rosdep2.RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack)
    installer, installer_keys, default_key, \
               os_name, os_version = rosdep2.get_default_installer(lookup)

    # compute the keys we need to resolve
    packages = rosstack.packages_of(stack_name)
    rosdep_keys = []
    for p in packages:
        rosdep_keys.extend(lookup.get_rosdeps(p, implicit=False))

    # resolve the keys
    resolved = []
    for rosdep_name in rosdep_keys:
        view = lookup.get_rosdep_view(stack_name)
        d = view.lookup(rosdep_name)
        _, rule = d.get_rule_for_platform(os_name, os_version, installer_keys, default_key)
        resolved.extend(installer.resolve(rule))
    return resolved
        
