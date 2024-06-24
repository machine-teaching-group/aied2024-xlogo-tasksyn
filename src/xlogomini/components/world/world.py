import numpy as np
import pandas as pd
from src.xlogomini.utils.helpers import yx2i
from src.xlogomini.utils.enums import *
from src.xlogomini.components.world.turtle import Turtle
from src.xlogomini.components.world.item import Item
from src.xlogomini.components.world.tile import Tile
from src.xlogomini.components.world.marker import MarkerArray, Line


class World(object):
    def __init__(self, rows, cols, turtle_json, tiles_json, items_json, lines_json):
        self.rows = rows
        self.cols = cols
        self.numAPICalls = 0
        self.crashed_msg = None

        # objects in the worlds
        self.turtle = Turtle(turtle_json["y"], turtle_json["x"], turtle_json["direction"])
        self.tiles = np.empty((rows, cols), dtype=object)
        self.items = np.empty((rows, cols), dtype=object)  # array filled with Nones
        self.markers = MarkerArray(rows, cols)

        # memories
        self.trace = [yx2i(self.turtle.y, self.turtle.x, self.cols)]  # include the initial pos
        self.pen_color = None
        self.drawn_markers = MarkerArray(rows, cols)

        # conceptual stats of the world
        # stats of items
        self.itemtypes_used = set()
        self.colors_used = set()
        self.shapes_used = set()
        self.pen_colors_used = set()

        self.n_items = 0
        self.use_count = False

        # stats of tiles
        self.n_walls = 0
        self.n_forbidden_areas = 0
        self.non_existent_tiles = 0

        # stats of markers
        self.markers_used = False

        self._build_tiles(tiles_json)
        self._build_items(items_json)
        self._build_markers(lines_json)

    @classmethod
    def init_from_json(cls, js):
        rows = max([tile['y'] for tile in js['tiles']]) + 1
        cols = max([tile['x'] for tile in js['tiles']]) + 1
        turtle_json = js['turtle']
        item_list = js['items']
        tile_list = js['tiles']
        line_list = js['lines']
        return cls(rows, cols, turtle_json, tile_list, item_list, line_list)

    def _build_tiles(self, tiles_json):
        # build tiles
        for tile in tiles_json:
            top = tile['walls']['top'] if 'top' in tile["walls"].keys() else False
            left = tile['walls']['left'] if 'left' in tile["walls"].keys() else False
            right = tile['walls']['right'] if 'right' in tile["walls"].keys() else False
            bottom = tile['walls']['bottom'] if 'bottom' in tile["walls"].keys() else False
            self.tiles[tile["y"], tile["x"]] = Tile(allowed=tile["allowed"],
                                                    exist=tile["exist"] if "exist" in tile.keys() else True,
                                                    wall_top=top,
                                                    wall_left=left,
                                                    wall_right=right,
                                                    wall_bottom=bottom)
            # count of walls
            self.n_walls += sum([top, left, right, bottom])

            if not tile['allowed']:
                self.n_forbidden_areas += 1

        # indentify the non-existing tiles
        for r in range(self.rows):
            for c in range(self.cols):
                if self.tiles[r, c] is None:
                    self.non_existent_tiles += 1
                    self.tiles[r, c] = Tile(allowed=False,
                                            exist=False,
                                            wall_top=None,
                                            wall_left=None,
                                            wall_right=None,
                                            wall_bottom=None)

    def _build_items(self, items_json):
        # build items
        for item in items_json:
            self.items[item["y"], item["x"]] = Item(name=item["name"],
                                                    color=item["color"],
                                                    count=item["count"])
            # exists an item with count > 1
            if item['count'] > 1:
                self.use_count = True

            if item['name'] in ITEM_FRUIT:
                self.itemtypes_used.add('fruit')
            elif item['name'] in ITEM_CHAR:
                self.itemtypes_used.add('char')
            elif item['name'] in ITEM_SHAPE:
                self.itemtypes_used.add('shape')
                self.colors_used.add(item['color'])
                self.shapes_used.add(item['name'])
            else:
                raise ValueError(f"{item['name']} not recognized")

            self.n_items += 1

    def _build_markers(self, lines_json):
        for line_json in lines_json:
            line = Line.init_from_json(line_json)  # build line
            self.markers_used = True
            self.markers.update(line)
            if line.color is not None:
                self.pen_colors_used.add(line.color)

    def fd(self):
        """
        check condition (walls, allowed)
        update location
        collect items
        """
        if self.isCrashed(): return
        tile = self.tiles[self.turtle.y, self.turtle.x]

        dir = DEG_MAP[self.turtle.dir]
        if dir == 'NORTH':
            if tile.wall_top:
                # add position to the crash message
                self.crashed_msg = {"crash_type": CRASHED_MSG["WALL"], "pos": (self.turtle.x, self.turtle.y)}
            delta_y = -1
            delta_x = 0
        elif dir == 'EAST':
            if tile.wall_right:
                self.crashed_msg = {"crash_type": CRASHED_MSG["WALL"], "pos": (self.turtle.x, self.turtle.y)}
            delta_y = 0
            delta_x = 1
        elif dir == 'SOUTH':
            if tile.wall_bottom:
                self.crashed_msg = {"crash_type": CRASHED_MSG["WALL"], "pos": (self.turtle.x, self.turtle.y)}
            delta_y = 1
            delta_x = 0
        elif dir == 'WEST':
            if tile.wall_left:
                self.crashed_msg = {"crash_type": CRASHED_MSG["WALL"], "pos": (self.turtle.x, self.turtle.y)}
            delta_y = 0
            delta_x = -1
        else:
            raise ValueError("dir name not recognized.")

        # update turtle's location
        self.turtle.y += delta_y
        self.turtle.x += delta_x

        # add trace
        self.trace.append(yx2i(self.turtle.y, self.turtle.x, self.cols))

        if not self.isCrashed():
            # still within the grid world?
            if not ((self.turtle.y < self.rows) and
                    (self.turtle.y >= 0) and
                    (self.turtle.x < self.cols) and
                    (self.turtle.x >= 0)):
                self.crashed_msg = {"crash_type": CRASHED_MSG["OUT_OF_WORLD"], "pos": (self.turtle.x, self.turtle.y)}

        if not self.isCrashed():
            # check forbidden area
            if not self.tiles[self.turtle.y, self.turtle.x].allowed:
                self.crashed_msg = {"crash_type": CRASHED_MSG["FORBIDDEN_AREA"], "pos": (self.turtle.x, self.turtle.y)}

        if not self.isCrashed():
            # check grid existence
            if not self.tiles[self.turtle.y, self.turtle.x].exist:
                self.crashed_msg = {"crash_type": CRASHED_MSG["GRID_NOT_EXIST"], "pos": (self.turtle.x, self.turtle.y)}

        if not self.isCrashed():
            # Object collected, set None
            self.items[self.turtle.y, self.turtle.x] = None

            # add lines
            drawn_line = Line(x1=self.turtle.x - delta_x,
                              y1=self.turtle.y - delta_y,
                              x2=self.turtle.x,
                              y2=self.turtle.y,
                              color=self.pen_color if self.pen_color is not None else 'black')
            self.drawn_markers.update(drawn_line)

        self.noteApiCall()

    def bk(self):
        """
        check condition (walls, allowed)
        update location
        collect items
        """
        if self.isCrashed(): return
        tile = self.tiles[self.turtle.y, self.turtle.x]

        dir = DEG_MAP[self.turtle.dir]
        if dir == 'SOUTH':
            if tile.wall_top:
                self.crashed_msg = {"crash_type": CRASHED_MSG["WALL"], "pos": (self.turtle.x, self.turtle.y)}
            delta_y = -1
            delta_x = 0
        elif dir == 'WEST':
            if tile.wall_right:
                self.crashed_msg = {"crash_type": CRASHED_MSG["WALL"], "pos": (self.turtle.x, self.turtle.y)}
            delta_y = 0
            delta_x = 1
        elif dir == 'NORTH':
            if tile.wall_bottom:
                self.crashed_msg = {"crash_type": CRASHED_MSG["WALL"], "pos": (self.turtle.x, self.turtle.y)}
            delta_y = 1
            delta_x = 0
        elif dir == 'EAST':
            if tile.wall_left:
                self.crashed_msg = {"crash_type": CRASHED_MSG["WALL"], "pos": (self.turtle.x, self.turtle.y)}
            delta_y = 0
            delta_x = -1
        else:
            raise ValueError("dir name not recognized.")

        # update turtle's location
        self.turtle.x += delta_x
        self.turtle.y += delta_y

        # add trace
        self.trace.append(yx2i(self.turtle.y, self.turtle.x, self.cols))

        if not self.isCrashed():
            # still within the grid world?
            if not ((self.turtle.y < self.rows) and
                    (self.turtle.y >= 0) and
                    (self.turtle.x < self.cols) and
                    (self.turtle.x >= 0)):
                self.crashed_msg = {"crash_type": CRASHED_MSG["OUT_OF_WORLD"], "pos": (self.turtle.x, self.turtle.y)}

        if not self.isCrashed():
            # check forbidden area
            if not self.tiles[self.turtle.y, self.turtle.x].allowed:
                self.crashed_msg = {"crash_type": CRASHED_MSG["FORBIDDEN_AREA"], "pos": (self.turtle.x, self.turtle.y)}

        if not self.isCrashed():
            # check grid existence
            if not self.tiles[self.turtle.y, self.turtle.x].exist:
                self.crashed_msg = {"crash_type": CRASHED_MSG["GRID_NOT_EXIST"], "pos": (self.turtle.x, self.turtle.y)}

        if not self.isCrashed():
            # Object collected, set None
            self.items[self.turtle.y, self.turtle.x] = None

            # add drawn_marker
            drawn_line = Line(x1=self.turtle.x - delta_x,
                              y1=self.turtle.y - delta_y,
                              x2=self.turtle.x,
                              y2=self.turtle.y,
                              color=self.pen_color if self.pen_color is not None else 'black')
            self.drawn_markers.update(drawn_line)

        self.noteApiCall()

    def lt(self):
        if self.isCrashed(): return
        self.turtle.dir = (self.turtle.dir - 1) % 4
        self.noteApiCall()

    def rt(self):
        if self.isCrashed(): return
        self.turtle.dir = (self.turtle.dir + 1) % 4
        self.noteApiCall()

    def setpc(self, color):
        self.pen_color = color
        self.noteApiCall()

    def isCrashed(self):
        return self.crashed_msg is not None

    # Function: note api call
    # ------------------
    # To catch infinite loops, we limit the number of API calls.
    # If the num api calls exceeds a max, the program is crashed.
    def noteApiCall(self):
        self.numAPICalls += 1
        if self.numAPICalls > MAX_API_CALLS:
            self.crashed_msg = "EXCEED_MAX_CALLS"

    def toPytorchTensor(self, padding):
        import torch
        tensor = torch.FloatTensor(65, padding, padding).zero_()
        colors = ["red", "green", "blue", "yellow", "black", "orange", "purple", "pink", "white"]
        for r in range(self.rows):
            for c in range(self.cols):
                if self.turtle.y == r and self.turtle.x == c:
                    # turtle: dim=4 (0-3)
                    turtle_feats = [1 if self.turtle.dir == 0 else 0,
                                    1 if self.turtle.dir == 90 else 0,
                                    1 if self.turtle.dir == 180 else 0,
                                    1 if self.turtle.dir == 270 else 0]
                else:
                    turtle_feats = [0, 0, 0, 0]
                # tile: dim=6, (4-9)
                if self.tiles[r, c].exist:
                    tile_feats = [
                        int(self.tiles[r, c].wall_top) if self.tiles[r, c] is not None else 0,
                        int(self.tiles[r, c].wall_right) if self.tiles[r, c] is not None else 0,
                        int(self.tiles[r, c].wall_bottom) if self.tiles[r, c] is not None else 0,
                        int(self.tiles[r, c].wall_left) if self.tiles[r, c] is not None else 0,
                        int(self.tiles[r, c].allowed) if self.tiles[r, c] is not None else 0,
                        int(self.tiles[r, c].exist) if self.tiles[r, c] is not None else 0
                    ]
                else:
                    tile_feats = [0, 0, 0, 0, 0, 0]

                if self.items[r, c] is not None:
                    # item name: dim=6, (10-15)
                    item_name_feats = [
                        int(self.items[r, c].name == 'strawberry'),
                        int(self.items[r, c].name == 'lemon'),
                        int(self.items[r, c].name == 'circle'),
                        int(self.items[r, c].name == 'rectangle'),
                        int(self.items[r, c].name == 'triangle'),
                        int(self.items[r, c].name == 'cross'),
                    ]
                    # item color: dim=9, (16-24)
                    item_color_feats = [int(self.items[r, c].color == color) for color in colors]
                    # item count: dim=4, (25-28)
                    item_count_feats = [
                        int(self.items[r, c].count) == 1,
                        int(self.items[r, c].count) == 2,
                        int(self.items[r, c].count) == 3,
                        int(self.items[r, c].count) == 4
                    ]
                else:
                    item_name_feats = [0] * 6
                    item_color_feats = [0] * len(colors)
                    item_count_feats = [0] * 4

                if self.markers[r, c] is not None:
                    # marker: dim=4, (28-31)
                    # marker_feats = [
                    #     1 if self.markers[r, c].top else 0,
                    #     1 if self.markers[r, c].right else 0,
                    #     1 if self.markers[r, c].bottom else 0,
                    #     1 if self.markers[r, c].left else 0,
                    # ]
                    # marker color: dim=36, (32-67)
                    marker_feats = []
                    for i, color in enumerate(colors):
                        marker_feats.extend([
                            1 if self.markers[r, c].top_color == color else 0,
                            1 if self.markers[r, c].right_color == color else 0,
                            1 if self.markers[r, c].bottom_color == color else 0,
                            1 if self.markers[r, c].left_color == color else 0
                        ])
                else:
                    # marker_feats = [0] * 4
                    marker_feats = [0] * 4 * len(colors)

                tensor[:, r, c] = torch.from_numpy(np.concatenate([
                    turtle_feats,
                    tile_feats,
                    item_name_feats,
                    item_color_feats,
                    item_count_feats,
                    marker_feats
                ]))
        return tensor

    def getWorldStats(self):
        import torch
        color_list = ["red", "green", "blue", "yellow", "black", "orange", "purple", "pink", "white"]
        world_stats = {
            # colors
            "red"          : 0,
            "green"        : 0,
            "blue"         : 0,
            "yellow"       : 0,
            "black"        : 0,
            "orange"       : 0,
            "purple"       : 0,
            "pink"         : 0,
            "white"        : 0,
            # fruits
            "1strawberry"  : 0,
            "2strawberry"  : 0,
            "3strawberry"  : 0,
            "4strawberry"  : 0,
            "lemon"        : 0,
            # shapes
            "circle"       : 0,
            "rectangle"    : 0,
            "triangle"     : 0,
            "cross"        : 0,
            # walls
            "walls"        : 0,
            "forbidden"    : 0,
            # marker
            "markers"      : 0,
            # marker color
            "marker_red"   : 0,
            "marker_green" : 0,
            "marker_blue"  : 0,
            "marker_yellow": 0,
            "marker_black" : 0,
            "marker_orange": 0,
            "marker_purple": 0,
            "marker_pink"  : 0,
            "marker_white" : 0,
        }

        for r in range(self.rows):
            for c in range(self.cols):
                # items
                if self.items[r, c] is not None:
                    # item name
                    if self.items[r, c].name == 'strawberry':
                        world_stats[f"{self.items[r, c].count}{self.items[r, c].name}"] += 1
                    else:
                        world_stats[f"{self.items[r, c].name}"] += 1

                    # item color
                    for color in color_list:
                        world_stats[f'{color}'] += int(self.items[r, c].color == color)

                # tiles
                if self.tiles[r, c].exist:
                    world_stats['walls'] += (int(self.tiles[r, c].wall_top)
                                             + int(self.tiles[r, c].wall_left)
                                             + int(self.tiles[r, c].wall_right)
                                             + int(self.tiles[r, c].wall_bottom))
                    world_stats['forbidden'] += int(not self.tiles[r, c].allowed)

                # markers
                if self.markers[r, c] is not None:
                    if self.markers[r, c].top is not None:
                        world_stats['markers'] += int(self.markers[r, c].top)
                    if self.markers[r, c].left is not None:
                        world_stats['markers'] += int(self.markers[r, c].left)
                    if self.markers[r, c].right is not None:
                        world_stats['markers'] += int(self.markers[r, c].right)
                    if self.markers[r, c].bottom is not None:
                        world_stats['markers'] += int(self.markers[r, c].bottom)

                    for color in color_list:
                        world_stats[f'marker_{color}'] += (int(self.markers[r, c].top_color == color)
                                                           + int(self.markers[r, c].left_color == color)
                                                           + int(self.markers[r, c].right_color == color)
                                                           + int(self.markers[r, c].bottom_color == color))

        n_shapes = sum([1 if world_stats[shape] > 0 else 0
                        for shape in ['circle', 'rectangle', 'triangle', 'cross']])
        n_colors = sum([1 if world_stats[color] > 0 else 0
                        for color in color_list])
        n_fruits = sum([1 if world_stats[fruit] > 0 else 0
                        for fruit in ['1strawberry', 'lemon']])
        use_counting = int(any([world_stats['2strawberry'],
                                world_stats['3strawberry'],
                                world_stats['4strawberry']]))
        # use_markers = 1 if world_stats['markers'] > 0 else 0
        n_marker_colors = sum([1 if world_stats[f'marker_{color}'] > 0 else 0
                               for color in color_list])
        n_walls = world_stats['walls']
        n_forb = world_stats['forbidden'] / (self.rows * self.cols)  # normalized by max forbidden areas

        # normalization
        n_shapes = n_shapes / 4
        n_colors = n_colors / len(color_list)
        n_fruits = n_fruits / 2
        n_marker_colors = n_marker_colors / len(color_list)
        n_walls = n_walls / (self.rows * self.cols * 4)
        n_forb = n_forb / (self.rows * self.cols)

        return torch.tensor([n_shapes, n_colors, n_fruits, use_counting, n_marker_colors, n_walls, n_forb])

    def __repr__(self):
        """
        Returns a string version of the world.
        """
        map_rows = 4
        map_cols = 4

        def convert_grid(id, item, tile, has_turtle):
            """
            Each grid is represented by a 4x4 array.
            The meaning for each cell in the array is defined as:
                  0     1      2      3
            0   [id]   top   top
            1   left   count  color   right
            2   left   name   turtle  right
            3          bottom bottom
            """
            data = np.empty((map_cols, map_cols), dtype=np.dtype(object))

            data[0, 0] = f"[{id}]"

            if not tile.exist:
                data[:, :] = '.'
                return data

            if tile.wall_top:
                data[0, 1:-1] = '——'
            if tile.wall_left:
                data[1:-1, 0] = '|'
            if tile.wall_right:
                data[1:-1, -1] = '|'
            if tile.wall_bottom:
                data[-1, 1:-1] = '——'

            if tile.allowed:
                if item is not None:
                    data[1, 1] = str(item.count)
                    data[1, 2] = item.color
                    data[2, 1] = ITEM_UNICODE[item.name] if item.name in ITEM_UNICODE.keys() else item.name
            else:
                data[1, 1] = data[1, 2] = data[2, 1] = data[2, 2] = ITEM_UNICODE['forbid']

            if has_turtle:
                if DEG_MAP[self.turtle.dir] == 'NORTH':
                    data[2, 2] = ITEM_UNICODE['north']
                elif DEG_MAP[self.turtle.dir] == 'EAST':
                    data[2, 2] = ITEM_UNICODE['east']
                elif DEG_MAP[self.turtle.dir] == 'SOUTH':
                    data[2, 2] = ITEM_UNICODE['south']
                elif DEG_MAP[self.turtle.dir] == 'WEST':
                    data[2, 2] = ITEM_UNICODE['west']
                else:
                    raise ValueError(f"{self.turtle.dir} not recognized")

            return data

        world_str = []
        for y in range(self.rows):
            for x in range(self.cols):
                has_turtle = True if x == self.turtle.x and y == self.turtle.y else False
                world_str.append(convert_grid(yx2i(y, x, self.cols), self.items[y, x], self.tiles[y, x], has_turtle))

        world_map = np.empty((self.rows * map_rows, self.cols * map_cols), dtype=object)
        for i in range(len(world_str)):
            for y in range(world_str[i].shape[0]):
                for x in range(world_str[i].shape[1]):
                    y_ = (i // self.cols) * map_rows + y
                    x_ = (i % self.cols) * map_cols + x
                    world_map[y_, x_] = world_str[i][y, x]
                    if world_map[y_, x_] is None:
                        world_map[y_, x_] = ''

        world_map = pd.DataFrame(world_map)

        # insert sep cols
        for i in range(self.cols + 1):
            world_map.insert(map_cols * i + i, 'sep', '.', allow_duplicates=True)
        world_map = world_map.T
        # insert sep rows
        for i in range(self.rows + 1):
            world_map.insert(map_cols * i + i, 'sep', '.', allow_duplicates=True)

        return world_map.T.to_string(header=False, index=False)

    def __eq__(self, other):
        if isinstance(other, World):
            return self.__repr__() == other.__repr__()
        else:
            return False

    def __hash__(self):
        return hash(self.__repr__())