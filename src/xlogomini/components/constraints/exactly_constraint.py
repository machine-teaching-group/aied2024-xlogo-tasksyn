from src.xlogomini.components.constraints.base_constraint import *


class ExactlyConstraints(BaseConstraints):
    def __init__(self, json):
        BaseConstraints.__init__(self, json)
