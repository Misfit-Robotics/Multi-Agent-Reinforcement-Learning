import argparse
from pathlib import Path
from limb_controller import Limb

ROOT = Path(__file__).resolve().parents[2]


def config_limbs(args):
    front_left_leg = Limb(ROOT / "config.yml", "FL_Leg")


def main():
    parser = argparse.ArgumentParser()
    subparsers_temp = parser.add_subparsers(dest="command", required=True)

    p_add = subparsers_temp.add_parser("load_config_to_limbs")
    p_add.set_defaults(func=config_limbs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
