#############################################################################
#
# Copyright (c) 2010 by Casey Duncan and contributors
# All Rights Reserved.
#
# This software is subject to the provisions of the MIT License
# A copy of the license should accompany this distribution.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
#############################################################################

__version__ = '$Id$'

__all__ = ('Vector',)

from grease.geometry import Vec2d
import ctypes
from math import sin, cos, radians
import pyglet


class Vector(object):
	"""Renders shapes in a classic vector graphics style
	
	:param scale: Scaling factor applied to shape vertices when rendered.
	
	:param line_width: The line width provided to ``glLineWidth`` before rendering.
		If not specified or None, ``glLineWidth`` is not called, and the line
		width used is determined by the OpenGL state at the time of rendering.

	:param anti_alias: If ``True``, OpenGL blending and line smoothing is enabled.
		This allows for fractional line widths as well. If ``False``, the blending
		and line smoothing modes are unchanged.

	:param corner_fill: If true (the default), the shape corners will be filled
		with round points when the ``line_width`` exceeds 2.0. This improves
		the visual quality of the rendering at larger line widths at some
		cost to performance. Has no effect if ``line_width`` is not specified.

	:param position_component: Name of :class:`grease.component.Position` 
		component to use. Shapes rendered are offset by the entity positions.

	:param renderable_component: Name of :class:`grease.component.Renderable` 
		component to use. This component specifies the entities to be 
		rendered and their base color.

	:param shape_component: Name of :class:`grease.component.Shape` 
		component to use. Source of the shape vertices for each entity.

	The entities rendered are taken from the intersection of he position,
	renderable and shape components each time :meth:`draw` is called.
	"""

	CORNER_FILL_SCALE = 0.6
	CORNER_FILL_THRESHOLD = 2.0

	def __init__(self, scale=1.0, line_width=None, anti_alias=True, corner_fill=True,
		position_component='position', 
		renderable_component='renderable', 
		shape_component='shape'):
		self.scale = float(scale)
		self.corner_fill = corner_fill
		self.line_width = line_width
		self.anti_alias = anti_alias
		self._max_line_width = None
		self.position_component = position_component
		self.renderable_component = renderable_component
		self.shape_component = shape_component
	
	def set_world(self, world):
		self.world = world

	def _generate_verts(self):
		"""Generate vertex and index arrays for rendering"""
		vert_count = sum(len(shape.verts) + 1
			for shape, ignored, ignored in self.world.components.join(
				self.shape_component, self.position_component, self.renderable_component))
		v_array = (CVertColor * vert_count)()
		if vert_count > 65536:
			i_array = (ctypes.c_uint * 2 * vert_count)()
			i_size = pyglet.gl.GL_UNSIGNED_INT
		else:
			i_array = (ctypes.c_ushort * (2 * vert_count))()
			i_size = pyglet.gl.GL_UNSIGNED_SHORT
		v_index = 0
		i_index = 0
		scale = self.scale
		rot_vec = Vec2d(0, 0)
		for shape, position, renderable in self.world.components.join(
			self.shape_component, self.position_component, self.renderable_component):
			shape_start = v_index
			angle = radians(-position.angle)
			rot_vec.x = cos(angle)
			rot_vec.y = sin(angle)
			r = int(renderable.color.r * 255)
			g = int(renderable.color.g * 255)
			b = int(renderable.color.b * 255)
			a = int(renderable.color.a * 255)
			for vert in shape.verts:
				vert = vert.cpvrotate(rot_vec) * scale + position.position
				v_array[v_index].vert.x = vert.x
				v_array[v_index].vert.y = vert.y
				v_array[v_index].color.r = r
				v_array[v_index].color.g = g
				v_array[v_index].color.b = b
				v_array[v_index].color.a = a
				if v_index > shape_start:
					i_array[i_index] = v_index - 1
					i_index += 1
					i_array[i_index] = v_index
					i_index += 1
				v_index += 1
			if shape.closed and v_index - shape_start > 2:
				i_array[i_index] = v_index - 1
				i_index += 1
				i_array[i_index] = shape_start
				i_index += 1
		return v_array, i_size, i_array, i_index

	def draw(self, gl=pyglet.gl):
		vertices, index_size, indices, index_count = self._generate_verts()
		if index_count:
			if self.anti_alias:
				gl.glEnable(gl.GL_LINE_SMOOTH)
				gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
				gl.glEnable(gl.GL_BLEND)
				gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
			gl.glPushClientAttrib(gl.GL_CLIENT_VERTEX_ARRAY_BIT)
			gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
			gl.glEnableClientState(gl.GL_COLOR_ARRAY)
			gl.glVertexPointer(
				2, gl.GL_FLOAT, ctypes.sizeof(CVertColor), ctypes.pointer(vertices))
			gl.glColorPointer(
				4, gl.GL_UNSIGNED_BYTE, ctypes.sizeof(CVertColor), 
				ctypes.pointer(vertices[0].color))
			if self.line_width is not None:
				gl.glLineWidth(self.line_width)
				if self._max_line_width is None:
					range_out = (ctypes.c_float * 2)()
					gl.glGetFloatv(gl.GL_ALIASED_LINE_WIDTH_RANGE, range_out)
					self._max_line_width = float(range_out[1]) * self.CORNER_FILL_SCALE
				if self.corner_fill and self.line_width > self.CORNER_FILL_THRESHOLD:
					gl.glEnable(gl.GL_POINT_SMOOTH)
					gl.glPointSize(
						min(self.line_width * self.CORNER_FILL_SCALE, self._max_line_width))
					gl.glDrawArrays(gl.GL_POINTS, 0, index_count)
			gl.glDrawElements(gl.GL_LINES, index_count, index_size, ctypes.pointer(indices))
			gl.glPopClientAttrib()


class CVert(ctypes.Structure):
	_fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

class CColor(ctypes.Structure):
	_fields_ = [
		("r", ctypes.c_ubyte), 
		("g", ctypes.c_ubyte), 
		("b", ctypes.c_ubyte), 
		("a", ctypes.c_ubyte),
	]

class CVertColor(ctypes.Structure):
	_fields_ = [("vert", CVert), ("color", CColor)]

