import pyglet

class Camera(object):
	"""Sets the point of view for further renderers by altering the
	model/view matrix when it is drawn. It does not actually perform
	any drawing itself.

	:param position: The position vector for the camera. Sets the center of the view.
	:type position: Vec2d
	:param angle: Camera rotation in degrees about the z-axis.
	:type angle: float
	:param zoom: Scaling vector for the coordinate axis.
	:type zoom: Vec2d
	:param relative: Flag to indicate if the camera settings are relative 
		to the previous view state. If ``False`` the view state is reset before 
		setting the camera view by loading the identity model/view matrix.
	
	At runtime the camera may be manipulated via attributes with the 
	same names and functions as the parameters above.
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

