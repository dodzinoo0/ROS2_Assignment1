#Turtlesim Control Lab

A ROS 2 workspace that drives the `turtlesim` turtle to arbitrary poses and
makes it draw squares, using custom messages, a service, and two actions.

## Team

| Name               | ID      |
|--------------------|---------|
| Rahma Yahia Farag  | 2304162 |
| Yassin Amr Salem   | 2304159 |
| Eyad Khaled Zaki   | 2304157 |

## Overview

The workspace contains two packages:

**`turtlesim_interfaces`** (CMake / `ament_cmake`) — the custom interface definitions:
- `msg/PoseTarget.msg` — a target pose (`x`, `y`, `yaw`)
- `srv/SetSpeedLimits.srv` — set the max linear / angular speed at runtime
- `action/GoToPose.action` — drive the turtle to a `PoseTarget` (feedback: distance to goal)
- `action/DrawSquare.action` — draw a square of a given side length (feedback: current side)

**`turtlesim_control`** (Python / `ament_python`) — the nodes:
- `turtle_controller` — subscribes to `/turtle1/pose`, publishes `/turtle1/cmd_vel`, and provides:
  - the `go_to_pose` action (closed-loop position + heading control)
  - the `set_speed_limits` service
  - the `reset_turtle` service (pen up, teleport home, clear, pen down)
- `square_action_server` — provides the `draw_square` action, which resets the
  turtle and then calls `go_to_pose` for each of the four corners.

A launch file, `turtle_mission.launch.py`, starts `turtlesim_node`, the
controller, and the square action server together.

## Prerequisites

- A ROS 2 distribution with `colcon` and `turtlesim` installed. This lab uses
  the `turtlesim_msgs` package, so it targets **ROS 2 Jazzy or newer**
  (on older distros these messages live in the `turtlesim` package instead).
- The `turtlesim` demo and build tools:

  ```bash
  sudo apt update
  sudo apt install ros-$ROS_DISTRO-turtlesim python3-colcon-common-extensions
  ```

- Source your ROS 2 installation in every new terminal:

  ```bash
  source /opt/ros/$ROS_DISTRO/setup.bash
  ```

> On Windows, run the project from a ROS 2 environment (WSL/Ubuntu is the
> simplest). If you build natively on Windows, replace `setup.bash` with
> `install\setup.bat` in the commands below.

## Build

From the workspace root (`ROS2_test`):

```bash
cd /path/to/ROS2_test

# Build the interfaces first, then everything else.
# colcon resolves the dependency order automatically:
colcon build

# Source the workspace so the new packages and interfaces are found:
source install/setup.bash
```

If you ever change the message/service/action definitions in
`turtlesim_interfaces`, rebuild and re-source before running the nodes again.

## Run

### Option A — launch everything at once (recommended)

In one terminal (workspace sourced):

```bash
ros2 launch turtlesim_control turtle_mission.launch.py
```

This opens the turtlesim window and starts both nodes. You can override the
speed limits at launch:

```bash
ros2 launch turtlesim_control turtle_mission.launch.py max_linear_speed:=3.0 max_angular_speed:=3.0
```

### Option B — run each node in its own terminal

Remember to `source install/setup.bash` in every terminal first.

```bash
# Terminal 1 — the simulator
ros2 run turtlesim turtlesim_node

# Terminal 2 — the controller (go_to_pose action + services)
ros2 run turtlesim_control turtle_controller

# Terminal 3 — the square action server
ros2 run turtlesim_control square_action_server
```

## Sending commands

Open another terminal, source the workspace (`source install/setup.bash`), then:

**Draw a square** (side length in turtlesim units, must be `0 < side <= 5`):

```bash
ros2 action send_goal /draw_square turtlesim_interfaces/action/DrawSquare "{side_length: 3.0}" --feedback
```

**Drive to a specific pose** (`x`, `y` in units, `yaw` in radians):

```bash
ros2 action send_goal /go_to_pose turtlesim_interfaces/action/GoToPose "{target_pose: {x: 8.0, y: 8.0, yaw: 0.0}}" --feedback
```

**Change the speed limits at runtime:**

```bash
ros2 service call /set_speed_limits turtlesim_interfaces/srv/SetSpeedLimits "{max_linear_speed: 2.0, max_angular_speed: 2.0}"
```

**Reset the turtle** (teleport home and clear the trail):

```bash
ros2 service call /reset_turtle std_srvs/srv/Empty "{}"
```

## Handy inspection commands

```bash
ros2 node list                    # see the running nodes
ros2 action list                  # /go_to_pose and /draw_square
ros2 service list                 # /set_speed_limits, /reset_turtle, ...
ros2 topic echo /turtle1/pose     # watch the turtle's live pose
```

## Project structure

```
ROS2_test/
├── README.md
└── src/
    ├── turtlesim_control/                 # Python nodes + launch
    │   ├── launch/turtle_mission.launch.py
    │   ├── turtlesim_control/
    │   │   ├── turtle_controller.py
    │   │   └── square_action_server.py
    │   ├── package.xml
    │   └── setup.py
    └── turtlesim_interfaces/              # custom msg / srv / action
        ├── msg/PoseTarget.msg
        ├── srv/SetSpeedLimits.srv
        ├── action/GoToPose.action
        ├── action/DrawSquare.action
        ├── CMakeLists.txt
        └── package.xml
```
