import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/eyadmin/Desktop/Bennett/debug/ros2_ws/src/install/yolov8_detector'
