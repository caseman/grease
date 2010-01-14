import unittest


class GeneralTest(unittest.TestCase):

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
		self.assertFalse(1 in c)
		ed = c.add(1)
		self.assertTrue(1 in c)
		self.assertEqual(ed.entity_id, 1)
	
	def test_add_kw_data(self):
		from grease.component import Component
		c = Component(x=float, y=float, name=str)
		self.assertFalse(33 in c)
		ed = c.add(33, x=10, y=-1, name="timmy!")
		self.assertTrue(33 in c)
		self.assertEqual(ed.x, 10)
		self.assertEqual(ed.y, -1)
		self.assertEqual(ed.name, "timmy!")
		self.assertEqual(ed.entity_id, 33)
	
	def test_add_data_object(self):
		from grease.component import Component
		c = Component(sweat=int, odor=str)
		class Data: pass
		d = Data()
		d.sweat = 100
		d.odor = "rank"
		ed = c.add(99, d)
		self.assertTrue(99 in c)
		self.assertEqual(ed.sweat, 100)
		self.assertEqual(ed.odor, "rank")
		self.assertEqual(ed.entity_id, 99)
	
	def test_add_with_data_object_and_kw(self):
		from grease.component import Component
		c = Component(state=str, time=float)
		class Data: pass
		d = Data()
		d.state = "grimey"
		d.time = 12.5
		ed = c.add(5, d, state="greasy")
		self.assertTrue(5 in c)
		self.assertEqual(ed.state, "greasy")
		self.assertEqual(ed.time, 12.5)
		self.assertEqual(ed.entity_id, 5)
	
	def test_data_defaults(self):
		from grease.component import Component
		from grease.vector import Vec2d
		c = Component(speed=int, accel=Vec2d, state=str)
		ed = c.add(3, accel=(10,5))
		self.assertEqual(ed.speed, 0)
		self.assertEqual(ed.accel, (10,5))
		self.assertEqual(ed.state, "")
		ed = c.add(2, state="uber")
		self.assertEqual(ed.speed, 0)
		self.assertEqual(ed.accel, (0,0))
		self.assertEqual(ed.state, "uber")
	
	def test_getitem(self):
		from grease.component import Component
		c = Component()
		self.assertRaises(KeyError, lambda: c[43])
		ed = c.add(43)
		self.assertTrue(c[43] is ed)
	
	def test_remove_and_contains(self):
		from grease.component import Component
		c = Component()
		self.assertFalse(c.remove(23))
		c.add(23)
		c.add(45)
		self.assertTrue(c.remove(23))
		self.assertFalse(23 in c)
		self.assertTrue(45 in c)
		self.assertFalse(c.remove(23))
		self.assertTrue(45 in c)
		self.assertTrue(c.remove(45))
		self.assertFalse(45 in c)
		self.assertFalse(23 in c)
	
	def test_len(self):
		from grease.component import Component
		c = Component()
		self.assertEqual(len(c), 0)
		[c.add(i+1) for i in range(50)]
		self.assertEqual(len(c), 50)
		[c.remove(i+1) for i in range(25)]
		self.assertEqual(len(c), 25)
	
	def test_iter(self):
		from grease.component import Component
		c = Component()
		self.assertEqual(list(c), [])
		ed = [c.add(3), c.add(7), c.add(12)]
		self.assertEqual(sorted(c, key=lambda e: e.entity_id), ed)
	
	def test_set_manager(self):
		from grease.component import Component
		c = Component()
		manager = object()
		c.set_manager(manager)
		self.assertTrue(c.manager is manager)
		self.assertRaises(AssertionError, c.set_manager, object())
	
	def test_entity_set(self):
		from grease.component import Component
		c = Component()
		c.set_manager(object())
		self.assertEqual(len(c.entity_set), 0)
		e1 = c.add(12)
		e2 = c.add(15)
		e3 = c.add(21)
		self.assertEqual(len(c.entity_set), 3)
		self.assertTrue(e1 in c.entity_set)
		self.assertTrue(e2 in c.entity_set)
		self.assertTrue(e3 in c.entity_set)
		c.remove(15)
		self.assertEqual(len(c.entity_set), 2)
		self.assertTrue(e1 in c.entity_set)
		self.assertFalse(e2 in c.entity_set)
		self.assertTrue(e3 in c.entity_set)
	
	def test_entity_id_set(self):
		from grease.component import Component
		c = Component()
		self.assertEqual(len(c.entity_id_set), 0)
		c.add(5)
		c.add(6)
		c.add(3)
		self.assertEqual(sorted(c.entity_id_set), [3, 5, 6])
		c.remove(5)
		self.assertEqual(sorted(c.entity_id_set), [3, 6])


if __name__ == '__main__':
	unittest.main()
