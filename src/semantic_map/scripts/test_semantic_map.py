#!/usr/bin/env python3
import rospy
import sys
import actionlib
from semantic_map.srv import AddSemanticTag, QuerySemanticTag, DeleteSemanticTag, ListSemanticTags
from semantic_map.msg import NavigateToSemanticTagAction, NavigateToSemanticTagGoal

def test_add_tag(name, x, y, yaw, tag_type, description):
    rospy.wait_for_service('/semantic_map/add_tag')
    try:
        add_tag = rospy.ServiceProxy('/semantic_map/add_tag', AddSemanticTag)
        response = add_tag(name, x, y, yaw, tag_type, description)
        print(f"Add tag '{name}': {response.success} - {response.message}")
        return response.success
    except rospy.ServiceException as e:
        print(f"Service call failed: {e}")
        return False

def test_query_tag(name):
    rospy.wait_for_service('/semantic_map/query_tag')
    try:
        query_tag = rospy.ServiceProxy('/semantic_map/query_tag', QuerySemanticTag)
        response = query_tag(name)
        if response.success:
            print(f"Query tag '{name}':")
            print(f"  Position: ({response.x}, {response.y})")
            print(f"  Yaw: {response.yaw}")
            print(f"  Type: {response.tag_type}")
            print(f"  Description: {response.description}")
        else:
            print(f"Query tag '{name}': Not found")
        return response.success
    except rospy.ServiceException as e:
        print(f"Service call failed: {e}")
        return False

def test_delete_tag(name):
    rospy.wait_for_service('/semantic_map/delete_tag')
    try:
        delete_tag = rospy.ServiceProxy('/semantic_map/delete_tag', DeleteSemanticTag)
        response = delete_tag(name)
        print(f"Delete tag '{name}': {response.success} - {response.message}")
        return response.success
    except rospy.ServiceException as e:
        print(f"Service call failed: {e}")
        return False

def test_list_tags(tag_type=""):
    rospy.wait_for_service('/semantic_map/list_tags')
    try:
        list_tags = rospy.ServiceProxy('/semantic_map/list_tags', ListSemanticTags)
        response = list_tags(tag_type)
        if response.success:
            print(f"List tags (type='{tag_type}'): {response.names}")
        else:
            print("List tags failed")
        return response.success
    except rospy.ServiceException as e:
        print(f"Service call failed: {e}")
        return False

def test_navigate_to_tag(tag_name):
    client = actionlib.SimpleActionClient('/semantic_map/navigate_to_tag', NavigateToSemanticTagAction)
    print(f"Waiting for navigate_to_tag action server...")
    if not client.wait_for_server(rospy.Duration(10.0)):
        print("Action server not available")
        return False
    
    goal = NavigateToSemanticTagGoal()
    goal.tag_name = tag_name
    
    print(f"Sending navigation goal for '{tag_name}'...")
    client.send_goal(goal)
    
    finished = client.wait_for_result(rospy.Duration(30.0))
    if not finished:
        print("Navigation timed out")
        client.cancel_goal()
        return False
    
    result = client.get_result()
    print(f"Navigate to '{tag_name}': {result.success} - {result.message}")
    if result.success:
        print(f"  Final position: ({result.final_x}, {result.final_y}, yaw={result.final_yaw})")
    return result.success

def feedback_callback(feedback):
    print(f"Navigation feedback: {feedback.status} - ({feedback.current_x}, {feedback.current_y})")

if __name__ == '__main__':
    rospy.init_node('semantic_map_test', anonymous=True)
    
    print("\n=== Testing Semantic Map Services ===\n")
    
    print("1. Testing list tags (empty type)...")
    test_list_tags()
    
    print("\n2. Testing add tag 'test_charging'...")
    test_add_tag("test_charging", 1.0, 2.0, 0.0, "charging_station", "Test charging station")
    
    print("\n3. Testing add tag 'test_entrance'...")
    test_add_tag("test_entrance", -1.0, 1.0, 3.14159, "entrance", "Test entrance")
    
    print("\n4. Testing add danger zone 'test_danger'...")
    test_add_tag("test_danger", 0.5, 1.5, 0.0, "danger_zone", "Test danger zone")
    
    print("\n5. Testing list tags (all)...")
    test_list_tags()
    
    print("\n6. Testing list tags (type='charging_station')...")
    test_list_tags("charging_station")
    
    print("\n7. Testing query tag 'test_charging'...")
    test_query_tag("test_charging")
    
    print("\n8. Testing query tag 'non_existent'...")
    test_query_tag("non_existent")
    
    print("\n9. Testing delete tag 'test_charging'...")
    test_delete_tag("test_charging")
    
    print("\n10. Testing list tags after deletion...")
    test_list_tags()
    
    print("\n=== Test completed ===")