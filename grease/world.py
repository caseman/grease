import itertools
import pyglet
from pyglet import gl
from grease import mode
from grease.component import ComponentError
from grease.entity import Entity, ComponentEntitySet


class World(mode.Mode):
	"""A coordinated collection of components, systems and entities
	
	A world is also a mode that may be pushed onto a 
	:class:`grease.mode.Manager`

	Args:
		`step_rate`: The rate of `step()` calls per second. 

		`master_clock`: The :class:`pyglet.clock.Clock` interface used
			as the master clock that ticks the world's clock. This 
			defaults to the main pyglet clock.
	"""

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
	"""Current clock time of the world"""

	running = True
	"""Flag to indicate that the world clock is running, advancing time
	and stepping the world. Set running to False to pause the world.
	"""

	def __init__(self, step_rate=60, master_clock=pyglet.clock,
		         clock_factory=pyglet.clock.Clock):
		super(World, self).__init__(step_rate, master_clock, clock_factory)
		self.components = ComponentMapper(self)
		self.systems = SystemMap(self)
		self._renderers = ()
		self.new_entity_id = itertools.count().next
		self.new_entity_id() # skip id 0
		self.entities = WorldEntitySet(self)
		self._full_extent = EntityExtent(self, self.entities)
		self._extents = {}
		self.configure()

	def configure(self):
		"""Hook to configure the world after construction. Override
		in a subclass to configure the world's components, systems,
		and renderers.

		The default implementation does nothing.
		"""
		
	def _set_renderers(self, renderers):
		self._renderers = tuple(renderers)
		for renderer in self._renderers:
			if hasattr(renderer, 'set_world'):
				renderer.set_world(self)
	
	def _get_renderers(self):
		return self._renderers
	
	renderers = property(_get_renderers, _set_renderers,
		doc="""A sequence of renderers. Renderers define the presentation
		of the world""")
	
	def __getitem__(self, entity_class):
		"""Return an entity extent for the given entity class. This extent
		can be used to access the set of entities of that class in the world
		or to query these entities via their components. 

		`entity_class` may also be a tuple of entity classes, in which case
		the extent returned contains union of all entities of the classes
		in the world.

		`entity_class` may also be the special value ellipsis (...), which
		returns an extent containing all entities in the world.  This allows
		you to conveniently query all entities using `world[...]`.
		"""
		if isinstance(entity_class, tuple):
			entities = set()
			for cls in entity_class:
				if cls in self._extents:
					entities |= self._extents[cls].entities
			return EntityExtent(self, entities)
		elif entity_class is Ellipsis:
			return self._full_extent
		try:
			return self._extents[entity_class]
		except KeyError:
			extent = self._extents[entity_class] = EntityExtent(self, set())
			return extent
		
	def activate(self, manager):
		"""Activate the mode for the given manager, if the mode is already active, 
		do nothing

		The systems of the world are pushed onto `manager.event_dispatcher`
		so they can receive system events.
		"""
		if not self.active:
			for system in self.systems:
				manager.event_dispatcher.push_handlers(system)
		super(World, self).activate(manager)
	
	def deactivate(self, manager):
		"""Deactivate the mode, if the mode is not active, do nothing

		Removes the system handlers from the `manager.event_dispatcher`
		"""
		for system in self.systems:
			manager.event_dispatcher.remove_handlers(system)
		super(World, self).deactivate(manager)

	def tick(self, dt):
		"""Tick the mode's clock, but only if the world is currently running"""
		if self.running:
			super(World, self).tick(dt)
	
	def step(self, dt):
		"""Execute a time step for the world. Updates the world `time`
		and invokes the world's systems.
		
		Note that the specified time delta will be pinned to 10x the
		configured step rate. For example if the step rate is 60,
		then dt will be pinned at a maximum of 0.1666. This avoids 
		pathological behavior when the time between steps goes
		much longer than expected.
		"""
		dt = min(dt, 10.0 / self.step_rate)
		self.components.step(dt)
		self.systems.step(dt)

	def on_draw(self, gl=pyglet.gl):
		"""Clear the current OpenGL context, reset the model/view matrix and
		invoke the `draw()` methods of the renderers in order
		"""
		gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
		gl.glLoadIdentity()
		for renderer in self.renderers:
			renderer.draw()


class WorldEntitySet(set):
	"""Entity set for a :class:`World`"""

	def __init__(self, world):
		self.world = world
	
	def add(self, entity):
		"""Add the entity to the set and all necessary class sets
		Return the unique entity id for the entity, creating one
		as needed.
		"""
		super(WorldEntitySet, self).add(entity)
		for cls in entity.__class__.__mro__:
			if issubclass(cls, Entity):
				self.world[cls].entities.add(entity)

	def remove(self, entity):
		"""Remove the entity from the set and, world components,
		and all necessary class sets
		"""
		super(WorldEntitySet, self).remove(entity)
		for component in self.world.components.itervalues():
			try:
				del component[entity]
			except KeyError:
				pass
		for cls in entity.__class__.__mro__:
			if issubclass(cls, Entity):
				self.world[cls].entities.discard(entity)
	
	def discard(self, entity):
		"""Remove the entity from the set if it exists, if not,
		do nothing
		"""
		try:
			self.remove(entity)
		except KeyError:
			pass


class EntityExtent(object):
	"""Encapsulates a set of entities queriable by component"""

	entities = None
	"""The full set of entities in the extent""" 

	def __init__(self, world, entities):
		self.__world = world
		self.entities = entities

	def __getattr__(self, name):
		"""Access a component for the set of entities for querying"""
		try:
			component = self.__world.components[name]
		except KeyError:
			raise AttributeError("No such component: %s" % name)
		return ComponentEntitySet(component, self.entities & component.entities)


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
	
	def __iadd__(self, named_system):
		"""Add a system in place"""
		self.add(named_system)
		return self

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

