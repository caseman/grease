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
"""Grease entities are useful as actionable, interactive
game elements that are often visible to the player.

You might use entities to represent:

- Characters
- Bullets
- Particles
- Pick-ups
- Space Ships
- Weapons
- Trees
- Planets
- Explosions

See :ref:`an example entity class in the tutorial <tut-entity-example>`.
"""
from grease import component

__all__ = ('Entity',)


class EntityMeta(type):
	"""The Entity metaclass ensures that :class:`grease.component.Property`
	objects on the class are assigned a name according to their attribute
	name if one was not explicitly specified.
	"""

	def __new__(cls, clsname, clsbases, clsdict):
		for name, obj in clsdict.items():
			if isinstance(obj, component.Property) and obj.name is None:
				obj.name = name
		return type.__new__(cls, clsname, clsbases, clsdict)


class Entity(object):
	"""Base class for grease entities.
	
	Entity objects themselves are merely identifiers within a :class:`grease.world.World`.
	They also provide a facade for convenient entity-wise access of component
	data. However, they do not contain any data themselves other than an
	entity id.

	Entities must be instantiated in the context of a world. To instantiate an
	entity, you must pass the world as the first argument to the constructor.
	Subclasses that implement the :meth:`__init__()` method, must accept the world
	as their first argument (after ``self``). Other constructor arguments can be
	specified arbitarily by the subclass.
	"""
	__metaclass__ = EntityMeta

	def __new__(cls, world, *args, **kw):
		"""Create a new entity and add it to the world"""
		entity = object.__new__(cls)
		entity.world = world
		entity.entity_id = world.entity_id_generator.new_entity_id(entity)
		world.entities.add(entity)
		return entity

	def delete(self):
		"""Delete the entity from its world. This removes all of its
		component data. If the entity has already been deleted, 
		this call does nothing.
		"""
		self.world.entities.discard(self)

	@property
	def exists(self):
		"""True if the entity still exists in the world"""
		return self.entity_id is not None and self in self.world.entities
	
	def __hash__(self):
		return hash(self.entity_id)
	
	def __eq__(self, other):
		return self.world is other.world and self.entity_id == other.entity_id

	def __repr__(self):
		return "<%s id: %s of %s %x>" % (
			self.__class__.__name__, self.entity_id,
			self.world.__class__.__name__, id(self.world))









