import unittest

world = object()


class TestEntity(object):
	world = world

	def __init__(self, block, index, gen=0):
		self.entity_id = (gen, block, index)


class FieldTestCase(unittest.TestCase):

	def test_field_name(self):
		from grease.component.field import Field
		f = Field("foobar", "i")
		self.assertEquals(f.name, "foobar")
	
	def test_python_int_field(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("myint", int)
		self.assert_(f.dtype is dtype(int))
	
	def test_python_int_field_defaults_to_zero(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("myint", int)
		self.assertEquals(f.default, 0)
	
	def test_python_float_field(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("myfloat", float)
		self.assert_(f.dtype is dtype(float))
	
	def test_python_float_field_defaults_to_zero(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("myfloat", float)
		self.assertEquals(f.default, 0)
	
	def test_python_bool_field(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("mybool", bool)
		self.assert_(f.dtype is dtype(bool))
	
	def test_python_bool_field_defaults_to_zero(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("mybool", bool)
		self.assertEquals(f.default, 0)

	def test_python_complex_field(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("mycomplex", complex)
		self.assert_(f.dtype is dtype(complex))
	
	def test_python_complex_field_defaults_to_zero(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("mycomplex", complex)
		self.assertEquals(f.default, 0)
	
	def test_python_object_field(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("myobject", object)
		self.assert_(f.dtype is dtype(object))
	
	def test_python_object_field_has_no_default(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("myobject", object)
		self.assertNotEqual(f.default, 0)
		self.assert_(f.default is not None)
	
	def test_python_object_field_default(self):
		from numpy import dtype
		from grease.component.field import Field
		f = Field("myobject", object, None)
		self.assert_(f.default is None)
	
	def test_int_various_sizes(self):
		from numpy import dtype
		from grease.component.field import Field
		f8 = Field('8', 'int8')
		self.assertEqual(f8.dtype, dtype('int8'))
		f16 = Field('16', 'int16')
		self.assertEqual(f16.dtype, dtype('int16'))
		f32 = Field('32', 'int32')
		self.assertEqual(f32.dtype, dtype('int32'))
		f64 = Field('64', 'int64')
		self.assertEqual(f64.dtype, dtype('int64'))
		
	def test_uint_various_sizes(self):
		from numpy import dtype
		from grease.component.field import Field
		f8 = Field('8', 'uint8')
		self.assertEqual(f8.dtype, dtype('uint8'))
		f16 = Field('16', 'uint16')
		self.assertEqual(f16.dtype, dtype('uint16'))
		f32 = Field('32', 'uint32')
		self.assertEqual(f32.dtype, dtype('uint32'))
		f64 = Field('64', 'uint64')
		self.assertEqual(f64.dtype, dtype('uint64'))

	def test_float_various_sizes(self):
		from numpy import dtype
		from grease.component.field import Field
		f32 = Field('32', 'float32')
		self.assertEqual(f32.dtype, dtype('float32'))
		f64 = Field('64', 'float64')
		self.assertEqual(f64.dtype, dtype('float64'))
		f128 = Field('128', 'float128')
		self.assertEqual(f128.dtype, dtype('float128'))
	
	def test_int_vector(self):
		from numpy import dtype
		from grease.component.field import Field
		fiv = Field("intvec", "3i")
		self.assertEqual(fiv.dtype.base, dtype('int32'))
		self.assertEqual(fiv.dtype.shape, (3,))
	
	def test_int_vector_defaults_to_zero(self):
		from numpy import dtype
		from grease.component.field import Field
		fiv = Field("intvec", "3i")
		self.assertEqual(fiv.default, 0)
	
	def test_double_vector(self):
		from numpy import dtype
		from grease.component.field import Field
		fdv = Field("doublevec", "2d")
		self.assertEqual(fdv.dtype.base, dtype('float64'))
		self.assertEqual(fdv.dtype.shape, (2,))
	
	def test_double_vector_defaults_to_zero(self):
		from numpy import dtype
		from grease.component.field import Field
		fdv = Field("doublevec", "2d")
		self.assertEqual(fdv.default, 0)
	
	def test_explicit_dtype(self):
		from numpy import dtype
		from grease.component.field import Field
		dt = dtype(('i4', [('r','u1'),('g','u1'),('b','u1'),('a','u1')]))
		f = Field("colorific", dt)
		self.assertEqual(f.dtype, dt)
	
	def test_getitem_fails_empty_field(self):
		from grease.component.field import Field
		e = TestEntity(0, 0)
		f = Field("bar", "i")
		try:
			f[e]
		except (IndexError, KeyError):
			pass
		else:
			self.fail()
	
	def test_getitem_fails_new_block(self):
		from grease.component.field import Field
		f = Field("bar", "i")
		f[TestEntity(0, 0)] = 1
		try:
			f[TestEntity(1, 0)]
		except (IndexError, KeyError):
			pass
		else:
			self.fail()

	def test_setitem_getitem(self):
		from grease.component.field import Field
		e1 = TestEntity(0, 0)
		f = Field("bar", "i")
		f[e1] = 2
		self.assertEqual(f[e1], 2)
		e2 = TestEntity(0, 1)
		f[e2] = -1
		self.assertEqual(f[e1], 2)
		self.assertEqual(f[e2], -1)
		e3 = TestEntity(1, 0)
		f[e3] = 5
		self.assertEqual(f[e1], 2)
		self.assertEqual(f[e2], -1)
		self.assertEqual(f[e3], 5)
		f[e1] = 100
		self.assertEqual(f[e1], 100)
		self.assertEqual(f[e2], -1)
		self.assertEqual(f[e3], 5)
	
	def test_setitem_vector_accepts_tuple(self):
		from grease.component.field import Field
		e = TestEntity(0, 0)
		f = Field("bar", "3f")
		f[e] = (2.5, -1, 0.25)
		self.assert_((f[e] == (2.5, -1, 0.25)).all())
	
	def test_setitem_getitem_object(self):
		from grease.component.field import Field
		e = TestEntity(0, 0)
		f = Field("bar", object)
		f[e] = "Hello"
		self.assertEqual(f[e], "Hello")
	
	def test_setitem_many(self):
		from grease.component.field import Field
		f = Field("baz", "i")
		entities = [TestEntity(0,i) for i in range(1000)]
		for i, e in enumerate(entities):
			f[e] = i
		for i, e in enumerate(entities):
			self.assertEqual(f[e], i)

	def test_setitem_many_unordered(self):
		from grease.component.field import Field
		ids = [66, 96, 0, 94, 64, 71, 99, 8, 47, 98, 45, 93, 85, 5, 7, 30, 37,
			12, 92, 70, 10, 69, 39, 28, 42, 89, 33, 90, 13, 4, 43, 1, 56, 60,
			63, 77, 32, 46, 21, 74, 91, 79, 22, 18, 82, 17, 31, 44, 67, 75,
			26, 95, 57, 62, 72, 68, 73, 9, 16, 11, 88, 58, 41, 59, 53, 48, 81,
			40, 51, 61, 24, 52, 54, 50, 38, 6, 83, 25, 65, 3, 36, 34, 23, 87,
			80, 2, 76, 97, 14, 35, 84, 86, 15, 78, 55, 27, 20, 19, 49, 29]
		f = Field("baz", "i")
		entities = [TestEntity(0,i) for i in ids]
		for i, e in enumerate(entities):
			f[e] = i
		for i, e in enumerate(entities):
			self.assertEqual(f[e], i)


class GeneralTestCase(): #unittest.TestCase):

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
		self.assertEqual(sorted(c.itervalues()), sorted(ed))
	
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
