import unittest

class TestCollisionComp(dict):

	def __init__(self):
		self.new_entities = set()
		self.deleted_entities = set()

	def set(self, entity, left, bottom, right, top, from_mask=0xffffffff, into_mask=0xffffffff):
		if entity in self:
			data = self[entity]
		else:
			data = self[entity] = Data()
		data.entity = entity
		data.AABB = Data(left=left, top=top, right=right, bottom=bottom)
		data.from_mask = from_mask
		data.into_mask = into_mask


class TestWorld(object):

	def __init__(self):
		self.components = self
		self.collision = TestCollisionComp()

	def __getitem__(self, name):
		return self.collision

class Data(object):

	def __init__(self, **kw):
		self.__dict__.update(kw)


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


if __name__ == '__main__':
	unittest.main()
