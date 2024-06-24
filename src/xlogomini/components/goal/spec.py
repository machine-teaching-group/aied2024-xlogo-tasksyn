from src.xlogomini.utils.enums import *


class Spec(object):
    """
    This module defines the `Spec` class, which represents a specification in Conjunctive Normal Form (CNF).
    """
    def __init__(self, cnf):
        """
        Initializes the `Spec` object with a CNF representation.

        Examples
        --------
        >>> spec_json = [[{"type": "element", "neg": 0}, {"color": "red", "neg": 1}],\
        ...              [{"name": "lemon", "neg": 0}, {"count": "3", "neg": 0}]]
        >>> s = Spec(spec_json)
        >>> s.cnf
        [['element', '-red'], ['lemon', '3']]

        This CNF means: (type='element' ∨ ⌝color='red') ∧ (name='lemon' ∨ count=3)
        """
        self.cnf = cnf

    @classmethod
    def init_from_json(cls, spec_json):
        """
        Class method to initialize a `Spec` object from a JSON representation.

        Parameters:
            spec_json (list): A list of lists representing the CNF clauses.

        Examples:
        --------
        >>> cls.init_from_json([[{"color": "green", "neg": 0}, {"color": "red", "neg": 1}], \
                           [{"name": "lemon", "neg": 0}, {"count": "3", "neg": 0}]])
        [["green", "-red"], ["lemon", "3"]]

        >>> cls.init_from_json([[{"start": 0, "end": 1, "color": "red", "neg": 0}],\
                           [{"start": 2, "end": 3, "color": "blue", "neg": 0}]])
        [["0_1_red"], ["2_3_blue"]]
        """
        cnf = []
        for c in spec_json:
            clause = []
            for l in c:
                neg_prefix = '' if 'neg' not in l.keys() or not l['neg'] else '-'
                # always make sure that start < end, otherwise exchange start and end
                if 'x1' in l.keys():
                    assert 'y1' in l.keys() and 'x2' in l.keys() and 'y2' in l.keys()
                    var_name = f"{neg_prefix}l_{l['x1']}_{l['y1']}_{l['x2']}_{l['y2']}_{COLORS[l['color']]}"
                else:
                    var_name = neg_prefix + '_'.join(map(str, [l[k] for k in l.keys() if k != 'neg']))
                clause.append(var_name)
            cnf.append(clause)
        return cls(cnf)

    def to_json(self):
        """
        Converts the specification to a JSON representation.

        Returns:
            list: A list of lists representing the CNF clauses in JSON format.
        """
        cnf_json = []
        for c in self.cnf:
            clause = []
            for l in c:
                # parse negation
                if l[0] == '~':
                    use_negation = 1
                    l = l[1:]
                else:
                    use_negation = 0

                if l in ITEM_NAME:
                    clause.append({"name": l, "neg": use_negation})
                elif l in ITEM_COLOR:
                    clause.append({"color": l, "neg": use_negation})
                elif l in ITEM_COUNT:
                    clause.append({"count": l, "neg": use_negation})
                else:
                    raise ValueError(f"{l} not recognized")
            cnf_json.append(clause)
        return cnf_json

    def toPytorchTensor(self):
        """
        Converts the specification to a PyTorch tensor.

        Returns:
            torch.Tensor: A tensor representation of the specification.
        """
        import torch as th
        MAX_CLAUSES = 2
        MAX_LITERALS = 2

        feats = ["red", "green", "blue", "yellow", "black", "orange", "purple", "pink", "white",
                 "strawberry", "lemon", "triangle", "rectangle", "cross", "circle"]

        def literal2vec(l):
            vec = [0] * len(feats)
            if l in feats:
                idx = feats.index(l)
                vec[idx] = 1
            return th.Tensor(vec)

        def clause2vec(c):
            vec = []
            for i, l in enumerate(c):
                if i > MAX_LITERALS:
                    break
                vec.append(literal2vec(l))

            # padding for empty literals
            while True:
                if len(vec) < MAX_LITERALS:
                    vec.append(th.zeros_like(vec[0]))
                else:
                    break
            return th.concat(vec).flatten()

        vec = [clause2vec(c) for i, c in enumerate(self.cnf) if i < MAX_CLAUSES]

        # assuming having , add padding
        if len(vec) < MAX_CLAUSES:
            vec.append(th.zeros_like(vec[0]))

        spec_tensor = th.concat(vec).flatten()
        assert spec_tensor.shape[0] == 60
        return spec_tensor

    def __str__(self):
        """
        Returns a human-readable string representation of the specification.

        Returns:
            str: The string representation of the specification.
        """
        and_list = []
        for c in self.cnf:
            and_list.append(' or '.join(c).replace('-', '~'))

        sorted_and_list = []
        for x in and_list:
            if x in NAME_VARS:
                sorted_and_list.append(x)
            else:
                sorted_and_list.insert(0, x)
        spec_str = " ".join(sorted_and_list)
        return spec_str