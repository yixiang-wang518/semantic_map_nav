#!/usr/bin/env python3
import rospy
import json
import os
import threading
from std_msgs.msg import String
from semantic_map.srv import AddSemanticTag, AddSemanticTagResponse
from semantic_map.srv import QuerySemanticTag, QuerySemanticTagResponse
from semantic_map.srv import DeleteSemanticTag, DeleteSemanticTagResponse
from semantic_map.srv import ListSemanticTags, ListSemanticTagsResponse

class SemanticTagManager:
    def __init__(self):
        rospy.init_node('semantic_tag_manager', anonymous=False)
        
        self.data_dir = rospy.get_param('~data_dir', os.path.join(os.path.dirname(__file__), '../data'))
        self.data_file = rospy.get_param('~data_file', os.path.join(self.data_dir, 'semantic_tags.json'))
        self.auto_save_interval = rospy.get_param('~auto_save_interval', 30)
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        self.tags = {}
        self.lock = threading.Lock()
        self.save_timer = None
        
        self.load_tags()
        
        self.add_tag_service = rospy.Service('/semantic_map/add_tag', AddSemanticTag, self.handle_add_tag)
        self.query_tag_service = rospy.Service('/semantic_map/query_tag', QuerySemanticTag, self.handle_query_tag)
        self.delete_tag_service = rospy.Service('/semantic_map/delete_tag', DeleteSemanticTag, self.handle_delete_tag)
        self.list_tags_service = rospy.Service('/semantic_map/list_tags', ListSemanticTags, self.handle_list_tags)
        
        self.tags_publisher = rospy.Publisher('/semantic_map/tags', String, queue_size=10, latch=True)
        
        rospy.on_shutdown(self.shutdown_handler)
        
        if self.auto_save_interval > 0:
            self.start_auto_save()
        
        self.broadcast_tags()
        
        rospy.loginfo("Semantic Tag Manager node started")
        rospy.loginfo(f"Auto-save interval: {self.auto_save_interval}s")
        
    def start_auto_save(self):
        self.save_timer = rospy.Timer(rospy.Duration(self.auto_save_interval), self.auto_save_callback)
    
    def auto_save_callback(self, event):
        self.save_tags()
    
    def shutdown_handler(self):
        if self.save_timer:
            self.save_timer.shutdown()
        self.save_tags()
    
    def load_tags(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.tags = json.load(f)
                rospy.loginfo(f"Loaded {len(self.tags)} semantic tags from {self.data_file}")
            except Exception as e:
                rospy.logwarn(f"Failed to load tags: {e}")
                self.tags = {}
        else:
            rospy.loginfo("No existing data file, starting with empty tag list")
    
    def save_tags(self):
        with self.lock:
            try:
                with open(self.data_file, 'w') as f:
                    json.dump(self.tags, f, indent=2)
                rospy.logdebug(f"Saved {len(self.tags)} semantic tags to {self.data_file}")
            except Exception as e:
                rospy.logerr(f"Failed to save tags: {e}")
    
    def handle_add_tag(self, req):
        with self.lock:
            if req.name in self.tags:
                return AddSemanticTagResponse(False, f"Tag '{req.name}' already exists")
            
            self.tags[req.name] = {
                'x': req.x,
                'y': req.y,
                'yaw': req.yaw,
                'tag_type': req.tag_type,
                'description': req.description
            }
            
            self.broadcast_tags()
            rospy.loginfo(f"Added semantic tag: {req.name} ({req.tag_type}) at ({req.x}, {req.y})")
            return AddSemanticTagResponse(True, f"Tag '{req.name}' added successfully")
    
    def handle_query_tag(self, req):
        with self.lock:
            if req.name not in self.tags:
                return QuerySemanticTagResponse(False, "", 0.0, 0.0, 0.0, "", "")
            
            tag = self.tags[req.name]
            return QuerySemanticTagResponse(
                True,
                req.name,
                tag['x'],
                tag['y'],
                tag['yaw'],
                tag['tag_type'],
                tag['description']
            )
    
    def handle_delete_tag(self, req):
        with self.lock:
            if req.name not in self.tags:
                return DeleteSemanticTagResponse(False, f"Tag '{req.name}' not found")
            
            del self.tags[req.name]
            self.broadcast_tags()
            rospy.loginfo(f"Deleted semantic tag: {req.name}")
            return DeleteSemanticTagResponse(True, f"Tag '{req.name}' deleted successfully")
    
    def handle_list_tags(self, req):
        with self.lock:
            if req.tag_type:
                names = [name for name, tag in self.tags.items() if tag['tag_type'] == req.tag_type]
            else:
                names = list(self.tags.keys())
            return ListSemanticTagsResponse(True, names)
    
    def broadcast_tags(self):
        try:
            tags_json = json.dumps(self.tags)
            self.tags_publisher.publish(tags_json)
        except Exception as e:
            rospy.logerr(f"Failed to broadcast tags: {e}")

if __name__ == '__main__':
    try:
        manager = SemanticTagManager()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Semantic Tag Manager node interrupted")