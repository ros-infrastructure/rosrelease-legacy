import os
import rospkg.distro
import shutil

from rosrelease.executor import MockExecutor
from rosrelease.vcs_support import checkout_branch, svn_url_exists, tag_release

def get_test_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'rosdistro'))

def test_checkout_branch():
    distro = rospkg.distro.load_distro(os.path.join(get_test_path(), 'fuerte.rosdistro'))
    executor = MockExecutor()
    tmpdir = checkout_branch(distro.stacks['common'], 'devel', executor)
    shutil.rmtree(tmpdir)

def test_svn_url_exists():
    assert svn_url_exists('https://code.ros.org/svn/ros/stacks/')
    assert not svn_url_exists('https://code.ros.org/svn/ros/stacks/fake')

def test_tag_release():
    distro = rospkg.distro.load_distro(os.path.join(get_test_path(), 'fuerte.rosdistro'))

    svn_stack = distro.stacks['laser_drivers']
    executor = MockExecutor()
    tag_release(svn_stack, '/tmp/fake', executor)

    cmds = executor.calls['ask_and_call'][0][0]
    from_url = 'https://code.ros.org/svn/ros-pkg/stacks/laser_drivers/trunk'
    to_url = 'https://code.ros.org/svn/ros-pkg/stacks/laser_drivers/tags/laser_drivers-1.5.1'

    assert cmds[0] == ['svn', 'rm', '-m', 'Making room for new release', to_url]
    assert cmds[1] == ['svn', 'cp', '--parents', '-m', 'Tagging laser_drivers-1.5.1 new release', from_url, to_url], cmds[1]

    hg_stack = distro.stacks['common']
    executor = MockExecutor()    
    tag_release(hg_stack, '/tmp/fake', executor)
    # release tag, then distro tag
    cmd1 = executor.calls['check_call'][0]
    assert cmd1[0] == ['hg', 'tag', '-f', 'common-1.8.0'], cmd1[0]
    cmd2 = executor.calls['check_call'][1]
    assert cmd2[0] == ['hg', 'push']

    cmd3 = executor.calls['check_call'][2]
    assert cmd3[0] == ['hg', 'tag', '-f', 'fuerte'], cmd3[0]
    cmd4 = executor.calls['check_call'][3]
    assert cmd4[0] == ['hg', 'push']

    #TODO: git, bzr
