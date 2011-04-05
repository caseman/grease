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
from grease.component import field
from grease.entity import ComponentEntitySet


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

	entity_set_factory = ComponentEntitySet
	field_factory = field.Field

	def __init__(self, **fields):
		self.fields = {}
		for fname, dtype in fields.items():
			self.fields[fname] = self.field_factory(fname, dtype)
		self.entities = self.entity_set_factory(self)
		self._added = []
		self._deleted = []
	
	def set_world(self, world):
		self.world = world
	
	def step(self, dt):
		"""Update the component for the next timestep."""
		self.new_entities = self._added
		self.deleted_entities = self._deleted
		self._added = []
		self._deleted = []
	
	def set(self, entity, **data_kw):
		"""Set the component data for an entity, adding it to the component if
		it is not already a member. Any fields not specified when the entity
		is added will be set to their respective defaults.

		``ValueError`` is raised if an entity belonging to a different |World|
		is provided.
		"""
		if entity not in self.entities:
			if entity.world is not self.world:
				raise ValueError(
					"Cannot add entity to component, not in same world")
			self._added.append(entity)
			self.entities.add(entity)
			for fname, field in self.fields.items():
				field[entity] = data_kw.get(fname, field.default)
		else:
			# Entity already in component, set only those fields specified
			for fname, value in data_kw.items():
				self.fields[fname][entity] = value
	
	def get(self, entity):
		"""Return the component data of all fields for this entity in a dict"""
		if entity not in self.entities:
			raise KeyError(entity)
		data = {}
		for fname, field in self.fields.items():
			data[fname] = field[entity]
		return data
	
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


