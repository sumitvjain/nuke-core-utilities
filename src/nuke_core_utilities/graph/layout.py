"""
Node graph layout and organization utilities
"""

import math
import random
from typing import Dict, List, Tuple, Optional, Set, Any
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.constants import COLOR_UTILITY, COLOR_GROUP
from .connections import ConnectionManager

logger = get_logger(__name__)

class GraphLayout:
    """Automatic graph layout and organization"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.default_spacing = (100, 80)  # (horizontal, vertical)
        self.margin = 50
    
    def auto_layout(self, nodes: List['nuke.Node'] = None,
                   algorithm: str = 'hierarchical',
                   center: Tuple[int, int] = None) -> bool:
        """
        Automatically layout nodes
        
        Args:
            nodes: Nodes to layout (None for all nodes)
            algorithm: 'hierarchical', 'radial', or 'grid'
            center: Center point for layout
            
        Returns:
            Success status
        """
        with TimerContext(f"auto_layout_{algorithm}", logger):
            try:
                if nodes is None:
                    nodes = nuke.allNodes()
                
                if not nodes:
                    return False
                
                if center is None:
                    # Calculate center of existing nodes
                    x_positions = [n.xpos() for n in nodes]
                    y_positions = [n.ypos() for n in nodes]
                    center = (
                        sum(x_positions) // len(x_positions),
                        sum(y_positions) // len(y_positions)
                    )
                
                # Select layout algorithm
                if algorithm == 'hierarchical':
                    success = self._hierarchical_layout(nodes, center)
                elif algorithm == 'radial':
                    success = self._radial_layout(nodes, center)
                elif algorithm == 'grid':
                    success = self._grid_layout(nodes, center)
                else:
                    logger.error(f"Unknown layout algorithm: {algorithm}")
                    return False
                
                if success:
                    logger.info(f"Applied {algorithm} layout to {len(nodes)} nodes")
                
                return success
                
            except Exception as e:
                logger.error(f"Failed to auto layout: {e}")
                return False
    
    def _hierarchical_layout(self, nodes: List['nuke.Node'],
                           center: Tuple[int, int]) -> bool:
        """Apply hierarchical (tree) layout"""
        try:
            # Find source nodes (no inputs)
            source_nodes = [
                n for n in nodes 
                if all(n.input(i) is None for i in range(n.inputs()))
            ]
            
            if not source_nodes:
                # Use nodes with lowest indegree
                source_nodes = sorted(
                    nodes,
                    key=lambda n: sum(1 for i in range(n.inputs()) if n.input(i))
                )[:min(3, len(nodes))]
            
            # Layout each source tree
            x_offset = center[0]
            for source in source_nodes:
                tree_nodes = self.connection_manager.get_island_nodes(source)
                tree_nodes = [n for n in tree_nodes if n in nodes]
                
                if tree_nodes:
                    self._layout_tree(source, tree_nodes, x_offset, center[1])
                    x_offset += (
                        max(n.screenWidth() for n in tree_nodes) + 
                        self.default_spacing[0] * 2
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed hierarchical layout: {e}")
            return False
    
    def _layout_tree(self, root: 'nuke.Node', nodes: List['nuke.Node'],
                    start_x: int, start_y: int):
        """Layout nodes in a tree structure"""
        # Group nodes by depth
        depth_groups = defaultdict(list)
        node_depths = {}
        
        # Calculate depths using BFS
        queue = deque([(root, 0)])
        visited = set([root])
        
        while queue:
            current, depth = queue.popleft()
            node_depths