import argparse
from z3 import Int, Solver, Not, And, Or, simplify, sat, Distinct, Const, Implies
import json
import os
from src.xlogomini.components.task import Goal
from src.xlogomini.utils.formulas import Equals, exactly_the_same
from src.xlogomini.utils.json_conversions import cnf2json
from src.xlogomini.utils.boolean_logic import cnf2dnf, dnf2cnf
from src.xlogomini.utils.enums import *
from src.xlogomini.smt.world.item_smt import ItemSMT
from src.xlogomini.smt.goal.goal_smt import GoalSMT
from src.xlogomini.utils.model_conversions import model2values

Fruit, fruits = EnumSort('Fruit', ['strawberry', 'lemon', 'noname'])
Color, colors = EnumSort('Color',
                         ['red', 'blue', 'green', 'black', 'yellow', 'orange', 'pink', 'purple', 'nocolor'])
Shape, shapes = EnumSort('Shape', ["triangle", "rectangle", "cross", "circle", 'noname'])
Char, chars = EnumSort('Char', ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
                                "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
                                "noname"])
Count, counts = EnumSort('Count', ["_0", "_1", "_2", "_3", "_4"])

fruits = {str(k): k for k in fruits}
colors = {str(k): k for k in colors}
shapes = {str(k): k for k in shapes}
chars = {str(k): k for k in chars}
counts = {str(k): k for k in counts}


class GoalSyn():
    def __init__(self, goal_json):
        self.goal = Goal.init_from_json(goal_json)

        self.rows = 3
        self.cols = 3

        self._build_vars()

    def _build_vars(self):
        # for goal mutation
        vars = {}

        # var of total_cnt for 'sum'
        if 'sum' in self.goal.objs.keys():
            vars['sum_total_0'] = Int('sum_total_0')  # make the format the same as other variables

        vars_tree = []
        # for each objective
        for obj_name in self.goal.objs.keys():
            for obj in self.goal.objs[obj_name]:
                vars_obj = []
                # for each spec
                for s_i, spec in enumerate(obj.specs):
                    vars_spec = []
                    # for each clause
                    for c_i, clause in enumerate(spec.cnf):
                        vars_clause = []
                        # for each literal
                        for l_i, l in enumerate(clause):
                            # remove negation sign
                            if l[0] == '-':
                                l = l[1:]

                            if l in NAME_VARS:
                                if l in FRUIT_VARS:
                                    var_name = f"{obj.obj_name}_fruit_{l}"
                                    vars[var_name] = Const(var_name, Fruit)
                                elif l in CHAR_VARS:
                                    var_name = f"{obj.obj_name}_char_{l}"
                                    vars[var_name] = Const(var_name, Char)
                                elif l in SHAPE_VARS:
                                    var_name = f"{obj.obj_name}_shape_{l}"
                                    vars[var_name] = Const(var_name, Shape)
                            elif l in COLOR_VARS:
                                var_name = f"{obj.obj_name}_color_{l}"
                                vars[var_name] = Const(var_name, Color)
                            elif l in COUNT_VARS:
                                var_name = f"{obj.obj_name}_count_{l}"
                                vars[var_name] = Const(var_name, Count)
                            else:
                                raise ValueError(f"{l} not recognized")
                            vars_clause.append(var_name)
                        vars_spec.append(vars_clause)
                    vars_obj.append(vars_spec)
                vars_tree.append(vars_obj)

        self.vars = vars
        self.vars_tree = vars_tree

    def properties(self, max_count_inc=0, max_count_dec=0):
        C = [
            self.properties_for_items(),
            self.properties_for_not_all_empty(),
            self.properties_for_distinction_and_equality()
        ]
        if 'sum' in self.goal.objs.keys():
            C.append(self.vars['sum_total_0'] <= self.goal.objs['sum'][0].total_cnt + max_count_inc)
            C.append(self.vars['sum_total_0'] >= self.goal.objs['sum'][0].total_cnt - max_count_dec)
        return And(C)

    def properties_for_items(self):
        C = []

        def collect_vars_data(vars):
            data_dict = {}
            for var in vars:
                type = str(var).split('_')[1]
                data_dict[type] = var
            return data_dict

        for o in self.vars_tree:
            for s in o:
                dnf = cnf2dnf(s)
                for c in dnf:
                    data = collect_vars_data(c)
                    if 'color' in data.keys() and 'shape' in data.keys():
                        C.append(Implies(
                            Or(self.vars[data['shape']] == shapes['triangle'],
                               self.vars[data['shape']] == shapes['rectangle'],
                               self.vars[data['shape']] == shapes['cross'],
                               ),
                            Or(self.vars[data['color']] == colors['blue'],
                               self.vars[data['color']] == colors['red'],
                               self.vars[data['color']] == colors['green'],
                               )))
                    if 'color' in data.keys() and 'fruit' in data.keys():
                        C.extend([
                            Implies(
                                self.vars[data['fruit']] == shapes['lemon'],
                                self.vars[data['color']] == colors['yellow']
                            ),
                            Implies(
                                self.vars[data['fruit']] == shapes['strawberry'],
                                self.vars[data['color']] == colors['red']
                            )])
        return And(C)

    def properties_for_not_all_empty(self):
        C = []

        for o in self.vars_tree:
            for s in o:
                for c in s:
                    # the literals in a clause cannot be all empty
                    literal_all_empty = []
                    for l in c:
                        obj_name, attr, id = l.split('_')
                        if attr == 'fruit':
                            literal_all_empty.append(self.vars[l] == fruits['noname'])
                        elif attr == 'shape':
                            literal_all_empty.append(self.vars[l] == shapes['noname'])
                        elif attr == 'char':
                            literal_all_empty.append(self.vars[l] == chars['noname'])
                        elif attr == 'color':
                            literal_all_empty.append(self.vars[l] == colors['nocolor'])
                        elif attr == 'count':
                            literal_all_empty.append(self.vars[l] == counts['_0'])
                    C.append(Not(And(literal_all_empty)))
        return And(C)

    def properties_for_distinction_and_equality(self):
        C = []

        # constraints on the tree structure
        colors_cont = []
        chars_cont = []
        fruits_cont = []
        shapes_cont = []

        for o in self.vars_tree:
            for s in o:
                for c in s:
                    for l in c:
                        obj_name, attr, id = l.split('_')
                        if attr == 'fruit':
                            fruits_cont.append(self.vars[l])
                        elif attr == 'shape':
                            shapes_cont.append(self.vars[l])
                        elif attr == 'char':
                            chars_cont.append(self.vars[l])
                        elif attr == 'color':
                            colors_cont.append(self.vars[l])

        def collect_vars_data(vars):
            data_dict = {}
            for var in vars:
                org_value = str(var).split('_')[-1]
                if org_value not in data_dict.keys():
                    data_dict[org_value] = [var]
                else:
                    data_dict[org_value].append(var)
            return data_dict

        # all variables within an objective are distinct
        if len(colors_cont) > 0:
            data_dict = collect_vars_data(colors_cont)
            C.extend([
                And([Equals(data_dict[k]) for k in data_dict.keys()]),
                Distinct([data_dict[k][0] for k in data_dict.keys()])
            ])
        if len(fruits_cont) > 0:
            data_dict = collect_vars_data(fruits_cont)
            C.extend([
                And([Equals(data_dict[k]) for k in data_dict.keys()]),
                Distinct([data_dict[k][0] for k in data_dict.keys()])
            ])
        if len(chars_cont) > 0:
            data_dict = collect_vars_data(chars_cont)
            C.extend([
                And([Equals(data_dict[k]) for k in data_dict.keys()]),
                Distinct([data_dict[k][0] for k in data_dict.keys()])
            ])
        if len(shapes_cont) > 0:
            data_dict = collect_vars_data(shapes_cont)
            C.extend([
                And([Equals(data_dict[k]) for k in data_dict.keys()]),
                Distinct([data_dict[k][0] for k in data_dict.keys()])
            ])
        return simplify(And(C))

    def model2instance(self, model_values):
        """
        :param model_values: a dict containing the value for each symbol (e.g., {'find_name_0': 10, 'find_color_0': 1})
        """
        sym_value = {k: str(model_values[k]) for k, v in model_values.items()}

        goal_json = []

        for o in self.vars_tree:
            specs = []
            for s in o:
                cnf = []
                for c in s:
                    parsed_c = [sym_value[l] for l in c if sym_value[l] not in ['noname', 'nocolor']]
                    cnf.append(parsed_c)

                # cnf to dnf
                dnf = cnf2dnf(cnf)
                simplified_dnf = [c for c in dnf if self.is_valid_dnf_clause(c)]

                # It's possible that none of clauses are valid
                if len(simplified_dnf) > 0:
                    simplified_cnf = dnf2cnf(simplified_dnf)
                    specs.append(cnf2json(simplified_cnf))
            # parse obj_name
            obj_name = o[0][0][0].split('_')[0]
            # add objective to the goal
            goal_json.append({
                "name"     : obj_name,
                "specs"    : specs,
                "total_cnt": model_values['sum_total_0'].as_long() if obj_name == 'sum' else None
            })

        return Goal.init_from_json(goal_json)

    def is_valid_instance(self, goal):
        """
        Check if the generated goal is valid
        """
        obj_names = goal._get_list_of_obj_names()

        # only `forbid`, return False
        if len(obj_names) == 1 and 'forbid' in obj_names:
            return False

        # 'concat' but only 1 or 0 specs, return False
        if 'concat' in obj_names and len(goal.objs['concat'][0].specs) <= 1:
            return False

        # construct visited
        if 'concat' in obj_names or 'sum' in obj_names:
            assert len(obj_names) == 1
            visited = list(range(6))
        elif 'collectall' in obj_names:
            visited = list(range(6))
        else:
            visited = [0, 1]

        item_smt = ItemSMT(self.rows, self.cols)
        goal_smt = GoalSMT(self.rows, self.cols, item_smt.vars, goal, visited)

        # constraints
        s = Solver()
        s.add(item_smt.properties(
            colors_straw=['red'],
            colors_lemon=['yellow'],
            colors_char=['black'],
            colors_triangle=['red', 'green', 'blue'],
            colors_rectangle=['red', 'green', 'blue'],
            colors_cross=['red', 'green', 'blue'],
            colors_circle=['red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple', 'black'],
            # count
            count_straw=[1, 2, 3, 4],
            count_lemon=[1],
            count_shapes=[1],
            count_chars=[1]
        ))

        s.add(goal_smt.properties())

        return s.check() == sat

    def is_valid_dnf_clause(self, clause):
        item_smt = ItemSMT(1, 1)

        s = Solver()
        s.add(item_smt.properties(
            # colors
            colors_straw=['red'],
            colors_lemon=['yellow'],
            colors_char=['black'],
            colors_triangle=['red', 'green', 'blue'],
            colors_rectangle=['red', 'green', 'blue'],
            colors_cross=['red', 'green', 'blue'],
            colors_circle=['red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple', 'black'],
            # count
            count_straw=[1, 2, 3, 4],
            count_lemon=[1],
            count_shapes=[1],
            count_chars=[1]
        ))

        for l in clause:
            if l in NAME_VARS or l in COLOR_VARS:
                s.add(item_smt.vars[l][0] == True)
            elif l in COUNT_VARS:
                s.add(item_smt.vars['count'][0] == l)
            else:
                raise ValueError(f"{l} not recognized")

        return s.check() == sat

    def __getitem__(self, var_name):
        return self.vars[var_name]

    def generate(self, n_max=10, save_dir=None, save=False,
                 max_count_inc=0, max_count_dec=0, same_goal=True):
        """
        Generate `n` instances.
        If `save`=True, then the generated instance are saved into a file.
        """
        if same_goal:
            return [self.goal]
        s = Solver()
        s.add(self.properties(max_count_inc=max_count_inc,
                              max_count_dec=max_count_dec))

        mutations = set()
        while s.check() == sat and len(mutations) < n_max:
            model_values = model2values(self.vars, s.model())

            # synthesized code_constraints
            instance = self.model2instance(model_values)

            mutations.add(instance)

            # next model not exactly the same
            s.add(Not(exactly_the_same(self.vars, model_values)))
        # save to file
        if save:
            # create dir if not exists
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            # save to file
            with open(f'{save_dir}/output_goals.json', 'w') as f:
                goal_jsons = [goal.to_json() for goal in mutations]
                json.dump(goal_jsons, f)

        return mutations