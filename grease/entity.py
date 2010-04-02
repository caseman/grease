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

__version__ = '$Id$'

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
		entity.entity_id = world.new_entity_id()
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
		return self.entity_id
	
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
		return self in self.world.entities


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

