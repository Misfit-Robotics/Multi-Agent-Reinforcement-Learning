import yaml

coax_angle = 0
femur_angle = 0
tibia_angle = 0
femur_length = 4.0 #length in inches
tibia_length = 4.5
coax_length = 2.5


class Limb:

    def __init__(self, config_file, limb_name):

        with open(config_file) as f:
            config = yaml.safe_load(f)

        print(f"Initializing {limb_name} on {config["robot"]["name"]}")
        self.coax = config[limb_name]["coax_loc"]       #array location of the coax servo
        self.femur = config[limb_name]["femur_loc"]      #array location of the femur servo
        self.tibia = config[limb_name]["tibia_loc"]      #array location of the femur servo# self.tibia = tibia  #array location of the tibia servo

        self.x_min = config[limb_name]["min_x"]
        self.x_max = config[limb_name]["max_x"]
        self.y_min = config[limb_name]["min_y"]
        self.y_max = config[limb_name]["max_y"]
        self.z_min = config[limb_name]["min_z"]
        self.z_min = config[limb_name]["max_z"]

        if config["robot"]["connected"]:
            from adafruit_servokit import ServoKit
            import board
            import busio
            i2c = busio.I2C(board.SCL, board.SDA)
            kit = ServoKit(channels=16, i2c=i2c) # Initialize the ServoKit with 16 channels (for the PCA9685)
            self.controller_kit.servo[self.hip].set_pulse_width_range(100, 2250)
            self.controller_kit.servo[self.femur].set_pulse_width_range(100, 2250)
            self.controller_kit.servo[self.tibia].set_pulse_width_range(500, 2500)

#
#         self.inverse = inverse
#
#         self.TIBIA_OFFSET = -15
#         self.FEMUR_OFFSET = -45
#
#         self.HSA_current = 0
#         self.HSA_target = 0
#         self.FSA_current = 0
#         self.FSA_target = 0
#         self.TSA_current = 0
#         self.TSA_target = 0
#
#     def reposition_leg(self, x, y, z):
#
#         if x < self.x_min or x > self.x_max:
#             print("Out of Bounds")
#             return
#         if y < self.y_min or y > self.y_max:
#             print("Out of Bounds")
#             return
#         if z < self.z_min or z > self.z_max:
#             print("Out of Bounds")
#             return
#         if z == 0:
#                         z = 0.0001
#         if x == 0:
#                         x = 0.0001
#         if y == 0:
#                         y = 0.0001
#
#         H = math.sqrt(math.pow(x, 2) + math.pow(y,2))
#         self.HSA_target = math.degrees(math.atan(x/y))
#         print(f"HSA Degrees: {self.HSA_target}")
#         if self.inverse:
#                 self.HSA_target = 180 - self.HSA_target
#         if self.HSA_target < 0:
#                 self.HSA_target = 90 + self.HSA_target
#         kit.servo[self.hip].angle = self.HSA_target * 2
#
#
#         L = math.sqrt(math.pow(H, 2) + math.pow(z,2))
#         TSA = math.acos((math.pow(TL, 2) + math.pow(FL, 2) - math.pow(L, 2)) / (2 * TL * FL))
#         self.TSA_target = math.degrees(TSA) + self.TIBIA_OFFSET
#         if self.TSA_target < 15:
#                 self.TSA_target = 15
#                 print("Tibia Unable to Reach")
#         if self.TSA_target > 180:
#                 self.TSA_target = 180
#                 print("Tibia Unable to Reach")
#         print(f"TSA Degrees: {self.TSA_target}")
#         kit.servo[self.tibia].angle = self.TSA_target
#
#         vb = math.acos((math.pow(L, 2) + math.pow(FL, 2) - math.pow(TL, 2))/(2 * L * FL))
#         va = math.atan((H-HL)/z)
#         FSA = vb+va
#         self.FSA_target = math.degrees(FSA)
#         print(f"FSA Degrees: {self.FSA_target}")
#         self.FSA_target = self.FSA_target + self.FEMUR_OFFSET
#         kit.servo[self.femur].angle = 2 * (90 - self.FSA_target)
#
# leg_rr = Leg(0, 1, 2, False, 0, 6, -6, 0, 0, 6)
# leg_fr = Leg(4, 5, 6, False, 0, 6, 0, 6, 0, 6)
# leg_fl = Leg(8, 9, 10, False, -6, 0, 0, 6, 0, 6)
# leg_rl = Leg(12, 13, 14, False, -6, 0, -6, 0, 0, 6)
#
# #Laydown
# leg_fr.reposition_leg(3, 3, 5)
# leg_fl.reposition_leg(-3, 3, 5)
# leg_rl.reposition_leg(-3, -3, 5)
# leg_rr.reposition_leg(3, -3, 5)
# time.sleep(2)