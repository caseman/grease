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

__version__ = '$Id$'

from grease.component import base
from grease.component import field
from grease.entity import ComponentEntitySet


class Component(dict):
	"""General component with a configurable schema

	The field schema is defined via keyword args where the 
	arg name is the field name and the value is the type object.

	The following types are supported for fields:

	- :class:`int`
	- :class:`float`
	- :class:`bool`
	- :class:`str`
	- :class:`object`
	- |Vec2d|
	- |Vec2dArray|
	- |RGBA|
	- |Rect|
	"""

	deleted_entities = ()
	"""List of entities deleted from the component since the last time step"""

	new_entities = ()
	"""List of entities added to the component since the last time step"""

	def __init__(self, **fields):
		self.fields = {}
		for fname, ftype in fields.items():
			assert ftype in field.types, fname + " has an illegal field type"
			self.fields[fname] = field.Field(self, fname, ftype)
		self.entities = ComponentEntitySet(self)
		self._added = []
		self._deleted = []
	
	def set_world(self, world):
		self.world = world
	
	def step(self, dt):
		"""Update the component for the next timestep"""
		delitem = super(Component, self).__delitem__
		for entity in self._deleted:
			delitem(entity)
		self.new_entities = self._added
		self.deleted_entities = self._deleted
		self._added = []
		self._deleted = []
	
	def set(self, entity, data=None, **data_kw):
		"""Set the component data for an entity, adding it to the
		component if it is not already a member.

		If data is specified, its data for the new entity's fields are
		copied from its attributes, making it easy to copy another
		entity's data. Keyword arguments are also matched to fields.
		If both a data attribute and keyword argument are supplied for
		a single field, the keyword arg is used.
		"""
		if data is not None:
			for fname, field in self.fields.items():
				if fname not in data_kw and hasattr(data, fname):
					data_kw[fname] = getattr(data, fname)
		data = self[entity] = Data(self.fields, entity, **data_kw)
		return data
	
	def __setitem__(self, entity, data):
		assert entity.world is self.world, "Entity not in component's world"
		if entity not in self.entities:
			self._added.append(entity)
			self.entities.add(entity)
		super(Component, self).__setitem__(entity, data)
	
	def remove(self, entity):
		if entity in self.entities:
			self._deleted.append(entity)
			self.entities.remove(entity)
			return True
		return False
	
	__delitem__ = remove

	def __repr__(self):
		return '<%s %x of %r>' % (
			self.__class__.__name__, id(self), getattr(self, 'world', None))


class Singleton(Component):
	"""Component that may contain only a single entity"""

	def add(self, entity_id, data=None, **data_kw):
		if entity_id not in self._data:
			self.entity_id_set.clear()
			self._data.clear()
		Component.add(self, entity_id, data, **data_kw)
	
	@property
	def entity(self):
		"""Return the entity in the component, or None if empty"""
		if self._data:
			return self.manager[self._data.keys()[0]]
	

class Data(object):

	def __init__(self, fields, entity, **data):
		self.__dict__['_Data__fields'] = fields
		self.__dict__['entity'] = entity
		for field in fields.values():
			if field.name in data:
				setattr(self, field.name, data[field.name])
			else:
				setattr(self, field.name, field.default())
	
	def __setattr__(self, name, value):
		if name in self.__fields:
			self.__dict__[name] = self.__fields[name].cast(value)
		else:
			raise AttributeError("Invalid data field: " + name)
	
	def __repr__(self):
		return '<%s(%r)>' % (self.__class__.__name__, self.__dict__)

			

