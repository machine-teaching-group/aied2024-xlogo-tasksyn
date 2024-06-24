class ComponentSMT():
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.ntiles = rows * cols

        self.vars = {}
        self.var_names = self.vars.keys()

    def __getitem__(self, item):
        return self.vars[item]
