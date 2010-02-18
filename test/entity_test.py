import unittest
import itertools

from grease import Entity


class TestWorld(object):
	entity_types = {'Entity': Entity}
	
	def __init__(self, **kw):
		for ename, etype in self.entity_types.items():
			wrapped = type(ename, (etype,), 
				{'world': self, 'entities': set(), 
				'__register__': False, '__baseclass__': etype})
			setattr(self, ename, wrapped)
		self.components = kw
		self.entities = set()
		self.new_entity_id = itertools.count().next
		self.new_entity_id() # skip id 0
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


class TestEntity(Entity):
	
	def __new__(cls, world=None, id=1):
		entity = object.__new__(cls)
		entity.__dict__['world'] = world
		entity.__dict__['entity_id'] = id
		return entity
	
	def __init__(self, world=None, id=1):
		super(TestEntity, self).__init__()

TestEntity.__baseclass__ = TestEntity


class EntityTest(unittest.TestCase):
	
	def test_repr(self):
		entity = TestEntity(TestWorld(), 72)
		self.assertTrue(repr(entity).startswith('<TestEntity id: 72 of TestWorld'), repr(entity))
	
	def test_accessor_getattr_for_nonexistant_component(self):
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = TestEntity(world, 72)
		self.assertTrue(entity not in comp)
		self.assertRaises(AttributeError, getattr, entity, 'foo')
	
	def test_accessor_getattr_for_non_member_entity(self):
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = TestEntity(world, 96)
		accessor = entity.test
		self.assertFalse(entity in comp)
		self.assertRaises(AttributeError, getattr, accessor, 'attr')
	
	def test_accessor_getattr_for_member_entity(self):
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = TestEntity(world, 96)
		comp.set(entity)
		self.assertTrue(entity in comp)
		self.assertEqual(entity.test.attr, 'deadbeef')
	
	def test_accessor_setattr_adds_non_member_entity(self):
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = TestEntity(world, 101)
		self.assertFalse(entity in comp)
		entity.test.attr = 'foobar'
		self.assertEqual(entity.test.attr, 'foobar')
		self.assertTrue(entity in comp)

	def test_accessor_setattr_for_member_entity(self):
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = TestEntity(world, 999)
		comp.set(entity)
		self.assertNotEqual(entity.test.attr, 'spam')
		entity.test.attr = 'spam'
		self.assertTrue(entity in comp)
		self.assertEqual(entity.test.attr, 'spam')
	
	def test_eq(self):
		world = TestWorld()
		self.assertEqual(TestEntity(world, 78), TestEntity(world, 78))
		otherworld = TestWorld()
		self.assertNotEqual(TestEntity(world, 8), TestEntity(otherworld, 8))
		self.assertNotEqual(TestEntity(world, 51), TestEntity(world, 32))
	
	def test_delattr(self):
		comp = TestComponent()
		world = TestWorld(test=comp)
		entity = TestEntity(world, 88)
		comp.set(entity)
		self.failUnless(entity in comp)
		del entity.test
		self.failIf(entity in comp)
	
	def test_entity_id(self):
		world = TestWorld()
		entity1 = world.Entity()
		entity2 = world.Entity()
		self.assertTrue(entity1.entity_id > 0)
		self.assertTrue(entity2.entity_id > 0)
		self.assertNotEqual(entity1.entity_id, entity2.entity_id)
	
	def test_delete_exists(self):
		world = TestWorld()
		self.assertEqual(world.entities, set())
		entity1 = world.Entity()
		entity2 = world.Entity()
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
	
	def test_entity_baseclass_sets(self):
		class Foo(Entity):
			pass

		class Bar(Foo):
			pass

		class Baz(Entity):
			pass

		class World(TestWorld):
			entity_types = {'Entity': Entity, 'Foo': Foo, 'Bar': Bar, 'Baz':Baz}
		world = World()
		foo = world.Foo()
		self.assertTrue(foo in world.entities)
		self.assertTrue(foo not in world.Bar.entities)
		self.assertTrue(foo not in world.Baz.entities)
		self.assertTrue(foo in world.Foo.entities)
		self.assertTrue(foo in world.Entity.entities)
		bar = world.Bar()
		self.assertTrue(bar in world.entities)
		self.assertTrue(bar in world.Bar.entities)
		self.assertTrue(bar in world.Foo.entities)
		self.assertTrue(bar not in world.Baz.entities)
		self.assertTrue(bar in world.Entity.entities)
		baz = world.Baz()
		self.assertTrue(baz in world.entities)
		self.assertTrue(baz not in world.Bar.entities)
		self.assertTrue(baz not in world.Foo.entities)
		self.assertTrue(baz in world.Baz.entities)
		self.assertTrue(baz in world.Entity.entities)

		bar.delete()
		self.assertTrue(bar not in world.entities)
		self.assertTrue(bar not in world.Bar.entities)
		self.assertTrue(bar not in world.Foo.entities)
		self.assertTrue(bar not in world.Baz.entities)
		self.assertTrue(bar not in world.Entity.entities)


class EntityComponentAccessorTestCase(unittest.TestCase):

	def test_getattr(self):
		world = TestWorld()
		from grease.entity import EntityComponentAccessor
		entity = TestEntity(world, id=1)
		component = {entity: TestData(foo=5)}
		accessor = EntityComponentAccessor(component, entity)
		self.assertEqual(accessor.foo, 5)
		self.assertRaises(AttributeError, getattr, accessor, 'bar')

		entity2 = TestEntity(world, id=2)
		accessor = EntityComponentAccessor(component, entity2)
		self.assertRaises(AttributeError, getattr, accessor, 'foo')
		self.assertRaises(AttributeError, getattr, accessor, 'bar')
	
	def test_setattr_member_entity(self):
		from grease.entity import EntityComponentAccessor
		world = TestWorld()
		entity = TestEntity(world)
		data = TestData(foo=5)
		accessor = EntityComponentAccessor({entity: data}, entity)
		self.assertEqual(data.foo, 5)
		accessor.foo = 66
		self.assertEqual(data.foo, 66)
		accessor.bar = '!!'
		self.assertEqual(data.bar, '!!')
	
	def test_setattr_nonmember_entity(self):
		from grease.entity import EntityComponentAccessor
		world = TestWorld()
		entity = TestEntity(world)
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
		world = TestWorld()
		entity = TestEntity(world)
		component = TestComponent()
		accessor = EntityComponentAccessor(component, entity)
		self.assertFalse(accessor)
		component[entity] = 456
		self.assertTrue(accessor)


if __name__ == '__main__':
	unittest.main()
