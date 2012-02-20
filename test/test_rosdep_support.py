from __future__ import print_function

import os
import sys

import rospkg
import rosrelease.rosdep_support

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

def test_resolve_rosdeps():
    from rosrelease.rosdep_support import resolve_rosdeps
    rospack = rospkg.RosPack()
    rosstack = rospkg.RosStack()
    rosdep_keys = [ 'python-qt-bindings' ]
    resolved = resolve_rosdeps(rosdep_keys, 'oneiric', rospack, rosstack)
    assert 'python-qt4' in resolved, resolved
    assert 'python-qt4-dev' in resolved, resolved
    #no dupes
    assert len(resolved) == len(list(set(resolved)))

    rosdep_keys = [ 'python-empy', 'python-nose' ]
    resolved = resolve_rosdeps(rosdep_keys, 'oneiric', rospack, rosstack)
    assert set(['python-empy', 'python-nose']) == set(resolved)
    #no dupes
    assert len(resolved) == len(list(set(resolved)))

    try:
        resolve_rosdeps(['not a key'], 'oneiric', rospack, rosstack)
        assert False, "should have raised"
    except KeyError as e:
        assert 'not a key' in str(e), "[%s]"%e
    
