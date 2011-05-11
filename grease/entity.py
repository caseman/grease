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

import numpy
from grease.block import Block

__all__ = ('Entity', 'EntityComponentAccessor', 'ComponentEntitySet')


class EntityMeta(type):
	"""The entity metaclass enforces fixed slots of `entity_id` and `world`
	for all subclasses. This prevents accidental use of other entity instance 
	attributes, which may not be saved. 
	
	Class attributes are not affected by this restriction, but subclasses
	should be careful not to cause name collisions with world components,
	which are exposed as entity attributes. Using a naming convention for
	class attributes, such as UPPER_CASE_WITH_UNDERSCORES is recommended to
	avoid name clashes.

	Note as a result of this, entity subclasses are not allowed to define
	`__slots__`, and doing so will cause a `TypeError` to be raised.
	"""

	def __new__(cls, name, bases, clsdict):
		if '__slots__' in clsdict:
			raise TypeError('__slots__ may not be defined in Entity subclasses')
		clsdict['__slots__'] = ('world', 'entity_id')
		return type.__new__(cls, name, bases, clsdict)


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
	
	def __getattr__(self, name):
		"""Return an :class:`EntityComponentAccessor` for this entity
		for the component named.

		Example::

			my_entity.movement
		"""
		component = getattr(self.world.components, name)
		return EntityComponentAccessor(component, self)
	
	def __setattr__(self, name, value):
		"""Set the entity data in the named component for this entity.
		This sets the values of the component fields to the values of
		the matching attributes of the value provided. This value must
		have attributes for each of the component fields.

		This allows you to easily copy component data from one entity
		to another.

		Example::

			my_entity.position = other_entity.position
		"""
		if name in self.__class__.__slots__:
			super(Entity, self).__setattr__(name, value)
		else:
			component = getattr(self.world.components, name)
			component.set(self, value)
	
	def __delattr__(self, name):
		"""Remove this entity and its data from the component.
		
		Example::
		
			del my_entity.renderable
		"""
		component = getattr(self.world.components, name)
		del component[self]
	
	def __hash__(self):
		return hash(self.entity_id)
	
	def __eq__(self, other):
		return self.world is other.world and self.entity_id == other.entity_id

	def __repr__(self):
		return "<%s id: %s of %s %x>" % (
			self.__class__.__name__, self.entity_id,
			self.world.__class__.__name__, id(self.world))

	def delete(self):
		"""Delete the entity from its world. This removes all of its
		component data. If then entity has already been deleted, 
		this call does nothing.
		"""
		self.world.entities.discard(self)

	@property
	def exists(self):
		"""True if the entity still exists in the world"""
		return self.entity_id is not None and self in self.world.entities


class EntityComponentAccessor(object):
	"""A facade for accessing specific component data for a single entity.
	The implementation is lazy and does not actually access the component
	data until needed. If an attribute is set for a component that the 
	entity is not yet a member of, it is automatically added to the
	component first.

	:param component: The :class:`grease.Component` being accessed
	:param entity: The :class:`Entity` being accessed
	"""
	
	# beware, name mangling ahead. We want to avoid clashing with any
	# user-configured component field names
	__data = None

	def __init__(self, component, entity):
		clsname = self.__class__.__name__
		self.__dict__['_%s__component' % clsname] = component
		self.__dict__['_%s__entity' % clsname] = entity
	
	def __nonzero__(self):
		"""The accessor is True if the entity is in the component,
		False if not, for convenient membership tests
		"""
		return self.__entity in self.__component
	
	def __getattr__(self, name):
		"""Return the data for the specified field of the entity's component"""
		if self.__data is None:
			try:
				data = self.__component[self.__entity]
			except KeyError:
				raise AttributeError(name)
			clsname = self.__class__.__name__
			self.__dict__['_%s__data' % clsname] = data
		return getattr(self.__data, name)
	
	def __setattr__(self, name, value):
		"""Set the data for the specified field of the entity's component"""
		if self.__data is None:
			clsname = self.__class__.__name__
			if self.__entity in self.__component:
				self.__dict__['_%s__data' % clsname] = self.__component[self.__entity]
			else:
				self.__dict__['_%s__data' % clsname] = self.__component.set(self.__entity)
		setattr(self.__data, name, value)


class ComponentEntitySet(set):
	"""Set of entities in a component, can be queried by component fields"""

	_component = None

	def __init__(self, component, entities=()):
		self.__dict__['_component'] = component
		super(ComponentEntitySet, self).__init__(entities)
	
	def __getattr__(self, name):
		if self._component is not None and name in self._component.fields:
			return self._component.fields[name].accessor(self)
		raise AttributeError(name)
	
	def __setattr__(self, name, value):
		if self._component is not None and name in self._component.fields:
			self._component.fields[name].accessor(self).__set__(value)
		raise AttributeError(name)


class EntitySet(object):
	"""Set of entities in a world"""

	def __init__(self, world):
		self.world = world
		self.blocks = {}
	
	def new_empty(self):
		"""Create a new empty set of the same type and world.
		This is a common interface for creating a set with no
		arguments.
		"""
		new = EntitySet.__new__(self.__class__)
		new.world = self.world
		new.blocks = {}
		return new
	
	def _get_block(self, block_id, index):
		try:
			block = self.blocks[block_id]
			block.grow(index + 1, 0)
		except KeyError:
			block = self.blocks[block_id] = Block(
				shape=index + 1, dtype="int32")
			block.fill(0)
		return block
	
	def add(self, entity):
		"""Add an entity to the set.
		
		:raises ValueError: If the entity is not part of the same
		world as the set, also for deleted entities.
		"""
		if entity.world is not self.world:
			raise ValueError("Cannot add entity from different world")
		if entity not in self.world.entities:
			raise ValueError("Cannot add deleted entity")
		gen, block, index = entity.entity_id
		self._get_block(block, index)[index] = gen
	
	def remove(self, entity):
		"""Remove an entity from the set. 
		
		:raises KeyError: if entity is not in the set.
		"""
		gen, block, index = entity.entity_id
		try:
			gen_in = self.blocks[block][index]
		except (KeyError, IndexError):
			raise KeyError(entity)
		if entity.world is self.world and gen_in == gen:
			self.blocks[block][index] = 0
		else:
			raise KeyError(entity)
	
	def discard(self, entity):
		"""Remove an entity from the set, do nothing if the entity is
		not in the set
		"""
		gen, block, index = entity.entity_id
		try:
			gen_in_set = self.blocks[block][index]
		except (KeyError, IndexError):
			return
		if entity.world is self.world and gen_in_set == gen:
			self.blocks[block][index] = 0
	
	def __contains__(self, entity):
		if entity.world is self.world:
			gen, block, index = entity.entity_id
			try:
				return self.blocks[block][index] == gen
			except (KeyError, IndexError):
				return False
		return False
	
	def __iter__(self):
		id_to_entity = self.world.entities.id_to_entity
		for block_id, block in self.blocks.items():
			for index, gen in enumerate(block):
				try:
					yield id_to_entity[gen, block_id, index]
				except KeyError:
					pass
	
	def __nonzero__(self):
		for block in self.blocks.values():
			if block.any():
				return True
		return False

	def __len__(self):
		return sum(len(block.nonzero()[0]) for block in self.blocks.values())
	
	def __eq__(self, other):
		if self is other:
			return True
		if isinstance(other, EntitySet):
			self_blk_ids = set(self.blocks)
			other_blk_ids = set(other.blocks)
			for blk_id in (self_blk_ids - other_blk_ids):
				if self.blocks[blk_id].any():
					return False
			for blk_id in (other_blk_ids - self_blk_ids):
				if other.blocks[blk_id].any():
					return False
			for blk_id, blk in self.blocks.items():
				if blk_id in other.blocks:
					other_blk = other.blocks[blk_id]
					if len(blk) > len(other_blk):
						if not ((blk[:len(other_blk)] == other_blk).all() and
							(blk[len(other_blk):] == 0).all()):
							return False
					elif len(blk) < len(other_blk):
						if not ((other_blk[:len(blk)] == blk).all() and
							(other_blk[len(blk):] == 0).all()):
							return False
					elif not (blk == other_blk).all():
						return False
			return True
		else:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def intersection(self, other):
		"""Return a set which is the intersection of this set and another"""
		if self.world is not other.world:
			raise ValueError("Can't combine sets from different worlds")
		result = self.new_empty()
		for blk_id, blk in self.blocks.items():
			if blk_id in other.blocks:
				other_blk = other.blocks[blk_id]
				if len(blk) < len(other_blk):
					other_blk = other_blk[:len(blk)]
				elif len(blk) > len(other_blk):
					blk = blk[:len(other_blk)]
				result_blk = numpy.where(blk == other_blk, blk, 0)
				if result_blk.any():
					result.blocks[blk_id] = result_blk
		return result
	
	__and__ = intersection

	def union(self, other):
		"""Return a set which is the union of this set and another"""
		if self.world is not other.world:
			raise ValueError("Can't combine sets from different worlds")
		result = self.new_empty()
		for blk_id, blk in self.blocks.items():
			if blk_id not in other.blocks:
				result.blocks[blk_id] = self.blocks[blk_id].copy()
		for blk_id, other_blk in other.blocks.items():
			if blk_id not in self.blocks:
				result.blocks[blk_id] = other_blk.copy()
			else:
				blk = self.blocks[blk_id]
				if len(blk) < len(other_blk):
					lblk = blk
					rblk = other_blk[:len(blk)]
				elif len(blk) > len(other_blk):
					lblk = blk[:len(other_blk)]
					rblk = other_blk
				else:
					lblk = blk
					rblk = other_blk
				result_blk = numpy.where(lblk >= rblk, lblk, rblk)
				if len(blk) < len(other_blk):
					result_blk = numpy.concatenate(
						(result_blk, other_blk[len(blk):]))
				elif len(blk) > len(other_blk):
					result_blk = numpy.concatenate(
						(result_blk, blk[len(other_blk):]))
				result.blocks[blk_id] = result_blk
		return result
	
	__or__ = union

	def difference(self, other):
		"""Return a set which is the difference of this set and another"""
		if self.world is not other.world:
			raise ValueError("Can't combine sets from different worlds")
		result = self.new_empty()
		for blk_id, blk in self.blocks.items():
			if blk_id not in other.blocks:
				result.blocks[blk_id] = blk.copy()
			else:
				other_blk = other.blocks[blk_id]
				if len(blk) > len(other_blk):
					lblk = blk[:len(other_blk)]
					result_blk = numpy.where(lblk > other_blk, lblk, 0)
					result_blk = numpy.concatenate(
						(result_blk, blk[len(other_blk):]))
				else:
					result_blk = numpy.where(
						blk > other_blk[:len(blk)], blk, 0)
				if result_blk.any():
					result.blocks[blk_id] = result_blk
		return result
	
	__sub__ = difference






