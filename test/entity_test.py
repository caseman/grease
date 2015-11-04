import unittest
import itertools


class TestWorld(object):
	
	def __init__(self, **kw):
		self.__dict__.update(kw)
		self.components = self
		self.entities = set()
		self.new_entity_id = itertools.count().__next__
		self.new_entity_id() # skip id 0
		for comp in list(kw.values()):
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
		self.assertTrue(entity in comp)
		del entity.test
		self.assertFalse(entity in comp)
	
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


if __name__ == '__main__':
	unittest.main()
