import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
import cv2
import numpy as np
import math

class BallTracker(Node):
    def __init__(self):
        super().__init__('ball_tracker')
        
        self.subscription = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        # NEW: Publisher to send the 3D coordinate to our controller
        self.publisher_target = self.create_publisher(Point, 'target_point', 10)
        
        self.bridge = CvBridge()
        self.get_logger().info("Vision System Online. Calculating 3D trajectory...")

        # Camera constants (TurtleBot3 Waffle Pi Camera)
        self.fov_horizontal = 1.085 # ~62.2 degrees in radians
        self.real_ball_radius = 0.05 # 5cm in meters

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            return

        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([40, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            pixel_area = cv2.contourArea(largest_contour)
            
            if pixel_area > 50:
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    
                    # --- 2D TO 3D MATH ---
                    image_width = cv_image.shape[1]
                    center_x = image_width / 2.0
                    
                    # 1. Calculate focal length in pixels
                    focal_length = center_x / math.tan(self.fov_horizontal / 2.0)
                    
                    # 2. Calculate pixel radius
                    pixel_radius = math.sqrt(pixel_area / math.pi)
                    
                    # 3. Estimate Distance (Z in camera frame)
                    distance = (self.real_ball_radius * focal_length) / pixel_radius
                    
                    # 4. Estimate Angle (Yaw)
                    angle_offset = ((center_x - cX) / image_width) * self.fov_horizontal
                    
                    # 5. Convert to Robot Coordinate Frame (X forward, Y left)
                    target_x = distance * math.cos(angle_offset)
                    target_y = distance * math.sin(angle_offset)
                    
                    # Publish the target
                    target_msg = Point()
                    target_msg.x = target_x
                    target_msg.y = target_y
                    target_msg.z = 0.0 # It's on the floor
                    self.publisher_target.publish(target_msg)
                    
                    # Draw HUD
                    cv2.circle(cv_image, (cX, cY), int(pixel_radius), (0, 255, 0), 2)
                    cv2.putText(cv_image, f"Dist: {distance:.2f}m", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
        cv2.imshow("Waffle Camera Feed", cv_image)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = BallTracker()
    rclpy.spin(node)
    node.destroy_node()
    cv2.destroyAllWindows()
    rclpy.shutdown()