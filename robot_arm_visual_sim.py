import matplotlib.pyplot as plt
import numpy as np

class RobotArmSimulator:
    def __init__(self, segment_lengths):
        self.segment_lengths = segment_lengths
        self.num_joints = len(segment_lengths)
        self.angles = [0.0] * self.num_joints  # in degrees

    def set_joint_angles(self, angles):
        if len(angles) != self.num_joints:
            raise ValueError("Angle list length must match number of joints")
        self.angles = angles
        self.draw_arm()

    def draw_arm(self):
        x = [0]
        y = [0]
        theta = 0
        for i in range(self.num_joints):
            theta += np.deg2rad(self.angles[i])
            x.append(x[-1] + self.segment_lengths[i] * np.cos(theta))
            y.append(y[-1] + self.segment_lengths[i] * np.sin(theta))
        plt.clf()
        plt.plot(x, y, marker='o')
        plt.xlim(-sum(self.segment_lengths), sum(self.segment_lengths))
        plt.ylim(0, sum(self.segment_lengths))
        plt.title("Robot Arm Visual Simulator")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.grid(True)
        plt.pause(0.01)

if __name__ == "__main__":
    # Example: 3-joint arm with segments of length 5, 4, 3
    arm = RobotArmSimulator([5, 4, 3])
    plt.ion()
    for angle1 in range(0, 91, 10):
        for angle2 in range(0, 91, 30):
            for angle3 in range(0, 91, 45):
                arm.set_joint_angles([angle1, angle2, angle3])
                plt.pause(0.2)
    plt.ioff()
    plt.show()