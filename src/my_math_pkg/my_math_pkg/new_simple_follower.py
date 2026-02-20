import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, TwistStamped
import math
import os

class VisualServoFollower(Node):
    def __init__(self):
        super().__init__('visual_servo_follower')
        
        self.subscription_target = self.create_subscription(
            Point, 'target_point', self.target_callback, 10)
            
        # THE FIX: Restored to TwistStamped for the modern Gazebo bridge
        self.publisher_vel = self.create_publisher(
            TwistStamped, '/cmd_vel', 10)

        self.target_x = 0.0
        self.target_y = 0.0
        self.has_target = False

        self.prev_error = 0.0
        self.integral_error = 0.0
        
        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info("Visual Servoing PID Controller Online.")

    def target_callback(self, msg):
        self.target_x = msg.x
        self.target_y = msg.y
        self.has_target = True

    def reset_simulation(self):
        self.get_logger().warn("Resetting Simulation Environment...")
        os.system("gz service -s /world/turtlebot3_world/control --reqtype ignition.msgs.WorldControl --reptype ignition.msgs.Boolean --timeout 3000 --req 'reset: {all: true}'")
        self.has_target = False # Clear the old target

    def control_loop(self):
        if not self.has_target:
            return

        distance_error = math.sqrt(self.target_x**2 + self.target_y**2)
        angle_error = math.atan2(self.target_y, self.target_x)

        # Setup the TwistStamped message
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'base_link'

        # --- THE STOP CONDITION ---
        if distance_error < 0.40:
            cmd.twist.linear.x = 0.0
            cmd.twist.angular.z = 0.0
            self.publisher_vel.publish(cmd)
            self.get_logger().info("Target reached and centered. Brakes applied.")
            
            # Trigger the simulation reset!
            self.reset_simulation()
            return

        # --- PID ALGORITHM ---
        Kp = 2.0   
        Ki = 0.001 
        Kd = 1.0   

        P = angle_error
        self.integral_error = max(min(self.integral_error + angle_error, 1.0), -1.0)
        I = self.integral_error
        D = angle_error - self.prev_error
        
        angular_output = (Kp * P) + (Ki * I) + (Kd * D)
        self.prev_error = angle_error
        
        # Apply the hardware speed limits to the twist parameters
        cmd.twist.linear.x = min(1.0 * distance_error, 0.22) 
        cmd.twist.angular.z = angular_output

        self.publisher_vel.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = VisualServoFollower()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()