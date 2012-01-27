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

from __future__ import print_function

import os
import subprocess
import tempfile
import vcstools

from .executor import get_default_executor

def checkout_branch(distro_stack, branch_name, executor):
    """
    Checkout an VCS-based 'dev' code tree to a temporary directory.

    WARNING: executor cannot be used for simulating this method.

    :param executor: only used for printing. Actual checkout will
      occur regardless of executor.
    :param distro_stack: `DistroStack` instance for stack
    :param branch_name: branch name to checkout.  See
      `rospkg.distro.VcsConfig` for valid values.
    
    :returns: temporary directory that contains checkout of tree
      temporary directory.  The checkout will be in a subdirectory
      matching the stack name.  This returns the parent directory so
      that checkout and the temporary directory can be removed
      easily. ``str``
    :raises: :exc:`ValueError` if branch is invalid
    """
    stack_name = distro_stack.name
    vcs_config = distro_stack.vcs_config

    # get this before we do anything with sideeffects
    uri, branch_version = vcs_config.get_branch(branch_name, anonymous=True)
    branch_version = branch_version or '' # convert for vcstools
    
    tmp_dir = tempfile.mkdtemp()
    dest = os.path.join(tmp_dir, stack_name)
    executor.info('Checking out a fresh copy of %s from %s to %s...'%(stack_name, uri, dest))
    vcs_client = vcstools.VcsClient(vcs_config.type, dest)
    vcs_client.checkout(uri, branch_version)
    return tmp_dir

def svn_url_exists(url):
    """
    :returns: ``True`` if SVN url points to an existing resource
    """
    try:
        p = subprocess.Popen(['svn', 'info', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        return p.returncode == 0
    except:
        return False

def append_rm_if_exists(url, cmds, msg):
    if svn_url_exists(url):
        cmds.append(['svn', 'rm', '-m', msg, url]) 
    
def tag_release(distro_stack, checkout_dir, executor=None):
    if executor is None:
        executor = get_default_executor()
        
    if 'svn' in distro_stack._rules:
        tag_subversion(distro_stack, executor)
    elif 'git' in distro_stack._rules:
        tag_git(distro_stack, checkout_dir, executor)
    elif 'hg' in distro_stack._rules:
        tag_mercurial(distro_stack, checkout_dir, executor)
    elif 'bzr' in distro_stack._rules:
        tag_bzr(distro_stack, executor)
    else:
        raise ValueError("unsupported VCS")
    
def tag_subversion(distro_stack, executor):
    cmds = []
    config = distro_stack.vcs_config
    for tag_url in [config.release_tag, config.distro_tag]:
        from_url = config.dev
        release_name = "%s-%s"%(distro_stack.name, distro_stack.version)

        # delete old svn tag if it's present
        append_rm_if_exists(tag_url, cmds, 'Making room for new release')
        # svn cp command to create new tag
        cmds.append(['svn', 'cp', '--parents', '-m', 'Tagging %s new release'%(release_name), from_url, tag_url])
    if not executor.ask_and_call(cmds):    
        executor.info("create_release will not create this tag in subversion")
        return []
    else:
        return [tag_url]
    
def tag_mercurial(distro_stack, checkout_dir, executor):
    config = distro_stack.vcs_config
    from_url = config.repo_uri
    temp_repo = os.path.join(checkout_dir, distro_stack.name)     

    for tag_name in [config.release_tag, config.distro_tag]:
        if executor.prompt("Would you like to tag %s as %s in %s"%(config.dev_branch, tag_name, from_url)):
            executor.check_call(['hg', 'tag', '-f', tag_name], cwd=temp_repo)
            executor.check_call(['hg', 'push'], cwd=temp_repo)
    return [tag_name]

def tag_bzr(distro_stack):
    config = distro_stack.vcs_config
    from_url = config.repo_uri

    # First create a release tag in the bzr repository.
    if prompt("Would you like to tag %s as %s in %s"%(config.dev_branch, config.release_tag, from_url)):
        temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
        #directly create and push the tag to the repo
        subprocess.check_call(['bzr', 'tag', '-d', config.dev_branch,'--force',config.release_tag], cwd=temp_repo)

    # Now create a distro branch.
    # In bzr a branch is a much better solution since
    # branches can be force-updated by fetch.
    branch_name = config.release_tag
    if prompt("Would you like to create the branch %s as %s in %s"%(config.dev_branch, branch_name, from_url)):
        temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
        subprocess.check_call(['bzr', 'push', '--create-prefix', from_url+"/"+branch_name], cwd=temp_repo)
    return [config.distro_tag]

def tag_git(distro_stack, checkout_dir):
    config = distro_stack.vcs_config
    from_url = config.repo_uri
    temp_repo = os.path.join(checkout_dir, distro_stack.name)

    # First create a release tag in the git repository.
    if prompt("Would you like to tag %s as %s in %s"%(config.dev_branch, config.release_tag, from_url)):
        subprocess.check_call(['git', 'tag', '-f', config.release_tag], cwd=temp_repo)
        subprocess.check_call(['git', 'push', '--tags'], cwd=temp_repo)

    # Now create a distro branch. In git tags are not overwritten
    # during updates, so a branch is a much better solution since
    # branches can be force-updated by fetch.
    branch_name = config.distro_tag
    if prompt("Would you like to create the branch %s as %s in %s"%(config.dev_branch, branch_name, from_url)):
        subprocess.check_call(['git', 'branch', '-f', branch_name, config.dev_branch], cwd=temp_repo)
        subprocess.check_call(['git', 'push', from_url, branch_name], cwd=temp_repo)
    return [config.distro_tag]

def checkout_svn_to_tmp(name, uri, executor):
    """
    Checkout an SVN tree to the tmp dir.
    
    Utility routine -- need to replace with vcs
    
    :returns: temporary directory that contains checkout of SVN tree in
      directory 'name'. temporary directory will be a subdirectory of
      OS-provided temporary space. ``str``
    """
    tmp_dir = tempfile.mkdtemp()
    dest = os.path.join(tmp_dir, name)
    executor.info('Checking out a fresh copy of %s from %s to %s...'%(name, uri, dest))
    subprocess.check_call(['svn', 'co', uri, dest])
    return tmp_dir

