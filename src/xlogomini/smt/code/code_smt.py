from z3 import *
from src.xlogomini.smt.code.repeat_smt import *


class CodeSMT(BaseRecursiveBlockSMT):
    def __init__(self, js):
        BaseRecursiveBlockSMT.__init__(self, body_js=js['run'], id="")
        self.js = js
        self.vars = self._build_vars()

    def _build_vars(self):
        vars = self.get_body_vars()
        return vars

    def properties(self, rows, cols,
                   max_code_inc, max_code_dec,  # blocks added or removed globally
                   exact_code_inc,
                   max_rep_body_inc, max_rep_body_dec,  # n blocks added or removed inside repeat
                   max_rep_times_inc, max_rep_times_dec):  #
        C = [
            self.properties_for_body(rows=rows,
                                     cols=cols,
                                     max_code_inc=max_rep_body_inc,
                                     max_code_dec=max_rep_body_dec,
                                     exact_code_inc=None,  # used by repeat if exists
                                     max_rep_times_inc=max_rep_times_inc,
                                     max_rep_times_dec=max_rep_times_dec),
            self.properties_for_total_blocks(max_code_inc=max_code_inc,
                                             max_code_dec=max_code_dec,
                                             exact_code_inc=exact_code_inc),
            self.properties_for_keeping_repeat_body_same(),

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

            # use at least one `fd` or `bk`
            # self.target_block_cnt(fd) + self.target_block_cnt(bk) > 0,
            # lt/rt cannot be the last block of the code
            Not(self.properties_for_last_nth_block(1, rt)),
            Not(self.properties_for_last_nth_block(1, lt)),

            self.properties_for_pen_colors(),

            # don't allow 'blue' and 'black' to co-exist
            self.properties_for_exclusive_colors(),

            # prevent the pattern like: bk, repeat(n){bk}
            self.properties_for_merging_repeat()
        ]
        return simplify(And(C))

    def target_block_cnt(self, block, mutated):
        if mutated:
            return Sum([smt.target_block_cnt(block, mutated) for smt in self.body])
        else:
            return Sum([smt.target_block_cnt(block, mutated) for smt in self.old_body])

    def total_block_cnt(self, mutated):
        """
        Return a smt formula that represents the number of total block.
        """
        if mutated:
            cnt_list = [smt.total_block_cnt(mutated=True) for smt in self.body]
        else:
            cnt_list = [smt.total_block_cnt(mutated=False) for smt in self.old_body]
        return Sum(cnt_list)

    def to_json(self, models_values, with_run=False):
        code_json = []
        for smt in self.body:
            block_js = smt.to_json(models_values)
            if block_js is not None:
                code_json.append(block_js)
        if with_run:
            return {"run": code_json}
        return code_json
