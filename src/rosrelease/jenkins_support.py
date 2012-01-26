import jenkins

def trigger_jenkins_source_deb(name, version, distro):
    h = jenkins.Jenkins(SERVER)
    parameters = {
        'DISTRO_NAME': distro.release_name,
        'STACK_NAME': name,
        'STACK_VERSION': version,        
        }
    h.build_job('debbuild-sourcedeb', parameters=parameters, token='RELEASE_SOURCE_DEB')

def trigger_debs(distro_name, os_platform, arch):
    h = jenkins.Jenkins(SERVER)
    parameters = {
        'DISTRO_NAME': distro_name,
        'STACK_NAME': 'ALL',
        'OS_PLATFORM': os_platform,
        'ARCH': arch,        
        }
    h.build_job('debbuild-build-debs-%s-%s-%s'%(distro_name, os_platform, arch), parameters=parameters, token='RELEASE_BUILD_DEBS')

