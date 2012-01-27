#!/usr/bin/env python

from setuptools import setup

import sys
sys.path.insert(0, 'src')

from rosrelease import __version__

setup(name='rosrelease',
      version=__version__,
      install_requires=['python-jenkins', 'rospkg', 'vcstools', 'rosdep'],
      packages=['rosrelease'],
      package_dir = {'':'src'},
      scripts = ['scripts/rosrelease-legacy'],
      author = "Ken Conley", 
      author_email = "kwc@willowgarage.com",
      url = "http://www.ros.org/wiki/rosrelease",
      download_url = "http://pr.willowgarage.com/downloads/rosrelease/", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      description = "ROS stack release support", 
      long_description = """\
Tools for releasing stacks into ROS distributions.
""",
      license = "BSD"
      )
