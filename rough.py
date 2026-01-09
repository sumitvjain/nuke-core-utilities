metadata.py

import nuke 


def get_read_metadata(node):
    """Return metadata dictionary from Read node"""

def get_metadata_value(node, key):
    """Fetch single metadata key"""

def print_metadata(node):
    """Pretty print metadata"
-------------------------------------------------------
read_write.py

import nuke 
import json
import os



def read_yaml(path):
    """Read YAML config"""


def read_json(path):
    """
    Read JSON file safely
    """
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    """
    Write JSON data safely
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
----------------------------------------------------------------
connection.py

import nuke 



def connect_nodes(output_node, input_node, input_index=0):
    """Connect output to input"""

def disconnect_node(node, input_index=0):
    """Disconnect node input"""

def get_input_nodes(node):
    """Return input nodes list"""
---------------------------------------------------------------------
layout.py

import nuke 


def auto_place_below(node, offset=100):
    """Place node below given node"""

def align_nodes_horizontally(nodes):
    """Align nodes on X axis"""

def align_nodes_vertically(nodes):
    """Align nodes on Y axis"""
---------------------------------------------------------------
traversal.py

def get_downstream_nodes(node):
    """
    Param:
        node : node object/instance

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

        # walk_downstrea(node)
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
--------------------------------------------------------------------
modify.py

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
---------------------------------------------------------

query.py

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
--------------------------------------------------------
context.py

import nuke 


def get_context_from_script():
    """Extract show/seq/shot from script path"""

def build_context_dict():
    """Return context dictionary"""
----------------------------------------------------------
paths.py

import nuke 

def get_project_root():
    """Return project root directory"""

def normalize_path(path):
    """Normalize path for OS"""

def get_shot_from_path(path):
    """Extract shot name from path"""
------------------------------------------------------------
write_nodes.py

import nuke 


def set_write_defaults(node):
    """Apply studio default settings"""

def version_up_write_path(node):
    """Auto increment version"""

def get_write_nodes():
    """Return all Write nodes"""
----------------------------------------------------------
selection.py

import nuke 


def select_nodes(nodes):
    """Select given nodes"""

def clear_selection():
    """Clear current selection"""

def invert_selection():
    """Invert current selection"""
-----------------------------------------------------------
knobs.py

import nuke 


def knob_exists(node, knob_name):
    """Check knob existence"""

def copy_knob_values(src, dst):
    """Copy common knobs"""

def reset_knobs(node):
    """Reset knobs to default"""
----------------------------------------------------
validation.py

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
---------------------------------------------------------------------
