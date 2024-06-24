from z3 import EnumSort

MATRIX_DIMENSIONS = 4
MAX_API_CALLS = 1e5
CRASHED_MSG = {
    "WALL"            : "WALL",
    "FORBIDDEN_AREA"  : "FORBIDDEN_AREA",
    "OUT_OF_WORLD"    : "OUT_OF_WORLD",
    "EXCEED_MAX_CALLS": "EXCEED_MAX_CALLS",
    "GRID_NOT_EXIST"  : "GRID_NOT_EXIST",
}

# turtle direction
DEG_MAP = {
    0: 'NORTH',
    1: 'EAST',
    2: 'SOUTH',
    3: 'WEST'
}
ITEM_UNICODE = {
    # https://www.fileformat.info/index.htm
    'turtle'    : u"\U0001F422",
    'strawberry': '\U0001F353',
    'lemon'     : '\U0001F34B',
    'rectangle' : u"\u25FC",
    'circle'    : u"\u25CF",
    'triangle'  : u"\u25B2",
    'cross'     : u"\u271A",
    'forbid'    : u"\u2A2F",
    'west'      : u"\u2190",
    'north'     : u"\u2191",
    'east'      : u"\u2192",
    'south'     : u"\u2193",

}

# Hex Colors for line
COLORS = {
    '#009624': 'green',
    '#0D47A1': 'blue',
    '#D60000': 'red',
    '#000000': 'black',
    '#FFD600': 'yellow',
    '#FFFFFF': 'white',
    'green'  : '#009624',
    'blue'   : '#0D47A1',
    'red'    : '#D60000',
    'black'  : '#000000',
    'yellow' : '#FFD600',
    'white'  : '#FFFFFF'
}

TCOLORS = {
    'black' : '\033[30m',
    "red"   : '\033[31m',
    "green" : '\033[32m',
    "yellow": '\033[33m',
    "blue"  : '\033[34m',
    "white" : '\033[37m',
    "end"   : '\033[0m',
}

XLOGO_CHAPS = {
    '1' : ["1", "2", "3", "4", "5", "6", "7", "8", "9a", "9b"],
    '2' : ["10a", "10b", "11", "12a", "12b", "13", "14", "15", "16", "17a", "17b", "18a", "18b", "19"],
    '3' : ["20", "21", "22", "23", "24", "25", "26", "27", "28", "29"],
    '4' : ["30", "31", "32", "33", "34", "35", "36", "37", "38", "39"],
    '5' : ["40a", "40b", "40c", "41", "42", "43", "44", "45", "46", "47"],
    '6' : ["50", "51", "52", "53", "54", "55", "56", "57", "58", "59"],
    '7' : ["60", "61", "62", "63", "64", "65", "66", "67"],
    '8' : ["70", "71", "72", "73"],
    '9' : ["80", "81", "82", "83", "84", "85", "86", "87"],
    '10': ["90", "91", "92", "93", "94"],
    '11': ["100", "101", "102", "103", "104", "105"],
    '12': ["110", "111", "112", "113", "114", "115", "116"],
    '13': ["120a", "120b", "120c", "121a", "121b", "121c", "122a", "122b", "122c", "123a", "123b"],
}

# all task ids except chapter 5, 12 and 13
XLOGO_TASK_IDS = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9a", "9b",
    "10a", "10b", "11", "12a", "12b", "13", "14", "15", "16", "17a", "17b", "18a", "18b", "19",
    "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
    "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    # "40a", "40b", "40c", "41", "42", "43", "44", "45", "46", "47",
    "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "60", "61", "62", "63", "64", "65", "66", "67",
    "70", "71", "72", "73",
    "80", "81", "82", "83", "84", "85", "86", "87",
    "90", "91", "92", "93", "94",
    "100", "101", "102", "103", "104", "105"
]

# XLOGO_ITEM_CHAPS = {
#     '1': ["1", "2", "3", "4", "5", "6", "7", "8", "9a", "9b"],
#     '2': ["10a", "10b", "11", "12a", "12b", "13", "14", "15", "16", "17a", "17b", "18a", "18b", "19"],
#     '3': ["20", "21", "22", "23", "24", "25", "26", "27", "28", "29"],
#     '4': ["30", "31", "32", "33", "34", "35", "36", "37", "38", "39"],
#     '5': ["40a", "40b", "40c", "41", "42", "43", "44", "45", "46", "47"],
#     '9': ["80", "81", "82", "83", "84", "85", "86", "87"],
# }
#
# XLOGO_DRAW_CHAPS = {
#     '6' : ["50", "51", "52", "53", "54", "55", "56", "57", "58", "59"],
#     '7' : ["60", "61", "62", "63", "64", "65", "66", "67"],
#     '8' : ["70", "71", "72", "73"],
#     '10': ["90", "91", "92", "93", "94"],
#     '11': ["100", "101", "102", "103", "104", "105"],
# }
#
# XLOGO_ITEM_TASKS = set([task_id for _, v in XLOGO_ITEM_CHAPS.items() for task_id in v])
# XLOGO_DRAW_TASKS = set([task_id for _, v in XLOGO_DRAW_CHAPS.items() for task_id in v])

# ITEM
ITEM_COLOR = {"red", "blue", "yellow", "green", "black", "orange", "purple", "pink"}
ITEM_FRUIT = {"strawberry", "lemon"}
ITEM_SHAPE = {"triangle", "rectangle", "cross", "circle"}
ITEM_CHAR = {"A", "B", "C", "D", "E", "F", "G", "H", "I",
             "J", "K", "L", "M", "N", "O", "P", "Q", "R",
             "S", "T", "U", "V", "W", "X", "Y", "Z"}
ITEM_NAME = ITEM_FRUIT.union(ITEM_SHAPE).union(ITEM_CHAR)
ITEM_COUNT = {1, 2, 3, 4}
ITEM_TYPE = {'fruit', 'shape', 'char', 'marker'}

# vars for item
COLOR_VARS = ITEM_COLOR.union({'nocolor'})  # color
COUNT_VARS = ITEM_COUNT.union({0})  # count
NAME_VARS = ITEM_FRUIT.union(ITEM_CHAR).union(ITEM_SHAPE).union({'noname'})  # name
FRUIT_VARS = ITEM_FRUIT  # fruit
SHAPE_VARS = ITEM_SHAPE  # shape
CHAR_VARS = ITEM_CHAR  # char
# vars for turtle
TURTLE_POS_VARS = {'turtle'}
TURTLE_DIR_VARS = {'north', 'south', 'east', 'west'}
# vars for tile
TILE_VARS = {'allowed', 'top', 'right', 'bottom', 'left'}

# vars for marker color
MarkerColor, (red, green, blue, black, white, yellow, nocolor) = EnumSort('MarkerColor', (
    'red', 'green', 'blue', 'black', 'white', 'yellow', 'nocolor'))
MARKER_COLORS = {
    'red'    : red,
    'green'  : green,
    'blue'   : blue,
    'black'  : black,
    'white'  : white,
    'yellow' : yellow,
    'nocolor': nocolor
}
