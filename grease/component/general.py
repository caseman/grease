#############################################################################
#
# Copyright (c) 2010, 2011 by Casey Duncan and contributors
# All Rights Reserved.
#
# This software is subject to the provisions of the MIT License
# A copy of the license should accompany this distribution.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
#############################################################################
from grease.component import field
from grease.set import EntitySet

__all__ = ('Component', 'ComponentAccessor')


class Component(object):
	"""General component with a configurable schema.

	The component field schema is defined via keyword args where the arg name
	is the field name and the value is the field data type spec (dtype) stored
	for each entity "row".

	Here are some examples of common field data types:

	- :class:`int` (native integer)
	- :class:`float` (double-precision float)
	- :class:`bool` (1 byte boolean)
	- :class:`object` (arbitrary Python object)
	- "int8", "int16", "int32" (various integer sizes)
	- "float32", "float64", "float128" (various float sizes)
	- "2d", "3d", "4d" (double-precision vectors of 2, 3, and 4 dimensions)
	- "2f", "3f", "4f" (single-precision vectors)
	- "2i", "3i", "4i" (integer vectors)

	The dtype specified is used to create numpy arrays that store the field
	data. numpy dtypes are extremely powerful and support just about any
	arbitrary static data structure. See the |Field| class reference and `the
	numpy dtype documentation
	<http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html>`_ for
	complete details.
	"""

	entities = None
	"""Set of |Entity| objects that have data in this component."""

	fields = None
	"""Mapping of field names to the component's |Field| objects."""

	deleted_entities = ()
	"""List of entities deleted from the component since the last time step."""

	new_entities = ()
	"""List of entities added to the component since the last time step."""

	world = None
	"""The |World| this component belongs to."""

	entity_set_factory = EntitySet
	field_factory = field.Field

	def __init__(self, **fields):
		self.fields = {}
		for fname, dtype in fields.items():
			self.fields[fname] = self.field_factory(fname, dtype)
		self._added = []
		self._deleted = []
	
	def set_world(self, world):
		self.world = world
		self.entities = self.entity_set_factory(world)
	
	def step(self, dt):
		"""Update the component for the next timestep."""
		self.new_entities = self._added
		self.deleted_entities = self._deleted
		self._added = []
		self._deleted = []
	
	def add(self, entity):
		if entity.world is not self.world:
			if self.world is None:
				raise RuntimeError(
					"Cannot add entity, component world not set")
			raise ValueError(
				"Cannot add entity to component, not in same world")
		if entity not in self.entities:
			self._added.append(entity)
			self.entities.add(entity)
			for field in self.fields.values():
				field[entity] = field.default
	
	def delete(self, entity):
		"""Delete an entity from the component. Return True if the entity was
		in the component, False if not. In the latter case this method does
		nothing.
		"""
		if entity in self.entities:
			self._deleted.append(entity)
			self.entities.remove(entity)
			return True
		return False
	
	def __contains__(self, entity):
		"""Return True if the specified entity is in the component"""
		return entity in self.entities

	def __repr__(self):
		return '<%s %x of %r>' % (
			self.__class__.__name__, id(self), self.world)


class ComponentAccessor(object):
	"""A facade for accessing specific component data for a single entity.
	If an attribute is set for a component that the entity is not yet a member
	of, it is automatically added to the component first.

	:param component: The :class:`grease.Component` being accessed
	:param entity: The :class:`Entity` being accessed
	"""

	def __init__(self, component, entity):
		self.__component = component
		self.__entity = entity
	
	def __nonzero__(self):
		"""The accessor is True if the entity is in the component,
		False if not, for convenient membership tests
		"""
		return self.__entity in self.__component
	
	def __getattr__(self, name):
		if self.__entity in self.__component.entities:
			try:
				return self.__component.fields[name][self.__entity]
			except (KeyError, IndexError):
				raise AttributeError(name)
		raise AttributeError(name)
	
	def __setattr__(self, name, value):
		"""Set the data for the specified field of the entity's component"""
		if not name.startswith('_'):
			if self.__entity not in self.__component.entities:
				self.__component.add(self.__entity)
			try:
				self.__component.fields[name][self.__entity] = value
			except KeyError:
				raise AttributeError(name)
		else:
			super(ComponentAccessor, self).__setattr__(name, value)

	def __repr__(self):
		return '<%s %x for %r, %r>' % (
			self.__class__.__name__, id(self), self.__entity, self.__component)


class Property(object):
	"""A descriptor for accessing and manipulating component values as 
	attributes of an entity::

		class MyEntity(Entity):
			movement = component.Property()

			def __init__(self, world, velocity):
				self.movement.velocity = velocity
	
	:arg component_name: The name of the component to access via the
		property. If omitted, it will be derived automatically from
		the attribute name when assigned to an |Entity| subclass.
	:type component_name: str
	:arg doc: Optional doc string for this property.
	:type doc: str
	"""

	def __init__(self, component_name=None, doc=None):
		self.name = component_name
		self.__doc__ = doc

	def __get__(self, entity, cls):
		component = getattr(entity.world.components, self.name)
		return ComponentAccessor(component, entity)

	def __set__(self, entity, value):
		component = getattr(entity.world.components, self.name)
		for fname, field in component.fields:
			if hasattr(value, fname):
				field[entity] = getattr(value, fname)

	def __delete__(self, entity):
		component = getattr(entity.world.components, self.name)
		component.delete(entity)
	
	def __repr__(self):
		return '<component.Property for component %s>' % self.name

