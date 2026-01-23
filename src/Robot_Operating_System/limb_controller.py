import yaml
import math
import logging
import socket
import time

# Establishing the logger for the limb controller
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s    %(levelname)s    %(message)s",
    handlers=[
        logging.FileHandler("limb_controller.log", mode="a"),
    ],
)


class Limb:

    def __init__(self, config_file, limb_name):
        """
        Initialize a single robotic limb using parameters from a YAML config file.

        This method loads servo channel assignments, limb geometry, motion limits,
        and hardware connection settings for the specified limb. If the robot is
        marked as connected, the PCA9685 servo controller is initialized and each
        servo channel is configured with its appropriate pulse width range.

        Args:
            config_file (str): Path to the YAML configuration file.
            limb_name (str): Name of the limb section within the config (e.g. "front_left").

        """

        with open(config_file) as f:
            config = yaml.safe_load(f)

        logging.info(f"Initializing {limb_name} on {config["robot"]["name"]}")
        self.limb_name = limb_name
        self.coax = config[limb_name]["coax_loc"]
        self.femur = config[limb_name]["femur_loc"]
        self.tibia = config[limb_name]["tibia_loc"]

        self.coax_length = config[limb_name]["coax_length"]
        self.femur_length = config[limb_name]["femur_length"]
        self.tibia_length = config[limb_name]["tibia_length"]

        self.x_min = config[limb_name]["min_x"]
        self.x_max = config[limb_name]["max_x"]
        self.y_min = config[limb_name]["min_y"]
        self.y_max = config[limb_name]["max_y"]
        self.z_min = config[limb_name]["min_z"]
        self.z_max = config[limb_name]["max_z"]

        self.connected = config["robot"]["connected"]

        if self.connected:
            from adafruit_servokit import ServoKit
            import board
            import busio

            i2c = busio.I2C(board.SCL, board.SDA)
            self.controller_kit = ServoKit(
                channels=16, i2c=i2c
            )  # Initialize the ServoKit with 16 channels (for the PCA9685)

            self.controller_kit.servo[self.coax].set_pulse_width_range(
                config[limb_name]["coax_min_pulse"], config[limb_name]["coax_max_pulse"]
            )
            self.controller_kit.servo[self.femur].set_pulse_width_range(
                config[limb_name]["femur_min_pulse"],
                config[limb_name]["femur_max_pulse"],
            )
            self.controller_kit.servo[self.tibia].set_pulse_width_range(
                config[limb_name]["tibia_min_pulse"],
                config[limb_name]["tibia_max_pulse"],
            )

        self.inverse = config[limb_name]["inverse"]

        self.HSA_current = 0
        self.HSA_target = 0
        self.FSA_current = 0
        self.FSA_target = 0
        self.TSA_current = 0
        self.TSA_target = 0

    # **********************************************************************************************************************
    def move_limb(self, x, y, z):
        """
        Move the limb to a target (x, y, z) position using inverse kinematics.

        This method computes the required joint angles for the coax, femur, and tibia
        using trigonometric IK, applies calibration offsets, and sends the resulting
        angles to the servo controller if hardware is connected.

        Args:
            x (float): Target X coordinate relative to the limb base.
            y (float): Target Y coordinate relative to the limb base.
            z (float): Target Z coordinate (height) relative to the limb base.

        Notes:
            - Applies inverse mode for mirrored limbs.
            - Uses femur/tibia geometry to compute knee and hip angles.
            - Sends angles to hardware only when `connected=True`.
        """

        logging.info(f"Repositioning leg {self.limb_name} to {x}, {y}, {z}")
        if x < self.x_min:
            logging.warning(f"{self.limb_name} x is out of limits as {x}")
            x = self.x_min

        if x > self.x_max:
            logging.warning(f"{self.limb_name} x is out of limits as {x}")
            x = self.x_max

        if y < self.y_min:
            logging.warning(f"{self.limb_name} y is out of limits as {y}")
            y = self.y_min

        if y > self.y_max:
            logging.warning(f"{self.limb_name} y is out of limits as {y}")
            y = self.y_max

        if z < self.z_min:
            logging.warning(f"{self.limb_name} z is out of limits as {z}")
            z = self.z_min

        if z > self.z_max:
            logging.warning(f"{self.limb_name} z is out of limits as {z}")
            z = self.z_max

        # Ensures no values are divided by zero
        if z == 0:
            z = 0.0001
        if x == 0:
            x = 0.0001
        if y == 0:
            y = 0.0001

        # Calculates the coax angle.
        h = math.sqrt(math.pow(x, 2) + math.pow(y, 2))
        self.HSA_target = math.degrees(math.atan(x / y))
        if self.inverse:
            self.HSA_target = 90 - abs(self.HSA_target)

        logging.info(f"Coax Angle: {self.HSA_target}")
        if self.connected:
            self.controller_kit.servo[self.coax].angle = self.HSA_target * 2

        # Calculates to tibia angle.
        l = math.sqrt(math.pow(h - self.coax_length, 2) + math.pow(z, 2))
        tsa = math.acos(
            (
                math.pow(self.tibia_length, 2)
                + math.pow(self.femur_length, 2)
                - math.pow(l, 2)
            )
            / (2 * self.tibia_length * self.femur_length)
        )
        self.TSA_target = math.degrees(tsa)

        logging.info(f"Tibia Angle: {self.TSA_target}")
        if self.connected:
            self.controller_kit.servo[self.tibia].angle = self.TSA_target

        # Calculates to femur angle.
        vb = math.acos(
            (
                math.pow(l, 2)
                + math.pow(self.femur_length, 2)
                - math.pow(self.tibia_length, 2)
            )
            / (2 * l * self.femur_length)
        )
        va = math.atan((h - self.coax_length) / z)
        femur_angle = vb + va
        self.FSA_target = math.degrees(femur_angle)

        logging.info(f"Femur Angle: {self.FSA_target}")
        if self.connected:
            self.controller_kit.servo[self.femur].angle = 2 * (90 - self.FSA_target)

    # **********************************************************************************************************************
    def move_joint(self, joint, angle):
        """
        Move a single joint to a specified angle for testing or calibration.

        This helper method directly commands one of the limb's servos—coax,
        femur, or tibia—to the given angle. It is primarily used for manual
        cycling, debugging, or verifying servo motion without running full
        inverse kinematics.

        Args:
            joint (str): Name of the joint to move. Must be one of:
                - "coax"
                - "femur"
                - "tibia"
            angle (float): Target angle in degrees to send to the servo.

        Notes:
            - Logs a message when a joint is cycled.
            - If an invalid joint name is provided, no action is taken.
            - Assumes hardware is connected and initialized.
        """

        if joint == "coax":
            logging.info(f"Cycling coax to {angle}")
            if self.connected:
                self.controller_kit.servo[self.coax].angle = angle
        elif joint == "tibia":
            logging.info(f"Cycling tibia to {angle}")
            if self.connected:
                self.controller_kit.servo[self.tibia].angle = angle
        elif joint == "femur":
            logging.info(f"Cycling femur to {angle}")
            if self.connected:
                self.controller_kit.servo[self.femur].angle = angle
        else:
            logging.info(f"No matching joint identified for {joint}")


# **********************************************************************************************************************
def limb_controller():
    udp_ip = None
    udp_port = None

    config_path = "limb_controller_config.yml"  # The config file that will be used to load parameters.

    # Loading the IP and traffic information from the config file.
    logging.info(f"Loading config file from: {config_path}")
    with open(config_path) as f:
        config = yaml.safe_load(f)
        udp_ip = config["robot"]["UDP_IP"]
        udp_port = config["robot"]["UDP_PORT"]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))
    logging.info(f"Limb controller is listening for UDP packets on {udp_ip}:{udp_port}")

    limbs = {
        limb_name: Limb(config_path, limb_name)
        for limb_name in config.keys()
        if limb_name != "robot"
    }
    logging.info(f"Loading limbs: {limbs}")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode("utf-8").replace(" ", "")
        logging.info(message)
        try:
            if message.startswith("shutdown"):
                logging.info("Shutting down leg controller")
                return

            else:
                command_list = message.split(",")
                if command_list[0] == "move_limb":
                    target_limb = command_list[1]
                    if target_limb in limbs:
                        limbs[target_limb].move_limb(
                            int(command_list[2]),
                            int(command_list[3]),
                            int(command_list[4]),
                        )

                    else:
                        logging.info(f"No leg matched that name: {command_list[1]}")

                if command_list[0] == "move_joint":
                    target_limb = command_list[1]
                    if target_limb in limbs:
                        limbs[target_limb].move_joint(
                            command_list[2], int(command_list[3])
                        )

                    else:
                        logging.info(f"No leg matched that name: {command_list[1]}")

        except Exception as e:
            logging.warning(f"Error in message: {e}")

        time.sleep(0.05)


if __name__ == "__main__":
    limb_controller()
