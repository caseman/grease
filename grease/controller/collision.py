from bisect import bisect_right

class SAPCollision(object):
	"""2D Broad-phase sweep and prune bounding box collision detection

	This algorithm is efficient for collision detection between many
	moving bodies. It has linear algorithmic complexity and takes
	advantage of temporal coherence between frames. It also does
	not suffer from bad worst-case performance (like RDC can). 
	Unlike spacial hashing, it does not need to be optimized for 
	specific space and body sizes.

	Other algorithms may be more efficient for collision detection with
	stationary bodies, or bodies that are always evenly distributed.
	"""

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
		"""Update and sort the axis arrays"""
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
		"""Return the current collision pairs, recalculating as needed"""
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
		"""Hit test at the point specified. Return a set of entity ids
		where the point is inside their bounding boxes as of the last
		run() invocation.
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


class Pair(frozenset):
	"""Unordered pair of objects"""

	def __new__(cls, obj1, obj2):
		return frozenset.__new__(cls, (obj1, obj2))
	
	def __repr__(self):
		return '%s(%r, %r)' % (self.__class__.__name__, self[0], self[1])

