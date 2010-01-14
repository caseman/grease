import operator
from grease.entity import EntitySet
from grease.vector import Vec2d, Vec2dArray
from grease import color

# Allowed field types -> default values
types = {int:lambda: 0, 
         float:lambda: 0.0, 
		 str:lambda:"", 
		 Vec2d:lambda: Vec2d(0,0), 
		 Vec2dArray:lambda: Vec2dArray(),
		 color.RGBA: lambda: color.RGBA(0.0, 0.0, 0.0, 0.0)}

class Schema(dict):
	"""Field schema definition for custom components"""

	def __init__(self, **fields):
		for ftype in fields.values():
			assert ftype in types, fname + " has an illegal field type"
		self.update(fields)

class FieldAccessor(object):
	"""Facade for manipulating a field for a set of entities"""

	def __init__(self, field, entity_id_set):
		self.field = field
		self.entity_ids = entity_id_set
	
	def __iter__(self):
		"""Return an iterator of all field values in the set"""
		component = self.field.component
		name = self.field.name
		for entity_id in self.entity_ids:
			try:
				data = component[entity_id]
			except KeyError:
				continue
			yield getattr(data, name)
	
	def enumerate(self):
		"""yield (entity id, field value) pairs for each entity in the set"""
		component = self.field.component
		name = self.field.name
		for entity_id in self.entity_ids:
			try:
				data = component[entity_id]
			except KeyError:
				continue
			yield entity_id, getattr(data, name)
	
	def _match(self, value, op):
		value = self.field.cast(value)
		component = self.field.component
		name = self.field.name
		matches = set()
		add = matches.add
		for entity_id in self.entity_ids:
			try:
				data = component[entity_id]
			except KeyError:
				continue
			if op(getattr(data, name), value):
				add(entity_id)
		return EntitySet(self.field.component.manager, matches)
	
	def __eq__(self, value):
		"""Return an entity set of all entities with a matching field value"""
		return self._match(value, operator.eq)
	
	where_equals = __eq__
	
	def __ne__(self, value):
		"""Return an entity set of all entities not matching field value"""
		return self._match(value, operator.ne)
	
	where_not_equals = __ne__
	
	def __gt__(self, value):
		"""Return an entity set of all entities with a greater field value"""
		return self._match(value, operator.gt)
	
	where_greater = __gt__
	
	def __ge__(self, value):
		"""Return an entity set of all entities with a greater or equal field value"""
		return self._match(value, operator.ge)
	
	where_equal_or_greater = __ge__
	
	def __lt__(self, value):
		"""Return an entity set of all entities with a lesser field value"""
		return self._match(value, operator.lt)
	
	where_less = __lt__
	
	def __le__(self, value):
		"""Return an entity set of all entities with a lesser or equal field value"""
		return self._match(value, operator.le)
	
	where_less_or_equal = __le__
	
	def where_in(self, values):
		"""Return an entity set of all entities with a field value contained in values"""
		return self._match(values, operator.contains)
	
	## Batch mutator methods

	def set_all(self, value):
		"""Set the value of the field for all entities"""
		self.field.set(value, self.entity_id_set)

	def _do_all(self, value, op):
		value = self.field.cast(value)
		component = self.field.component
		name = self.field.name
		for entity_id in self.entity_ids:
			try:
				data = component[entity_id]
			except KeyError:
				continue
			setattr(data, name, op(getattr(data, name), value))
	
	def add_all(self, value):
		"""Add all entity values of this field by value in-place"""
		self._do_all(value, operator.iadd)
	
	__iadd__ = add_all

	def subtract_all(self, value):
		"""Subtract value from all entity values of this field in-place"""
		self._do_all(value, operator.isub)
	
	__isub__ = subtract_all
	
	def multiply_all(self, value):
		"""Multiply all entity values of this field by value in-place"""
		self._do_all(value, operator.imul)
	
	__imul__ = multiply_all
	
	def divide_all(self, value):
		"""Divide all entity values of this field by value in-place"""
		self._do_all(value, operator.idiv)
	
	__idiv__ = divide_all

	def mod_all(self, value):
		"""Compute the modulo by value for all entity values of this field in-place"""
		self._do_all(value, operator.imod)
	
	__imod__ = mod_all



class Field(object):
	"""Component field metadata and accessor interface"""

	def __init__(self, component, name, type, accessor_factory=FieldAccessor):
		self.component = component
		self.name = name
		self.type = type
		self.default = types.get(type)
		self.accessor_factory = accessor_factory
	
	def cast(self, value):
		"""Cast value to the appropriate type for thi field"""
		return self.type(value)
	
	def set(self, value, entity_id_set=None):
		"""Set the value for this component field for all entities in the component,
		or all entities in the id set specified that are also in the component
		"""
		value = self.cast(value)
		component = self.component
		name = self.name
		component_entity_ids = component.entity_id_set
		if entity_id_set is None or entity_id_set is component_entity_ids:
			entity_ids = component_entity_ids
		else:
			entity_ids = entity_id_set & component_entity_ids
		for entity_id in entity_ids:
			setattr(component[entity_id], name, value)
	
	def accessor(self, entity_id_set=None):
		"""Return the field accessor for the entities in the component,
		or all entities in the id set specified that are also in the component
		"""
		component_entity_ids = self.component.entity_id_set
		if entity_id_set is None or entity_id_set is component_entity_ids:
			entity_ids = component_entity_ids
		else:
			entity_ids = entity_id_set & component_entity_ids
		return self.accessor_factory(self, entity_ids)
		

