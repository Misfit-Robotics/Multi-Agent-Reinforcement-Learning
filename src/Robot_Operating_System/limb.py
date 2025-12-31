import yaml
import math
import logging
import sys
import socket
import time


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s    %(levelname)s    %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


class Limb:

    def __init__(self, config_file, limb_name):

        with open(config_file) as f:
            config = yaml.safe_load(f)

        logging.info(f"Initializing {limb_name} on {config["robot"]["name"]}")
        self.limb_name = limb_name
        self.coax = config[limb_name]["coax_loc"]       #array location of the coax servo
        self.femur = config[limb_name]["femur_loc"]      #array location of the femur servo
        self.tibia = config[limb_name]["tibia_loc"]      #array location of the femur servo# self.tibia = tibia  #array location of the tibia servo

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
            self.controller_kit = ServoKit(channels=16, i2c=i2c) # Initialize the ServoKit with 16 channels (for the PCA9685)
            self.controller_kit.servo[self.coax].set_pulse_width_range(100, 2250)
            self.controller_kit.servo[self.femur].set_pulse_width_range(100, 2250)
            self.controller_kit.servo[self.tibia].set_pulse_width_range(500, 2500)

        self.inverse = config[limb_name]["inverse"]

        self.TIBIA_OFFSET = -15
        self.FEMUR_OFFSET = -45

        self.HSA_current = 0
        self.HSA_target = 0
        self.FSA_current = 0
        self.FSA_target = 0
        self.TSA_current = 0
        self.TSA_target = 0

    def reposition_leg(self, x, y, z):
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

        if z == 0:
            z = 0.0001
        if x == 0:
            x = 0.0001
        if y == 0:
            y = 0.0001



        h = math.sqrt(math.pow(x, 2) + math.pow(y,2))
        self.HSA_target = math.degrees(math.atan(x/y))

        if self.inverse:
                self.HSA_target = 180 - self.HSA_target
        if self.HSA_target < 0:
                self.HSA_target = 90 + self.HSA_target

        if self.connected:
            self.controller_kit.servo[self.coax].angle = self.HSA_target * 2
        else:
            logging.info(f"Coax Angle: {self.HSA_target}")



        l = math.sqrt(math.pow(h, 2) + math.pow(z,2))
        tsa = math.acos((math.pow(self.tibia_length, 2) + math.pow(self.femur_length, 2) - math.pow(l, 2)) / (2 * self.tibia_length * self.femur_length))
        self.TSA_target = math.degrees(tsa) + self.TIBIA_OFFSET
        if self.TSA_target < 15:
                self.TSA_target = 15
                logging.warning("Tibia Unable to Reach")
        if self.TSA_target > 180:
                self.TSA_target = 180
                logging.warning("Tibia Unable to Reach")

        if self.connected:
            self.controller_kit.servo[self.tibia].angle = self.TSA_target
        else:
            logging.info(f"Tibia Angle: {self.TSA_target}")



        vb = math.acos((math.pow(l, 2) + math.pow(self.femur_length, 2) - math.pow(self.tibia_length, 2))/(2 * l * self.femur_length))
        va = math.atan((h-self.coax_length)/z)
        femur_angle = vb+va
        self.FSA_target = math.degrees(femur_angle)

        if self.connected:
            self.controller_kit.servo[self.femur].angle = 2 * (90 - self.FSA_target)
        else:
            logging.info(f"Femur Angle: {self.FSA_target}")


def main():
    udp_ip = None
    udp_port = None

    config_path = "config.yaml"
    logging.info(f"Loading config file from: {config_path}")
    with open(config_path) as f:
        config = yaml.safe_load(f)
        udp_ip = config["robot"]["UDP_IP"]
        udp_port = config["robot"]["UDP_PORT"]
    front_left_limb = Limb(config_path, "FL_Leg")
    logging.info(front_left_limb.limb_name)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))
    logging.info(f"Controller is listening for UDP packets on {udp_ip}:{udp_port}")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode('utf-8')

        try:
            command_list = message.split(',')

            if command_list[0] == front_left_limb.limb_name:
                front_left_limb.reposition_leg(int(command_list[1]),
                                               int(command_list[2]),
                                               int(command_list[3]))
            else:
                logging.info(f"No leg matched that name: {command_list[0]}")
        except:
            logging.warning(f"Error in message: {message}")
        time.sleep(.05)


if __name__ == "__main__":
    main()
