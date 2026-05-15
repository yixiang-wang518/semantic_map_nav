#!/usr/bin/env python3
import rospy
import json
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point

class SemanticVisualizer:
    def __init__(self):
        rospy.init_node('semantic_visualizer', anonymous=False)
        
        self.marker_pub = rospy.Publisher('/semantic_map/markers', MarkerArray, queue_size=10)
        
        self.tags_sub = rospy.Subscriber('/semantic_map/tags', String, self.handle_tags_update)
        
        self.tag_colors = {
            'charging_station': {'r': 0.0, 'g': 0.5, 'b': 1.0, 'a': 1.0},
            'entrance': {'r': 0.0, 'g': 1.0, 'b': 0.0, 'a': 1.0},
            'danger_zone': {'r': 1.0, 'g': 0.0, 'b': 0.0, 'a': 1.0},
            'goal': {'r': 1.0, 'g': 1.0, 'b': 0.0, 'a': 1.0},
            'default': {'r': 1.0, 'g': 0.8, 'b': 0.0, 'a': 1.0}
        }
        
        self.tag_icons = {
            'charging_station': '⚡',
            'entrance': '🚪',
            'danger_zone': '⚠️',
            'goal': '🎯',
            'default': '📍'
        }
        
        rospy.loginfo("Semantic Visualizer node started")
    
    def handle_tags_update(self, msg):
        try:
            tags = json.loads(msg.data)
            self.publish_markers(tags)
        except Exception as e:
            rospy.logerr(f"Failed to parse tags: {e}")
    
    def publish_markers(self, tags):
        marker_array = MarkerArray()
        marker_id = 0
        
        for tag_name, tag_data in tags.items():
            tag_type = tag_data.get('tag_type', 'default')
            
            position_marker = Marker()
            position_marker.header.frame_id = "map"
            position_marker.header.stamp = rospy.Time.now()
            position_marker.ns = "semantic_tags"
            position_marker.id = marker_id
            position_marker.type = Marker.SPHERE
            position_marker.action = Marker.ADD
            
            position_marker.pose.position.x = tag_data['x']
            position_marker.pose.position.y = tag_data['y']
            position_marker.pose.position.z = 0.0
            position_marker.pose.orientation.w = 1.0
            
            color = self.tag_colors.get(tag_type, self.tag_colors['default'])
            position_marker.color.r = color['r']
            position_marker.color.g = color['g']
            position_marker.color.b = color['b']
            position_marker.color.a = color['a']
            
            position_marker.scale.x = 0.3
            position_marker.scale.y = 0.3
            position_marker.scale.z = 0.1
            
            marker_array.markers.append(position_marker)
            marker_id += 1
            
            arrow_marker = Marker()
            arrow_marker.header.frame_id = "map"
            arrow_marker.header.stamp = rospy.Time.now()
            arrow_marker.ns = "semantic_tags"
            arrow_marker.id = marker_id
            arrow_marker.type = Marker.ARROW
            arrow_marker.action = Marker.ADD
            
            arrow_marker.pose.position.x = tag_data['x']
            arrow_marker.pose.position.y = tag_data['y']
            arrow_marker.pose.position.z = 0.05
            
            import math
            yaw = tag_data.get('yaw', 0.0)
            arrow_marker.pose.orientation.z = math.sin(yaw / 2.0)
            arrow_marker.pose.orientation.w = math.cos(yaw / 2.0)
            
            arrow_marker.color.r = color['r']
            arrow_marker.color.g = color['g']
            arrow_marker.color.b = color['b']
            arrow_marker.color.a = color['a']
            
            arrow_marker.scale.x = 0.5
            arrow_marker.scale.y = 0.1
            arrow_marker.scale.z = 0.1
            
            marker_array.markers.append(arrow_marker)
            marker_id += 1
            
            text_marker = Marker()
            text_marker.header.frame_id = "map"
            text_marker.header.stamp = rospy.Time.now()
            text_marker.ns = "semantic_tags"
            text_marker.id = marker_id
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            
            text_marker.pose.position.x = tag_data['x']
            text_marker.pose.position.y = tag_data['y'] + 0.4
            text_marker.pose.position.z = 0.1
            text_marker.pose.orientation.w = 1.0
            
            icon = self.tag_icons.get(tag_type, self.tag_icons['default'])
            text_marker.text = f"{icon} {tag_name}"
            
            text_marker.color.r = color['r']
            text_marker.color.g = color['g']
            text_marker.color.b = color['b']
            text_marker.color.a = color['a']
            
            text_marker.scale.z = 0.25
            
            marker_array.markers.append(text_marker)
            marker_id += 1
        
        self.marker_pub.publish(marker_array)
        rospy.loginfo(f"Published {len(marker_array.markers)} markers for {len(tags)} tags")

if __name__ == '__main__':
    try:
        visualizer = SemanticVisualizer()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Semantic Visualizer node interrupted")