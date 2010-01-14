from field import Schema
from general import Component
from grease.vector import Vec2d, Vec2dArray
from grease import color

class ComponentError(Exception):
	"""General component error"""


class Position(Component):
	"""Stores position and rotation info for entities"""

	def __init__(self):
		Component.__init__(self, xy=Vec2d, last_xy=Vec2d, z=float, angle=float, last_angle=float)


class Movement(Component):
	"""Stores velocity and acceleration info for entities"""

	def __init__(self):
		Component.__init__(self, velocity=Vec2d, last_velocity=Vec2d, accel=Vec2d)


class Shape(Component):
	"""Stores shape vertices for entities"""

	def __init__(self):
		Component.__init__(self, verts=Vec2dArray, line_color=color.RGBA, fill_color=color.RGBA)
