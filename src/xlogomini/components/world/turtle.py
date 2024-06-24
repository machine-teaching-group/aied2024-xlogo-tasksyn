class Turtle(object):
    def __init__(self, y, x, dir):
        """
        :param y:
            - y axis
        :param x:
            - x axis
        :param dir:
            - direction of the turtle, `dir` ∈ {0, 1, 2, 3}
        """
        self.y = y
        self.x = x
        self.dir = dir

        assert (dir is None) or (dir >= 0)

    def to_dict(self):
        return {
            "y"        : self.y,
            "x"        : self.x,
            "direction": self.dir
        }
