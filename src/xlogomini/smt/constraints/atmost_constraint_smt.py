from src.xlogomini.smt.constraints.exactly_constraint_smt import ExactlyConstraintSMT


class AtMostConstraintSMT(ExactlyConstraintSMT):
    def __init__(self, js):
        ExactlyConstraintSMT.__init__(self, js)
        self.id = "most"
        self.vars = self._build_vars()
