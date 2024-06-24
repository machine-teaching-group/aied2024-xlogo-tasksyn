from z3 import And, Or, simplify, AtLeast, AtMost, Not
from src.xlogomini.utils.enums import *
from src.xlogomini.utils.helpers import get_neighboring_ids


def exactly_one(vars):
    return simplify(And(AtLeast(*vars, 1), AtMost(*vars, 1)))


def Equals(var_list):
    """
    Return an equality expression for all variables in var_list.
    """
    constr = True
    if var_list:
        base = var_list[0]
        for x in var_list[1:]:
            constr = And(constr, base == x)
    return constr


def exactly_the_same(A, B):
    C = []
    for k in A.keys():
        if isinstance(A[k], list):
            C.extend([A[k][i] == B[k][i] for i in range(len(A[k]))])
        elif isinstance(B[k], list):
            C.extend([A[k][i] == B[k][i] for i in range(len(B[k]))])
        else:
            C.append(A[k] == B[k])
    return And(C)


def model2values(vars, model):
    model_values = {}
    for k in vars.keys():
        if isinstance(vars[k], list):
            model_values[k] = [model.eval(var, model_completion=True) for var in vars[k]]
        else:
            model_values[k] = model.eval(vars[k], model_completion=True)
    return model_values


def cnf_formula(vars, cnf, locs, operator='or', n=None):
    """
    Return the SMT formula for the given locations.

    Examples
    --------
    >>> cnf
    [['red', 'blue'], ['-lemon'], ['orange']]
    >>> cnf_formula([1,2], 'or')
    Or(And(Or(x_1_blue, x_1_red), Not(x_1_lemon), x_1_orange),
       And(Or(x_2_red, x_2_blue), Not(x_2_lemon), x_2_orange))
    """
    locs = [locs] if isinstance(locs, int) else locs
    loc_list = []
    for loc in locs:
        and_list = []
        for clause in cnf:
            and_list.append(clause_formula(vars, clause, loc))
        loc_list.append(And(and_list))

    if operator == 'or':
        return simplify(Or(loc_list))
    elif operator == 'and':
        return simplify(And(loc_list))
    elif operator == 'exactly_one':
        return simplify(exactly_one(loc_list))
    elif operator == 'at_least':
        assert n is not None
        return simplify(AtLeast(*loc_list, n))
    else:
        raise ValueError(f"{operator} not recognized")


def clause_formula(vars, clause, loc):
    """
    Return the SMT formula for the given clause at the location.

    Examples:
    --------
    >>> clause_formula(['red', 'green'], 3)
    Or(x_3_red, x_3_green)
    >>> clause_formula(vars, ['red', '-green', 'black'], 3)
    Or(x_5_red, x_5_black, Not(x_5_green))
    """
    or_list = []
    for l in clause:

        if l[0] == '~':
            use_negation = True
            l = l[1:]
        else:
            use_negation = False

        if l in COUNT_VARS:  # count
            if use_negation:
                or_list.append(Not(vars['count'][loc] == int(l)))
            else:
                or_list.append(vars['count'][loc] == int(l))
        else:
            if use_negation:
                or_list.append(Not(vars[l][loc]))
            else:
                or_list.append(vars[l][loc])

    return simplify(Or(or_list))


def wall_vars_along_the_path(vars, rows, cols, path):
    path_walls = []
    for i in range(len(path) - 1):
        ids = get_neighboring_ids(path[i], rows, cols)
        if ids['top'] == path[i + 1]:
            path_walls.append(vars['topW'][path[i]])
            path_walls.append(vars['bottomW'][path[i + 1]])
        elif ids['left'] == path[i + 1]:
            path_walls.append(vars['leftW'][path[i]])
            path_walls.append(vars['rightW'][path[i + 1]])
        elif ids['right'] == path[i + 1]:
            path_walls.append(vars['rightW'][path[i]])
            path_walls.append(vars['leftW'][path[i + 1]])
        elif ids['bottom'] == path[i + 1]:
            path_walls.append(vars['bottomW'][path[i]])
            path_walls.append(vars['topW'][path[i + 1]])
        else:
            raise ValueError(f"Node {path[i]} and {path[i + 1]} are not adjacent")
    return path_walls


def is_standalone_wall(vars, rows, cols, wall_id):
    """
    Return the smt formula representing if the {position} wall at position i is a standalone wall.
    """
    position, i = str(wall_id).split('__')
    position = position[:-1]
    i = int(i)
    assert position == 'left' or position == 'right' or position == 'top' or position == 'bottom'

    # get all neighbors
    neighbors = get_neighboring_ids(i, rows, cols)

    if position == 'top':
        if neighbors['top'] is not None:
            return And(vars['allowed'][i],
                       vars['allowed'][neighbors['top']],
                       vars[f'{position}W'][i])
    elif position == 'left':
        if neighbors['left']:
            return And(vars['allowed'][i],
                       vars['allowed'][neighbors['left']],
                       vars[f'{position}W'][i])
    elif position == 'right':
        if neighbors['right']:
            return And(vars['allowed'][i],
                       vars['allowed'][neighbors['right']],
                       vars[f'{position}W'][i])
    elif position == 'bottom':
        if neighbors['bottom']:
            return And(vars['allowed'][i],
                       vars['allowed'][neighbors['bottom']],
                       vars[f'{position}W'][i])
    return False
