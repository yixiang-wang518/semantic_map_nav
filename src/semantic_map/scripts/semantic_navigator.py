#!/usr/bin/env python3
import rospy
import math
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import Quaternion, PoseStamped
from semantic_map.msg import NavigateToSemanticTagAction, NavigateToSemanticTagResult, NavigateToSemanticTagFeedback
from semantic_map.srv import QuerySemanticTag, QuerySemanticTagRequest, ListSemanticTags

def quaternion_from_euler(yaw):
    return Quaternion(0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))

def euler_from_quaternion(q):
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)

class SemanticNavigator:
    def __init__(self):
        rospy.init_node('semantic_navigator', anonymous=False)
        
        self.move_base_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        rospy.loginfo("Waiting for move_base action server...")
        self.move_base_client.wait_for_server()
        rospy.loginfo("Connected to move_base action server")
        
        self.navigate_action_server = actionlib.SimpleActionServer(
            '/semantic_map/navigate_to_tag',
            NavigateToSemanticTagAction,
            execute_cb=self.execute_navigation,
            auto_start=False
        )
        self.navigate_action_server.start()
        
        self.current_pose_sub = rospy.Subscriber('/amcl_pose', PoseStamped, self.update_current_pose)
        self.current_x = 0.0
        self.current_y = 0.0
        
        self.navigation_timeout = rospy.get_param('~navigation_timeout', 300.0)
        self.danger_zone_radius = rospy.get_param('~danger_zone_radius', 1.0)
        
        rospy.loginfo("Semantic Navigator node started")
    
    def update_current_pose(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
    
    def check_danger_zones(self, target_x, target_y):
        dangerous_zones = []
        try:
            rospy.wait_for_service('/semantic_map/list_tags', timeout=2.0)
            list_tags = rospy.ServiceProxy('/semantic_map/list_tags', ListSemanticTags)
            response = list_tags("danger_zone")
            
            if response.success:
                rospy.wait_for_service('/semantic_map/query_tag', timeout=2.0)
                query_tag = rospy.ServiceProxy('/semantic_map/query_tag', QuerySemanticTag)
                
                for zone_name in response.names:
                    zone_response = query_tag(zone_name)
                    if zone_response.success:
                        dist = math.sqrt((zone_response.x - target_x)**2 + (zone_response.y - target_y)**2)
                        if dist < self.danger_zone_radius:
                            dangerous_zones.append(zone_name)
        except Exception as e:
            rospy.logwarn(f"Failed to check danger zones: {e}")
        
        return dangerous_zones
    
    def execute_navigation(self, goal):
        tag_name = goal.tag_name
        rospy.loginfo(f"Received navigation request for tag: {tag_name}")
        
        result = NavigateToSemanticTagResult()
        feedback = NavigateToSemanticTagFeedback()
        
        try:
            rospy.wait_for_service('/semantic_map/query_tag', timeout=5.0)
            query_service = rospy.ServiceProxy('/semantic_map/query_tag', QuerySemanticTag)
            response = query_service(tag_name)
            
            if not response.success:
                result.success = False
                result.message = f"Tag '{tag_name}' not found"
                self.navigate_action_server.set_aborted(result)
                return
            
            tag_x = response.x
            tag_y = response.y
            tag_yaw = response.yaw
            rospy.loginfo(f"Found tag '{tag_name}' at ({tag_x}, {tag_y}) with yaw {tag_yaw}")
            
            danger_zones = self.check_danger_zones(tag_x, tag_y)
            if danger_zones:
                result.success = False
                result.message = f"Target location is near danger zones: {', '.join(danger_zones)}"
                self.navigate_action_server.set_aborted(result)
                return
            
            move_base_goal = MoveBaseGoal()
            move_base_goal.target_pose.header.frame_id = "map"
            move_base_goal.target_pose.header.stamp = rospy.Time.now()
            move_base_goal.target_pose.pose.position.x = tag_x
            move_base_goal.target_pose.pose.position.y = tag_y
            move_base_goal.target_pose.pose.orientation = quaternion_from_euler(tag_yaw)
            
            rospy.loginfo(f"Sending navigation goal to ({tag_x}, {tag_y})...")
            self.move_base_client.send_goal(
                move_base_goal,
                feedback_cb=self.feedback_callback
            )
            
            feedback.status = "Navigating..."
            feedback.current_x = self.current_x
            feedback.current_y = self.current_y
            self.navigate_action_server.publish_feedback(feedback)
            
            finished_within_time = self.move_base_client.wait_for_result(rospy.Duration(self.navigation_timeout))
            
            if not finished_within_time:
                self.move_base_client.cancel_goal()
                result.success = False
                result.message = "Navigation timed out"
                result.final_x = self.current_x
                result.final_y = self.current_y
                result.final_yaw = 0.0
                self.navigate_action_server.set_aborted(result)
                return
            
            state = self.move_base_client.get_state()
            
            if state == actionlib.GoalStatus.SUCCEEDED:
                rospy.loginfo(f"Navigation to '{tag_name}' succeeded")
                result.success = True
                result.message = "Navigation succeeded"
                result.final_x = tag_x
                result.final_y = tag_y
                result.final_yaw = tag_yaw
                self.navigate_action_server.set_succeeded(result)
            else:
                rospy.logwarn(f"Navigation to '{tag_name}' failed with state {state}")
                result.success = False
                result.message = f"Navigation failed - state: {state}"
                result.final_x = self.current_x
                result.final_y = self.current_y
                result.final_yaw = 0.0
                self.navigate_action_server.set_aborted(result)
                
        except rospy.ServiceException as e:
            result.success = False
            result.message = f"Service call failed: {str(e)}"
            self.navigate_action_server.set_aborted(result)
        except rospy.ROSException as e:
            result.success = False
            result.message = f"ROS exception: {str(e)}"
            self.navigate_action_server.set_aborted(result)
        except Exception as e:
            result.success = False
            result.message = f"Unexpected error: {str(e)}"
            self.navigate_action_server.set_aborted(result)
    
    def feedback_callback(self, move_base_feedback):
        feedback = NavigateToSemanticTagFeedback()
        feedback.current_x = move_base_feedback.base_position.pose.position.x
        feedback.current_y = move_base_feedback.base_position.pose.position.y
        feedback.status = "In progress"
        self.navigate_action_server.publish_feedback(feedback)

if __name__ == '__main__':
    try:
        navigator = SemanticNavigator()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Semantic Navigator node interrupted")