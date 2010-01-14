

class EntityData(object):
	"""Base class for entity data returned from a component. These
	objects are implemented as flyweights for efficiency. Instances
	can be persisted in components directly but it may be more
	efficient to use them as proxies for "dense" data structures in the
	component.

	EntityData objects are hashable and comparable, which is
	necessary for compatibility with EntityDataSet.

	You may implement your own entity data types without subclassing
	this, the only requirement is that it has a (read-only) entity_id
	attribute. If the entity data attributes are fixed, you could
	gain some space efficiency by implementing your own class and
	declaring __slots__
	"""

	__entity_data_pool = []
	__max_pool_size = 50
	__next_entity_data = None

	def __new__(cls, entity_id, **data):
		if cls.__entity_data_pool:
			obj = cls.__entity_data_pool.pop()
		else:
			obj = super(EntityData, cls).__new__(cls)
		obj.__dict__.update(data)
		obj.__entity_id = entity_id
	
	def __del__(self):
		if self.__entity_pool_size < self.__max_pool_size:
			self.__dict__.clear()
			self.__entity_data_pool.append(self)
	
	@property
	def entity_id(self):
		return self.__entity_id

	def hash(self):
		return hash(self.__entity_id)
	
	def __eq__(self, other):
		# Strictly speaking, __dict__ contains the entity id, so we are
		# comparing it twice here, but we do so just in case a subclass
		# overrides entity_id using something not in __dict__
		return (self.__class__ is other.__class__ 
			and self.entity_id == other.entity_id
			and self.__dict__ == other.__dict__)


