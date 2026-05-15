# Semantic Map Navigation System - Usage Guide

## Overview
This package provides a complete semantic map construction and target navigation system for ROS1.

## Package Structure
```
semantic_map/
├── srv/                    # ROS service definitions
├── scripts/               # Python nodes
├── launch/               # Launch files
├── config/               # RViz configuration
└── data/                 # Persistent storage
```

## Nodes

### 1. semantic_tag_manager
- **Function**: Manages semantic tags (add/query/delete/list)
- **Services**:
  - `/semantic_map/add_tag` - Add new semantic tag
  - `/semantic_map/query_tag` - Query tag by name
  - `/semantic_map/delete_tag` - Delete tag by name
  - `/semantic_map/list_tags` - List all tags
- **Topics**:
  - `/semantic_map/tags` - Broadcasts all tags (latched)

### 2. semantic_navigator
- **Function**: Navigation to semantic tags using move_base
- **Services**:
  - `/semantic_map/navigate_to_tag` - Navigate to tag by name

### 3. semantic_visualizer
- **Function**: RViz visualization of semantic tags
- **Topics**:
  - `/semantic_map/markers` - MarkerArray for visualization

## Tag Types
- `charging_station` - Blue color with ⚡ icon
- `entrance` - Green color with 🚪 icon
- `danger_zone` - Red color with ⚠️ icon
- `goal` - Yellow color with 🎯 icon
- `default` - Orange color with 📍 icon

## Quick Start

### 1. Build the package
```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

### 2. Launch semantic map nodes
```bash
roslaunch semantic_map semantic_map.launch
```

### 3. Launch with RViz
```bash
roslaunch semantic_map semantic_map_with_rviz.launch
```

### 4. Launch full system with map_server
```bash
roslaunch semantic_map full_system.launch map_file:=/path/to/your/map.yaml
```

## Service Usage Examples

### Add Semantic Tag
```bash
rosservice call /semantic_map/add_tag "name: 'charging_station_1'
x: 2.0
y: 3.0
yaw: 0.0
tag_type: 'charging_station'
description: 'Main charging station'"
```

### Query Semantic Tag
```bash
rosservice call /semantic_map/query_tag "name: 'charging_station_1'"
```

### Delete Semantic Tag
```bash
rosservice call /semantic_map/delete_tag "name: 'charging_station_1'"
```

### List All Tags
```bash
rosservice call /semantic_map/list_tags "tag_type: ''"
```

### List Tags by Type
```bash
rosservice call /semantic_map/list_tags "tag_type: 'charging_station'"
```

### Navigate to Tag
```bash
rosservice call /semantic_map/navigate_to_tag "tag_name: 'charging_station_1'"
```

## Testing

Run the test script:
```bash
rosrun semantic_map test_semantic_map.py
```

## Configuration

### Node Parameters

#### semantic_tag_manager
- `data_dir` (string, default: `$(find semantic_map)/data`) - Directory for persistent storage

#### semantic_navigator
- `navigation_timeout` (double, default: 300.0) - Navigation timeout in seconds

## Persistent Storage
Semantic tags are automatically saved to `semantic_tags.json` in the data directory on shutdown and loaded on startup.

## Dependencies
- rospy
- std_msgs
- geometry_msgs
- move_base_msgs
- visualization_msgs
- std_srvs

## Integration

### With map_server
```bash
rosrun map_server map_server /path/to/map.yaml
roslaunch semantic_map semantic_map.launch
```

### With move_base
Ensure move_base is running before starting semantic_navigator:
```bash
roslaunch your_robot move_base.launch
roslaunch semantic_map semantic_map.launch
```

## Troubleshooting

1. **Service not available**: Ensure all nodes are running
2. **Navigation fails**: Check if move_base is running and map is loaded
3. **Visualization not showing**: Check RViz topic subscription to `/semantic_map/markers`
4. **Data not persisting**: Check write permissions for the data directory