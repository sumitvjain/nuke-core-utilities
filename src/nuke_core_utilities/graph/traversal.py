import nuke


def get_upstream_nodes(node, collected=None):
    """
    Param:
        node : node object/instance
        collected: nodes objects(set)
    Returns:
        collected_lst : dependencies nodes list
    """
    if collected is None:
        collected = set()

    for i in range(node.inputs()):
        input_node = node.input(i)
        if input_node and input_node not in collected:
            collected.add(input_node)
            get_upstream_nodes(input_node, collected)

    collected_lst = list(collected)

    return collected_lst



