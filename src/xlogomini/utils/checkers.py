from src.xlogomini.utils.helpers import yx2i
from z3 import And, Solver, Bool, sat
from src.xlogomini.smt.world.item_smt import ItemSMT
from src.xlogomini.smt.goal.goal_smt import GoalSMT


def check_goal(goal, inp_world, out_world):
    """
    Return True if all objs are satisfied.
    """
    rows = inp_world.rows
    cols = inp_world.cols
    ntiles = rows * cols

    items = inp_world.items
    markers = inp_world.markers
    visited = out_world.trace
    drawn_markers = out_world.drawn_markers

    # check markers
    if 'draw' in goal.objs.keys():
        return markers == drawn_markers
    else:
        item_smt = ItemSMT(rows, cols)
        goal_smt = GoalSMT(rows, cols, item_smt.vars, goal, visited)

        # use SMT solver to check the items
        solver = Solver()
        solver.add(item_smt.properties())
        solver.add(goal_smt.properties_for_emulator())

        model_values = {}
        for y in range(rows):
            for x in range(cols):
                i = yx2i(y, x, cols)
                color = 'nocolor' if items[y, x] is None else items[y, x].color
                name = 'noname' if items[y, x] is None else items[y, x].name
                count = 0 if items[y, x] is None else int(items[y, x].count)

                if color not in model_values.keys():
                    model_values[color] = [None] * ntiles
                if name not in model_values.keys():
                    model_values[name] = [None] * ntiles
                if 'count' not in model_values.keys():
                    model_values['count'] = [None] * ntiles

                model_values[color][i] = True
                model_values['count'][i] = count
                model_values[name][i] = True

        # check item assumption using SMT solver
        item_asp = Bool('asp')
        solver.add(
            And([item_smt.vars[k][i] == model_values[k][i]
                 for k in model_values.keys()
                 for i in range(len(model_values[k]))
                 if model_values[k][i] is not None]) == item_asp)
        return solver.check(item_asp) == sat


def check_code_constraints(code, constraint):
    # check at_most and exactly for used blocks
    for block_name, cnt in code.block_cnt.items():
        if (cnt > constraint.at_most(block_name)) or (cnt < constraint.at_least(block_name)):
            return False

    # check at_most and exactly for 'all'
    if code.n_blocks > constraint.at_most('all') or (code.n_blocks < constraint.at_least('all')):
        return False

    # check start-by
    if len(constraint.start) > 0:
        for i in range(len(constraint.start)):
            if code.astJson['run'][i]['type'] != constraint.start[i]:
                return False
    return True
