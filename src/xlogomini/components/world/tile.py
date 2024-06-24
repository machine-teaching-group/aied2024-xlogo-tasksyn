class Tile(object):
    def __init__(self,
                 allowed=None,
                 exist=None,
                 wall_top=None,
                 wall_left=None,
                 wall_bottom=None,
                 wall_right=None):
        self.allowed = allowed
        self.exist = exist

        # walls
        self.wall_top = wall_top
        self.wall_left = wall_left
        self.wall_bottom = wall_bottom
        self.wall_right = wall_right
