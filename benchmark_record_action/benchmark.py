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

import os
import shutil
from pathlib import Path
import subprocess
from benchmark_record_action.animation import record_animations
import benchmark_record_action.utils.git as git

DESTINATION_DIRECTORY = 'tmp/animation'

class Competitor:
    def __init__(self, id, controller_repository):
        self.id = id
        self.username = controller_repository.split('/')[0]
        self.repository_name = controller_repository.split('/')[1]
        self.controller_repository = controller_repository
        self.controller_path = None
        self.controller_name = None


def benchmark(config):
    # get world configuration
    world_config = config['world']

    # Initialise Git
    git.init()

    # Parse input competitor
    competitor = _get_competitor()

    # Clone and run Docker containers
    _clone_competitor_controller(competitor)
    _run_competitor_controller(world_config, competitor)
    _remove_competitor_controller()

    # Commit and Push updates
    git.push(message="record and update benchmark animations")


def _get_competitor():
    print("\nParsing competitor...")

    input_competitor = os.environ['INPUT_INDIVIDUAL_EVALUATION']
    competitor = Competitor(
        id = input_competitor.split(":")[0],
        controller_repository = input_competitor.split(":")[1].strip()
    )
    
    print("done parsing competitor")

    return competitor


def _clone_competitor_controller(competitor):
    print("\nCloning competitor repo...")

    competitor.controller_name = "competitor_" + competitor.id + "_" + competitor.username
    competitor.controller_path = os.path.join('controllers', competitor.controller_name)

    repo = 'https://{}:{}@github.com/{}/{}'.format(
        "Benchmark_Evaluator",
        os.environ['INPUT_FETCH_TOKEN'],
        competitor.username,
        competitor.repository_name
    )
    subprocess.check_output(f'git clone {repo} {competitor.controller_path}', shell=True)

    print("done fetching repo")


def _run_competitor_controller(world_config, competitor):
    print("\nRunning competitor's controller...")

    # Save original world file
    with open(world_config['file'], 'r') as f:
        world_content = f.read()

    # Run controller and record animation
    _record_benchmark_animation(world_config, competitor)

    # Revert to original world file
    with open(world_config['file'], 'w') as f:
        f.write(world_content)

    print("done running competitor's controller")


def _record_benchmark_animation(world_config, competitor):

    # Record animation and return performance
    performance = record_animations(
        world_config,
        DESTINATION_DIRECTORY,
        competitor.controller_name
    )

    # Update competitors.txt and animation
    _refresh_perf_and_animation(performance, competitor)

    # Remove tmp files
    shutil.rmtree('tmp')

    print('done recording animations')

def _refresh_perf_and_animation(performance, competitor):

    # Move animations and format new performance
    updated_competitor = _move_animations_and_format_perf(performance, competitor)

    # Only change the requested competitor's performance
    tmp_competitors = ""
    with open('competitors.txt', 'r') as f:
        for line in f:
            # stripping line break
            line = line.strip()
            test_id = line.split(':')[0]

            if test_id == competitor.id:
                new_line = updated_competitor.strip()
            else:
                new_line = line
            # concatenate the new string and add an end-line break
            tmp_competitors = tmp_competitors + new_line + "\n"
    
    with open('competitors.txt', 'w') as f:
        f.write(tmp_competitors)

def _move_animations_and_format_perf(performance, competitor):
    
    _, performance_value, performance_string, date = performance.split(':')

    # performance
    updated_competitor = f"{competitor.id}:{competitor.controller_repository}:{performance_value}:{performance_string}:{date}"
    
    # animations
    new_destination_directory = os.path.join('storage', 'wb_animation_' + competitor.id)
    # remove old animation
    subprocess.check_output(['rm', '-r', '-f', new_destination_directory])
    # replace by new animation
    subprocess.check_output(['mkdir', '-p', new_destination_directory])
    subprocess.check_output(f'mv {DESTINATION_DIRECTORY}/{competitor.controller_name}.* {new_destination_directory}', shell=True)
    
    _cleanup_storage_files(new_destination_directory)
    
    return updated_competitor

def _cleanup_storage_files(directory):
    if Path(directory).exists():
        for path in Path(directory).glob('*'):
            path = str(path)
            if path.endswith('.html') or path.endswith('.css'):
                os.remove(path)
            elif path.endswith('.json'):
                os.rename(path, directory + '/animation.json')
            elif path.endswith('.x3d'):
                os.rename(path, directory + '/scene.x3d')


def _remove_competitor_controller():
    for path in Path('controllers').glob('*'):
        controller = str(path).split('/')[1]
        if controller.startswith('competitor'):
            shutil.rmtree(path)
