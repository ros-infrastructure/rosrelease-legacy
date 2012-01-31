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

import rosdep2
import rospkg

from .rosdep_support import stack_rosdeps

IMPLICIT_DEPS = ['libc6','build-essential','cmake','python-yaml','subversion']

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
        try:
            rosdeps[platform] = stack_rosdeps(stack_name, platform, rospack, rosstack)
            rosdeps[platform].extend([x for x in IMPLICIT_DEPS if not x in rosdeps[platform]])
        except rosdep2.ResolutionError:
            # this is expected; not all platforms are supported by every stack
            pass
        
    return metadata

def _text_only(soup):
    return ''.join(soup.findAll(text=True))

def convert_html_to_text(d):
    """
    Convert a HTML description to plain text. This routine still has
    much work to do, but appears to handle the common uses of HTML in
    our current manifests.
    """
    # check for presence of tags
    if '<' in d:
        from .BeautifulSoup import BeautifulSoup
        soup = BeautifulSoup(d)

        # first, target formatting tags with a straight replace
        for t in ['b', 'strong', 'em', 'i', 'tt', 'a']:
            tags = soup.findAll(t)
            for x in tags:
                x.replaceWith(_text_only(x))
                
        # second, target low-level container tags
        tags = soup.findAll('li')
        for x in tags:
            x.replaceWith('* '+_text_only(x)+'\n')

        # convert all high-level containers to line breaks
        for t in ['p', 'div']:
            tags = soup.findAll(t)
            for t in tags:
                t.replaceWith(_text_only(t)+'\n')

        # findAll text strips remaining tags
        d = ''.join(soup.findAll(text=True))
        
    # reduce the whitespace as the debian parsers have strict rules
    # about what is a paragraph and what is verbose based on leading
    # whitespace.
    d = '\n'.join([x.strip() for x in d.split('\n')])

    d_reduced = ''
    last = None
    for x in d.split('\n'):
        if last is None:
            d_reduced = x
        else:
            if x == '':
                if last == '':
                    pass
                else:
                    d_reduced += '\n'
            else:
                d_reduced += x + ' '
        last = x
    return d_reduced
