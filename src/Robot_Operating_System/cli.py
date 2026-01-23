import argparse
import socket
import subprocess
import sys
import os
import logging
import time

# Networking
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
IP = "127.0.0.1"
PORT = 5005

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s    %(levelname)s    %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


limb_process = None

# ────────────────────────────────────────────────────────────────────────────────
# Start Controller
# ────────────────────────────────────────────────────────────────────────────────


def start_controller(args):
    global limb_process

    if limb_process is not None:
        logging.info("Limb controller already running.")
        return

    limb_process = subprocess.Popen(
        [sys.executable, "-m", "limb_controller"], text=True
    )

    logging.info(f"Limb controller has started. Process ID {limb_process.pid}")


# ────────────────────────────────────────────────────────────────────────────────
# Stop Controller
# ────────────────────────────────────────────────────────────────────────────────
def stop_controller(args):
    message = "shutdown".encode("utf-8")
    sock.sendto(message, (IP, PORT))
    logging.info("Shutting down limb controller.")


# ────────────────────────────────────────────────────────────────────────────────
# Move Limb
# ────────────────────────────────────────────────────────────────────────────────
def move_limb(args):
    message = f"move_limb,{args.limb},{args.x},{args.y},{args.z}".encode("utf-8")
    sock.sendto(message, (IP, PORT))
    logging.info(f"Sent move command to {args.limb} → ({args.x}, {args.y}, {args.z})")


# ────────────────────────────────────────────────────────────────────────────────
# Move Limb
# ────────────────────────────────────────────────────────────────────────────────
def move_joint(args):
    message = f"move_joint,{args.leg},{args.joint},{args.angle}".encode("utf-8")
    sock.sendto(message, (IP, PORT))
    print(f"Sent move_joint command → {args.joint} to angle {args.angle}")


# ────────────────────────────────────────────────────────────────────────────────
# Standup Robot
# ────────────────────────────────────────────────────────────────────────────────
def stand(args):
    message = f"move_limb,FL_Leg,-3,3,-3".encode("utf-8")
    sock.sendto(message, (IP, PORT))
    message = f"move_limb,FR_Leg,3,3,-3".encode("utf-8")
    sock.sendto(message, (IP, PORT))
    message = f"move_limb,BL_Leg,-3,-3,-3".encode("utf-8")
    sock.sendto(message, (IP, PORT))
    message = f"move_limb,BR_Leg,3,-3,-3".encode("utf-8")
    sock.sendto(message, (IP, PORT))
    print("Sent stand command → primitive: stand")


# ────────────────────────────────────────────────────────────────────────────────
# Show Logs (full history + follow)
# ────────────────────────────────────────────────────────────────────────────────
def show_logs(args):

    if not os.path.exists("limb_controller.log"):
        logging.info("No log file found.")
        return

    print("Showing all logs. Press Ctrl+C to stop.\n")

    try:
        with open("limb_controller.log", "r") as f:
            # 1. Print the entire file from the beginning
            for line in f:
                print(line, end="")

            # 2. Now follow new lines as they appear
            while True:
                line = f.readline()
                if line:
                    print(line, end="")
                else:
                    time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopped log streaming.")


# ────────────────────────────────────────────────────────────────────────────────
# Main CLI
# ────────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Robot Limb Controller CLI",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_start = subparsers.add_parser(
        "start_controller",
        help="Start the limb controller process",
        description="""
        Start the limb controller background process.
        This launches the limb controller as a separate Python subprocess.
        The controller will begin listening for UDP commands on 127.0.0.1:5005.
        Logs are written to limb_controller.log.
        """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_start.set_defaults(func=start_controller)

    p_stop = subparsers.add_parser(
        "stop_controller",
        help="Stop the limb controller",
        description="""
        Stop the limb controller process.
        This sends a 'shutdown' UDP message to the controller.
        """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_stop.set_defaults(func=stop_controller)

    p_logs = subparsers.add_parser(
        "controller_logs",
        help="Show controller logs",
        description="""
        Display the limb controller log output.
        This prints the entire log file from the beginning, then continues
        streaming new log entries in real time.
        Press Ctrl+C to exit.
        """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_logs.set_defaults(func=show_logs)

    p_move = subparsers.add_parser(
        "move_limb",
        help="Move a specific limb",
        description="""
        Move a limb to a target coordinate.

        Arguments:
        limb   The limb name (e.g., front_left, front_right)
        x      X coordinate (integer)
        y      Y coordinate (integer)
        z      Z coordinate (integer)

        Example: python robot.py move front_left 10 20 30
        """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_move.add_argument("limb", help="Name of the limb to move")
    p_move.add_argument("x", type=int, help="X coordinate")
    p_move.add_argument("y", type=int, help="Y coordinate")
    p_move.add_argument("z", type=int, help="Z coordinate")
    p_move.set_defaults(func=move_limb)

    p_joint = subparsers.add_parser(
        "move_joint",
        help="Move a specific joint on a specific leg",
        description="""
        Move a joint on a given leg to a target angle.

        Arguments:
          leg     The leg name (e.g., front_left, front_right)
          joint   The joint name (e.g., coax, tibia, femur)
          angle   Target angle in degrees (integer)
    
        Example:
          python robot.py move_joint front_left coax 45
        """,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    p_joint.add_argument("leg", help="Name of the leg (e.g., front_left)")
    p_joint.add_argument("joint", help="Name of the joint (e.g., hip, knee)")
    p_joint.add_argument("angle", type=int, help="Target angle in degrees")
    p_joint.set_defaults(func=move_joint)

    p_stand = subparsers.add_parser(
        "stand",
        help="Command the robot to enter a stable standing pose",
        description="""
    Command the robot to stand.

    This triggers a high-level motion primitive inside the limb controller.
    The controller is responsible for coordinating all legs and joints into
    a stable, neutral standing posture.

    Example:
      python cli.py stand
    """,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    p_stand.set_defaults(func=stand)

    # ───────────────────────────────────────────────────────────────
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
