import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from std_srvs.srv import Empty

from turtlesim_interfaces.action import DrawSquare, GoToPose
from turtlesim_interfaces.msg import PoseTarget

class SquareActionServer(Node):
    def __init__(self):
        super().__init__('square_action_server')
        self.cb_group = ReentrantCallbackGroup()
        self.reset_cli = self.create_client(Empty, 'reset_turtle', callback_group=self.cb_group)
        self.goto_client = ActionClient(self, GoToPose, 'go_to_pose', callback_group=self.cb_group)
        self.server = ActionServer(self, DrawSquare, 'draw_square', execute_callback=self.execute_cb, goal_callback=self.goal_cb, cancel_callback=self.cancel_cb, callback_group=self.cb_group)

    def goal_cb(self, req):
        return GoalResponse.ACCEPT if 0.0 < req.side_length <= 5.0 else GoalResponse.REJECT

    def cancel_cb(self, handle):
        return CancelResponse.ACCEPT

    async def execute_cb(self, handle):
        side = handle.request.side_length
        result = DrawSquare.Result()
        feedback = DrawSquare.Feedback()

        if self.reset_cli.wait_for_service(5.0):
            await self.reset_cli.call_async(Empty.Request())
        else:
            handle.abort()
            result.success = False
            return result

        if not self.goto_client.wait_for_server(5.0):
            handle.abort()
            result.success = False
            return result

        x0, y0 = 5.544445, 5.544445
        corners = [
            (x0 + side, y0, 1.5708),
            (x0 + side, y0 + side, 3.14159),
            (x0, y0 + side, -1.5708),
            (x0, y0, 0.0)
        ]

        for idx, (x, y, yaw) in enumerate(corners):
            if handle.is_cancel_requested:
                handle.canceled()
                result.success = False
                return result

            feedback.current_side = idx + 1
            handle.publish_feedback(feedback)

            goal_msg = GoToPose.Goal()
            goal_msg.target_pose = PoseTarget(x=float(x), y=float(y), yaw=float(yaw))
            
            future = await self.goto_client.send_goal_async(goal_msg)
            if not future.accepted:
                handle.abort()
                result.success = False
                return result

            res = await future.get_result_async()
            if not res.result.success:
                handle.abort()
                result.success = False
                return result

        handle.succeed()
        result.success = True
        return result

def main():
    rclpy.init()
    node = SquareActionServer()
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