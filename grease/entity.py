
class EntityMeta(type):
	"""The entity metaclass enforces fixed slots of `entity_id` and `world`
	for all subclasses. This prevents accidental use of other entity instance 
	attributes, which may not be saved. 
	
	Class attributes are not affected by this restriction, but subclasses
	should be careful not to cause name collisions with world components,
	which are exposed as entity attributes. Using a naming convention for
	class attributes, such as UPPER_CASE_WITH_UNDERSCORES is recommended to
	avoid name clashes.

	Note as a result of this, entity subclasses are not allowed to define
	`__slots__`, and doing so will cause a `TypeError` to be raised.
	"""

	def __new__(cls, name, bases, clsdict):
		if '__slots__' in clsdict:
			raise TypeError('__slots__ may not be defined in Entity subclasses')
		clsdict['__slots__'] = ('world', 'entity_id')
		return type.__new__(cls, name, bases, clsdict)


class Entity(object):
	"""Base class for grease entities.
	
	Entity objects themselves are actually just a facade for convient access
	of component data for a single entity, they do not contain any data
	themselves other than an entity id.

	Entities must be instantiated in the context of a world. To instantiate an
	entity, you must pass the world as the first argument to the constructor.
	Subclasses that implement the `__init__()` method, must accept the world
	as their first argument (after `self`). Other constructor arguments can be
	specified arbitarily by the subclass.

	Attributes:
		`world`: The :class:`grease.World` object that this entity belongs to

		`entity_id`: Unique entity identifier
	"""
	__metaclass__ = EntityMeta

	def __new__(cls, world, *args, **kw):
		"""Create a new entity and add it to the world"""
		entity = object.__new__(cls)
		entity.world = world
		entity.entity_id = world.new_entity_id()
		world.entities.add(entity)
		return entity
	
	def __getattr__(self, name):
		"""Return a component accessor for this entity"""
		component = getattr(self.world.components, name)
		return EntityComponentAccessor(component, self)
	
	def __setattr__(self, name, value):
		if name in self.__class__.__slots__:
			super(Entity, self).__setattr__(name, value)
		else:
			component = getattr(self.world.components, name)
			component.set(self, value)
	
	def __delattr__(self, name):
		"""Remove the data for this entity from the component"""
		component = getattr(self.world.components, name)
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
		self.world.entities.discard(self)

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
	
	def __nonzero__(self):
		"""The accessor is True if the entity is in the component,
		False if not, for convenient membership tests
		"""
		return self.__entity in self.__component
	
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

