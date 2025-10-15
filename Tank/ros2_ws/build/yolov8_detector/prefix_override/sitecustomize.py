import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/bennett/github/PAI/Tank/ros2_ws/install/yolov8_detector'
