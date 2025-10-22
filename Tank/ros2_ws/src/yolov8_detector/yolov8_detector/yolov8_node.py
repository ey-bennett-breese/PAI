import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO
from ultralytics.engine.results import Boxes  # Add at the top

class Yolov8Detector(Node):
    def __init__(self):
        super().__init__('yolov8_detector')
        self.subscription = self.create_subscription(
            Image,
            '/rgb',  # The topic where Isaac Sim publishes camera frames
            self.listener_callback,
            10)
        self.publisher = self.create_publisher(Image, '/camera/detections', 10)
        self.bridge = CvBridge()
        
        # self.model = YOLO('yolov8x-worldv2.pt')
        # self.model = YOLO('yolov8n.pt')  
        self.model = YOLO('yolov8n-oiv7') # Path to your YOLOv8 model. oiv7 seems to give reasonable results

        self.filter = True
        self.allowed_class_names = [
            'Filing cabinet','Desk', 'Person', 'Chair', 'Couch', 'Closet', 
            'Dog', 'Humidifier', 'Laptop', 'Whiteboard'
        ]

        # Map class names to indices once
        self.allowed_class_ids = [
            class_id for class_id, class_name in self.model.names.items()
            if class_name in self.allowed_class_names
        ]

        
    def listener_callback(self, msg):
        # Convert ROS Image message to OpenCV format
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        # Perform object detection
        results = self.model(cv_image)
        
        # Get detection result for first image
        result = results[0]
        
        if self.filter:
            result.boxes = result.boxes[[i for i, c in enumerate(result.boxes.cls.int()) if c.item() in self.allowed_class_ids]]

        # Draw bounding boxes on the image
        annotated_frame = result.plot()
        # Convert back to ROS Image message
        detection_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
        detection_msg.header = msg.header  # Retain original message header
        self.publisher.publish(detection_msg)
def main(args=None):
    rclpy.init(args=args)
    yolov8_detector = Yolov8Detector()
    rclpy.spin(yolov8_detector)
    yolov8_detector.destroy_node()
    rclpy.shutdown()
if __name__ == '__main__':
    main()
