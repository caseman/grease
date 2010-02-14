import warnings

# Mapping of defined entity types, managed by the EntityTypeRegistrar
# and used by World objects
entity_types = {}

class EntityTypeRegistrar(type):
	"""Simple entity metaclass that registers entity types
	so they can be access from World instances for context
	wrapping.
	"""

	def __new__(cls, name, bases, clsdict):
		newcls = type.__new__(cls, name, bases, clsdict)
		if clsdict.get('__register__', True):
			if name not in entity_types:
				entity_types[name] = newcls
			else:
				warnings.warn("duplicate Entity class name: %s. "
					"Only the original class with that name will be "
					"available for instantiation via worlds." % name)
		return newcls
	
	def __getattr__(cls, name):
		"""Class getattr hook to provide access to components for
		the extent of a given classes entities
		"""
		try:
			component = cls.world.components[name]
		except KeyError:
			raise AttributeError("No such component: %s" % name)
		return ComponentEntitySet(component, cls.entities & component.entities)


class Entity(object):
	"""Base class for grease entities.
	
	Entity objects themselves are actually just a facade for convient access
	of component data for a single entity, they do not contain any data
	themselves other than an entity id.

	You cannot instantiate an Entity class directly, entities must be
	instantiated in the context of a world. Subclasses of Entity are
	automatically registered with grease so that they can be accessed as
	attributes of any World instance. When accessed as attributes of a world,
	the Entity class is automatically put into the context of that world so
	that it can be instantiated, e.g.:

	entity = my_world.Entity()
	"""

	__metaclass__ = EntityTypeRegistrar

	# Set this flag to False in a subclass to disable
	# automatic registration for this entity type. This
	# can be useful for abstract base classes to avoid
	# namespace pollution
	__register__ = True

	# class attributes set by the metaclass
	world = None
	__baseclass__ = None

	def __new__(cls, *args, **kw):
		"""Create a new entity and add it to the world"""
		if cls.world is None:
			raise RuntimeError(
				"Cannot instantiate %s outside of a world. Try using world.%s(...)" 
				% (cls.__name__, cls.__name__))
		entity = object.__new__(cls)
		entity.entity_id = cls.world.new_entity_id()
		cls.world.entities.add(entity)
		for clsname in cls.world.entity_types:
			entity_cls = getattr(cls.world, clsname)
			if issubclass(cls.__baseclass__, entity_cls.__baseclass__):
				entity_cls.entities.add(entity)
		return entity
	
	def __getattr__(self, name):
		"""Return a component accessor for this entity"""
		try:
			component = self.world.components[name]
		except KeyError:
			raise AttributeError("No such component: %s" % name)
		return EntityComponentAccessor(component, self)
	
	def __setattr__(self, name, value):
		if name == 'entity_id':
			super(Entity, self).__setattr__(name, value)
		else:
			try:
				component = self.world.components[name]
			except KeyError:
				raise AttributeError("No such component: %s" % name)
			component.set(self, value)
	
	def __delattr__(self, name):
		"""Remove the data for this entity from the component"""
		try:
			component = self.world.components[name]
		except KeyError:
			raise AttributeError("No such component: %s" % name)
		del component[self]
	
	def __hash__(self):
		return self.entity_id
	
	def __eq__(self, other):
		return self.world is other.world and self.entity_id == other.entity_id

	def __repr__(self):
		return "<%s id: %s of %s %x>" % (
			self.__class__.__name__, self.entity_id,
			self.world.__class__.__name__, id(self.world))

	def delete(self):
		"""Delete the entity from its world. If then entity has already
		been deleted, this call does nothing
		"""
		for clsname in self.world.entity_types:
			cls = getattr(self.world, clsname)
			if issubclass(self.__baseclass__, cls.__baseclass__):
				try:
					cls.entities.remove(self)
				except KeyError:
					pass
		try:
			self.world.entities.remove(self)
		except KeyError:
			pass

	@property
	def exists(self):
		"""Return true if the entity still exists in the world"""
		return self in self.world.entities


class EntityComponentAccessor(object):
	"""A facade for accessing specific component data for a single entity.
	The implementation is lazy and does not actually access the component
	data until needed. If an attribute is set for a component that the 
	entity is not yet a member of, it is automatically added to the
	component first.
	"""
	
	# beware, name mangling ahead. We want to avoid clashing with any
	# user-configured component field names
	__data = None

	def __init__(self, component, entity):
		clsname = self.__class__.__name__
		self.__dict__['_%s__component' % clsname] = component
		self.__dict__['_%s__entity' % clsname] = entity
	
	def __getattr__(self, name):
		if self.__data is None:
			try:
				data = self.__component[self.__entity]
			except KeyError:
				raise AttributeError(name)
			clsname = self.__class__.__name__
			self.__dict__['_%s__data' % clsname] = data
		return getattr(self.__data, name)
	
	def __setattr__(self, name, value):
		if self.__data is None:
			clsname = self.__class__.__name__
			if self.__entity in self.__component:
				self.__dict__['_%s__data' % clsname] = self.__component[self.__entity]
			else:
				self.__dict__['_%s__data' % clsname] = self.__component.set(self.__entity)
		setattr(self.__data, name, value)


class ComponentEntitySet(set):
	"""set of entities in a component, can be queried by component fields"""

	_component = None

	def __init__(self, component, entities=()):
		self.__dict__['_component'] = component
		super(ComponentEntitySet, self).__init__(entities)
	
	def __getattr__(self, name):
		if self._component is not None and name in self._component.fields:
			return self._component.fields[name].accessor(self)
		raise AttributeError(name)
	
	def __setattr__(self, name, value):
		if self._component is not None and name in self._component.fields:
			self._component.fields[name].accessor(self).__set__(value)
		raise AttributeError(name)

