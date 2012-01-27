import urllib2
import os
import sys

from .release_base import ReleaseException
from .executor import get_default_executor
from .jenkins_support import trigger_source_deb
from .rospkg_support import check_stack_depends, confirm_stack_version

from optparse import OptionParser

LEGACY_VERSION=8

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
        executor.info("""Before releasing a stack, you should make sure your stack works well,
 and that the new release does not break any already released stacks
 that depend on your stack.
Willow Garage offers a pre-release test set that tests your stack and all
 released stacks that depend on your stack, on all distributions and architectures
 supported by Willow Garage. 
You can trigger pre-release builds for your stack on <http://code.ros.org/prerelease/>""")
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
        raise ReleaseException("ERROR: Cannot find local checkout of stack [%s].\nThis script requires a local version of the stack that you wish to release.\n"%(name))

    prerelease_check(executor)
    
    distro = load_distro_file(distro_file, stack_name, executor)
    distro_stack = distro.stacks[stack_name]

    tmp_stack_checkout = checkout_and_validate_stack_source(distro_stack, stack_version,
                                                            rospack, rosstack, executor)
    
    # have to do this after validation step
    distro_stack.update_version(stack_version)
    email = get_email()            

    # create the tarball
    tarball, control = make_dist_of_dir(tmp_stack_checkout, stack_name, stack_version, distro_stack)
    if not control['rosdeps']:
        executor.error("""Misconfiguration: control rosdeps are empty.\n
In order to run create.py, the stack you are releasing must be on your current
ROS_PACKAGE_PATH. This is so create.py can access the stack's rosdeps.\n""")
        executor.exit(1)

    print_bold("Release should be in %s"%(tarball))
    if email:
        print("including contact e-mail")
        control['contact'] = email
    else:
        print("no valid contact e-mail, will not send build failure messages")

    # create the VCS tags
    tag_release(distro_stack, tmp_stack_checkout)

    # Remove checkout dir
    shutil.rmtree(tmp_stack_checkout)

    # checkin the tarball
    copy_to_server(stack_name, stack_version, tarball, control)

    # cleanup temporary file
    os.remove(tarball)

    # update the rosdistro file
    update_rosdistro_yaml(stack_name, stack_version, distro_file)
    checkin_distro_file(stack_name, stack_version, distro_file)

    # trigger source deb system
    trigger_source_deb(stack_name, stack_version, distro)

    executor.info("""

Now:
 * update the changelist at http://www.ros.org/wiki/%s/ChangeList
"""%name)
        
