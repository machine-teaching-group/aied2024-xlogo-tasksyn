from src.xlogomini.smt.world.base_component_smt import *
from z3 import And, Or, BoolVector, Const, is_bool, is_const, eq, Implies, Not
from src.xlogomini.utils.helpers import get_neighboring_ids, i2yx
from src.xlogomini.utils.enums import MarkerColor
from src.xlogomini.utils.enums import nocolor


class MarkerSMT(ComponentSMT):
    def __init__(self, rows, cols):
        ComponentSMT.__init__(self, rows, cols)
        self.vars['topM'] = BoolVector('topM', rows * cols)
        self.vars['leftM'] = BoolVector('leftM', rows * cols)
        self.vars['rightM'] = BoolVector('rightM', rows * cols)
        self.vars['bottomM'] = BoolVector('bottomM', rows * cols)

        self.vars['topM_color'] = [Const(f'topM_color__{i}', MarkerColor) for i in range(rows * cols)]
        self.vars['leftM_color'] = [Const(f'leftM_color__{i}', MarkerColor) for i in range(rows * cols)]
        self.vars['rightM_color'] = [Const(f'rightM_color__{i}', MarkerColor) for i in range(rows * cols)]
        self.vars['bottomM_color'] = [Const(f'bottomM_color__{i}', MarkerColor) for i in range(rows * cols)]

    def set_empty(self):
        return And(
            Not(Or(self.vars['topM'])),
            Not(Or(self.vars['leftM'])),
            Not(Or(self.vars['rightM'])),
            Not(Or(self.vars['bottomM']))
        )

    def properties(self):
        C = []
        # have marker -> marker color != none
        for i in range(self.rows * self.cols):
            # marker exists -> marker color exists
            C.extend([
                self.vars['topM'][i] == (self.vars['topM_color'][i] != nocolor),
                self.vars['leftM'][i] == (self.vars['leftM_color'][i] != nocolor),
                self.vars['rightM'][i] == (self.vars['rightM_color'][i] != nocolor),
                self.vars['bottomM'][i] == (self.vars['bottomM_color'][i] != nocolor)
            ])

            # properties for neighboring tiles
            neighbors = get_neighboring_ids(i, self.rows, self.cols)
            top_id = neighbors['top']
            left_id = neighbors['left']
            right_id = neighbors['right']
            bottom_id = neighbors['bottom']
            if top_id is not None:
                C.extend([
                    Implies(self.vars['bottomM'][top_id], self.vars['topM'][i]),
                    self.vars['bottomM_color'][top_id] == self.vars['topM_color'][i]
                ])
            if left_id is not None:
                C.extend([
                    Implies(self.vars['rightM'][left_id], self.vars['leftM'][i]),
                    self.vars['rightM_color'][left_id] == self.vars['leftM_color'][i]
                ])
            if right_id is not None:
                C.extend([
                    Implies(self.vars['leftM'][right_id], self.vars['rightM'][i]),
                    self.vars['leftM_color'][right_id] == self.vars['rightM_color'][i]
                ])
            if bottom_id is not None:
                C.extend([
                    Implies(self.vars['topM'][bottom_id], self.vars['bottomM'][i]),
                    self.vars['topM_color'][bottom_id] == self.vars['bottomM_color'][i]
                ])

            # properties for edged tiles
            y, x = i2yx(i, self.cols)
            if x == 0:
                C.append(self.vars['leftM'][i] == False)
            if x == self.cols - 1:
                C.append(self.vars['rightM'][i] == False)
            if y == 0:
                C.append(self.vars['topM'][i] == False)
            if y == self.rows - 1:
                C.append(self.vars['bottomM'][i] == False)

        return And(C)
