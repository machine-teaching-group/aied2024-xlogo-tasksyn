from src.xlogomini.smt.code.base_block_smt import *
from src.xlogomini.smt.code.action_smt import ActionSMT
from src.xlogomini.smt.code.setpc_smt import SetPCSMT
from z3 import And, Int, Not, Implies, If, Sum, Const, Or
import random


class BaseRecursiveBlockSMT():
    def __init__(self, body_js, id):
        self.body_js = body_js  # a list of blocks
        self.id = id

        self.body = self._build_body()
        self.old_body = self.body
        self.vars = self._build_vars()

        self.mutated = False

    def _build_body(self):
        import xlogomini.smt.code.repeat_smt as repeat_smt  # Move import here
        body = []
        for i, block_js in enumerate(self.body_js):
            if block_js['type'] in ['fd', 'bk', 'lt', 'rt']:
                body.append(ActionSMT(block_js, f"{self.id}_{i}"))
            elif block_js['type'] in ['setpc']:
                body.append(SetPCSMT(block_js, f"{self.id}_{i}"))
            elif block_js['type'] in ['repeat']:
                body.append(repeat_smt.RepeatSMT(block_js, f"{self.id}_{i}"))
            else:
                raise ValueError(f"{block_js['type']} not recognized")
        return body

    def _build_vars(self):
        pass

    def get_body_vars(self):
        vars = {}
        for block in self.body:
            vars.update(block.vars)
        return vars

    def properties_for_body(self,
                            rows, cols,
                            max_code_inc,
                            max_code_dec,
                            exact_code_inc,
                            max_rep_times_inc,
                            max_rep_times_dec):
        import xlogomini.smt.code.repeat_smt as repeat_smt  # Move import here
        C = []
        for b in self.body:
            if isinstance(b, ActionSMT):
                C.append(b.properties())
            elif isinstance(b, SetPCSMT):
                C.append(b.properties())
            elif isinstance(b, repeat_smt.RepeatSMT):
                C.append(b.properties(rows=rows, cols=cols,
                                      max_code_inc=max_code_inc,
                                      max_code_dec=max_code_dec,
                                      exact_code_inc=exact_code_inc,
                                      max_rep_times_inc=max_rep_times_inc,
                                      max_rep_times_dec=max_rep_times_dec))
        return And(C)

    def properties_for_total_blocks(self, max_code_inc, max_code_dec, exact_code_inc=None):
        import xlogomini.smt.code.repeat_smt as repeat_smt  # Move import here
        C = []
        self_cnt = 1 if isinstance(self, repeat_smt.RepeatSMT) else 0
        if exact_code_inc is not None:
            if max_code_inc is not None:
                assert exact_code_inc <= max_code_inc

            C.extend([
                # exactly n blocks increased
                self.total_block_cnt(mutated=True) == self.total_block_cnt(mutated=False) + exact_code_inc
            ])
        else:
            C.extend([
                self.total_block_cnt(mutated=True) >= max(self.total_block_cnt(mutated=False) - max_code_dec,
                                                          1 + self_cnt),
                # at most n+2 blocks
                self.total_block_cnt(mutated=True) <= self.total_block_cnt(mutated=False) + max_code_inc
            ])
        return And(C)

    def properties_for_disabling_pattern(self, body, pattern, consider_proceeding_nulls=False):
        """
        Disable the appearance of `patter` in the `body`.

        Note: not work when len(pattern) == 1 at the first time
        """
        body_vars = [body[i].vars[f'block__{body[i].id}'] for i in range(len(body))]

        if len(body_vars) < len(pattern):
            return True

        if len(body_vars) == 0 or len(pattern) == 0:
            return True

        if len(body_vars) == 1 and len(pattern) == 1:
            return body_vars[0] != pattern[0]

        elif len(body_vars) > 1 and len(pattern) == 1:
            C = []
            for i in range(len(body_vars)):
                C.append(Implies(body_vars[i] == pattern[0],
                                 Or([And(var != noblock, var != pattern[0]) for var in body_vars[:i]])))
            return And(C)

        elif len(body_vars) == 1 and len(pattern) > 1:
            return True

        elif len(body_vars) > 1 and len(pattern) > 1:
            C = []
            sliding_size = 3
            for i in range(len(body_vars)):
                # only consider the proceeding nulls for the recursive calls
                if consider_proceeding_nulls:
                    # condition for "all blocks before index i are noblock"
                    all_pre_i_is_noblock = And([var == noblock for var in body_vars[:i]])
                    C.append(Implies(And(body_vars[i] == pattern[0],
                                         all_pre_i_is_noblock),
                                     self.properties_for_disabling_pattern(
                                         body[i + 1: i + 1 + len(pattern) + sliding_size],
                                         pattern=pattern[1:],
                                         consider_proceeding_nulls=True)))
                else:
                    C.append(Implies(body_vars[i] == pattern[0], self.properties_for_disabling_pattern(
                        body[i + 1: i + 1 + len(pattern) + sliding_size],
                        pattern=pattern[1:], consider_proceeding_nulls=True)))
            return And(C)

    def properties_for_keeping_repeat_body_same(self):
        import xlogomini.smt.code.repeat_smt as repeat_smt  # Move import here
        C = []

        def two_repeats_the_same_smt(rep1, rep2):
            """
            Set up the constraints for two Repeat objects to be the same in terms of their SMT representation.

            The two Repeat objects are considered the same if their blocks' SMT representations are equal.

            Parameters:
            - rep1 (Repeat): The first Repeat object to compare.
            - rep2 (Repeat): The second Repeat object to compare.

            Returns:
            - z3.ExprRef: An SMT expression that represents the equality constraint of the two Repeat objects.
            """
            C = []
            for i in range(len(rep1.body)):
                b1, b2 = rep1.body[i], rep2.body[i]
                C.append(b1.vars[f'block__{b1.id}'] == b2.vars[f'block__{b2.id}'])
            return And(C)

        # all repeat blocks
        reps = [block for block in self.body if isinstance(block, repeat_smt.RepeatSMT)]

        # only 1 repeat inside, return
        if len(reps) <= 1:
            return True

        # more than 1 repeats
        # then check if each two pair of repeats are the same
        for i in range(len(reps)):
            for j in range(i + 1, len(reps)):
                if reps[i] == reps[j]:  # if the body are the same
                    C.append(two_repeats_the_same_smt(reps[i], reps[j]))
                # if the `times` is the same, then also add this constraint
                if reps[i].js['times'] == reps[j].js['times']:
                    C.append(reps[i].vars[f'times__{reps[i].id}'] == reps[j].vars[f'times__{reps[j].id}'])
        return And(C)

    def mutate(self, n_blks_insert_hetero, n_blks_insert_homog, prob_insert_rep):
        import xlogomini.smt.code.repeat_smt as repeat_smt  # Move import here
        def sample_n_blocks(block_id, cnt, repeat_prob, n):
            blocks = []
            for k in range(n):
                rand = random.random()
                if rand < repeat_prob:
                    blocks.append(repeat_smt.RepeatSMT.new_random_repeat(f"{block_id}_i{cnt + k}"))
                else:
                    blocks.append(ActionSMT(None, f"{block_id}_i{cnt + k}"))
            return blocks

        self.mutated = True  # set the flag
        self.old_body = self.body  # save old body

        cnt = 0

        # add n_blks_insert_hetero blocks af the beginning
        mutated_body = sample_n_blocks(self.id, cnt, prob_insert_rep, n_blks_insert_hetero)
        cnt += n_blks_insert_hetero

        ext_body = [*self.body, None]  # add one extra block for convenience (won't take effect)

        for i in range(len(ext_body) - 1):
            mutated_body.append(ext_body[i])
            # heterogeneous
            if isinstance(ext_body[i], repeat_smt.RepeatSMT) \
                    or isinstance(ext_body[i + 1], repeat_smt.RepeatSMT) \
                    or ext_body[i + 1] is None:
                mutated_body.extend(sample_n_blocks(self.id, cnt, prob_insert_rep, n_blks_insert_hetero))
                cnt += n_blks_insert_hetero
            # homogeneous
            else:
                mutated_body.extend(sample_n_blocks(self.id, cnt, prob_insert_rep, n_blks_insert_homog))
                cnt += n_blks_insert_homog

        # mutate repeat block
        for i in range(len(mutated_body)):
            if isinstance(mutated_body[i], repeat_smt.RepeatSMT):
                mutated_body[i].mutate(n_blks_insert_hetero,
                                       n_blks_insert_homog,
                                       prob_insert_rep=0)  # don't allow to be repeat inside repeat
        self.body = mutated_body
        self.vars = self._build_vars()

    def properties_for_exclusive_colors(self):
        import xlogomini.smt.code.setpc_smt as setpc_smt  # Move import here
        """
        Exclusive colors are those color which are hard to distinguish if they exist together.
        E.g., blue and black are exclusive.
        """
        setpc_blks = [blk for blk in self.body if isinstance(blk, SetPCSMT)]

        BLUE_EXISTS = Or([blk.vars[f'value__{blk.id}'] == blue for blk in setpc_blks])
        BLACK_EXISTS = Or([blk.vars[f'value__{blk.id}'] == black for blk in setpc_blks])

        C = [
            Implies(BLUE_EXISTS, Not(BLACK_EXISTS)),
            Implies(BLACK_EXISTS, Not(BLUE_EXISTS))
        ]

        return And(C)

    def properties_for_pen_colors(self):
        import xlogomini.smt.code.setpc_smt as setpc_smt  # Move import here
        """
        Don't allow the pen colors to be the same for two adjacent setpc blocks
        """
        C = []
        setpc_blks = [blk for blk in self.body if isinstance(blk, SetPCSMT)]
        for i in range(len(setpc_blks)):
            for j in range(i + 1, len(setpc_blks)):
                blk_i, blk_j = setpc_blks[i], setpc_blks[j]

                BLK_I_SETPC = blk_i.vars[f'block__{blk_i.id}'] == setpc
                BLK_J_SETPC = blk_j.vars[f'block__{blk_j.id}'] == setpc

                BLK_I_COLOR = blk_i.vars[f'value__{blk_i.id}']
                BLK_J_COLOR = blk_j.vars[f'value__{blk_j.id}']

                NO_SETPC_BETWEEN_I_J = And([blk.vars[f'block__{blk.id}'] != setpc for blk in setpc_blks[i + 1:j]])

                C.append(Implies(And(BLK_I_SETPC, BLK_J_SETPC, NO_SETPC_BETWEEN_I_J),
                                 BLK_I_COLOR != BLK_J_COLOR))
        return And(C)

    def the_same_body(self, body1, body2):
        C = []
        body1 = [body1[i].vars[f'block__{body1[i].id}'] for i in range(len(body1))]
        body2 = [body2[i].vars[f'block__{body2[i].id}'] for i in range(len(body2))]

        for i in range(len(body1)):
            for j in range(len(body2)):
                N_NOT_NOBLOCKS_BEFORE_I = Sum([If(b != noblock, 1, 0) for b in body1[:i]])
                N_NOT_NOBLOCKS_BEFORE_J = Sum([If(b != noblock, 1, 0) for b in body2[:j]])
                C.append(
                    Implies(And(body1[i] != noblock,
                                body2[j] != noblock,
                                N_NOT_NOBLOCKS_BEFORE_I == N_NOT_NOBLOCKS_BEFORE_J
                                ),
                            body1[i] == body2[j])
                )
        C.append(Sum([If(b != noblock, 1, 0) for b in body1]) == Sum([If(b != noblock, 1, 0) for b in body2]))
        return And(C)

    def properties_for_merging_repeat(self):
        import xlogomini.smt.code.repeat_smt as repeat_smt  # Move import here
        C = []
        # prevent the pattern like: bk, repeat(n){bk}
        for i, blk in enumerate(self.body):
            if isinstance(blk, repeat_smt.RepeatSMT):
                for j in range(i + 2, len(self.body) + 1):
                    C.append(Not(self.the_same_body(blk.body, self.body[i + 1: j])))
                for j in range(0, i):
                    C.append(Not(self.the_same_body(blk.body, self.body[j:i])))
        return And(C)

    def properties_for_last_nth_block(self, n, block):
        """
        The last n-th block must the given `block`. `n` starts from 1.
        """
        assert n > 0
        C = []
        for i in range(len(self.body)):
            BLKS_ARE_NONE_AFTER_I = Sum([smt.vars[f'block__{smt.id}'] != noblock for smt in self.body[i + 1:]]) == n - 1
            BLK_I_NOT_NONE = self.body[i].vars[f'block__{self.body[i].id}'] != noblock
            BLK_I_IS_BLOCK = self.body[i].vars[f'block__{self.body[i].id}'] == block
            C.append(Implies(And(BLKS_ARE_NONE_AFTER_I, BLK_I_NOT_NONE),
                             BLK_I_IS_BLOCK))
        return And(C)

    def properties_for_nth_block(self, n, block):
        """
        The first n-th block must the given `block`. `n` starts from 1.
        """
        assert n > 0
        C = []
        for i in range(len(self.body)):
            BLKS_ARE_NONE_BEFORE_I = Sum([smt.vars[f'block__{smt.id}'] != noblock for smt in self.body[:i]]) == n - 1
            BLK_I_NOT_NONE = self.body[i].vars[f'block__{self.body[i].id}'] != noblock
            BLK_I_IS_BLOCK = self.body[i].vars[f'block__{self.body[i].id}'] == block
            C.append(Implies(And(BLKS_ARE_NONE_BEFORE_I, BLK_I_NOT_NONE),
                             BLK_I_IS_BLOCK))
        return And(C)

    def total_block_cnt(self, mutated):
        pass

    def __len__(self):
        return sum([len(x) for x in self.body])

    def to_json(self, model_values):
        pass
