import unittest
import operator


class TestController(object):
	
	runtime = 0
	manager = None
	order = 0

	def set_manager(self, manager):
		self.manager = manager
	
	def run(self, dt):
		self.runtime += dt
		TestController.order += 1
		self.order = TestController.order

class TestControllerInjector(TestController):

	def __init__(self, controller):
		self.injected = False
		self.controller = controller
	
	def run(self, dt):
		TestController.run(self, dt)
		if not self.injected:
			self.manager.controllers.add(self.controller)
			self.injected = True

class TestComponent(dict):
	
	manager = None

	def set_manager(self, manager):
		self.manager = manager
		self.entity_set = set()
		self.entity_id_set = set()
	
	def add(self, entity_id, data=None):
		self.entity_id_set.add(entity_id)
		self[entity_id] = data
	
class TestEntity(object):

	def __init__(self, manager, id):
		self.entity_id = id
		self.manager = manager
	
	def __eq__(self, other):
		return self.manager is other.manager and self.entity_id == other.entity_id
	
	def __repr__(self):
		return 'TestEntity(%s)' % self.entity_id
		

class Data(object):

	def __init__(self, **kw):
		self.__dict__.update(kw)


class ComponentEntityManagerTestCase(unittest.TestCase):

	def test_add_components_as_kwargs(self):
		from grease import ComponentEntityManager
		comp1 = TestComponent()
		comp2 = TestComponent()
		comp3 = TestComponent()
		manager = ComponentEntityManager(foo=comp1, bar=comp2, baz=comp3)
		self.assertFalse(manager.controllers)
		self.assertEqual(len(manager.components), 3)
		self.assertTrue(manager.components['foo'] is comp1)
		self.assertTrue(comp1.manager is manager)
		self.assertTrue(manager.foo is comp1.entity_set)
		self.assertTrue(manager.components['bar'] is comp2)
		self.assertTrue(comp2.manager is manager)
		self.assertTrue(manager.bar is comp2.entity_set)
		self.assertTrue(manager.components['baz'] is comp3)
		self.assertTrue(comp3.manager is manager)
		self.assertTrue(manager.baz is comp3.entity_set)
	
	def test_add_components_via_map(self):
		from grease import ComponentEntityManager
		comp1 = TestComponent()
		comp2 = TestComponent()
		comp3 = TestComponent()
		manager = ComponentEntityManager()
		self.assertFalse(manager.controllers)
		self.assertFalse(manager.components)
		self.assertRaises(AttributeError, getattr, manager, 'foobar')
		self.assertRaises(KeyError, lambda: manager.components['foobar'])
		manager.components['foobar'] = comp1
		self.assertTrue(manager.components['foobar'] is comp1)
		self.assertTrue(manager.foobar is comp1.entity_set)
		self.assertTrue(comp1.manager is manager)
		self.assertEqual(len(manager.components), 1)

		self.assertRaises(AttributeError, getattr, manager, 'spam')
		self.assertRaises(KeyError, lambda: manager.components['spam'])
		manager.components['spam'] = comp2
		self.assertTrue(manager.components['foobar'] is comp1)
		self.assertTrue(manager.components['spam'] is comp2)
		self.assertTrue(manager.foobar is comp1.entity_set)
		self.assertTrue(manager.spam is comp2.entity_set)
		self.assertTrue(comp2.manager is manager)
		self.assertEqual(len(manager.components), 2)

		manager.components['foobar'] = comp3
		self.assertFalse(manager.components['foobar'] is comp1)
		self.assertTrue(manager.components['foobar'] is comp3)
		self.assertTrue(manager.components['spam'] is comp2)
		self.assertFalse(manager.foobar is comp1.entity_set)
		self.assertTrue(manager.foobar is comp3.entity_set)
		self.assertTrue(manager.spam is comp2.entity_set)
		self.assertTrue(comp3.manager is manager)
		self.assertEqual(len(manager.components), 2)
	
	def test_iter_components(self):
		from grease import ComponentEntityManager
		comp1 = TestComponent()
		comp2 = TestComponent()
		comp3 = TestComponent()
		manager = ComponentEntityManager(foo=comp1, bar=comp2, baz=comp3)
		self.assertEqual(sorted(list(manager.components)), sorted([comp1, comp2, comp3]))
		

	def test_controller_name_collision(self):
		from grease import ComponentEntityManager
		from grease.component import ComponentError
		self.assertRaises(ComponentError, ComponentEntityManager, components=TestComponent())
		self.assertRaises(ComponentError, ComponentEntityManager, new_entity=TestComponent())
		manager = ComponentEntityManager(foo=TestComponent())
		newfoo = TestComponent()
		manager.components['foo'] = newfoo
		self.assertRaises(ComponentError, 
			manager.components.__setitem__, 'controllers', TestComponent())
		self.assertRaises(ComponentError, ComponentEntityManager, _foo=TestComponent())
	
	def test_add_controllers_at_init(self):
		from grease import ComponentEntityManager
		cont1 = TestController()
		cont2 = TestController()
		cont3 = TestController()
		controllers = [cont2, cont1, cont3]
		manager = ComponentEntityManager(controllers=controllers)
		self.assertFalse(manager.components)
		self.assertEqual(list(manager.controllers), controllers)
		controllers.remove(cont1)
		self.assertNotEqual(list(manager.controllers), controllers)
		self.assertTrue(cont1.manager is manager)
		self.assertTrue(cont2.manager is manager)
		self.assertTrue(cont3.manager is manager)
	
	def test_add_controller_via_list(self):
		from grease import ComponentEntityManager
		cont1 = TestController()
		cont2 = TestController()
		cont3 = TestController()
		manager = ComponentEntityManager()
		self.assertFalse(manager.components)
		self.assertFalse(manager.controllers)
		manager.controllers.add(cont1)
		self.assertEqual(list(manager.controllers), [cont1])
		manager.controllers.append(cont2)
		self.assertEqual(list(manager.controllers), [cont1, cont2])
		manager.controllers.add(cont3, cont1)
		self.assertEqual(list(manager.controllers), [cont3, cont1, cont2])
		self.assertTrue(cont1.manager is manager)
		self.assertTrue(cont2.manager is manager)
		self.assertTrue(cont3.manager is manager)
		self.assertRaises(ValueError, manager.controllers.add, TestController(), TestController())
		self.assertEqual(list(manager.controllers), [cont3, cont1, cont2])
	
	def test_remove_controller(self):
		from grease import ComponentEntityManager
		cont1 = TestController()
		cont2 = TestController()
		cont3 = TestController()
		manager = ComponentEntityManager(controllers=(cont1, cont2, cont3))
		self.assertEqual(tuple(manager.controllers), (cont1, cont2, cont3))
		manager.controllers.remove(cont1)
		self.assertEqual(tuple(manager.controllers), (cont2, cont3))
		manager.controllers.remove(cont3)
		self.assertEqual(tuple(manager.controllers), (cont2,))
		self.assertRaises(ValueError, manager.controllers.remove, cont1)
		self.assertEqual(tuple(manager.controllers), (cont2,))
	
	def test_controller_run_order(self):
		from grease import ComponentEntityManager
		cont1 = TestController()
		cont2 = TestController()
		cont3 = TestController()
		manager = ComponentEntityManager(controllers=(cont2, cont1))
		manager.controllers.add(cont3)
		self.assertEqual(len(manager.controllers), 3)
		self.assertTrue(cont1.runtime == cont2.runtime == cont3.runtime == 0)
		self.assertTrue(cont1.order == cont2.order == cont3.order == TestController.order)
		manager.controllers.run(0.13)
		self.assertTrue(cont1.runtime == cont2.runtime == cont3.runtime == 0.13)
		start = cont2.order
		self.assertEqual(cont1.order, start + 1)
		self.assertEqual(cont3.order, start + 2)
	
	def test_add_controller_during_run(self):
		from grease import ComponentEntityManager
		cont1 = TestController()
		to_inject = TestController()
		injector = TestControllerInjector(to_inject)
		manager = ComponentEntityManager(controllers=(injector, cont1))
		self.assertEqual(len(manager.controllers), 2)
		self.assertTrue(cont1.runtime == to_inject.runtime == injector.runtime == 0)
		self.assertFalse(injector.injected)
		manager.controllers.run(0.2)
		self.assertEqual(len(manager.controllers), 3)
		self.assertEqual(cont1.runtime, 0.2)
		self.assertEqual(injector.runtime, 0.2)
		self.assertEqual(to_inject.runtime, 0)
		self.assertTrue(injector.injected)
		manager.controllers.run(0.2)
		self.assertEqual(len(manager.controllers), 3)
		self.assertEqual(cont1.runtime, 0.4)
		self.assertEqual(injector.runtime, 0.4)
		self.assertEqual(to_inject.runtime, 0.2)
	
	def test_new_entity_no_template(self):
		from grease import ComponentEntityManager
		manager = ComponentEntityManager()
		manager._entity_factory = TestEntity
		self.assertEqual(len(manager), 0)
		entity = manager.new_entity()
		self.assertNotEqual(entity.entity_id, 0)
		self.assertTrue(entity.manager is manager)
		self.assertEqual(len(manager), 1)
		ids = set([entity.entity_id])
		for i in range(1000):
			ids.add(manager.new_entity())
		self.assertEqual(len(manager), len(ids))
	
	def test_new_entity_with_template(self):
		from grease import ComponentEntityManager
		foo_comp = TestComponent()
		bar_comp = TestComponent()
		manager = ComponentEntityManager(foo=foo_comp, bar=bar_comp)
		manager._entity_factory = TestEntity
		template = Data(foo=Data(f1=23, f2='argh'))
		entity = manager.new_entity(template)
		self.assertTrue(entity.entity_id in foo_comp)
		self.assertTrue(entity.entity_id not in bar_comp)
		self.assertEqual(foo_comp[entity.entity_id].f1, 23)
		self.assertEqual(foo_comp[entity.entity_id].f2, 'argh')

		template = Data(foo=None, bar=Data(go=False))
		entity = manager.new_entity(template)
		self.assertTrue(entity.entity_id in foo_comp)
		self.assertTrue(entity.entity_id in bar_comp)
		self.assertEqual(bar_comp[entity.entity_id].go, False)
	
	def test_new_entity_with_component_kwargs(self):
		from grease import ComponentEntityManager
		foo_comp = TestComponent()
		bar_comp = TestComponent()
		manager = ComponentEntityManager(foo=foo_comp, bar=bar_comp)
		manager._entity_factory = TestEntity
		entity = manager.new_entity(foo=Data(flim='flam'))
		self.assertTrue(entity.entity_id in foo_comp)
		self.assertTrue(entity.entity_id not in bar_comp)
		self.assertEqual(foo_comp[entity.entity_id].flim, 'flam')
		# kwarg data overrides template attrs
		template = Data(foo=Data(test=321), bar=Data(go=True))
		entity = manager.new_entity(template, foo=Data(test=123))
		self.assertTrue(entity.entity_id in foo_comp)
		self.assertTrue(entity.entity_id in bar_comp)
		self.assertEqual(bar_comp[entity.entity_id].go, True)
		self.assertEqual(foo_comp[entity.entity_id].test, 123)
	
	def test_new_entity_fails_cleanly(self):
		# Errors should not leave behind turds on entity creation
		from grease import ComponentEntityManager
		from grease.component import ComponentError
		foo_comp = TestComponent()
		bar_comp = TestComponent()
		manager = ComponentEntityManager(foo=foo_comp, bar=bar_comp)
		self.assertRaises(ComponentError, manager.new_entity, foo=Data(), baz=Data())
		self.assertEqual(len(manager), 0)
		self.assertEqual(len(foo_comp), 0)
		self.assertEqual(len(bar_comp), 0)
	
	def test_contains_entity(self):
		from grease import ComponentEntityManager
		manager = ComponentEntityManager()
		manager._entity_factory = TestEntity
		self.assertTrue(1 not in manager)
		entity = manager.new_entity()
		self.assertTrue(entity.entity_id in manager)
		self.assertTrue(entity in manager)
		del manager[entity]
		self.assertTrue(entity not in manager)
	
	def test_len(self):
		from grease import ComponentEntityManager
		manager = ComponentEntityManager()
		manager._entity_factory = TestEntity
		self.assertEqual(len(manager), 0)
		entity = manager.new_entity()
		self.assertEqual(len(manager), 1)
		[manager.new_entity() for _ in range(99)]
		self.assertEqual(len(manager), 100)
	
	def test_iter(self):
		from grease import ComponentEntityManager
		manager = ComponentEntityManager()
		manager._entity_factory = TestEntity
		entities = [manager.new_entity() for _ in range(20)]
		entity_id = operator.attrgetter('entity_id')
		self.assertEqual(
			sorted(iter(manager), key=entity_id), sorted(entities, key=entity_id))
	
	def test_iter_component_data(self):
		from grease import ComponentEntityManager
		foo_comp = TestComponent()
		bar_comp = TestComponent()
		baz_comp = TestComponent()
		manager = ComponentEntityManager(foo=foo_comp, bar=bar_comp, baz=baz_comp)
		manager._entity_factory = TestEntity
		entities = [manager.new_entity(foo=Data(), baz=Data()) for i in range(10)]
		bar_comp.add(entities[4].entity_id, Data())
		bar_comp.add(entities[8].entity_id, Data())
		self.assertEqual(list(manager.components.iter_data()), [])
		self.assertEqual(sorted(manager.components.iter_data('baz')),
			sorted((d,) for d in baz_comp.itervalues()))
		self.assertEqual(sorted(manager.components.iter_data('foo', 'baz')),
			sorted((foo_comp[id], baz_comp[id]) for id in foo_comp))
		self.assertEqual(sorted(manager.components.iter_data('baz', 'foo')),
			sorted((baz_comp[id], foo_comp[id]) for id in foo_comp))
		self.assertEqual(sorted(manager.components.iter_data('baz', 'bar')),
			sorted((baz_comp[id], bar_comp[id]) for id in bar_comp))

	def test_entity_sets(self):
		from grease import ComponentEntityManager
		manager = ComponentEntityManager()
		manager._entity_factory = TestEntity
		entities = [manager.new_entity() for _ in range(20)]
		entity_id = operator.attrgetter('entity_id')
		self.assertEqual(
			sorted(manager.entity_set, key=entity_id), sorted(entities, key=entity_id))
		id_set = set(e.entity_id for e in entities)
		self.assertEqual(manager.entity_id_set, id_set)
	
	def test_getitem(self):
		from grease import ComponentEntityManager
		manager = ComponentEntityManager()
		manager._entity_factory = TestEntity
		self.assertRaises(KeyError, manager.__getitem__, 1)
		entities = [manager.new_entity() for _ in range(10)]
		for e in entities:
			self.assertEqual(e, manager[e.entity_id])

	def test_delitem(self):
		from grease import ComponentEntityManager
		foo_comp = TestComponent()
		bar_comp = TestComponent()
		manager = ComponentEntityManager(foo=foo_comp, bar=bar_comp)
		manager._entity_factory = TestEntity
		self.assertRaises(KeyError, manager.__delitem__, 1)
		entities = [manager.new_entity(foo=Data()) for i in range(10)]
		self.assertEqual(len(manager), 10)
		self.assertEqual(manager.entity_id_set, set(foo_comp))
		self.assertTrue(entities[3] in manager)
		self.assertTrue(entities[3].entity_id in foo_comp)
		del manager[entities[3]]
		self.assertEqual(len(manager), 9)
		self.assertTrue(entities[3] not in manager)
		self.assertTrue(entities[3].entity_id not in foo_comp)
		self.assertEqual(manager.entity_id_set, set(foo_comp))
		self.assertTrue(entities[8] in manager)
		self.assertTrue(entities[8].entity_id in foo_comp)
		del manager[entities[8].entity_id]
		self.assertEqual(len(manager), 8)
		self.assertTrue(entities[8] not in manager)
		self.assertTrue(entities[8].entity_id not in foo_comp)
		self.assertEqual(manager.entity_id_set, set(foo_comp))
		self.assertRaises(KeyError, manager.__delitem__, entities[8].entity_id)
	

if __name__ == '__main__':
	unittest.main()
