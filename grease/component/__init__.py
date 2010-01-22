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
	"""Stores velocity, acceleration and rotation info for entities"""

	def __init__(self):
		Component.__init__(self, velocity=Vec2d, last_velocity=Vec2d, accel=Vec2d, rotation=float)


class Shape(Component):
	"""Stores shape vertices for entities"""

	def __init__(self):
		Component.__init__(self, closed=int, verts=Vec2dArray)
		self.fields['closed'].default = lambda: 1


class Renderable(Component):
	"""Identifies entities to be rendered and provides their color"""

	def __init__(self):
		Component.__init__(self, color=color.RGBA)
		self.fields['color'].default = lambda: color.RGBA(1,1,1,1)

