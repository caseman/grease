import unittest


class TestManager(object):
	
	def __init__(self, **kw):
		self.components = kw
		for comp in kw.values():
			comp._manager = self
	
	def __getitem__(self, name):
		return self.components[name]


class TestComponent(object):
	
	def __init__(self, data=None):
		self.data = data or {}
		self.entity_set = self
	
	def __contains__(self, id):
		return id in self.data
	
	def __getitem__(self, id):
		return self.data[id]
	
	def add(self, id):
		data = TestData()
		data.entity_id = id
		self.data[id] = data
		return data
	
	def remove(self, id):
		del self.data[id]
	
	@property
	def _entities(self):
		return set(self.data.keys())
	

class TestData(object):
	attr = 'deadbeef'


class EntityTest(unittest.TestCase):

	def test_entity_id(self):
		from grease.entity import Entity
		entity = Entity(TestManager(), 101)
		self.assertEqual(entity.entity_id, 101)
	
	def test_repr(self):
		from grease.entity import Entity
		entity = Entity(TestManager(), 72)
		self.assertTrue(repr(entity).startswith('<Entity id: 72 of TestManager'), repr(entity))
	
	def test_accessor_getattr_for_nonexistant_component(self):
		from grease.entity import Entity
		comp = TestComponent()
		manager = TestManager(test=comp)
		entity = Entity(manager, 72)
		self.assertRaises(AttributeError, getattr, entity, 'foo')
	
	def test_accessor_getattr_for_non_member_entity(self):
		from grease.entity import Entity
		comp = TestComponent()
		manager = TestManager(test=comp)
		entity = Entity(manager, 96)
		accessor = entity.test
		self.assertFalse(96 in comp.data)
		self.assertRaises(KeyError, getattr, accessor, 'attr')
	
	def test_accessor_getattr_for_member_entity(self):
		from grease.entity import Entity
		comp = TestComponent({96: TestData()})
		manager = TestManager(test=comp)
		entity = Entity(manager, 96)
		self.assertTrue(96 in comp.data)
		self.assertEqual(entity.test.attr, 'deadbeef')
	
	def test_accessor_setattr_adds_non_member_entity(self):
		from grease.entity import Entity
		comp = TestComponent()
		manager = TestManager(test=comp)
		entity = Entity(manager, 101)
		self.assertFalse(101 in comp.data)
		entity.test.attr = 'foobar'
		self.assertEqual(entity.test.attr, 'foobar')
		self.assertTrue(101 in comp.data)

	def test_accessor_setattr_for_member_entity(self):
		from grease.entity import Entity
		comp = TestComponent({999: TestData()})
		manager = TestManager(test=comp)
		entity = Entity(manager, 999)
		self.assertTrue(999 in comp.data)
		self.assertNotEqual(entity.test.attr, 'spam')
		entity.test.attr = 'spam'
		self.assertTrue(999 in comp.data)
		self.assertEqual(entity.test.attr, 'spam')
	
	def test_eq(self):
		from grease.entity import Entity
		manager = TestManager()
		self.assertEqual(Entity(manager, 78), Entity(manager, 78))
		othermgr = TestManager()
		self.assertNotEqual(Entity(manager, 8), Entity(othermgr, 8))
		self.assertNotEqual(Entity(manager, 51), Entity(manager, 32))
	
	def test_delattr(self):
		from grease.entity import Entity
		comp = TestComponent({88: TestData()})
		manager = TestManager(test=comp)
		entity = Entity(manager, 88)
		self.failUnless(88 in comp.data)
		del entity.test
		self.failIf(88 in comp.data)


class EntitySetTest(unittest.TestCase):

	def test_contains(self):
		from grease.entity import EntitySet, Entity
		manager = TestManager()
		es = EntitySet(manager)
		e1 = Entity(manager, 1)
		e2 = Entity(manager, 2)
		e3 = Entity(manager, 3)
		for e in (e1, e2, e3):
			self.assertFalse(e in es, e)
			self.assertFalse(e.entity_id in es, e.entity_id)

		es = EntitySet(manager, (1, 3))
		self.assertTrue(e1 in es)
		self.assertTrue(1 in es)
		self.assertFalse(e2 in es)
		self.assertFalse(2 in es)
		self.assertTrue(e3 in es)
		self.assertTrue(3 in es)
	
	def test_len(self):
		from grease.entity import EntitySet
		manager = TestManager()
		self.assertEqual(len(EntitySet(manager)), 0)
		self.assertEqual(len(EntitySet(manager, [1])), 1)
		self.assertEqual(len(EntitySet(manager, range(1000))), 1000)
	
	def test_iter(self):
		from grease.entity import EntitySet, Entity
		manager = TestManager()
		e1 = Entity(manager, 1)
		e2 = Entity(manager, 3)
		e3 = Entity(manager, 100)
		self.assertEqual(list(iter(EntitySet(manager))), [])
		self.assertEqual(sorted(iter(EntitySet(manager, [1]))), [e1])
		self.assertEqual(
			sorted(iter(EntitySet(manager, [1,100,3])), key=lambda e: e.entity_id), 
			[e1,e2,e3])
	
	def test_eq(self):
		from grease.entity import EntitySet
		manager = TestManager()
		self.assertEqual(EntitySet(manager), EntitySet(manager))
		self.assertEqual(EntitySet(manager, [1,2,8,100]), EntitySet(manager, [1,2,8,100]))
		self.assertNotEqual(EntitySet(manager, [1,100]), EntitySet(manager, [1,200,201]))
		othermgr = TestManager()
		self.assertNotEqual(EntitySet(manager), EntitySet(othermgr))
		self.assertNotEqual(EntitySet(manager, [1,2,3]), EntitySet(othermgr, [1,2,3]))
		self.assertNotEqual(EntitySet(manager, [3,7]), EntitySet(othermgr, [5,8,11,12]))
	
	def test_intersection(self):
		from grease.entity import EntitySet
		manager = TestManager()
		set1 = EntitySet(manager, [1, 3, 7, 5])
		set2 = EntitySet(manager, [1, 2, 3, 4])
		expected = EntitySet(manager, [1, 3])
		self.assertEqual(set1.intersection(set2), expected)
		self.assertEqual(set1 & set2, expected)
		self.assertEqual(set2 & set1, expected)
		self.assertEqual(set1.intersection(set1), set1)
		empty = EntitySet(manager)
		self.assertEqual(set1 & empty, empty)
		othermgr = TestManager()
		self.assertRaises(AssertionError, set1.intersection, EntitySet(othermgr, [1,2]))
	
	def test_union(self):
		from grease.entity import EntitySet
		manager = TestManager()
		set1 = EntitySet(manager, [1, 3, 7, 5])
		set2 = EntitySet(manager, [1, 2, 3, 4])
		expected = EntitySet(manager, [1, 2, 3, 4, 5, 7])
		self.assertEqual(set1.union(set2), expected)
		self.assertEqual(set1 | set2, expected)
		self.assertEqual(set2 | set1, expected)
		self.assertEqual(set1.union(set1), set1)
		empty = EntitySet(manager)
		self.assertEqual(set1 | empty, set1)
		othermgr = TestManager()
		self.assertRaises(AssertionError, set1.union, EntitySet(othermgr, [1,2]))
	
	def test_difference(self):
		from grease.entity import EntitySet
		manager = TestManager()
		set1 = EntitySet(manager, [1, 3, 7, 5])
		set2 = EntitySet(manager, [1, 2, 3, 4])
		expected = EntitySet(manager, [5, 7])
		self.assertEqual(set1.difference(set2), expected)
		self.assertEqual(set1 - set2, expected)
		expected = EntitySet(manager, [2, 4])
		self.assertEqual(set2.difference(set1), expected)
		self.assertEqual(set2 - set1, expected)
		empty = EntitySet(manager)
		self.assertEqual(set1 - empty, set1)
		self.assertEqual(empty - set1, empty)
		othermgr = TestManager()
		self.assertRaises(AssertionError, set1.difference, EntitySet(othermgr, [1,2]))
	
	def test_component_access(self):
		from grease.entity import EntitySet
		comp = TestComponent({11: TestData()})
		manager = TestManager(test=comp)
		es = EntitySet(manager, [2, 5, 11])
		comp_es = es.test
		self.assertTrue(isinstance(comp_es, EntitySet))
		self.assertEqual(comp_es, EntitySet(manager, [11]))
		self.assertRaises(AttributeError, getattr, es, "notthere")


if __name__ == '__main__':
	unittest.main()
