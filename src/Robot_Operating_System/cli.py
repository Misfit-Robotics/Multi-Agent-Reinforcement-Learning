import argparse

from mypy.dmypy.client import subparsers


def greet(args):
    print(f"Hello, {args.name}")


def add_numbers(args):
    print(args.a + args.b)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_hello = subparsers.add_parser("hello")
    p_hello.add_argument("name")
    p_hello.set_defaults(func=greet)

    p_add = subparsers.add_parser("add")
    p_add.add_argument("a", type=int)
    p_add.add_argument("b", type=int)
    p_add.set_defaults(func=add_numbers)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
