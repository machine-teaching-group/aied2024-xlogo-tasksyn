REGISTRY = {}

from .find_smt import FindSMT
from .forbid_smt import ForbidSMT
from .collectall_smt import CollectAllSMT
from .sum_smt import SumSMT
from .concat_smt import ConcatSMT
from .draw_smt import DrawSMT

REGISTRY["find"] = FindSMT
REGISTRY["forbid"] = ForbidSMT
REGISTRY["collectall"] = CollectAllSMT
REGISTRY["sum"] = SumSMT
REGISTRY["concat"] = ConcatSMT
REGISTRY["draw"] = DrawSMT
