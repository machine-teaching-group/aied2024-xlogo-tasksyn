from src.xlogomini.smt.code.base_block_smt import *
from z3 import And, Int, If, Sum, Const, Implies, Or, Not
from src.xlogomini.smt.code.base_recursive_block_smt import BaseRecursiveBlockSMT


class RepeatSMT(BaseRecursiveBlockSMT):
    def __init__(self, js, id):
        BaseRecursiveBlockSMT.__init__(self, js['body'], id)
        self.js = js
        self.vars = self._build_vars()

    @classmethod
    def new_random_repeat(cls, id):
        js = {"type": "repeat", "times": 2, "body": [{"type": "fd"}]}
        return cls(js, id)

    def _build_vars(self):
        vars = {}
        vars[f'block__{self.id}'] = Const(f'block__{self.id}', Block)
        vars[f'times__{self.id}'] = Int(f"times__{self.id}")
        vars.update(self.get_body_vars())
        return vars

    def properties(self,
                   rows, cols,
                   max_code_inc,
                   max_code_dec,
                   exact_code_inc,
                   max_rep_times_inc,
                   max_rep_times_dec):
        C = []

        C.extend([
            self.vars[f'block__{self.id}'] == repeat,

            # range for times
            And(self.vars[f'times__{self.id}'] >= max(self.js['times'] - max_rep_times_dec, 2),
                self.vars[f'times__{self.id}'] <= self.js['times'] + max_rep_times_inc),
            self.properties_for_keeping_repeat_body_same(),
            self.properties_for_body(rows, cols,
                                     max_code_inc=max_code_inc,
                                     max_code_dec=max_code_dec,
                                     exact_code_inc=exact_code_inc,
                                     max_rep_times_inc=max_rep_times_inc,
                                     max_rep_times_dec=max_rep_times_dec),
            self.properties_for_total_blocks(max_code_inc=max_code_inc,
                                             max_code_dec=max_code_dec,
                                             exact_code_inc=exact_code_inc),
            self.properties_for_disabling_pattern(self.body, [lt, lt, lt]),
            self.properties_for_disabling_pattern(self.body, [rt, rt, rt]),

            self.properties_for_disabling_pattern(self.body, [fd for _ in range(max(rows, cols))]),
            self.properties_for_disabling_pattern(self.body, [bk for _ in range(max(rows, cols))]),

            self.properties_for_disabling_pattern(self.body, [lt, rt]),
            self.properties_for_disabling_pattern(self.body, [rt, lt]),

            self.properties_for_disabling_pattern(self.body, [fd, bk, fd]),
            self.properties_for_disabling_pattern(self.body, [bk, fd, bk]),

            self.properties_for_disabling_pattern(self.body, [rt, rt, fd]),
            self.properties_for_disabling_pattern(self.body, [rt, rt, bk]),
            self.properties_for_disabling_pattern(self.body, [lt, lt, fd]),
            self.properties_for_disabling_pattern(self.body, [lt, lt, bk]),

            self.properties_for_disabling_pattern(self.body, [fd, rt, rt]),
            self.properties_for_disabling_pattern(self.body, [fd, lt, lt]),
            self.properties_for_disabling_pattern(self.body, [bk, rt, rt]),
            self.properties_for_disabling_pattern(self.body, [bk, lt, lt]),
            # self.properties_for_disabling_pattern(self.body, [fd, bk]),  # only forbidden in repeat
            # self.properties_for_disabling_pattern(self.body, [bk, fd]),  # only forbidden in repeat

            # don't allow turns (e.g., lt/rt) to appear at the first and the last together
            Not(And(
                Or(self.properties_for_nth_block(1, lt),
                   self.properties_for_nth_block(1, rt)),
                Or(self.properties_for_last_nth_block(1, lt),
                   self.properties_for_last_nth_block(1, rt)),
            )),

            self.properties_for_pen_colors(),

            # don't allow 'blue' and 'black' to co-exist
            self.properties_for_exclusive_colors(),

            # prevent the pattern like: bk, repeat(n){bk}
            self.properties_for_merging_repeat(),

            self.properties_for_disabling_only_fd_bk_inside_repeat()
        ])
        return And(C)

    def properties_for_disabling_only_fd_bk_inside_repeat(self):
        """
        Disable the code like:
        repeat(n){fd}
        repeat(n){bk}
        repeat(n){fd, bk}
        repeat(n){bk, fd}
        """
        body = [self.body[i].vars[f'block__{self.body[i].id}'] for i in range(len(self.body))]

        n_fd = Sum([If(b == fd, 1, 0) for b in body])
        n_bk = Sum([If(b == bk, 1, 0) for b in body])
        n_noblock = Sum([If(b == noblock, 1, 0) for b in body])

        # only 1 fd, 1 fd and all others are noblock
        ONLY_FD_BK = And(n_fd == 1,
                         n_bk == 1,
                         n_fd + n_bk + n_noblock == len(body))
        # disable repeat(n){fd, fd}
        ONLY_FD = And(n_fd > 1, n_fd + n_noblock == len(body))
        # disable repeat(n){bk, bk}
        ONLY_BK = And(n_bk > 1, n_bk + n_noblock == len(body))
        return Not(Or(ONLY_FD_BK, ONLY_FD, ONLY_BK))

    def target_block_cnt(self, block, mutated):
        """
        Return a smt formula that represents the number of `block`.
        """
        if mutated:
            tar_block = [1 if block == repeat else 0]
            for smt in self.body:
                tar_block.append(smt.target_block_cnt(block, mutated))
            return Sum(tar_block)
        else:
            tar_block = [1 if str(block) == self.js['type'] else 0]
            for smt in self.old_body:
                tar_block.append(smt.target_block_cnt(block, mutated))
            return sum(tar_block)

    def total_block_cnt(self, mutated):
        """
        Return a smt formula that represents the number of total block.
        """
        if mutated:
            # current block (i.e., repeat)
            total_block = [If(self.vars[f'block__{self.id}'] != noblock, 1, 0)]
            # blocks inside repeat
            for smt in self.body:
                total_block.append(smt.total_block_cnt(mutated))
            return Sum(total_block)
        else:
            # current block (i.e., repeat)
            total_block = [1]
            # blocks inside repeat
            for smt in self.old_body:
                total_block.append(smt.total_block_cnt(mutated))
            return Sum(total_block)

    def to_json(self, model_values):
        js = {
            "type" : 'repeat',
            "times": model_values[str(self.vars[f'times__{self.id}'])].as_long(),
            "body" : [x.to_json(model_values) for x in self.body if x.to_json(model_values) is not None]
        }
        return js

    def __eq__(self, other):
        """
        Check if two RepeatSMT objects are equal.

        Two RepeatSMT objects are considered equal if they have the same items in their body_js attribute in the same order.

        Parameters:
        - other (RepeatSMT or any): The object to compare to self.

        Returns:
        - bool: True if both objects are equal, False otherwise.
        """
        if isinstance(other, RepeatSMT):
            all_self_items_in_other = all(item in other.body_js for item in self.body_js)
            all_other_items_in_self = all(item in self.body_js for item in other.body_js)
            return all_self_items_in_other and all_other_items_in_self
        else:
            return False
