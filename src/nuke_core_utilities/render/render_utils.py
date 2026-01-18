"""
Render management and utilities
"""

import threading
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.env import get_env
from ..core.constants import *
from ..data.cache import cached_function

logger = get_logger(__name__)

class RenderManager:
    """Render management and utilities"""
    
    def __init__(self):
        self.env = get_env()
        self.active_renders = {}
        self.render_queue = []
        self.render_thread = None
    
    def render_node(self, node: 'nuke.Node',
                   frame_range: Tuple[int, int] = None,
                   views: List[str] = None,
                   proxy: bool = False,
                   continue_on_error: bool = False) -> Dict[str, Any]:
        """
        Render a node
        
        Args:
            node: Node to render (typically a Write node)
            frame_range: (first, last) frame range
            views: List of views to render
            proxy: Render proxy mode
            continue_on_error: Continue on render errors
            
        Returns:
            Render results
        """
        with TimerContext(f"render_{node.name()}", logger):
            try:
                # Validate node
                if node.Class() != 'Write':
                    return {
                        'success': False,
                        'error': f"Node {node.name()} is not a Write node"
                    }
                
                # Get frame range
                if frame_range is None:
                    frame_range = (
                        nuke.root()['first_frame'].value(),
                        nuke.root()['last_frame'].value()
                    )
                
                first_frame, last_frame = frame_range
                frame_count = last_frame - first_frame + 1
                
                # Get views
                if views is None:
                    views = nuke.views()
                
                # Prepare render info
                render_id = f"render_{node.name()}_{int(time.time())}"
                render_info = {
                    'id': render_id,
                    'node': node.name(),
                    'frame_range': frame_range,
                    'views': views,
                    'proxy': proxy,
                    'start_time': datetime.now().isoformat(),
                    'status': 'starting'
                }
                
                # Store in active renders
                self.active_renders[render_id] = render_info
                
                # Execute render
                try:
                    nuke.execute(
                        node,
                        first_frame,
                        last_frame,
                        views=views,
                        continueOnError=continue_on_error
                    )
                    
                    # Update status
                    render_info['status'] = 'completed'
                    render_info['end_time'] = datetime.now().isoformat()
                    render_info['success'] = True
                    
                    # Log completion
                    logger.info(f"Render completed: {node.name()} frames {first_frame}-{last_frame}")
                    
                    return render_info
                    
                except Exception as e:
                    # Update status
                    render_info['status'] = 'failed'
                    render_info['end_time'] = datetime.now().isoformat()
                    render_info['error'] = str(e)
                    render_info['success'] = False
                    
                    logger.error(f"Render failed: {node.name()} - {e}")
                    return render_info
                
            except Exception as e:
                logger.error(f"Failed to render node: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
    
    def render_multiple(self, nodes: List['nuke.Node'],
                       frame_ranges: List[Tuple[int, int]] = None,
                       continue_on_error: bool = False) -> List[Dict[str, Any]]:
        """
        Render multiple nodes
        
        Args:
            nodes: List of nodes to render
            frame_ranges: List of frame ranges for each node
            continue_on_error: Continue on render errors
            
        Returns:
            List of render results
        """
        results = []
        
        for i, node in enumerate(nodes):
            frame_range = None
            if frame_ranges and i < len(frame_ranges):
                frame_range = frame_ranges[i]
            
            result = self.render_node(
                node,
                frame_range=frame_range,
                continue_on_error=continue_on_error
            )
            results.append(result)
        
        return results
    
    def add_to_render_queue(self, node: 'nuke.Node',
                           frame_range: Tuple[int, int] = None,
                           priority: int = 0) -> str:
        """
        Add node to render queue
        
        Args:
            node: Node to render
            frame_range: Frame range
            priority: Render priority (higher = sooner)
            
        Returns:
            Queue item ID
        """
        try:
            item_id = f"queue_{len(self.render_queue)}_{int(time.time())}"
            
            queue_item = {
                'id': item_id,
                'node': node,
                'frame_range': frame_range,
                'priority': priority,
                'added_time': datetime.now().isoformat(),
                'status': 'queued'
            }
            
            self.render_queue.append(queue_item)
            
            # Sort by priority
            self.render_queue.sort(key=lambda x: x['priority'], reverse=True)
            
            logger.debug(f"Added {node.name()} to render queue (priority: {priority})")
            return item_id
            
        except Exception as e:
            logger.error(f"Failed to add to render queue: {e}")
            return ""
    

    def start_render_queue(self, max_concurrent: int = 1) -> bool:
        """
        Start processing render queue
        
        Args:
            max_concurrent: Maximum concurrent renders
            
        Returns:
            Success status
        """
        try:
            if self.render_thread and self.render_thread.is_alive():
                logger.warning("Render queue already running")
                return False
            
            # Start render thread
            self.render_thread = threading.Thread(
                target=self._process_render_queue,
                args=(max_concurrent,),
                daemon=True
            )
            self.render_thread.start()
            
            logger.info(f"Started render queue with max {max_concurrent} concurrent renders")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start render queue: {e}")
            return False
    
    def _process_render_queue(self, max_concurrent: int):
        """Process render queue in background thread"""
        while self.render_queue:
            # Get next item
            if not self.render_queue:
                time.sleep(1)
                continue
            
            item = self.render_queue.pop(0)
            item['status'] = 'processing'
            item['start_time'] = datetime.now().isoformat()
            
            # Render the item
            try:
                result = self.render_node(
                    item['node'],
                    frame_range=item['frame_range']
                )
                
                item['result'] = result
                item['status'] = 'completed' if result.get('success') else 'failed'
                item['end_time'] = datetime.now().isoformat()
                
            except Exception as e:
                item['result'] = {'error': str(e)}
                item['status'] = 'failed'
                item['end_time'] = datetime.now().isoformat()
            
            # Wait before next render if at max concurrent
            active_count = sum(1 for r in self.active_renders.values() 
                             if r.get('status') == 'processing')
            if active_count >= max_concurrent:
                time.sleep(5)
    
    def stop_render_queue(self) -> bool:
        """Stop render queue"""
        try:
            if self.render_thread:
                # Clear queue
                self.render_queue.clear()
                
                # Wait for thread to finish
                self.render_thread.join(timeout=5)
                
                logger.info("Stopped render queue")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop render queue: {e}")
            return False
    
    def get_render_status(self, render_id: str = None) -> Dict[str, Any]:
        """
        Get render status
        
        Args:
            render_id: Specific render ID (None for all)
            
        Returns:
            Render status information
        """
        try:
            if render_id:
                return self.active_renders.get(render_id, {})
            else:
                return {
                    'active': self.active_renders,
                    'queued': self.render_queue,
                    'stats': self._get_render_stats()
                }
        except Exception as e:
            logger.error(f"Failed to get render status: {e}")
            return {}
    
    def _get_render_stats(self) -> Dict[str, Any]:
        """Get render statistics"""
        stats = {
            'active_count': len(self.active_renders),
            'queued_count': len(self.render_queue),
            'completed_count': 0,
            'failed_count': 0,
            'total_frames': 0
        }
        
        for render in self.active_renders.values():
            if render.get('status') == 'completed':
                stats['completed_count'] += 1
            elif render.get('status') == 'failed':
                stats['failed_count'] += 1
            
            # Count frames
            frame_range = render.get('frame_range')
            if frame_range:
                stats['total_frames'] += frame_range[1] - frame_range[0] + 1
        
        return stats
    
    def estimate_render_time(self, node: 'nuke.Node',
                           frame_range: Tuple[int, int] = None) -> Dict[str, Any]:
        """
        Estimate render time for a node
        
        Args:
            node: Node to estimate
            frame_range: Frame range
            
        Returns:
            Time estimate
        """
        try:
            if frame_range is None:
                frame_range = (
                    nuke.root()['first_frame'].value(),
                    nuke.root()['last_frame'].value()
                )
            
            first_frame, last_frame = frame_range
            frame_count = last_frame - first_frame + 1
            
            # Sample a few frames for timing
            sample_frames = min(5, frame_count)
            sample_step = max(1, frame_count // sample_frames)
            
            sample_times = []
            
            for i in range(0, frame_count, sample_step):
                if i >= sample_frames:
                    break
                
                sample_frame = first_frame + i
                start_time = time.time()
                
                try:
                    nuke.execute(node, sample_frame, sample_frame)
                    sample_time = time.time() - start_time
                    sample_times.append(sample_time)
                except:
                    pass
            
            if not sample_times:
                return {'error': 'Could not sample frames'}
            
            # Calculate estimates
            avg_time = sum(sample_times) / len(sample_times)
            total_estimate = avg_time * frame_count
            
            return {
                'frame_count': frame_count,
                'average_frame_time': avg_time,
                'total_estimate_seconds': total_estimate,
                'total_estimate_hours': total_estimate / 3600,
                'sample_frames': len(sample_times),
                'confidence': min(1.0, len(sample_times) / 5.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to estimate render time: {e}")
            return {'error': str(e)}
    
    def monitor_disk_space(self, required_gb: float = 10.0) -> Dict[str, Any]:
        """
        Monitor disk space for renders
        
        Args:
            required_gb: Required space in GB
            
        Returns:
            Disk space information
        """
        try:
            import shutil
            
            # Get temp directory
            temp_dir = self.env.get_nuke_temp_dir()
            
            # Check disk space
            total, used, free = shutil.disk_usage(temp_dir)
            
            free_gb = free / (1024**3)
            required_bytes = required_gb * (1024**3)
            
            status = {
                'temp_directory': temp_dir,
                'total_gb': total / (1024**3),
                'used_gb': used / (1024**3),
                'free_gb': free_gb,
                'required_gb': required_gb,
                'has_space': free >= required_bytes,
                'warning': free_gb < required_gb * 2  # Warn if less than 2x required
            }
            
            if not status['has_space']:
                logger.warning(f"Insufficient disk space: {free_gb:.1f}GB free, {required_gb}GB required")
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to monitor disk space: {e}")
            return {'error': str(e)}

# Helper functions
def render_node(node: 'nuke.Node', **kwargs) -> Dict[str, Any]:
    """Helper function to render node"""
    manager = RenderManager()
    return manager.render_node(node, **kwargs)

def estimate_render_time(node: 'nuke.Node', **kwargs) -> Dict[str, Any]:
    """Helper function to estimate render time"""
    manager = RenderManager()
    return manager.estimate_render_time(node, **kwargs)