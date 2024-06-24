from src.xlogomini.components.task import CodeConstraints
from src.xlogomini.smt.code.base_block_smt import noblock
from src.xlogomini.smt.constraints.exactly_constraint_smt import ExactlyConstraintSMT
from src.xlogomini.smt.constraints.startby_constraint_smt import StartByConstraintSMT
from src.xlogomini.smt.constraints.atmost_constraint_smt import AtMostConstraintSMT
from z3 import And, Implies, Sum, Not, sat, Solver, If


class CodeConstraintsSMT():
    def __init__(self, constraints):
        self.instance_type = 'constraints'
        self.mutated = False
        if type(constraints) == dict:
            self.constraints = constraints
        elif type(constraints) == list:
            if len(constraints) > 0:
                self.constraints = constraints[0]
            else:
                self.constraints = {}
        else:
            raise ValueError("Constraints not recognized.")

        self.body = {
            "exactly" : ExactlyConstraintSMT(
                self.constraints['exactly'] if 'exactly' in self.constraints.keys() else {}),
            "at_most" : AtMostConstraintSMT(
                self.constraints['at_most'] if 'at_most' in self.constraints.keys() else {}),
            "start_by": StartByConstraintSMT(
                self.constraints['start_by'] if 'start_by' in self.constraints.keys() else [])
        }
        self.vars = self._build_vars()

    def _build_vars(self):
        vars = {}
        vars.update(self.body['exactly'].vars)
        vars.update(self.body['at_most'].vars)
        vars.update(self.body['start_by'].vars)
        return vars

    def properties(self, max_dec, max_inc):
        """
        :param max_dec: Max number of constraints can be deleted
        :param max_inc: Max number of constraints can be added
        """
        n_type = int(len(self.body['exactly'].js) > 0) + int(
            len(self.body['at_most'].js) > 0) + int(
            len(self.body['start_by'].js) > 0)
        C = [
            self.body['exactly'].properties(),
            self.body['at_most'].properties(),
            self.body['start_by'].properties(),

            (self.body['exactly'].size_inc() +
             self.body['at_most'].size_inc() +
             self.body['start_by'].size_inc()) <= max_inc,

            # The type of constraints can only be increased by max_inc
            Sum([If(self.body['exactly'].size() > 0, 1, 0),
                 If(self.body['at_most'].size() > 0, 1, 0),
                 If(self.body['start_by'].size() > 0, 1, 0)]) <= n_type + max_inc,

            (self.body['exactly'].size_dec() +
             self.body['at_most'].size_dec() +
             self.body['start_by'].size_dec()) <= max_dec,

            self.properties_for_exactly_most(),
            self.properties_for_exactly_start(),
            self.properties_for_most_start()
        ]
        return And(C)

    def properties_for_most_start(self):
        C = []
        for i, e_var in enumerate(self.vars['most_name']):
            # if exactly_cnt of a block is 0, and this block is not noblock, then cannot start by this block
            C.extend([Implies(And(self.vars['most_cnt'][i] == 0, e_var != noblock),
                              s_var != e_var) for s_var in self.vars['start_name']])

            # if n `block` in exactly constraint, then less than n `block` in start_by constraint
            n = Sum([If(s_var == e_var, 1, 0) for s_var in self.vars['start_name']])
            C.append(Implies(e_var != noblock, n <= self.vars['most_cnt'][i]))
        return And(C)

    def properties_for_exactly_start(self):
        C = []
        for i, e_var in enumerate(self.vars['exactly_name']):
            # if exactly_cnt of a block is 0, and this block is not noblock, then cannot start by this block
            C.extend([Implies(And(self.vars['exactly_cnt'][i] == 0, e_var != noblock),
                              s_var != e_var) for s_var in self.vars['start_name']])

            # if n `block` in exactly constraint, then less than n `block` in start_by constraint
            n = Sum([If(s_var == e_var, 1, 0) for s_var in self.vars['start_name']])
            C.append(Implies(e_var != noblock, n <= self.vars['exactly_cnt'][i]))
        return And(C)

    def properties_for_exactly_most(self):
        C = []
        # the same block cannot co-exist in exactly and most.
        for e_var in self.vars['exactly_name']:
            for m_var in self.vars['most_name']:
                C.append(Implies(And(e_var != noblock, m_var != noblock),
                                 e_var != m_var))
        return And(C)

    def mutate(self):
        self.mutated = True

        self.body['exactly'].mutate()
        self.body['at_most'].mutate()
        self.body['start_by'].mutate()

        # rebuild vars
        self.vars = self._build_vars()

    def to_json(self, model_values):
        cons_json = {
            "exactly" : self.body['exactly'].to_json(model_values),
            "at_most" : self.body['at_most'].to_json(model_values),
            "start_by": self.body['start_by'].to_json(model_values)
        }
        return cons_json

    def model2instance(self, model_values):
        """
        :param model_values: a dict containing the value for each symbol (e.g., {'find_name_0': 10, 'find_color_0': 1})
        """
        sym_value = {}

        for k in model_values.keys():
            if 'name' in k:
                sym_value[k] = [str(v) for v in model_values[k]]
            elif 'cnt' in k:
                sym_value[k] = [v.as_long() for v in model_values[k]]
            else:
                raise ValueError("Model key not recognized.")

        n_exactly = len(sym_value['exactly_name'])
        n_most = len(sym_value['most_name'])
        n_start = len(sym_value['start_name'])

        exactly = {sym_value["exactly_name"][i]: sym_value["exactly_cnt"][i]
                   for i in range(n_exactly) if sym_value["exactly_name"][i] != 'noblock'}
        most = {sym_value["most_name"][i]: sym_value["most_cnt"][i] for i in range(n_most)}
        start = [sym_value["start_name"][i] for i in range(n_start) if sym_value["start_name"][i] != 'noblock']

        code_constraints_json = {
            "exactly" : exactly,
            "at_most" : most,
            "start_by": start
        }

        return CodeConstraints(code_constraints_json)
