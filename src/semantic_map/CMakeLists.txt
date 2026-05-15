cmake_minimum_required(VERSION 3.0.2)
project(semantic_map)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  move_base_msgs
  visualization_msgs
  std_srvs
  actionlib
  actionlib_msgs
  message_generation
)

add_service_files(
  FILES
  AddSemanticTag.srv
  QuerySemanticTag.srv
  DeleteSemanticTag.srv
  ListSemanticTags.srv
)

add_action_files(
  FILES
  NavigateToSemanticTag.action
)

generate_messages(
  DEPENDENCIES
  std_msgs
  geometry_msgs
  actionlib_msgs
)

catkin_package(
  CATKIN_DEPENDS
  rospy
  std_msgs
  geometry_msgs
  move_base_msgs
  visualization_msgs
  std_srvs
  actionlib
  actionlib_msgs
  message_runtime
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

catkin_install_python(PROGRAMS
  scripts/semantic_tag_manager.py
  scripts/semantic_navigator.py
  scripts/semantic_visualizer.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config data
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)