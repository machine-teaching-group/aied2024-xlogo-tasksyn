from z3 import Implies, And, Or, Not, simplify, If, Sum, AtMost, AtLeast
from src.xlogomini.utils.enums import *
from src.xlogomini.smt.z3_constraints.reachability import properties_for_reachability
from src.xlogomini.utils.helpers import yx2i, get_neighboring_ids
from src.xlogomini.smt.world.item_smt import ItemSMT
from src.xlogomini.smt.world.tile_smt import TileSMT
from src.xlogomini.smt.world.marker_smt import MarkerSMT
from src.xlogomini.smt.world.turtle_smt import TurtleSMT
from src.xlogomini.utils.formulas import exactly_one
import math


class WorldSMT():
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.ntiles = self.rows * self.cols

        self.turtle_smt = TurtleSMT(self.rows, self.cols)
        self.item_smt = ItemSMT(self.rows, self.cols)
        self.tile_smt = TileSMT(self.rows, self.cols)
        self.marker_smt = MarkerSMT(self.rows, self.cols)

        self.vars = self._build_vars()

    def _build_vars(self):
        return self.turtle_smt.vars | self.item_smt.vars | self.tile_smt.vars | self.marker_smt.vars

    def pworld_indep_properties(self,
                                colors_straw,
                                colors_lemon,
                                colors_triangle,
                                colors_rectangle,
                                colors_circle,
                                colors_cross,
                                colors_char,
                                # count
                                count_straw,
                                count_lemon,
                                count_shapes,
                                count_chars,
                                symmetric
                                ):
        # basic properties
        C = [
            self.turtle_smt.properties(),
            self.item_smt.properties(
                # colors
                colors_straw=colors_straw,
                colors_lemon=colors_lemon,
                colors_triangle=colors_triangle,
                colors_rectangle=colors_rectangle,
                colors_circle=colors_circle,
                colors_cross=colors_cross,
                colors_char=colors_char,
                # count
                count_straw=count_straw,
                count_lemon=count_lemon,
                count_shapes=count_shapes,
                count_chars=count_chars
            ),
            self.tile_smt.properties(symmetric=symmetric),
            self.marker_smt.properties(),
            # mutual properties
            self._properties_between_turtle_and_tiles(),
            self._properties_between_turtle_and_items(),
            self._properties_between_tiles_and_items(),
        ]

        return simplify(And(C))

    def _properties_between_turtle_and_tiles(self):
        C = []
        for i in range(self.ntiles):
            C.extend([
                # turtle at (x,y) -> no items at (x,y)
                Implies(self.turtle_smt['turtle'][i],
                        self.item_smt['noname'][i]),
                # turtle at (x,y) -> cannot be forbidden
                Implies(self.turtle_smt['turtle'][i],
                        self.tile_smt['allowed'][i]),
                # turtle at (x,y) -> turtle cannot be completely surrounded by walls
                Implies(self.turtle_smt['turtle'][i],
                        Not(And(self.tile_smt['topW'][i],
                                self.tile_smt['rightW'][i],
                                self.tile_smt['leftW'][i],
                                self.tile_smt['bottomW'][i])))
            ])
        return And(C)

    def _properties_between_turtle_and_items(self):
        # turtle at (x,y) -> no items at (x,y)
        C = [Implies(self.turtle_smt['turtle'][i], self.item_smt['noname'][i]) for i in range(self.ntiles)]
        return And(C)

    def _properties_between_tiles_and_items(self):
        C = []
        for i in range(self.ntiles):
            C.extend([
                # not allowed -> noname
                Implies(Not(self.tile_smt['allowed'][i]), self.item_smt['noname'][i]),
                # item at the grid -> no walls around
                Implies(Not(self.item_smt['noname'][i]),
                        Not(And(self.tile_smt['topW'][i],
                                self.tile_smt['leftW'][i],
                                self.tile_smt['rightW'][i],
                                self.tile_smt['bottomW'][i]))
                        )
            ])
        return And(C)

    def properties_for_pworld(self, pworld, marker_world):
        C = []

        turtle = pworld.init_turtle
        items = pworld.items
        tiles = pworld.tiles
        drawn_markers = pworld.drawn_markers

        # constraints for the given turtle
        if turtle is not None:
            assert turtle.y is not None and turtle.x is not None
            i = yx2i(turtle.y, turtle.x, self.cols)
            C.append(self.turtle_smt['turtle'][i] == True)
            # turtle direction
            if turtle.dir is not None:
                C.append(self.turtle_smt['dir'][turtle.dir])

        for y in range(self.rows):
            for x in range(self.cols):
                i = yx2i(y, x, self.cols)
                # partially initialized from given tiles
                if tiles[y, x].exist is not None:
                    C.append(self.tile_smt['exist'][i] == tiles[y, x].exist)
                if tiles[y, x].allowed is not None:
                    C.append(self.tile_smt['allowed'][i] == tiles[y, x].allowed)
                if tiles[y, x].wall_top is not None:
                    C.append(self.tile_smt['topW'][i] == tiles[y, x].wall_top)
                if tiles[y, x].wall_right is not None:
                    C.append(self.tile_smt['rightW'][i] == tiles[y, x].wall_right)
                if tiles[y, x].wall_bottom is not None:
                    C.append(self.tile_smt['bottomW'][i] == tiles[y, x].wall_bottom)
                if tiles[y, x].wall_left is not None:
                    C.append(self.tile_smt['leftW'][i] == tiles[y, x].wall_left)

                # partially initialized from given items
                if items[y, x] is not None:
                    if items[y, x].color is not None:
                        C.append(self.item_smt[items[y, x].color][i] == True)
                    if items[y, x].name is not None:
                        C.append(self.item_smt[items[y, x].name][i] == True)
                    if items[y, x].count is not None:
                        C.append(self.item_smt['count'][i] == int(items[y, x].count))

                if marker_world:
                    # partially initialized from drawn markers
                    if drawn_markers[y, x].top is not None:
                        C.append(drawn_markers[y, x].top == self.marker_smt['topM'][i])
                        C.append(MARKER_COLORS[drawn_markers[y, x].top_color] == self.marker_smt['topM_color'][i])
                    else:
                        C.append(self.marker_smt['topM'][i] == False)

                    if drawn_markers[y, x].left is not None:
                        C.append(drawn_markers[y, x].left == self.marker_smt['leftM'][i])
                        C.append(MARKER_COLORS[drawn_markers[y, x].left_color] == self.marker_smt['leftM_color'][i])
                    else:
                        C.append(self.marker_smt['leftM'][i] == False)

                    if drawn_markers[y, x].right is not None:
                        C.append(drawn_markers[y, x].right == self.marker_smt['rightM'][i])
                        C.append(MARKER_COLORS[drawn_markers[y, x].right_color] == self.marker_smt['rightM_color'][i])
                    else:
                        C.append(self.marker_smt['rightM'][i] == False)

                    if drawn_markers[y, x].bottom is not None:
                        C.append(drawn_markers[y, x].bottom == self.marker_smt['bottomM'][i])
                        C.append(MARKER_COLORS[drawn_markers[y, x].bottom_color] == self.marker_smt['bottomM_color'][i])
                    else:
                        C.append(self.marker_smt['bottomM'][i] == False)

        return And(C)

    def _properties_for_sim_items(self, ref_world):
        """
        1. Same type of items
        2. Similar count
        3. Similar colors
        4. Similar shapes
        5. Similar items ratio
        """
        C = []
        # only allow the same type of items as the inp_world
        for i in range(self.ntiles):
            forbidden_types = ITEM_TYPE - ref_world.itemtypes_used
            for t in forbidden_types:
                if t == 'fruit':
                    C.extend([self.item_smt[name][i] == False for name in FRUIT_VARS])
                elif t == 'shape':
                    C.extend([self.item_smt[name][i] == False for name in SHAPE_VARS])
                elif t == 'char':
                    C.extend([self.item_smt[name][i] == False for name in CHAR_VARS])
        # count
        if not ref_world.use_count:
            C.extend([self.item_smt['count'][i] <= 1 for i in range(self.ntiles)])

        # for tasks with more than 3 different colors
        if len(ref_world.colors_used) >= 4:
            # at most one type of shape
            C.append(exactly_one([Or(self.item_smt.vars[shape]) for shape in SHAPE_VARS]))

        # for tasks focusing on `shape`
        if len(ref_world.shapes_used) >= 3:
            # <= 3 colors
            C.append(AtMost(*[Or(self.item_smt.vars[c]) for c in COLOR_VARS if c != 'nocolor'], 3))
            C.append(AtLeast(*[Or(self.item_smt.vars[c]) for c in COLOR_VARS if c != 'nocolor'], 3))

            # make the number of different colors nearly the same
            N_RED = Sum([If(self.item_smt['red'][i], 1, 0) for i in range(self.ntiles)])
            N_GREEN = Sum([If(self.item_smt['green'][i], 1, 0) for i in range(self.ntiles)])
            N_BLUE = Sum([If(self.item_smt['blue'][i], 1, 0) for i in range(self.ntiles)])
            C.append(And(N_RED - N_GREEN <= 1))
            C.append(And(N_GREEN - N_RED <= 1))
            C.append(And(N_BLUE - N_RED <= 1))
            C.append(And(N_RED - N_BLUE <= 1))

            COLORS_CIRCLE = ('red', 'green', 'blue')
            for i in range(self.ntiles):
                C.append(Implies(self.vars['circle'][i], Or([self.vars[c][i] for c in COLORS_CIRCLE])))

        return And(C)

    def _properties_for_item_ratio(self, ref_world):
        """
        Currently, this is not really the ratio.
        If grid size increases, allow at most `ref_n_items + 1 * size_diff` items in generated tasks
        If grid size the same or smaller, keep the same number of items
        """
        C = []

        # number of the items
        n_items = Sum([If(self.item_smt['noname'][i], 0, 1) for i in range(self.ntiles)])

        # ref_item_ratio = ref_world.n_items / (ref_world.rows * ref_world.cols)

        if self.ntiles <= (ref_world.rows * ref_world.cols):
            # if the grid size is equal or smaller, then keep the same number of items (not ratio)
            C.append(n_items == ref_world.n_items)
        else:
            # if the grid size increases, then allow the item ratio in pworld to be n more or n less
            C.append(
                n_items <= ref_world.n_items + 1 * (max(self.rows, self.cols) - max(ref_world.rows, ref_world.cols)))
            C.append(n_items >= ref_world.n_items)

        return And(C)

    def _properties_for_wall_ratio(self, ref_world, wall_ratio_variation):
        assert wall_ratio_variation < 1
        assert wall_ratio_variation > 0

        C = []

        n_walls = Sum(self.tile_smt['topW']) + \
                  Sum(self.tile_smt['leftW']) + \
                  Sum(self.tile_smt['rightW']) + \
                  Sum(self.tile_smt['bottomW'])

        ref_wall_ratio = ref_world.n_walls / (ref_world.rows * ref_world.cols)

        if ref_wall_ratio <= 0:
            if self.ntiles <= (ref_world.rows * ref_world.cols):
                # if no walls in ref tasks and the grid size is equal or smaller
                # then not allow any walls in pworld
                C.extend([
                    Not(Or(self.tile_smt['topW'])),
                    Not(Or(self.tile_smt['leftW'])),
                    Not(Or(self.tile_smt['rightW'])),
                    Not(Or(self.tile_smt['bottomW']))
                ])
            else:
                # if no walls in ref tasks but grid size is larger
                # then don't put any constrains on the ratio of walls
                pass
        else:
            # if walls in ref world, then allow the wall ratio
            # in pworld to be x% more
            C.append(math.ceil(ref_wall_ratio * (1 + wall_ratio_variation) * self.ntiles) >= n_walls)
            C.append(n_walls > 0)
            # Note: constraint for lower bound of wall_ratio is removed,
            # because it may violate the constraint for forbidden areas
            # (each forbidden areas must be surrounded by walls)
            # C.append(math.floor(ref_wall_ratio * (1 - wall_ratio_variation) * self.ntiles) <= n_walls)
        return And(C)

    def _properties_for_forb_ratio(self, ref_world, forb_ratio_variation=0.2):
        C = []

        n_forbid = Sum([If(self.tile_smt['allowed'][i], 0, 1) for i in range(self.ntiles)])
        ref_forb_ratio = ref_world.n_forbidden_areas / (ref_world.rows * ref_world.cols)

        if ref_forb_ratio <= 0:
            if self.ntiles <= (ref_world.rows * ref_world.cols):
                # if no forbidden areas in ref tasks and the grid size is equal or smaller
                # then not allow any forbidden areas in the synthesized tasks
                C.append(And([Implies(self.tile_smt['exist'][i],
                                      self.tile_smt['allowed'][i])
                              for i in range(self.ntiles)]))
            else:
                # if no forbidden areas in ref tasks and the grid size is larger
                # then don't put any constrains on the ratio of forbidden areas
                pass

        else:
            # if there are forbidden areas in ref tasks
            # then keep the similar ratio of forbidden areas with the ref task
            C.append(math.ceil(ref_forb_ratio * (1 + forb_ratio_variation) * self.ntiles) >= n_forbid)
            C.append(math.floor(ref_forb_ratio * (1 - forb_ratio_variation) * self.ntiles) <= n_forbid)

        # non-exist
        if ref_world.non_existent_tiles == 0:
            C.append(And(self.tile_smt['exist']))
        return And(C)

    def properties_for_item_world(self,
                                  ref_world,
                                  req_reachable=True,
                                  req_sim_items=True,
                                  wall_ratio_variation=0.1,
                                  forb_ratio_variation=0.2
                                  ):
        NO_MARKERS = And(Not(Or(self.vars['topM'])),
                         Not(Or(self.vars['leftM'])),
                         Not(Or(self.vars['rightM'])),
                         Not(Or(self.vars['bottomM'])))
        ALL_TILES_EXIST = And(self.tile_smt['exist'])

        C = [
            NO_MARKERS,
            ALL_TILES_EXIST,
            self._properties_for_wall_ratio(ref_world, wall_ratio_variation=wall_ratio_variation),
            self._properties_for_forb_ratio(ref_world, forb_ratio_variation=forb_ratio_variation),
            self._properties_for_item_ratio(ref_world),
            properties_for_reachability(self.vars, self.rows, self.cols) if req_reachable else True,
            self._properties_for_sim_items(ref_world=ref_world) if req_sim_items else True,
        ]
        return And(C)

    def properties_for_marker_world(self):
        """
        Return constraints that only apply to marker world.
        """
        NO_ITEMS = And(And(self.vars['noname']),
                       And(self.vars['nocolor']),
                       And([self.vars['count'][i] == 0
                            for i in range(len(self.vars['count']))]))

        # if tile exists, then no walls
        NO_WALLS = And([Implies(self.vars['exist'][i],
                                self.vars[f'{pos}W'][i] == False)
                        for i in range(self.ntiles)
                        for pos in ['top', 'left', 'right', 'bottom']])

        C = [
            NO_ITEMS,
            NO_WALLS,
        ]
        return And(C)

    def __getitem__(self, i):
        return self.vars[i]
