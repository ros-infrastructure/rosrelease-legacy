import os
import sys
import rospkg
import rospkg.manifest

from .release_base import ReleaseException

# this is mostly a copy of the roscreatestack version, but as it has
# different error behavior, I decided to copy it and slim it down (kwc)
def _compute_stack_depends(stack_name, rospack, rosstack):
    """
    :returns: depends, licenses, ``{str: [str]}, [str]``
    :raises: :exc:`ReleaseException` If error occurs detecting dependencies
    """
    packages = rosstack.packages_of(stack_name)
    depends = _sub_compute_stack_depends(stack_name, packages, rospack, rosstack)
    # add in bare ros dependency into any stack as an implicit depend
    if not 'ros' in depends and stack_name != 'ros':
        depends['ros'] = []
    return depends
    
def _sub_compute_stack_depends(stack, packages, rospack, rosstack):
    pkg_depends = []
    for pkg in packages:
        m = rospack.get_manifest(pkg)
        pkg_depends.extend([d.name for d in m.depends])
        
    stack_depends = {}
    for pkg in pkg_depends:
        if pkg in packages:
            continue
        try:
            st = rospack.stack_of(pkg)
        except rospkg.ResourceNotFound:
            raise ReleaseException("cannot locate package [%s], which is a dependency in the [%s] stack"%(pkg, stack))
        if not st:
            # filter out catkin-ized legacy manifests
            package_manifest = rospack.get_manifest(pkg)
            if package_manifest.is_catkin:
                continue
            else:
                raise ReleaseException("stack depends on [%s], which is not in a stack"%pkg)
        if st == stack:
            continue
        if not st in stack_depends:
            stack_depends[st] = []            
        stack_depends[st].append(pkg)
    return stack_depends

def confirm_stack_version(rosstack, checkout_path, stack_name, stack_version):
    """
    :raises: :exc:`ReleaseException` If declared stack versions do not match declared version
    """
    rosstack_vcs = rospkg.RosStack([checkout_path])
    vcs_version = rosstack_vcs.get_stack_version(stack_name)
    local_version = rosstack.get_stack_version(stack_name)
    if vcs_version != stack_version:
        raise ReleaseException("The version number of stack %s stored in version control does not match specified release version:\n\n%s"%(stack_name, vcs_version))
    if local_version != stack_version:
        raise ReleaseException("The version number of stack %s on your ROS_PACKAGE_PATH does not match specified release version:\n\n%s"%(stack_name, local_version))
    
def check_stack_depends(stack_name, rospack, rosstack):
    """
    :param local_path: stack directory
    :param stack_name: stack name
    :raises: :exc:`ReleaseException` If declared dependencies for stack do not match actual depends
    """
    depends = _compute_stack_depends(stack_name, rospack, rosstack)
    m = rosstack.get_manifest(stack_name)
    declared = [d.name for d in m.depends]

    # we enable one more level down for forwarded depends
    # (e.g. metastacks), but go no further.
    for d in m.depends:
        m_depend = rosstack.get_manifest(d.name)
        declared.extend([d.name for d in m_depend.depends])
    
    # it is okay for a stack to overdeclare as it may be doing
    # something metapackage-like, but it must have every dependency
    # that is calculated.
    missing = set(depends) - set(declared)
    if missing:
        raise ReleaseException("Stack's declared dependencies are missing calculated dependencies:\n"+'\n'.join(list(missing)))
        

