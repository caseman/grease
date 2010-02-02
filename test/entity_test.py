import unittest

from grease import Entity

class TestWorld(object):
	
	def __init__(self, **kw):
		self.components = kw
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
	
	def __init__(self, world=None, id=None):
		pass


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


class EntityComponentAccessorTestCase(unittest.TestCase):

	def test_getattr(self):
		from grease.entity import EntityComponentAccessor
		entity = TestEntity(id=1)
		component = {entity: TestData(foo=5)}
		accessor = EntityComponentAccessor(component, entity)
		self.assertEqual(accessor.foo, 5)
		self.assertRaises(AttributeError, getattr, accessor, 'bar')

		entity2 = TestEntity(id=2)
		accessor = EntityComponentAccessor(component, entity2)
		self.assertRaises(AttributeError, getattr, accessor, 'foo')
		self.assertRaises(AttributeError, getattr, accessor, 'bar')
	
	def test_setattr_member_entity(self):
		from grease.entity import EntityComponentAccessor
		entity = TestEntity()
		data = TestData(foo=5)
		accessor = EntityComponentAccessor({entity: data}, entity)
		self.assertEqual(data.foo, 5)
		accessor.foo = 66
		self.assertEqual(data.foo, 66)
		accessor.bar = '!!'
		self.assertEqual(data.bar, '!!')
	
	def test_setattr_nonmember_entity(self):
		from grease.entity import EntityComponentAccessor
		entity = TestEntity()
		component = TestComponent()
		accessor = EntityComponentAccessor(component, entity)
		self.assertRaises(AttributeError, getattr, entity, 'baz')
		self.assertTrue(entity not in component)
		accessor.baz = 1000
		self.assertTrue(entity in component)
		self.assertEqual(accessor.baz, 1000)
		self.assertEqual(component[entity].baz, 1000)


if __name__ == '__main__':
	unittest.main()
