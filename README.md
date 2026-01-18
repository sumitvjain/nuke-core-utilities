Nuke Core Utilities
A comprehensive toolkit for Nuke pipeline development and automation, designed for developers and TDs.

📦 Overview
Nuke Core Utilities provides a modular, production-ready framework for building Nuke pipeline tools. It includes everything from environment management and logging to node manipulation, graph analysis, and render management.

🚀 Quick Start
Installation
Clone the repository:

bash
git clone https://github.com/your-org/nuke-core-utilities.git
Add to your Nuke path:

bash
export NUKE_PATH=/path/to/nuke-core-utilities/src:$NUKE_PATH
Or install as Python package:

bash
cd nuke-core-utilities
pip install -e .
Basic Usage
python
import nuke_core_utilities as ncu

# Initialize environment
env = ncu.get_env()
env.print_system_info()

# Get logger
logger = ncu.get_logger()
logger.info("Nuke Core Utilities loaded")

# Create a node with custom settings
node = ncu.create_node("Grade", name="Grade_Main", position=(100, 100))

# Analyze graph connections
graph_info = ncu.analyze_connection_graph()
print(f"Graph has {graph_info['total_nodes']} nodes")

# Render management
render_manager = ncu.RenderManager()
render_manager.render_node(write_node)
📁 Project Structure
text
NUKE-CORE-UTILITIES/
├── src/
│   └── nuke_core_utilities/
│       ├── core/              # Core infrastructure
│       │   ├── __init__.py
│       │   ├── constants.py   # All constants
│       │   ├── env.py         # Environment management
│       │   └── logging_utils.py # Advanced logging
│       │
│       ├── data/              # Data handling
│       │   ├── __init__.py
│       │   ├── cache.py       # Caching system
│       │   ├── metadata.py    # Metadata management
│       │   └── read_write.py  # File operations
│       │
│       ├── graph/             # Graph operations
│       │   ├── __init__.py
│       │   ├── connections.py # Connection management
│       │   ├── layout.py      # Graph layout
│       │   └── traversal.py   # Graph traversal
│       │
│       ├── nodes/             # Node operations
│       │   ├── __init__.py
│       │   ├── create.py      # Node creation
│       │   ├── delete.py      # Node deletion
│       │   ├── modify.py      # Node modification
│       │   └── query.py       # Node querying
│       │
│       ├── project/           # Project management
│       │   ├── __init__.py
│       │   ├── context.py     # Project context
│       │   ├── paths.py       # Path management
│       │   └── versions.py    # Version control
│       │
│       ├── render/            # Render utilities
│       │   ├── __init__.py
│       │   ├── render_utils.py # Render management
│       │   └── write_nodes.py  # Write node utilities
│       │
│       ├── selection/         # Selection tools
│       │   ├── __init__.py
│       │   └── selection.py   # Selection management
│       │
│       └── utils/             # Utility functions
│           ├── __init__.py
│           ├── knobs.py       # Knob utilities
│           ├── validation.py  # Validation tools
│           ├── callbacks.py   # Callback system
│           └── isolate.py     # Isolation tools
│
├── tests/                    # Unit tests
├── examples/                 # Example scripts
├── docs/                     # Documentation
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup
└── README.md                 # This file
✨ Key Features
🎯 Core Infrastructure
Environment Management: Automatic system detection and configuration

Structured Logging: JSON logging, Nuke Script Editor integration, performance tracking

Configuration: Centralized constants and settings management

🔧 Node Operations
Smart Creation: Templates, grids, groups, and backdrops

Safe Deletion: Connection cleanup, backups, and validation

Advanced Modification: Alignment, distribution, coloring, and transformations

Powerful Querying: Multi-criteria search, statistics, and comparison

🕸️ Graph Management
Connection Analysis: Cycle detection, path finding, dependency graphs

Automatic Layout: Hierarchical, radial, and grid layouts

Traversal Algorithms: BFS, DFS, topological sort, connected components

📊 Data Management
Intelligent Caching: TTL-based caching with persistence

Metadata System: Custom knob management and script metadata

File Operations: Script import/export with compression and backup

🎬 Pipeline Tools
Project Context: Show/shot/task management and session tracking

Path Resolution: Template-based path resolution and validation

Version Control: Automatic versioning, comparison, and restoration

🎞️ Render Pipeline
Render Management: Queue system, concurrent renders, status tracking

Write Node Templates: Preconfigured output formats (EXR, JPEG, MOV, etc.)

Performance: Time estimation, disk space monitoring, optimization

🛠️ Utilities
Validation: Script and node validation with error reporting

Knob Management: Creation, copying, animation handling

Event System: Callback management for Nuke events

Isolation Tools: Focus and isolation for complex graphs

📚 API Reference
Core Functions
Environment
python
from nuke_core_utilities import get_env

env = get_env()
env.print_system_info()                    # Print system information
env.get_nuke_version()                     # Get Nuke version
env.get_ocio_config()                      # Get OCIO config path
env.create_environment_report()            # Generate detailed report
Logging
python
from nuke_core_utilities import get_logger

logger = get_logger()
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.log_performance("Operation", 2.5)   # Log performance metrics
Node Operations
Creation
python
from nuke_core_utilities import create_node, create_backdrop, create_node_group

# Create nodes
node = create_node("Grade", name="Grade1", position=(100, 100))
backdrop = create_backdrop(label="Color Correction", color=0xFF0000FF)
group = create_node_group(name="CompGroup")

# Create from templates
from nuke_core_utilities.nodes.create import NodeCreator
creator = NodeCreator()
nodes = creator.create_template("color_correction", position=(0, 0))
Querying
python
from nuke_core_utilities import find_nodes_by_type, get_node_info

# Find nodes
grade_nodes = find_nodes_by_type(["Grade", "ColorCorrect"])

# Get detailed information
node_info = get_node_info(node)
print(f"Node class: {node_info['basic']['class']}")
print(f"Position: {node_info['basic']['position']}")

# Script statistics
from nuke_core_utilities.nodes.query import NodeQuery
query = NodeQuery()
stats = query.get_script_statistics()
Modification
python
from nuke_core_utilities import set_node_color, align_nodes, rename_nodes

# Color nodes by type
from nuke_core_utilities.nodes.modify import NodeModifier
modifier = NodeModifier()
modifier.color_nodes_by_type()

# Align and distribute
align_nodes(alignment='left', spacing=20)
modifier.distribute_nodes(direction='horizontal', spacing=100)

# Rename with pattern
rename_map = rename_nodes(pattern="{class}_{index:03d}")
Graph Operations
Connections
python
from nuke_core_utilities import connect_nodes, get_upstream_nodes, analyze_connection_graph

# Manage connections
connect_nodes(source_node, target_node, input_index=0)

# Analyze graph
graph_info = analyze_connection_graph()
print(f"Total connections: {graph_info['connection_stats']['total_connections']}")

# Find dependencies
upstream = get_upstream_nodes(node, include_self=True)
Traversal
python
from nuke_core_utilities import topological_sort, find_cycles, get_execution_order

# Sort nodes by dependency
ordered_nodes = topological_sort()

# Find cycles
cycles = find_cycles()
if cycles:
    print(f"Found {len(cycles)} cycles in graph")

# Get execution order
execution_order = get_execution_order()
Project Management
Context
python
from nuke_core_utilities import get_project_context

context = get_project_context()
context.set_context_value("show", "MYSHOW")
context.set_context_value("shot", "sh010")
context.save_context()  # Save to file
Paths
python
from nuke_core_utilities import resolve_path, ensure_path

# Resolve paths using templates
comp_path = resolve_path("shot_comp", {"task": "comp"})
render_path = resolve_path("shot_render", {"task": "main"})

# Ensure directories exist
success, path = ensure_path("shot_comp")
Versions
python
from nuke_core_utilities import get_current_version, increment_version, get_version_history

# Version management
current_version = get_current_version()
new_version, new_path = increment_version(save_copy=True)

# History
history = get_version_history()
for version_info in history:
    print(f"Version {version_info['version']}: {version_info['filepath']}")
Render Management
Render Control
python
from nuke_core_utilities import render_node, estimate_render_time

# Render with options
render_info = render_node(
    write_node,
    frame_range=(1, 100),
    views=["left", "right"],
    continue_on_error=True
)

# Estimate render time
estimate = estimate_render_time(write_node)
print(f"Estimated render time: {estimate['total_estimate_hours']:.2f} hours")
Write Nodes
python
from nuke_core_utilities import create_write_node, validate_write_nodes

# Create write nodes from templates
write_node = create_write_node(
    template="exr_16bit",
    name="Write_EXR",
    filepath="/output/render.exr"
)

# Validate write nodes
validation = validate_write_nodes()
if validation['errors']:
    for error in validation['errors']:
        print(f"Error: {error}")
Utilities
Validation
python
from nuke_core_utilities import validate_nuke_script, validate_node

# Validate entire script
results = validate_nuke_script()
if not results['valid']:
    for error in results['errors']:
        print(f"ERROR: {error}")

# Validate specific node
node_validation = validate_node(node)
Knobs
python
from nuke_core_utilities import get_knob_info, set_knob_value, copy_knobs

# Get knob information
knob_info = get_knob_info(node, "mix")
print(f"Knob value: {knob_info['value']}")

# Set knob with animation
set_knob_value(node, "mix", 0.5, animated=True)

# Copy knobs between nodes
copy_knobs(source_node, target_node, copy_animations=True)
Selection
python
from nuke_core_utilities import select_by_criteria, select_connected, clear_selection

# Select by criteria
selected = select_by_criteria({
    "class": ["Grade", "ColorCorrect"],
    "min_inputs": 1,
    "color": 0xFF0000FF
})

# Select connected nodes
connected = select_connected(direction="both", include_self=False)

# Clear selection
clear_selection()
🧪 Examples
Example 1: Batch Node Processing
python
import nuke_core_utilities as ncu

# Find all Grade nodes
grade_nodes = ncu.find_nodes_by_type(["Grade"])

# Process each node
for node in grade_nodes:
    # Add metadata
    ncu.set_knob_value(node, "metadata_artist", "John Doe")
    
    # Color code by user
    ncu.set_node_color(node, 0x00FF00FF)
    
    # Log operation
    ncu.get_logger().log_node_operation("processed", node.name())
Example 2: Script Analysis Tool
python
import nuke_core_utilities as ncu
import json

# Analyze script
graph_info = ncu.analyze_connection_graph()
script_stats = ncu.get_script_statistics()
validation = ncu.validate_nuke_script()

# Generate report
report = {
    "graph_analysis": graph_info,
    "statistics": script_stats,
    "validation": validation,
    "environment": ncu.get_env().get_system_info()
}

# Save report
with open("script_analysis.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print(f"Script analysis saved with {len(graph_info['islands'])} islands")
Example 3: Automated Render Pipeline
python
import nuke_core_utilities as ncu
from datetime import datetime

# Setup render manager
render_manager = ncu.RenderManager()

# Get all write nodes
write_nodes = ncu.find_nodes_by_type(["Write"])

# Add to render queue
for write_node in write_nodes:
    render_manager.add_to_render_queue(
        write_node,
        frame_range=(1, 100),
        priority=1 if "main" in write_node.name() else 0
    )

# Start rendering
render_manager.start_render_queue(max_concurrent=2)

# Monitor progress
while render_manager.render_queue:
    status = render_manager.get_render_status()
    print(f"Active: {status['stats']['active_count']}, "
          f"Queued: {status['stats']['queued_count']}, "
          f"Completed: {status['stats']['completed_count']}")
    import time
    time.sleep(5)
Example 4: Project Setup
python
import nuke_core_utilities as ncu

# Initialize project
context = ncu.get_project_context()
context.set_context_value("show", "MYSHOW")
context.set_context_value("shot", "sh010")
context.set_context_value("task", "comp")

# Setup project paths
paths = ncu.ProjectPaths()
paths.ensure_path("shot_comp")
paths.ensure_path("shot_render")
paths.ensure_path("shot_plate")

# Create standard nodes
ncu.create_write_node(
    template="exr_16bit",
    name="Write_Main",
    filepath=paths.resolve_path("shot_render") + "/render.exr"
)

# Save context
context.save_context("project_context.json")
🔧 Configuration
Environment Variables
bash
# Required
export PROJECT_ROOT="/path/to/project"
export SHOW="myshow"
export SHOT="sh010"

# Optional
export NUKE_PATH="/custom/nuke/path"
export NUKE_TEMP_DIR="/custom/temp"
export NUKE_DEBUG="true"
export NUKE_PRODUCTION="false"
Logging Configuration
python
from nuke_core_utilities import setup_logging

# Configure logging
setup_logging(
    level="INFO",          # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_console=True,   # Output to Nuke Script Editor
    log_to_file=True       # Output to log files
)
🧪 Testing
Run the test suite:

bash
cd nuke-core-utilities
python -m pytest tests/ -v
Run specific test module:

bash
python -m pytest tests/test_nodes.py -v
📖 Documentation
API Reference - Complete API documentation

Examples - Practical usage examples

Best Practices - Development guidelines

🤝 Contributing
Fork the repository

Create a feature branch (git checkout -b feature/amazing-feature)

Commit changes (git commit -m 'Add amazing feature')

Push to branch (git push origin feature/amazing-feature)

Open a Pull Request

Development Setup
bash
# Clone and setup
git clone https://github.com/your-org/nuke-core-utilities.git
cd nuke-core-utilities

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Generate documentation
cd docs && make html
📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🆘 Support
📚 Documentation

🐛 Issue Tracker

💬 Discussions

📈 Roadmap
GPU acceleration utilities

Machine learning integration

Cloud rendering support

USD integration enhancements

Real-time collaboration tools

🙏 Acknowledgments
The Foundry for Nuke

OpenColorIO community

All contributors and users

Built with ❤️ for the VFX community