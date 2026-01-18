import nuke
import os


# def create_node(node_class, name=None, xpos=None, ypos=None):
#     """
#     Create a Nuke node safely with optional name and position.

#     Args:
#         node_class (str): Nuke node class name (e.g. 'Grade', 'Merge').
#         name (str, optional): Name for the node.
#         xpos (int, optional): X position in node graph.
#         ypos (int, optional): Y position in node graph.

#     Returns:
#         nuke.Node: Created node, or None if creation fails.
#     """
#     try:
#         node = nuke.createNode(node_class, inpanel=False)

#         if name is not None:
#             node.setName(name)

#         if xpos is not None:
#             node.setXpos(int(xpos))

#         if ypos is not None:
#             node.setYpos(int(ypos))

#         return node

#     except Exception as e:
#         nuke.warning("Failed to create node {}: {}".format(node_class, e))
#         return None


# def create_read(path, colorspace=None):
#     """
#     Create a Read node with file path and optional colorspace.

#     Params:
#         path : File path (str)
#         colorspace : str

#     Returns:
#         read : read node object or None
#     """
#     if not path:
#         nuke.warning("create_read: Empty path provided")
#         return None

#     if not os.path.exists(path):
#         nuke.warning("create_read: Path does not exist: {}".format(path))
#         return None

#     try:
#         read = nuke.createNode("Read", inpanel=False)
#         read["file"].fromUserText(path)

#         if colorspace:
#             try:
#                 read["colorspace"].setValue(colorspace)
#             except Exception:
#                 nuke.warning(
#                     "Colorspace '{}' not available on this Read node".format(colorspace)
#                 )

#         return read

#     except Exception as e:
#         nuke.warning("Failed to create Read node: {}".format(e))
#         return None


# def create_write(path, file_type="exr"):
#     """
#     Create a Write node with defaults. Auto-connect Input if node selected. 

#     Args:
#         path (str): Output file path (can include frame padding).
#         file_type (str): File type (exr, png, jpg, mov, etc).

#     Returns:
#         nuke.Node: Created Write node, or None if creation fails.
#     """
#     if not path:
#         nuke.warning("create_write: Empty output path")
#         return None

#     try:
#         write = nuke.createNode("Write", inpanel=False)

#         # Set file path
#         write["file"].fromUserText(path)

#         # File type
#         if "file_type" in write.knobs():
#             write["file_type"].setValue(file_type)

#         # ---- Defaults for EXR ----
#         if file_type.lower() == "exr":
#             if "channels" in write.knobs():
#                 write["channels"].setValue("rgba")

#             if "datatype" in write.knobs():
#                 write["datatype"].setValue("16 bit half")

#             if "compression" in write.knobs():
#                 write["compression"].setValue("Zip (16 scanlines)")

#         sel = nuke.selectedNode()
#         if sel:
#             write.setInput(0, sel[0])


#         return write

#     except Exception as e:
#         nuke.warning("Failed to create Write node: {}".format(e))
#         return None



##################################################################


# """
# Node creation utilities
# """

import random
from typing import Dict, List, Tuple, Optional, Any
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.constants import *
from ..data.cache import cached_function

logger = get_logger(__name__)

class NodeCreator:
    """Advanced node creation utilities"""
    
    def __init__(self):
        self.node_templates = {}
        self._load_node_templates()
    
    def _load_node_templates(self):
        """Load predefined node templates"""
        self.node_templates = {
            'color_correction': {
                'nodes': [
                    {'class': 'Grade', 'name': 'Grade1'},
                    {'class': 'ColorCorrect', 'name': 'ColorCorrect1'},
                    {'class': 'Clamp', 'name': 'Clamp1'}
                ],
                'connections': [
                    (0, 1, 0, 0),
                    (1, 2, 0, 0)
                ],
                'positions': [
                    (0, 0),
                    (150, 0),
                    (300, 0)
                ]
            },
            'keying_setup': {
                'nodes': [
                    {'class': 'Keyer', 'name': 'Keyer1'},
                    {'class': 'IBKColour', 'name': 'IBKColour1'},
                    {'class': 'IBKGizmo', 'name': 'IBKGizmo1'},
                    {'class': 'Merge2', 'name': 'Merge1', 'knobs': {'operation': 'mask'}}
                ],
                'connections': [
                    (0, 3, 0, 0),
                    (1, 3, 0, 1),
                    (2, 3, 0, 2)
                ],
                'positions': [
                    (0, 0),
                    (0, 100),
                    (0, 200),
                    (150, 100)
                ]
            }
        }
    
    def create_node(self, node_class: str, 
                   name: str = None,
                   position: Tuple[int, int] = None,
                   knobs: Dict[str, Any] = None,
                   color: int = None) -> Optional['nuke.Node']:
        """
        Create a node with custom settings
        
        Args:
            node_class: Nuke node class
            name: Custom node name
            position: (x, y) position
            knobs: Dictionary of knob values
            color: Tile color
            
        Returns:
            Created node or None
        """
        with TimerContext(f"create_node_{node_class}", logger):
            try:
                # Create node
                node = nuke.createNode(node_class)
                
                if not node:
                    return None
                
                # Set name if provided
                if name:
                    node.setName(name)
                
                # Set position if provided
                if position:
                    node.setXpos(position[0])
                    node.setYpos(position[1])
                
                # Set knob values
                if knobs:
                    self._set_knob_values(node, knobs)
                
                # Set color if provided
                if color is not None:
                    self._set_node_color(node, color)
                
                logger.debug(f"Created node: {node_class} -> {node.name()}")
                return node
                
            except Exception as e:
                logger.error(f"Failed to create node {node_class}: {e}")
                return None
    
    def create_node_group(self, nodes: List['nuke.Node'] = None,
                         name: str = "Group1",
                         position: Tuple[int, int] = None,
                         color: int = COLOR_GROUP) -> Optional['nuke.Group']:
        """
        Create a group from selected nodes
        
        Args:
            nodes: Nodes to group (None for selected nodes)
            name: Group name
            position: Group position
            color: Group color
            
        Returns:
            Created group or None
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if not nodes:
                logger.warning("No nodes to group")
                return None
            
            # Store original selection
            original_selection = nuke.selectedNodes()
            
            # Select nodes to group
            nuke.selectAll()
            nuke.invertSelection()
            for node in nodes:
                node.setSelected(True)
            
            # Create group
            group = nuke.collapseToGroup()
            group.setName(name)
            
            # Set position
            if position:
                group.setXpos(position[0])
                group.setYpos(position[1])
            
            # Set color
            self._set_node_color(group, color)
            
            # Restore original selection
            nuke.selectAll()
            nuke.invertSelection()
            for node in original_selection:
                node.setSelected(True)
            
            logger.info(f"Created group '{name}' with {len(nodes)} nodes")
            return group
            
        except Exception as e:
            logger.error(f"Failed to create group: {e}")
            return None
    
    def create_backdrop(self, nodes: List['nuke.Node'] = None,
                       label: str = "",
                       color: int = COLOR_UTILITY,
                       z_order: int = 0) -> Optional['nuke.Node']:
        """
        Create backdrop around nodes
        
        Args:
            nodes: Nodes to enclose (None for selected nodes)
            label: Backdrop label
            color: Backdrop color
            z_order: Z-order (higher = behind)
            
        Returns:
            Created backdrop or None
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if not nodes:
                # Create empty backdrop at center
                backdrop = nuke.nodes.BackdropNode(
                    label=label,
                    tile_color=color,
                    note_font_size=42,
                    z_order=z_order
                )
                backdrop.setXpos(-100)
                backdrop.setYpos(-100)
                backdrop['bdwidth'].setValue(200)
                backdrop['bdheight'].setValue(200)
                return backdrop
            
            # Calculate bounds
            x_positions = [n.xpos() for n in nodes]
            y_positions = [n.ypos() for n in nodes]
            widths = [n.screenWidth() for n in nodes]
            heights = [n.screenHeight() for n in nodes]
            
            min_x = min(x_positions) - 20
            min_y = min(y_positions) - 20
            max_x = max(x + w for x, w in zip(x_positions, widths)) + 20
            max_y = max(y + h for y, h in zip(y_positions, heights)) + 20
            
            # Create backdrop
            backdrop = nuke.nodes.BackdropNode(
                xpos=min_x,
                ypos=min_y,
                bdwidth=max_x - min_x,
                bdheight=max_y - min_y,
                label=label,
                tile_color=color,
                note_font_size=42,
                z_order=z_order
            )
            
            logger.debug(f"Created backdrop around {len(nodes)} nodes")
            return backdrop
            
        except Exception as e:
            logger.error(f"Failed to create backdrop: {e}")
            return None
    
    def create_template(self, template_name: str,
                       position: Tuple[int, int] = None,
                       name_prefix: str = "") -> List['nuke.Node']:
        """
        Create nodes from a template
        
        Args:
            template_name: Template name
            position: Base position
            name_prefix: Prefix for node names
            
        Returns:
            List of created nodes
        """
        template = self.node_templates.get(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return []
        
        try:
            created_nodes = []
            
            # Create nodes
            for i, node_def in enumerate(template['nodes']):
                node_class = node_def['class']
                node_name = f"{name_prefix}{node_def['name']}"
                
                # Calculate position
                if position and 'positions' in template and i < len(template['positions']):
                    node_pos = (
                        position[0] + template['positions'][i][0],
                        position[1] + template['positions'][i][1]
                    )
                else:
                    node_pos = position
                
                # Create node
                node = self.create_node(
                    node_class,
                    name=node_name,
                    position=node_pos,
                    knobs=node_def.get('knobs', {})
                )
                
                if node:
                    created_nodes.append(node)
            
            # Create connections
            if 'connections' in template:
                for conn in template['connections']:
                    if (len(conn) >= 4 and 
                        conn[0] < len(created_nodes) and 
                        conn[1] < len(created_nodes)):
                        source = created_nodes[conn[0]]
                        target = created_nodes[conn[1]]
                        target.setInput(conn[3], source)
            
            logger.info(f"Created template '{template_name}' with {len(created_nodes)} nodes")
            return created_nodes
            
        except Exception as e:
            logger.error(f"Failed to create template {template_name}: {e}")
            return []
    
    def create_node_grid(self, node_class: str,
                        rows: int = 3,
                        cols: int = 3,
                        start_position: Tuple[int, int] = (0, 0),
                        spacing: Tuple[int, int] = (100, 100),
                        naming_pattern: str = "{class}_{row}_{col}") -> List['nuke.Node']:
        """
        Create a grid of nodes
        
        Args:
            node_class: Node class to create
            rows: Number of rows
            cols: Number of columns
            start_position: Top-left position
            spacing: Spacing between nodes
            naming_pattern: Naming pattern with {class}, {row}, {col} placeholders
            
        Returns:
            List of created nodes
        """
        nodes = []
        
        try:
            for row in range(rows):
                for col in range(cols):
                    position = (
                        start_position[0] + col * spacing[0],
                        start_position[1] + row * spacing[1]
                    )
                    
                    name = naming_pattern.format(
                        node_class,
                        row=row + 1,
                        col=col + 1
                    )
                    
                    node = self.create_node(node_class, name=name, position=position)
                    if node:
                        nodes.append(node)
            
            logger.debug(f"Created {len(nodes)} {node_class} nodes in grid")
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to create node grid: {e}")
            return []
    
    def duplicate_nodes(self, nodes: List['nuke.Node'] = None,
                       offset: Tuple[int, int] = (100, 0),
                       connect_inputs: bool = False,
                       connect_outputs: bool = False) -> List['nuke.Node']:
        """
        Duplicate nodes with optional connections
        
        Args:
            nodes: Nodes to duplicate (None for selected nodes)
            offset: Position offset for duplicates
            connect_inputs: Connect to same inputs as original
            connect_outputs: Connect to same outputs as original
            
        Returns:
            List of duplicated nodes
        """
        if nodes is None:
            nodes = nuke.selectedNodes()
        
        if not nodes:
            return []
        
        try:
            # Store original selection
            original_selection = nuke.selectedNodes()
            
            # Select nodes to duplicate
            nuke.selectAll()
            nuke.invertSelection()
            for node in nodes:
                node.setSelected(True)
            
            # Copy and paste
            nuke.nodeCopy("%clipboard%")
            nuke.nodePaste("%clipboard%")
            
            # Get duplicated nodes
            duplicated = nuke.selectedNodes()
            
            # Position duplicates
            for i, node in enumerate(duplicated):
                if i < len(nodes):
                    original = nodes[i]
                    node.setXpos(original.xpos() + offset[0])
                    node.setYpos(original.ypos() + offset[1])
            
            # Restore original selection
            nuke.selectAll()
            nuke.invertSelection()
            for node in original_selection:
                node.setSelected(True)
            
            logger.debug(f"Duplicated {len(duplicated)} nodes")
            return duplicated
            
        except Exception as e:
            logger.error(f"Failed to duplicate nodes: {e}")
            return []
    
    def _set_knob_values(self, node: 'nuke.Node', knobs: Dict[str, Any]):
        """Set multiple knob values on a node"""
        for knob_name, value in knobs.items():
            knob = node.knob(knob_name)
            if knob:
                try:
                    knob.setValue(value)
                except Exception as e:
                    logger.debug(f"Failed to set knob {knob_name}: {e}")
    
    def _set_node_color(self, node: 'nuke.Node', color: int):
        """Set node tile color"""
        try:
            tile_color_knob = node.knob('tile_color')
            if tile_color_knob:
                tile_color_knob.setValue(color)
        except:
            pass

# Helper functions
def create_node(node_class: str, **kwargs) -> Optional['nuke.Node']:
    """Helper function to create node"""
    creator = NodeCreator()
    return creator.create_node(node_class, **kwargs)

def create_backdrop(nodes: List['nuke.Node'] = None, **kwargs) -> Optional['nuke.Node']:
    """Helper function to create backdrop"""
    creator = NodeCreator()
    return creator.create_backdrop(nodes, **kwargs)

def create_node_group(nodes: List['nuke.Node'] = None, **kwargs) -> Optional['nuke.Group']:
    """Helper function to create group"""
    creator = NodeCreator()
    return creator.create_node_group(nodes, **kwargs)