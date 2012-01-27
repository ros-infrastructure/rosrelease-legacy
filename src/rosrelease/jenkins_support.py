import os
import jenkins

SERVER = 'http://build.willowgarage.com/'

def trigger_source_deb(stack_name, stack_version, distro, simulate=False):
    h = jenkins.Jenkins(SERVER)
    parameters = {
        'DISTRO_NAME': distro.release_name,
        'STACK_NAME': stack_name,
        'STACK_VERSION': stack_version,        
        }
    args = ('debbuild-sourcedeb',)
    kwds = dict(parameters=parameters, token='RELEASE_SOURCE_DEB')
    if simulate:
        return h.build_job_url(*args, **kwds)
    else:
        h.build_job(*args, **kwds)
