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

import tarfile
import tempfile
import shutil
import hashlib

from .sourcedeb_support import control_data

def md5sum_file(filename):
    m = hashlib.md5()
    with open(filename, 'rb') as f:
        data = f.read(4096)
        while data:
            m.update(data)
            data = f.read(4096)
    return m.hexdigest()

def make_dist_of_dir(tmp_dir, distro_stack, rospack, rosstack, executor):
    """
    Create tarball in a temporary directory. 
    It is expected the tempdir has a fresh checkout of the stack.

    @param name: stack name
    @param version: stack version
    @return: tarball file path, control data. 
    """
    name = distro_stack.name
    version = distro_stack.version
    tmp_source_dir = os.path.join(tmp_dir, name)
    executor.info('Building a distribution for %s in %s'%(name, tmp_source_dir))
    tarball = create_stack_tarball(tmp_source_dir, name, version)
    md5sum = md5sum_file(tarball)
    control = control_data(name, version, md5sum, rospack, rosstack)
    
    # move tarball outside tmp_dir so we can clean it up
    dst = os.path.join(tempfile.gettempdir(), os.path.basename(tarball))
    shutil.copyfile(tarball, dst)
    return dst, control


TAR_IGNORE_TOP=['build']
TAR_IGNORE_ALL=['.svn', '.git', '.hg']

def tar_exclude(name):
    if name.split('/')[-1] in TAR_IGNORE_ALL:
        return True
    else:
        return False

def create_stack_tarball(path, stack_name, stack_version):
    """
    Create a source tarball from a stack at a particular path.
  
    @param name: name of stack
    @param stack_version: version number of stack
    @param path: the path of the stack to package up
    @return: the path of the resulting tarball, or else None
    """

    # Verify that the stack has both a stack.xml and CMakeLists.txt file
    stack_xml_path = os.path.join(path, 'stack.xml')
    cmake_lists_path = os.path.join(path, 'CMakeLists.txt')

    if not os.path.exists(stack_xml_path):
        raise ReleaseException("Could not find stack manifest, expected [%s]."%(stack_xml_path))
    if not os.path.exists(cmake_lists_path):
        raise ReleaseException("Could not find CMakeLists.txt file, expected [%s]."%(cmake_lists_path))

    # Create the build directory
    build_dir = os.path.join(path, 'build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    tarfile_name = os.path.join(build_dir,'%s-%s.tar.bz2'%(stack_name, stack_version))
    archive_dir = '%s-%s'%(stack_name, stack_version)

    tar = tarfile.open(tarfile_name, 'w:bz2')
  
    for x in os.listdir(path):
        if x not in TAR_IGNORE_TOP + TAR_IGNORE_ALL:
            # path of item
            p = os.path.join(path,x)
            # tar path of item
            tp = os.path.join(archive_dir, x)
            
            tar.add(p, tp, exclude=tar_exclude)
            
    tar.close()
    return tarfile_name

