import nuke


def get_upstream_nodes(node, collected=None):
    """
    Recursively collect upstream nodes
    """
    if collected is None:
        collected = set()

    for i in range(node.inputs()):
        input_node = node.input(i)
        if input_node and input_node not in collected:
            collected.add(input_node)
            get_upstream_nodes(input_node, collected)

    return list(collected)


def get_downstream_nodes(node):
    """
    Return all downstream (dependent) nodes of the given node.

    Args:
        node (nuke.Node): Starting node.

    Returns:
        list[nuke.Node]: All dependent nodes (unique, in graph order).
    """
    if not node:
        return []

    downstream = []
    visited = set()

    def walk_downstrea(n):
        for dep in n.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS):
            if dep not in visited:
                visited.add(dep)
                downstream.append(dep)
                walk_downstrea(dep)

    walk_downstrea(node)
    return downstream


def get_upstream_nodes_name(node):
    """
    Docstring for get_upstream_nodes_name
    
    :param node: Node object/instance
    """
    return [n.name() for n in get_upstream_nodes(node)]
    

def get_downstream_nodes_name(node):
    """
    Docstring for get_downstream_nodes_name
    
    :param node: Node object/instance
    """
    
    return [n.name() for n in get_downstream_nodes(node)]
