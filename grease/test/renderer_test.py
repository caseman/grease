import itertools
import unittest
import math

sqrt2 = math.sqrt(2)

class TestWorld(object):

	def __init__(self):
		self.components = self

	def join(self, *components):
		assert components == ('shape', 'position', 'renderable')
		return itertools.izip(self.shapes, self.positions, self.renderable)

class Data(object):

	def __init__(self, **kw):
		self.__dict__.update(kw)


class TestGL(object):
	
	GL_CLIENT_VERTEX_ARRAY_BIT = 1
	GL_VERTEX_ARRAY = 2
	GL_COLOR_ARRAY = 3
	GL_FLOAT = 4
	GL_LINES = 5
	GL_UNSIGNED_BYTE = 6
	GL_ALIASED_LINE_WIDTH_RANGE = 7
	GL_POINT_SMOOTH = 8
	GL_POINTS = 9
	GL_LINE_SMOOTH = 10
	GL_LINE_SMOOTH_HINT = 11
	GL_NICEST = 12
	GL_BLEND = 13
	GL_SRC_ALPHA = 14
	GL_ONE_MINUS_SRC_ALPHA = 15

	def __init__(self):
		self.enabled = []

	def glPushClientAttrib(self, what):
		self.state_reset = False
		self.client_attrib_pushed = what
	
	def glPopClientAttrib(self):
		self.state_reset = True
	
	def glEnableClientState(self, what):
		self.state_reset = False
		self.enabled.append(what)
	
	glEnable = glEnableClientState

	def glHint(self, who, what):
		self.hint = who, what
	
	def glBlendFunc(self, what, func):
		self.blend_func = what, func

	def glLineWidth(self, width):
		self.line_width = width
	
	def glPointSize(self, size):
		self.point_size = size
	
	def glGetFloatv(self, what, out):
		pass
	
	def glVertexPointer(self, size, type, stride, pointer):
		self.vert_size = size
		self.vert_type = type
		self.vert_stride = stride
		self.vert_pointer = pointer

	def glColorPointer(self, size, type, stride, pointer):
		self.color_size = size
		self.color_type = type
		self.color_stride = stride
		self.color_pointer = pointer
	
	def glDrawArrays(self, mode, start, count):
		self.draw_arr_mode = mode
		self.draw_arr_start = start
		self.draw_arr_count = count
	
	def glDrawElements(self, mode, count, type, indices):
		self.draw_mode = mode
		self.draw_count = count
		self.draw_type = type
		self.draw_indices = indices


class VectorTestCase(unittest.TestCase):

	def assertArrayEqual(self, a1, a2):
		for (x1, y1), (x2, y2) in zip(a1, a2):
			self.assertAlmostEqual(x1, x2, 4, '%r != %r' % (a1, a2))
			self.assertAlmostEqual(y1, y2, 4, '%r != %r' % (a1, a2))
	
	def make_world(self):
		from grease.geometry import Vec2d, Vec2dArray
		from grease.color import RGBA
		world = TestWorld()
		world.shapes = [
			Data(closed=True, verts=Vec2dArray([(0,0), (0, 1), (0.5, 0.5)])),
			Data(closed=True, verts=Vec2dArray([(-1, -1), (1, -1), (1, 1), (-1, 1)])),
			Data(closed=False, verts=Vec2dArray([(1, -1), (-1, -1), (1, 1), (-1, 1)])),
		]
		world.positions = [
			Data(position=Vec2d(10, 10), angle=0),
			Data(position=Vec2d(4, 3), angle=0),
			Data(position=Vec2d(0, 0), angle=0),
		]
		world.renderable = [
			Data(color=RGBA(1,1,1,1)),
			Data(color=RGBA(1,1,1,1)),
			Data(color=RGBA(1,1,1,1)),
		]
		return world

	def test_defaults(self):
		from grease.renderer import Vector
		vr = Vector()
		self.assertEqual(vr.scale, 1.0)
		self.assertEqual(vr.line_width, None)
		self.assertEqual(vr.corner_fill, True)
		self.assertEqual(vr.anti_alias, True)
		self.assertEqual(vr.position_component, 'position')
		self.assertEqual(vr.shape_component, 'shape')
		self.assertEqual(vr.renderable_component, 'renderable')

	def test_overrides(self):
		from grease.renderer import Vector
		vr = Vector(scale=2.5, line_width=3.7, corner_fill=False, anti_alias=False,
			position_component='pos', shape_component='fit', renderable_component='drawme')
		self.assertEqual(vr.scale, 2.5)
		self.assertEqual(vr.line_width, 3.7)
		self.assertEqual(vr.corner_fill, False)
		self.assertEqual(vr.anti_alias, False)
		self.assertEqual(vr.position_component, 'pos')
		self.assertEqual(vr.shape_component, 'fit')
		self.assertEqual(vr.renderable_component, 'drawme')
	
	def test_set_world(self):
		from grease.renderer import Vector
		world = object()
		vr = Vector()
		vr.set_world(world)
		self.assertTrue(vr.world is world)
	
	def get_verts(self, array):
		return [(i.vert.x, i.vert.y) for i in array]
	
	def get_rgba(self, array):
		return [(i.color.r, i.color.g, i.color.b, i.color.a) for i in array]

	def test_generate_verts_no_scale_or_angle(self):
		from grease.renderer import Vector
		world = self.make_world()
		renderer = Vector()
		renderer.set_world(world)
		v_array, i_size, i_array, i_count = renderer._generate_verts()
		self.assertEqual(i_count, 20)
		self.assertEqual(self.get_verts(v_array[:3]), [(10, 10), (10, 11), (10.5, 10.5)]) 
		self.assertEqual(list(i_array[:6]), [0, 1, 1, 2, 2, 0]) 
		self.assertEqual(self.get_verts(v_array[3:7]), [(3, 2), (5, 2), (5, 4), (3, 4)]) 
		self.assertEqual(list(i_array[6:14]), [3, 4, 4, 5, 5, 6, 6, 3]) 
		self.assertEqual(self.get_verts(v_array[7:11]), [(1, -1), (-1, -1), (1, 1), (-1, 1)]) 
		self.assertEqual(list(i_array[14:20]), [7, 8, 8, 9, 9, 10]) 
		self.assertEqual(self.get_rgba(v_array[:11]), [(255,255,255,255)] * 11)

	def test_generate_verts_with_color(self):
		from grease.renderer import Vector
		from grease.color import RGBA
		world = self.make_world()
		world.renderable = [
			Data(color=RGBA(1,0,0,1)),
			Data(color=RGBA(1,0,1,1)),
			Data(color=RGBA(0,0,1,1)),
		]
		renderer = Vector()
		renderer.set_world(world)
		v_array, i_size, i_array, i_count = renderer._generate_verts()
		self.assertEqual(i_count, 20)
		self.assertEqual(self.get_verts(v_array[:3]), [(10, 10), (10, 11), (10.5, 10.5)]) 
		self.assertEqual(self.get_rgba(v_array[:3]), [(255,0,0,255)] * 3)
		self.assertEqual(list(i_array[:6]), [0, 1, 1, 2, 2, 0]) 
		self.assertEqual(self.get_verts(v_array[3:7]), [(3, 2), (5, 2), (5, 4), (3, 4)]) 
		self.assertEqual(self.get_rgba(v_array[3:7]), [(255,0,255,255)] * 4)
		self.assertEqual(list(i_array[6:14]), [3, 4, 4, 5, 5, 6, 6, 3]) 
		self.assertEqual(self.get_verts(v_array[7:11]), [(1, -1), (-1, -1), (1, 1), (-1, 1)]) 
		self.assertEqual(self.get_rgba(v_array[7:11]), [(0,0,255,255)] * 4)
		self.assertEqual(list(i_array[14:20]), [7, 8, 8, 9, 9, 10]) 

	def test_generate_verts_with_scale(self):
		from grease.renderer import Vector
		world = self.make_world()
		renderer = Vector(scale=10.0)
		renderer.set_world(world)
		self.assertTrue(renderer.world is world)
		v_array, i_size, i_array, i_count = renderer._generate_verts()
		self.assertEqual(i_count, 20)
		self.assertEqual(self.get_verts(v_array[:3]), [(10, 10), (10, 20), (15, 15)]) 
		self.assertEqual(list(i_array[:6]), [0, 1, 1, 2, 2, 0]) 
		self.assertEqual(self.get_verts(v_array[3:7]), [(-6, -7), (14, -7), (14, 13), (-6, 13)]) 
		self.assertEqual(list(i_array[6:14]), [3, 4, 4, 5, 5, 6, 6, 3]) 
		self.assertEqual(self.get_verts(v_array[7:11]), [(10, -10), (-10, -10), (10, 10), (-10, 10)]) 
		self.assertEqual(list(i_array[14:20]), [7, 8, 8, 9, 9, 10]) 
		self.assertEqual(self.get_rgba(v_array[:11]), [(255,255,255,255)] * 11)

	def test_generate_verts_with_angle(self):
		from grease.renderer import Vector
		from grease.geometry import Vec2d, Vec2dArray
		world = self.make_world()
		renderer = Vector()
		renderer.set_world(world)
		self.assertTrue(renderer.world is world)
		world.shapes = [
			Data(closed=True, verts=Vec2dArray([(0,0), (0, 1), (1, 0)])),
			Data(closed=True, verts=Vec2dArray([(-2, -1), (2, -1), (2, 1), (-2, 1)])),
			Data(closed=False, verts=Vec2dArray([(1, -1), (-1, -1), (1, 1), (-1, 1)])),
		]
		world.positions = [
			Data(position=Vec2d(10, 10), angle=45),
			Data(position=Vec2d(4, 3), angle=90),
			Data(position=Vec2d(0, 0), angle=-45),
		]
		v_array, i_size, i_array, i_count = renderer._generate_verts()
		self.assertEqual(i_count, 20)
		sin45 = math.sin(math.radians(45))
		cos45 = math.cos(math.radians(45))
		self.assertArrayEqual(self.get_verts(v_array[:3]), 
			[(10, 10), (sin45+10, cos45+10), (cos45+10, -sin45+10)]) 
		self.assertEqual(list(i_array[:6]), [0, 1, 1, 2, 2, 0]) 
		self.assertArrayEqual(self.get_verts(v_array[3:7]), [(3, 5), (3, 1), (5, 1), (5, 5)]) 
		self.assertEqual(list(i_array[6:14]), [3, 4, 4, 5, 5, 6, 6, 3]) 
		self.assertArrayEqual(self.get_verts(v_array[7:11]), 
			[(sqrt2, 0), (0, -sqrt2), (0, sqrt2), (-sqrt2, 0)]) 
		self.assertEqual(list(i_array[14:20]), [7, 8, 8, 9, 9, 10]) 
		self.assertEqual(self.get_rgba(v_array[:11]), [(255,255,255,255)] * 11)
	
	def test_draw_empty(self):
		from grease.renderer import Vector
		world = TestWorld()
		world.shapes = []
		world.positions = []
		world.renderable = []
		renderer = Vector()
		renderer.set_world(world)
		gl = TestGL()
		# Renderer should run without complaint with no verts
		renderer.draw(gl=gl)

	def test_draw_plain(self):
		from grease.renderer import Vector
		from grease.geometry import Vec2d, Vec2dArray
		import pyglet
		world = self.make_world()
		renderer = Vector()
		renderer.set_world(world)
		gl = TestGL()
		renderer.draw(gl=gl)
		self.assertTrue(gl.GL_VERTEX_ARRAY in gl.enabled)
		self.assertTrue(gl.GL_COLOR_ARRAY in gl.enabled)
		self.assertEqual(gl.client_attrib_pushed, gl.GL_CLIENT_VERTEX_ARRAY_BIT)
		verts = gl.vert_pointer.contents
		indices = gl.draw_indices.contents
		self.assertTrue(len(verts) > max(indices))
		self.assertTrue(len(indices) >= gl.draw_count)
		self.assertTrue(gl.draw_count < 65536)
		self.assertEqual(gl.draw_type, pyglet.gl.GL_UNSIGNED_SHORT)
		self.assertTrue(gl.state_reset)
		self.assertFalse(hasattr(gl, 'line_width'))

	def test_draw_line_width(self):
		from grease.renderer import Vector
		from grease.geometry import Vec2d, Vec2dArray
		import pyglet
		world = self.make_world()
		renderer = Vector(line_width=3.0)
		renderer.set_world(world)
		gl = TestGL()
		renderer.draw(gl=gl)
		self.assertTrue(gl.GL_VERTEX_ARRAY in gl.enabled)
		self.assertTrue(gl.GL_COLOR_ARRAY in gl.enabled)
		self.assertEqual(gl.client_attrib_pushed, gl.GL_CLIENT_VERTEX_ARRAY_BIT)
		verts = gl.vert_pointer.contents
		indices = gl.draw_indices.contents
		self.assertTrue(len(verts) > max(indices))
		self.assertTrue(len(indices) >= gl.draw_count)
		self.assertEqual(gl.line_width, 3.0)
		self.assertEqual(gl.draw_arr_mode, gl.GL_POINTS)
		self.assertEqual(gl.draw_arr_count, gl.draw_count)
		self.assertTrue(gl.draw_count < 65536)
		self.assertEqual(gl.draw_type, pyglet.gl.GL_UNSIGNED_SHORT)
		self.assertTrue(gl.state_reset)
	
	def test_anti_alias_on(self):
		from grease.renderer import Vector
		world = self.make_world()
		renderer = Vector()
		renderer.set_world(world)
		gl = TestGL()
		renderer.draw(gl=gl)
		self.assertTrue(gl.GL_LINE_SMOOTH in gl.enabled)
		self.assertTrue(gl.GL_BLEND in gl.enabled)
	
	def test_anti_alias_off(self):
		from grease.renderer import Vector
		world = self.make_world()
		renderer = Vector(anti_alias=False)
		renderer.set_world(world)
		gl = TestGL()
		renderer.draw(gl=gl)
		self.assertTrue(gl.GL_LINE_SMOOTH not in gl.enabled)
		self.assertTrue(gl.GL_BLEND not in gl.enabled)


if __name__ == '__main__':
	unittest.main()
