from .base_component_smt import ComponentSMT
from z3 import BoolVector, And
from src.xlogomini.utils.formulas import exactly_one
from src.xlogomini.utils.enums import DEG_MAP


class TurtleSMT(ComponentSMT):
    def __init__(self, rows, cols):
        ComponentSMT.__init__(self, rows, cols)
        # position
        self.vars['turtle'] = BoolVector('turtle', rows * cols)
        # dir
        self.vars['dir'] = BoolVector('dir', len(DEG_MAP))

    def properties(self):
        C = [
            # exactly one turtle
            exactly_one(self.vars['turtle']),
            # only one dir could be true
            exactly_one(self.vars['dir'])
        ]
        return And(C)
