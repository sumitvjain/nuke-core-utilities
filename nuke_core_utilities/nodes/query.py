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


def get_nodes_by_class(node_class):
    """
    Returns list of nodes of given class
    """
    return nuke.allNodes(node_class)


def get_node_by_name(name):
    """
    Return node by name or None
    """
    try:
        return nuke.toNode(name)
    except Exception:
        return None


def get_selected_nodes():
    """
    Return selected nodes
    """
    return nuke.selectedNodes()


def get_node_knob_value(node, knob_name):
    """
    Safely fetch knob value
    """
    if knob_name in node.knobs():
        return node[knob_name].value()
    return None
