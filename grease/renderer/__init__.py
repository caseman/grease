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
"""Renderers define world presentation. This module contains the
built-in renderer classes.

See also:

- :class:`~grease.Renderer` abstract base class.
- :ref:`Example renderer class in the tutorial <tut-renderer-example>`
"""

__all__ = ('Vector', 'Camera')

from grease.renderer.vector import Vector
from grease.renderer.camera import Camera
