import unittest

class TestComponent(dict):
	
	world = None
	runtime = 0

	def __init__(self):
		self.entities = set()

	def set_world(self, world):
		self.world = world
	
	def add(self, entity, data=None):
		self[entity] = data
		self.entities.add(entity)
	
	def step(self, dt):
		self.runtime += dt

class TestSystem(object):
	
	runtime = 0
	world = None
	order = 0

	def set_world(self, world):
		self.world = world
	
	def step(self, dt):
		self.runtime += dt
		TestSystem.order += 1
		self.order = TestSystem.order

class TestSystemInjector(TestSystem):

	def __init__(self, name, system):
		self.injected = False
		self.name = name
		self.system = system
	
	def step(self, dt):
		TestSystem.step(self, dt)
		if not self.injected:
			self.world.systems.add((self.name, self.system))
			self.injected = True

class TestWindow(object):
	cleared = False

	def clear(self):
		self.cleared = True

	def on_draw(self):
		pass

class TestRenderer(object):
	world = None
	drawn = False
	order = 0

	def draw(self):
		self.drawn = True
		TestRenderer.order += 1
		self.order = TestRenderer.order

	def set_world(self, world):
		self.world = world

class TestGL(object):
	matrix_reset = False
	def glLoadIdentity(self):
		self.matrix_reset = True

class TestClock(object):
	def __init__(self):
		self.scheduled = []

	def schedule_interval(self, what, interval):
		self.scheduled.append((what, interval))
	
	def unschedule(self, what):
		for i in range(len(self.scheduled)):
			if self.scheduled[i][0] == what:
				del self.scheduled[i]
				return


class WorldTestCase(unittest.TestCase):

	def test_defaults(self):
		from grease import World
		world = World()
		self.assertEqual(world.window, None)
		self.assertEqual(world.step_rate, 60)
		self.assertTrue(world.running)
	
	def test_overrides(self):
		from grease import World
		window = TestWindow()
		world = World(window, 30, False)
		self.assertTrue(world.window is window)
		self.assertEqual(window.on_draw, world.on_draw)
		self.assertEqual(world.step_rate, 30)
		self.assertFalse(world.running)

	def test_get_wrapped_entity_type(self):
		from grease import World
		class MyEntity(object): pass
		world = World(entity_types={'MyEntity': MyEntity})
		Wrapped = world.MyEntity
		self.assertTrue(issubclass(Wrapped, MyEntity))
		self.assertTrue(Wrapped is not MyEntity)
	
	def test_create_entities_in_context(self):
		from grease import World
		stuffs = []
		class MyEntity(object):
			def __init__(self, stuff):
				stuffs.append(stuff)
		class Another(object): pass
		class Subclass(Another, MyEntity): pass
		world = World(entity_types={
			'MyEntity': MyEntity, 'Another': Another, 'Subclass':Subclass})
		entity = world.MyEntity('abc')
		self.assertTrue(isinstance(entity, MyEntity))
		self.assertTrue(entity.entity_id > 0)
		self.assertTrue(entity in world.entities)
		self.assertTrue(entity in world.MyEntity.entities)
		self.assertTrue(entity not in world.Another.entities)
		self.assertTrue(entity not in world.Subclass.entities)
		self.assertEqual(stuffs, ['abc'])
		
		another = world.Another()
		self.assertTrue(another.entity_id > 0)
		self.assertNotEqual(another.entity_id, entity.entity_id)
		self.assertTrue(another in world.entities)
		self.assertTrue(another not in world.MyEntity.entities)
		self.assertTrue(another in world.Another.entities)
		self.assertTrue(another not in world.Subclass.entities)
		self.assertEqual(stuffs, ['abc'])

		yetanother = world.Another()
		self.assertTrue(yetanother.entity_id > 0)
		self.assertNotEqual(yetanother.entity_id, entity.entity_id)
		self.assertNotEqual(yetanother.entity_id, another.entity_id)
		self.assertTrue(yetanother in world.entities)
		self.assertTrue(yetanother not in world.MyEntity.entities)
		self.assertTrue(yetanother in world.Another.entities)

		sub = world.Subclass('123')
		self.assertTrue(sub.entity_id > 0)
		self.assertTrue(sub in world.entities)
		self.assertTrue(sub in world.MyEntity.entities)
		self.assertTrue(sub in world.Another.entities)
		self.assertTrue(sub in world.Subclass.entities)
		self.assertEqual(stuffs, ['abc', '123'])
	
	def test_entities_set(self):
		from grease import World
		class Entity1(object): pass
		class Entity2(object): pass
		class Entity3(object): pass
		world = World(entity_types={'Entity1': Entity1, 'Entity2': Entity2, 'Entity3': Entity3})
		self.assertEqual(world.entities, set())
		self.assertEqual(world.Entity1.entities, set())
		self.assertEqual(world.Entity2.entities, set())
		self.assertEqual(world.Entity3.entities, set())
		test_entities = (world.Entity1(), world.Entity1(), world.Entity2())
		self.assertEqual(world.entities, set(test_entities))
		self.assertEqual(world.Entity1.entities, set(test_entities[:2]))
		self.assertEqual(world.Entity2.entities, set(test_entities[2:]))
		self.assertEqual(world.Entity3.entities, set())
	
	def test_map_components(self):
		from grease import World
		comp1 = TestComponent()
		comp2 = TestComponent()
		comp3 = TestComponent()
		world = World()
		self.assertEqual(len(world.components), 0)
		world.components.map(one=comp1, two=comp2, three=comp3)
		self.assertEqual(len(world.components), 3)
		self.assertTrue(world.components['one'] is comp1)
		self.assertTrue(world.components['two'] is comp2)
		self.assertTrue(world.components['three'] is comp3)
		self.assertTrue(comp1.world is world)
		self.assertTrue(comp2.world is world)
		self.assertTrue(comp3.world is world)

	def test_set_components(self):
		from grease import World
		comp1 = TestComponent()
		comp2 = TestComponent()
		comp3 = TestComponent()
		world = World()
		self.assertFalse(world.systems)
		self.assertFalse(world.components)
		self.assertRaises(KeyError, lambda: world.components['foobar'])
		world.components['foobar'] = comp1
		self.assertTrue(world.components['foobar'] is comp1)
		self.assertTrue(comp1.world is world)
		self.assertEqual(len(world.components), 1)

		self.assertRaises(KeyError, lambda: world.components['spam'])
		world.components['spam'] = comp2
		self.assertTrue(world.components['foobar'] is comp1)
		self.assertTrue(world.components['spam'] is comp2)
		self.assertTrue(comp2.world is world)
		self.assertEqual(len(world.components), 2)

		world.components['foobar'] = comp3
		self.assertFalse(world.components['foobar'] is comp1)
		self.assertTrue(world.components['foobar'] is comp3)
		self.assertTrue(world.components['spam'] is comp2)
		self.assertTrue(comp3.world is world)
		self.assertEqual(len(world.components), 2)
	
	def test_iter_components(self):
		from grease import World
		comp1 = TestComponent()
		comp2 = TestComponent()
		comp3 = TestComponent()
		world = World()
		world.components.map(foo=comp1, bar=comp2)
		world.components['baz'] = comp3
		self.assertEqual(sorted(list(world.components)), sorted([comp1, comp2, comp3]))
	
	def test_step_components(self):
		from grease import World
		comp1 = TestComponent()
		comp2 = TestComponent()
		world = World()
		world.components.map(foo=comp1, bar=comp2)
		self.assertTrue(comp1.runtime == comp2.runtime == 0, comp1.runtime)
		world.components.step(0.5)
		self.assertEqual(comp1.runtime, 0.5)
		self.assertEqual(comp2.runtime, 0.5)
		world.components.step(0.75)
		self.assertEqual(comp1.runtime, 1.25)
		self.assertEqual(comp2.runtime, 1.25)

	def test_join_components(self):
		from grease import World
		comp1 = TestComponent()
		comp2 = TestComponent()
		comp3 = TestComponent()
		for i in range(20):
			entity = object()
			comp1.add(entity, i)
			if i < 5:
				comp2.add(entity, i * 10)
			if i < 3:
				comp3.add(entity, i * 100)
		world = World()
		world.components.map(foo=comp1, bar=comp2, baz=comp3)
		self.assertEqual(sorted(world.components.join('baz', 'bar', 'foo')), [
			(0, 0, 0), (100, 10, 1), (200, 20, 2)])
		self.assertEqual(sorted(world.components.join('foo', 'bar')), [
			(0, 0), (1, 10), (2, 20), (3, 30), (4, 40)])
		self.assertEqual(sorted(world.components.join('baz')), [
			(0,), (100,), (200,)])

	def test_system_illegal_name(self):
		from grease import World
		from grease.component import ComponentError
		world = World()
		self.assertRaises(ComponentError, world.systems.add, ('add', None))
		self.assertRaises(ComponentError, world.systems.add, ('_reserved', None))
		world.systems.add(('foo', None))
		self.assertRaises(ComponentError, world.systems.add, ('foo', None))
	
	def test_add_systems(self):
		from grease import World
		sys1 = TestSystem()
		sys2 = TestSystem()
		sys3 = TestSystem()
		systems = [('one', sys1), ('two', sys2), ('three', sys3)]
		world = World()
		self.assertFalse(world.systems)
		world.systems.add(*systems)
		self.assertEqual(list(world.systems), [sys[1] for sys in systems])
		self.assertTrue(world.systems.one is sys1)
		self.assertTrue(world.systems.two is sys2)
		self.assertTrue(world.systems.three is sys3)
		self.assertTrue(sys1.world is world)
		self.assertTrue(sys2.world is world)
		self.assertTrue(sys3.world is world)
		return systems, world
	
	def test_remove_systems(self):
		systems, world = self.test_add_systems()
		sys1, sys2, sys3 = [sys[1] for sys in systems]
		world.systems.remove('one')
		self.assertEqual(list(world.systems), [sys[1] for sys in systems[1:]])
		self.assertRaises(AttributeError, getattr, world.systems, 'one')
		self.assertTrue(world.systems.two is sys2)
		self.assertTrue(world.systems.three is sys3)
		self.assertRaises(AttributeError, world.systems.remove, 'one')
		world.systems.remove('three')
		self.assertEqual(list(world.systems), [sys[1] for sys in systems[1:2]])
		self.assertRaises(AttributeError, getattr, world.systems, 'one')
		self.assertTrue(world.systems.two is sys2)
		self.assertRaises(AttributeError, getattr, world.systems, 'three')
	
	def test_insert_system_before(self):
		systems, world = self.test_add_systems()
		inserted = TestSystem()
		world.systems.insert('inserted', inserted, before='two')
		systems.insert(1, ('inserted', inserted))
		self.assertEqual(list(world.systems), [sys[1] for sys in systems])
		another = TestSystem()
		world.systems.insert('another', another, before=world.systems.inserted)
		systems.insert(1, ('another', another))
		self.assertEqual(list(world.systems), [sys[1] for sys in systems])
	
	def test_system_step_order(self):
		from grease import World
		sys1 = TestSystem()
		sys2 = TestSystem()
		sys3 = TestSystem()
		world = World()
		world.systems.add(('one', sys1), ('three', sys3))
		world.systems.insert('two', sys2, index=1)
		self.assertEqual(len(world.systems), 3)
		self.assertTrue(sys1.runtime == sys2.runtime == sys3.runtime == 0)
		self.assertTrue(sys1.order == sys2.order == sys3.order == TestSystem.order)
		world.systems.step(0.13)
		self.assertTrue(sys1.runtime == sys2.runtime == sys3.runtime == 0.13)
		start = sys1.order
		self.assertEqual(sys2.order, start + 1)
		self.assertEqual(sys3.order, start + 2)
	
	def test_add_system_during_run(self):
		from grease import World
		sys1 = TestSystem()
		to_inject = TestSystem()
		injector = TestSystemInjector('injected', to_inject)
		world = World()
		world.systems.add(('one', sys1), ('injector', injector))
		self.assertEqual(len(world.systems), 2)
		self.assertTrue(sys1.runtime == to_inject.runtime == injector.runtime == 0)
		self.assertFalse(injector.injected)
		world.systems.step(0.2)
		self.assertEqual(len(world.systems), 3)
		self.assertEqual(sys1.runtime, 0.2)
		self.assertEqual(injector.runtime, 0.2)
		self.assertEqual(to_inject.runtime, 0)
		self.assertTrue(injector.injected)
		world.systems.step(0.2)
		self.assertEqual(len(world.systems), 3)
		self.assertEqual(sys1.runtime, 0.4)
		self.assertEqual(injector.runtime, 0.4)
		self.assertEqual(to_inject.runtime, 0.2)
	
	def test_step_increments_world_time(self):
		from grease import World
		world = World()
		self.assertEqual(world.time, 0)
		dt = 1.0/30.0
		world.step(dt)
		self.assertAlmostEqual(world.time, dt)
		world.step(dt)
		self.assertAlmostEqual(world.time, dt*2)
	
	def test_step_max_dt(self):
		from grease import World
		sys1 = TestSystem()
		comp1 = TestComponent()
		world = World()
		world.components.map(foo=comp1)
		world.systems.add(('sys', sys1))
		world.step(10000)
		self.assertEqual(comp1.runtime, 10.0 / world.step_rate)
		self.assertEqual(sys1.runtime, 10.0 / world.step_rate)
	
	def test_get_set_renderers(self):
		from grease import World
		world = World()
		self.assertEqual(tuple(world.renderers), ())
		renderer1 = TestRenderer()
		renderer2 = TestRenderer()
		renderer3 = object() # arbitrary objects should be supported as renderers
		world.renderers = (renderer1, renderer2, renderer3)
		self.assertEqual(tuple(world.renderers), (renderer1, renderer2, renderer3))
		# objects with a set_world() method should have it called when set
		self.assertTrue(renderer1.world is world)
		self.assertTrue(renderer2.world is world)
	
	def test_on_draw(self):
		from grease import World
		sys2 = TestSystem()
		window = TestWindow()
		world = World(window)
		renderer1 = TestRenderer()
		renderer2 = TestRenderer()
		world.renderers = [renderer1, renderer2]
		gl = TestGL()
		self.assertFalse(window.cleared)
		self.assertFalse(gl.matrix_reset)
		self.assertFalse(renderer1.drawn)
		self.assertFalse(renderer2.drawn)
		window.on_draw(gl=gl)
		self.assertTrue(window.cleared)
		self.assertTrue(gl.matrix_reset)
		self.assertTrue(renderer1.drawn)
		self.assertTrue(renderer2.drawn)
		start = renderer1.order
		self.assertEqual(renderer2.order, start + 1)
	
	def test_start(self):
		from grease import World
		clock = TestClock()
		world = World(start=False, clock=clock)
		self.assertFalse(world.running)
		self.assertFalse(clock.scheduled)
		world.start()
		self.assertTrue(world.running)
		self.assertEqual(clock.scheduled, [(world.step, 1.0 / world.step_rate)])
		# repeated calls to start() should have no effect
		world.start()
		self.assertTrue(world.running)
		self.assertEqual(clock.scheduled, [(world.step, 1.0 / world.step_rate)])
		return world, clock
	
	def test_stop(self):
		world, clock = self.test_start()
		self.assertTrue(world.running)
		world.stop()
		self.assertFalse(world.running)
		self.assertFalse(clock.scheduled)
		# repeated calls to stop should have no effect
		world.stop()
		self.assertFalse(world.running)
		self.assertFalse(clock.scheduled)
		

if __name__ == '__main__':
	unittest.main()

