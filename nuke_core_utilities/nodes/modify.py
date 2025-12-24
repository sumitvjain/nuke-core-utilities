import nuke


def get_all_knobs_lst(node):
    knobs_lst = [knob.name() for knob in node.allKnobs()]
    return knobs_lst


def set_knob_value(node, knob_name, value):
    """
    Set knob value safely
    """
    if knob_name not in get_all_knobs_lst(node):
        return False

    node[knob_name].setValue(value)
    return True


def disable_node(node, state=True):
    """
    Enable / disable node
    """
    if "disable" in get_all_knobs_lst(node):
        node["disable"].setValue(state)

def set_node_label(node, text):
    """
    Set node label
    """
    if "label" in get_all_knobs_lst(node):
        node["label"].setValue(text)
