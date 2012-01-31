from __future__ import print_function

import os
import sys

import rospkg
rosstack = rospkg.RosStack()
disable = False
try:
    rosstack.get_path('python_qt_binding')
    rosstack.get_path('visualization')
except rospkg.ResourceNotFound:
    print("WARNING: this test suite requires python_qt_binding and visualization to test against", file=sys.stderr)

def test_control_data():
    if disable:
        return
    
    rospack = rospkg.RosPack()
    rosstack = rospkg.RosStack()

    from rosrelease.sourcedeb_support import control_data
    stack_name = 'python_qt_binding'
    stack_version = '1.2.3'
    md5sum = '12345'
    metadata = control_data(stack_name, stack_version, md5sum, rospack, rosstack)

    assert metadata['stack'] == stack_name
    assert metadata['version'] == stack_version
    assert metadata['description-full']
    assert metadata['md5sum'] == md5sum
    assert 'oneiric' in metadata['rosdeps'], metadata['rosdeps']
    assert 'python-qt4' in metadata['rosdeps']['oneiric']

    stack_name = 'visualization'
    metadata = control_data(stack_name, stack_version, md5sum, rospack, rosstack)
    assert metadata['description-full']
    assert 'python_qt_binding' in metadata['depends']

def test_convert_html_to_text():
    rosstack = rospkg.RosStack()
    from rosrelease.sourcedeb_support import convert_html_to_text
    for stack_name in rosstack.list():
        m = rosstack.get_manifest(stack_name)
        converted = convert_html_to_text(m.description)
        # some stacks do in fact have empty descriptions
        if stack_name in ['navigation', 'visualization', 'geometry']:
            assert converted



