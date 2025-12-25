import nuke


def get_first_last_frame():
    """
    Return:
        first_frame : int
        last_frame : int
    """
    root = nuke.root()
    first_frame = root.firstFrame()
    last_frame = root.lastFrame()

    return first_frame, last_frame



