"""
**Grease collision detection systems**

Grease uses two-phase broad and narrow collision detection. *Broad-phase*
collision systems are used to efficiently identify pairs that may be colliding
without resorting to a brute-force check of all possible pairs. *Narrow-phase*
collision systems use the pairs generated by the broad-phase and perform more
precise collision tests to determine if a collision has actually occurred. The
narrow-phase system also calculates more details about each collision,
including collision point and normal vector for use in collision response.

A typical collision detection system consists of a narrow-phase system that
contains a broad-phased system. The narrow-phase system is usually the only
one that the application directly interacts with, though the application is
free to use the broad-phased system directly if desired. This could be
useful in cases where speed, rather than precision is paramount.

Note that broad-phase systems can return false positives, though they should
never return false negatives. Do not assume that all pairs returned by a
broad-phase system are actually in collision.
"""

from grease.geometry import Vec2d
from bisect import bisect_right


class Pair(tuple):
	"""Collision pair. An ordered sequence of two entities, that
	compares and hashes unordered.
	
	Also stores additional collision point and normal vectors
	for each entity.
	"""
	info = None
	"""A sequence of (entity, collision point, collision normal)
	for each entity in the pair
	"""

	def __new__(cls, entity1, entity2, point=None, normal=None):
		pair = tuple.__new__(cls, (entity1, entity2))
		return pair
	
	def __hash__(self):
		return hash(self[0]) ^ hash(self[1])
	
	def __eq__(self, other):
		other = tuple(other)
		return tuple(self) == other or (self[1], self[0]) == other
	
	def __repr__(self):
		return '%s%r' % (self.__class__.__name__, tuple(self))
	
	def set_point_normal(self, point0, normal0, point1, normal1):
		"""Set the collision point and normal for both entities"""
		self.info = (
			(self[0], point0, normal0),
			(self[1], point1, normal1),
		)


class BroadSweepAndPrune(object):
	"""2D Broad-phase sweep and prune bounding box collision detection

	This algorithm is efficient for collision detection between many
	moving bodies. It has linear algorithmic complexity and takes
	advantage of temporal coherence between frames. It also does
	not suffer from bad worst-case performance (like RDC can). 
	Unlike spacial hashing, it does not need to be optimized for 
	specific space and body sizes.

	Other algorithms may be more efficient for collision detection with
	stationary bodies, bodies that are always evenly distributed, or ad-hoc
	queries.
	"""
	world = None
	""":class:`grease.World` object this system belongs to"""

	collision_component = None
	"""Name of world's collision component used by this system"""

	LEFT_ATTR = "left"
	RIGHT_ATTR = "right"
	TOP_ATTR = "top"
	BOTTOM_ATTR = "bottom"

	def __init__(self, collision_component='collision'):
		self.collision_component = collision_component
		self._by_x = None
		self._by_y = None
		self._collision_pairs = None
	
	def set_world(self, world):
		"""Bind the system to a world"""
		self.world = world
	
	def step(self, dt):
		"""Update the system for this time step, updates and sorts the 
		axis arrays
		"""
		component = self.world.components[self.collision_component]
		LEFT = self.LEFT_ATTR
		RIGHT = self.RIGHT_ATTR
		TOP = self.TOP_ATTR
		BOTTOM = self.BOTTOM_ATTR
		if self._by_x is None:
			# Build axis lists from scratch
			# Note we cache the box positions here
			# so that we can perform hit tests efficiently
			# it also isolates us from changes made to the 
			# box positions after we run
			by_x = self._by_x = []
			append_x = by_x.append
			by_y = self._by_y = []
			append_y = by_y.append
			for data in component.itervalues():
				append_x([data.AABB.left, LEFT, data])
				append_x([data.AABB.right, RIGHT, data])
				append_y([data.AABB.bottom, BOTTOM, data])
				append_y([data.AABB.top, TOP, data])
		else:
			by_x = self._by_x
			by_y = self._by_y
			removed = []
			for entry in by_x:
				entry[0] = getattr(entry[2].AABB, entry[1])
			for entry in by_y:
				entry[0] = getattr(entry[2].AABB, entry[1])
			# Removing entities is inefficient, but expected to be rare
			if component.deleted_entities:
				deleted_entities = component.deleted_entities
				deleted_x = []
				deleted_y = []
				for i, (_, _, data) in enumerate(by_x):
					if data.entity in deleted_entities:
						deleted_x.append(i)
				deleted_x.reverse()
				for i in deleted_x:
					del by_x[i]
				for i, (_, _, data) in enumerate(by_y):
					if data.entity in deleted_entities:
						deleted_y.append(i)
				deleted_y.reverse()
				for i in deleted_y:
					del by_y[i]
			# Tack on new entities
			for entity in component.new_entities:
				data = component[entity]
				by_x.append([data.AABB.left, LEFT, data])
				by_x.append([data.AABB.right, RIGHT, data])
				by_y.append([data.AABB.bottom, BOTTOM, data])
				by_y.append([data.AABB.top, TOP, data])
				
		# Tim-sort is highly efficient with mostly sorted lists.
		# Because positions tend to change little each frame
		# we take advantage of this here. Obviously things are
		# less efficient with very fast moving, or teleporting entities
		by_x.sort()
		by_y.sort()
		self._collision_pairs = None
	
	@property
	def collision_pairs(self):
		"""Candidate collision pairs for this timestep"""
		if self._collision_pairs is None:
			if self._by_x is None:
				# Axis arrays not ready
				return set()

			LEFT = self.LEFT_ATTR
			RIGHT = self.RIGHT_ATTR
			TOP = self.TOP_ATTR
			BOTTOM = self.BOTTOM_ATTR
			# Build candidates overlapping along the x-axis
			component = self.world.components[self.collision_component]
			xoverlaps = set()
			add_xoverlap = xoverlaps.add
			discard_xoverlap = xoverlaps.discard
			open = set()
			add_open = open.add
			discard_open = open.discard
			for _, side, data in self._by_x:
				if side is LEFT:
					for open_entity in open:
						add_xoverlap(Pair(data.entity, open_entity))
					add_open(data.entity)
				elif side is RIGHT:
					discard_open(data.entity)

			if len(xoverlaps) <= 10 and len(xoverlaps)*4 < len(self._by_y):
				# few candidates were found, so just scan the x overlap candidates
				# along y. This requires an additional sort, but it should
				# be cheaper than scanning everyone and its simpler
				# than a separate brute-force check
				entities = set([entity for entity, _ in xoverlaps] 
					+ [entity for _, entity in xoverlaps])
				by_y = []
				for entity in entities:
					data = component[entity]
					# We can use tuples here, which are cheaper to create
					by_y.append((data.AABB.bottom, BOTTOM, data))
					by_y.append((data.AABB.top, TOP, data))
				by_y.sort()
			else:
				by_y = self._by_y

			# Now check the candidates along the y-axis
			open.clear()
			self._collision_pairs = set()
			add_pair = self._collision_pairs.add
			for _, side, data in by_y:
				if side is BOTTOM:
					for open_entity in open:
						pair = Pair(data.entity, open_entity)
						if pair in xoverlaps:
							discard_xoverlap(pair)
							add_pair(pair)
							if not xoverlaps:
								# No more candidates, bail
								return self._collision_pairs
					add_open(data.entity)
				elif side is TOP:
					discard_open(data.entity)
		return self._collision_pairs
	
	def query_point(self, x_or_point, y=None):
		"""Hit test at the point specified. Return a set of entities
		where the point is inside their bounding boxes as of the last
		time step.

		Args:
			x_or_point: x coordinate (float) or sequence of (x, y) floats.

			y: y coordinate (float) if x is not a sequence

		"""
		if self._by_x is None:
			# Axis arrays not ready
			return set()
		if y is None:
			x, y = x_or_point
		else:
			x = x_or_point
		LEFT = self.LEFT_ATTR
		RIGHT = self.RIGHT_ATTR
		TOP = self.TOP_ATTR
		BOTTOM = self.BOTTOM_ATTR
		x_index = bisect_right(self._by_x, [x])
		x_hits = set()
		add_x_hit = x_hits.add
		discard_x_hit = x_hits.discard
		if x_index <= len(self._by_x) // 2:
			# closer to the left, scan from left to right
			while (x == self._by_x[x_index][0] 
				and self._by_x[x_index][1] is LEFT 
				and x_index < len(self._by_x)):
				# Ensure we hit on exact left edge matches
				x_index += 1
			for _, side, data in self._by_x[:x_index]:
				if side is LEFT:
					add_x_hit(data.entity)
				else:
					discard_x_hit(data.entity)
		else:
			# closer to the right
			for _, side, data in reversed(self._by_x[x_index:]):
				if side is RIGHT:
					add_x_hit(data.entity)
				else:
					discard_x_hit(data.entity)
		if not x_hits:
			return x_hits

		y_index = bisect_right(self._by_y, [y])
		y_hits = set()
		add_y_hit = y_hits.add
		discard_y_hit = y_hits.discard
		if y_index <= len(self._by_y) // 2:
			# closer to the bottom
			while (y == self._by_y[y_index][0] 
				and self._by_y[y_index][1] is BOTTOM 
				and y_index < len(self._by_y)):
				# Ensure we hit on exact bottom edge matches
				y_index += 1
			for _, side, data in self._by_y[:y_index]:
				if side is BOTTOM:
					add_y_hit(data.entity)
				else:
					discard_y_hit(data.entity)
		else:
			# closer to the top
			for _, side, data in reversed(self._by_y[y_index:]):
				if side is TOP:
					add_y_hit(data.entity)
				else:
					discard_y_hit(data.entity)
		if y_hits:
			return x_hits & y_hits
		else:
			return y_hits


class Circular(object):
	"""Basic narrow-phase collision detection system which treats all entities as
	circles with their radius defined in the collision component.

	Args:
		collision_component: Name of collision component for this system,
			defaults to 'collision'. This supplies each entity's collision
			radius.

		position_component: Name of position component for this system,
			defaults to 'position'. This supplies each entity's position.

		broad_phase: A broad-phase collision system to use as a source
			for collision pairs. If not specified, a :class:`BroadSweepAndPrune`
			system will be created automatically.
	"""
	world = None
	""":class:`grease.World` object this system belongs to"""

	position_component = None
	"""Name of world's position component used by this system"""

	collision_component = None
	"""Name of world's collision component used by this system"""

	broad_phase = None
	"""Broad phase collision system used as a source for collision pairs"""

	def __init__(self, position_component='position', collision_component='collision', 
		broad_phase=None):
		if broad_phase is None:
			broad_phase = BroadSweepAndPrune(collision_component)
		self.collision_component = collision_component
		self.position_component = position_component
		self.broad_phase = broad_phase
		self._collision_pairs = None
	
	def set_world(self, world):
		"""Bind the system to a world"""
		self.world = world
	
	def step(self, dt):
		"""Update the collision system for this time step"""
		self.broad_phase.step(dt)
		self._collision_pairs = None
	
	@property
	def collision_pairs(self):
		"""The set of entity pairs in collision in this timestep"""
		if self._collision_pairs is None:
			position = self.world.components[self.position_component]
			collision = self.world.components[self.collision_component]
			pairs = self._collision_pairs = set()
			for pair in self.broad_phase.collision_pairs:
				entity1, entity2 = pair
				position1 = position[entity1].position
				position2 = position[entity2].position
				radius1 = collision[entity1].radius
				radius2 = collision[entity2].radius
				separation = position2 - position1
				if separation.get_length_sqrd() <= (radius1 + radius2)**2:
					normal = separation.normalized()
					pair.set_point_normal(
						normal * radius1 + position1, normal,
						normal * -radius2 + position2, -normal)
					pairs.add(pair)
		return self._collision_pairs
	
	def query_point(self, x_or_point, y=None):
		"""Hit test at the point specified. Return a set of entities
		where the point is inside their collision radii as of the last
		time step.

		Args:
			x_or_point: x coordinate (float) or sequence of (x, y) floats.

			y: y coordinate (float) if x is not a sequence

		"""
		if y is None:
			point = Vec2d(x_or_point)
		else:
			point = Vec2d(x_or_point, y)
		hits = set()
		position = self.world.components[self.position_component]
		collision = self.world.components[self.collision_component]
		for entity in self.broad_phase.query_point(x_or_point, y):
			separation = point - position[entity].position
			if separation.get_length_sqrd() <= collision[entity].radius**2:
				hits.add(entity)
		return hits

