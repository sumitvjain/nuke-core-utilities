from nuke_core_utilities.nodes import NodeCreator

"""
This is Nuke python module, if require then append in system path for write nuke api code
import sys
sys.path.append(r"C:\\Program Files\\Nuke15.1v3\\lib\\site-packages")
"""


node_creator = NodeCreator()
# help(node_creator.create_node)

node_creator.create_node(
    node_class='Blur', 
    name='sumit', 
    position=(100, 100), 
    knobs={'size': 5.5, 'quality': 5, 'mix':0.70}, 
    color=2448378879
    )