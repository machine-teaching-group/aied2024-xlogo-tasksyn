END_BODY = {"type": 'endBody'}  ## No such block. It is written this way to keep block["type"] reference consistent.

FORWARD = {"type": "fd"}
BACKWARD = {"type": "bk"}
TURN_LEFT = {"type": "lt"}
TURN_RIGHT = {"type": "rt"}

SETPC_RED = {"type": "setpc", "value": "red"}
SETPC_BLACK = {"type": "setpc", "value": "black"}
SETPC_BLUE = {"type": "setpc", "value": "blue"}
SETPC_GREEN = {"type": "setpc", "value": "green"}
SETPC_WHITE = {"type": "setpc", "value": "white"}
SETPC_YELLOW = {"type": "setpc", "value": "yellow"}
SETPC_NULL = {"type": "setpc", "value": None}

REPEAT_1 = {"body": [], "times": 1, "type": "repeat"}
REPEAT_2 = {"body": [], "times": 2, "type": "repeat"}
REPEAT_3 = {"body": [], "times": 3, "type": "repeat"}
REPEAT_4 = {"body": [], "times": 4, "type": "repeat"}
REPEAT_5 = {"body": [], "times": 5, "type": "repeat"}
REPEAT_6 = {"body": [], "times": 6, "type": "repeat"}
REPEAT_7 = {"body": [], "times": 7, "type": "repeat"}
REPEAT_8 = {"body": [], "times": 8, "type": "repeat"}
REPEAT_9 = {"body": [], "times": 9, "type": "repeat"}
REPEAT_10 = {"body": [], "times": 10, "type": "repeat"}
REPEAT_11 = {"body": [], "times": 11, "type": "repeat"}
REPEAT_12 = {"body": [], "times": 12, "type": "repeat"}

ACTION_MAP = {
    0 : END_BODY,
    ## Basic Actions
    1 : FORWARD,
    2 : BACKWARD,
    3 : TURN_LEFT,
    4 : TURN_RIGHT,
    ## VARIABLES
    5 : SETPC_RED,
    6 : SETPC_BLUE,
    7 : SETPC_WHITE,
    8 : SETPC_BLACK,
    9 : SETPC_GREEN,
    10: SETPC_YELLOW,
    11: SETPC_NULL,
    ## REPEATs
    12: REPEAT_1,
    13: REPEAT_2,
    14: REPEAT_3,
    15: REPEAT_4,
    16: REPEAT_5,
    17: REPEAT_6,
    18: REPEAT_7,
    19: REPEAT_8,
    20: REPEAT_9,
    21: REPEAT_10,
    22: REPEAT_11,
    23: REPEAT_12,
}

BASIC_ACTIONS = [
    FORWARD,
    BACKWARD,
    TURN_LEFT,
    TURN_RIGHT,
]

SET_VARIABLES = [
    SETPC_RED,
    SETPC_YELLOW,
    SETPC_GREEN,
    SETPC_BLACK,
    SETPC_WHITE,
    SETPC_BLUE,
    SETPC_NULL
]

INTERNAL_ACTIONS = [0]  ## END_BODY doesn't count towards block limit


def get_allowed_actions(end_body_allowed=False,
                        if_allowed=False,
                        ifelse_allowed=False,
                        while_allowed=False,
                        repeat_allowed=False,
                        put_marker_allowed=False, pick_marker_allowed=False):
    bitmap = [0 for _ in ACTION_MAP.keys()]
    for i in range(1, 4):
        bitmap[i] = 1
    if end_body_allowed:
        bitmap[0] = 1
    if pick_marker_allowed:
        bitmap[4] = 1
    if put_marker_allowed:
        bitmap[5] = 1
    if while_allowed:
        for i in range(6, 14):
            bitmap[i] = 1
    if if_allowed:
        for i in range(14, 22):
            bitmap[i] = 1
    if ifelse_allowed:
        for i in range(22, 30):
            bitmap[i] = 1
    if repeat_allowed:
        for i in range(30, 42):
            bitmap[i] = 1

    return bitmap
