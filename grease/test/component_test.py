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
	
	def __init__(self):
		self.entities = WorldEntities()
		self.entity_id_generator = TestIdGen()


world = TestWorld()

class TestEntity(object):
	world = world

	def __init__(self, block=0, index=0, gen=0):
		self.entity_id = (gen, block, index)
		self.world.entities.add(self)


class TestComponent(object):
	world = world
	
	def __init__(self, field=None):
		self.entities = set()
		if field is not None:
			self.fields = {field: {}}
	
	def add(self, entity):
		self.entities.add(entity)
	
	def delete(self, entity):
		self.entities.remove(entity)
	
	def __contains__(self, entity):
		return entity in self.entities


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
	
	@raises(TypeError)
	def test_bad_dtype(self):
		from grease.component.field import Field
		Field("vvvv", "invalidtype")

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
	
	def test_setitem_many_with_default(self):
		from grease.component.field import Field
		f = Field("obj", object, default="foobar")
		entities = [TestEntity(0,i) for i in range(1000)]
		for i, e in enumerate(entities):
			f[e] = str(i)
		for i, e in enumerate(entities):
			self.assertEqual(f[e], str(i))

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
	
	def test_repr(self):
		from grease.component.field import Field
		self.assertEqual(repr(Field("goober", float)), 
			"Field(name='goober', dtype=dtype('float64'))")
		self.assertEqual(repr(Field("goober", '3d')), 
			"Field(name='goober', dtype=dtype(('float64',(3,))))")


class TestField(dict):
	def __init__(self, name, dtype):
		import numpy
		self.name = name
		self.dtype = numpy.dtype(dtype)
		self.default = None


class TestEntitySet(set):
	def __init__(self, world):
		self.world = world


class ComponentTestCase(unittest.TestCase):

	def mkcomponent(self, **fields):
		from grease.component import Component
		old_esf = Component.entity_set_factory
		Component.entity_set_factory = TestEntitySet
		old_ff = Component.field_factory
		Component.field_factory = TestField
		try:
			c = Component(**fields)
			c.set_world(world)
		finally:
			Component.entity_set_factory = old_esf
			Component.field_factory = old_ff
		return c

	def test_no_fields(self):
		c = self.mkcomponent()
		self.assertEqual(len(c.fields), 0)

	def test_fields(self):
		from numpy import dtype
		c = self.mkcomponent(f1=int, f2=float, f3='3d')
		self.assertEqual(len(c.fields), 3)
		self.assertEqual(c.fields['f1'].name, 'f1')
		self.assertEqual(c.fields['f1'].dtype, dtype(int))
		self.assertEqual(c.fields['f2'].name, 'f2')
		self.assertEqual(c.fields['f2'].dtype, dtype(float))
		self.assertEqual(c.fields['f3'].name, 'f3')
		self.assertEqual(c.fields['f3'].dtype, dtype('3d'))
	
	@raises(TypeError)
	def test_invalid_field_type(self):
		self.mkcomponent(f="blahblah")
	
	def test_set_add_entity(self):
		c = self.mkcomponent()
		entity = TestEntity()
		self.assertFalse(entity in c)
		c.add(entity)
		self.assertTrue(entity in c)
		self.assertEqual(list(c.entities), [entity])
	
	def test_add_new_entity_defaults(self):
		c = self.mkcomponent(i=int, o=object)
		c.fields['i'].default = 0
		c.fields['o'].default = "nothing"
		entity = TestEntity()
		c.add(entity)
		self.assertEqual(c.fields['i'][entity], 0)
		self.assertEqual(c.fields['o'][entity], "nothing")
	
	@raises(ValueError)
	def test_add_new_entity_different_world(self):
		c = self.mkcomponent()
		e = TestEntity()
		e.world = object()
		c.add(e)
	
	def test_step_updates_new_and_deleted_lists(self):
		c = self.mkcomponent()
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [])
		e1 = TestEntity()
		e2 = TestEntity()
		c.add(e1)
		c.add(e2)
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [])
		c.step(0)
		self.assertEqual(list(c.new_entities), [e1, e2])
		self.assertEqual(list(c.deleted_entities), [])
		c.step(0)
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [])
		c.delete(e1)
		c.delete(e2)
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [])
		c.step(0)
		self.assertEqual(list(c.new_entities), [])
		self.assertEqual(list(c.deleted_entities), [e1, e2])
	
	def test_delete_and_contains(self):
		c = self.mkcomponent()
		e1 = TestEntity()
		e2 = TestEntity()
		self.assertFalse(c.delete(e1))
		c.add(e1)
		c.add(e2)
		self.assertTrue(c.delete(e1))
		self.assertFalse(e1 in c)
		self.assertTrue(e2 in c)
		self.assertFalse(c.delete(e1))
		self.assertTrue(c.delete(e2))
		self.assertFalse(e1 in c)
		self.assertFalse(e2 in c)
	
	def test_contains_different_world(self):
		c = self.mkcomponent()
		e1 = TestEntity()
		e2 = TestEntity()
		self.assertEqual(e1.entity_id, e2.entity_id)
		e2.world = object()
		c.add(e1)
		assert e1 in c
		assert e2 not in c
	
	def test_set_world(self):
		c = self.mkcomponent()
		world = object()
		c.set_world(world)
		self.assertTrue(c.world is world)
	
	def test_entities_set(self):
		c = self.mkcomponent()
		self.assertEqual(len(c.entities), 0)
		self.assert_(c.entities.world is world)
		entity1 = TestEntity()
		entity2 = TestEntity()
		entity3 = TestEntity()
		c.add(entity1)
		c.add(entity2)
		c.add(entity3)
		self.assertEqual(len(c.entities), 3)
		self.assertTrue(entity1 in c.entities)
		self.assertTrue(entity2 in c.entities)
		self.assertTrue(entity3 in c.entities)
		c.delete(entity2)
		self.assertEqual(len(c.entities), 2)
		self.assertTrue(entity1 in c.entities)
		self.assertFalse(entity2 in c.entities)
		self.assertTrue(entity3 in c.entities)
	
	def test_repr(self):
		c = self.mkcomponent()
		self.assertEqual(repr(c), "<Component %x of %r>" % (id(c), world))


class ComponentAccessorTestCase(unittest.TestCase):

	def test_getattr(self):
		from grease.component.general import ComponentAccessor
		from grease import Entity
		world = TestWorld()
		entity = Entity(world)
		component = TestComponent('foo')
		component.add(entity)
		component.fields['foo'][entity] = 42
		accessor = ComponentAccessor(component, entity)
		self.assertEqual(accessor.foo, 42)
		self.assertRaises(AttributeError, getattr, accessor, 'bar')

		entity2 = Entity(world)
		accessor = ComponentAccessor(component, entity2)
		self.assertRaises(AttributeError, getattr, accessor, 'foo')
		self.assertRaises(AttributeError, getattr, accessor, 'bar')
	
	def test_setattr_member_entity(self):
		from grease.component.general import ComponentAccessor
		from grease import Entity
		world = TestWorld()
		entity = Entity(world)
		component = TestComponent('foo')
		component.add(entity)
		component.fields['foo'][entity] = 5
		accessor = ComponentAccessor(component, entity)
		accessor.foo = 66
		self.assertEqual(component.fields['foo'][entity], 66)
	
	def test_setattr_nonmember_entity(self):
		from grease.component.general import ComponentAccessor
		from grease import Entity
		world = TestWorld()
		entity = Entity(world)
		component = TestComponent('baz')
		accessor = ComponentAccessor(component, entity)
		self.assertRaises(AttributeError, getattr, entity, 'baz')
		self.assertTrue(entity not in component)
		accessor.baz = 1000
		self.assertTrue(entity in component)
		self.assertEqual(accessor.baz, 1000)
		self.assertEqual(component.fields['baz'][entity], 1000)
	
	def test_truthiness(self):
		from grease.component.general import ComponentAccessor
		from grease import Entity
		world = TestWorld()
		entity = Entity(world)
		component = TestComponent()
		accessor = ComponentAccessor(component, entity)
		self.assertFalse(accessor)
		component.add(entity)
		self.assertTrue(accessor)



if __name__ == '__main__':
	unittest.main()
