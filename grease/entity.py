
class Entity(object):
	"""An interface for accessing and manipulating component
	data for a single entity. Note data is not actually stored
	in this object directly, it is just for convenience.
	"""

	def __init__(self, component_manager, entity_id):
		self.__manager = component_manager
		self.__entity_id = entity_id
	
	@property
	def entity_id(self):
		return self.__entity_id

	def __getattr__(self, name):
		"""Return a component accessor for this entity"""
		try:
			component = self.__manager.components[name]
		except KeyError:
			raise AttributeError("No such component: %s" % name)
		return EntityComponentAccessor(component, self.__entity_id)
	
	def __delattr__(self, name):
		"""Remove the data for this entity from the component"""
		try:
			component = self.__manager.components[name]
		except KeyError:
			raise AttributeError("No such component: %s" % name)
		component.remove(self.__entity_id)
	
	def __eq__(self, other):
		return self.__manager is other.__manager and self.entity_id == other.entity_id

	def __repr__(self):
		return "<%s id: %s of %s %x>" % (
			self.__class__.__name__, self.__entity_id,
			self.__manager.__class__.__name__, id(self.__manager))


class EntityComponentAccessor(object):
	"""A facade for accessing specific component data for a single entity.
	The implementation is lazy and does not actually access the component
	data until needed. If an attribute is set for a component that the 
	entity is not yet a member of, it is automatically added to the
	component first.
	"""

	def __init__(self, component, entity_id):
		cls = self.__class__.__name__
		self.__dict__['_%s__component' % cls] = component
		self.__dict__['_%s__entity_id' % cls] = entity_id
		self.__dict__['_%s__data' % cls] = None
	
	def __getattr__(self, name):
		if self.__data is None:
			cls = self.__class__.__name__
			self.__dict__['_%s__data' % cls] = self.__component[self.__entity_id]
		return getattr(self.__data, name)
	
	def __setattr__(self, name, value):
		if self.__data is None:
			cls = self.__class__.__name__
			if self.__entity_id in self.__component:
				self.__dict__['_%s__data' % cls] = self.__component[self.__entity_id]
			else:
				self.__dict__['_%s__data' % cls] = self.__component.add(self.__entity_id)
		setattr(self.__data, name, value)


class EntitySet(object):
	"""A queriable set of entities"""

	def __init__(self, manager, entity_ids=(), entity_factory=Entity):
		self._manager = manager
		if not isinstance(entity_ids, set):
			entity_ids = set(entity_ids)
		self._entities = entity_ids
		self._entity_factory = entity_factory
	
	def __len__(self):
		return len(self._entities)
	
	def __contains__(self, entity):
		entity_id = getattr(entity, "entity_id", entity)
		return entity_id in self._entities
	
	def __iter__(self):
		manager = self._manager
		entity_factory = self._entity_factory
		for entity_id in self._entities:
			yield entity_factory(manager, entity_id)
	
	def __eq__(self, other):
		return self._manager is other._manager and self._entities == other._entities

	def intersection(self, other):
		assert self._manager is other._manager, "Sets must have same component manager"
		return EntitySet(self._manager, self._entities.intersection(other._entities))
	
	__and__ = intersection
	
	def union(self, other):
		assert self._manager is other._manager, "Sets must have same component manager"
		return EntitySet(self._manager, self._entities.union(other._entities))
	
	__or__ = union

	def difference(self, other):
		assert self._manager is other._manager, "Sets must have same component manager"
		return EntitySet(self._manager, self._entities.difference(other._entities))

	__sub__ = difference

	def __getattr__(self, name):
		if name in self._manager.components:
			return self & self._manager.components[name].entity_set
		raise AttributeError(name)


class ComponentEntitySet(EntitySet):
	"""set of entities in a component, can be queried by component fields"""

	_component = None

	def __init__(self, component, entity_ids=None):
		self._component = component
		EntitySet.__init__(self, component.manager, entity_ids)
	
	def __getattr__(self, name):
		if self._component is not None and name in self._component.fields:
			return self._component.fields[name].accessor(self._entities)
		raise AttributeError(name)
	
	def __setattr__(self, name, value):
		if self._component is not None and name in self._component.fields:
			self._component.fields[name].set(value, self._entities)
		else:
			EntitySet.__setattr__(self, name, value)

