"""
Node connection management and analysis
"""

from collections import defaultdict, deque
from typing import Dict, List, Tuple, Set, Optional, Any
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..data.cache import cached_function

logger = get_logger(__name__)

class ConnectionManager:
    """Manager for node connections"""
    
    def __init__(self):
        self.connection_cache = {}
    
    @cached_function(ttl=300)
    def get_node_connections(self, node: 'nuke.Node', 
                           direction: str = 'both') -> Dict:
        """
        Get all connections for a node
        
        Args:
            node: Source node
            direction: 'inputs', 'outputs', or 'both'
            
        Returns:
            Dictionary of connections
        """
        connections = {
            'inputs': {},
            'outputs': {},
            'all': {}
        }
        
        try:
            # Get input connections
            if direction in ['inputs', 'both']:
                for i in range(node.inputs()):
                    input_node = node.input(i)
                    if input_node:
                        connections['inputs'][i] = {
                            'node': input_node.name(),
                            'class': input_node.Class(),
                            'connected': True
                        }
                    else:
                        connections['inputs'][i] = {
                            'node': None,
                            'class': None,
                            'connected': False
                        }
            
            # Get output connections
            if direction in ['outputs', 'both']:
                dependents = node.dependent()
                for i, dep in enumerate(dependents):
                    # Find which input of dependent is connected to our node
                    for input_idx in range(dep.inputs()):
                        if dep.input(input_idx) == node:
                            connections['outputs'][i] = {
                                'node': dep.name(),
                                'class': dep.Class(),
                                'input_index': input_idx
                            }
                            break
            
            # Combine all connections
            connections['all'] = {
                'inputs': connections['inputs'],
                'outputs': connections['outputs']
            }
            
        except Exception as e:
            logger.error(f"Failed to get connections for node {node.name()}: {e}")
        
        return connections
    
    def connect_nodes(self, source: 'nuke.Node', target: 'nuke.Node',
                     input_index: int = 0,
                     output_index: int = 0) -> bool:
        """
        Connect two nodes
        
        Args:
            source: Source node
            target: Target node
            input_index: Input index on target
            output_index: Output index on source
            
        Returns:
            Success status
        """
        try:
            # Validate indices
            if input_index >= target.inputs():
                logger.error(f"Target node only has {target.inputs()} inputs")
                return False
            
            # Disconnect existing connection if any
            existing_source = target.input(input_index)
            if existing_source:
                self.disconnect_nodes(existing_source, target, input_index)
            
            # Make connection
            target.setInput(input_index, source)
            
            logger.debug(f"Connected {source.name()} -> {target.name()}[{input_index}]")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect nodes: {e}")
            return False
    
    def disconnect_nodes(self, source: 'nuke.Node', target: 'nuke.Node',
                        input_index: int = None) -> bool:
        """
        Disconnect nodes
        
        Args:
            source: Source node
            target: Target node
            input_index: Specific input index (None for all)
            
        Returns:
            Success status
        """
        try:
            if input_index is not None:
                # Disconnect specific input
                if target.input(input_index) == source:
                    target.setInput(input_index, None)
                    logger.debug(f"Disconnected {source.name()} from {target.name()}[{input_index}]")
                    return True
            else:
                # Disconnect all connections from source to target
                disconnected = False
                for i in range(target.inputs()):
                    if target.input(i) == source:
                        target.setInput(i, None)
                        disconnected = True
                
                if disconnected:
                    logger.debug(f"Disconnected all connections from {source.name()} to {target.name()}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to disconnect nodes: {e}")
            return False
    
    def insert_node(self, existing_source: 'nuke.Node', 
                   new_node: 'nuke.Node',
                   existing_target: 'nuke.Node' = None,
                   input_index: int = 0) -> bool:
        """
        Insert a node between two existing nodes
        
        Args:
            existing_source: Original source node
            new_node: Node to insert
            existing_target: Original target node (None to insert before all dependents)
            input_index: Input index on existing_target
            
        Returns:
            Success status
        """
        try:
            if existing_target:
                # Insert between specific nodes
                if self.disconnect_nodes(existing_source, existing_target, input_index):
                    self.connect_nodes(existing_source, new_node, 0)
                    self.connect_nodes(new_node, existing_target, input_index)
                    return True
            else:
                # Insert before all dependents
                dependents = existing_source.dependent()
                connections_made = 0
                
                # Store original connections
                original_connections = []
                for dep in dependents:
                    for i in range(dep.inputs()):
                        if dep.input(i) == existing_source:
                            original_connections.append((dep, i))
                
                # Disconnect originals and reconnect through new node
                for dep, input_idx in original_connections:
                    self.disconnect_nodes(existing_source, dep, input_idx)
                    self.connect_nodes(new_node, dep, input_idx)
                
                # Connect source to new node
                self.connect_nodes(existing_source, new_node, 0)
                
                connections_made = len(original_connections)
                logger.debug(f"Inserted {new_node.name()} affecting {connections_made} connections")
                return connections_made > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to insert node: {e}")
            return False
    
    def reroute_connections(self, old_node: 'nuke.Node',
                          new_node: 'nuke.Node',
                          copy_connections: bool = True) -> bool:
        """
        Replace one node with another, rerouting connections
        
        Args:
            old_node: Node to replace
            new_node: Replacement node
            copy_connections: Copy input/output connections
            
        Returns:
            Success status
        """
        try:
            # Store connections
            input_connections = []
            for i in range(old_node.inputs()):
                input_node = old_node.input(i)
                if input_node:
                    input_connections.append((i, input_node))
            
            output_connections = defaultdict(list)
            dependents = old_node.dependent()
            for dep in dependents:
                for i in range(dep.inputs()):
                    if dep.input(i) == old_node:
                        output_connections[i].append(dep)
            
            # Copy connections if requested
            if copy_connections:
                # Copy input connections
                for input_idx, input_node in input_connections:
                    if input_idx < new_node.inputs():
                        self.connect_nodes(input_node, new_node, input_idx)
                
                # Copy output connections
                for output_idx, deps in output_connections.items():
                    for dep in deps:
                        for dep_input_idx in range(dep.inputs()):
                            if dep.input(dep_input_idx) == old_node:
                                self.connect_nodes(new_node, dep, dep_input_idx)
            
            logger.info(f"Rerouted connections from {old_node.name()} to {new_node.name()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reroute connections: {e}")
            return False
    
    def find_connection_path(self, start_node: 'nuke.Node',
                           end_node: 'nuke.Node',
                           max_depth: int = 100) -> Optional[List['nuke.Node']]:
        """
        Find path between two nodes
        
        Args:
            start_node: Starting node
            end_node: Target node
            max_depth: Maximum search depth
            
        Returns:
            List of nodes in path or None
        """
        try:
            # BFS search
            queue = deque([(start_node, [start_node])])
            visited = set([start_node])
            
            while queue:
                current, path = queue.popleft()
                
                if len(path) > max_depth:
                    continue
                
                if current == end_node:
                    return path
                
                # Check outputs
                for dep in current.dependent():
                    if dep not in visited:
                        visited.add(dep)
                        queue.append((dep, path + [dep]))
                
                # Check inputs
                for i in range(current.inputs()):
                    input_node = current.input(i)
                    if input_node and input_node not in visited:
                        visited.add(input_node)
                        queue.append((input_node, path + [input_node]))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find connection path: {e}")
            return None
    
    def get_upstream_nodes(self, node: 'nuke.Node',
                          include_self: bool = False) -> List['nuke.Node']:
        """
        Get all nodes upstream of a node
        
        Args:
            node: Starting node
            include_self: Include starting node in result
            
        Returns:
            List of upstream nodes
        """
        upstream = set()
        
        def traverse_upstream(current):
            for i in range(current.inputs()):
                input_node = current.input(i)
                if input_node and input_node not in upstream:
                    upstream.add(input_node)
                    traverse_upstream(input_node)
        
        traverse_upstream(node)
        
        if include_self:
            upstream.add(node)
        
        return list(upstream)
    
    def get_downstream_nodes(self, node: 'nuke.Node',
                           include_self: bool = False) -> List['nuke.Node']:
        """
        Get all nodes downstream of a node
        
        Args:
            node: Starting node
            include_self: Include starting node in result
            
        Returns:
            List of downstream nodes
        """
        downstream = set()
        
        def traverse_downstream(current):
            for dep in current.dependent():
                if dep not in downstream:
                    downstream.add(dep)
                    traverse_downstream(dep)
        
        traverse_downstream(node)
        
        if include_self:
            downstream.add(node)
        
        return list(downstream)
    
    def get_island_nodes(self, node: 'nuke.Node') -> List['nuke.Node']:
        """
        Get all nodes in the same island (connected component)
        
        Args:
            node: Starting node
            
        Returns:
            List of connected nodes
        """
        visited = set()
        
        def traverse(current):
            if current in visited:
                return
            visited.add(current)
            
            # Traverse inputs
            for i in range(current.inputs()):
                input_node = current.input(i)
                if input_node:
                    traverse(input_node)
            
            # Traverse outputs
            for dep in current.dependent():
                traverse(dep)
        
        traverse(node)
        return list(visited)
    
    def analyze_connection_graph(self) -> Dict:
        """
        Analyze the entire connection graph
        
        Returns:
            Graph analysis data
        """
        with TimerContext("analyze_connection_graph", logger):
            try:
                nodes = nuke.allNodes()
                graph = {
                    'total_nodes': len(nodes),
                    'connection_stats': defaultdict(int),
                    'node_degrees': {},
                    'islands': [],
                    'critical_paths': []
                }
                
                # Calculate node degrees
                for node in nodes:
                    indegree = sum(1 for i in range(node.inputs()) if node.input(i))
                    outdegree = len(node.dependent())
                    
                    graph['node_degrees'][node.name()] = {
                        'indegree': indegree,
                        'outdegree': outdegree,
                        'total': indegree + outdegree
                    }
                    
                    # Update connection stats
                    graph['connection_stats']['total_connections'] += indegree
                    if indegree == 0:
                        graph['connection_stats']['source_nodes'] += 1
                    if outdegree == 0:
                        graph['connection_stats']['sink_nodes'] += 1
                    if indegree > 1:
                        graph['connection_stats']['merge_points'] += 1
                    if outdegree > 1:
                        graph['connection_stats']['branch_points'] += 1
                
                # Find islands (connected components)
                visited = set()
                for node in nodes:
                    if node not in visited:
                        island = self.get_island_nodes(node)
                        graph['islands'].append({
                            'size': len(island),
                            'nodes': [n.name() for n in island]
                        })
                        visited.update(island)
                
                # Find critical paths (longest chains)
                graph['critical_paths'] = self._find_critical_paths(nodes)
                
                return graph
                
            except Exception as e:
                logger.error(f"Failed to analyze connection graph: {e}")
                return {}
    
    def _find_critical_paths(self, nodes: List['nuke.Node'], 
                           top_n: int = 5) -> List[Dict]:
        """Find the longest connection paths"""
        paths = []
        
        # Find source nodes (no inputs)
        source_nodes = [n for n in nodes if all(n.input(i) is None for i in range(n.inputs()))]
        
        for source in source_nodes:
            # DFS to find longest path from this source
            longest_path = self._find_longest_path_from(source, nodes)
            if longest_path:
                paths.append({
                    'length': len(longest_path),
                    'nodes': [n.name() for n in longest_path],
                    'source': source.name()
                })
        
        # Sort by length and return top N
        paths.sort(key=lambda x: x['length'], reverse=True)
        return paths[:top_n]
    
    def _find_longest_path_from(self, start: 'nuke.Node',
                              all_nodes: List['nuke.Node']) -> List['nuke.Node']:
        """Find longest path starting from a node"""
        longest = []
        
        def dfs(current, path):
            nonlocal longest
            current_path = path + [current]
            
            if len(current_path) > len(longest):
                longest = current_path.copy()
            
            # Continue with dependents
            for dep in current.dependent():
                if dep not in current_path:
                    dfs(dep, current_path)
        
        dfs(start, [])
        return longest

# Helper functions
def connect_nodes(source: 'nuke.Node', target: 'nuke.Node', **kwargs) -> bool:
    """Helper function to connect nodes"""
    manager = ConnectionManager()
    return manager.connect_nodes(source, target, **kwargs)

def insert_node(existing_source: 'nuke.Node', new_node: 'nuke.Node', **kwargs) -> bool:
    """Helper function to insert node"""
    manager = ConnectionManager()
    return manager.insert_node(existing_source, new_node, **kwargs)

def get_upstream_nodes(node: 'nuke.Node', **kwargs) -> List['nuke.Node']:
    """Helper function to get upstream nodes"""
    manager = ConnectionManager()
    return manager.get_upstream_nodes(node, **kwargs)

def analyze_connection_graph() -> Dict:
    """Helper function to analyze connection graph"""
    manager = ConnectionManager()
    return manager.analyze_connection_graph()