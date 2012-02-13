# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import sys

import rospkg
import rosdep2
import rosdep2.platforms.debian

OS_NAME = rospkg.os_detect.OS_UBUNTU
INSTALLER_KEY = rosdep2.platforms.debian.APT_INSTALLER

def create_rosdep_lookup(rospack, rosstack):
    #TODO: should use specific SourceListLoader backend that loads db
    #from web to prevent issue with inconsistent trees.
    return rosdep2.RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack)
    
def stack_rosdep_keys(stack_name, rospack, rosstack):
    """
    Calculate rosdep keys of stack.
    
    :returns: list of rosdep keys, ``str``
    :raises :exc:`rospkg.ResourceNotFound` if stack cannot be found
    """
    lookup = create_rosdep_lookup(rospack, rosstack)
    
    # compute the keys we need to resolve
    packages = rosstack.packages_of(stack_name)
    rosdep_keys = []
    for p in packages:
        rosdep_keys.extend(lookup.get_rosdeps(p, implicit=False))
    return rosdep_keys
    
def resolve_stack_rosdeps(stack_name, rosdep_keys, platform, rospack, rosstack):
    """
    Resolve rosdep keys of stack on an 'ubuntu' OS, including both
    ROS stacks and their rosdep dependencies, for the specified
    ubuntu release version.
    
    NOTE: one flaw in this implementation is that it uses the rosdep
    view from the *active environment* to generate the rosdeps. It
    does not generate them from specific versions of stacks. The hope
    is that rosdeps improve monotonically over time, so that this will
    not be a major issue.

    :param platform: platform name (e.g. lucid)

    :returns: list of system package deps, ``str``
    :raises :exc:`rosdep2.ResolutionError` if rosdeps for stack cannot be resolved on the specified platform
    :raises :exc:`rospkg.ResourceNotFound` if stack cannot be found
    :raises :exc:`rosdep2.UnsupportedOs`
    """
    lookup = create_rosdep_lookup(rospack, rosstack)

    # get the apt installer
    context = rosdep2.create_default_installer_context()
    installer = context.get_installer(INSTALLER_KEY)

    # resolve the keys
    resolved = []
    for rosdep_name in rosdep_keys:
        view = lookup.get_rosdep_view(stack_name)
        d = view.lookup(rosdep_name)
        _, rule = d.get_rule_for_platform(OS_NAME, platform, [INSTALLER_KEY], INSTALLER_KEY)
        resolved.extend(installer.resolve(rule))
    return list(set(resolved))
        
