import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class BallTracker(Node):
    def __init__(self):
        super().__init__('ball_tracker')
        
        # Subscribe to the robot's camera
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10)
            
        self.bridge = CvBridge()
        self.get_logger().info("Vision System Online. Searching for target...")

    def image_callback(self, msg):
        try:
            # Convert ROS Image to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f"Image conversion failed: {e}")
            return

        # Convert BGR (Blue-Green-Red) to HSV (Hue-Saturation-Value)
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        
        # Define the exact color of our Gazebo tennis ball (Yellow)
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([40, 255, 255])
        
        # Create a binary mask (White where it's yellow, Black everywhere else)
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Find the outlines (contours) of the yellow blobs
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Assume the largest yellow blob is our tennis ball
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Only track if it's bigger than a few pixels (noise filtering)
            if cv2.contourArea(largest_contour) > 50:
                # Calculate the exact center pixel (X, Y) using image moments
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    
                    # Draw a targeting circle and center dot on the image
                    cv2.circle(cv_image, (cX, cY), int(np.sqrt(cv2.contourArea(largest_contour)/np.pi)), (0, 255, 0), 2)
                    cv2.circle(cv_image, (cX, cY), 5, (0, 0, 255), -1)
                    
                    self.get_logger().info(f"Target Locked -> Screen X: {cX}, Screen Y: {cY}")
        else:
            self.get_logger().info("Scanning...")

        # Display the live feed with our targeting HUD
        cv2.imshow("Waffle Camera Feed", cv_image)
        cv2.waitKey(1) # Required for OpenCV to update the window

def main(args=None):
    rclpy.init(args=args)
    node = BallTracker()
    rclpy.spin(node)
    node.destroy_node()
    cv2.destroyAllWindows()
    rclpy.shutdown()

if __name__ == '__main__':
    main()