import os
import shutil

import rospkg
import rospkg.distro

from rosrelease import ReleaseException
from rosrelease.executor import MockExecutor
from rosrelease.vcs_support import checkout_branch
from rosrelease.rospkg_support import confirm_stack_version, _compute_stack_depends, check_stack_depends

def get_test_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'rosdistro'))

def test_compute_stack_depends():
    # mostly tripwire -- need to scaffold in fake RPP to do better than this
    rospack = rospkg.RosPack()
    rosstack = rospkg.RosStack()
    depends = _compute_stack_depends('geometry', rospack, rosstack)
    assert 'ros' in depends
    
def test_check_stack_depends():
    # mostly tripwire -- need to scaffold in fake RPP to do better than this
    rospack = rospkg.RosPack()
    rosstack = rospkg.RosStack()
    check_stack_depends('geometry', rospack, rosstack)
    
def test_confirm_stack_version():
    distro = rospkg.distro.load_distro(os.path.join(get_test_path(), 'fuerte.rosdistro'))
    stack_name = 'common_rosdeps'
    distro_stack = distro.stacks[stack_name]

    # checkout the stack twice and make one look like a ROS_PACKAGE_PATH
    executor = MockExecutor()
        
    tmpdir1 = checkout_branch(distro_stack, 'release', executor)
    tmpdir2 = checkout_branch(distro_stack, 'release', executor)
    stack_tmpdir1 = os.path.join(tmpdir1, stack_name)
    stack_tmpdir2 = os.path.join(tmpdir2, stack_name)
    
    rosstack = rospkg.RosStack(ros_paths=[stack_tmpdir1])
    try:
        confirm_stack_version(rosstack, stack_tmpdir2, stack_name, '1.0.2')

        try:
            confirm_stack_version(rosstack, stack_tmpdir2, stack_name, '0.1.2')
            assert False, "should raise"
        except ReleaseException:
            pass
    finally:
        shutil.rmtree(tmpdir1)
        shutil.rmtree(tmpdir2)    


    
