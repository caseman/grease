from grease.component.general import Component
from grease.geometry import Vec2d, Vec2dArray, Rect
from grease import color

class ComponentError(Exception):
	"""General component error"""


class Position(Component):
	"""Stores position and orientation info for entities"""

	def __init__(self):
		Component.__init__(self, position=Vec2d, angle=float)


class Transform(Component):
	"""Stores offset, shear, rotation and scale info for entity shapes"""

	def __init__(self):
		Component.__init__(self, offset=Vec2d, shear=Ve2d, rotation=float, scale=float)
		self.fields['scale'].default = lambda: 1.0


class Movement(Component):
	"""Stores velocity, acceleration and rotation info for entities"""

	def __init__(self):
		Component.__init__(self, velocity=Vec2d, accel=Vec2d, rotation=float)


class Shape(Component):
	"""Stores shape vertices for entities"""

	def __init__(self):
		Component.__init__(self, closed=int, verts=Vec2dArray)
		self.fields['closed'].default = lambda: 1


class Renderable(Component):
	"""Identifies entities to be rendered and provides their depth and color"""

	def __init__(self):
		Component.__init__(self, depth=float, color=color.RGBA)
		self.fields['color'].default = lambda: color.RGBA(1,1,1,1)


class Collision(Component):
	"""Stores collision masks to determine which entities can collide

	Fields:

	aabb (Rect) -- The axis-aligned bounding box for the entity.
	This is used for broad-phase collision detection.

	radius (float) -- The collision radius of the entity, used for narrow-phase
	collision detection. The exact meaning of this value depends on the collision
	system in use.
	
	from_mask (int) -- A bitmask that determines what entities this object
	can collide with.

	into_mask (int) -- A bitmask that determines what entities can collide
	with this object.

	When considering an entity A for collision with entity B, A's from_mask is
	bit ANDed with B's into_mask. If the result is nonzero (meaning 1 or more
	bits is set the same for each) then the collision test is made. Otherwise,
	the pair cannot collide.  This also enables the specification of a
	collision "direction".  For instance, it is possible that entity A can be
	considered colliding into entity B, but not vice versa. This allows for
	simpler collision handling for things like bullets, where the logic may be
	better placed on one side than the other.

	The default value for both of these masks is 0xffffffff, which means that
	all entities will collide with each other by default.
	"""
	def __init__(self):
		Component.__init__(self, aabb=Rect, radius=float, from_mask=int, into_mask=int)
		self.fields['into_mask'].default = lambda: 0xffffffff
		self.fields['from_mask'].default = lambda: 0xffffffff

