from z3 import EnumSort

Block, (fd, bk, lt, rt, repeat, setpc, noblock, allblocks) = EnumSort("Block", (
    "fd", "bk", "lt", "rt", "repeat", "setpc", "noblock", "allblocks"))
PColor, (white, black, green, yellow, blue, red) = EnumSort("PColor", (
    "white", "black", "green", "yellow", "blue", "red"))


class BaseBlockSMT():
    def __init__(self, js, id):
        """
        `js`: json of the code
        `id`: a unique identifier for the position of code block.
        """
        self.js = js
        self.id = id

        self.vars = {}

    def properties(self):
        pass
