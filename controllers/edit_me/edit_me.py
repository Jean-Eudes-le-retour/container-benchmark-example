"""Simple robot controller."""

from controller import Robot
import sys

# Define the target motor position in radians.
target = 4

# Get pointer to the robot.
robot = Robot()

# Get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# Print the program output on the console
print("Move the motors of the Thymio II to position " + str(target) + ".")

# Set the target position of the left and right wheels motors.
robot.getDevice("motor.left").setPosition(target)
robot.getDevice("motor.right").setPosition(target)

# TODO: need to find a way of stopping a evaluation if bugged controller
#  (or missing the code below, not calling robot.step, exiting instantly, ...)
while robot.step(timestep) != -1:
    pass