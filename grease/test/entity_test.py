import unittest
import itertools
from nose.tools import raises

class TestIdGen(object):

	next_id = itertools.count().next

	def new_entity_id(self, entity):
		assert not hasattr(entity, 'entity_id')
		return self.next_id()


class WorldEntities(set):
	
	def __init__(self):
		self.id_to_entity = {}
	
	def add(self, e):
		super(WorldEntities, self).add(e)
		self.id_to_entity[e.entity_id] = e


class TestWorld(object):
	
	def __init__(self, **kw):
		self.__dict__.update(kw)
		self.components = self
		self.entities = WorldEntities()
		self.entity_id_generator = TestIdGen()
		for comp in kw.values():
			comp.world = self


class TestComponent(dict):
	
	def __init__(self):
		self.entities = set()
	
	def set(self, entity):
		data = TestData()
		self[entity] = data
		self.entities.add(entity)
		return data
	
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
	
	def test_accessor_getattr_for_nonexistant_component(self):
		from grease import Entity
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = Entity(world)
		self.assertTrue(entity not in comp)
		self.assertRaises(AttributeError, getattr, entity, 'foo')
	
	def test_accessor_getattr_for_non_member_entity(self):
		from grease import Entity
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = Entity(world)
		accessor = entity.test
		self.assertFalse(entity in comp)
		self.assertRaises(AttributeError, getattr, accessor, 'attr')
	
	def test_accessor_getattr_for_member_entity(self):
		from grease import Entity
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = Entity(world)
		comp.set(entity)
		self.assertTrue(entity in comp)
		self.assertEqual(entity.test.attr, 'deadbeef')
	
	def test_accessor_setattr_adds_non_member_entity(self):
		from grease import Entity
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = Entity(world)
		self.assertFalse(entity in comp)
		entity.test.attr = 'foobar'
		self.assertEqual(entity.test.attr, 'foobar')
		self.assertTrue(entity in comp)

	def test_accessor_setattr_for_member_entity(self):
		from grease import Entity
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = Entity(world)
		comp.set(entity)
		self.assertNotEqual(entity.test.attr, 'spam')
		entity.test.attr = 'spam'
		self.assertTrue(entity in comp)
		self.assertEqual(entity.test.attr, 'spam')
	
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
	
	def test_delattr(self):
		from grease import Entity
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = Entity(world)
		comp.set(entity)
		self.failUnless(entity in comp)
		del entity.test
		self.failIf(entity in comp)
	
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
	
	def test_entity_subclass_slots(self):
		from grease import Entity
		class NewEntity(Entity):
			pass
		world = TestWorld()
		entity = NewEntity(world)
		self.assertRaises(AttributeError, setattr, entity, 'notanattr', 1234)
	
	def test_entity_subclass_cant_have_slots(self):
		from grease import Entity
		self.assertRaises(TypeError, 
			type, 'Test', (Entity,), {'__slots__': ('foo', 'bar')})
	
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


class EntityComponentAccessorTestCase(unittest.TestCase):

	def test_getattr(self):
		from grease.entity import EntityComponentAccessor
		from grease import Entity
		world = TestWorld()
		entity = Entity(world)
		component = {entity: TestData(foo=5)}
		accessor = EntityComponentAccessor(component, entity)
		self.assertEqual(accessor.foo, 5)
		self.assertRaises(AttributeError, getattr, accessor, 'bar')

		entity2 = Entity(world)
		accessor = EntityComponentAccessor(component, entity2)
		self.assertRaises(AttributeError, getattr, accessor, 'foo')
		self.assertRaises(AttributeError, getattr, accessor, 'bar')
	
	def test_setattr_member_entity(self):
		from grease.entity import EntityComponentAccessor
		from grease import Entity
		world = TestWorld()
		entity = Entity(world)
		data = TestData(foo=5)
		accessor = EntityComponentAccessor({entity: data}, entity)
		self.assertEqual(data.foo, 5)
		accessor.foo = 66
		self.assertEqual(data.foo, 66)
		accessor.bar = '!!'
		self.assertEqual(data.bar, '!!')
	
	def test_setattr_nonmember_entity(self):
		from grease.entity import EntityComponentAccessor
		from grease import Entity
		world = TestWorld()
		entity = Entity(world)
		component = TestComponent()
		accessor = EntityComponentAccessor(component, entity)
		self.assertRaises(AttributeError, getattr, entity, 'baz')
		self.assertTrue(entity not in component)
		accessor.baz = 1000
		self.assertTrue(entity in component)
		self.assertEqual(accessor.baz, 1000)
		self.assertEqual(component[entity].baz, 1000)
	
	def test_truthiness(self):
		from grease.entity import EntityComponentAccessor
		from grease import Entity
		world = TestWorld()
		entity = Entity(world)
		component = TestComponent()
		accessor = EntityComponentAccessor(component, entity)
		self.assertFalse(accessor)
		component[entity] = 456
		self.assertTrue(accessor)


class TestEntity(object):

	def __init__(self, world, block=0, index=0, gen=1):
		self.world = world
		self.entity_id = (gen, block, index)
		world.entities.add(self)


class EntitySetTestCase(unittest.TestCase):

	def test_world(self):
		from grease.entity import EntitySet
		world = object()
		s = EntitySet(world)
		self.assert_(s.world is world)
	
	def test_add_contains(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
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
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		world2 = TestWorld()
		e = TestEntity(world2)
		world2.entities.add(e)
		s.add(e)

	@raises(ValueError)
	def test_add_deleted_entity(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		e = TestEntity(world)
		world.entities.remove(e)
		s.add(e)

	def test_add_remove(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
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
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		s.remove(TestEntity(world))
	
	@raises(KeyError)
	def test_remove_different_world(self):
		from grease.entity import EntitySet
		world1 = TestWorld()
		world2 = TestWorld()
		e1 = TestEntity(world1)
		e2 = TestEntity(world2)
		self.assertEqual(e1.entity_id, e2.entity_id)
		s1 = EntitySet(world1)
		s1.add(e1)
		s1.remove(e2)

	def test_discard(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
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
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		s.discard(TestEntity(world))

	def test_discard_different_world(self):
		from grease.entity import EntitySet
		world1 = TestWorld()
		world2 = TestWorld()
		e1 = TestEntity(world1)
		e2 = TestEntity(world2)
		self.assertEqual(e1.entity_id, e2.entity_id)
		s1 = EntitySet(world1)
		s1.add(e1)
		self.assert_(e1 in s1)
		s1.discard(e2)
		self.assert_(e1 in s1)

	def test_contains_different_world(self):
		from grease.entity import EntitySet
		world1 = TestWorld()
		world2 = TestWorld()
		e1 = TestEntity(world1)
		e2 = TestEntity(world2)
		self.assertEqual(e1.entity_id, e2.entity_id)
		s1 = EntitySet(world1)
		s2 = EntitySet(world2)
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
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		self.assertEqual(tuple(s), ())
	
	def test_iter(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
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
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
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
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		self.failIf(s)
	
	def test_truthiness_mutate(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		e = TestEntity(world)
		s.add(e)
		s.remove(e)
		self.failIf(s)
	
	def test_truthiness_true(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		s.add(TestEntity(world))
		self.failUnless(s)
	
	def test_len_empty(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
		self.assertEqual(len(s), 0)
	
	def test_len_mutate(self):
		from grease.entity import EntitySet
		world = TestWorld()
		s = EntitySet(world)
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


if __name__ == '__main__':
	unittest.main()
