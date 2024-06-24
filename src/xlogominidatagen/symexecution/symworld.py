import copy
from src.xlogomini.components.world.marker import MarkerArray
from src.xlogomini.utils.enums import *
from src.xlogomini.utils.helpers import yx2i
from src.xlogomini.components.world.turtle import Turtle
from src.xlogomini.components.world.tile import Tile
from src.xlogomini.components.world.item import Item
from src.xlogomini.components.world.marker import Line
import numpy as np
import pandas as pd
from src.xlogominidatagen.symexecution.decision_maker import RandomDecisionMaker


class SymWorld(object):
    def __init__(self, rows, cols, turtle, tiles, items, markers, decision_maker):
        self.rows = rows
        self.cols = cols
        self.numAPICalls = 0
        self.crashed_msg = None

        self.init_turtle = copy.deepcopy(turtle)

        # objects in the worlds
        self.turtle = turtle
        self.tiles = tiles
        self.items = items
        self.markers = markers

        # memories
        self.trace = [yx2i(self.init_turtle.y, self.init_turtle.x, self.cols)]  # should be initialized to an empty list
        self.edge_colors = []
        self.pen_color = None
        self.drawn_markers = MarkerArray(rows, cols)

        self.decision_maker = decision_maker

    @classmethod
    def init_from_world(cls, world, decision_maker=None):
        assert 'rows' in world.keys()
        assert 'cols' in world.keys()
        assert 'turtle' in world.keys()
        assert 'tiles' in world.keys()
        assert 'items' in world.keys()
        assert 'lines' in world.keys()

        rows = world['rows']
        cols = world['cols']
        ntiles = rows * cols

        if decision_maker is None:
            decision_maker = RandomDecisionMaker.auto_init()

        # build turtle
        turtle = world['turtle']
        tur_y = turtle['y'] if 'y' in turtle.keys() else decision_maker.pick_int(0, rows)
        tur_x = turtle['x'] if 'x' in turtle.keys() else decision_maker.pick_int(0, cols)
        tur_dir = turtle['dir'] if 'dir' in turtle.keys() else decision_maker.pick_int(0, len(DEG_MAP))
        turtle = Turtle(tur_y, tur_x, tur_dir)

        # build items
        items = np.array([Item() for _ in range(ntiles)]).reshape(rows, cols)
        item_list = world['items']
        for i in range(len(item_list)):
            item = item_list[i]
            items[item['y'], item['x']] = Item(name=item['name'] if 'name' in item.keys() else None,
                                               color=item['color'] if 'color' in item.keys() else None,
                                               count=item['count'] if 'count' in item.keys() else None)

        # build tiles
        tiles = np.array([Tile() for _ in range(ntiles)]).reshape(rows, cols)
        tile_list = world['tiles']
        for i in range(len(tile_list)):
            tile = tile_list[i]
            tiles[tile['y'], tile['x']] = Tile(allowed=tile['allowed'] if 'allowed' in tile.keys() else None,
                                               exist=tile['exist'] if 'exist' in tile.keys() else None,
                                               wall_top=tile['walls']['top'] if ('walls' in tile.keys()) and (
                                                       'top' in tile['walls'].keys()) else None,
                                               wall_left=tile['walls']['left'] if ('walls' in tile.keys()) and (
                                                       'left' in tile['walls'].keys()) else None,
                                               wall_right=tile['walls']['right'] if ('walls' in tile.keys()) and (
                                                       'right' in tile['walls'].keys()) else None,
                                               wall_bottom=tile['walls']['bottom'] if ('walls' in tile.keys()) and (
                                                       'bottom' in tile['walls'].keys()) else None)
        # build markers
        markers = MarkerArray(rows, cols)
        for line_json in world['lines']:
            line = Line.init_from_json(line_json)  # get the lind
            markers.update(line)  # update the markers with the line

        return cls(rows, cols, turtle, tiles, items, markers, decision_maker)

    def fd(self):
        """
        check condition (walls, allowed)
        update location
        collect items
        """
        if self.isCrashed(): return
        dir = DEG_MAP[self.turtle.dir]

        # the tile where our turtle stands
        tile = self.tiles[self.turtle.y, self.turtle.x]
        tile.allowed = True
        tile.exist = True
        if dir == 'NORTH':
            delta_y = -1
            delta_x = 0
            tile.wall_top = False
        elif dir == 'EAST':
            delta_y = 0
            delta_x = 1
            tile.wall_right = False
        elif dir == 'SOUTH':
            delta_y = 1
            delta_x = 0
            tile.wall_bottom = False
        elif dir == 'WEST':
            delta_y = 0
            delta_x = -1
            tile.wall_left = False
        else:
            raise ValueError("dir name not recognized")

        # update turtle's location
        self.turtle.y += delta_y
        self.turtle.x += delta_x

        # add trace
        self.trace.append(yx2i(self.turtle.y, self.turtle.x, self.cols))
        self.edge_colors.append(self.pen_color if self.pen_color is not None else 'black')

        if not self.isCrashed():
            # still within the grid world?
            if not ((self.turtle.y < self.rows) and
                    (self.turtle.y >= 0) and
                    (self.turtle.x < self.cols) and
                    (self.turtle.x >= 0)):
                self.crashed_msg = CRASHED_MSG["OUT_OF_WORLD"]

        if not self.isCrashed():
            # set next tile if not out of grid
            next_tile = self.tiles[self.turtle.y, self.turtle.x]
            next_tile.allowed = True
            next_tile.exist = True
            if dir == 'NORTH':
                next_tile.wall_bottom = False
            elif dir == 'EAST':
                next_tile.wall_left = False
            elif dir == 'SOUTH':
                next_tile.wall_top = False
            elif dir == 'WEST':
                next_tile.wall_right = False
            else:
                raise ValueError(f"{dir} not recognized")

            # add lines to drawn_markers if not crash
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
        dir = DEG_MAP[self.turtle.dir]

        # the tile where our turtle stands
        tile = self.tiles[self.turtle.y, self.turtle.x]
        tile.allowed = True
        tile.exist = True
        if dir == 'SOUTH':
            tile.wall_top = False
            delta_y = -1
            delta_x = 0
        elif dir == 'WEST':
            tile.wall_right = False
            delta_y = 0
            delta_x = 1
        elif dir == 'NORTH':
            tile.wall_bottom = False
            delta_y = 1
            delta_x = 0
        elif dir == 'EAST':
            tile.wall_left = False
            delta_y = 0
            delta_x = -1
        else:
            raise ValueError("dir name not recognized.")

        # update turtle's location
        self.turtle.x += delta_x
        self.turtle.y += delta_y

        # add trace
        self.trace.append(yx2i(self.turtle.y, self.turtle.x, self.cols))
        self.edge_colors.append(self.pen_color if self.pen_color is not None else 'black')

        if not self.isCrashed():
            # still within the grid world?
            if not ((self.turtle.y < self.rows) and
                    (self.turtle.y >= 0) and
                    (self.turtle.x < self.cols) and
                    (self.turtle.x >= 0)):
                self.crashed_msg = CRASHED_MSG["OUT_OF_WORLD"]

        if not self.isCrashed():
            # set next tile if not out of grid
            next_tile = self.tiles[self.turtle.y, self.turtle.x]
            next_tile.allowed = True
            next_tile.exist = True
            if dir == 'NORTH':
                next_tile.wall_top = False
            elif dir == 'EAST':
                next_tile.wall_right = False
            elif dir == 'SOUTH':
                next_tile.wall_bottom = False
            elif dir == 'WEST':
                next_tile.wall_left = False
            else:
                raise ValueError(f"{dir} not recognized")

            # add lines to drawn_markers
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

    def __repr__(self):
        """
        Returns a string version of the world.
        """
        map_rows = 4
        map_cols = 4

        def convert_grid(id, item, tile, has_turtle):
            """
                  0     1      2      3
            0   wall   wall   wall   wall
            1   wall   count  color  wall
            2   wall         turtle  wall
            3   wall   wall   wall   wall
            """
            data = np.empty((map_cols, map_cols), dtype=np.dtype(object))

            data[0, 0] = f"[{id}]"

            if tile.wall_top == True:
                data[0, 1:-1] = '——'
            elif tile.wall_top is None:
                data[0, 1:-1] = '?'

            if tile.wall_left == True:
                data[1:-1, 0] = '|'
            elif tile.wall_left is None:
                data[1:-1, 0] = '?'

            if tile.wall_right == True:
                data[1:-1, -1] = '|'
            elif tile.wall_right is None:
                data[1:-1, -1] = '?'

            if tile.wall_bottom == True:
                data[-1, 1:-1] = '——'
            elif tile.wall_bottom is None:
                data[-1, 1:-1] = '?'

            if tile.allowed == True or tile.allowed is None:
                if item is not None:
                    data[1, 1] = str(item.count) if item.count is not None else '?'
                    data[1, 2] = item.color if item.color is not None else '?'
                    if item.name is not None:
                        data[2, 1] = ITEM_UNICODE[item.name] if item.name in ITEM_UNICODE.keys() else item.name
                    else:
                        data[2, 1] = '?'
            elif tile.allowed == False:
                data[1, 1] = data[1, 2] = data[2, 1] = data[2, 2] = ITEM_UNICODE['forbid']
            else:
                raise ValueError(f"tile.allowed {tile.allowed} not recognized")

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
                if self.turtle is not None:
                    has_turtle = True if x == self.turtle.x and y == self.turtle.y else False
                else:
                    has_turtle = False
                world_str.append(convert_grid(yx2i(y, x, self.cols),
                                              self.items[y, x],
                                              self.tiles[y, x],
                                              has_turtle))

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

        # insert sep rows
        world_map = world_map.T
        for i in range(self.rows + 1):
            world_map.insert(map_cols * i + i, 'sep', '.', allow_duplicates=True)

        return world_map.T.to_string(header=False, index=False)

    def __eq__(self, other):
        if isinstance(other, SymWorld):
            return self.__repr__() == other.__repr__()
        else:
            return False

    def __hash__(self):
        return hash(self.__repr__())
