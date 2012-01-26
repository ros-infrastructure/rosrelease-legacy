from . release_base import ReleaseException

def update_rosdistro_yaml(stack_name, version, distro_file, executor):
    """
    Update distro file for new stack version
    """
    if not os.path.exists(distro_file):
        raise ReleaseException("[%s] does not exist"%distro_file)

    with open(distro_file) as f:
        d = [d for d in yaml.load_all(f.read())]
        if len(d) != 1:
            raise ReleaseException("found more than one release document in [%s]"%distro_file)
        d = d[0]

    distro_d = d
    if not 'stacks' in d:
        d['stacks'] = {}
    d = d['stacks']
    if not stack_name in d:
        d[stack_name] = {}
    d = d[stack_name]
    # set the version key, assume not overriding properties
    d['version'] = str(version)

    executor.info("Writing new release properties to [%s]"%distro_file)
    with open(distro_file, 'w') as f:
        f.write(yaml.safe_dump(distro_d))
        
def checkin_distro_file(name, version, distro_file, executor):
    cwd = os.path.dirname(distro_file)
    executor.check_call(['svn', 'diff', distro_file], cwd=cwd)
    cmd = ['svn', 'ci', '-m', "%s %s"%(name, version), distro_file]
    executor.ask_and_call([cmd], cwd=cwd)
    
def load_and_validate_distro_file(distro_file, stack_name, executor):
    # make sure distro_file is up-to-date
    executor.info("Retrieving up-to-date %s"%(distro_file))
    executor.check_call(['svn', 'up', distro_file])
        
    distro = rospkg.distro.load_distro(distro_file)
    load_and_validate_properties(stack_name, distro, distro_file, executor)

def load_and_validate_properties(stack_name, distro, distro_file, executor):
    """
    @return: stack_name, version, distro_file, distro
    @rtype: (str, str, str, release.Distro)
    """
    try:
        props = distro.stacks[stack_name]
    except KeyError:
        raise ReleaseException("%s is not listed in distro file %s"%(stack_name, distro_file))
    
    executor.info_bold("Release Properties")
    for p in ['name', 'dev_svn', 'release_svn']:
        executor.info(" * %s: %s"%(p, getattr(props, p)))
    executor.info("Release target is [%s]"%(distro.release_name))
    
