"""
Graph traversal algorithms for Nuke node graphs
"""

from collections import deque, defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..data.cache import cached_function

logger = get_logger(__name__)

class GraphTraversal:
    """Advanced graph traversal algorithms for Nuke nodes"""
    
    def __init__(self):
        self.visited_cache = {}
    
    def bfs_traversal(self, start_node: 'nuke.Node',
                     direction: str = 'forward',
                     max_depth: int = None,
                     filter_func: Callable = None) -> List['nuke.Node']:
        """
        Breadth-First Search traversal
        
        Args:
            start_node: Starting node
            direction: 'forward' (outputs), 'backward' (inputs), or 'both'
            max_depth: Maximum traversal depth
            filter_func: Function to filter nodes (returns bool)
            
        Returns:
            List of visited nodes in BFS order
        """
        visited = []
        queue = deque([(start_node, 0)])
        visited_set = set([start_node])
        
        while queue:
            current, depth = queue.popleft()
            
            # Apply filter
            if filter_func and not filter_func(current):
                continue
            
            visited.append(current)
            
            # Check depth limit
            if max_depth and depth >= max_depth:
                continue
            
            # Get neighbors based on direction
            neighbors = []
            
            if direction in ['forward', 'both']:
                neighbors.extend(current.dependent())
            
            if direction in ['backward', 'both']:
                for i in range(current.inputs()):
                    input_node = current.input(i)
                    if input_node:
                        neighbors.append(input_node)
            
            # Add unvisited neighbors to queue
            for neighbor in neighbors:
                if neighbor not in visited_set:
                    visited_set.add(neighbor)
                    queue.append((neighbor, depth + 1))
        
        return visited
    
    def dfs_traversal(self, start_node: 'nuke.Node',
                     direction: str = 'forward',
                     max_depth: int = None,
                     filter_func: Callable = None) -> List['nuke.Node']:
        """
        Depth-First Search traversal
        
        Args:
            start_node: Starting node
            direction: 'forward' (outputs), 'backward' (inputs), or 'both'
            max_depth: Maximum traversal depth
            filter_func: Function to filter nodes (returns bool)
            
        Returns:
            List of visited nodes in DFS order
        """
        visited = []
        visited_set = set()
        
        def dfs_recursive(current, depth):
            if current in visited_set:
                return
            
            if max_depth and depth > max_depth:
                return
            
            # Apply filter
            if filter_func and not filter_func(current):
                return
            
            visited_set.add(current)
            visited.append(current)
            
            # Get neighbors based on direction
            neighbors = []
            
            if direction in ['forward', 'both']:
                neighbors.extend(current.dependent())
            
            if direction in ['backward', 'both']:
                for i in range(current.inputs()):
                    input_node = current.input(i)
                    if input_node:
                        neighbors.append(input_node)
            
            # Recursively traverse neighbors
            for neighbor in neighbors:
                dfs_recursive(neighbor, depth + 1)
        
        dfs_recursive(start_node, 0)
        return visited
    
    def topological_sort(self, nodes: List['nuke.Node'] = None) -> List['nuke.Node']:
        """
        Topological sort of nodes (dependency order)
        
        Args:
            nodes: Nodes to sort (None for all nodes)
            
        Returns:
            Nodes in topological order
        """
        try:
            if nodes is None:
                nodes = nuke.allNodes()
            
            # Calculate indegree for each node
            indegree = defaultdict(int)
            for node in nodes:
                for i in range(node.inputs()):
                    input_node = node.input(i)
                    if input_node and input_node in nodes:
                        indegree[node] += 1
            
            # Find nodes with indegree 0
            queue = deque([n for n in nodes if indegree[n] == 0])
            result = []
            
            while queue:
                current = queue.popleft()
                result.append(current)
                
                # Reduce indegree of dependents
                for dependent in current.dependent():
                    if dependent in nodes:
                        indegree[dependent] -= 1
                        if indegree[dependent] == 0:
                            queue.append(dependent)
            
            # Check for cycles
            if len(result) != len(nodes):
                logger.warning(f"Graph has cycles: {len(nodes) - len(result)} nodes not sorted")
                # Add remaining nodes
                remaining = [n for n in nodes if n not in result]
                result.extend(remaining)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed topological sort: {e}")
            return nodes or []
    
    def find_cycles(self, nodes: List['nuke.Node'] = None) -> List[List['nuke.Node']]:
        """
        Find cycles in the graph
        
        Args:
            nodes: Nodes to analyze (None for all nodes)
            
        Returns:
            List of cycles (each cycle is a list of nodes)
        """
        try:
            if nodes is None:
                nodes = nuke.allNodes()
            
            cycles = []
            visited = set()
            recursion_stack = set()
            parent_map = {}
            
            def dfs_cycle(current):
                visited.add(current)
                recursion_stack.add(current)
                
                # Check dependents
                for dependent in current.dependent():
                    if dependent not in nodes:
                        continue
                    
                    if dependent not in visited:
                        parent_map[dependent] = current
                        if dfs_cycle(dependent):
                            return True
                    elif dependent in recursion_stack:
                        # Found a cycle
                        cycle = []
                        node_in_cycle = current
                        while node_in_cycle != dependent:
                            cycle.append(node_in_cycle)
                            node_in_cycle = parent_map.get(node_in_cycle)
                        cycle.append(dependent)
                        cycle.reverse()
                        cycles.append(cycle)
                        return True
                
                recursion_stack.remove(current)
                return False
            
            for node in nodes:
                if node not in visited:
                    parent_map.clear()
                    dfs_cycle(node)
            
            return cycles
            
        except Exception as e:
            logger.error(f"Failed to find cycles: {e}")
            return []
    
    def find_all_paths(self, start_node: 'nuke.Node',
                      end_node: 'nuke.Node',
                      max_paths: int = 100,
                      max_length: int = 20) -> List[List['nuke.Node']]:
        """
        Find all paths between two nodes
        
        Args:
            start_node: Starting node
            end_node: Target node
            max_paths: Maximum number of paths to find
            max_length: Maximum path length
            
        Returns:
            List of paths (each path is a list of nodes)
        """
        paths = []
        
        def dfs_find_paths(current, current_path, visited):
            if len(paths) >= max_paths:
                return
            
            if len(current_path) > max_length:
                return
            
            if current == end_node:
                paths.append(current_path.copy())
                return
            
            visited.add(current)
            
            # Explore dependents
            for dependent in current.dependent():
                if dependent not in visited:
                    current_path.append(dependent)
                    dfs_find_paths(dependent, current_path, visited)
                    current_path.pop()
            
            visited.remove(current)
        
        dfs_find_paths(start_node, [start_node], set())
        return paths
    
    def get_dependency_tree(self, node: 'nuke.Node',
                          max_depth: int = None) -> Dict:
        """
        Build dependency tree for a node
        
        Args:
            node: Root node
            max_depth: Maximum tree depth
            
        Returns:
            Nested dictionary representing dependency tree
        """
        tree = {
            'node': node.name(),
            'class': node.Class(),
            'children': [],
            'depth': 0
        }
        
        def build_tree(current, parent_dict, current_depth):
            if max_depth and current_depth >= max_depth:
                return
            
            # Get dependents as children
            for dependent in current.dependent():
                child = {
                    'node': dependent.name(),
                    'class': dependent.Class(),
                    'children': [],
                    'depth': current_depth + 1
                }
                parent_dict['children'].append(child)
                build_tree(dependent, child, current_depth + 1)
        
        build_tree(node, tree, 0)
        return tree
    
    def find_common_ancestors(self, nodes: List['nuke.Node']) -> List['nuke.Node']:
        """
        Find common ancestors of multiple nodes
        
        Args:
            nodes: List of nodes
            
        Returns:
            List of common ancestor nodes
        """
        if not nodes:
            return []
        
        if len(nodes) == 1:
            return self.bfs_traversal(nodes[0], direction='backward')
        
        # Get ancestors for each node
        all_ancestors = []
        for node in nodes:
            ancestors = set(self.bfs_traversal(node, direction='backward'))
            all_ancestors.append(ancestors)
        
        # Find intersection
        common = set.intersection(*all_ancestors)
        return list(common)
    
    def find_common_descendants(self, nodes: List['nuke.Node']) -> List['nuke.Node']:
        """
        Find common descendants of multiple nodes
        
        Args:
            nodes: List of nodes
            
        Returns:
            List of common descendant nodes
        """
        if not nodes:
            return []
        
        if len(nodes) == 1:
            return self.bfs_traversal(nodes[0], direction='forward')
        
        # Get descendants for each node
        all_descendants = []
        for node in nodes:
            descendants = set(self.bfs_traversal(node, direction='forward'))
            all_descendants.append(descendants)
        
        # Find intersection
        common = set.intersection(*all_descendants)
        return list(common)
    
    def get_graph_components(self, nodes: List['nuke.Node'] = None) -> List[List['nuke.Node']]:
        """
        Find connected components in the graph
        
        Args:
            nodes: Nodes to analyze (None for all nodes)
            
        Returns:
            List of connected components
        """
        if nodes is None:
            nodes = nuke.allNodes()
        
        visited = set()
        components = []
        
        for node in nodes:
            if node not in visited:
                # Find connected component using BFS
                component = []
                queue = deque([node])
                visited.add(node)
                
                while queue:
                    current = queue.popleft()
                    component.append(current)
                    
                    # Add inputs
                    for i in range(current.inputs()):
                        input_node = current.input(i)
                        if input_node and input_node in nodes and input_node not in visited:
                            visited.add(input_node)
                            queue.append(input_node)
                    
                    # Add dependents
                    for dependent in current.dependent():
                        if dependent in nodes and dependent not in visited:
                            visited.add(dependent)
                            queue.append(dependent)
                
                components.append(component)
        
        return components
    
    def calculate_node_centrality(self, nodes: List['nuke.Node'] = None) -> Dict[str, float]:
        """
        Calculate betweenness centrality for nodes
        
        Args:
            nodes: Nodes to analyze (None for all nodes)
            
        Returns:
            Dictionary mapping node names to centrality scores
        """
        if nodes is None:
            nodes = nuke.allNodes()
        
        centrality = {node.name(): 0.0 for node in nodes}
        node_map = {node.name(): node for node in nodes}
        
        # For each pair of nodes, find shortest paths
        for i, start in enumerate(nodes):
            for end in nodes[i+1:]:
                if start == end:
                    continue
                
                # Find shortest paths
                paths = self._find_shortest_paths(start, end, nodes)
                
                if paths:
                    # Count how many paths go through each node
                    for path in paths:
                        for node in path[1:-1]:  # Exclude start and end
                            centrality[node.name()] += 1.0 / len(paths)
        
        # Normalize
        if centrality:
            max_score = max(centrality.values())
            if max_score > 0:
                for name in centrality:
                    centrality[name] /= max_score
        
        return centrality
    
    def _find_shortest_paths(self, start: 'nuke.Node', 
                           end: 'nuke.Node',
                           all_nodes: List['nuke.Node']) -> List[List['nuke.Node']]:
        """Find all shortest paths between two nodes"""
        # BFS to find shortest path length
        queue = deque([(start, [start])])
        visited = set([start])
        shortest_length = None
        shortest_paths = []
        
        while queue:
            current, path = queue.popleft()
            
            if current == end:
                if shortest_length is None or len(path) == shortest_length:
                    shortest_length = len(path)
                    shortest_paths.append(path)
                elif len(path) > shortest_length:
                    break
                continue
            
            # Expand to dependents
            for dependent in current.dependent():
                if dependent in all_nodes and dependent not in visited:
                    visited.add(dependent)
                    queue.append((dependent, path + [dependent]))
        
        return shortest_paths
    
    def get_execution_order(self, nodes: List['nuke.Node'] = None) -> List['nuke.Node']:
        """
        Get execution order for nodes (considering dependencies)
        
        Args:
            nodes: Nodes to order (None for all nodes)
            
        Returns:
            Nodes in execution order
        """
        if nodes is None:
            nodes = nuke.allNodes()
        
        # Topological sort gives us dependency order
        ordered = self.topological_sort(nodes)
        
        # For nodes at same level, sort by position (left to right, top to bottom)
        def get_position_key(node):
            return (node.ypos(), node.xpos())
        
        # Group by depth in dependency tree
        depth_groups = defaultdict(list)
        for node in ordered:
            depth = self._get_dependency_depth(node, nodes)
            depth_groups[depth].append(node)
        
        # Sort each group
        result = []
        for depth in sorted(depth_groups.keys()):
            group = sorted(depth_groups[depth], key=get_position_key)
            result.extend(group)
        
        return result
    
    def _get_dependency_depth(self, node: 'nuke.Node',
                            all_nodes: List['nuke.Node']) -> int:
        """Calculate dependency depth of a node"""
        max_depth = 0
        
        def dfs(current, visited, current_depth):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for i in range(current.inputs()):
                input_node = current.input(i)
                if input_node and input_node in all_nodes and input_node not in visited:
                    visited.add(input_node)
                    dfs(input_node, visited, current_depth + 1)
        
        dfs(node, set([node]), 0)
        return max_depth
    
    def find_critical_path(self, nodes: List['nuke.Node'] = None) -> List['nuke.Node']:
        """
        Find the critical path (longest dependency chain)
        
        Args:
            nodes: Nodes to analyze (None for all nodes)
            
        Returns:
            Critical path as list of nodes
        """
        if nodes is None:
            nodes = nuke.allNodes()
        
        # Find source nodes
        source_nodes = [n for n in nodes if all(n.input(i) is None for i in range(n.inputs()))]
        
        longest_path = []
        
        for source in source_nodes:
            # DFS to find longest path from this source
            path = self._find_longest_path_from(source, nodes)
            if len(path) > len(longest_path):
                longest_path = path
        
        return longest_path
    
    def _find_longest_path_from(self, start: 'nuke.Node',
                              all_nodes: List['nuke.Node']) -> List['nuke.Node']:
        """Find longest path starting from a node"""
        longest = []
        
        def dfs(current, path, visited):
            nonlocal longest
            current_path = path + [current]
            
            if len(current_path) > len(longest):
                longest = current_path.copy()
            
            visited.add(current)
            
            # Continue with dependents
            for dep in current.dependent():
                if dep in all_nodes and dep not in visited:
                    dfs(dep, current_path, visited.copy())
        
        dfs(start, [], set())
        return longest

# Helper functions
def topological_sort(nodes: List['nuke.Node'] = None) -> List['nuke.Node']:
    """Helper function for topological sort"""
    traversal = GraphTraversal()
    return traversal.topological_sort(nodes)

def find_cycles(nodes: List['nuke.Node'] = None) -> List[List['nuke.Node']]:
    """Helper function to find cycles"""
    traversal = GraphTraversal()
    return traversal.find_cycles(nodes)

def get_execution_order(nodes: List['nuke.Node'] = None) -> List['nuke.Node']:
    """Helper function to get execution order"""
    traversal = GraphTraversal()
    return traversal.get_execution_order(nodes)

def find_critical_path(nodes: List['nuke.Node'] = None) -> List['nuke.Node']:
    """Helper function to find critical path"""
    traversal = GraphTraversal()
    return traversal.find_critical_path(nodes)