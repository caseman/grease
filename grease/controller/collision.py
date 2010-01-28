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
	
	def add_manager(self, manager):
		self.manager = manager
	
	def run(self, dt):
		"""Update and sort the axis arrays"""
		component = self.manager.components[self.collision_component]
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
			by_y = self._by_y = []
			for data in component:
				by_x.append([data.AABB.left, data, LEFT])
				by_x.append([data.AABB.right, data, RIGHT])
				by_y.append([data.AABB.bottom, data, BOTTOM])
				by_y.append([data.AABB.top, data, TOP])
		else:
			by_x = self._by_x
			by_y = self._by_y
			removed = []
			for entry in by_x:
				entry[0] = getattr(entry[1].AABB, entry[2])
			for entry in by_y:
				entry[0] = getattr(entry[1].AABB, entry[2])
			# Removing entities is inefficient, but expected to be rare
			if component.deleted_entity_ids:
				deleted_ids = component.deleted_entity_ids
				deleted_x = []
				deleted_y = []
				for i, (_, box, _) in enumerate(by_x):
					if box.entity_id in deleted_ids:
						deleted_x.append(i)
				deleted_x.reverse()
				for i in deleted_x:
					del by_x[i]
				for i, (_, box, _) in enumerate(by_y):
					if box.entity_id in deleted_ids:
						deleted_y.append(i)
				deleted_y.reverse()
				for i in deleted_y:
					del by_y[i]
			# Tack on new entities
			for id in component.new_entity_ids:
				data = component[id]
				by_x.append([data.AABB.left, data, LEFT])
				by_x.append([data.AABB.right, data, RIGHT])
				by_y.append([data.AABB.bottom, data, BOTTOM])
				by_y.append([data.AABB.top, data, TOP])
				
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
			component = self.manager.components[self.collision_component]
			xoverlaps = set()
			add_xoverlap = xoverlaps.add
			discard_xoverlap = xoverlaps.discard
			open = set()
			add_open = open.add
			discard_open = open.discard
			for _, data, side in self._by_x:
				if side is LEFT:
					for open_id in open:
						add_xoverlap((data.entity_id, open_id))
					add_open(data.entity_id)
				elif side is RIGHT:
					discard_open(data.entity_id)

			if len(xoverlaps) <= 10 and len(xoverlaps)*4 < len(self._by_y):
				# few candidates were found, so just scan the x overlap candidates
				# along y. This requires an additional sort, but it should
				# be cheaper than scanning everyone and its simpler
				# than a separate brute-force check
				ids = set([id for id, _ in xoverlaps] + [id for _, id in xoverlaps])
				by_y = []
				for id in ids:
					data = component[id]
					# We can use tuples here, which are cheaper to create
					by_y.append((data.AABB.bottom, data, BOTTOM))
					by_y.append((data.AABB.top, data, TOP))
				by_y.sort()

			# Now check the candidates along the y-axis
			open.clear()
			self._collision_pairs = set()
			add_pair = self._collision_pairs.add
			for _, data, side in by_y:
				if side is BOTTOM:
					for open_id in open:
						pair = (data.entity_id, open_id)
						if discard_xoverlap(pair):
							add_pair(pair)
							if not xoverlaps:
								# No more candidates, bail
								return self._collision_pairs
					add_open(data.entity_id)
				elif side is TOP:
					discard_open(id)
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
			for x, data, side in self._by_x[:x_index]:
				if side is LEFT:
					add_x_hit(data.entity_id)
				else:
					discard_x_hit(data.entity_id)
		else:
			# closer to the right
			while x_index > 0 and x == self._by_x[x_index][0]:
				# Ensure we don't miss exact hits to the left
				# These should be rare, but would result in
				# a false negative
				x_index -= 1
			for x, data, side in reversed(self._by_x[x_index:]):
				if side is RIGHT:
					add_x_hit(data.entity_id)
				else:
					discard_x_hit(data.entity_id)
		if not x_hits:
			return x_hits

		y_index = bisect_right(self._by_y, [y])
		y_hits = set()
		add_y_hit = hits.add
		discard_y_hit = hits.discard
		if y_index <= len(self._by_y) // 2:
			# closer to the bottom
			for y, data, side in self._by_y[:y_index]:
				if side is BOTTOM:
					add_y_hit(data.entity_id)
				else:
					discard_y_hit(data.entity_id)
		else:
			# closer to the top
			while y_index > 0 and y == self._by_x[y_index][0]:
				# Ensure we don't miss exact hits to the bottom
				y_index -= 1
			for y, data, side in reversed(self._by_y[y_index:]):
				if side is TOP:
					add_y_hit(data.entity_id)
				else:
					discard_y_hit(data.entity_id)
		if y_hits:
			return x_hits & y_hits
		else:
			return y_hits


