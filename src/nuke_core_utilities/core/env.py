import nuke

def get_nuke_version():
    """
    Return:
        MAJOR_VER : int
        MINOR_VER : int
        STRING    : str
        RELEASE   : int
    """

    major = nuke.NUKE_VERSION_MAJOR
    minor = nuke.NUKE_VERSION_MINOR
    string = nuke.NUKE_VERSION_STRING
    release = nuke.NUKE_VERSION_RELEASE

    return major, minor, string, release

def is_gui():
    """
    Return:
        is_gui : bool
    """
    is_gui = nuke.env.get('gui')

    return is_gui


def get_threads():
    """
    Return :
        thread_value : int
    """
    thread_value = nuke.env.get('threads')

    return thread_value

def get_cpu_count():
    """
    Return:
        cpu_count : int 
    """
    cpu_count = nuke.env.get('numCPUs')

    return cpu_count

def get_executable_path():
    """
    Return:
        exe_path = str
    """
    exe_path = nuke.env.get('ExecutablePath')

    return exe_path

def get_current_script_path():
    """
    Return:
        cur_script_path : str
    """
    cur_script_path = nuke.root().name()

    return cur_script_path

def get_existing_channels():
    """
    Return:
        channels_lst : list
    """
    channels_lst = nuke.root().channels()

    return channels_lst


def is_script_saved():
    """
    Check whether the current Nuke script is saved.

    Returns:
        bool: True if the script has been saved, False otherwise.
    """
    script_path = nuke.root().name()

    if script_path and script_path != "Root":
        return True
    else:
        return False

