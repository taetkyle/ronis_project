import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, PointStamped
from visualization_msgs.msg import Marker

class MousePathNode(Node):
    def __init__(self):
        super().__init__('mouse_path_node')
        
        # Listener for Rviz clicks
        self.subscription_click = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.click_callback,
            10)

        # Publishers
        self.publisher_ = self.create_publisher(Point, 'target_point', 10)
        self.vis_publisher_ = self.create_publisher(Marker, 'path_marker', 10)
        
        self.target_x = 0.0
        self.target_y = 0.0
        # Initialize z slightly up so it doesn't start underground
        self.target_z = 0.5 
        
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info("Mouse Mode Started: Use 'Publish Point' in Rviz!")

    def click_callback(self, msg):
        # Update target when user clicks
        self.target_x = msg.point.x
        self.target_y = msg.point.y
        # Keep the Z height consistent for visualization
        self.target_z = 0.5 
        self.get_logger().info(f"New Target: {self.target_x:.2f}, {self.target_y:.2f}")

    def timer_callback(self):
        # 1. Tell Robot where to go (Robot only cares about X and Y)
        msg = Point()
        msg.x = self.target_x
        msg.y = self.target_y
        self.publisher_.publish(msg)

        # 2. Draw Marker in Rviz
        marker = Marker()
        marker.header.frame_id = "odom"
        marker.header.stamp = self.get_clock().now().to_msg()
        
        # --- FIX FOR "STAYING" MARKERS ---
        # Explicitly set namespace and ID. 
        # Rviz will overwrite existing markers with the same ns/id.
        marker.ns = "current_target"
        marker.id = 0
        
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        
        # --- FIX FOR VISIBILITY ---
        # Made bigger (0.5) and lifted up (target_z)
        marker.scale.x = 0.5
        marker.scale.y = 0.5
        marker.scale.z = 0.5
        marker.color.a = 1.0 # Alpha (transparency) must be 1.0 to be visible
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        
        marker.pose.position.x = self.target_x
        marker.pose.position.y = self.target_y
        marker.pose.position.z = self.target_z # Floating in air
        
        self.vis_publisher_.publish(marker)

def main(args=None):
    rclpy.init(args=args)
    node = MousePathNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()