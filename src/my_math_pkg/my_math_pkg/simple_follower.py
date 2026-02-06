import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, TwistStamped  # <--- CHANGE 1: Import TwistStamped
from nav_msgs.msg import Odometry
import math

class SimpleFollower(Node):
    def __init__(self):
        super().__init__('simple_follower')
        
        # Subscribe to Target
        self.subscription_target = self.create_subscription(
            Point,
            'target_point',
            self.target_callback,
            10)
        
        # Subscribe to Odom
        self.subscription_odom = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10)

        # <--- CHANGE 2: Publish TwistStamped instead of Twist
        self.publisher_vel = self.create_publisher(TwistStamped, '/cmd_vel', 10)

        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        
        self.target_x = 0.0
        self.target_y = 0.0
        
        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info("Simple Follower (TwistStamped) Started")

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
        dx = self.target_x - self.robot_x
        dy = self.target_y - self.robot_y
        
        distance_error = math.sqrt(dx**2 + dy**2)
        desired_angle = math.atan2(dy, dx)
        angle_error = desired_angle - self.robot_yaw
        
        while angle_error > math.pi:
            angle_error -= 2.0 * math.pi
        while angle_error < -math.pi:
            angle_error += 2.0 * math.pi

        # Gains
        K_linear = 1.0
        K_angular = 1.5

        # <--- CHANGE 3: Create TwistStamped message
        cmd = TwistStamped()
        
        # IMPORTANT: You must attach the current time!
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'base_link'
        
        if distance_error > 0.1:
            # Note the extra ".twist" layer
            cmd.twist.linear.x = K_linear * distance_error
            cmd.twist.angular.z = K_angular * angle_error
            
            # Safety Limit
            cmd.twist.linear.x = min(cmd.twist.linear.x, 0.3)
        else:
            cmd.twist.linear.x = 0.0
            cmd.twist.angular.z = 0.0

        self.publisher_vel.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = SimpleFollower()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()