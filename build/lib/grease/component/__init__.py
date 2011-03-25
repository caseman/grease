#############################################################################
#
# Copyright (c) 2010 by Casey Duncan and contributors
# All Rights Reserved.
#
# This software is subject to the provisions of the MIT License
# A copy of the license should accompany this distribution.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
#############################################################################
"""Components store all entity data in a given |World|. You can
think of components as tables with entities as their primary keys. Like
database tables, components are defined with a "schema" that specifies
the data fields. Each field in a component has a name and a type.

Component objects themselves have a dict-like interface with entities
as keys and data records as values. An application will typically 
interact with components via entity attributes, entity extents or
by joining them. For more information see:

- :class:`~grease.entity.Entity` class.
- :class:`~grease.world.EntityExtent` class.
- :meth:`~grease.world.ComponentParts.join` method of ComponentParts.

See also :ref:`defining custom components in the tutorial <custom-component-example>`.
"""

__version__ = '$Id$'

__all__ = ('Component', 'ComponentError', 'Position', 'Transform', 'Movement', 
	'Shape', 'Renderable', 'Collision')

from grease.component.general import Component
from grease.geometry import Vec2d, Vec2dArray, Rect
from grease import color


class ComponentError(Exception):
	"""General component error"""


class Position(Component):
	"""Predefined component that stores position and orientation info for 
	entities.

	Fields:

	- **position** (Vec2d) -- Position vector
	- **angle** (float) -- Angle, in degrees
	"""

	def __init__(self):
		Component.__init__(self, position=Vec2d, angle=float)


class Transform(Component):
	"""Predefined component that stores offset, shear, 
	rotation and scale info for entity shapes.
	
	Fields:

	- **offset** (Vec2d)
	- **shear** (Vec2d)
	- **rotation** (float)
	- **scale** (float, default 1.0)
	"""

	def __init__(self):
		Component.__init__(self, offset=Vec2d, shear=Vec2d, rotation=float, scale=float)
		self.fields['scale'].default = lambda: 1.0


class Movement(Component):
	"""Predefined component that stores velocity, 
	acceleration and rotation info for entities.
	
	Fields:

	- **velocity** (Vec2d) -- Rate of change of entity position
	- **accel** (Vec2d) -- Rate of change of entity velocity
	- **rotation** (Vec2d) -- Rate of change of entity angle, in degrees/time
	"""

	def __init__(self):
		Component.__init__(self, velocity=Vec2d, accel=Vec2d, rotation=float)


class Shape(Component):
	"""Predefined component that stores shape vertices for entities
	
	- **closed** (bool) -- If the shapes is closed implying an edge between
	  last and first vertices.
	- **verts** (Vec2dArray) -- Array of vertex points
	"""

	def __init__(self):
		Component.__init__(self, closed=int, verts=Vec2dArray)
		self.fields['closed'].default = lambda: 1


class Renderable(Component):
	"""Predefined component that identifies entities to be 
	rendered and provides their depth and color.
	
	- **depth** (float) -- Drawing depth, can be used to determine z-order
		  while rendering.
	- **color** (color.RGBA) -- Color used for entity. The effect of this
		  field depends on the renderer.
	"""

	def __init__(self):
		Component.__init__(self, depth=float, color=color.RGBA)
		self.fields['color'].default = lambda: color.RGBA(1,1,1,1)


class Collision(Component):
	"""Predefined component that stores collision masks to determine 
	which entities can collide.

	Fields:

	- **aabb** (Rect) -- The axis-aligned bounding box for the entity.
		This is used for broad-phase collision detection.

	- **radius** (float) -- The collision radius of the entity, used for narrow-phase
		collision detection. The exact meaning of this value depends on the collision
		system in use.
	
	- **from_mask** (int) -- A bitmask that determines what entities this object
		can collide with.

	- **into_mask** (int) -- A bitmask that determines what entities can collide
		with this object.

	When considering an entity A for collision with entity B, A's ``from_mask`` is
	bit ANDed with B's ``into_mask``. If the result is nonzero (meaning 1 or more
	bits is set the same for each) then the collision test is made. Otherwise,
	the pair cannot collide. 

	The default value for both of these masks is ``0xffffffff``, which means that
	all entities will collide with each other by default.
	"""
	def __init__(self):
		Component.__init__(self, aabb=Rect, radius=float, from_mask=int, into_mask=int)
		self.fields['into_mask'].default = lambda: 0xffffffff
		self.fields['from_mask'].default = lambda: 0xffffffff

