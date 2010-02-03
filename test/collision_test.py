import unittest

class TestCollisionComp(dict):

	def __init__(self):
		self.new_entities = set()
		self.deleted_entities = set()

	def add(self, id, left, bottom, right, top, from_mask=0xffffffff, into_mask=0xffffffff):
		self[id] = Data(entity=id, 
			AABB=Data(left=left, top=top, right=right, bottom=bottom),
			from_mask=from_mask, into_mask=into_mask)

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
		from grease.controller.collision import Pair
		p = Pair(3, 4)
		self.assertEqual(p[0], 3)
		self.assertEqual(p[1], 4)
		self.assertEqual(tuple(p), (3, 4))
		self.assertRaises(TypeError, p, 1, 2, 3)
	
	def test_symmetric_hash(self):
		from grease.controller.collision import Pair
		self.assertEqual(hash(Pair('spam', 'eggs')), hash(Pair('eggs', 'spam')))
	
	def test_unordered_comparison(self):
		from grease.controller.collision import Pair
		self.assertEqual(Pair(42, 24), Pair(24, 42))


class SAPCollisionTestCase(unittest.TestCase):

	def test_before_step(self):
		# Queries should be well behaved even before the controller is run
		from grease.controller.collision import SAPCollision
		coll = SAPCollision()
		self.assertEqual(coll.collision_pairs, set())
		self.assertEqual(coll.query_point(0,0), set())
	
	def test_collision_pairs_no_collision(self):
		from grease.controller.collision import SAPCollision
		world = TestWorld()
		coll = SAPCollision()
		add = world.collision.add
		add(1, 10, 10, 20, 20)
		add(2, 0, 0, 3, 3)
		add(3, 11, 21, 15, 40)
		add(4, -5, 0, -3, 100)
		coll.set_world(world)
		self.assertTrue(coll.world is world)
		coll.step(0)
		self.assertEqual(coll.collision_pairs, set())
		coll.step(0)
		self.assertEqual(coll.collision_pairs, set())
	
	def test_collision_pairs_static_collision(self):
		from grease.controller.collision import SAPCollision, Pair
		world = TestWorld()
		coll = SAPCollision()
		coll.set_world(world)
		add = world.collision.add

		add(1, 10, 10, 20, 20)
		add(2, 15, 15, 25, 25)
		add(3, 5, 12, 30, 15)

		# boxes fully enclosed
		add(4, 30, 10, 40, 13)
		add(5, 31, 11, 39, 12)

		add(6, 0, 0, 2, 2)
		add(7, -1, 0.5, 1, 1.5)

		# no collisions with below
		add(8, 2.1, 2.1, 2.2, 2.2)
		add(9, 50, -40, 55, 40)
		add(10, -50, -50, 50, -45) 

		#import pdb; pdb.set_trace()
		coll.step(0)
		pairs = set(coll.collision_pairs)
		self.assertTrue(Pair(1,2) in pairs, pairs)
		self.assertTrue(Pair(1,3) in pairs, pairs)
		self.assertTrue(Pair(2,3) in pairs, pairs)
		self.assertTrue(Pair(4,5) in pairs, pairs)
		self.assertTrue(Pair(6,7) in pairs, pairs)
		self.assertEqual(len(pairs), 5)

		coll.step(0)
		self.assertEqual(coll.collision_pairs, pairs)

if __name__ == '__main__':
	unittest.main()
