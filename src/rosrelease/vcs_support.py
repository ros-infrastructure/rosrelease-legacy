from __future__ import print_function

from .executor import get_default_executor

import subprocess

def svn_url_exists(url):
    """
    @return: True if SVN url points to an existing resource
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
        if executor.prompt("Would you like to tag %s as %s in %s, [y/n]"%(config.dev_branch, tag_name, from_url)):
            executor.check_call(['hg', 'tag', '-f', tag_name], cwd=temp_repo)
            executor.check_call(['hg', 'push'], cwd=temp_repo)
    return [tag_name]

def tag_bzr(distro_stack):
    config = distro_stack.vcs_config
    from_url = config.repo_uri

    # First create a release tag in the bzr repository.
    if prompt("Would you like to tag %s as %s in %s, [y/n]"%(config.dev_branch, config.release_tag, from_url)):
        temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
        #directly create and push the tag to the repo
        subprocess.check_call(['bzr', 'tag', '-d', config.dev_branch,'--force',config.release_tag], cwd=temp_repo)

    # Now create a distro branch.
    # In bzr a branch is a much better solution since
    # branches can be force-updated by fetch.
    branch_name = config.release_tag
    if prompt("Would you like to create the branch %s as %s in %s, [y/n]"%(config.dev_branch, branch_name, from_url)):
        temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
        subprocess.check_call(['bzr', 'push', '--create-prefix', from_url+"/"+branch_name], cwd=temp_repo)
    return [config.distro_tag]

def tag_git(distro_stack, checkout_dir):
    config = distro_stack.vcs_config
    from_url = config.repo_uri
    temp_repo = os.path.join(checkout_dir, distro_stack.name)

    # First create a release tag in the git repository.
    if prompt("Would you like to tag %s as %s in %s, [y/n]"%(config.dev_branch, config.release_tag, from_url)):
        subprocess.check_call(['git', 'tag', '-f', config.release_tag], cwd=temp_repo)
        subprocess.check_call(['git', 'push', '--tags'], cwd=temp_repo)

    # Now create a distro branch. In git tags are not overwritten
    # during updates, so a branch is a much better solution since
    # branches can be force-updated by fetch.
    branch_name = config.distro_tag
    if prompt("Would you like to create the branch %s as %s in %s, [y/n]"%(config.dev_branch, branch_name, from_url)):
        subprocess.check_call(['git', 'branch', '-f', branch_name, config.dev_branch], cwd=temp_repo)
        subprocess.check_call(['git', 'push', from_url, branch_name], cwd=temp_repo)
    return [config.distro_tag]

