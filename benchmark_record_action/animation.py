#!/usr/bin/env python3
#
# Copyright 1996-2020 Cyberbotics Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import os

def record_animations(world_config, destination_directory, controller_name):
    # Create temporary directory
    subprocess.check_output(['mkdir', '-p', destination_directory])

    # Temporary file changes:
    #  - World file: change the robot's controller to <extern>
    world_content = _replace_field(world_config['file'],
        (f'controller "{os.environ["DEFAULT_CONTROLLER"]}"',), ('controller "<extern>"',))
    
    #  - Supervisor controller: change RECORD_ANIMATION to True
    supervisor_content = _replace_field("controllers/supervisor/supervisor.py",
        ("RECORD_ANIMATION = False",), ("RECORD_ANIMATION = True",))

    #  - Recorder library: set variables for recorder.py
    recorder_content = _replace_field(
        "controllers/supervisor/recorder/recorder.py",
        (
            'OUTPUT_FOLDER = "storage/"',
            'CONTROLLER_NAME = "animation_0"',
            'MAX_DURATION = 10',
            'METRIC = "percent"'
        ),
        (
            f'OUTPUT_FOLDER = "{destination_directory}/"',
            f'CONTROLLER_NAME = "{controller_name}"',
            f'MAX_DURATION = {world_config["max-duration"]}',
            f'METRIC = "{world_config["metric"]}"'
        )
    )
    
    # Build the recorder and the controller containers with their respective Dockerfile
    subprocess.check_output([
        "docker", "build",
        "-t", "recorder-webots",
        "-f", "recorder_Dockerfile", "."
    ])
    # - Build the controller container from the cloned repository
    subprocess.check_output([
        "docker", "build",
        "-t", "controller-docker",
        "-f", f"controllers/{controller_name}/controller_Dockerfile",
        f"controllers/{controller_name}"
    ])

    # Run the Webots container with Popen to read the stdout
    webots_process = subprocess.Popen(
        [
            "docker", "run", "-t", "--rm",
            "--mount", f'type=bind,source={os.getcwd()}/tmp/animation,target=/usr/local/tmp/animation',
            "-p", "3005:1234", "recorder-webots"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf-8'
    )

    # - Read webots' stdout in real-time to know when to start the competitor's controller
    already_launched_controller = False
    while webots_process.poll() is None:
        realtime_output = webots_process.stdout.readline()
        print(realtime_output.replace('\n', ''))
        if not already_launched_controller and "waiting for connection" in realtime_output:
                print("Webots ready for controller, launching controller container...")
                subprocess.Popen(["docker", "run", "--rm", "controller-docker"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                already_launched_controller = True
        if already_launched_controller and "performance_line:" in realtime_output:
            performance = realtime_output.strip().replace("performance_line:", "")
        if ("docker" in realtime_output and "Error" in realtime_output) or ("'supervisor' controller exited with status: 1" in realtime_output):
            subprocess.run(['/bin/bash', '-c', 'docker kill "$( docker ps -f "ancestor=recorder-webots" -q )"'])
            subprocess.run(['/bin/bash', '-c', 'docker kill "$( docker ps -f "ancestor=controller-webots" -q )"'])
    
    # Removing the temporary changes:
    # - Restoring the world file
    with open(world_config['file'], 'w') as f:
        f.write(world_content)
    # - Restoring the supervisor controller
    with open("controllers/supervisor/supervisor.py", 'w') as f:
        f.write(supervisor_content)
    # - Restoring the recorder library
    with open("controllers/supervisor/recorder/recorder.py", 'w') as f:
        f.write(recorder_content)
    
    return performance

def _replace_field(file, original_fields, updated_fields):
    with open(file, 'r') as f:
        file_content = f.read()

    updated_file = file_content
    for original_field, updated_field in zip(original_fields, updated_fields):
        updated_file = updated_file.replace(original_field, updated_field)
    
    with open(file, 'w') as f:
        f.write(updated_file)
    return file_content