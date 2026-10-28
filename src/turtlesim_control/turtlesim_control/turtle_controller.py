import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty

# Lyrical-specific imports
from turtlesim_msgs.msg import Pose
from turtlesim_msgs.srv import TeleportAbsolute, SetPen

from turtlesim_interfaces.srv import SetSpeedLimits
from turtlesim_interfaces.action import GoToPose

def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle

class TurtleController(Node):
    def __init__(self):
        super().__init__('turtle_controller')
        self.cb_group = ReentrantCallbackGroup()

        self.declare_parameter('max_linear_speed', 2.0)
        self.declare_parameter('max_angular_speed', 2.0)

        self.current_pose = None
        self.pose_sub = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10, callback_group=self.cb_group)
        self.cmd_vel_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        self.clear_cli = self.create_client(Empty, '/clear', callback_group=self.cb_group)
        self.teleport_cli = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute', callback_group=self.cb_group)
        self.set_pen_cli = self.create_client(SetPen, '/turtle1/set_pen', callback_group=self.cb_group)

        self.speed_srv = self.create_service(SetSpeedLimits, 'set_speed_limits', self.set_speed_limits_cb, callback_group=self.cb_group)
        self.reset_srv = self.create_service(Empty, 'reset_turtle', self.reset_turtle_cb, callback_group=self.cb_group)
        
        self.action_server = ActionServer(self, GoToPose, 'go_to_pose', execute_callback=self.execute_goto, goal_callback=self.goal_cb, cancel_callback=self.cancel_cb, callback_group=self.cb_group)

    def pose_callback(self, msg):
        self.current_pose = msg

    def set_speed_limits_cb(self, request, response):
        if request.max_linear_speed <= 0.0 or request.max_angular_speed <= 0.0:
            response.success = False
            return response
        self.set_parameters([
            rclpy.parameter.Parameter('max_linear_speed', rclpy.Parameter.Type.DOUBLE, request.max_linear_speed),
            rclpy.parameter.Parameter('max_angular_speed', rclpy.Parameter.Type.DOUBLE, request.max_angular_speed)
        ])
        response.success = True
        return response

    async def reset_turtle_cb(self, request, response):
        if self.set_pen_cli.wait_for_service(1.0):
            await self.set_pen_cli.call_async(SetPen.Request(off=1))
        if self.teleport_cli.wait_for_service(1.0):
            await self.teleport_cli.call_async(TeleportAbsolute.Request(x=5.544445, y=5.544445, theta=0.0))
        if self.set_pen_cli.wait_for_service(1.0):
            await self.set_pen_cli.call_async(SetPen.Request(r=179, g=184, b=255, width=3, off=0))
        if self.clear_cli.wait_for_service(1.0):
            await self.clear_cli.call_async(Empty.Request())
        return response

    def goal_cb(self, req):
        return GoalResponse.ACCEPT

    def cancel_cb(self, handle):
        return CancelResponse.ACCEPT

    async def execute_goto(self, goal_handle):
        rate = self.create_rate(20.0)
        target = goal_handle.request.target_pose
        feedback = GoToPose.Feedback()
        result = GoToPose.Result()

        while self.current_pose is None:
            rclpy.spin_once(self, timeout_sec=0.1)

        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.cmd_vel_pub.publish(Twist())
                result.success = False
                return result

            max_v = self.get_parameter('max_linear_speed').get_parameter_value().double_value
            max_w = self.get_parameter('max_angular_speed').get_parameter_value().double_value

            dx = target.x - self.current_pose.x
            dy = target.y - self.current_pose.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            feedback.distance_to_goal = dist
            goal_handle.publish_feedback(feedback)

            if dist < 0.08:
                break

            angle_err = normalize_angle(math.atan2(dy, dx) - self.current_pose.theta)
            t = Twist()
            if abs(angle_err) > 0.4:
                t.angular.z = max(min(4.0 * angle_err, max_w), -max_w)
            else:
                t.linear.x = min(1.5 * dist, max_v)
                t.angular.z = max(min(4.0 * angle_err, max_w), -max_w)
            self.cmd_vel_pub.publish(t)
            rate.sleep()

        self.cmd_vel_pub.publish(Twist())

        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.success = False
                return result
            max_w = self.get_parameter('max_angular_speed').get_parameter_value().double_value
            yaw_err = normalize_angle(target.yaw - self.current_pose.theta)
            if abs(yaw_err) < 0.04:
                break
            t = Twist()
            t.angular.z = max(min(4.0 * yaw_err, max_w), -max_w)
            self.cmd_vel_pub.publish(t)
            rate.sleep()

        self.cmd_vel_pub.publish(Twist())
        goal_handle.succeed()
        result.success = True
        return result

def main():
    rclpy.init()
    node = TurtleController()
    from rclpy.executors import MultiThreadedExecutor
    exec = MultiThreadedExecutor()
    exec.add_node(node)
    try:
        exec.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()