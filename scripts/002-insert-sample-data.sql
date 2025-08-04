-- Insert sample ROS domains
INSERT INTO ros_domains (name, description, agent_status) VALUES
('robotics_lab', 'Main robotics laboratory domain for research projects', 'active'),
('warehouse_automation', 'Automated warehouse management system domain', 'active'),
('autonomous_vehicle', 'Self-driving car development domain', 'active'),
('drone_swarm', 'Multi-drone coordination and control domain', 'inactive'),
('manufacturing_line', 'Industrial manufacturing automation domain', 'active'),
('home_assistant', 'Smart home automation and assistance domain', 'error');

-- Insert sample nodes
INSERT INTO nodes (name, domain_id, node_type, status, metadata) VALUES
-- Robotics Lab nodes
('camera_sensor', 1, 'topic', 'active', '{"frequency": 30, "resolution": "1920x1080", "format": "RGB"}'),
('lidar_scanner', 1, 'topic', 'active', '{"range": 100, "accuracy": 0.1, "scan_rate": 10}'),
('motion_planner', 1, 'service', 'active', '{"algorithm": "RRT*", "timeout": 5.0}'),
('gripper_controller', 1, 'action', 'active', '{"max_force": 50, "precision": 0.01}'),
('robot_state', 1, 'topic', 'active', '{"joints": 7, "update_rate": 100}'),

-- Warehouse Automation nodes
('inventory_scanner', 2, 'topic', 'active', '{"scan_type": "barcode", "range": 5}'),
('conveyor_control', 2, 'service', 'active', '{"speed_range": [0, 2], "direction": "bidirectional"}'),
('package_sorter', 2, 'action', 'active', '{"capacity": 1000, "sort_criteria": ["size", "weight", "destination"]}'),
('warehouse_map', 2, 'topic', 'active', '{"resolution": 0.05, "size": [100, 50]}'),
('agv_fleet', 2, 'service', 'active', '{"fleet_size": 10, "max_payload": 500}'),

-- Autonomous Vehicle nodes
('gps_receiver', 3, 'topic', 'active', '{"accuracy": 0.1, "update_rate": 10}'),
('imu_sensor', 3, 'topic', 'active', '{"gyro_range": 2000, "accel_range": 16}'),
('path_planning', 3, 'service', 'active', '{"algorithm": "A*", "real_time": true}'),
('vehicle_control', 3, 'action', 'active', '{"max_speed": 60, "max_acceleration": 5}'),
('obstacle_detection', 3, 'topic', 'active', '{"sensor_fusion": true, "detection_range": 50}'),

-- Drone Swarm nodes (inactive domain)
('drone_commander', 4, 'service', 'inactive', '{"max_drones": 20, "formation_types": ["line", "circle", "grid"]}'),
('swarm_coordination', 4, 'topic', 'inactive', '{"communication_range": 1000, "update_rate": 20}'),
('battery_monitor', 4, 'topic', 'inactive', '{"voltage_range": [11.1, 12.6], "capacity": 5000}'),

-- Manufacturing Line nodes
('quality_inspector', 5, 'service', 'active', '{"inspection_types": ["visual", "dimensional"], "accuracy": 99.5}'),
('assembly_robot', 5, 'action', 'active', '{"degrees_of_freedom": 6, "payload": 10}'),
('production_scheduler', 5, 'service', 'active', '{"optimization": "throughput", "constraints": ["time", "resources"]}'),
('sensor_array', 5, 'topic', 'active', '{"sensors": 12, "types": ["temperature", "pressure", "vibration"]}'),

-- Home Assistant nodes (error domain)
('smart_thermostat', 6, 'service', 'error', '{"temperature_range": [10, 35], "zones": 4}'),
('security_system', 6, 'topic', 'error', '{"cameras": 8, "sensors": 16, "zones": ["indoor", "outdoor"]}'),
('voice_assistant', 6, 'service', 'error', '{"languages": ["en", "ko", "ja"], "wake_words": ["hey_home"]}}');

-- Insert sample node connections
INSERT INTO node_connections (source_node_id, target_node_id, connection_type, status, metadata) VALUES
-- Robotics Lab connections
(1, 4, 'publisher', 'active', '{"topic": "/camera/image_raw", "qos": "reliable"}'),
(2, 3, 'publisher', 'active', '{"topic": "/scan", "qos": "best_effort"}'),
(3, 4, 'client', 'active', '{"service": "/plan_motion", "timeout": 10}'),
(5, 3, 'publisher', 'active', '{"topic": "/joint_states", "qos": "reliable"}'),

-- Warehouse Automation connections
(6, 8, 'publisher', 'active', '{"topic": "/inventory_data", "qos": "reliable"}'),
(7, 8, 'client', 'active', '{"service": "/conveyor_control", "timeout": 5}'),
(9, 10, 'publisher', 'active', '{"topic": "/warehouse_map", "qos": "reliable"}'),
(10, 8, 'client', 'active', '{"service": "/agv_dispatch", "timeout": 15}'),

-- Autonomous Vehicle connections
(11, 13, 'publisher', 'active', '{"topic": "/gps/fix", "qos": "reliable"}'),
(12, 13, 'publisher', 'active', '{"topic": "/imu/data", "qos": "reliable"}'),
(13, 14, 'client', 'active', '{"service": "/plan_path", "timeout": 20}'),
(15, 14, 'publisher', 'active', '{"topic": "/obstacles", "qos": "best_effort"}'),

-- Cross-domain connections (Warehouse to Autonomous Vehicle)
(9, 11, 'publisher', 'active', '{"topic": "/shared_map", "qos": "reliable"}'),
(10, 13, 'client', 'active', '{"service": "/coordinate_vehicles", "timeout": 30}'),

-- Manufacturing Line connections
(17, 18, 'client', 'active', '{"service": "/quality_check", "timeout": 10}'),
(19, 17, 'client', 'active', '{"service": "/schedule_production", "timeout": 5}'),
(20, 17, 'publisher', 'active', '{"topic": "/sensor_readings", "qos": "reliable"}'),

-- Inactive connections for demonstration
(16, 17, 'subscriber', 'inactive', '{"topic": "/drone_status", "qos": "reliable"}'),
(21, 22, 'publisher', 'inactive', '{"topic": "/home_status", "qos": "best_effort"}');

-- Insert sample messages
INSERT INTO node_messages (connection_id, message_type, payload) VALUES
-- Recent messages from active connections
(1, 'sensor_msgs/Image', '{"header": {"stamp": {"sec": 1704067200, "nanosec": 0}, "frame_id": "camera_link"}, "height": 1080, "width": 1920, "encoding": "rgb8", "data": "base64_encoded_image_data"}'),
(2, 'sensor_msgs/LaserScan', '{"header": {"stamp": {"sec": 1704067201, "nanosec": 0}, "frame_id": "laser_link"}, "angle_min": -3.14159, "angle_max": 3.14159, "ranges": [1.2, 1.5, 2.0, 1.8, 0.5]}'),
(3, 'moveit_msgs/MotionPlanRequest', '{"workspace_parameters": {"header": {"frame_id": "base_link"}, "min_corner": {"x": -1, "y": -1, "z": 0}, "max_corner": {"x": 1, "y": 1, "z": 2}}, "start_state": {"joint_state": {"name": ["joint1", "joint2"], "position": [0.0, 0.0]}}}'),
(4, 'sensor_msgs/JointState', '{"header": {"stamp": {"sec": 1704067202, "nanosec": 0}}, "name": ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7"], "position": [0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7], "velocity": [0.01, -0.02, 0.03, -0.04, 0.05, -0.06, 0.07]}'),

(5, 'warehouse_msgs/InventoryItem', '{"barcode": "1234567890123", "name": "Widget A", "quantity": 50, "location": {"aisle": 3, "shelf": 2, "bin": 5}, "weight": 2.5}'),
(6, 'std_msgs/String', '{"data": "conveyor_start_forward_speed_1.5"}'),
(7, 'nav_msgs/OccupancyGrid', '{"header": {"stamp": {"sec": 1704067203, "nanosec": 0}, "frame_id": "map"}, "info": {"resolution": 0.05, "width": 2000, "height": 1000, "origin": {"position": {"x": -50, "y": -25, "z": 0}}}, "data": [0, 0, 0, 100, 100, 0, 0]}'),
(8, 'fleet_msgs/RobotState', '{"name": "agv_001", "battery_percent": 85.5, "location": {"x": 10.5, "y": 5.2, "theta": 1.57}, "mode": {"mode": 2}, "task_id": "task_123"}'),

(9, 'sensor_msgs/NavSatFix', '{"header": {"stamp": {"sec": 1704067204, "nanosec": 0}, "frame_id": "gps_link"}, "status": {"status": 0, "service": 1}, "latitude": 37.7749, "longitude": -122.4194, "altitude": 10.5, "position_covariance": [1, 0, 0, 0, 1, 0, 0, 0, 1]}'),
(10, 'sensor_msgs/Imu', '{"header": {"stamp": {"sec": 1704067205, "nanosec": 0}, "frame_id": "imu_link"}, "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}, "angular_velocity": {"x": 0.01, "y": -0.02, "z": 0.005}, "linear_acceleration": {"x": 0.1, "y": 0.05, "z": 9.81}}'),
(11, 'nav_msgs/Path', '{"header": {"stamp": {"sec": 1704067206, "nanosec": 0}, "frame_id": "map"}, "poses": [{"header": {"frame_id": "map"}, "pose": {"position": {"x": 0, "y": 0, "z": 0}, "orientation": {"w": 1}}}, {"header": {"frame_id": "map"}, "pose": {"position": {"x": 1, "y": 0, "z": 0}, "orientation": {"w": 1}}}]}'),
(12, 'obstacle_msgs/ObstacleArray', '{"header": {"stamp": {"sec": 1704067207, "nanosec": 0}, "frame_id": "base_link"}, "obstacles": [{"id": 1, "polygon": {"points": [{"x": 2.0, "y": 1.0}, {"x": 2.5, "y": 1.0}, {"x": 2.5, "y": 1.5}, {"x": 2.0, "y": 1.5}]}, "velocities": {"twist": {"linear": {"x": 0, "y": 0}, "angular": {"z": 0}}}}]}'),

-- Cross-domain messages
(13, 'nav_msgs/OccupancyGrid', '{"header": {"stamp": {"sec": 1704067208, "nanosec": 0}, "frame_id": "shared_map"}, "info": {"resolution": 0.1, "width": 1000, "height": 1000}, "data": [0, 0, 100, 0, 0]}'),
(14, 'coordination_msgs/VehicleCommand', '{"vehicle_id": "av_001", "command": "navigate_to_pickup", "target_location": {"x": 15.5, "y": 8.2, "z": 0}, "priority": 1, "estimated_duration": 300}'),

-- Manufacturing messages
(15, 'quality_msgs/InspectionResult', '{"part_id": "part_12345", "inspection_type": "visual", "result": "pass", "confidence": 0.98, "defects": [], "timestamp": {"sec": 1704067209, "nanosec": 0}}'),
(16, 'production_msgs/Schedule', '{"shift_id": "morning_001", "tasks": [{"task_id": "asm_001", "part_type": "widget_a", "quantity": 100, "priority": 1, "estimated_time": 3600}], "start_time": {"sec": 1704067200, "nanosec": 0}}'),
(17, 'sensor_msgs/Temperature', '{"header": {"stamp": {"sec": 1704067210, "nanosec": 0}, "frame_id": "temp_sensor_01"}, "temperature": 45.2, "variance": 0.1}');

-- Insert additional recent messages for better demonstration
INSERT INTO node_messages (connection_id, message_type, payload, timestamp) VALUES
(1, 'sensor_msgs/Image', '{"header": {"stamp": {"sec": 1704067220, "nanosec": 0}}, "height": 1080, "width": 1920, "encoding": "rgb8"}', NOW() - INTERVAL '5 minutes'),
(2, 'sensor_msgs/LaserScan', '{"ranges": [1.1, 1.6, 2.1, 1.9, 0.4]}', NOW() - INTERVAL '3 minutes'),
(5, 'warehouse_msgs/InventoryItem', '{"barcode": "9876543210987", "name": "Widget B", "quantity": 25}', NOW() - INTERVAL '2 minutes'),
(9, 'sensor_msgs/NavSatFix', '{"latitude": 37.7750, "longitude": -122.4195, "altitude": 10.6}', NOW() - INTERVAL '1 minute'),
(15, 'quality_msgs/InspectionResult', '{"part_id": "part_12346", "result": "pass", "confidence": 0.99}', NOW() - INTERVAL '30 seconds');
