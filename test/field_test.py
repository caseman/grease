import unittest


class TestData(object):

	def __init__(self, entity=None, **kw):
		self.entity = entity
		self.__dict__.update(kw)


class TestComponent(dict):

	def __init__(self, entities=()):
		self.entities = set(entities)
	
	def __getitem__(self, entity):
		return self.setdefault(entity, TestData(entity))


class TestField(object):

	def __init__(self, component, name):
		self.component = component
		self.name = name
		self.cast = int


class TestAccessor(object):

	def __init__(self, field, entities):
		self.field = field
		self.entities = entities
		

class FieldTestCase(unittest.TestCase):

	def test_basics(self):
		from grease.component.field import Field
		comp = TestComponent()

		f = Field(comp, "myfield", int)
		self.assertTrue(f.component is comp, (f.component, comp))
		self.assertTrue(f.type is int, f.type)
		self.assertEqual(f.default(), 0)
	
	def test_cast(self):
		from grease.component.field import Field
		from grease.geometry import Vec2d
		f = Field(None, "string", str)
		self.assertEqual(f.cast(22), "22")
		f = Field(None, "int", int)
		self.assertEqual(f.cast("42"), 42)
		f = Field(None, "vec", Vec2d)
		self.assertEqual(f.cast((11,12)), Vec2d(11,12))
	
	def test_accessor_default_set(self):
		from grease.component.field import Field
		comp = TestComponent()
		f = Field(comp, "acc_default", str, TestAccessor)
		acc = f.accessor()
		self.assertTrue(acc.field is f, (acc.field, f))
		self.assertTrue(acc.entities is comp.entities, (acc.entities, comp.entities))
	
	def test_accessor_subset(self):
		from grease.component.field import Field
		comp = TestComponent((1,2,3,4))
		f = Field(comp, "acc_default", str, TestAccessor)
		acc = f.accessor(set([2,4,6,8]))
		self.assertTrue(acc.field is f, (acc.field, f))
		self.assertEqual(acc.entities, set([2,4]))


class FieldAccessorTestCase(unittest.TestCase):

	def test_iter(self):
		from grease.component.field import FieldAccessor
		entities = set([1,5,9])
		comp = TestComponent()
		accessor = FieldAccessor(TestField(comp, 'entity'), entities)
		self.assertEqual(sorted(iter(accessor)), [1, 5, 9])
	
	def test_child_attr(self):
		from grease.component.field import FieldAccessor
		entities = set([1,2,3])
		comp = TestComponent()
		comp[1] = TestData(foo=TestData(bar=100, baz=TestData(spam=-1)))
		comp[2] = TestData(foo=TestData(bar=200, baz=TestData(spam=-2)))
		comp[3] = TestData(foo=TestData(bar=300, baz=TestData(spam=-3)))
		accessor = FieldAccessor(TestField(comp, 'foo'), entities)
		bar_acc = accessor.bar
		self.assertTrue(isinstance(bar_acc, FieldAccessor))
		self.assertEqual(bar_acc[1], 100)
		self.assertEqual(bar_acc[2], 200)
		self.assertEqual(bar_acc[3], 300)
		self.assertRaises(KeyError, lambda: bar_acc[4])
		baz_spam_acc = accessor.baz.spam
		self.assertTrue(isinstance(baz_spam_acc, FieldAccessor))
		self.assertEqual(baz_spam_acc[1], -1)
		self.assertEqual(baz_spam_acc[2], -2)
		self.assertEqual(baz_spam_acc[3], -3)
		self.assertRaises(KeyError, lambda: baz_spam_acc[4])
	
	def test_set(self):
		from grease.component.field import FieldAccessor
		entities = set([3,7,8])
		comp = TestComponent()
		for i in range(9):
			comp[i] = TestData(id=i, xy=TestData(x=i*10, y=i*-10))
		id_accessor = FieldAccessor(TestField(comp, 'id'), entities)
		xy_accessor = FieldAccessor(TestField(comp, 'xy'), entities)
		id_accessor.__set__(10)
		xy_accessor.x = 0
		for i in range(9):
			if i in entities:
				self.assertEqual(comp[i].id, 10)
				self.assertEqual(comp[i].xy.x, 0)
				self.assertEqual(comp[i].xy.y, i*-10)
			else:
				self.assertEqual(comp[i].id, i)
				self.assertEqual(comp[i].xy.x, i*10)
				self.assertEqual(comp[i].xy.y, i*-10)
	
	def test_set_join(self):
		from grease.component.field import FieldAccessor
		entities1 = set([2,3,7,8])
		entities2 = set([1,2,3])
		comp1 = TestComponent()
		comp2 = TestComponent()
		for i in range(9):
			comp1[i] = TestData(foo=i)
			comp2[i] = TestData(bar=-i)
		foo_accessor = FieldAccessor(TestField(comp1, 'foo'), entities1)
		bar_accessor = FieldAccessor(TestField(comp2, 'bar'), entities2)
		foo_accessor.__set__(bar_accessor)
		for i in range(9):
			if i in entities1 & entities2:
				self.assertEqual(comp1[i].foo, -i)
			else:
				self.assertEqual(comp1[i].foo, i)
			self.assertEqual(comp2[i].bar, -i)
		bar_accessor = FieldAccessor(TestField(comp2, 'bar'), entities1)
		foo_accessor.__set__(bar_accessor)
		for i in range(9):
			if i in entities1:
				self.assertEqual(comp1[i].foo, -i)
			else:
				self.assertEqual(comp1[i].foo, i)
			self.assertEqual(comp2[i].bar, -i)
		bar_accessor.__set__(foo_accessor)
		for i in range(9):
			if i in entities1:
				self.assertEqual(comp1[i].foo, comp2[i].bar)
			else:
				self.assertEqual(comp1[i].foo, i)
				self.assertEqual(comp2[i].bar, -i)
	
	def test_use_as_bool(self):
		from grease.component.field import FieldAccessor
		field = TestField(TestComponent(), 'test')
		self.assertFalse(FieldAccessor(field, set()))
		self.assertTrue(FieldAccessor(field, set([1,2,3])))
	
	def test_repr(self):
		from grease.component.field import FieldAccessor
		field = TestField(TestComponent(), 'test')
		accessor = FieldAccessor(field, set())
		self.assertTrue(
			repr(accessor).startswith('<FieldAccessor test '), repr(accessor))
		self.assertTrue(
			repr(accessor.foo.bar).startswith('<FieldAccessor test.foo.bar '),
			repr(accessor))
	
	def test_query_ops(self):
		from grease.component.field import FieldAccessor
		comp = TestComponent()
		for i in range(1,4):
			comp[i] = TestData(x=i*i, pos=TestData(x=i, y=-i))
			comp[i+3] = TestData(x=i*i, pos=TestData(x=i, y=-i))
			comp[i+6] = TestData(x=i*i, pos=TestData(x=i, y=-i))
		entities = set(range(1,7))
		x_accessor = FieldAccessor(TestField(comp, 'x'), entities)
		self.assertEqual(x_accessor == 4, set([2, 5]))
		self.assertEqual(x_accessor == 0, set())
		self.assertEqual(x_accessor != 1, set([2, 3, 5, 6]))
		self.assertEqual(x_accessor != 33, set([1, 2, 3, 4, 5, 6]))
		self.assertEqual(x_accessor > 5, set([3, 6]))
		self.assertEqual(x_accessor > 9, set())
		self.assertEqual(x_accessor >= 4, set([2, 3, 5, 6]))
		self.assertEqual(x_accessor >= 10, set())
		self.assertEqual(x_accessor < 2, set([1, 4]))
		self.assertEqual(x_accessor < 1, set())
		self.assertEqual(x_accessor <= 4, set([1, 2, 4, 5]))
		self.assertEqual(x_accessor <= -1, set())

		pos_accessor = FieldAccessor(TestField(comp, 'pos'), entities)
		self.assertEqual(pos_accessor.x == 3, set([3, 6]))
		self.assertEqual(pos_accessor.x < 3, set([1, 2, 4, 5]))
	
	def test_query_ops_join(self):
		from grease.component.field import FieldAccessor
		comp = TestComponent()
		entities1 = set([2,3,7,8])
		entities2 = set([1,2,3,8])
		comp1 = TestComponent()
		comp2 = TestComponent()
		for i in range(9):
			comp1[i] = TestData(foo=i)
			comp2[i] = TestData(bar=6-i)
		foo_accessor = FieldAccessor(TestField(comp1, 'foo'), entities1)
		bar_accessor = FieldAccessor(TestField(comp2, 'bar'), entities2)
		self.assertEqual(foo_accessor == bar_accessor, set([3]))
		self.assertEqual(foo_accessor > bar_accessor, set([8]))
		self.assertEqual(foo_accessor >= bar_accessor, set([3, 8]))
		self.assertEqual(foo_accessor <= bar_accessor, set([2, 3]))
		self.assertEqual(foo_accessor < bar_accessor, set([2]))
		self.assertEqual(foo_accessor != bar_accessor, set([2,8]))
	
	def test_inplace_mutators(self):
		from grease.component.field import FieldAccessor
		entities = set([2,6,7])
		comp = TestComponent()
		for i in range(9):
			comp[i] = TestData(size=i, xy=TestData(x=i*10, y=i*-10))
		xy_accessor = FieldAccessor(TestField(comp, 'xy'), entities)
		sa = size_accessor = FieldAccessor(TestField(comp, 'size'), entities)
		size_accessor += 1
		xy_accessor.y += 5
		self.assertTrue(sa is size_accessor, (sa, size_accessor))
		for i in range(9):
			if i in entities:
				self.assertEqual(comp[i].size, i + 1)
				self.assertEqual(comp[i].xy.y, i*-10 + 5)
			else:
				self.assertEqual(comp[i].size, i)
				self.assertEqual(comp[i].xy.y, i*-10)
			self.assertEqual(comp[i].xy.x, i*10)

		size_accessor -= 24
		size_accessor *= -12
		size_accessor /= 2
		size_accessor //= 3
		size_accessor %= 7
		size_accessor **= 2
		# TODO: these operators are broken in Python3
		# size_accessor <<= 3
		# size_accessor >>= 1
		# size_accessor |= 0x888
		# size_accessor &= 0xDD7
		# size_accessor ^= 0xF

		for i in range(9):
			if i in entities:
				expected = i + 1 - 24
				expected *= -12
				expected /= 2
				expected //= 3
				expected %= 7
				expected **= 2
				# expected <<= 3
				# expected >>= 1
				# expected |= 0x888
				# expected &= 0xDD7
				# expected ^= 0xF
				self.assertEqual(comp[i].size, expected)
			else:
				self.assertEqual(comp[i].size, i)
			self.assertEqual(comp[i].xy.x, i*10)
	
	def test_inplace_mutators_join(self):
		from grease.component.field import FieldAccessor
		comp = TestComponent()
		entities1 = set([2,3,7,8])
		entities2 = set([1,2,3,8])
		comp1 = TestComponent()
		comp2 = TestComponent()
		for i in range(9):
			comp1[i] = TestData(foo=i)
			comp2[i] = TestData(bar=i/2 + 1)
		foo_accessor = FieldAccessor(TestField(comp1, 'foo'), entities1)
		bar_accessor = FieldAccessor(TestField(comp2, 'bar'), entities2)
		foo_accessor += bar_accessor
		for i in range(9):
			if i in entities1 & entities2:
				self.assertEqual(comp1[i].foo, i + i/2 + 1)
			else:
				self.assertEqual(comp1[i].foo, i)
			self.assertEqual(comp2[i].bar, i/2 + 1)
		foo_accessor -= bar_accessor
		for i in range(9):
			self.assertEqual(comp1[i].foo, i)
			self.assertEqual(comp2[i].bar, i/2 + 1)


if __name__ == '__main__':
	unittest.main()

