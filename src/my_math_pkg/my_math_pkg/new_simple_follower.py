import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, TwistStamped
from nav_msgs.msg import Odometry
import math

class PIDFollower(Node):
    def __init__(self):
        super().__init__('pid_follower')
        
        # Subscribers & Publishers
        self.subscription_target = self.create_subscription(
            Point, 'target_point', self.target_callback, 10)
        self.subscription_odom = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10)
        self.publisher_vel = self.create_publisher(
            TwistStamped, '/cmd_vel', 10)

        # Robot State
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.target_x = 0.0
        self.target_y = 0.0

        # --- PID MEMORY VARIABLES ---
        self.prev_error = 0.0
        self.integral_error = 0.0
        
        # Timer (Control Loop 20Hz)
        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info("PID Controller Started")

    def target_callback(self, msg):
        self.target_x = msg.x
        self.target_y = msg.y

    def odom_callback(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        
        # Quaternion to Euler
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.robot_yaw = math.atan2(siny_cosp, cosy_cosp)

    def control_loop(self):
        # 1. Calculate Errors
        dx = self.target_x - self.robot_x
        dy = self.target_y - self.robot_y
        distance_error = math.sqrt(dx**2 + dy**2)
        
        desired_angle = math.atan2(dy, dx)
        angle_error = desired_angle - self.robot_yaw
        
        # Normalize angle (-pi to +pi)
        while angle_error > math.pi:
            angle_error -= 2.0 * math.pi
        while angle_error < -math.pi:
            angle_error += 2.0 * math.pi

        # --- PID ALGORITHM START ---
        
        # TUNING KNOBS (Play with these!)
        Kp = 2.0   # Power (How hard to turn)
        Ki = 0.001 # Memory (Fixes small drifts over time)
        Kd = 1.0   # Damper (Prevents wobbling/overshoot)

        # Proportional Term
        P = angle_error
        
        # Integral Term (Accumulate error)
        self.integral_error += angle_error
        # Clamp Integral (Anti-windup): Don't let memory get too big
        self.integral_error = max(min(self.integral_error, 1.0), -1.0)
        I = self.integral_error

        # Derivative Term (Change in error)
        D = angle_error - self.prev_error
        
        # Calculate Output
        angular_output = (Kp * P) + (Ki * I) + (Kd * D)
        
        # Save error for next loop
        self.prev_error = angle_error
        
        # --- PID ALGORITHM END ---

        # Send Command
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'base_link'
        
        if distance_error > 0.1:
            # Linear speed is simple P-control based on distance
            cmd.twist.linear.x = 2.0 * distance_error 
            cmd.twist.angular.z = angular_output
            
            # Speed Limits
            cmd.twist.linear.x = min(cmd.twist.linear.x, 2.5) # Max 0.4 m/s
        else:
            # Stop if close
            cmd.twist.linear.x = 0.0
            cmd.twist.angular.z = 0.0

        self.publisher_vel.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = PIDFollower()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()