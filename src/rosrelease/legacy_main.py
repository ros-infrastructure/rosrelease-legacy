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

# program name
NAME='rosrelease-legacy'

import os
import sys
import shutil
import urllib2
import yaml

import rospkg

from .executor import get_default_executor
from .jenkins_support import trigger_source_deb
from .release_base import ReleaseException, get_email
from .rospkg_support import check_stack_depends, confirm_stack_version
from .rosdistro_support import load_and_validate_distro_file, update_rosdistro_yaml, checkin_distro_file
from .tarballer import make_dist_of_dir
from .vcs_support import checkout_branch, tag_release, svn_url_exists, checkout_svn_to_tmp

from optparse import OptionParser

LEGACY_VERSION=8

TARBALL_DIR_URL = 'https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(stack_name)s-%(stack_version)s'
ROSORG_URL = 'http://ros.org/download/stacks/%(stack_name)s/%(stack_name)s-%(stack_version)s.tar.bz2'
    
def copy_to_server(name, version, tarball, control, executor, control_only=False):
    """
    :param name: stack name, ``str``
    :param version: stack version, ``str``
    :param tarball: path to tarball file to upload
    :param control: debian control file data, ``dict``
    """
    # create a separate directory for new tarball inside of stack-specific directory
    # - rename vars for URL pattern
    stack_name = name
    stack_version = version
    url = TARBALL_DIR_URL%locals()

    if not svn_url_exists(url):
        cmd = ['svn', 'mkdir', '--parents', "-m", "creating new tarball directory", url]
        executor.info("creating new tarball directory")
        executor.info(' '.join(cmd))
        executor.check_call(cmd)

    tarball_name = os.path.basename(tarball)

    # check to see if tarball already exists. This happens in
    # multi-distro releases. It's best to reuse the existing tarball.
    tarball_url = url + '/' + tarball_name
    if svn_url_exists(tarball_url):
        # no longer ask user to reuse, always reuse b/c people answer
        # this wrong and it breaks things.  the correct way to
        # invalidate is to delete the tarball manually with SVN from
        # now on.
        executor.info("reusing existing tarball of release for this distribution")
        return

    # checkout tarball tree so we can add new tarball
    dir_name = "%s-%s"%(name, version)
    tmp_dir = checkout_svn_to_tmp(dir_name, url, executor)
    subdir = os.path.join(tmp_dir, dir_name)
    if not control_only:
        to_path = os.path.join(subdir, tarball_name)
        executor.info("copying %s to %s"%(tarball, to_path))
        assert os.path.exists(tarball)
        shutil.copyfile(tarball, to_path)

    # write control data to file
    control_f = '%s-%s.yaml'%(name, version)
    with open(os.path.join(subdir, control_f), 'w') as f:
        f.write(yaml.safe_dump(control))
    
    # svn add tarball and control file data
    if not control_only:
        executor.check_call(['svn', 'add', tarball_name], cwd=subdir)
    executor.check_call(['svn', 'add', control_f], cwd=subdir)
    if control_only:
        executor.check_call(['svn', 'ci', '-m', "new release %s-%s"%(name, version), control_f], cwd=subdir)
    else:
        executor.check_call(['svn', 'ci', '-m', "new release %s-%s"%(name, version), tarball_name, control_f], cwd=subdir)

def check_version():
    url = 'https://code.ros.org/svn/release/trunk/VERSION'
    f = urllib2.urlopen(url)
    req_version = int(f.read())
    f.close()
    return bool(LEGACY_VERSION >= req_version)

def checkout_and_validate_stack_source(distro_stack, stack_version,
                                       rospack, rosstack, executor):
    #checkout the stack
    stack_name = distro_stack.name
    tmp_dir = checkout_branch(distro_stack, 'devel', executor)
    confirm_stack_version(rosstack, os.path.join(tmp_dir, stack_name),
                          stack_name, stack_version)
    # raises ReleaseException if check fails
    if 0:
        # disabled because this is causing too many problems with
        # improperly catkin-ized packages.
        check_stack_depends(stack_name, rospack, rosstack)
    return tmp_dir

def load_sys_args(distros_dir):
    """
    :returns: name, version, distro_file, distro_name, ``(str, str, str, str)``
    """
    parser = OptionParser(usage="usage: %prog <stack> <version> <release-name>", prog=NAME)
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error("""You must specify: 
 * stack name (e.g. common_msgs)
 * version (e.g. 1.0.1)
 * distro release name (e.g. cturtle)""")

    name, version, release_name = args
    distro_file = os.path.join(distros_dir, '%s.rosdistro'%(release_name))
    distro_file = os.path.abspath(distro_file)
    if not os.path.isfile(distro_file):
        parser.error("Could not find rosdistro file for [%s].\nExpected it in %s"%(release_name, distro_file))
    # brittle test to make sure that user got the args correct
    if not '.' in version:
        parser.error("[%s] doesn't appear to be a version number"%version)
    return name, version, distro_file

def prerelease_check(executor):
    # ask if stack got tested
    if not executor.prompt('Did you run prerelease tests on your stack?'):
        executor.info("""
Before releasing a stack, you should make sure your stack works well,
and that the new release does not break any already released stacks
that depend on your stack.

Willow Garage offers a pre-release test set that tests your stack and all
released stacks that depend on your stack, on all distributions and
architectures supported by Willow Garage. 

You can trigger pre-release builds for your stack at:

http://code.ros.org/prerelease
""")
        executor.exit(1)
    
def legacy_main():
    executor = get_default_executor()
    if not check_version():
        executor.info("This release script is out-of-date.\nPlease upgrade your release and ros_release scripts")
        executor.exit(1)

    rospack = rospkg.RosPack()
    rosstack = rospkg.RosStack()    

    try:
        distros_dir = os.path.join(rospack.get_path('release_resources'), '..', 'distros')
    except rospkg.ResourceNotFound:
        executor.error("cannot find 'release_resources' package.  Please see release setup instructions")
        executor.exit(1)
    try:
        _legacy_main(executor, rospack, rosstack, distros_dir)
    except ReleaseException as e:
        executor.error(str(e))
        executor.exit(1)

def _legacy_main(executor, rospack, rosstack, distros_dir):
    # load the args
    stack_name, stack_version, distro_file = load_sys_args(distros_dir)
    try:
        local_stack_path = rosstack.get_path(stack_name)
    except rospkg.ResourceNotFound:
        raise ReleaseException("ERROR: Cannot find local checkout of stack [%s].\nThis script requires a local version of the stack that you wish to release.\n"%(stack_name))

    prerelease_check(executor)
    
    distro = load_and_validate_distro_file(distro_file, stack_name, executor)
    distro_stack = distro.stacks[stack_name]

    tmp_stack_checkout = checkout_and_validate_stack_source(distro_stack, stack_version,
                                                            rospack, rosstack, executor)
    
    # Replace DistroStack instance with new, updated version
    # number. Have to do this after validation step.
    distro.stacks[stack_name] = distro_stack = \
                                rospkg.distro.DistroStack(distro_stack.name, stack_version,
                                                          distro_stack.release_name, distro_stack._rules)
    email = get_email(executor)

    # create the tarball
    try:
        tarball, control = make_dist_of_dir(tmp_stack_checkout, distro_stack, rospack, rosstack, executor)
    except rospkg.ResourceNotFound as e:
        executor.error("""Misconfiguration: cannot find dependency.  Please add to your
ROS_PACKAGE_PATH and try your release again.\nResource not found: %s"""%(str(e)))        
        executor.exit(1)
    if not control['rosdeps']:
        executor.error("""Misconfiguration: control rosdeps are empty.\n
In order to run create.py, the stack you are releasing must be on your current
ROS_PACKAGE_PATH. This is so create.py can access the stack's rosdeps.\n""")
        executor.exit(1)

    executor.info_bold("Release should be in %s"%(tarball))
    if email:
        print("including contact e-mail")
        control['contact'] = email
    else:
        print("no valid contact e-mail, will not send build failure messages")

    # create the VCS tags
    tag_release(distro_stack, tmp_stack_checkout, executor)

    # Remove checkout dir
    shutil.rmtree(tmp_stack_checkout)

    # checkin the tarball
    copy_to_server(stack_name, stack_version, tarball, control, executor)

    # cleanup temporary file
    os.remove(tarball)

    # update the rosdistro file
    update_rosdistro_yaml(stack_name, stack_version, distro_file, executor)
    checkin_distro_file(stack_name, stack_version, distro_file, executor)

    # trigger source deb system
    trigger_source_deb(stack_name, stack_version, distro)

    executor.info("""

Now:
 * update the changelist at http://www.ros.org/wiki/%s/ChangeList
"""%stack_name)
        
