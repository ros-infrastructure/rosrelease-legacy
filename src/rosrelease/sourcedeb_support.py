import os
import sys

import rosdep2
import rospkg

from .rosdep_support import stack_rosdeps

ubuntu_map = {
    '12.04': 'precise',
    '11.10': 'oneiric',
    '11.04': 'natty',
    '10.10': 'maverick',
    '10.04': 'lucid',
    }

def platforms():
    # calling this 'platforms' instead of ubuntu_platforms to allow easier conversion to any debian-based release
    return ubuntu_map.values()

def debianize_name(name):
    """
    Convert ROS stack name to debian conventions (dashes, not underscores)
    """
    return name.replace('_', '-')

def control_data(stack_name, stack_version, md5sum, rospack, rosstack):
    """
    Generate metadata for control file. Cannot generate debian dependencies as these are platform specific.
    
    :param stack_name: name of stack, ``str``
    :param stack_version: stack version id, ``str``
    """
    m = rosstack.get_manifest(stack_name)

    #md5sum: #3301
    metadata = dict(md5sum=md5sum, stack=stack_name, package=debianize_name(stack_name),
                    version=stack_version, homepage=m.url, priority='optional')
    
    if m.author.startswith('Maintained by '):
        metadata['maintainer'] = m.author[len('Maintained by '):]
    else:
        metadata['maintainer'] = m.author        
    if m.brief:
        # 60-char limit on control files
        metadata['description-brief'] = m.brief[:60]
    else:
        metadata['description-brief'] = m.brief[:60]

    try:
        description = convert_html_to_text(m.description).rstrip()
    except:
        description = "unknown"

    # per debian spec, single-space pad to signal paragraph
    desc_padded = ''
    for l in description.split('\n'):
        desc_padded += ' '+l+'\n'
    metadata['description-full'] = desc_padded.rstrip()

    # do deps in two parts as ros stack depends need to become version
    # locked later on due to lack of ABI compat
    metadata['depends'] = [d.name for d in m.depends]
    metadata['rosdeps'] = rosdeps = {}
    for platform in platforms():
        rosdeps[platform] = stack_rosdeps(stack_name, platform, rospack, rosstack)
    
    return metadata

