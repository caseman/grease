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

import operator
import numpy
from copy import copy
from grease.geometry import Vec2d, Vec2dArray, Rect
from grease import color

# Allowed field types -> default values
types = {int:lambda: 0, 
         float:lambda: 0.0, 
		 bool:lambda: False,
		 str:lambda:"", 
		 object:lambda:None,
		 Vec2d:lambda: Vec2d(0,0), 
		 Vec2dArray:lambda: Vec2dArray(),
		 color.RGBA: lambda: color.RGBA(0.0, 0.0, 0.0, 0.0),
		 Rect: lambda: Rect(0.0, 0.0, 0.0, 0.0)}

_missing = object()


class Field(object):
	"""Component data field definition and storage.
	
	:param name: Field name, must be unique within its parent component.
	:type name: str
	:param dtype: Field data type. Must be a value that can be used
		as the dtype to construct a numpy array. This could be a Python type
		(like ``float``, ``int``, ``object``, etc), a string dtype spec (like
		``"3d"`, ``"2i"``, or ``"S32"``), a numpy built-in type (like
		numpy.uint32) or an actual ``numpy.dtype`` object.  See `the numpy
		documentation
		<http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html>`_ for
		full details.
	:param default: The default value for this field if no value is 
		specified when an entity is added. This value must be able to be
		coerced into the dtype specified. If not specified, a generic default
		value will be used, such as zeros for numeric types, and None for
		object types.
	"""

	def __init__(self, name, dtype, default=_missing):
		self.name = name
		if not isinstance(dtype, numpy.dtype):
			# coerce to a numpy dtype so invalid types
			# passed as strings or other objects fail early
			dtype = numpy.dtype(dtype)
		self.dtype = dtype
		if default is _missing and dtype.base.kind in 'biufc':
			# Generic default for numeric dtypes
			self.default = 0
		else:
			self.default = default
		self.blocks = {}

	def _block_factory(self, size):
		if self.default == 0:
			return numpy.zeros(shape=size, dtype=self.dtype)
		else:
			block = numpy.ndarray(shape=size, dtype=self.dtype)
			if self.default is not _missing:
				block.fill(self.default)
			return block

	def __getitem__(self, entity):
		"""Retrieve the field value for a given entity"""
		_, block, index = entity.entity_id
		return self.blocks[block][index]

	def __setitem__(self, entity, value):
		"""Set the field value for a given entity"""
		_, block_id, index = entity.entity_id
		try:
			block = self.blocks[block_id]
		except KeyError:
			block = self.blocks[block_id] = self._block_factory(index + 1)
		orig_size = len(block)
		if orig_size <= index:
			if index < 64:
				new_size = max((index + 1) * 2, 4)
			else:
				new_size = (index + 1) * 5 // 4
			block.resize(new_size, refcheck=False)
		block[index] = value


class FieldAccessor(object):
	"""Facade for manipulating a field for a set of entities"""

	__field = None
	__entities = None
	__attrs = None
	__getter = None
	__parent_getters = ()

	def __init__(self, field, entities, attrs=()):
		self.__field = field
		self.__entities = entities
		field_getter = operator.attrgetter(field.name)
		self.__attrs = attrs
		if attrs:
			getters = [field_getter] + [operator.attrgetter(attr) for attr in attrs]
			def get(entity):
				value = entity
				for getter in getters:
					value = getter(value)
				return value
			self.__getter = get
			self.__parent_getters = getters[:-1]
		else:
			self.__getter = field_getter
	
	def __getattr__(self, name):
		"""Return a FieldAccessor for the child attribute"""
		return self.__class__(self.__field, self.__entities, self.__attrs + (name,))
	
	def __setattr__(self, name, value):
		if value is self:
			return # returned by in-place mutators
		if hasattr(self.__class__, name):
			# Set local attr
			self.__dict__[name] = value
		elif not name.startswith('_'):
			getattr(self, name).__set__(value)
		else:
			raise AttributeError("Cannot set field attribute: %s" % name)
	
	@property
	def __setter(self):
		"""Return the proper setter function for setting the field value"""
		if not self.__attrs:
			return setattr
		else:
			parent_getters = self.__parent_getters
			def setter(data, name, value):
				for getter in parent_getters:
					data = getter(data)
				setattr(data, name, value)
			self.__setter = setter
			return setter
	
	def __set__(self, value):
		"""Set field values en masse"""
		# Mass set field attr
		setter = self.__setter
		component = self.__field.component
		if self.__attrs:
			name = self.__attrs[-1]
		else:
			name = self.__field.name
		if isinstance(value, FieldAccessor):
			# Join set between two entity sets
			if not self.__attrs:
				cast = self.__field.cast
			else: 
				cast = lambda x: x
			for entity in self.__entities:
				try:
					setter(component[entity], name, cast(value[entity]))
				except KeyError:
					pass
		else:
			if not self.__attrs:
				value = self.__field.cast(value)
			for entity in self.__entities:
				try:
					setter(component[entity], name, value)
				except KeyError:
					pass
	
	def __getitem__(self, entity):
		"""Return the field value for a single entity (used for joins)"""
		if entity in self.__entities:
			return self.__getter(self.__field.component[entity])
		raise KeyError(entity)
	
	def __contains__(self, entity):
		return entity in self.__entities

	def __repr__(self):
		return '<%s %s @ %x>' % (
			self.__class__.__name__, 
			'.'.join((self.__field.name,) + self.__attrs), id(self))
	
	def __nonzero__(self):
		return bool(self.__entities)
	
	def __iter__(self):
		"""Return an iterator of all field values in the set"""
		component = self.__field.component
		getter = self.__getter
		for entity in self.__entities:
			try:
				data = component[entity]
			except KeyError:
				continue
			yield getter(data)
	
	## batch comparison operators ##
	
	def __match(self, value, op):
		component = self.__field.component
		getter = self.__getter
		matches = set()
		add = matches.add
		if isinstance(value, FieldAccessor):
			# Join match between entity sets
			for entity in self.__entities:
				try:
					data = component[entity]
					other = value[entity]
				except KeyError:
					continue
				if op(getter(data), other):
					add(entity)
		else:
			for entity in self.__entities:
				try:
					data = component[entity]
				except KeyError:
					continue
				if op(getter(data), value):
					add(entity)
		return matches
	
	def __eq__(self, value):
		"""Return an entity set of all entities with a matching field value"""
		return self.__match(value, operator.eq)
	
	def __ne__(self, value):
		"""Return an entity set of all entities not matching field value"""
		return self.__match(value, operator.ne)
	
	def __gt__(self, value):
		"""Return an entity set of all entities with a greater field value"""
		return self.__match(value, operator.gt)
	
	def __ge__(self, value):
		"""Return an entity set of all entities with a greater or equal field value"""
		return self.__match(value, operator.ge)
	
	def __lt__(self, value):
		"""Return an entity set of all entities with a lesser field value"""
		return self.__match(value, operator.lt)
	
	def __le__(self, value):
		"""Return an entity set of all entities with a lesser or equal field value"""
		return self.__match(value, operator.le)
	
	def _contains(self, values):
		"""Return an entity set of all entities with a field value contained in values"""
		return self.__match(values, operator.contains)
	
	## Batch in-place mutator methods

	def __mutate(self, value, op):
		component = self.__field.component
		if self.__attrs:
			name = self.__attrs[-1]
		else:
			name = self.__field.name
		getter = self.__getter
		setter = self.__setter
		if isinstance(value, FieldAccessor):
			# Join between entity sets
			for entity in self.__entities:
				try:
					data = component[entity]
					other = value[entity]
				except KeyError:
					continue
				setter(data, name, op(getter(data), other))
		else:
			for entity in self.__entities:
				try:
					data = component[entity]
				except KeyError:
					continue
				setter(data, name, op(getter(data), value))
		return self
	
	def __iadd__(self, value):
		return self.__mutate(value, operator.iadd)
	
	def __isub__(self, value):
		return self.__mutate(value, operator.isub)
	
	def __imul__(self, value):
		return self.__mutate(value, operator.imul)
	
	def __idiv__(self, value):
		return self.__mutate(value, operator.idiv)
	
	def __itruediv__(self, value):
		return self.__mutate(value, operator.itruediv)
	
	def __ifloordiv__(self, value):
		return self.__mutate(value, operator.ifloordiv)

	def __imod__(self, value):
		return self.__mutate(value, operator.imod)

	def __ipow__(self, value):
		return self.__mutate(value, operator.ipow)

	def __ilshift__(self, value):
		return self.__mutate(value, operator.ilshift)

	def __irshift__(self, value):
		return self.__mutate(value, operator.irshift)

	def __iand__(self, value):
		return self.__mutate(value, operator.iand)

	def __ior__(self, value):
		return self.__mutate(value, operator.ior)

	def __ixor__(self, value):
		return self.__mutate(value, operator.ixor)

