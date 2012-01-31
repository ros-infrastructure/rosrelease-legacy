from __future__ import print_function

import rospkg
rosstack = rospkg.RosStack()
disable = False
try:
    rosstack.get_path('python_qt_binding')
except rospkg.ResourceNotFound:
    print("WARNING: this test suite requires python_qt_binding to test against", file=sys.stderr)
    
#TODO: this test will not work for very long
def test_stack_rosdeps():
    if disable:
        return
    from rosrelease.rosdep_support import stack_rosdeps
    rospack = rospkg.RosPack()
    rosstack = rospkg.RosStack()
    resolved = stack_rosdeps('python_qt_binding', 'oneiric', rospack, rosstack)
    assert 'python-qt4' in resolved, resolved
    #no dupes
    assert len(resolved) == len(list(set(resolved)))

    
