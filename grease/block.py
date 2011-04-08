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
"""Blocks are slighly specialized numpy arrays that are used for storing
dynamically sized arrays of data.
"""

import numpy


class Block(numpy.ndarray):
	
	def grow(self, size):
		"""Resize the block with extra space for additional growth.  The
		resulting block array may be larger than the requested size.
		"""
		if len(self) < size:
			if size < 64:
				size = max(size * 2, 4)
			else:
				size = size * 5 // 4
			self.resize(size, refcheck=False)

