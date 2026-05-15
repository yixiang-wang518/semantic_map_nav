#!/usr/bin/env python3
import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import Quaternion
from semantic_map.srv import NavigateToSemanticTag, NavigateToSemanticTagResponse
from semantic_map.srv import QuerySemanticTag, QuerySemanticTagRequest

def quaternion_from_euler(yaw):
    import math
    return Quaternion(0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))

class SemanticNavigator:
    def __init__(self):
        rospy.init_node('semantic_navigator', anonymous=False)
        
        self.move_base_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        rospy.loginfo("Waiting for move_base action server...")
        self.move_base_client.wait_for_server()
        rospy.loginfo("Connected to move_base action server")
        
        self.navigate_service = rospy.Service('/semantic_map/navigate_to_tag', NavigateToSemanticTag, self.handle_navigate)
        
        rospy.loginfo("Semantic Navigator node started")
    
    def handle_navigate(self, req):
        rospy.loginfo(f"Received navigation request for tag: {req.tag_name}")
        
        try:
            rospy.wait_for_service('/semantic_map/query_tag', timeout=5.0)
            query_service = rospy.ServiceProxy('/semantic_map/query_tag', QuerySemanticTag)
            response = query_service(req.tag_name)
            
            if not response.success:
                return NavigateToSemanticTagResponse(False, f"Tag '{req.tag_name}' not found")
            
            tag_x = response.x
            tag_y = response.y
            tag_yaw = response.yaw
            rospy.loginfo(f"Found tag '{req.tag_name}' at ({tag_x}, {tag_y}) with yaw {tag_yaw}")
            
            goal = MoveBaseGoal()
            goal.target_pose.header.frame_id = "map"
            goal.target_pose.header.stamp = rospy.Time.now()
            goal.target_pose.pose.position.x = tag_x
            goal.target_pose.pose.position.y = tag_y
            goal.target_pose.pose.orientation = quaternion_from_euler(tag_yaw)
            
            rospy.loginfo(f"Sending navigation goal to ({tag_x}, {tag_y})...")
            self.move_base_client.send_goal(goal)
            
            timeout = rospy.get_param('~navigation_timeout', 300.0)
            finished_within_time = self.move_base_client.wait_for_result(rospy.Duration(timeout))
            
            if not finished_within_time:
                self.move_base_client.cancel_goal()
                return NavigateToSemanticTagResponse(False, "Navigation timed out")
            
            result = self.move_base_client.get_result()
            
            if result:
                rospy.loginfo(f"Navigation to '{req.tag_name}' succeeded")
                return NavigateToSemanticTagResponse(True, "Navigation succeeded")
            else:
                rospy.logwarn(f"Navigation to '{req.tag_name}' failed")
                return NavigateToSemanticTagResponse(False, "Navigation failed - unknown reason")
                
        except rospy.ServiceException as e:
            return NavigateToSemanticTagResponse(False, f"Service call failed: {str(e)}")
        except rospy.ROSException as e:
            return NavigateToSemanticTagResponse(False, f"ROS exception: {str(e)}")
        except Exception as e:
            return NavigateToSemanticTagResponse(False, f"Unexpected error: {str(e)}")

if __name__ == '__main__':
    try:
        navigator = SemanticNavigator()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Semantic Navigator node interrupted")