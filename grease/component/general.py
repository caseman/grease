import base
import field
from grease.entity import ComponentEntitySet

class Component(base.ComponentBase):
	"""General component with a configurable schema"""

	def __init__(self, **fields):
		"""Initialize the component

		The field schema is defined via keyword args where the 
		arg name is the field name and the value is the type object.
		"""
		self.fields = {}
		for fname, ftype in fields.items():
			assert ftype in field.types, fname + " has an illegal field type"
			self.fields[fname] = field.Field(self, fname, ftype)
		self.entity_id_set = set()
		self._data = {}
	
	@property
	def entity_set(self):
		"""Return an entity set for all entities in this component"""
		return ComponentEntitySet(self, self.entity_id_set)
	
	def add(self, entity_id, data=None, **data_kw):
		"""Add the entity_id to the component and return an entity data
		object for it. 

		If data is specified, its data for the new entity's fields are
		copied from its attributes, making it easy to copy another
		entity's data. Keyword arguments are also matched to fields.
		If both a data attribute and keyword argument are supplied for
		a single field, the keyword arg is used.
		"""
		if entity_id not in self._data:
			if data is not None:
				for fname, field in self.fields.items():
					if fname not in data_kw and hasattr(data, fname):
						data_kw[fname] = getattr(data, fname)
			self._data[entity_id] = Data(self.fields, entity_id, **data_kw)
			self.entity_id_set.add(entity_id)
		return self._data[entity_id]
	
	def remove(self, entity_id):
		if entity_id in self.entity_id_set:
			del self._data[entity_id]
			self.entity_id_set.remove(entity_id)
			return True
		return False
	
	__delitem__ = remove

	def __len__(self):
		return len(self.entity_id_set)

	def __getitem__(self, entity_id):
		return self._data[entity_id]
	
	def __contains__(self, entity_id):
		return entity_id in self._data
	
	def __iter__(self):
		return self._data.itervalues()
	

class Data(object):

	def __init__(self, fields, entity_id, **data):
		self.__dict__['_Data__fields'] = fields
		self.__dict__['entity_id'] = entity_id
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

			

