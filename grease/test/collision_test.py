import unittest

class TestCollisionComp(dict):

	def __init__(self):
		self.new_entities = set()
		self.deleted_entities = set()

	def set(self, entity, left=0, bottom=0, right=0, top=0, radius=0,
		from_mask=0xffffffff, into_mask=0xffffffff,):
		if entity in self:
			data = self[entity]
		else:
			data = self[entity] = Data()
		data.entity = entity
		data.aabb = Data(left=left, top=top, right=right, bottom=bottom)
		data.radius = radius
		data.from_mask = from_mask
		data.into_mask = into_mask
		return entity
	
class TestPositionComp(dict):

	def set(self, entity, position):
		from grease.geometry import Vec2d
		if entity in self:
			data = self[entity]
		else:
			data = self[entity] = Data()
		data.entity = entity
		data.position = Vec2d(position)

class TestWorld(object):

	def __init__(self):
		self.components = self
		self.collision = TestCollisionComp()
		self.position = TestPositionComp()
	
	def join(self, *names):
		for entity in getattr(self, names[0]):
			try:
				yield tuple(getattr(self, name)[entity] for name in names)
			except KeyError:
				pass

class Data(object):

	def __init__(self, **kw):
		self.__dict__.update(kw)
	
	def __eq__(self, other):
		return self.__class__ is other.__class__ and self.__dict__ == other.__dict__
	
	def __repr__(self):
		return "Data(%r)" % self.__dict__

class TestCollisionSys(object):

	collision_component = 'collision'

	runtime = 0
	last_from_mask = None

	def __init__(self, pairs=()):
		self.collision_pairs = pairs or set()
	
	def set_world(self, world):
		self.world = world
	
	def step(self, dt):
		self.runtime += dt

	def query_point(self, x, y=None, from_mask=None):
		self.last_from_mask = from_mask
		return set(self.world.collision)


class PairTestCase(unittest.TestCase):

	def test_create_pair(self):
		from grease.collision import Pair
		p = Pair(3, 4)
		self.assertEqual(sorted(p), [3, 4])
		self.assertRaises(TypeError, p, 1, 2, 3)
	
	def test_symmetric_hash(self):
		from grease.collision import Pair
		self.assertEqual(hash(Pair('spam', 'eggs')), hash(Pair('eggs', 'spam')))
	
	def test_unordered_comparison(self):
		from grease.collision import Pair
		self.assertEqual(Pair(42, 24), Pair(24, 42))
	
	def test_pair_set(self):
		from grease.collision import Pair
		p1 = Pair(3,4)
		p2 = Pair(4,5)
		pairs = set([p1, p2])
		self.assertTrue(Pair(3,4) in pairs)
		self.assertTrue(Pair(4,3) in pairs)
		self.assertTrue(Pair(4,5) in pairs)
		self.assertTrue(Pair(5,4) in pairs)
	
	def test_pair_repr(self):
		from grease.collision import Pair
		self.assertEqual(repr(Pair(2,1)), "Pair(2, 1)")


class BroadSweepAndPruneTestCase(unittest.TestCase):

	def test_before_step(self):
		# Queries should be well behaved even before the controller is run
		from grease.collision import BroadSweepAndPrune
		coll = BroadSweepAndPrune()
		self.assertEqual(coll.collision_pairs, set())
		self.assertEqual(coll.query_point(0,0), set())
	
	def test_collision_pairs_no_collision(self):
		from grease.collision import BroadSweepAndPrune
		world = TestWorld()
		coll = BroadSweepAndPrune()
		set_entity = world.collision.set
		set_entity(1, 10, 10, 20, 20)
		set_entity(2, 0, 0, 3, 3)
		set_entity(3, 11, 21, 15, 40)
		set_entity(4, -5, 0, -3, 100)
		coll.set_world(world)
		self.assertTrue(coll.world is world)
		coll.step(0)
		self.assertEqual(coll.collision_pairs, set())
		coll.step(0)
		self.assertEqual(coll.collision_pairs, set())
	
	def assertPairs(self, set1, *pairs):
		pairs = set(pairs)
		self.assertEqual(set1, pairs,
			"%r not found, %r not expected" % (tuple(pairs - set1), tuple(set1 - pairs)))
	
	def test_collision_pairs_static_collision(self):
		from grease.collision import BroadSweepAndPrune, Pair
		world = TestWorld()
		coll = BroadSweepAndPrune()
		coll.set_world(world)
		set_entity = world.collision.set

		set_entity(1, 10, 10, 20, 20)
		set_entity(2, 15, 15, 25, 25)
		set_entity(3, 5, 12, 30, 15)

		# boxes fully enclosed
		set_entity(4, 31, 10, 40, 13)
		set_entity(5, 32, 11, 39, 12)

		set_entity(6, 0, 0, 2, 2)
		set_entity(7, -1, 0.5, 1, 1.5)

		# no collisions with below
		set_entity(8, 2.1, 2.1, 2.2, 2.2)
		set_entity(9, 50, -40, 55, 40)
		set_entity(10, -50, -50, 50, -45) 

		coll.step(0)
		pairs = set(coll.collision_pairs)
		self.assertPairs(pairs, Pair(1,2), Pair(1,3), Pair(2,3), Pair(4,5), Pair(6,7))

		coll.step(0)
		self.assertEqual(coll.collision_pairs, pairs)
	
	def test_collision_pairs_no_collide_then_collide(self):
		from grease.collision import BroadSweepAndPrune, Pair
		world = TestWorld()
		coll = BroadSweepAndPrune()
		coll.set_world(world)
		set_entity = world.collision.set

		# Start with no collisions
		set_entity(1, 0, 0, 10, 10)
		set_entity(2, 7, 12, 9, 13)
		set_entity(3, -2.1, 1, -0.1, 2)
		coll.step(0)
		self.assertEqual(coll.collision_pairs, set())

		# One pair collides
		set_entity(2, 8, 11, 10, 12)
		set_entity(3, -2, 1, 0, 2)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(1,3))

		# Now two pair
		set_entity(2, 9, 10, 11, 11)
		set_entity(3, -1.9, 1, 0.1, 2)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(1,3), Pair(1,2))

		# Same
		set_entity(2, 10, 9, 12, 10)
		set_entity(3, -1.8, 1, 0.2, 2)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(1,3), Pair(1,2))

		# Now just one again
		set_entity(2, 11, 8, 13, 9)
		set_entity(3, -1.7, 1, 0.3, 2)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(1,3))
	
	def test_collision_pairs_new_entities(self):
		from grease.collision import BroadSweepAndPrune, Pair
		world = TestWorld()
		coll = BroadSweepAndPrune()
		coll.set_world(world)
		set_entity = world.collision.set

		# Start with a couple not colliding
		set_entity(1, 1, 1, 3, 3)
		set_entity(2, 4, 0, 10, 3)
		coll.step(0)
		self.assertEqual(coll.collision_pairs, set())

		# Add one that collides, one that doesn't
		set_entity(3, 2, 2, 4, 4)
		set_entity(4, 20, 5, 25, 7)
		world.collision.new_entities.add(3)
		world.collision.new_entities.add(4)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(1,3), Pair(3, 2))

		# Add one more and move one into collision and one out
		set_entity(5, 19, 8, 21, 14)
		set_entity(4, 20, 6, 25, 8)
		set_entity(2, 5, 0, 11, 3)
		world.collision.new_entities.clear()
		world.collision.new_entities.add(5)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(1,3), Pair(4,5))
	
	def test_collision_pairs_deleted_entities(self):
		from grease.collision import BroadSweepAndPrune, Pair
		world = TestWorld()
		coll = BroadSweepAndPrune()
		coll.set_world(world)
		set_entity = world.collision.set

		# Add some colliding pairs
		set_entity(1, 1, 1, 5, 2)
		set_entity(2, 2, 0, 3, 5)
		set_entity(3, 0, 0, 2, 2)
		set_entity(4, 4, 0, 5, 2)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(1,2), Pair(1,3), Pair(2,3), Pair(1,4))

		# Remove one
		world.collision.deleted_entities.add(3)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(1,2), Pair(1,4))

		# Remove another and move one into collision
		world.collision.deleted_entities.clear()
		world.collision.deleted_entities.add(1)
		set_entity(2, 4, 0, 5, 5)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, Pair(4,2))
	
	def test_collision_pairs_with_masks(self):
		from grease.collision import BroadSweepAndPrune, Pair
		world = TestWorld()
		coll = BroadSweepAndPrune()
		coll.set_world(world)
		set_entity = world.collision.set

		set_entity(1, 0, 0, 1, 1, from_mask=1, into_mask=0)
		set_entity(2, 0, 0, 1, 1, from_mask=0, into_mask=2)
		set_entity(3, 0, 0, 1, 1, from_mask=2, into_mask=1)
		set_entity(4, 0, 0, 1, 1, from_mask=0, into_mask=0)
		set_entity(5, 0, 0, 1, 1, from_mask=0xffffffff, into_mask=0xffffffff)
		coll.step(0)
		self.assertPairs(coll.collision_pairs, 
			Pair(1,3), Pair(1,5), Pair(2,3), Pair(2,5), Pair(3,1), Pair(3,5))

	def test_query_point(self):
		from grease.collision import BroadSweepAndPrune, Pair
		world = TestWorld()
		coll = BroadSweepAndPrune()
		coll.set_world(world)
		set_entity = world.collision.set

		set_entity(1, -1, -1, 3, 1)
		set_entity(2, 4, 4, 8, 8)
		set_entity(3, 6, 6, 9, 9)

		# Queries before the first step should always return no hits
		self.assertEqual(coll.query_point(0, 0), set())
		coll.step(0)
		self.assertEqual(coll.query_point(0, 0), set([1]))
		self.assertEqual(coll.query_point([0, 0]), set([1]))

		set_entity(2, 4, 4, 8, 8)
		set_entity(3, 6, 6, 9, 9)
		world.collision.new_entities.add(2)
		world.collision.new_entities.add(3)
		coll.step(0)
		self.assertEqual(coll.query_point(0, 0), set([1]))
		self.assertEqual(coll.query_point([0, 0]), set([1]))
		self.assertEqual(coll.query_point(-1, 0), set([1]))
		self.assertEqual(coll.query_point(-1.0001, 0), set())
		self.assertEqual(coll.query_point(3, 0), set([1]))
		self.assertEqual(coll.query_point(3.0001, 0), set())
		self.assertEqual(coll.query_point(0, -1), set([1]))
		self.assertEqual(coll.query_point(0, -1.0001), set())
		self.assertEqual(coll.query_point(0, 1), set([1]))
		self.assertEqual(coll.query_point(0, 1.0001), set())
		self.assertEqual(coll.query_point(-1, -1), set([1]))
		self.assertEqual(coll.query_point(3, -1), set([1]))
		self.assertEqual(coll.query_point(3, 1), set([1]))
		self.assertEqual(coll.query_point(3, 1), set([1]))

		self.assertEqual(coll.query_point(5, 5), set([2]))
		self.assertEqual(coll.query_point([6, 7]), set([2, 3]))
		self.assertEqual(coll.query_point([7, 7]), set([2, 3]))
		self.assertEqual(coll.query_point([7, 8]), set([2, 3]))
		self.assertEqual(coll.query_point([8.5, 8.5]), set([3]))

		self.assertEqual(coll.query_point(-2, 0), set())
		self.assertEqual(coll.query_point(10, 5), set())
		self.assertEqual(coll.query_point(7, 10), set())
		self.assertEqual(coll.query_point(7, -10), set())
		self.assertEqual(coll.query_point(-200, 100), set())
	
	def test_query_point_with_mask(self):
		from grease.collision import BroadSweepAndPrune, Pair
		world = TestWorld()
		coll = BroadSweepAndPrune()
		coll.set_world(world)
		set_entity = world.collision.set
		
		set_entity(1, 0, 0, 2, 2, into_mask=1)
		set_entity(2, 0, 0, 2, 2, into_mask=2)
		set_entity(3, 0, 0, 2, 2, into_mask=5)
		coll.step(0)
		self.assertEqual(coll.query_point(1, 1), set([1, 2, 3]))
		self.assertEqual(coll.query_point(1, 1, from_mask=1), set([1, 3]))
		self.assertEqual(coll.query_point(1, 1, from_mask=2), set([2]))
		self.assertEqual(coll.query_point(1, 1, from_mask=3), set([1, 2, 3]))
		self.assertEqual(coll.query_point(1, 1, from_mask=4), set([3]))
		self.assertEqual(coll.query_point(1, 1, from_mask=5), set([1, 3]))
		self.assertEqual(coll.query_point(1, 1, from_mask=8), set())


class CircularTestCase(unittest.TestCase):

	def test_defaults(self):
		from grease.collision import Circular, BroadSweepAndPrune
		coll = Circular()
		self.assertEqual(tuple(coll.handlers), ())
		self.assertTrue(isinstance(coll.broad_phase, BroadSweepAndPrune))
		self.assertEqual(coll.position_component, 'position')
		self.assertEqual(coll.collision_component, 'collision')
		self.assertTrue(coll.update_aabbs)
	
	def test_overrides(self):
		from grease.collision import Circular
		broad = TestCollisionSys()
		handlers = (object(), object())
		coll = Circular(broad_phase=broad, position_component='posi', collision_component='hal',
			update_aabbs=False, handlers=handlers)
		self.assertEqual(tuple(coll.handlers), handlers)
		self.assertTrue(coll.broad_phase is broad)
		self.assertEqual(coll.position_component, 'posi')
		self.assertEqual(coll.collision_component, 'hal')
		self.assertFalse(coll.update_aabbs)
	
	def test_before_step(self):
		# Queries should be well behaved even before the controller is run
		from grease.collision import Circular
		world = TestWorld()
		broad = TestCollisionSys()
		coll = Circular(broad_phase=broad)
		coll.set_world(world)
		self.assertEqual(coll.collision_pairs, set())
		self.assertEqual(coll.query_point(0,0), set())

	def test_step(self):
		from grease.collision import Circular
		# Stepping the circular collision system should also step the broad phase
		broad = TestCollisionSys()
		world = TestWorld()
		coll = Circular(broad_phase=broad)
		coll.set_world(world)
		self.assertTrue(coll.world is world)
		self.assertTrue(coll.broad_phase.world is world)
		self.assertEqual(coll.collision_pairs, set())
		self.assertEqual(broad.runtime, 0)
		coll.step(2)
		self.assertEqual(broad.runtime, 2)
		coll.step(1)
		self.assertEqual(broad.runtime, 3)
		self.assertEqual(coll.collision_pairs, set())
	
	def test_handlers(self):
		from grease.collision import Circular
		world = TestWorld()
		handler_calls = [0, 0]
		def handler1(system):
			self.assertTrue(system is coll, system)
			handler_calls[0] += 1
		def handler2(system):
			self.assertTrue(system is coll, system)
			handler_calls[1] += 1
		coll = Circular(handlers=(handler1, handler2))
		coll.set_world(world)
		coll.step(0)
		self.assertEqual(handler_calls, [1, 1])
		coll.step(0)
		self.assertEqual(handler_calls, [2, 2])
		coll.handlers = (handler2,)
		coll.step(0)
		self.assertEqual(handler_calls, [2, 3])

	def test_update_aabbs(self):
		from grease.collision import Circular
		broad = TestCollisionSys()
		world = TestWorld()
		coll = Circular(broad_phase=broad)
		coll.set_world(world)
		pos = world.position
		col = world.collision
		pos.set(1, (0, 0))
		col.set(1, radius=2)
		pos.set(2, (2, -3))
		col.set(2, radius=0.5)
		pos.set(3, (-5, -2))
		col.set(3, radius=10)
		for i in range(3):
			aabb = col[i + 1].aabb
			self.assertTrue(aabb.left == aabb.top == aabb.right == aabb.bottom == 0, aabb)
		coll.step(0)
		self.assertEqual(col[1].aabb, Data(left=-2, top=2, right=2, bottom=-2))
		self.assertEqual(col[2].aabb, Data(left=1.5, top=-2.5, right=2.5, bottom=-3.5))
		self.assertEqual(col[3].aabb, Data(left=-15, top=8, right=5, bottom=-12))

		pos.set(1, (2, 0))
		pos.set(2, (0, 0))
		col.set(3, radius=5)
		coll.step(0)
		self.assertEqual(col[1].aabb, Data(left=0, top=2, right=4, bottom=-2))
		self.assertEqual(col[2].aabb, Data(left=-0.5, top=0.5, right=0.5, bottom=-0.5))
		self.assertEqual(col[3].aabb, Data(left=-10, top=3, right=0, bottom=-7))

		coll.update_aabbs = False
		pos[1].position = (0, 0)
		col[1].radius = 3
		col[2].radius = 0.75
		col[3].position = (-3, 0)
		# aabbs should not change with update_aabbs set False
		coll.step(0)
		self.assertEqual(col[1].aabb, Data(left=0, top=2, right=4, bottom=-2))
		self.assertEqual(col[2].aabb, Data(left=-0.5, top=0.5, right=0.5, bottom=-0.5))
		self.assertEqual(col[3].aabb, Data(left=-10, top=3, right=0, bottom=-7))
	
	
	def test_collision_pairs(self):
		from grease.collision import Circular, Pair
		broad = TestCollisionSys()
		world = TestWorld()
		coll = Circular(broad_phase=broad)
		coll.set_world(world)
		pos_set = world.position.set
		col_set = world.collision.set
		pos_set(1, (0, 0))
		col_set(1, radius=5)
		pos_set(2, (3, 3))
		col_set(2, radius=0)
		pos_set(3, (6, 0))
		col_set(3, radius=1)
		pos_set(4, (-10, 4))
		col_set(4, radius=2)
		pos_set(5, (-13, 4))
		col_set(5, radius=2)
		pos_set(6, (0, 7))
		col_set(6, radius=1.99)

		# Pair everything and make sure the narrow phase sorts it out
		broad.collision_pairs = set([
			Pair(x+1, y+1) for x in range(6) for y in range(6) if x != y])
		coll.step(0)
		self.assertEqual(coll.collision_pairs, set([Pair(1,2), Pair(1, 3), Pair(4, 5)]))
	
	def test_collision_point_and_normal(self):
		from grease.collision import Circular, Pair
		broad = TestCollisionSys()
		world = TestWorld()
		coll = Circular(broad_phase=broad)
		coll.set_world(world)
		pos_set = world.position.set
		col_set = world.collision.set
		pos_set(1, (0, 0))
		col_set(1, radius=2)
		pos_set(2, (4, 0))
		col_set(2, radius=3)
		broad.collision_pairs = set([Pair(1,2)])
		coll.step(0)
		pair = list(coll.collision_pairs)[0]
		(e1, p1, n1), (e2, p2, n2) = pair.info
		self.assertEqual(e1, 1)
		self.assertEqual(p1, (2, 0))
		self.assertEqual(n1, (1, 0))
		self.assertEqual(e2, 2)
		self.assertEqual(p2, (1, 0))
		self.assertEqual(n2, (-1, 0))

		pos_set(2, (0, -5))
		col_set(2, radius=3.5)
		broad.collision_pairs = set([Pair(1,2)])
		coll.step(0)
		pair = list(coll.collision_pairs)[0]
		(e1, p1, n1), (e2, p2, n2) = pair.info
		self.assertEqual(e1, 1)
		self.assertEqual(p1, (0, -2))
		self.assertEqual(n1, (0, -1))
		self.assertEqual(e2, 2)
		self.assertEqual(p2, (0, -1.5))
		self.assertEqual(n2, (0, 1))
	
	def test_query_point(self):
		from grease.collision import Circular, Pair
		world = TestWorld()
		broad = TestCollisionSys()
		coll = Circular(broad_phase=broad)
		coll.set_world(world)
		pos_set = world.position.set
		col_set = world.collision.set
		pos_set(1, (0, 0))
		col_set(1, radius=1)
		pos_set(2, (0, 2))
		col_set(2, radius=1.5)
		pos_set(3, (-4, 3))
		col_set(3, radius=3)
		coll.step(0)
		self.assertEqual(broad.last_from_mask, None)
		self.assertEqual(coll.query_point(0,0), set([1]))
		self.assertEqual(coll.query_point(0,1), set([1, 2]))
		self.assertEqual(coll.query_point([0,1]), set([1, 2]))
		self.assertEqual(coll.query_point(1, 0), set([1]))
		self.assertEqual(coll.query_point(1.0001, 0), set())
		self.assertEqual(coll.query_point(-1, 3), set([2,3]))
		self.assertEqual(coll.query_point(-5, 3), set([3]))
		self.assertEqual(broad.last_from_mask, 0xffffffff)
		coll.query_point([0, 0], from_mask=0xff)
		self.assertEqual(broad.last_from_mask, 0xff)


class TestEntity(object):

	def __init__(self):
		self.collisions = set()

	def on_collide(self, other, point, normal):
		self.collisions.add((other, point, normal))


class CollisionHandlerTestCase(unittest.TestCase):

	def test_dispatch_events_all_pairs(self):
		from grease.collision import dispatch_events, Pair
		world = TestWorld()
		col = world.collision
		entities = [col.set(TestEntity()) for i in range(4)]
		system = TestCollisionSys(pairs=[
			Pair(entities[0], entities[1]),
			Pair(entities[1], entities[2]),
			Pair(entities[0], entities[2]),
		])
		system.set_world(world)
		dispatch_events(system)
		self.assertEqual(entities[0].collisions, 
			set([(entities[1], None, None), (entities[2], None, None)]))
		self.assertEqual(entities[1].collisions, 
			set([(entities[0], None, None), (entities[2], None, None)]))
		self.assertEqual(entities[2].collisions,
			set([(entities[0], None, None), (entities[1], None, None)]))
		self.assertEqual(entities[3].collisions, set())

		# The handler should tolerate an entity missing from
		# the collision component without complaint
		del col[entities[1]]
		for entity in entities:
			entity.collisions.clear()
		dispatch_events(system)
		self.assertEqual(entities[0].collisions, set([(entities[2], None, None)]))
		self.assertEqual(entities[1].collisions, set([]))
		self.assertEqual(entities[2].collisions, set([(entities[0], None, None)]))
		self.assertEqual(entities[3].collisions, set())

	
	def test_dispatch_events_missing_method(self):
		from grease.collision import dispatch_events, Pair
		world = TestWorld()
		col = world.collision
		class NoEventEntity(object):
			pass
		entities = [col.set(NoEventEntity()) for i in range(4)]
		system = TestCollisionSys(pairs=[
			Pair(entities[0], entities[1]),
			Pair(entities[1], entities[2]),
			Pair(entities[0], entities[2]),
		])
		system.set_world(world)
		dispatch_events(system)
	
	def test_dispatch_events_respects_masks(self):
		from grease.collision import dispatch_events, Pair
		world = TestWorld()
		col = world.collision
		masks = [
			(1, 1),
			(3, 0),
			(2, 7),
			(0, 0),
		]
		entities = [col.set(TestEntity(), from_mask=frmask, into_mask=inmask) 
			for frmask, inmask in masks]
		# Create all possible pairs
		pairs = [Pair(entities[i], entities[j]) for i in range(len(masks)) 
					for j in range(len(masks)) if i != j]
		system = TestCollisionSys(pairs=pairs)
		system.set_world(world)
		dispatch_events(system)
		self.assertEqual(entities[0].collisions, set([(entities[1], None, None)]))
		self.assertEqual(entities[1].collisions, set())
		self.assertEqual(entities[2].collisions, 
			set([(entities[0], None, None), (entities[1], None, None)]))
		self.assertEqual(entities[3].collisions, set())


if __name__ == '__main__':
	unittest.main()
