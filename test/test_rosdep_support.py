from __future__ import print_function

import os
import sys

import rospkg
rosstack = rospkg.RosStack()
disable = False
try:
    rosstack.get_path('python_qt_binding')
except rospkg.ResourceNotFound:
    print("WARNING: this test suite requires python_qt_binding to test against", file=sys.stderr)
    
#TODO: this test will not work for very long
def test_stack_rosdeps_keys():
    if disable:
        return
    from rosrelease.rosdep_support import stack_rosdep_keys
    rospack = rospkg.RosPack()
    rosstack = rospkg.RosStack()
    resolved = stack_rosdep_keys('python_qt_binding', rospack, rosstack)
    assert 'python-qt-bindings' in resolved, resolved
    assert 'qt4-qmake' in resolved, resolved
    #no dupes
    assert len(resolved) == len(list(set(resolved)))

#TODO: this test will not work for very long
def test_resolve_stack_rosdeps():
    if disable:
        return
    from rosrelease.rosdep_support import stack_rosdep_keys
    from rosrelease.rosdep_support import resolve_stack_rosdeps
    rospack = rospkg.RosPack()
    rosstack = rospkg.RosStack()
    rosdep_keys = stack_rosdep_keys('python_qt_binding', rospack, rosstack)
    resolved = resolve_stack_rosdeps('python_qt_binding', rosdep_keys, 'oneiric', rospack, rosstack)
    assert 'python-qt4' in resolved, resolved
    #no dupes
    assert len(resolved) == len(list(set(resolved)))

    
