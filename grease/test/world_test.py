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
			setattr(self.world.systems, self.name, self.system)
			self.injected = True

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
	cleared = False

	GL_DEPTH_BUFFER_BIT = 1
	GL_COLOR_BUFFER_BIT = 2

	def glClear(self, bits):
		self.cleared = bits
	
	def glLoadIdentity(self):
		self.matrix_reset = True

class TestClock(object):
	def __init__(self, time_function=None):
		self.scheduled = []
		self.time_func = time_function
		self.ticks = 0

	def schedule_interval(self, what, interval):
		self.scheduled.append((what, interval))
	
	def schedule(self, what):
		self.scheduled.append((what, None))
	
	def unschedule(self, what):
		for i in range(len(self.scheduled)):
			if self.scheduled[i][0] == what:
				del self.scheduled[i]
				return
	
	def tick(self, poll=True):
		self.ticks += 1

class TestModeManager(object):
	def __init__(self):
		self.handlers = []
		self.event_dispatcher = self
	
	def push_handlers(self, handler):
		self.handlers.append(handler)

	def remove_handlers(self, handler):
		self.handlers.remove(handler)


class WorldTestCase(unittest.TestCase):

	def test_defaults(self):
		from grease import World
		world = World(clock_factory=TestClock)
		self.assertEqual(world.step_rate, 60)
		self.assertFalse(world.active)
		self.assertTrue(world.running)
		self.assertEqual(world.time, 0)
		self.assertTrue((world.step, 1.0/60) in world.clock.scheduled)
	
	def test_overrides(self):
		from grease import World
		world = World(step_rate=30, clock_factory=TestClock)
		self.assertEqual(world.step_rate, 30)
		self.assertTrue((world.step, 1.0/30) in world.clock.scheduled)

	def test_create_entities_in_world(self):
		from grease import World, Entity
		world = World()
		self.assertFalse(world.entities)
		e1 = Entity(world)
		e2 = Entity(world)
		self.assertEqual(len(world.entities), 2)
		self.assertTrue(e1 in world.entities)
		self.assertTrue(e1.world is world)
		self.assertTrue(e2 in world.entities)
		self.assertTrue(e2.world is world)
		self.assertNotEqual(e1, e2)
	
	def test_worlds_disjoint(self):
		from grease import World, Entity
		world1 = World()
		world2 = World()
		self.assertTrue(world1 is not world2)
		e1 = Entity(world1)
		e2 = Entity(world2)
		self.assertEqual(len(world1.entities), 1)
		self.assertEqual(len(world2.entities), 1)
		self.assertTrue(e1.world is world1)
		self.assertTrue(e2.world is world2)
		self.assertTrue(e1 in world1.entities)
		self.assertFalse(e2 in world1.entities)
		self.assertFalse(e1 in world2.entities)
		self.assertTrue(e2 in world2.entities)
		self.assertNotEqual(e1, e2)
	
	def test_remove_entity(self):
		from grease import World, Entity
		world = World()
		comp1 = world.components.one = TestComponent()
		comp2 = world.components.two = TestComponent()
		comp3 = world.components.three = TestComponent()
		entity = Entity(world)
		comp1.add(entity)
		comp2.add(entity)
		self.assertTrue(entity in world.entities)
		self.assertTrue(entity in comp1)
		self.assertTrue(entity in comp2)
		self.assertFalse(entity in comp3)
		world.entities.remove(entity)
		self.assertFalse(entity in world.entities)
		self.assertFalse(entity in comp1)
		self.assertFalse(entity in comp2)
		self.assertFalse(entity in comp3)
		self.assertRaises(KeyError, world.entities.remove, entity)
	
	def test_discard_entity(self):
		from grease import World, Entity
		world = World()
		comp1 = world.components.one = TestComponent()
		comp2 = world.components.two = TestComponent()
		comp3 = world.components.three = TestComponent()
		entity = Entity(world)
		comp1.add(entity)
		comp2.add(entity)
		self.assertTrue(entity in world.entities)
		self.assertTrue(entity in comp1)
		self.assertTrue(entity in comp2)
		self.assertFalse(entity in comp3)
		world.entities.discard(entity)
		self.assertFalse(entity in world.entities)
		self.assertFalse(entity in comp1)
		self.assertFalse(entity in comp2)
		self.assertFalse(entity in comp3)
		world.entities.discard(entity)
		self.assertFalse(entity in world.entities)
		self.assertFalse(entity in comp1)
		self.assertFalse(entity in comp2)
		self.assertFalse(entity in comp3)
	
	def test_entity_class_set_membership_simple(self):
		from grease import World, Entity
		class MyEntity(Entity):
			pass
		class Another(Entity):
			pass
		world = World()
		self.assertFalse(world.entities)
		class_set = world[MyEntity]
		self.assertFalse(class_set)
		entity1 = MyEntity(world)
		self.assertTrue(entity1 in class_set)
		entity2 = MyEntity(world)
		self.assertTrue(entity2 in class_set)
		world.entities.remove(entity2)
		self.assertTrue(entity1 in class_set)
		self.assertFalse(entity2 in class_set)
		entity3 = Another(world)
		self.assertFalse(entity3 in class_set)
		self.assertTrue(entity3 in world[Another])
	
	def test_entity_superclass_class_sets(self):
		from grease import World, Entity
		class Superentity(Entity):
			pass
		class Subentity(Superentity):
			pass
		class SubSubentity(Subentity):
			pass
		class Another(Entity):
			pass
		world = World()
		super_class_set = world[Superentity]
		super = Superentity(world)
		sub = Subentity(world)
		subsub = SubSubentity(world)
		another = Another(world)
		self.assertTrue(super in super_class_set)
		self.assertTrue(sub in super_class_set)
		self.assertTrue(subsub in super_class_set)
		self.assertFalse(another in super_class_set)
		sub_class_set = world[Subentity]
		self.assertFalse(super in sub_class_set)
		self.assertTrue(sub in sub_class_set)
		self.assertTrue(subsub in sub_class_set)
		self.assertFalse(another in sub_class_set)
		subsub_class_set = world[SubSubentity]
		self.assertFalse(super in subsub_class_set)
		self.assertFalse(sub in subsub_class_set)
		self.assertTrue(subsub in subsub_class_set)
		self.assertFalse(another in subsub_class_set)
		another_class_set = world[Another]
		self.assertFalse(super in another_class_set)
		self.assertFalse(sub in another_class_set)
		self.assertFalse(subsub in another_class_set)
		self.assertTrue(another in another_class_set)
		world.entities.remove(subsub)
		self.assertFalse(subsub in super_class_set)
		self.assertFalse(subsub in sub_class_set)
		self.assertFalse(subsub in subsub_class_set)
		self.assertFalse(subsub in another_class_set)
	
	def test_union_class_set(self):
		from grease import World, Entity
		class Entity1(Entity):
			pass
		class Entity2(Entity1):
			pass
		class Entity3(Entity):
			pass
		world = World()
		entities = [Entity1(world), Entity2(world), Entity2(world), Entity3(world)]
		self.assertEqual(sorted(world[Entity1, Entity2]), sorted(entities[:-1]))
		self.assertEqual(sorted(world[Entity2, Entity3]), sorted(entities[1:]))
		self.assertEqual(sorted(world[Entity1, Entity3]), sorted(entities))
	
	def test_empty_class_set(self):
		from grease import World, Entity
		world = World()
		e = Entity(world)
		class Entity1(Entity):
			pass
		self.assertEqual(len(world[Entity1]), 0)
		
	def test_empty_union_class_set(self):
		from grease import World, Entity
		world = World()
		e = Entity(world)
		class Entity1(Entity):
			pass
		class Entity2(Entity):
			pass
		class Entity3(Entity1):
			pass
		self.assertEqual(len(world[Entity2, Entity3]), 0)

	def test_full_set(self):
		from grease import World, Entity
		class Entity1(Entity):
			pass
		class Entity2(Entity1):
			pass
		class Entity3(Entity):
			pass
		world = World()
		full_set = world[Entity]
		self.assertEqual(world.entities, full_set)
		entities = sorted([Entity1(world), Entity2(world), Entity3(world), Entity1(world)])
		self.assertEqual(sorted(world.entities), entities)
		self.assertEqual(sorted(full_set), entities)
	
	def test_delete(self):
		from grease import World, Entity
		from grease.set import EntitySet
		class Entity1(Entity):
			pass
		class Entity2(Entity):
			pass
		class Entity3(Entity):
			pass
		world = World()
		entities = [Entity1(world), Entity2(world), Entity2(world), Entity3(world)]
		s = EntitySet(world)
		s.add(entities[2])
		s.add(entities[3])
		world.delete(s)
		self.assertEqual(sorted(world.entities), sorted(entities[:2]))
		self.assertEqual(list(world[Entity1]), [entities[0]])
		self.assertEqual(list(world[Entity2]), [entities[1]])
		self.assertEqual(list(world[Entity3]), [])


	def test_configure_components(self):
		from grease import World
		comp1 = TestComponent()
		comp2 = TestComponent()
		comp3 = TestComponent()
		world = World()
		self.assertEqual(len(world.components), 0)
		world.components.one = comp1
		world.components.two = comp2
		world.components.three = comp3
		self.assertEqual(list(world.components), [comp1, comp2, comp3])
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
		self.assertRaises(AttributeError, getattr, world, 'foobar')
		world.components.foobar = comp1
		self.assertTrue(world.components.foobar is comp1)
		self.assertTrue(comp1.world is world)
		self.assertEqual(len(world.components), 1)

		self.assertRaises(AttributeError, getattr, world, 'spam')
		world.components.spam = comp2
		self.assertTrue(world.components.spam is comp2)
		self.assertTrue(comp2.world is world)
		self.assertEqual(len(world.components), 2)

		self.assertRaises(AttributeError, getattr, world, 'foobar')
		world.components.foobar = comp3
		self.assertTrue(world.components.foobar is comp3)
		self.assertTrue(comp3.world is world)
		self.assertEqual(len(world.components), 2)
		self.assertEqual(list(world.components), [comp3, comp2])
	
	def test_del_component(self):
		from grease import World
		world = World()
		comp1 = world.components.one = TestComponent()
		comp2 = world.components.two = TestComponent()
		comp3 = world.components.three = TestComponent()
		self.assertEqual(list(world.components), [comp1, comp2, comp3])
		del world.components.two
		self.assertEqual(list(world.components), [comp1, comp3])
		del world.components.one
		self.assertEqual(list(world.components), [comp3])
		self.assertRaises(AttributeError, delattr, world, 'one')

	def test_step_components(self):
		from grease import World, Entity
		world = World()
		comp1 = world.components.one = TestComponent()
		comp2 = world.components.two = TestComponent()
		entity = Entity(world)
		self.assertTrue(comp1.runtime == comp2.runtime == 0, comp1.runtime)
		world.step(0.05)
		self.assertEqual(comp1.runtime, 0.05)
		self.assertEqual(comp2.runtime, 0.05)
		world.step(0.06)
		self.assertEqual(comp1.runtime, 0.11)
		self.assertEqual(comp2.runtime, 0.11)

	def test_join_components(self):
		from grease import World, Entity
		world = World()
		comp1 = world.components.foo = TestComponent()
		comp2 = world.components.bar = TestComponent()
		comp3 = world.components.baz = TestComponent()
		entity = Entity(world)
		for i in range(20):
			entity = object()
			comp1.add(entity, i)
			if i < 5:
				comp2.add(entity, i * 10)
			if i < 3:
				comp3.add(entity, i * 100)
		self.assertEqual(sorted(world.components.join('baz', 'bar', 'foo')), [
			(0, 0, 0), (100, 10, 1), (200, 20, 2)])
		self.assertEqual(sorted(world.components.join('foo', 'bar')), [
			(0, 0), (1, 10), (2, 20), (3, 30), (4, 40)])
		self.assertEqual(sorted(world.components.join('baz')), [
			(0,), (100,), (200,)])

	def test_illegal_part_name(self):
		from grease import World
		from grease.component import ComponentError
		world = World()
		self.assertRaises(ComponentError, 
			setattr, world.components, 'entities', TestComponent())
		self.assertRaises(ComponentError, 
			setattr, world.systems, 'entities', TestSystem())
		self.assertRaises(ComponentError, 
			setattr, world.renderers, 'entities', TestRenderer())
		self.assertRaises(ComponentError, 
			setattr, world.components, '_reserved', TestComponent())
		self.assertRaises(ComponentError, 
			setattr, world.systems, '_reserved', TestSystem())
		self.assertRaises(ComponentError, 
			setattr, world.renderers, '_reserved', TestRenderer())
		self.assertRaises(AttributeError, 
			setattr, world.components, 'insert', TestComponent())
		self.assertRaises(AttributeError, 
			setattr, world.systems, 'insert', TestSystem())
		self.assertRaises(AttributeError, 
			setattr, world.renderers, 'insert', TestRenderer())
	
	def test_add_systems(self):
		from grease import World
		world = World()
		self.assertFalse(world.systems)
		sys1 = world.systems.one = TestSystem()
		sys2 = world.systems.two = TestSystem()
		sys3 = world.systems.three = TestSystem()
		self.assertEqual(list(world.systems), [sys1, sys2, sys3])
		self.assertTrue(world.systems.one is sys1)
		self.assertTrue(world.systems.two is sys2)
		self.assertTrue(world.systems.three is sys3)
		self.assertTrue(sys1.world is world)
		self.assertTrue(sys2.world is world)
		self.assertTrue(sys3.world is world)
	
	def test_del_systems(self):
		from grease import World
		world = World()
		sys1 = world.systems.one = TestSystem()
		sys2 = world.systems.two = TestSystem()
		sys3 = world.systems.three = TestSystem()
		self.assertEqual(list(world.systems), [sys1, sys2, sys3])
		del world.systems.two
		self.assertEqual(list(world.systems), [sys1, sys3])
		del world.systems.one
		self.assertEqual(list(world.systems), [sys3])
		self.assertRaises(AttributeError, delattr, world, 'one')
	
	def test_insert_system(self):
		from grease import World
		world = World()
		sys1 = world.systems.sys1 = TestSystem()
		sys2 = world.systems.sys2 = TestSystem()
		sys3 = world.systems.sys3 = TestSystem()
		inserted = TestSystem()
		world.systems.insert('inserted', inserted, before='sys2')
		self.assertEqual(list(world.systems), [sys1, inserted, sys2, sys3])
		self.assertTrue(world.systems.inserted is inserted)
		another = TestSystem()
		world.systems.insert('another', another, before=world.systems.sys3)
		self.assertTrue(world.systems.another is another)
		self.assertEqual(list(world.systems), [sys1, inserted, sys2, another, sys3])
		onemore = TestSystem()
		world.systems.insert('onemore', onemore, index=1)
		self.assertEqual(list(world.systems), [sys1, onemore, inserted, sys2, another, sys3])
		self.assertTrue(world.systems.onemore is onemore)
	
	def test_insert_system_replaces_same_named_system(self):
		from grease import World
		world = World()
		sys1 = world.systems.sys1 = TestSystem()
		sys2 = world.systems.sys2 = TestSystem()
		replacement = TestSystem()
		world.systems.insert("sys1", replacement, before=sys2)
		self.assert_(world.systems.sys1 is replacement)
	
	def test_system_step_order(self):
		from grease import World
		world = World()
		sys1 = world.systems.one = TestSystem()
		sys3 = world.systems.three = TestSystem()
		sys2 = TestSystem()
		world.systems.insert('two', sys2, index=1)
		self.assertEqual(len(world.systems), 3)
		self.assertTrue(sys1.runtime == sys2.runtime == sys3.runtime == 0)
		self.assertTrue(sys1.order == sys2.order == sys3.order == TestSystem.order)
		world.step(0.13)
		self.assertTrue(sys1.runtime == sys2.runtime == sys3.runtime == 0.13)
		start = sys1.order
		self.assertEqual(sys2.order, start + 1)
		self.assertEqual(sys3.order, start + 2)
	
	def test_add_system_during_run(self):
		from grease import World
		world = World()
		sys1 = world.systems.sys1 = TestSystem()
		to_inject = TestSystem()
		injector = world.systems.injector = TestSystemInjector('injected', to_inject)
		self.assertEqual(len(world.systems), 2)
		self.assertTrue(sys1.runtime == to_inject.runtime == injector.runtime == 0)
		self.assertFalse(injector.injected)
		world.step(0.1)
		self.assertEqual(len(world.systems), 3)
		self.assertEqual(sys1.runtime, 0.1)
		self.assertEqual(injector.runtime, 0.1)
		self.assertEqual(to_inject.runtime, 0)
		self.assertTrue(injector.injected)
		world.step(0.1)
		self.assertEqual(len(world.systems), 3)
		self.assertEqual(sys1.runtime, 0.2)
		self.assertEqual(injector.runtime, 0.2)
		self.assertEqual(to_inject.runtime, 0.1)
	
	def test_activate(self):
		from grease import World
		world = World(master_clock=TestClock())
		sys1 = world.systems.one = TestSystem()
		sys2 = world.systems.two = TestSystem()
		manager = TestModeManager()
		self.assertFalse(world.active)
		world.activate(manager)
		self.assertTrue(world.manager is manager, world.manager)
		self.assertTrue(world.active)
		self.assertTrue((world.tick, None) in world.master_clock.scheduled)
		self.assertTrue(sys1 in manager.handlers)
		self.assertTrue(sys2 in manager.handlers)
		return world, manager
	
	def test_deactivate(self):
		world, manager = self.test_activate()
		sys1, sys2 = world.systems
		world.deactivate(manager)
		self.assertFalse(world.active)
		self.assertFalse((world.tick, None) in world.master_clock.scheduled)
		self.assertFalse(sys1 in manager.handlers)
		self.assertFalse(sys2 in manager.handlers)
	
	def test_tick_increments_world_time(self):
		from grease import World
		world = World(clock_factory=TestClock)
		self.assertEqual(world.time, 0)
		self.assertEqual(world.clock.ticks, 0)
		self.assertEqual(world.clock.time_func(), world.time)
		dt = 1.0/30.0
		world.tick(dt)
		self.assertAlmostEqual(world.time, dt)
		self.assertEqual(world.clock.time_func(), world.time)
		self.assertEqual(world.clock.ticks, 1)
		world.tick(dt)
		self.assertAlmostEqual(world.time, dt*2)
		self.assertEqual(world.clock.time_func(), world.time)
		self.assertEqual(world.clock.ticks, 2)
	
	def test_running(self):
		from grease import World
		world = World()
		self.assertTrue(world.running)
		self.assertEqual(world.time, 0)
		dt = 1.0/30.0
		world.tick(dt)
		self.assertAlmostEqual(world.time, dt)
		world.running = False
		world.tick(dt)
		world.tick(dt)
		self.assertAlmostEqual(world.time, dt)
		world.running = True
		world.tick(dt)
		self.assertAlmostEqual(world.time, dt*2)
	
	def test_step_max_dt(self):
		from grease import World
		world = World()
		sys1 = world.systems.sys = TestSystem()
		comp1 = world.components.foo = TestComponent()
		world.step(10000)
		self.assertEqual(comp1.runtime, 10.0 / world.step_rate)
		self.assertEqual(sys1.runtime, 10.0 / world.step_rate)
	
	def test_set_renderers(self):
		from grease import World
		world = World()
		self.assertEqual(tuple(world.renderers), ())
		renderer1 = world.renderers.one = TestRenderer()
		renderer2 = world.renderers.two = TestRenderer()
		renderer3 = world.renderers.three = object() # arbitrary objects can be renderers
		self.assertEqual(tuple(world.renderers), (renderer1, renderer2, renderer3))
		# objects with a set_world() method should have it called when set
		self.assertTrue(renderer1.world is world)
		self.assertTrue(renderer2.world is world)
	
	def test_on_draw(self):
		from grease import World
		world = World()
		renderer1 = world.renderers.one = TestRenderer()
		renderer2 = world.renderers.two = TestRenderer()
		gl = TestGL()
		self.assertFalse(gl.cleared)
		self.assertFalse(gl.matrix_reset)
		self.assertFalse(renderer1.drawn)
		self.assertFalse(renderer2.drawn)
		world.on_draw(gl=gl)
		self.assertTrue(gl.cleared)
		self.assertTrue(gl.matrix_reset)
		self.assertTrue(renderer1.drawn)
		self.assertTrue(renderer2.drawn)
		start = renderer1.order
		self.assertEqual(renderer2.order, start + 1)


class EntityIdGeneratorTestCase(unittest.TestCase):

	def test_id_length(self):
		from grease.world import _EntityIdGenerator
		gen =_EntityIdGenerator()
		i = gen.new_entity_id(object())
		self.assertEqual(len(i), 3)

	def test_id_members_ints(self):
		from grease.world import _EntityIdGenerator
		gen =_EntityIdGenerator()
		i = gen.new_entity_id(object())
		self.assert_(isinstance(i[0], int))
		self.assert_(isinstance(i[1], int))
		self.assert_(isinstance(i[2], int))

	def test_id_is_truthy(self):
		from grease.world import _EntityIdGenerator
		gen =_EntityIdGenerator()
		i = gen.new_entity_id(object())
		self.failUnless(i, i)

	def test_unique_index_same_entity_class(self):
		from grease.world import _EntityIdGenerator
		gen =_EntityIdGenerator()
		id1 = gen.new_entity_id(object())
		id2 = gen.new_entity_id(object())
		id3 = gen.new_entity_id(object())
		self.assertNotEqual(id1, id2)
		self.assertNotEqual(id1, id3)
		self.assertNotEqual(id2, id3)
		self.assertNotEqual(id1[2], id2[2])
		self.assertNotEqual(id1[2], id3[2])
		self.assertNotEqual(id2[2], id3[2])

	def test_same_block_same_entity_class(self):
		from grease.world import _EntityIdGenerator
		gen =_EntityIdGenerator()
		id1 = gen.new_entity_id(object())
		id2 = gen.new_entity_id(object())
		id3 = gen.new_entity_id(object())
		self.assertEqual(id1[1], id2[1])
		self.assertEqual(id1[1], id3[1])
		self.assertEqual(id2[1], id3[1])

	def test_same_generation_with_no_recycle(self):
		from grease.world import _EntityIdGenerator
		gen =_EntityIdGenerator()
		id1 = gen.new_entity_id(object())
		id2 = gen.new_entity_id(object())
		id3 = gen.new_entity_id(object())
		self.assertEqual(id1[0], id2[0])
		self.assertEqual(id1[0], id3[0])
		self.assertEqual(id2[0], id3[0])

	def test_different_block_different_entity_class(self):
		from grease.world import _EntityIdGenerator
		gen =_EntityIdGenerator()
		class E1(object): pass
		class E2(object): pass
		id1 = gen.new_entity_id(E1())
		id2 = gen.new_entity_id(E2())
		id3 = gen.new_entity_id(E1())
		self.assertNotEqual(id1[1], id2[1])
		self.assertNotEqual(id2[1], id3[1])
		self.assertEqual(id1[1], id3[1])
	
	def test_different_generation_after_recycle(self):
		from grease.world import _EntityIdGenerator
		gen =_EntityIdGenerator()
		class E1(object): pass
		class E2(object): pass
		e11 = E1()
		e21 = E2()
		e12 = E1()
		e11.entity_id = gen.new_entity_id(E1())
		e21.entity_id = gen.new_entity_id(E2())
		gen.recycle(e11)
		e12.entity_id = gen.new_entity_id(E1())
		self.assertNotEqual(e12.entity_id, e11.entity_id)
		self.assertNotEqual(e12.entity_id, e21.entity_id)
		self.assertNotEqual(e12.entity_id[0], e11.entity_id[0])
		self.assertEqual(e12.entity_id[1], e11.entity_id[1])
		self.assertEqual(e12.entity_id[2], e11.entity_id[2])


if __name__ == '__main__':
	unittest.main()

