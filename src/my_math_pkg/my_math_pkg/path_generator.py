import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
import math
import time

class MathPathNode(Node):
    def __init__(self):
        super().__init__('math_path_node')
        # Publish to a topic named 'target_point'
        self.publisher_ = self.create_publisher(Point, 'target_point', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.start_time = time.time()
        self.get_logger().info("Math Path Generator Started")

    def timer_callback(self):
        # --- YOUR MATH GOES HERE ---
        t = time.time() - self.start_time
        
        # Example: Figure-8 pattern
        # Change these equations to whatever you want
        x = 2.0 * math.sin(t * 0.5) 
        y = 1.0 * math.sin(t * 1.0)
        
        msg = Point()
        msg.x = x
        msg.y = y
        msg.z = 0.0 # Turtlebot is 2D, but we send Z anyway
        
        self.publisher_.publish(msg)
        # self.get_logger().info(f'Target: x={x:.2f}, y={y:.2f}')

def main(args=None):
    rclpy.init(args=args)
    node = MathPathNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()