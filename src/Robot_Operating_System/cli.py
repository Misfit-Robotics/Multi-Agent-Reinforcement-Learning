command = ""
while command != "exit":
    command = input("> ").lower()

    if command == "help":
        print("\tmove [x] [y] [z]\t\tMoves the leg to x, y, z.")
