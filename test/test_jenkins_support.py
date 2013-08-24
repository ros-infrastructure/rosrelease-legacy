import os
import rospkg.distro

from rosrelease.jenkins_support import trigger_source_deb

def get_test_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'rosdistro'))

def test_trigger_source_deb():
    distro = rospkg.distro.load_distro(os.path.join(get_test_path(), 'fuerte.rosdistro'))
    url = trigger_source_deb('common', '1.8.0', distro, simulate=True)
    # not much to this test, mainly tests data structure integration
    assert url == 'http://jenkins.ros.org/job/_dry_sourcedeb/buildWithParameters?STACK_NAME=common&STACK_VERSION=1.8.0&token=RELEASE_SOURCE_DEB&DISTRO_NAME=fuerte'
