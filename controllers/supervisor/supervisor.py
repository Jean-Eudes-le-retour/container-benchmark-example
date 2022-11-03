"""Supervisor of the Robot Programming benchmark."""

from controller import Supervisor
import os
import sys

# Constant used for the automated benchmark evaluation script
# - can also be used to generate an animation in storage folder if set to True
RECORD_ANIMATION = False

if RECORD_ANIMATION:
    import recorder.recorder as rec

def benchmarkPerformance(message):
    benchmark_name = message.split(':')[1]
    benchmark_performance_string = message.split(':')[3]
    print(benchmark_name + ' Benchmark complete! Your performance was ' + benchmark_performance_string)

supervisor = Supervisor()

timestep = int(supervisor.getBasicTimeStep())

thymio = supervisor.getFromDef("BENCHMARK_ROBOT")
translation = thymio.getField("translation")

if RECORD_ANIMATION:
    # Recorder code: wait for the controller to connect and start the animation
    rec.animation_start_and_connection_wait(supervisor)
    step_max = 1000 * rec.MAX_DURATION / timestep
    step_counter = 0

tx = 0
running = True
while supervisor.step(timestep) != -1 and running:
    t = translation.getSFVec3f()
    if running:
        percent = 1 - abs(0.25 + t[0]) / 0.25
        if percent < 0:
            percent = 0
        if t[0] < -0.01 and abs(t[0] - tx) < 0.0001:  # away from starting position and not moving any more
            running = False
            name = 'Robot Programming'
            message = f'success:{name}:{percent}:{percent*100:.2f}%'
        else:
            message = f"percent:{percent}"
        supervisor.wwiSendText(message)
        tx = t[0]
    if RECORD_ANIMATION:
        # Stops the simulation if the controller takes too much time
        step_counter += 1
        if step_counter >= step_max:
            break

if RECORD_ANIMATION:
    # Write performance to file, stop recording and close Webots
    rec.record_performance(running, percent)
    rec.animation_stop(supervisor, timestep)
    supervisor.simulationQuit(0)
else:
    benchmarkPerformance(message)

supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)
