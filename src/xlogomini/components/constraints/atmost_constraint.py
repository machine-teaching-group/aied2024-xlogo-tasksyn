from src.xlogomini.components.constraints.exactly_constraint import *


class AtMostConstraints(ExactlyConstraints):
    def __init__(self, json):
        ExactlyConstraints.__init__(self, json)
