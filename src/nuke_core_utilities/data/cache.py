"""
Cache management for Nuke operations
"""

import json
import pickle
import hashlib
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from functools import wraps
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.env import get_env

logger = get_logger(__name__)

class CacheEntry:
    """Single cache entry"""
    
    def __init__(self, key: str, value: Any, 
                 ttl: int = None, created_at: float = None):
        self.key = key
        self.value = value
        self.ttl = ttl  # Time to live in seconds
        self.created_at = created_at or time.time()
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl
    
    def access(self):
        """Mark entry as accessed"""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'key': self.key,
            'value': self.value,
            'ttl': self.ttl,
            'created_at': self.created_at,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed
        }

class NukeCache:
    """Cache manager for Nuke operations"""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            print("cls._instance ---- ", cls._instance)
        print("cls._instance ===== ", cls._instance)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        with self._lock:
            self.cache: Dict[str, CacheEntry] = {}
            self.max_size = 1000  # Maximum entries
            self.default_ttl = 3600  # 1 hour default TTL
            self.hits = 0
            self.misses = 0
            
            # Get cache directory from environment
            env = "get_env"()
            cache_dir = env.get_path('project_temp', Path.home() / '.nuke_cache')
            self.cache_dir = Path(cache_dir) / 'data_cache'
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Persistent storage
            self.persistent_file = self.cache_dir / 'cache_data.pkl'
            self._load_persistent()
            
            # Start cleanup thread
            self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self._cleanup_thread.start()
            
            self._initialized = True
            
            logger.info(f"Cache initialized at {self.cache_dir}")
    
    def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            time.sleep(60)  # Check every minute
            self.cleanup_expired()
            
            # Save to disk every 5 minutes
            if int(time.time()) % 300 == 0:
                self._save_persistent()
    
    def _load_persistent(self):
        """Load persistent cache from disk"""
        try:
            if self.persistent_file.exists():
                with open(self.persistent_file, 'rb') as f:
                    data = pickle.load(f)
                    self.cache = {
                        k: CacheEntry(**v) 
                        for k, v in data.get('cache', {}).items()
                    }
                    self.hits = data.get('hits', 0)
                    self.misses = data.get('misses', 0)
                logger.debug(f"Loaded {len(self.cache)} cache entries from disk")
        except Exception as e:
            logger.warning(f"Failed to load cache from disk: {e}")
    
    def _save_persistent(self):
        """Save cache to disk"""
        try:
            data = {
                'cache': {k: v.to_dict() for k, v in self.cache.items()},
                'hits': self.hits,
                'misses': self.misses,
                'timestamp': time.time()
            }
            
            # Save to temp file first
            temp_file = self.persistent_file.with_suffix('.tmp')
            with open(temp_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Replace original
            temp_file.replace(self.persistent_file)
            
            logger.debug(f"Saved {len(self.cache)} cache entries to disk")
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")
    
    def generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        # Create string representation
        key_parts = []
        
        # Add positional args
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword args
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        # Create hash
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                
                if entry.is_expired():
                    # Remove expired entry
                    del self.cache[key]
                    self.misses += 1
                    return default
                
                entry.access()
                self.hits += 1
                return entry.value
            else:
                self.misses += 1
                return default
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        with self._lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].last_accessed
                )
                del self.cache[oldest_key]
            
            if ttl is None:
                ttl = self.default_ttl
            
            entry = CacheEntry(key, value, ttl)
            self.cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        with self._lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                'size': len(self.cache),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'max_size': self.max_size,
                'default_ttl': self.default_ttl
            }
    
    def cache_node_data(self, node: 'nuke.Node', data: Any, ttl: int = None):
        """Cache data associated with a node"""
        if node is None:
            return
        
        key = f"node:{node.name()}:{hashlib.md5(str(data).encode()).hexdigest()}"
        self.set(key, data, ttl)
    
    def get_node_data(self, node: 'nuke.Node', default: Any = None) -> Any:
        """Get cached data for a node"""
        if node is None:
            return default
        
        # Try to find any cached data for this node
        with self._lock:
            for key in list(self.cache.keys()):
                if key.startswith(f"node:{node.name()}:"):
                    entry = self.cache[key]
                    if not entry.is_expired():
                        entry.access()
                        return entry.value
        
        return default
    
    def cache_script_state(self, script_path: str = None):
        """Cache current script state"""
        if script_path is None:
            try:
                script_path = nuke.root().name()
            except:
                script_path = "unsaved"
        
        key = f"script_state:{script_path}:{time.time()}"
        
        # Collect script data
        script_data = {
            'nodes': [],
            'connections': [],
            'settings': {}
        }
        
        try:
            # Cache node states
            for node in nuke.allNodes():
                node_data = {
                    'name': node.name(),
                    'class': node.Class(),
                    'position': (node.xpos(), node.ypos()),
                    'knobs': {}
                }
                script_data['nodes'].append(node_data)
            
            self.set(key, script_data, ttl=1800)  # 30 minutes
            logger.debug(f"Cached script state: {script_path}")
        except Exception as e:
            logger.error(f"Failed to cache script state: {e}")
    
    def flush_to_disk(self):
        """Force save cache to disk"""
        self._save_persistent()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.flush_to_disk()

# Function cache decorator
def cached_function(ttl: int = 3600, cache_instance: NukeCache = None):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = cache_instance or NukeCache()
            
            # Generate cache key
            key_parts = [func.__module__, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key_string = ":".join(key_parts)
            key = hashlib.md5(key_string.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, cached result")
            
            return result
        return wrapper
    return decorator

# Node-specific cache decorator
def cached_node_operation(ttl: int = 1800):
    """Decorator for caching node operation results"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(node: 'nuke.Node', *args, **kwargs):
            cache = NukeCache()
            
            if node is None:
                return func(node, *args, **kwargs)
            
            # Generate key based on node state and operation
            node_state = {
                'name': node.name(),
                'class': node.Class(),
                'knobs': {}
            }
            
            # Add relevant knob values
            for knob_name in ['tile_color', 'disable', 'hide_input']:
                knob = node.knob(knob_name)
                if knob:
                    node_state['knobs'][knob_name] = knob.value()
            
            key_data = {
                'function': func.__name__,
                'node': node_state,
                'args': args,
                'kwargs': kwargs
            }
            
            key = hashlib.md5(str(key_data).encode()).hexdigest()
            cache_key = f"node_op:{node.name()}:{key}"
            
            # Try cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute and cache
            with TimerContext(f"node_operation_{func.__name__}", logger):
                result = func(node, *args, **kwargs)
            
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Global cache instance
def get_cache() -> NukeCache:
    """Get global cache instance"""
    return NukeCache()