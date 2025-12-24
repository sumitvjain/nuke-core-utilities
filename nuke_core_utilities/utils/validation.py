import nuke 


def validate_node_class(node, expected_class):
    """Raise error if node class mismatches"""

def ensure_single_selection():
    """Ensure only one node selected"""

def validate_path_exists(path):
    """Check file path exists"""



def ensure_single_selection():
    """
    Ensure exactly one node is selected
    """
    nodes = nuke.selectedNodes()
    if len(nodes) != 1:
        raise RuntimeError("Please select exactly one node")
    return nodes[0]


def validate_node_class(node, expected_class):
    """
    Validate node class
    """
    if node.Class() != expected_class:
        raise TypeError(
            f"Expected {expected_class}, got {node.Class()}"
        )
