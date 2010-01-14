class ComponentBase(object):
	"""Component abstract base class

	Strictly speaking you do not need to derive from this class to create your
	own components, but it does serve to document the full interface that a
	component implements and it provides some basic implementations for
	certain methods
	"""

	## Optional attributes and methods ##

	def set_manager(self, manager):
		"""Set the manager of this component. If this method exists it will be
		automatically called when the component is added to a manager.

		This method stores the manager and allows the component to be added
		only once to a single manager.
		"""
		assert getattr(self, 'manager', None) is None, 'Component cannot be added to multiple managers'
		self.manager = manager

	def __del__(self):
		"""Break circrefs to allow faster collection"""
		if hasattr(self, 'manager'):
			del self.manager
	
	## Mandatory methods ##

	def add(self, entity_id, data=None, **data_kw):
		"""Add a data entry in the component for the given entity.  Additional
		data (if any) for the entry can be provided in the data argument or as
		keyword arguments. Additional data is optional and if omitted then
		suitable defaults will be used. Return an entity data object
		for the new entity entry.

		The semantics of the data arguments is up to the component.

		An entity_id is a unique key, thus multiple separate data entries for
		a given entity are not allowed.  Components can indivdually decide
		what to do if an entity_id is added multiple times to the component.
		Potential options include, raising an exception, replacing the
		existing data or coalescing it somehow.
		"""
	
	def remove(self, entity_id):
		"""Remove the entity data entry from the component. If the
		entity is not in the component, raise KeyError
		"""
	
	def __delitem_(self, entity_id):
		"""Same as remove()"""

	def __len__(self):
		"""Return the number of entities in the component"""
		raise NotImplementedError()
	
	def __iter__(self):
		"""Return an iterator of entity data objects in this component

		No order is defined for these data objects
		"""
		raise NotImplementedError()
	
	def __contains__(self, entity_id):
		"""Return True if the entity is contained in the component"""
		raise NotImplementedError()
	
	def __getitem__(self, entity_id):
		"""Return the entity data object for the given entity. 
		The entity data object returned may be mutable, immutable or a
		mutable copy of the data at the discretion of the component
		"""
		raise NotImplementedError()

