import os
import tempfile
import shutil

import rospkg.distro

from rosrelease import ReleaseException
from rosrelease.executor import MockExecutor
from rosrelease.rosdistro_support import update_rosdistro_yaml, checkin_distro_file, \
     load_and_validate_distro_file

  
def get_test_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'rosdistro'))

def test_update_rosdistro_yaml():
    for stack_name in ['common', 'foo']:
        tmpdir = tempfile.mkdtemp()
        from_rosdistro = os.path.join(get_test_path(), 'fuerte.rosdistro')
        distro_file = os.path.join(tmpdir, 'fuerte.rosdistro')
        shutil.copyfile(from_rosdistro, distro_file)

        update_rosdistro_yaml(stack_name, '0.1.2', distro_file, executor=MockExecutor())

        d = rospkg.distro.load_distro(distro_file)
        assert '0.1.2' == d.stacks[stack_name].version
        shutil.rmtree(tmpdir)

    try:
        update_rosdistro_yaml('common', '0.1.2', 'badfile', executor=MockExecutor())
        assert False, "should have thrown"
    except ReleaseException:
        pass

def test_checkin_distro_file():
    executor = MockExecutor()
    checkin_distro_file('foo', '1.2.3', '/tmp/foo.rosdistro', executor)
    assert executor.calls['ask_and_call'][0] == ([['svn', 'ci', '-m', 'foo 1.2.3', '/tmp/foo.rosdistro']], {'cwd': '/tmp'}), executor.calls['ask_and_call'][0]


def test_load_and_validate_distro_file():
    executor = MockExecutor()
    distro_file = os.path.join(get_test_path(), 'fuerte.rosdistro')
    distro = load_and_validate_distro_file(distro_file, 'common', executor)
    assert distro.stacks['common']

    try:
        distro = load_and_validate_distro_file(distro_file, 'bad', executor)
        assert False, "Should have thrown"
    except ReleaseException:
        pass
        
