from .base_component_smt import ComponentSMT
from z3 import BoolVector, IntVector, AtMost, AtLeast, And, Or, Not, Implies
from src.xlogomini.utils.enums import *


class ItemSMT(ComponentSMT):
    def __init__(self, rows, cols):
        ComponentSMT.__init__(self, rows, cols)
        # name
        for v in NAME_VARS:
            self.vars[v] = BoolVector(v, rows * cols)
        # color
        for v in COLOR_VARS:
            self.vars[v] = BoolVector(v, rows * cols)
        # count
        self.vars['count'] = IntVector('count', rows * cols)

    def set_empty(self):
        return And(
            And(self.vars['noname']),
            And(self.vars['nocolor']),
            And([self.vars['count'][i] == 0 for i in range(len(self.vars['count']))])
        )

    def properties(self,
                   colors_straw=('red',),
                   colors_lemon=('yellow',),
                   colors_char=('black',),
                   colors_triangle=('red', 'green', 'blue'),
                   colors_rectangle=('red', 'green', 'blue'),
                   colors_cross=('red', 'green', 'blue'),
                   colors_circle=('red', 'green', 'blue', 'yellow',
                                  'orange', 'pink', 'purple', 'black'),
                   # counts
                   count_straw=(1, 2, 3, 4),
                   count_lemon=(1,),
                   count_shapes=(1,),
                   count_chars=(1,)):
        C = [
            self.properties_for_name(),
            self.properties_for_color(colors_straw,
                                      colors_lemon,
                                      colors_char,
                                      colors_triangle,
                                      colors_rectangle,
                                      colors_cross,
                                      colors_circle),
            self.properties_for_count(count_straw,
                                      count_lemon,
                                      count_shapes,
                                      count_chars),
        ]
        return And(C)

    def properties_for_name(self):
        C = []
        for i in range(self.ntiles):
            name_list = [self.vars[name][i] for name in NAME_VARS]  # [x_i_strawberry, x_i_lemon, ...]
            # exactly one of the names can be true
            C.extend([
                AtLeast(*name_list, 1),
                AtMost(*name_list, 1),
                # noname <=> nocolor <=> count=0
                self.vars['nocolor'][i] == self.vars['noname'][i],
                self.vars['noname'][i] == (self.vars['count'][i] == 0)
            ])
        return And(C)

    def properties_for_count(self,
                             count_straw,
                             count_lemon,
                             count_shapes,
                             count_chars):
        C = []
        for i in range(self.ntiles):
            C.extend([
                # count for straw
                Implies(self.vars['strawberry'][i],
                        Or([self.vars['count'][i] == cnt for cnt in count_straw])),
                # count for lemon
                Implies(self.vars['lemon'][i],
                        Or([self.vars['count'][i] == cnt for cnt in count_lemon])),
                # count for shape
                Implies(Or([self.vars[shape][i] for shape in SHAPE_VARS]),
                        Or([self.vars['count'][i] == cnt for cnt in count_shapes])),
                # count for chars
                Implies(Or([self.vars[char][i] for char in CHAR_VARS]),
                        Or([self.vars['count'][i] == cnt for cnt in count_chars])),
            ])
        return And(C)

    def properties_for_color(self,
                             colors_straw,
                             colors_lemon,
                             colors_char,
                             colors_triangle,
                             colors_rectangle,
                             colors_cross,
                             colors_circle):
        C = []
        for i in range(self.ntiles):
            # general constraints for items
            clr_list = [self.vars[color][i] for color in COLOR_VARS]  # [x_i_red, x_i_blue, ...]
            # exactly one of the colors can be true
            C.extend([AtLeast(*clr_list, 1), AtMost(*clr_list, 1)])

            # colors for strawberry
            C.append(Implies(self.vars['strawberry'][i],
                             Or([self.vars[c][i] for c in colors_straw])))
            # colors for lemon
            C.append(Implies(self.vars['lemon'][i],
                             Or([self.vars[c][i] for c in colors_lemon])))
            # colors for triangle
            C.append(Implies(self.vars['triangle'][i],
                             Or([self.vars[c][i] for c in colors_triangle])))
            # colors for rectangle
            C.append(Implies(self.vars['rectangle'][i],
                             Or([self.vars[c][i] for c in colors_rectangle])))
            # colors for cross
            C.append(Implies(self.vars['cross'][i],
                             Or([self.vars[c][i] for c in colors_cross])))
            # colors for circle
            C.append(Implies(self.vars['circle'][i],
                             Or([self.vars[c][i] for c in colors_circle])))
            # colors for char
            C.extend([Implies(Or([self.vars[char][i] for char in CHAR_VARS]),
                              Or([self.vars[c][i] for c in colors_char]))])
        return And(C)
