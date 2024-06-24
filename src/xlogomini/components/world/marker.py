from src.xlogomini.utils.enums import COLORS
from src.xlogomini.utils.enums import TCOLORS
import numpy as np
import pandas as pd


class Marker(object):
    def __init__(self,
                 x=None,
                 y=None,
                 top=None,
                 left=None,
                 right=None,
                 bottom=None,
                 top_color=None,
                 left_color=None,
                 right_color=None,
                 bottom_color=None):
        self.x = x
        self.y = y
        self.top = top
        self.left = left
        self.right = right
        self.bottom = bottom

        self.top_color = top_color
        self.left_color = left_color
        self.right_color = right_color
        self.bottom_color = bottom_color

    def is_empty(self):
        return (not self.top) and (not self.left) and (not self.right) and (not self.bottom)

    def update(self, marker):
        if marker.y is not None and self.y is None:
            self.y = marker.y
        if marker.x is not None and self.x is None:
            self.x = marker.x
        if marker.top is not None:
            self.top = marker.top
            self.top_color = marker.top_color
        if marker.left is not None:
            self.left = marker.left
            self.left_color = marker.left_color
        if marker.right is not None:
            self.right = marker.right
            self.right_color = marker.right_color
        if marker.bottom is not None:
            self.bottom = marker.bottom
            self.bottom_color = marker.bottom_color

    def get_colors(self):
        """
        Return a set of colors used
        """
        colors = set([c for c in [self.top_color,
                                  self.left_color,
                                  self.right_color,
                                  self.bottom_color] if c is not None])
        return colors

    def __eq__(self, other):
        if isinstance(other, Marker):
            if (self.top == other.top) and (
                    self.left == other.left) and (
                    self.right == other.right) and (
                    self.bottom == other.bottom) and (
                    self.top_color == other.top_color) and (
                    self.left_color == other.left_color) and (
                    self.right_color == other.right_color) and (
                    self.bottom_color == other.bottom_color):
                return True
        return False

    def disable_color(self):
        self.top_color = 'black'
        self.left_color = 'black'
        self.right_color = 'black'
        self.bottom_color = 'black'


class MarkerArray():
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.markers = np.array([Marker(y=r, x=c) for r in range(rows) for c in range(cols)]).reshape(rows, cols)

    def is_empty(self):
        all_empty = [self.markers[r, c].is_empty() for r in range(self.rows) for c in range(self.cols)]
        return all(all_empty)

    def update(self, line):
        # convert line into two markers
        m_list = line.to_markers()
        for m in m_list:
            # update marker
            if self.markers[m.y, m.x] is None:
                self.markers[m.y, m.x] = m
            else:
                self.markers[m.y, m.x].update(m)

    def to_json(self):
        lines = []
        for r in range(self.rows):
            for c in range(self.cols):
                if c + 1 < self.cols:
                    if self.markers[r, c].right and self.markers[r, c + 1].left:
                        assert self.markers[r, c].right_color == self.markers[r, c + 1].left_color
                        lines.append({
                            "y1"   : r,
                            "x1"   : c,
                            "y2"   : r,
                            "x2"   : c + 1,
                            "color": COLORS[self.markers[r, c].right_color]
                        })
                if r + 1 < self.rows:
                    if self.markers[r, c].bottom and self.markers[r + 1, c].top:
                        assert self.markers[r, c].bottom_color == self.markers[r + 1, c].top_color
                        lines.append({
                            "y1"   : r,
                            "x1"   : c,
                            "y2"   : r + 1,
                            "x2"   : c,
                            "color": COLORS[self.markers[r, c].bottom_color]
                        })
        return lines

    def get_colors(self):
        colors = set()
        for r in range(self.rows):
            for c in range(self.cols):
                colors.update(self.markers[r, c].get_colors())
        return colors

    def disable_color(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.markers[r, c].disable_color()

    def __getitem__(self, pos):
        # TODO: two params?
        return self.markers[pos]

    def __eq__(self, other):
        if isinstance(other, MarkerArray):
            if all([self.markers[r, c] == other[r, c] for r in range(self.rows) for c in range(self.cols)]):
                return True
        return False

    def __setitem__(self, key, value):
        self.markers[key] = value

    def __repr__(self):
        map_rows, map_cols = 3, 3

        markers_str = np.full((self.rows * map_rows, self.cols * map_cols), f'{TCOLORS["white"]} {TCOLORS["end"]}',
                              dtype=object)
        for y in range(self.rows):
            for x in range(self.cols):
                x_ = map_cols * x + 1
                y_ = map_rows * y + 1
                if self.markers[y, x].top:
                    markers_str[y_ - 1, x_] = f'{TCOLORS[self.markers[y, x].top_color]}|{TCOLORS["end"]}'
                if self.markers[y, x].left:
                    markers_str[y_, x_ - 1] = f'{TCOLORS[self.markers[y, x].left_color]}——{TCOLORS["end"]}'
                if self.markers[y, x].right:
                    markers_str[y_, x_ + 1] = f'{TCOLORS[self.markers[y, x].right_color]}——{TCOLORS["end"]}'
                if self.markers[y, x].bottom:
                    markers_str[y_ + 1, x_] = f'{TCOLORS[self.markers[y, x].bottom_color]}|{TCOLORS["end"]}'

        markers_str = pd.DataFrame(markers_str)
        # insert sep cols
        for i in range(self.cols + 1):
            markers_str.insert(map_cols * i + i, 'sep', f'{TCOLORS["white"]}.{TCOLORS["end"]}', allow_duplicates=True)
        markers_str = markers_str.T
        # insert sep rows
        for i in range(self.rows + 1):
            markers_str.insert(map_cols * i + i, 'sep', f'{TCOLORS["white"]}.{TCOLORS["end"]}', allow_duplicates=True)
        return markers_str.T.to_string(header=False, index=False)


class Line():
    def __init__(self, x1, y1, x2, y2, color):
        assert color is not None
        assert x1 is not None
        assert y1 is not None
        assert x2 is not None
        assert y2 is not None
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = color

    @classmethod
    def init_from_json(cls, json):
        return cls(json['x1'], json['y1'], json['x2'], json['y2'], COLORS[json['color']])

    def to_markers(self):
        x1, x2, y1, y2 = self.x1, self.x2, self.y1, self.y2

        m_list = []
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                m_list.append(Marker(x=x, y=y))

        for i in range(len(m_list)):
            for j in range(i + 1, len(m_list)):
                m1, m2 = m_list[i], m_list[j]
                x1, y1 = m1.x, m1.y
                x2, y2 = m2.x, m2.y
                if (x1 == x2) and (y1 < y2):
                    m1.bottom = m2.top = True
                    m1.bottom_color = m2.top_color = self.color
                elif (x1 == x2) and (y1 > y2):
                    m1.top = m2.bottom = True
                    m1.top_color = m2.bottom_color = self.color
                elif (x1 > x2) and (y1 == y2):
                    m1.left = m2.right = True
                    m1.left_color = m2.right_color = self.color
                elif (x1 < x2) and (y1 == y2):
                    m1.right = m2.left = True
                    m1.right_color = m2.left_color = self.color
                else:
                    raise ValueError("Invalid line!")
        return m_list
