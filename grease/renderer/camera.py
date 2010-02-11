import pyglet

class Camera(object):
	"""Sets the point of view for further renderers"""

	position = (0, 0)
	"""The position vector for the camera. Sets the center of the view"""

	angle = 0
	"""Camera rotation in degrees about the z-axis"""

	zoom = (1.0, 1.0)
	"""Scaling vector for the coordinate axis"""

	relative = False
	"""Flag to indicate if the camera settings are relative to the previous
	view state. If False the view state is reset before setting the camera
	view
	"""

	def __init__(self, position=None, angle=None, zoom=None, relative=False):
		self.position = position
		self.angle = angle
		self.zoom = zoom
		self.relative = relative
	
	def draw(self, gl=pyglet.gl):
		if not self.relative:
			gl.glLoadIdentity()
		if self.position is not None:
			px, py = self.position
			gl.glTranslatef(px, py, 0)
		if self.angle is not None:
			gl.glRotatef(self.angle, 0, 0, 1)
		if self.zoom is not None:
			sx, sy = self.zoom
			gl.glScalef(sx, sy ,0)

