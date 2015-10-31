import unittest

world = object()

class TestEntity(object):
	world = world


class GeneralTestCase(unittest.TestCase):

	def test_fields(self):
		from grease.component import Component
		c = Component()
		self.assertEqual(len(c.fields), 0)

		c = Component(f1=int, f2=float, f3=str)
		self.assertEqual(len(c.fields), 3)
		self.assertEqual(c.fields['f1'].name, 'f1')
		self.assertEqual(c.fields['f1'].type, int)
		self.assertTrue(c.fields['f1'].component is c)
		self.assertEqual(c.fields['f2'].name, 'f2')
		self.assertEqual(c.fields['f2'].type, float)
		self.assertTrue(c.fields['f2'].component is c)
		self.assertEqual(c.fields['f3'].name, 'f3')
		self.assertEqual(c.fields['f3'].type, str)
		self.assertTrue(c.fields['f3'].component is c)
	
	def test_invalid_field_type(self):
		from grease.component import Component
		self.assertRaises(AssertionError, Component, t=tuple)
	
	def test_add_no_data(self):
		from grease.component import Component
		c = Component()
		c.set_world(world)
		entity = TestEntity()
		self.assertFalse(entity in c)
		ed = c.set(entity)
		self.assertTrue(entity in c)
		self.assertEqual(list(c), [entity])
	
	def test_add_kw_data(self):
		from grease.component import Component
		c = Component(x=float, y=float, name=str)
		c.set_world(world)
		entity = TestEntity()
		self.assertFalse(entity in c)
		ed = c.set(entity, x=10, y=-1, name="timmy!")
		self.assertTrue(entity in c)
		self.assertEqual(ed.x, 10)
		self.assertEqual(ed.y, -1)
		self.assertEqual(ed.name, "timmy!")
	
	def test_add_data_object(self):
		from grease.component import Component
		c = Component(sweat=int, odor=str)
		c.set_world(world)
		class Data: pass
		d = Data()
		d.sweat = 100
		d.odor = "rank"
		entity = TestEntity()
		ed = c.set(entity, d)
		self.assertTrue(entity in c)
		self.assertEqual(ed.sweat, 100)
		self.assertEqual(ed.odor, "rank")
	
	def test_add_with_data_object_and_kw(self):
		from grease.component import Component
		c = Component(state=str, time=float)
		c.set_world(world)
		class Data: pass
		d = Data()
		d.state = "grimey"
		d.time = 12.5
		entity = TestEntity()
		ed = c.set(entity, d, state="greasy")
		self.assertTrue(entity in c)
		self.assertEqual(ed.state, "greasy")
		self.assertEqual(ed.time, 12.5)
	
	def test_data_defaults(self):
		from grease.component import Component
		from grease.geometry import Vec2d
		c = Component(speed=int, accel=Vec2d, state=str)
		c.set_world(world)
		e1 = TestEntity()
		e2 = TestEntity()
		ed = c.set(e1, accel=(10,5))
		self.assertEqual(ed.speed, 0)
		self.assertEqual(ed.accel, (10,5))
		self.assertEqual(ed.state, "")
		ed = c.set(e2, state="uber")
		self.assertEqual(ed.speed, 0)
		self.assertEqual(ed.accel, (0,0))
		self.assertEqual(ed.state, "uber")
	
	def test_step_updates_new_and_deleted_lists(self):
		from grease.component import Component
		c = Component(x=float, y=float)
		c.set_world(world)
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [])
		e1 = TestEntity()
		e2 = TestEntity()
		c.set(e1)
		c.set(e2)
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [])
		c.step(0)
		self.assertEqual(list(c.new_entities), [e1, e2])
		self.assertEqual(list(c.deleted_entities), [])
		c.step(0)
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [])
		del c[e1]
		del c[e2]
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [])
		c.step(0)
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [e1, e2])
	
	def test_getitem(self):
		from grease.component import Component
		c = Component()
		c.set_world(world)
		entity = TestEntity()
		self.assertRaises(KeyError, lambda: c[entity])
		ed = c.set(entity)
		self.assertTrue(c[entity] is ed)
	
	def test_remove_and_contains(self):
		from grease.component import Component
		c = Component()
		c.set_world(world)
		e1 = TestEntity()
		e2 = TestEntity()
		self.assertFalse(c.remove(e1))
		c.set(e1)
		c.set(e2)
		self.assertTrue(c.remove(e1))
		self.assertTrue(e1 in c)
		c.step(0)
		self.assertFalse(e1 in c)
		self.assertTrue(e2 in c)
		self.assertFalse(c.remove(e1))
		c.step(0)
		self.assertTrue(c.remove(e2))
		self.assertTrue(e2 in c)
		c.step(0)
		self.assertFalse(e2 in c)
		self.assertFalse(e2 in c)
	
	def test_len(self):
		from grease.component import Component
		c = Component()
		c.set_world(world)
		self.assertEqual(len(c), 0)
		self.assertEqual(len(c.entities), 0)
		entities = [TestEntity() for _ in range(50)]
		[c.set(e) for e in entities]
		self.assertEqual(len(c), 50)
		self.assertEqual(len(c.entities), 50)
		[c.remove(e) for e in entities[:25]]
		self.assertEqual(len(c.entities), 25)
		self.assertEqual(len(c), 50)
		c.step(0)
		self.assertEqual(len(c), 25)
		self.assertEqual(len(c.entities), 25)
	
	def test_iter(self):
		from grease.component import Component
		c = Component()
		c.set_world(world)
		self.assertEqual(list(c), [])
		ed = [c.set(TestEntity()), c.set(TestEntity()), c.set(TestEntity())]
		self.assertEqual(sorted(c.values()), sorted(ed))
	
	def test_set_world(self):
		from grease.component import Component
		c = Component()
		world = object()
		c.set_world(world)
		self.assertTrue(c.world is world)
	
	def test_entities_set(self):
		from grease.component import Component
		c = Component()
		c.set_world(world)
		self.assertEqual(len(c.entities), 0)
		entity1 = TestEntity()
		entity2 = TestEntity()
		entity3 = TestEntity()
		c.set(entity1)
		c.set(entity2)
		c.set(entity3)
		self.assertEqual(len(c.entities), 3)
		self.assertTrue(entity1 in c.entities)
		self.assertTrue(entity2 in c.entities)
		self.assertTrue(entity3 in c.entities)
		c.remove(entity2)
		self.assertEqual(len(c.entities), 2)
		self.assertTrue(entity1 in c.entities)
		self.assertFalse(entity2 in c.entities)
		self.assertTrue(entity3 in c.entities)


if __name__ == '__main__':
	unittest.main()
