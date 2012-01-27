from __future__ import print_function

import os
import sys

import subprocess

def print_bold(m):
    print('\033[1m%s\033[0m'%m)

def yes_or_no():
    print(("(y/n)"))
    while 1:
        input = sys.stdin.readline().strip()
        if input in ['y', 'n']:
            break
    return input == 'y'

def prompt(msg):
    while True:
        prompt = raw_input(msg)
        if prompt == 'y':
            return True
        elif prompt == 'n':
            return False

#NOTE: ROS 1.2 does not have the cwd arg
def ask_and_call(cmds, cwd=None):
    """
    Pretty print cmds, ask if they should be run, and if so, runs
    them using subprocess.check_call.

    @return: True if cmds were run.
    """
    # Pretty-print a string version of the commands
    def quote(s):
        return '"%s"'%s if ' ' in s else s
    print("Okay to execute:\n")
    print_bold('\n'.join([' '.join([quote(s) for s in c]) for c in cmds]))
    accepted = yes_or_no()
    if accepted:
        for c in cmds:
            if cwd:
                subprocess.check_call(c, cwd=cwd)
            else:
                subprocess.check_call(c)                
    return accepted

class Executor(object):

    def prompt(self, msg):
        """
        Prompt user with message for yes/no confirmation
        """
        raise NotImplementedError()

    def ask_and_call(self, cmds, cwd=None):
        raise NotImplementedError()
    
    def info(self, msg):
        """
        Print msg to user
        """
        raise NotImplementedError()
    
    def info_bold(self, msg):
        raise NotImplementedError()
    
    def check_call(self, cmd, **kwds):
        """
        Invoke cmd.  kwds are same as subprocess.check_call()
        """
        raise NotImplementedError()

    def exit(self, code):
        raise NotImplementedError()
    
class StandardExecutor(object):

    def prompt(self, msg):
        prompt(msg)

    def check_calls(self, cmd, **kwds):
        subprocess.check_call(cmd, **kwds)

    def ask_and_call(self, cmds, cwd=None):
        ask_and_call(cmds, cwd=cwd)

    def info_bold(self, msg):
        print_bold(msg)
        
    def exit(self, code):
        sys.exit(code)
    
    def info(self, msg):
        """
        Print msg to user
        """
        print(msg)

def get_default_executor():
    return StandardExecutor()

from collections import defaultdict
class MockExecutor(object):

    def __init__(self):
        self.calls = defaultdict(list)
        
    def prompt(self, msg):
        """
        Prompt user with message for yes/no confirmation
        """
        self.calls['prompt'].append(msg)

    def ask_and_call(self, cmds, **kwds):
        self.calls['ask_and_call'].append((cmds, kwds))
    
    def info(self, msg):
        """
        Print msg to user
        """
        self.calls['info'].append(msg)
    
    def info_bold(self, msg):
        self.calls['info_bold'].append(msg)
    
    def check_call(self, cmd, **kwds):
        """
        Invoke cmd.  kwds are same as subprocess.check_call()
        """
        self.calls['check_call'].append((cmd, kwds))

    def exit(self, code):
        self.calls['exit'].append(code)
