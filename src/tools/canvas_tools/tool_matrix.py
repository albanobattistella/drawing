# tool_matrix.py
#
# Copyright 2018-2020 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cairo, math
from gi.repository import Gtk, Gdk, GdkPixbuf

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

class ToolMatrix(AbstractCanvasTool):
	__gtype_name__ = 'ToolMatrix'

	def __init__(self, window):
		super().__init__('matrix', _("Deformation"), 'tool-deformation-symbolic', window)
		self.row.get_style_context().add_class('destructive-action')

		self.apply_to_selection = False
		self.temp_w = 1
		self.temp_h = 1
		self.add_tool_action_simple('matrix-reset', self.on_reset_values)

	def get_edition_status(self):
		return "You're not supposed to use this tool (development only)."

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.on_reset_values()

	def try_build_panel(self):
		self.panel_id = 'matrix'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		self.bar = SkewToolPanel(self.window, self)
		return self.bar

	############################################################################

	def on_reset_values(self, *args):
		if self.apply_to_selection:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.temp_w = source_pixbuf.get_width()
		self.temp_h = source_pixbuf.get_height()
		self.bar.set_all_values(100, 0, 0, 100, 0, 0, 0)

	def new_angle(self, angle):
		rad = math.pi * angle / 180
		print('rad', rad)
		xx = math.cos(rad)
		xy = math.sin(rad)
		yx = -1 * math.sin(rad)
		yy = math.cos(rad)

		if rad % (2 * math.pi) == 0:
			x0 = 0
			y0 = 0
		elif rad < 0 and rad > math.pi/-2:
			x0 = self.temp_h * yx
			y0 = self.temp_w * xy
		elif rad > 0 and rad < math.pi/2:
			x0 = self.temp_h * yx
			y0 = self.temp_w * xy
		else:
			self.show_error('angle not supported')
			x0 = self.temp_h * yx
			y0 = self.temp_w * xy

		x0 = max(0, x0)
		y0 = max(0, y0)

		# x_old = 100
		# y_old = 100
		# x_new = xx * x_old + xy * y_old + x0
		# y_new = yx * x_old + yy * y_old + y0
		# print(x_new, y_new)

		self.bar.set_all_values(xx * 100, xy * 100, yx * 100, yy * 100, x0, y0, angle)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'local_dx': 0,
			'local_dy': 0,
			'xx': self.bar.xx_spinbtn.get_value_as_int()/100,
			'yx': self.bar.yx_spinbtn.get_value_as_int()/100,
			'xy': self.bar.xy_spinbtn.get_value_as_int()/100,
			'yy': self.bar.yy_spinbtn.get_value_as_int()/100,
			'x0': self.bar.x0_spinbtn.get_value_as_int(),
			'y0': self.bar.y0_spinbtn.get_value_as_int()
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		source_surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		coefs = [ operation['xx'], operation['yx'], operation['xy'], \
		                     operation['yy'], operation['x0'], operation['y0'] ]
		new_surface = self.get_deformed_surface(source_surface, coefs)
		new_pixbuf = Gdk.pixbuf_get_from_surface(new_surface, 0, 0, \
		                      new_surface.get_width(), new_surface.get_height())
		self.get_image().set_temp_pixbuf(new_pixbuf)
		self.common_end_operation(operation)

	############################################################################
################################################################################

class SkewToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'SkewToolPanel'

	def __init__(self, window, skew_tool):
		super().__init__()
		self.window = window
		# knowing the tool is needed because the panel doesn't compact the same
		# way if it's applied to the selection
		self.skew_tool = skew_tool
		self.dont_update = False

		builder = self.build_ui('tools/ui/tool_matrix.ui')
		self.values_btn = builder.get_object('values_btn')
		self.xy_label = builder.get_object('xy_label')
		self.yx_label = builder.get_object('yx_label')
		self.separator = builder.get_object('separator')

		self.angle_spinbtn = builder.get_object('angle_spinbtn')
		self.angle_spinbtn.connect('value-changed', self.on_angle_changed)

		self.xx_spinbtn = builder.get_object('xx_spinbtn')
		self.yx_spinbtn = builder.get_object('yx_spinbtn')
		self.xy_spinbtn = builder.get_object('xy_spinbtn')
		self.yy_spinbtn = builder.get_object('yy_spinbtn')
		self.x0_spinbtn = builder.get_object('x0_spinbtn')
		self.y0_spinbtn = builder.get_object('y0_spinbtn')
		self.xx_spinbtn.connect('value-changed', self.on_coord_changed)
		self.yx_spinbtn.connect('value-changed', self.on_coord_changed)
		self.xy_spinbtn.connect('value-changed', self.on_coord_changed)
		self.yy_spinbtn.connect('value-changed', self.on_coord_changed)
		self.x0_spinbtn.connect('value-changed', self.on_coord_changed)
		self.y0_spinbtn.connect('value-changed', self.on_coord_changed)

	def set_all_values(self, xx, xy, yx, yy, x0, y0, angle):
		self.dont_update = True
		self.xx_spinbtn.set_value(100)
		self.xy_spinbtn.set_value(0)
		self.yx_spinbtn.set_value(0)
		self.yy_spinbtn.set_value(100)
		self.x0_spinbtn.set_value(0)
		self.y0_spinbtn.set_value(0)
		self.angle_spinbtn.set_value(0)
		self.dont_update = False
		self.on_coord_changed()

	def on_angle_changed(self, *args):
		angle = self.angle_spinbtn.get_value_as_int()
		self.skew_tool.new_angle(angle)
		self.on_coord_changed()

	def on_coord_changed(self, *args):
		if self.dont_update:
			return
		self.skew_tool.build_and_do_op() # XXX yikes

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.centered_box.get_preferred_width()[0] + \
		                    self.cancel_btn.get_preferred_width()[0] + \
		                     self.apply_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def update_for_new_tool(self, tool):
		self.set_compact(self._is_narrow)

	def toggle_options_menu(self):
		self.values_btn.set_active(not self.values_btn.get_active())

	def hide_options_menu(self):
		self.values_btn.set_active(False)

	def set_compact(self, state):
		super().set_compact(state)
		if state:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.xy_label.set_visible(not state)
		self.yx_label.set_visible(not state)
		self.separator.set_visible(not state)

	############################################################################
################################################################################


