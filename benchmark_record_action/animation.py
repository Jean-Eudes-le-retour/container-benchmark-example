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
from datetime import datetime
from math import floor

def _generate_animation_recorder_vrml(duration, output, controller_name):
    return (
        f'DEF ANIMATION_RECORDER_SUPERVISOR Robot {{\n'
        f'  name "animation_recorder_supervisor"\n'
        f'  controller "animator"\n'
        f'  controllerArgs [\n'
        f'    "--duration={duration}"\n'
        f'    "--output={output}"\n'
        f'    "--controller={controller_name}"\n'
        f'  ]\n'
        f'  supervisor TRUE\n'
        f'}}\n'
    )

def record_animations(world_config, destination_directory, controller_name):
    # Create temporary directory
    subprocess.check_output(['mkdir', '-p', destination_directory])

    # Temporary file changes*:
    with open(world_config['file'], 'r') as f:
        world_content = f.read()
    updated_file = world_content.replace(f'controller "{os.environ["DEFAULT_CONTROLLER"]}"', 'controller "<extern>"')

    animation_recorder_vrml = _generate_animation_recorder_vrml(
        duration = world_config['max-duration'],
        output = destination_directory,
        controller_name = controller_name
    )

    with open(world_config['file'], 'w') as f:
        f.write(updated_file + animation_recorder_vrml)
    
    # Building the Docker containers
    subprocess.check_output([
        "docker", "build",
        "--build-arg", f'PROJECT_PATH={os.environ["PROJECT_PATH"]}',
        "-t", "recorder-webots",
        "-f", "Dockerfile", "."
    ])
    subprocess.check_output([
        "docker", "build",
        "-t", "controller-docker",
        "-f", f"controllers/{controller_name}/controller_Dockerfile",
        f"controllers/{controller_name}"
    ])

    # Run Webots container with Popen to read the stdout
    webots_docker = subprocess.Popen(
        [
            "docker", "run", "-t", "--rm",
            "--mount", f'type=bind,source={os.getcwd()}/tmp/animation,target={os.environ["PROJECT_PATH"]}/{destination_directory}',
            "-p", "3005:1234",
            "--env", "CI=true",
            "recorder-webots"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf-8'
    )

    already_launched_controller = False
    performance = 0
    timeout = False
    
    while webots_docker.poll() is None:
        realtime_output = webots_docker.stdout.readline()
        print(realtime_output.replace('\n', ''))
        if not already_launched_controller and "waiting for connection" in realtime_output:
                print("Webots ready for controller, launching controller container...")
                subprocess.Popen(
                    ["docker", "run", "--rm", "controller-docker"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
                )
                already_launched_controller = True
        if already_launched_controller and "performance_line:" in realtime_output:
            performance = float(realtime_output.strip().replace("performance_line:", ""))
            break
        elif already_launched_controller and "Controller timeout" in realtime_output:
            timeout = True
            break
    
    # Got what we need, kill the containers
    subprocess.run(['/bin/bash', '-c', 'docker kill "$( docker ps -f "ancestor=recorder-webots" -q )"'])
    subprocess.run(['/bin/bash', '-c', 'docker kill "$( docker ps -f "ancestor=controller-webots" -q )"'])

    # *Restoring temporary file changes
    with open(world_config['file'], 'w') as f:
        f.write(world_content)

    return _get_performance_line(timeout, performance, world_config)

def _get_performance_line(timeout, performance, world_config):
    metric = world_config['metric']
    if not timeout:
        # Benchmark completed normally
        performance_line = _performance_format(performance, metric)
    elif metric != 'time-duration':
        # Benchmark failed: time limit reached
        performance_line = _performance_format(0, metric)
    else:
        # Time-duration benchmark completed with maximum time
        performance_line = _performance_format(world_config['max-duration'], metric)

    return performance_line

def _performance_format(performance, metric):
    if performance == 0:
        performance_string = "failure"
    elif metric == "time-duration" or metric == "time-speed":
        performance_string = _time_convert(performance)
    elif metric ==  "percent":
        performance_string = str(round(performance * 100, 2)) + '%'
    elif metric == "distance":
        performance_string = "{:.3f} m.".format(performance)
    return f"{performance}:{performance_string}:{datetime.today().strftime('%Y-%m-%d')}"

def _time_convert(time):
    minutes = time / 60
    absolute_minutes =  floor(minutes)
    minutes_string = str(absolute_minutes).zfill(2)
    seconds = (minutes - absolute_minutes) * 60
    absolute_seconds =  floor(seconds)
    seconds_string = str(absolute_seconds).zfill(2)
    cs = floor((seconds - absolute_seconds) * 100)
    cs_string = str(cs).zfill(2)
    return minutes_string + "." + seconds_string + "." + cs_string
