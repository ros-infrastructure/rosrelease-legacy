import os
import sys

import rospkg.distro

from rosrelease.executor import MockExecutor
from rosrelease.legacy_main import check_version, prerelease_check
from rosrelease.vcs_support import checkout_branch

def get_test_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'rosdistro'))

def test_check_version():
    assert check_version()

def test_prerelease_check():
    executor = MockExecutor()
    executor.prompt_retval = False
    prerelease_check(executor)
    assert executor.calls['info']
    assert executor.calls['exit']

    executor = MockExecutor()
    executor.prompt_retval = True
    prerelease_check(executor)
    assert not executor.calls['exit']

def test_checkout_and_validate_stack_source():
    if 0:
        distro = rospkg.distro.load_distro(os.path.join(get_test_path(), 'fuerte.rosdistro'))
        stack_name = 'common_rosdeps'
        distro_stack = distro.stacks[stack_name]

        tmpdir = checkout_branch(distro_stack, 'release')
        executor = MockExecutor()
        checkout_and_validate_stack_source(distro_stack, tmpdir, stack_name, '1.0.2', executor)


    
