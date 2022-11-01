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

def record_animations(world_config, destination_directory, controllers):
    # Create temporary directory
    subprocess.check_output(['mkdir', '-p', destination_directory])

    #  - change the robot's controller to <extern>
    with open(world_config['file'], 'r') as f:
        world_content = f.read()

    with open(world_config['file'], 'w') as f:
        f.write(
            world_content.replace(f'controller "{os.environ["DEFAULT_CONTROLLER"]}"', 'controller "<extern>"')
        )
    
    #  - change RECORD_ANIMATION to True
    with open("controllers/supervisor/supervisor.py", 'r') as f:
        supervisor_content = f.read()

    with open("controllers/supervisor/supervisor.py", 'w') as f:
        f.write(
            supervisor_content.replace("RECORD_ANIMATION = False", "RECORD_ANIMATION = True")
        )

    #  - set variables for recorder.py
    with open("controllers/supervisor/recorder/recorder.py", 'r') as f:
        recorder_content = f.read()

    original_fields = (
        'OUTPUT_FOLDER = "tmp/animation"',
        'CONTROLLER_NAME = "animation"',
        'COMPETITOR_ID = 0'
    )
    updated_fields = (
        f'OUTPUT_FOLDER = "{destination_directory}"',
        f'CONTROLLER_NAME = "{controllers[0]}"',
        f'COMPETITOR_ID = {controllers[0].split("_")[1]}'
    )

    updated_recorder = recorder_content
    for original_field, updated_field in zip(original_fields, updated_fields):
        updated_recorder = updated_recorder.replace(original_field, updated_field)
    
    with open("controllers/supervisor/recorder/recorder.py", 'w') as f:
        f.write(updated_recorder)
    
    # build the animator and the controller containers with their respective Dockerfile
    subprocess.run(["docker", "build", "-t", "animator-webots", "-f", "headless_animator_Dockerfile", "."])
    subprocess.run(["docker", "build", "-t", "controller-docker", "-f", "controller_Dockerfile", "."])

    webots_process = subprocess.Popen(
        [
            "docker", "run", "-t", "--rm",
            "--mount", f'type=bind,source={os.getcwd()}/tmp/animation,target=/usr/local/tmp/animation',
            "-p", "3005:1234", "animator-webots"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf-8'
    )

    # read webots' stdout to know when to start the competitor's controller
    already_launched_controller = False
    while webots_process.poll() is None:
        realtime_output = webots_process.stdout.readline()
        if not already_launched_controller and "waiting for connection" in realtime_output:
                print("Webots ready for controller, launching controller container...")
                subprocess.run(["docker", "run", "--rm", "controller-docker"])
                already_launched_controller = True
        print(realtime_output.replace('\n', ''))
    
    # Reset world file
    with open(world_config['file'], 'w') as f:
        f.write(world_content)
    # Reset supervisor file
    with open("controllers/supervisor/supervisor.py", 'w') as f:
        f.write(supervisor_content)
    # Reset recorder file
    with open("controllers/supervisor/recorder/recorder.py", 'w') as f:
        f.write(recorder_content)
    