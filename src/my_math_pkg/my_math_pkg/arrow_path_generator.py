import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, PoseStamped # <--- CHANGED
from visualization_msgs.msg import Marker

class MousePathNode(Node):
    def __init__(self):
        super().__init__('mouse_path_node')
        
        # CHANGED: Listen to the "2D Goal Pose" arrow tool
        self.subscription_click = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.click_callback,
            10)

        self.publisher_ = self.create_publisher(Point, 'target_point', 10)
        self.vis_publisher_ = self.create_publisher(Marker, 'path_marker', 10)
        
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_z = 0.5 
        
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info("Ready! Use the '2D Goal Pose' (Green Arrow) in Rviz.")

    def click_callback(self, msg):
        # CHANGED: The arrow message structure is slightly different
        self.target_x = msg.pose.position.x
        self.target_y = msg.pose.position.y
        self.get_logger().info(f"New Target: {self.target_x:.2f}, {self.target_y:.2f}")

    def timer_callback(self):
        # ... (This part stays the same as before) ...
        msg = Point()
        msg.x = self.target_x
        msg.y = self.target_y
        self.publisher_.publish(msg)

        marker = Marker()
        marker.header.frame_id = "odom"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "current_target"
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.scale.x = 0.5
        marker.scale.y = 0.5
        marker.scale.z = 0.5
        marker.color.a = 1.0
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        marker.pose.position.x = self.target_x
        marker.pose.position.y = self.target_y
        marker.pose.position.z = self.target_z
        self.vis_publisher_.publish(marker)

def main(args=None):
    rclpy.init(args=args)
    node = MousePathNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()