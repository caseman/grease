import unittest
import itertools
from nose.tools import raises


class TestIdGen(object):

	next_id = itertools.count().next

	def __init__(self):
		self.recycled = []
		self.recycle = self.recycled.append
		self.recycle_many = self.recycled.extend

	def new_entity_id(self, entity):
		assert not hasattr(entity, 'entity_id')
		return self.next_id()


class WorldEntities(set):
	
	def iter_intersection(self, entity_set):
		for entity in self:
			if entity in entity_set:
				yield entity


class TestWorld(object):
	
	def __init__(self, **kw):
		self.__dict__.update(kw)
		self.components = TestComponent()
		self.entities = WorldEntities()
		self.entity_id_generator = TestIdGen()
		for comp in kw.values():
			comp.world = self


class TestComponent(dict):
	
	def __init__(self):
		self.entities = set()
	
	def remove(self, entity):
		del self[entity]
	

class TestData(object):
	attr = 'deadbeef'

	def __init__(self, **kw):
		self.__dict__.update(kw)


class EntityTestCase(unittest.TestCase):
	
	def test_repr(self):
		from grease import Entity
		entity = Entity(TestWorld())
		self.assertTrue(repr(entity).startswith(
			'<Entity id: %s of TestWorld' % entity.entity_id), 
			('<Entity id: %s of TestWorld' % entity.entity_id, repr(entity)))
	
	def test_eq(self):
		from grease import Entity
		world = TestWorld()
		e1 = Entity(world)
		e2 = Entity(world)
		self.assertNotEqual(e1, e2)
		e2.entity_id = e1.entity_id
		self.assertEqual(e1, e2)
		otherworld = TestWorld()
		e3 = Entity(otherworld)
		self.assertNotEqual(e1, e3)
		self.assertNotEqual(e2, e3)
		e3.entity_id = e1.entity_id
		self.assertNotEqual(e1, e3)
		self.assertNotEqual(e2, e3)
	
	def test_entity_id(self):
		from grease import Entity
		world = TestWorld()
		entity1 = Entity(world)
		entity2 = Entity(world)
		self.assertTrue(entity1.entity_id > 0)
		self.assertTrue(entity2.entity_id > 0)
		self.assertNotEqual(entity1.entity_id, entity2.entity_id)
	
	def test_delete_exists(self):
		from grease import Entity
		world = TestWorld()
		self.assertEqual(world.entities, set())
		entity1 = Entity(world)
		entity2 = Entity(world)
		self.assertEqual(world.entities, set([entity1, entity2]))
		self.assertTrue(entity1.exists)
		self.assertTrue(entity2.exists)
		entity1.delete()
		self.assertEqual(world.entities, set([entity2]))
		self.assertFalse(entity1.exists)
		self.assertTrue(entity2.exists)
		entity2.delete()
		self.assertEqual(world.entities, set())
		self.assertFalse(entity1.exists)
		self.assertFalse(entity2.exists)
	
	def test_entity_subclass_init(self):
		from grease import Entity
		stuff = []
		class TestEntity(Entity):
			def __init__(self, world, other):
				stuff.append(world)
				stuff.append(other)
		world = TestWorld()
		TestEntity(world, self)
		self.assertEqual(stuff, [world, self])
	
	def test_component_property_names(self):
		from grease import Entity, component
		class TestEntity(Entity):
			foo = component.Property("NotFoo")
			bar = component.Property()
			baz = component.Property()
			spam = object()
		self.assertEqual(TestEntity.__dict__['foo'].name, "NotFoo")
		self.assertEqual(TestEntity.__dict__['bar'].name, "bar")
		self.assertEqual(TestEntity.__dict__['baz'].name, "baz")


class TestEntity(object):

	def __init__(self, world, block=0, index=0, gen=1):
		self.world = world
		self.entity_id = (gen, block, index)
		world.entities.add(self)


class EntitySetTestBase(object):

	def test_world(self):
		world = object()
		s = self.set_class(world)
		self.assert_(s.world is world)
	
	def test_add_contains(self):
		world = TestWorld()
		s = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=5)
		e3 = TestEntity(world, block=2)
		self.assert_(e1 not in s)
		self.assert_(e2 not in s)
		self.assert_(e3 not in s)
		s.add(e2)
		self.assert_(e1 not in s)
		self.assert_(e2 in s)
		self.assert_(e3 not in s)
		s.add(e3)
		self.assert_(e1 not in s)
		self.assert_(e2 in s)
		self.assert_(e3 in s)
		s.add(e1)
		self.assert_(e1 in s)
		self.assert_(e2 in s)
		self.assert_(e3 in s)
	
	@raises(ValueError)
	def test_add_different_world(self):
		world = TestWorld()
		s = self.set_class(world)
		world2 = TestWorld()
		e = TestEntity(world2)
		world2.entities.add(e)
		s.add(e)

	def test_add_remove(self):
		world = TestWorld()
		s = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=1)
		e3 = TestEntity(world, block=1)
		s.add(e1)
		s.add(e2)
		s.add(e3)
		self.assert_(e1 in s)
		self.assert_(e2 in s)
		self.assert_(e3 in s)
		s.remove(e2)
		self.assert_(e1 in s)
		self.assert_(e2 not in s)
		self.assert_(e3 in s)
		s.remove(e3)
		self.assert_(e1 in s)
		self.assert_(e2 not in s)
		self.assert_(e3 not in s)
		s.remove(e1)
		self.assert_(e1 not in s)
		self.assert_(e2 not in s)
		self.assert_(e3 not in s)
	
	@raises(KeyError)
	def test_remove_not_in_set(self):
		world = TestWorld()
		s = self.set_class(world)
		s.remove(TestEntity(world))
	
	@raises(KeyError)
	def test_remove_different_world(self):
		world1 = TestWorld()
		world2 = TestWorld()
		e1 = TestEntity(world1)
		e2 = TestEntity(world2)
		self.assertEqual(e1.entity_id, e2.entity_id)
		s1 = self.set_class(world1)
		s1.add(e1)
		s1.remove(e2)

	def test_discard(self):
		world = TestWorld()
		s = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=1)
		e3 = TestEntity(world, block=1)
		s.add(e1)
		s.add(e2)
		s.add(e3)
		self.assert_(e1 in s)
		self.assert_(e2 in s)
		self.assert_(e3 in s)
		s.discard(e2)
		self.assert_(e1 in s)
		self.assert_(e2 not in s)
		self.assert_(e3 in s)
		s.discard(e3)
		self.assert_(e1 in s)
		self.assert_(e2 not in s)
		self.assert_(e3 not in s)
		s.discard(e1)
		self.assert_(e1 not in s)
		self.assert_(e2 not in s)
		self.assert_(e3 not in s)
	
	def test_discard_not_in_set(self):
		world = TestWorld()
		s = self.set_class(world)
		s.discard(TestEntity(world))

	def test_discard_different_world(self):
		world1 = TestWorld()
		world2 = TestWorld()
		e1 = TestEntity(world1)
		e2 = TestEntity(world2)
		self.assertEqual(e1.entity_id, e2.entity_id)
		s1 = self.set_class(world1)
		s1.add(e1)
		self.assert_(e1 in s1)
		s1.discard(e2)
		self.assert_(e1 in s1)

	def test_contains_different_world(self):
		world1 = TestWorld()
		world2 = TestWorld()
		e1 = TestEntity(world1)
		e2 = TestEntity(world2)
		self.assertEqual(e1.entity_id, e2.entity_id)
		s1 = self.set_class(world1)
		s2 = self.set_class(world2)
		self.assert_(e1 not in s1)
		self.assert_(e2 not in s1)
		self.assert_(e1 not in s2)
		self.assert_(e2 not in s2)
		s1.add(e1)
		self.assert_(e1 in s1)
		self.assert_(e2 not in s1)
		self.assert_(e1 not in s2)
		self.assert_(e2 not in s2)
		s2.add(e2)
		self.assert_(e1 in s1)
		self.assert_(e2 not in s1)
		self.assert_(e1 not in s2)
		self.assert_(e2 in s2)
	
	def test_iter_empty(self):
		world = TestWorld()
		s = self.set_class(world)
		self.assertEqual(tuple(s), ())
	
	def test_iter(self):
		world = TestWorld()
		s = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=10)
		e3 = TestEntity(world, block=5, index=2)
		s.add(e1)
		s.add(e2)
		s.add(e3)
		L = list(s)
		self.assertEqual(len(L), 3)
		self.assert_(e1 in s)
		self.assert_(e2 in s)
		self.assert_(e3 in s)
	
	def test_iter_mutate(self):
		world = TestWorld()
		s = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s.add(e1)
		s.add(e2)
		s.add(e3)
		s.add(e4)
		s.add(e5)
		s.remove(e1)
		s.remove(e5)
		L = list(s)
		self.assertEqual(len(L), 3)
		self.assert_(e2 in s)
		self.assert_(e3 in s)
		self.assert_(e4 in s)
	
	def test_truthiness_false(self):
		world = TestWorld()
		s = self.set_class(world)
		self.failIf(s)
	
	def test_truthiness_mutate(self):
		world = TestWorld()
		s = self.set_class(world)
		e = TestEntity(world)
		s.add(e)
		s.remove(e)
		self.failIf(s)
	
	def test_truthiness_true(self):
		world = TestWorld()
		s = self.set_class(world)
		s.add(TestEntity(world))
		self.failUnless(s)
	
	def test_len_empty(self):
		world = TestWorld()
		s = self.set_class(world)
		self.assertEqual(len(s), 0)
	
	def test_len_mutate(self):
		world = TestWorld()
		s = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s.add(e1)
		self.assertEqual(len(s), 1)
		s.add(e2)
		self.assertEqual(len(s), 2)
		# Repeated add should not change len
		s.add(e2)
		self.assertEqual(len(s), 2)
		s.add(e3)
		self.assertEqual(len(s), 3)
		s.remove(e2)
		self.assertEqual(len(s), 2)
		s.add(e4)
		self.assertEqual(len(s), 3)
		s.add(e5)
		self.assertEqual(len(s), 4)
		s.remove(e1)
		self.assertEqual(len(s), 3)
		s.discard(e1)
		self.assertEqual(len(s), 3)
		s.remove(e4)
		self.assertEqual(len(s), 2)
		s.remove(e5)
		self.assertEqual(len(s), 1)
		s.remove(e3)
		self.assertEqual(len(s), 0)
	
	def test_eq_self(self):
		world = TestWorld()
		s = self.set_class(world)
		self.assertEqual(s, s)
		s.add(TestEntity(world))
		self.assert_(s == s)
		self.assert_(not s != s)

	
	def test_eq_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		self.assertEqual(s1, s2)
	
	def test_eq_simple(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=2)
		s1.add(e1)
		s1.add(e2)
		s2.add(e1)
		s2.add(e2)
		self.assert_(s1 == s2)
		self.assert_(s2 == s1)
		self.assert_(not s1 != s2)

	def test_eq_more(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		entities = [
			TestEntity(world),
			TestEntity(world, index=2),
			TestEntity(world, index=3),
			TestEntity(world, block=5),
			TestEntity(world, block=5, index=1),
			TestEntity(world, block=15, index=2),
		]
		for e in entities:
			s1.add(e)
			s2.add(e)
		self.assert_(s1 == s2)
		self.assert_(s2 == s1)
		self.assert_(not s1 != s2)

	def test_eq_different_additions(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		entities = [
			TestEntity(world),
			TestEntity(world, index=2),
			TestEntity(world, index=3),
			TestEntity(world, block=15, index=2),
		]
		for e in entities:
			s1.add(e)
			s2.add(e)
		e1 = TestEntity(world, block=5)
		s1.add(e1)
		s1.remove(e1)
		e2 = TestEntity(world, block=5, index=1)
		s2.add(e2)
		s2.remove(e2)
		self.assert_(s1 == s2)
		self.assert_(s2 == s1)
		self.assert_(not s1 != s2)

	def test_not_eq_simple(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=2)
		s1.add(e1)
		s2.add(e1)
		s2.add(e2)
		self.assert_(not s1 == s2)
		self.assert_(not s2 == s1)
		self.assert_(s1 != s2)
		# Tests some additional code paths
		s1.add(e2)
		s1.remove(e2)
		self.assert_(not s1 == s2)
		self.assert_(not s2 == s1)
		self.assert_(s1 != s2)
	
	def test_not_eq_one_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		s2.add(e1)
		self.assert_(not s1 == s2)
		self.assert_(not s2 == s1)
		self.assert_(s1 != s2)
	
	def test_not_eq_different_types(self):
		world = TestWorld()
		s1 = self.set_class(world)
		self.assert_(not s1 == None)
		self.assert_(s1 != object())

	def test_intersect_both_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		s3 = s1.intersection(s2)
		self.assertEqual(len(s3), 0)
		self.assert_(s3 is not s1)
		self.assert_(s3 is not s2)

	def test_intersect_one_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		s2.add(e1)
		self.assertEqual(len(s1.intersection(s2)), 0)
		self.assertEqual(len(s2.intersection(s1)), 0)

	@raises(ValueError)
	def test_intersect_different_worlds(self):
		world = TestWorld()
		s1 = self.set_class(world)
		world2 = TestWorld()
		s2 = self.set_class(world2)
		s1.intersection(s2)

	def test_intersect_simple(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=2)
		s1.add(e1)
		s2.add(e1)
		s2.add(e2)
		self.assertEqual(list(s1 & s2), [e1])
		self.assertEqual(list(s2 & s1), [e1])

	def test_intersect_more(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e4)
		s1.add(e5)
		s2 = self.set_class(world)
		s2.add(e3)
		s2.add(e2)
		s2.add(e4)
		self.assertEqual(sorted(s1 & s2), sorted([e2, e4]))
		self.assertEqual(sorted(s2 & s1), sorted([e2, e4]))
		s2.remove(e2)
		self.assertEqual(sorted(s1 & s2), sorted([e4]))
		self.assertEqual(sorted(s2 & s1), sorted([e4]))
	
	def test_intersect_same(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e3)
		s1.add(e4)
		s2 = self.set_class(world)
		s2.add(e2)
		s2.add(e4)
		s2.add(e3)
		s2.add(e1)
		self.assertEqual(sorted(s1.intersection(s2)), sorted([e1,e2,e3,e4]))
		self.assertEqual(sorted(s2.intersection(s1)), sorted([e1,e2,e3,e4]))

	def test_intersect_disjoint(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e2)
		s1.add(e3)
		s2 = self.set_class(world)
		s2.add(e1)
		s2.add(e4)
		self.assertEqual(len(s1.intersection(s2)), 0)
		self.assertEqual(len(s2.intersection(s1)), 0)

	def test_union_both_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		s3 = s1.union(s2)
		self.assertEqual(len(s3), 0)
		self.assert_(s3 is not s1)
		self.assert_(s3 is not s2)

	def test_union_one_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		s2.add(e1)
		self.assertEqual(list(s1.union(s2)), [e1])
		self.assertEqual(list(s2.union(s1)), [e1])

	@raises(ValueError)
	def test_union_different_worlds(self):
		world = TestWorld()
		s1 = self.set_class(world)
		world2 = TestWorld()
		s2 = self.set_class(world2)
		s1.union(s2)

	def test_union_simple(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=2)
		s1.add(e1)
		s2.add(e1)
		s2.add(e2)
		self.assertEqual(sorted(s1 | s2), sorted([e1, e2]))
		self.assertEqual(sorted(s2 | s1), sorted([e1, e2]))

	def test_union_more(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e4)
		s1.add(e5)
		s2 = self.set_class(world)
		s2.add(e3)
		s2.add(e2)
		s2.add(e4)
		self.assertEqual(sorted(s1 | s2), sorted([e1, e2, e3, e4, e5]))
		self.assertEqual(sorted(s2 | s1), sorted([e1, e2, e3, e4, e5]))
		s2.remove(e3)
		s2.remove(e2)
		s1.remove(e5)
		self.assertEqual(sorted(s1 | s2), sorted([e1, e2, e4]))
		self.assertEqual(sorted(s2 | s1), sorted([e1, e2, e4]))
	
	def test_union_same(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e3)
		s1.add(e4)
		s2 = self.set_class(world)
		s2.add(e2)
		s2.add(e4)
		s2.add(e3)
		s2.add(e1)
		self.assertEqual(sorted(s1.union(s2)), sorted([e1,e2,e3,e4]))
		self.assertEqual(sorted(s2.union(s1)), sorted([e1,e2,e3,e4]))

	def test_union_disjoint(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e2)
		s1.add(e3)
		s2 = self.set_class(world)
		s2.add(e1)
		s2.add(e4)
		self.assertEqual(sorted(s1.union(s2)), sorted([e1,e2,e3,e4]))
		self.assertEqual(sorted(s2.union(s1)), sorted([e1,e2,e3,e4]))

	def test_difference_both_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		s3 = s1.difference(s2)
		self.assertEqual(len(s3), 0)
		self.assert_(s3 is not s1)
		self.assert_(s3 is not s2)

	def test_difference_one_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		s2.add(e1)
		self.assertEqual(list(s1.difference(s2)), [])
		self.assertEqual(list(s2.difference(s1)), [e1])

	@raises(ValueError)
	def test_difference_different_worlds(self):
		world = TestWorld()
		s1 = self.set_class(world)
		world2 = TestWorld()
		s2 = self.set_class(world2)
		s1.difference(s2)

	def test_difference_simple(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=2)
		s1.add(e1)
		s2.add(e1)
		s2.add(e2)
		self.assertEqual(list(s1 - s2), [])
		self.assertEqual(list(s2 - s1), [e2])

	def test_difference_more(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e5)
		s2 = self.set_class(world)
		s2.add(e3)
		s2.add(e2)
		s2.add(e4)
		self.assertEqual(sorted(s1 - s2), sorted([e1, e5]))
		self.assertEqual(sorted(s2 - s1), sorted([e3, e4]))
		s2.remove(e3)
		s2.remove(e2)
		s1.remove(e5)
		self.assertEqual(sorted(s1 - s2), sorted([e1, e2]))
		self.assertEqual(sorted(s2 - s1), [e4])
	
	def test_difference_same(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e3)
		s1.add(e4)
		s2 = self.set_class(world)
		s2.add(e2)
		s2.add(e4)
		s2.add(e3)
		s2.add(e1)
		self.assertEqual(list(s1.difference(s2)), [])
		self.assertEqual(list(s2.difference(s1)), [])

	def test_difference_disjoint(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e2)
		s1.add(e3)
		s2 = self.set_class(world)
		s2.add(e1)
		s2.add(e4)
		self.assertEqual(sorted(s1.difference(s2)), sorted([e2,e3]))
		self.assertEqual(sorted(s2.difference(s1)), sorted([e1,e4]))


class EntitySetTestCase(EntitySetTestBase, unittest.TestCase):
	from grease.set import EntitySet as set_class
	
	def test_new_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		e1 = TestEntity(world)
		s1.add(e1)
		self.assertEqual(len(s1), 1)
		s2 = s1.new_empty()
		self.assert_(s2.__class__ is self.set_class)
		self.assertEqual(len(s2), 0)
		
	def test_new_empty_subclass(self):
		class MyEntitySet(self.set_class):
			pass
		world = TestWorld()
		s1 = MyEntitySet(world)
		e1 = TestEntity(world)
		s1.add(e1)
		self.assertEqual(len(s1), 1)
		s2 = s1.new_empty()
		self.assert_(s2.__class__ is MyEntitySet)
		self.assertEqual(len(s2), 0)

	@raises(ValueError)
	def test_add_deleted_entity(self):
		world = TestWorld()
		s = self.set_class(world)
		e = TestEntity(world)
		world.entities.remove(e)
		s.add(e)

	def test_difference_update_both_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		s3 = s1.difference_update(s2)
		self.assertEqual(len(s3), 0)
		self.assert_(s3 is s1)
		self.assert_(s3 is not s2)

	def test_difference_update_one_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		s2.add(e1)
		s = s1
		s1.difference_update(s2)
		self.assert_(s1 is s)
		self.assertEqual(list(), [])

	@raises(ValueError)
	def test_difference_update_different_worlds(self):
		world = TestWorld()
		s1 = self.set_class(world)
		world2 = TestWorld()
		s2 = self.set_class(world2)
		s1.difference_update(s2)

	def test_difference_update_simple(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=2)
		s1.add(e1)
		s2.add(e1)
		s2.add(e2)
		s1 -= s2
		self.assertEqual(list(s1), [])

	def test_difference_update_more(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e5)
		s2 = self.set_class(world)
		s2.add(e3)
		s2.add(e2)
		s2.add(e4)
		s1 -= s2
		self.assertEqual(sorted(s1), sorted([e1, e5]))
	
	def test_difference_update_same(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e3)
		s1.add(e4)
		s2 = self.set_class(world)
		s2.add(e2)
		s2.add(e4)
		s2.add(e3)
		s2.add(e1)
		self.assertEqual(list(s1.difference_update(s2)), [])

	def test_difference_update_disjoint(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e2)
		s1.add(e3)
		s2 = self.set_class(world)
		s2.add(e1)
		s2.add(e4)
		self.assertEqual(sorted(s1.difference_update(s2)), sorted([e2,e3]))

	def test_update_both_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		s3 = s1.update(s2)
		self.assertEqual(len(s3), 0)
		self.assert_(s3 is s1)
		self.assert_(s3 is not s2)

	def test_update_one_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		s2.add(e1)
		self.assertEqual(list(s1.update(s2)), [e1])

	@raises(ValueError)
	def test_update_different_worlds(self):
		world = TestWorld()
		s1 = self.set_class(world)
		world2 = TestWorld()
		s2 = self.set_class(world2)
		s1.update(s2)

	def test_update_simple(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=2)
		s1.add(e1)
		s2.add(e1)
		s2.add(e2)
		s = s1
		s1 |= s2
		self.assert_(s1 is s)
		self.assertEqual(sorted(s1), sorted([e1, e2]))

	def test_update_more(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e4)
		s1.add(e5)
		s2 = self.set_class(world)
		s2.add(e3)
		s2.add(e2)
		s2.add(e4)
		s1 |= s2
		self.assertEqual(sorted(s1), sorted([e1, e2, e3, e4, e5]))
	
	def test_update_same(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e3)
		s1.add(e4)
		s2 = self.set_class(world)
		s2.add(e2)
		s2.add(e4)
		s2.add(e3)
		s2.add(e1)
		self.assertEqual(sorted(s1.update(s2)), sorted([e1,e2,e3,e4]))

	def test_update_disjoint(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e2)
		s1.add(e3)
		s2 = self.set_class(world)
		s2.add(e1)
		s2.add(e4)
		self.assertEqual(sorted(s1.update(s2)), sorted([e1,e2,e3,e4]))

	def test_intersect_update_both_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		s3 = s1.intersection_update(s2)
		self.assertEqual(len(s3), 0)
		self.assert_(s3 is s1)
		self.assert_(s3 is not s2)

	def test_intersect_update_one_empty(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		s2.add(e1)
		s = s1
		s1 &= s2
		self.assert_(s1 is s)
		self.assertEqual(len(s1), 0)

	@raises(ValueError)
	def test_intersect_update_different_worlds(self):
		world = TestWorld()
		s1 = self.set_class(world)
		world2 = TestWorld()
		s2 = self.set_class(world2)
		s1.intersection_update(s2)

	def test_intersect_update_simple(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s2 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=2)
		s1.add(e1)
		s2.add(e1)
		s2.add(e2)
		s1 &= s2
		self.assertEqual(list(s1), [e1])

	def test_intersect_update_more(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e4)
		s1.add(e5)
		s2 = self.set_class(world)
		s2.add(e3)
		s2.add(e2)
		s2.add(e4)
		s1 &= s2
		self.assertEqual(sorted(s1), sorted([e2, e4]))
	
	def test_intersect_update_same(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e3)
		s1.add(e4)
		s2 = self.set_class(world)
		s2.add(e2)
		s2.add(e4)
		s2.add(e3)
		s2.add(e1)
		s1.intersection_update(s2)
		self.assertEqual(sorted(s1), sorted([e1,e2,e3,e4]))

	def test_intersect_update_disjoint(self):
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		s1 = self.set_class(world)
		s1.add(e2)
		s1.add(e3)
		s2 = self.set_class(world)
		s2.add(e1)
		s2.add(e4)
		self.assertEqual(len(s1.intersection_update(s2)), 0)


class WorldEntitySetTestCase(EntitySetTestBase, unittest.TestCase):
	from grease.world import WorldEntitySet as set_class

	def test_new_empty(self):
		from grease.set import EntitySet
		world = TestWorld()
		s1 = self.set_class(world)
		e1 = TestEntity(world)
		s1.add(e1)
		self.assertEqual(len(s1), 1)
		s2 = s1.new_empty()
		self.assert_(s2.__class__ is EntitySet)
		self.assertEqual(len(s2), 0)
	
	def test_get_entity(self):
		world = TestWorld()
		s1 = self.set_class(world)
		e1 = TestEntity(world)
		s1.add(e1)
		self.assert_(s1[e1.entity_id] is e1)
	
	@raises(KeyError)
	def test_get_entity_not_added(self):
		world = TestWorld()
		s1 = self.set_class(world)
		e1 = TestEntity(world)
		s1[e1.entity_id]
	
	def test_get_entity_removed(self):
		world = TestWorld()
		s1 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=1)
		s1.add(e1)
		s1.add(e2)
		s1.remove(e1)
		self.assert_(e2 in s1)
		self.assertRaises(KeyError, lambda: s1[e1.entity_id])
	
	def test_entity_removed_is_recycled(self):
		world = TestWorld()
		s1 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=1)
		s1.add(e1)
		s1.add(e2)
		s1.remove(e1)
		self.assert_(e1 in world.entity_id_generator.recycled)
		self.assert_(e2 not in world.entity_id_generator.recycled)

	def test_get_entity_discarded(self):
		world = TestWorld()
		s1 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=1)
		s1.add(e1)
		s1.add(e2)
		s1.discard(e1)
		self.assert_(e2 in s1)
		self.assertRaises(KeyError, lambda: s1[e1.entity_id])

	def test_entity_discarded_is_recycled(self):
		world = TestWorld()
		s1 = self.set_class(world)
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=1)
		s1.add(e1)
		s1.add(e2)
		s1.remove(e1)
		self.assert_(e1 in world.entity_id_generator.recycled)
		self.assert_(e2 not in world.entity_id_generator.recycled)
	
	def test_discard_set(self):
		from grease.set import EntitySet
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e3)
		s1.add(e4)
		s1.add(e5)
		s2 = EntitySet(world)
		s2.add(e2)
		s2.add(e4)
		s2.add(e5)
		s1.discard_set(s2)
		self.assertEqual(sorted(s1), sorted([e1, e3]))

	@raises(ValueError)
	def test_discard_set_different_world(self):
		from grease.set import EntitySet
		world1 = TestWorld()
		world2 = TestWorld()
		s1 = self.set_class(world1)
		s2 = EntitySet(world2)
		s1.discard_set(s2)

	def test_iter_intersection(self):
		from grease.set import EntitySet
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		e3 = TestEntity(world, block=5)
		e4 = TestEntity(world, block=5, index=1)
		e5 = TestEntity(world, block=15, index=2)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s1.add(e3)
		s1.add(e4)
		s1.add(e5)
		s2 = EntitySet(world)
		s2.add(e2)
		s2.add(e4)
		s2.add(e5)
		self.assertEqual(sorted(s1.iter_intersection(s2)), sorted([e2,e4,e5]))
	
	def test_iter_intersection_empty(self):
		from grease.set import EntitySet
		world = TestWorld()
		e1 = TestEntity(world)
		e2 = TestEntity(world, index=3)
		s1 = self.set_class(world)
		s1.add(e1)
		s1.add(e2)
		s2 = EntitySet(world)
		self.assertEqual(list(s1.iter_intersection(s2)), [])

	@raises(ValueError)
	def test_iter_intersection_different_world(self):
		from grease.set import EntitySet
		world1 = TestWorld()
		world2 = TestWorld()
		s1 = self.set_class(world1)
		s2 = EntitySet(world2)
		s1.iter_intersection(s2).next()

	@raises(NotImplementedError)
	def test_update(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s1.update(s1)

	@raises(NotImplementedError)
	def test_intersection_update(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s1.intersection_update(s1)

	@raises(NotImplementedError)
	def test_difference_update(self):
		world = TestWorld()
		s1 = self.set_class(world)
		s1.difference_update(s1)


if __name__ == '__main__':
	unittest.main()
