import rospkg

from .release_base import ReleaseException

# this is mostly a copy of the roscreatestack version, but as it has
# different error behavior, I decided to copy it and slim it down (kwc)
def compute_stack_depends(stack_dir):
    """
    @return: depends, licenses
    @rtype: {str: [str]}, [str]
    @raise ReleaseException: if error occurs detecting dependencies
    """
    stack = os.path.basename(os.path.abspath(stack_dir))    
    if os.path.exists(stack_dir):
        packages = roslib.packages.list_pkgs_by_path(os.path.abspath(stack_dir))
        depends = _compute_stack_depends_and_licenses(stack, packages)
    else:
        depends = dict()
    # add in bare ros dependency into any stack as an implicit depend
    if not 'ros' in depends and stack != 'ros':
        depends['ros'] = []
    return depends
    
def _compute_stack_depends_and_licenses(stack, packages):
    pkg_depends = []
    for pkg in packages:
        m = roslib.manifest.parse_file(roslib.manifest.manifest_file(pkg))
        pkg_depends.extend([d.package for d in m.depends])
        
    stack_depends = {}
    for pkg in pkg_depends:
        if pkg in packages:
            continue
        try:
            st = roslib.stacks.stack_of(pkg)
        except roslib.packages.InvalidROSPkgException:
            raise ReleaseException("cannot locate package [%s], which is a dependency in the [%s] stack"%(pkg, stack))
        if not st:
            raise ReleaseException("WARNING: stack depends on [%s], which is not in a stack"%pkg)
        if st == stack:
            continue
        if not st in stack_depends:
            stack_depends[st] = []            
        stack_depends[st].append(pkg)
    return stack_depends

def confirm_stack_version(local_path, checkout_path, stack_name, version):
    vcs_version = get_stack_version(checkout_path, stack_name)
    local_version = get_stack_version(local_path, stack_name)
    if vcs_version != version:
        raise ReleaseException("The version number of stack %s stored in version control does not match specified release version:\n\n%s"%(stack_name, vcs_version))
    if local_version != version:
        raise ReleaseException("The version number of stack %s on your ROS_PACKAGE_PATH does not match specified release version:\n\n%s"%(stack_name, local_version))
    
def check_stack_depends(local_path, stack_name):
    """
    @param local_path: stack directory
    @param stack_name: stack name
    @raise ReleaseException: if declared dependencies for stack do not match actual depends
    """
    depends = compute_stack_depends(local_path)
    m = roslib.stack_manifest.parse_file(os.path.join(local_path, roslib.stack_manifest.STACK_FILE))
    declared = [d.stack for d in m.depends]

    # we enable one more level down for forwarded depends
    # (e.g. metastacks), but go no further.
    for d in m.depends:
        try:
            m_depend = roslib.stack_manifest.parse_file(roslib.stack_manifest.stack_file(d.stack))
            declared.extend([d.stack for d in m_depend.depends])
        except:
            pass
    
    # we enable one more level down for forwarded depends
    # (e.g. metastacks), but go no further.
    for d in m.depends:
        try:
            m_depend = roslib.stack_manifest.parse_file(roslib.stack_manifest.stack_file(d.stack))
            declared.extend([d.stack for d in m_depend.depends])
        except:
            pass
    
    # it is okay for a stack to overdeclare as it may be doing
    # something metapackage-like, but it must have every dependency
    # that is calculated.
    missing = set(depends) - set(declared)
    if missing:
        raise ReleaseException("Stack's declared dependencies are missing calculated dependencies:\n"+'\n'.join(list(missing)))
        

