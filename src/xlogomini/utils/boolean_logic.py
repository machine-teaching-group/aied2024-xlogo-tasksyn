import copy
from sympy.logic.boolalg import to_dnf, to_cnf, simplify_logic
from sympy import symbols
from sympy.logic.boolalg import And as S_And, Or as S_Or, Not as S_Not


def sym2nf(sym, from_nf, _to_cnf=None):
    def _sym2nf(sym, _to_cnf=None):
        if _to_cnf == True:
            sym = to_cnf(sym)
        elif _to_cnf == False:
            sym = to_dnf(sym)

        if sym.is_symbol:
            return str(sym)
        else:
            and_list = []
            or_list = []
            if str(sym.func) == 'And':
                for c in sym.args:
                    value = _sym2nf(c)
                    and_list.append(value)
                return and_list
            elif str(sym.func) == 'Or':
                for c in sym.args:
                    value = _sym2nf(c)
                    or_list.append(value)
                return or_list
            elif str(sym.func) == 'Not':
                return f'~{sym.args[0]}'
            else:
                ValueError(f'{sym.func} not recognized')

    nf = _sym2nf(sym, _to_cnf)

    if isinstance(nf, str):
        return [[nf]]
    elif isinstance(nf, list) and isinstance(nf[0], str):
        if len(from_nf[0]) == 1:
            return [nf]
        else:
            return [[c] for c in nf]
    else:
        return nf


def nf2sym(nf, from_cnf=True, to_cnf_sym=True):
    syms = {}
    for c in nf:
        for l in c:
            syms[l] = ~symbols(l[1:]) if l[0] == '~' else symbols(l)

    if from_cnf:
        clauses = [S_Or(*list(map(lambda x: syms[x], c))) for c in nf]
        sym = S_And(*clauses)
    else:
        clauses = [S_And(*list(map(lambda x: syms[x], c))) for c in nf]
        sym = S_Or(*clauses)

    if to_cnf_sym:
        return to_cnf(sym)
    else:
        return to_dnf(sym)


def cnf2dnf(cnf):
    return sym2nf(nf2sym(cnf, from_cnf=True), from_nf=cnf, _to_cnf=False)


def dnf2cnf(dnf):
    return sym2nf(nf2sym(dnf, from_cnf=False), from_nf=dnf, _to_cnf=True)


def not_cnf(cnf):
    cnf = copy.deepcopy(cnf)
    for i in range(len(cnf)):
        cnf[i].append('noname')
    not_cnf_sym = to_cnf(~(nf2sym(cnf, from_cnf=True)))
    return sym2nf(not_cnf_sym, from_nf=cnf, _to_cnf=True)
