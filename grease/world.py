import itertools
import pyglet
from pyglet import gl
from grease import entity
from grease.component import ComponentError


class World(object):
	"""A coordinated collection of components, systems and entities"""

	components = None
	"""Map of world components by name. Components define and contain
	all entity data
	"""

	systems = None
	"""The world's systems are exposed as attributes of `World.systems`. 
	Systems define entity behavior
	"""

	entities = None
	"""Set of entities that exist in the world"""

	clock = None
	""":class:`pyglet.clock` interface for use by constituents
	of the world for scheduling
	"""

	time = None
	"""Total run time of the world"""

	running = True
	"""Flag to indicate that the world step kshould advance the time
	This flag is also used by WorldMode objects to control the mode's
	clock, so that scheduled tasks can be stopped and started with
	the world.
	"""
		
	def _set_renderers(self, renderers):
		self._renderers = tuple(renderers)
		for renderer in self._renderers:
			if hasattr(renderer, 'set_world'):
				renderer.set_world(self)
	
	def _get_renderers(self):
		return self._renderers
	
	renderers = property(_get_renderers, _set_renderers, None,
		"""A sequence of renderers. Renderere define the presentation
		of the world""")

	def __init__(self, entity_types=entity.entity_types):
		self.components = ComponentMapper(self)
		self.systems = SystemMap(self)
		self._renderers = ()
		self.new_entity_id = itertools.count().next
		self.new_entity_id() # skip id 0
		self.entities = WorldEntities(self)
		self.entity_types = entity_types
		self.clock = pyglet.clock
		self.time = 0
	
	def __getattr__(self, name):
		"""Return a world-wrapped entity type for the given name"""
		try:
			entity_type = self.entity_types[name]
		except KeyError:
			raise AttributeError(name)
		wrapped_type = type(name, (entity_type,), 
			{'world': self, 'entities': set(), '__slots__': ['entity_id'],
			 '__register__': False, '__baseclass__': entity_type})
		setattr(self, name, wrapped_type)
		return wrapped_type
	
	def step(self, dt):
		"""Execute a time step for the world. Updates the world time
		and invokes the world's systems.
		"""
		self.time += dt
		self.components.step(dt)
		self.systems.step(dt)
	
	def draw(self):
		"""Dispatch the renderers' `draw()` methods in order"""
		for renderer in self.renderers:
			renderer.draw()


class WorldEntities(set):
	"""Entity set for a :class:`World`"""

	def __init__(self, world):
		self.world = world

	def remove(self, entity):
		"""Remove the entity from the set and all world components"""
		super(WorldEntities, self).remove(entity)
		for component in self.world.components.itervalues():
			try:
				del component[entity]
			except KeyError:
				pass


class ComponentMapper(dict):
	"""Maps world component names to components"""

	reserved_names = ('entities', 'entity_id', 'world')

	def __init__(self, world):
		self._world = world
	
	def map(self, **components):
		"""Map components to names using keyword arguments"""
		for name, component in components.items():
			self[name] = component
	
	def update(self, stuff):
		raise NotImplementedError()
	
	def __setitem__(self, name, component):
		if name in self.reserved_names or name.startswith('_'):
			raise ComponentError('illegal component name: %s' % name)
		dict.__setitem__(self, name, component)
		if hasattr(component, 'set_world'):
			component.set_world(self._world)
	
	def __iter__(self):
		return self.itervalues()
	
	def join(self, *component_names):
		"""Return an iterator of tuples containing data from each
		component specified by name for each entity in all of the
		components
		"""
		if component_names:
			components = [self[name] for name in component_names]
			if len(components) > 1:
				entities = components[0].entities & components[1].entities
				for comp in components[2:]:
					entities &= comp.entities
			else:
				entities = components[0].entities
			for entity in entities:
				yield tuple(comp[entity] for comp in components)
	
	def step(self, dt):
		"""Update components for the next time step"""
		for component in self.itervalues():
			if hasattr(component, 'step'):
				component.step(dt)


class SystemMap(object):
	"""Ordered map of world systems"""

	def __init__(self, world):
		self._world = world
		self._list = []
	
	def add(self, *names_and_systems):
		"""Add one of more systems. Each system to add is provided in a
		('name', system) pair.
		"""
		for name, system in names_and_systems:
			if hasattr(self, name) or name.startswith('_'):
				raise ComponentError('illegal or duplicate system name: %s' % name)
			if hasattr(system, 'set_world'):
				system.set_world(self._world)
			self._list.append(system)
			setattr(self, name, system)

	def insert(self, name, system, before=None, index=None):
		"""Add a system to the manager

		name -- The name of the system.

		system -- The system to be added
		
		before -- A system object or name. If specified, the system is
		inserted before the specified system in order, otherwise it is
		appended.

		index -- If specified, the system is inserted in the position
		specified. You cannot specify both before and index.
		"""
		assert before is not None or index is not None, (
			"Must specify a value for 'before' or 'index'")
		assert before is None or index is None, (
			"Cannot specify both 'before' and 'index' arguments when inserting system")
		if hasattr(self, name) or name.startswith('_'):
			raise ComponentError('illegal or duplicate system name: %s' % name)
		setattr(self, name, system)
		if before is None and index is None:
			self._list.append(system)
		elif before is not None:
			if isinstance(before, str):
				before = getattr(self, before)
			index = self._list.index(before)
			self._list.insert(index, system)
		else:
			self._list.insert(index, system)
		if hasattr(system, 'set_world'):
			system.set_world(self._world)
	
	def remove(self, system_name):
		"""Remove the system by name"""
		system = getattr(self, system_name)
		self._list.remove(system)
		delattr(self, system_name)
	
	def __len__(self):
		return len(self._list)
	
	def __iter__(self):
		"""Iterate the systems in order"""
		return iter(tuple(self._list))
	
	def step(self, dt):
		"""Run a time step for all runnable systems in order"""
		for system in self:
			if hasattr(system, "step"): 
				system.step(dt)

