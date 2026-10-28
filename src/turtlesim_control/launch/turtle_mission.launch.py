from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('max_linear_speed', default_value='2.0'),
        DeclareLaunchArgument('max_angular_speed', default_value='2.0'),
        Node(package='turtlesim', executable='turtlesim_node', name='turtlesim_sim', output='screen'),
        Node(package='turtlesim_control', executable='turtle_controller', name='turtle_controller', 
             parameters=[{'max_linear_speed': LaunchConfiguration('max_linear_speed'),
                          'max_angular_speed': LaunchConfiguration('max_angular_speed')}],
             output='screen'),
        Node(package='turtlesim_control', executable='square_action_server', name='square_action_server', output='screen')
    ])