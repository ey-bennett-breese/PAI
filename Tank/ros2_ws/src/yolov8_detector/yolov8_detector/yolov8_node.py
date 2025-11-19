# import rclpy
# from rclpy.node import Node
# from sensor_msgs.msg import Image
# from cv_bridge import CvBridge
# import cv2
# from ultralytics import YOLO
# from datetime import datetime
# import os


# class Yolov8Detector(Node):
#     def __init__(self):
#         super().__init__('yolov8_detector')

#         # --- Config ---
#         self.target_fps = 30.0
#         self.frame_period_sim = 1.0 / self.target_fps

#         # --- ROS setup ---
#         self.subscription = self.create_subscription(
#             Image,
#             '/rgb_side',
#             self.listener_callback,
#             10
#         )
#         self.publisher = self.create_publisher(Image, '/camera/detections', 10)
#         self.bridge = CvBridge()

#         # --- YOLO Model ---
#         self.model = YOLO('yolov8l-oiv7')

#         # --- Video setup ---
#         self.video_writer = None
#         self.output_filename = f"camera_detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
#         self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#         self.frame_size = None

#         # --- Sim time tracking ---
#         self.prev_sim_time = None  # in seconds

#         self.get_logger().info(
#             f"Initialized YOLOv8 detector using sim time. Output video: {self.output_filename}"
#         )

#     def listener_callback(self, msg: Image):
#         # Convert ROS time stamp to seconds (simulation time)
#         sim_time = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

#         # Convert to OpenCV image
#         cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

#         # Initialize video writer
#         if self.video_writer is None:
#             height, width, _ = cv_image.shape
#             self.frame_size = (width, height)
#             self.video_writer = cv2.VideoWriter(
#                 self.output_filename, self.fourcc, self.target_fps, self.frame_size
#             )
#             if not self.video_writer.isOpened():
#                 self.get_logger().error("Failed to open VideoWriter.")
#                 return
#             self.get_logger().info(f"Video recording started at {self.target_fps} FPS (sim time).")

#         # Perform YOLO detection
#         results = self.model(cv_image)
#         result = results[0]
#         annotated_frame = result.plot()

#         # Compute simulated time delta
#         if self.prev_sim_time is not None:
#             delta_t_sim = sim_time - self.prev_sim_time
#         else:
#             delta_t_sim = self.frame_period_sim  # default for first frame

#         self.prev_sim_time = sim_time

#         # Determine how many output frames this represents
#         num_video_frames = max(1, int(round(delta_t_sim / self.frame_period_sim)))

#         # Write the frame the appropriate number of times
#         for _ in range(num_video_frames):
#             self.video_writer.write(annotated_frame)

#         # Publish annotated image (latest one)
#         detection_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
#         detection_msg.header = msg.header
#         self.publisher.publish(detection_msg)

#     def destroy_node(self):
#         if self.video_writer is not None:
#             self.video_writer.release()
#             self.get_logger().info(f"Video saved to {os.path.abspath(self.output_filename)}")
#         super().destroy_node()


# def main(args=None):
#     rclpy.init(args=args)
#     node = Yolov8Detector()
#     try:
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         node.get_logger().info("Shutting down YOLOv8 detector...")
#     finally:
#         node.destroy_node()
#         rclpy.shutdown()


# if __name__ == '__main__':
#     main()

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
            '/rgb_side',  # The topic where Isaac Sim publishes camera frames
            self.listener_callback,
            10)
        self.publisher = self.create_publisher(Image, '/camera/detections', 10)
        self.bridge = CvBridge()
        
        # self.model = YOLO('yolov8x-worldv2.pt')
        # self.model = YOLO('yolov8n.pt')  
        self.model = YOLO('yolov8l-oiv7') # Path to your YOLOv8 model. oiv7 seems to give reasonable results
        # self.model = YOLO('yolo12l')
        # self.model = YOLO('yoloe-11l-seg')


        self.filter = True
        self.allowed_class_names = [
            'Filing cabinet','Desk', 'Person', 'Chair', 'Couch', 'Closet', 
            'Dog', 'Humidifier', 'Laptop', 'Whiteboard', 'Knife', 
            'Table', 'Umbrella', 'Watermelon', 'Bookshelf', 'Waste container', 
            'Weapon', 'Lemon', 'Mug', 'Cup', 'Spoon', 'Fork', 'Bowl', 'Bed',
            'Lime', 'Apple', 'Computer monitor', 'Keyboard', 'Mouse', 'Cell phone', 'Book',
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

        # print('dictionary = ', self.model.names.items())
        
        # if self.filter:
        #     result.boxes = result.boxes[[i for i, c in enumerate(result.boxes.cls.int()) if c.item() in self.allowed_class_ids]]

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
