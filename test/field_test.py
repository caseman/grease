import unittest


class TestData(object):
	pass


class TestComponent(object):

	def __init__(self, ids=()):
		self.data = {}
		self.entity_id_set = set(ids)
	
	def __getitem__(self, id):
		return self.data.setdefault(id, TestData())


class TestAccessor(object):

	def __init__(self, field, ids):
		self.field = field
		self.ids = ids
		

class FieldTest(unittest.TestCase):

	def test_basics(self):
		from grease.component.field import Field
		comp = TestComponent()

		f = Field(comp, "myfield", int)
		self.assertTrue(f.component is comp, (f.component, comp))
		self.assertTrue(f.type is int, f.type)
		self.assertEqual(f.default(), 0)
	
	def test_cast(self):
		from grease.component.field import Field
		from grease.vector import Vec2d
		f = Field(None, "string", str)
		self.assertEqual(f.cast(22), "22")
		f = Field(None, "int", int)
		self.assertEqual(f.cast("42"), 42)
		f = Field(None, "vec", Vec2d)
		self.assertEqual(f.cast((11,12)), Vec2d(11,12))
	
	def test_set(self):
		from grease.component.field import Field
		comp = TestComponent([8,11,12,13])
		f = Field(comp, "test_set", int)
		f.set(49)
		for id in set([8,11,12,13]):
			self.assertEqual(comp.data[id].test_set, 49)

		entity_ids = set([4,11,12])
		f.set("34", entity_ids)
		self.assertEqual(len(comp.data), 4)
		self.assertEqual(comp.data[8].test_set, 49)
		self.assertEqual(comp.data[11].test_set, 34)
		self.assertEqual(comp.data[12].test_set, 34)
		self.assertEqual(comp.data[13].test_set, 49)
	
	def test_accessor_default_set(self):
		from grease.component.field import Field
		comp = TestComponent()
		f = Field(comp, "acc_default", str, TestAccessor)
		acc = f.accessor()
		self.assertTrue(acc.field is f, (acc.field, f))
		self.assertTrue(acc.ids is comp.entity_id_set, (acc.ids, comp.entity_id_set))
	
	def test_accessor_subset(self):
		from grease.component.field import Field
		comp = TestComponent((1,2,3,4))
		f = Field(comp, "acc_default", str, TestAccessor)
		acc = f.accessor(set([2,4,6,8]))
		self.assertTrue(acc.field is f, (acc.field, f))
		self.assertEqual(acc.ids, set([2,4]))


class FieldAccessorTest(unittest.TestCase):

	def test_iter(self):
		from grease.component.field import FieldAccessor
		

if __name__ == '__main__':
	unittest.main()
