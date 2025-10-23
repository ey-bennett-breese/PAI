# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION
# SPDX-License-Identifier: Apache-2.0

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    use_sim_time = LaunchConfiguration("use_sim_time", default="True")

    map_dir = LaunchConfiguration(
        "map",
        default=os.path.join(
            get_package_share_directory("tank_navigation"),
            "maps",
            "tank_alpharetta_navigation.yaml",
        ),
    )

    param_dir = LaunchConfiguration(
        "params_file",
        default=os.path.join(
            get_package_share_directory("tank_navigation"),
            "params",
            "tank_navigation_params.yaml",
        ),
    )

    nav2_bringup_launch_dir = os.path.join(
        get_package_share_directory("nav2_bringup"), "launch"
    )

    rviz_config_dir = os.path.join(
        get_package_share_directory("tank_navigation"),
        "rviz2",
        "tank_navigation.rviz",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "map", default_value=map_dir, description="Full path to map file to load"
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=param_dir,
                description="Full path to param file to load",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use simulation clock if true",
            ),

            # ------------------------------------------------------------
            # RViz2 with config
            # ------------------------------------------------------------
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nav2_bringup_launch_dir, "rviz_launch.py")
                ),
                launch_arguments={
                    "namespace": "",
                    "use_namespace": "False",
                    "rviz_config": rviz_config_dir,
                }.items(),
            ),

            # ------------------------------------------------------------
            # Nav2 bringup (includes map_server, amcl, etc.)
            # ------------------------------------------------------------
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nav2_bringup_launch_dir, "bringup_launch.py")
                ),
                launch_arguments={
                    "map": map_dir,
                    "use_sim_time": use_sim_time,
                    "params_file": param_dir,
                }.items(),
            ),

            # ------------------------------------------------------------
            # Lifecycle Manager for localization (map_server + amcl)
            # ------------------------------------------------------------
            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="lifecycle_manager_localization",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "autostart": True,
                        "node_names": ["map_server", "amcl"],
                    }
                ],
            ),

            # ------------------------------------------------------------
            # Static TF publishers to complete TF tree
            # ------------------------------------------------------------

            # map -> odom (AMCL will later update this, but we need an initial link)
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="static_map_to_odom_tf",
                arguments=["0", "0", "0", "0", "0", "0", "map", "odom"],
            ),

            # odom -> base_link (if your robot or sim doesn't already publish it)
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="static_odom_to_base_link_tf",
                arguments=["0", "0", "0", "0", "0", "0", "odom", "base_link"],
            ),
        ]
    )

