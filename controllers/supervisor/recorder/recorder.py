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

import argparse
import os
from datetime import datetime
import math
import time

# Constants overwritten by animation.py
MAX_DURATION = 10
METRIC = "percent"
OUTPUT_FOLDER = "storage/"
CONTROLLER_NAME = "animation_0"

def time_convert(time):
    minutes = time / 60
    absolute_minutes =  math.floor(minutes)
    minutes_string = str(absolute_minutes).zfill(2)
    seconds = (minutes - absolute_minutes) * 60
    absolute_seconds =  math.floor(seconds)
    seconds_string = str(absolute_seconds).zfill(2)
    cs = math.floor((seconds - absolute_seconds) * 100)
    cs_string = str(cs).zfill(2)
    return minutes_string + "." + seconds_string + "." + cs_string

def animation_start_and_connection_wait(supervisor):
    supervisor.simulationSetMode(supervisor.SIMULATION_MODE_PAUSE)
    time.sleep(2)
    supervisor.simulationSetMode(supervisor.SIMULATION_MODE_REAL_TIME)
    supervisor.animationStartRecording(f"../../{OUTPUT_FOLDER}{CONTROLLER_NAME}.html")

def animation_stop(supervisor, timestep):
    for _ in range(50):
        supervisor.step(timestep)
    supervisor.animationStopRecording()

def record_performance(running, performance):
    if not running:
        message = "Benchmark completed."
        performance_line = _message_format(performance)
    elif METRIC != 'time-duration':
        message = "Benchmark failed: time limit reached."
        performance_line = _message_format(0)
    else:
        message = "Benchmark completed with duration at time limit."
        performance_line = _message_format(MAX_DURATION)

    print(f"performance_line:{performance_line}")

def _message_format(performance):
    if performance == 0:
        performance_string = "failure"
    elif METRIC == "time-duration" or METRIC == "time-speed":
        performance_string = time_convert(performance)
    elif METRIC ==  "percent":
        performance_string = str(round(performance * 100, 2)) + '%'
    elif METRIC == "distance":
        performance_string = "{:.3f} m.".format(performance)
    return f"{CONTROLLER_NAME.split('_')[1]}:{performance}:{performance_string}:{datetime.today().strftime('%Y-%m-%d')}"