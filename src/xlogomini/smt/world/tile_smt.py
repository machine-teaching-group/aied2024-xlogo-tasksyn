from src.xlogomini.smt.world.base_component_smt import ComponentSMT
from z3 import BoolVector, And, Not, Or, Implies, Bool
from src.xlogomini.utils.helpers import yx2i
from src.xlogomini.utils.helpers import right_tile_id, bottom_tile_id, get_edges, get_neighboring_ids
from src.xlogomini.utils.formulas import exactly_one, wall_vars_along_the_path


class TileSMT(ComponentSMT):
    def __init__(self, rows, cols):
        ComponentSMT.__init__(self, rows, cols)
        self.vars['topW'] = BoolVector('topW', self.ntiles)
        self.vars['leftW'] = BoolVector('leftW', self.ntiles)
        self.vars['rightW'] = BoolVector('rightW', self.ntiles)
        self.vars['bottomW'] = BoolVector('bottomW', self.ntiles)
        self.vars['allowed'] = BoolVector('allowed', self.ntiles)
        self.vars['exist'] = BoolVector('exist', self.ntiles)

    def properties(self, symmetric=True):
        C = [
            self.properties_for_adjacent_walls(),
            self.properties_for_edged_tiles(),
            self.properties_for_walls_of_forbidden_areas()
        ]

        if symmetric:
            C.append(self.properties_for_symmetric_forbidden_areas())

        return And(C)

    def properties_for_symmetric_forbidden_areas(self):
        C = []

        C_sym_lr = []
        for y in range(self.rows):
            for x in range(self.cols // 2):
                C_sym_lr.append(self.vars['allowed'][yx2i(y, x, self.cols)] ==
                                self.vars['allowed'][yx2i(y, self.cols - 1 - x, self.cols)])

        C_sym_td = []
        for y in range(self.rows // 2):
            for x in range(self.cols):
                C_sym_td.append(self.vars['allowed'][yx2i(y, x, self.cols)] ==
                                self.vars['allowed'][yx2i(self.rows - 1 - y, x, self.cols)])

        C_sym_diag_left = []
        if self.rows == self.cols:
            for y in range(self.rows):
                for x in range(y, self.cols):
                    C_sym_diag_left.append(self.vars['allowed'][yx2i(y, x, self.cols)] ==
                                           self.vars['allowed'][yx2i(x, y, self.cols)])
            C.append(And(C_sym_diag_left))

        C_sym_diag_right = []
        if self.rows == self.cols:
            for y in range(self.rows):
                for x in range(self.cols - y - 1):
                    C_sym_diag_right.append(self.vars['allowed'][yx2i(y, x, self.cols)] ==
                                            self.vars['allowed'][yx2i(self.rows - x - 1, self.cols - y - 1, self.cols)])
            C.append(And(C_sym_diag_right))

        C.append(And(C_sym_lr))
        C.append(And(C_sym_td))
        return Or(C)

    def properties_for_walls_of_forbidden_areas(self):
        """
        1. No walls in between two forbidden areas.
        2. Must be a wall in between a forbidden area and a non-forbidden area.
        """
        C = []

        def walls_between_two_grids(i, j, wall_pos):
            return And([
                # two grids are forbidden, no wall in between
                Implies(And(Not(self.vars['allowed'][i]),
                            Not(self.vars['allowed'][j])),
                        self.vars[f'{wall_pos}W'][i] == False),
                # any of two grids are forbidden, must be a wall in between
                Implies(And(self.vars['exist'][i],
                            self.vars['exist'][j]),
                        Implies(exactly_one([self.vars['allowed'][i],
                                             self.vars['allowed'][j]]),
                                self.vars[f'{wall_pos}W'][i] == True))
            ])

        for i in range(self.ntiles):
            # allowed exist
            #    1     1
            #    1     0 (cannot happen)
            #    0     1
            #    0     0

            # relation between allowed and exist
            DISABLE_ALLOWED_1_EXIST_0 = Not(And(self.vars['allowed'][i] == True,
                                                self.vars['exist'][i] == False))

            ids = get_neighboring_ids(i, self.rows, self.cols)

            top_id = ids['top']
            left_id = ids['left']
            right_id = ids['right']
            bottom_id = ids['bottom']

            walls = []
            if top_id is not None:
                C.append(walls_between_two_grids(i, top_id, 'top'))
                walls.append(self.vars['topW'][i])
            if left_id is not None:
                C.append(walls_between_two_grids(i, left_id, 'left'))
                walls.append(self.vars['leftW'][i])
            if right_id is not None:
                C.append(walls_between_two_grids(i, right_id, 'right'))
                walls.append(self.vars['rightW'][i])
            if bottom_id is not None:
                C.append(walls_between_two_grids(i, bottom_id, 'bottom'))
                walls.append(self.vars['bottomW'][i])

            # surrounded by walls -> forbidden area
            SUR_BY_WALLS_IMPLIES_FORBIDDEN = Implies(And(walls), Not(self.vars['allowed'][i]))

            C.extend([
                DISABLE_ALLOWED_1_EXIST_0,
                SUR_BY_WALLS_IMPLIES_FORBIDDEN
            ])

        return And(C)

    def properties_for_adjacent_walls(self):
        C = []
        # adjacent walls must be consistent
        edges = get_edges(self.rows, self.cols)
        for p1, p2 in edges:
            assert p1 < p2
            if right_tile_id(p1, self.rows, self.cols) == p2:
                C.append(self.vars['rightW'][p1] == self.vars['leftW'][p2])
            elif bottom_tile_id(p1, self.rows, self.cols) == p2:
                C.append(self.vars['bottomW'][p1] == self.vars['topW'][p2])
        return And(C)

    def properties_for_edged_tiles(self):
        C = []
        for y in range(self.rows):
            for x in range(self.cols):
                i = yx2i(y, x, self.cols)
                if x == 0:
                    # no left wall
                    C.append(Not(self.vars['leftW'][i]))
                if y == 0:
                    # no top wall
                    C.append(Not(self.vars['topW'][i]))
                if x == self.cols - 1:
                    # no right wall
                    C.append(Not(self.vars['rightW'][i]))
                if y == self.rows - 1:
                    # no bottom wall
                    C.append(Not(self.vars['bottomW'][i]))
        return And(C)
