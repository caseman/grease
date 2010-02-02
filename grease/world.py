import itertools
import pyglet
from pyglet import gl
from grease import entity
from grease.component import ComponentError


class World(object):
	
	def __init__(self, window=None, step_rate=60, start=True, 
		entity_types=entity.entity_types, clock=pyglet.clock):
		self.components = ComponentMapper(self)
		self.systems = SystemMap(self)
		self._renderers = ()
		self.new_entity_id = itertools.count().next
		self.new_entity_id() # skip id 0
		self.entities = set()
		self.window = window
		if window is not None:
			self.window.on_draw = self.on_draw
		self.step_rate = step_rate
		self.entity_types = entity_types
		self.time = 0
		self.running = False
		self.clock = clock
		if start:
			self.start()
	
	def __getattr__(self, name):
		"""Return a world-wrapped entity type for the given name"""
		try:
			entity_type = self.entity_types[name]
		except KeyError:
			raise AttributeError(name)
		wrapped_type = type(name, (_WorldWrappedEntity, entity_type), 
			{'world': self, 'entities': set(), '__register__': False})
		setattr(self, name, wrapped_type)
		return wrapped_type
	
	def step(self, dt):
		"""Execute a time step for the world. Updates the world time
		and invokes the world's systems.

		Note that the specified time delta will be pinned to 10x the
		configured step rate. For example if the step rate is 60,
		then dt will be pinned at a maximum of 0.1666. This avoids 
		pathological behavior when the time between steps goes
		much longer than expected.
		"""
		dt = min(dt, 10.0 / self.step_rate)
		self.time += dt
		self.systems.step(dt)
	
	def _set_renderers(self, renderers):
		self._renderers = tuple(renderers)
		for renderer in self._renderers:
			if hasattr(renderer, 'set_world'):
				renderer.set_world(self)
	
	def _get_renderers(self):
		return self._renderers
	
	renderers = property(_get_renderers, _set_renderers, None, 'World entity pipeline')
	
	def on_draw(self, gl=pyglet.gl):
		"""On draw handler for this world's window"""
		if self.window is not None:
			self.window.clear() # XXX this only clears color and depth buffers by default
		gl.glLoadIdentity()
		for renderer in self.renderers:
			renderer.draw()

	def start(self):
		"""Start stepping the world at the configured step rate"""
		if not self.running:
			self.clock.schedule_interval(self.step, 1.0 / self.step_rate)
			self.running = True

	def stop(self):
		"""Stop stepping the world"""
		self.clock.unschedule(self.step)
		self.running = False


class _WorldWrappedEntity(object):
	"""Entity type in world-context. This fronts for a user-defined 
	Entity class and ensures new instances are added to the world
	automatically
	"""

	__slots__ = ['entity_id']

	entities = None # Replaced by an entity set during wrapping
	
	def __new__(cls, *args, **kw):
		entity = object.__new__(cls)
		entity.entity_id = cls.world.new_entity_id()
		return entity
	
	def __init__(self, *args, **kw):
		super(_WorldWrappedEntity, self).__init__(*args, **kw)
		self.world.entities.add(self)
		self.entities.add(self)

	@classmethod
	def from_existing_id(cls, entity_id):
		"""Return an entity facade for an existing entity_id"""
		assert cls.world is not None, (
			"%(__name__)s cannot be created outside of a world." % cls.__dict__)
		entity = object.__new__(cls)
		entity.entity_id = entity_id
		return entity
	
	@property
	def exists(self):
		"""Return true if the entity still exists in the world"""
		return self in self.world.entities


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
			entities = components[0].entities
			for comp in components[1:]:
				entities &= comp.entities
			for entity in entities:
				yield tuple(comp[entity] for comp in components)


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

