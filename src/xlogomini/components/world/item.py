from src.xlogomini.utils.enums import ITEM_COLOR, ITEM_NAME, ITEM_COUNT


class Item(object):
    def __init__(self, name=None, color=None, count=None):
        """
        :param name:
            - `name` should be in {"strawberry", "lemon", "triangle", "rectangle", "cross", "circle"}

        :param count:
            - `count` should be in {1, 2, 3, 4}
            - maximum allowed `count` = 4

        :param color:
            - `color` should be in {None, "red", "blue", "green", "pink", "purple", "orange", "yellow", "black"}
            - `color` = None for name ∈ {"strawberry", "lemon"},

        :param type:
            - `type` should be in {"fruit", "element", "char"}
            - `type` = "element" for name ∈ {"triangle", "rectangle", "cross", "circle"}
        """

        self.name = name
        self.color = color
        self.count = count

        assert name in ITEM_NAME or name is None
        assert color in ITEM_COLOR or color is None
        assert count in ITEM_COUNT or count is None

    def __str__(self):
        return f"{self.count} {self.color} {self.name}"
