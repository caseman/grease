from grease import entity
from grease.component import ComponentError
from grease.entity import EntitySet


class ComponentEntityManager(object):
	"""manages components and entities. The CEM acts as a container
	for its entities. Component entity sets are exposed as attributes 
	of the CEM. Components themselves can be manipulated via the
	component map accessible through the "components" attribute.
	
	Controllers can also be bound to the CEM. These controllers can
	inspect and manipulate entities each time the CEM's run() method
	is called.
	"""
	_entity_factory = entity.Entity
	_component_map = None
	_controllers = None

	def __init__(self, controllers=(), **components):
		self._component_map = ComponentMap(self, components)
		self.entity_id_set = set()
		self._controllers = ControllerList(self, controllers)
		self._entity_id = 0
		self.time = 0

	@property
	def components(self):
		"""Return the component map"""
		return self._component_map
	
	@property
	def controllers(self):
		"""Return the controller list"""
		return self._controllers

	@property
	def entity_set(self):
		return EntitySet(self, self.entity_id_set, self._entity_factory)
		
	def __iter__(self):
		for entity_id in self.entity_id_set:
			try:
				yield self[entity_id]
			except KeyError:
				continue

	def __contains__(self, entity):
		entity_id = getattr(entity, "entity_id", entity)
		return entity_id in self.entity_id_set
	
	def __len__(self):
		return len(self.entity_id_set)
	
	def __getitem__(self, entity_id):
		"""Return an entity for the given id"""
		if entity_id in self.entity_id_set:
			return self._entity_factory(self, entity_id)
		else:
			raise KeyError(entity_id)
	
	def __delitem__(self, entity):
		"""Delete an entity from the manager and all components"""
		entity_id = getattr(entity, "entity_id", entity)
		if entity_id in self.entity_id_set:
			for com in self.components:
				try:
					del com[entity_id]
				except KeyError:
					pass
			self.entity_id_set.remove(entity_id)
		else:
			raise KeyError(entity_id)
	
	def new_entity(self, entity_template=None, **component_data):
		"""Create a new entity and return it. 
		
		If entity_template is specified, then the entity is added to all
		components that have a corresponding attribute in the template. The
		template attributes are passed as data to each component's add()
		method to set the field values. Passing an existing entity as the
		template allows you to make a copy. Note the template cannot be used
		to specify the new entity's id, that is always set by the manager.

		Data for individual components may be passed as keyword arguments.
		The argument names must match the names of the components. The
		argument passed as data to each component's add() method to set the
		field values.  Component data keyword arguments will override any
		corresponding attribute of the entity_template. Note that the entity
		will be added to all components specified by keyword argument, even if
		the value has no attributes that match the component fields. This can
		be used to specify which components the entity belongs to initially 
		without setting the data if desired. This method is also a convenient
		way to copy component data from another entity into the new entity.

		If no template or keyword arguments are specified, the new entity 
		will belong to no components initially.
		"""
		if entity_template is not None:
			for name in self.components.keys():
				if hasattr(entity_template, name) and name not in component_data:
					component_data[name] = getattr(entity_template, name)
		components = self.components
		for name in component_data.keys():
			if name not in components:
				raise ComponentError('No component named: %s' % name)
		self._entity_id += 1
		for name, data in component_data.items():
			components[name].add(self._entity_id, data)
		self.entity_id_set.add(self._entity_id)
		return self._entity_factory(self, self._entity_id)
	
	def __getattr__(self, name):
		"""Access component entity sets as manager attributes"""
		if name in self.components:
			return self.components[name].entity_set
		raise AttributeError(name)


class ComponentMap(dict):
	"""Maps component names to components"""

	def __init__(self, manager, components):
		self._manager = manager
		for name, comp in components.items():
			self[name] = comp
	
	def __setitem__(self, name, component):
		if name not in self and hasattr(self._manager, name) or name.startswith('_'):
			raise ComponentError('illegal component name: %s' % name)
		dict.__setitem__(self, name, component)
		if hasattr(component, 'set_manager'):
			component.set_manager(self._manager)
	
	def __iter__(self):
		return self.itervalues()
	
	def iter_data(self, *component_names):
		"""Return an iterator of tuples containing data from each
		component specified by name for each entity in all of the
		components
		"""
		if component_names:
			components = [self[name] for name in component_names]
			entity_ids = components[0].entity_id_set
			for comp in components[1:]:
				entity_ids &= comp.entity_id_set
			for id in entity_ids:
				yield tuple(comp[id] for comp in components)


class ControllerList(list):
	"""List of controllers that can be safely modified while iterated"""

	def __init__(self, manager, controllers):
		self._manager = manager
		for ctrlr in controllers:
			self.add(ctrlr)

	def add(self, controller, before=None):
		"""Add a controller to the manager
		
		If before is specified, the new controller is inserted
		before the specified controller in order, otherwise it
		is appended.
		"""
		if before is None:
			self.append(controller)
		else:
			index = self.index(before)
			self.insert(index, controller)
	
	def insert(self, index, controller):
		if hasattr(controller, 'set_manager'):
			controller.set_manager(self._manager)
		list.insert(self, index, controller)
	
	def append(self, controller):
		if hasattr(controller, 'set_manager'):
			controller.set_manager(self._manager)
		list.append(self, controller)
	
	def __setitem__(self, index, controller):
		if hasattr(controller, 'set_manager'):
			controller.set_manager(self._manager)
		list.__setitem__(self, index, controller)

	def __iter__(self):
		return iter(tuple(self))
	
	def run(self, dt):
		"""Run a time step for all controllers in order"""
		self._manager.time += dt
		for controller in iter(tuple(self)):
			controller.run(dt)



