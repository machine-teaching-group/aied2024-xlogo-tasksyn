class ObjectiveSMT():
    def __init__(self, rows, cols, vars, objective, visited):
        self.rows = rows
        self.cols = cols
        self.ntiles = rows * cols

        self.vars = vars

        self.objective = objective
        self.visited = visited

        self.cnfs = [objective.specs[i].cnf for i in range(len(objective.specs))]

    def properties(self):
        pass

    def feasible_path(self, path):
        return True
