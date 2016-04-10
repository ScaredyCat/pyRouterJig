###########################################################################
#
# Copyright 2015-2016 Robert B. Lowrie (http://github.com/lowrie)
#
# This file is part of pyRouterJig.
#
# pyRouterJig is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pyRouterJig is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# pyRouterJig; see the file LICENSE. If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################

'''
This module contains the Qt interface to setting config file parameters.
'''
from __future__ import print_function

import os, sys
from PyQt4 import QtCore, QtGui

import config_file
import qt_utils
import router

def form_line(label, widget=None, tooltip=None):
    '''
    Formats a line as

        label --------------- widget

    and returns the QLayout
    '''
    grid = QtGui.QGridLayout()
    line = qt_utils.create_hline()
    line.setMinimumWidth(20)
    if tooltip is not None:
        label.setToolTip(tooltip)
        if widget is not None:
            widget.setToolTip(tooltip)
        line.setToolTip(tooltip)
    grid.addWidget(label, 0, 0)
    grid.addWidget(line, 0, 1)
    if widget is not None:
        grid.addWidget(widget, 0, 2)
    grid.setColumnStretch(1, 5)
    return grid

class Misc_Value(object):
    '''
    Helper class to wrap dimensional values for use with qt_utils.set_router_value()
    '''
    def __init__(self, value, units, name):
        self.value = value
        self.units = units
        self.name = name
    def set_value_from_string(self, s):
        msg = 'Unable to set {} to: {}<p>'\
              'Set to a positive number.'.format(self.name, s)
        try:
            value = self.units.string_to_increments(s)
        except:
            raise router.Router_Exception(msg)
        if value <= 0:
            raise router.Router_Exception(msg)
        self.value = value

class Config_Window(QtGui.QDialog):
    '''
    Qt interface to config file parameters
    '''
    def __init__(self, config, units, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.config = config
        self.new_config = self.config.__dict__.copy()
        self.line_edit_width = 80
        self.units = units

        # Form these objects so that we can do error checking on their changes
        bit_width = self.units.abstract_to_increments(self.config.bit_width)
        bit_depth = self.units.abstract_to_increments(self.config.bit_depth)
        bit_angle = self.units.abstract_to_float(self.config.bit_angle)
        self.bit = router.Router_Bit(self.units, bit_width, bit_depth, bit_angle)
        board_width = self.units.abstract_to_increments(self.config.board_width)
        self.board = router.Board(self.bit, width=board_width)

        # Form the tabs and their contents
        title_label = QtGui.QLabel('<font color=blue size=4><b>pyRouterJig Preferences</b></font>')
        title_label.setAlignment(QtCore.Qt.AlignHCenter)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(title_label)
        
        tabs = QtGui.QTabWidget()

        tabs.addTab(self.create_output(), 'Output')
        tabs.addTab(self.create_boards(), 'Boards')
        tabs.addTab(self.create_bit(), 'Bit')
        tabs.addTab(self.create_units(), 'Units')
        tabs.addTab(self.create_misc(), 'Misc')

        vbox.addWidget(tabs)
        vbox.addLayout(self.create_buttons())
        self.setLayout(vbox)

        self.change_state = 0
        self.initialize()

    def create_units(self):
        '''Creates the layout for units preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        mesg = QtGui.QLabel('<font color=red><b>WARNING:</b></font>'
                            ' Changing any Units settings will require <i>pyRouterJig</i>'
                            ' to restart and your present joint will be lost.')
        mesg.setWordWrap(True)
        vbox.addWidget(mesg)

        self.cb_units_label = QtGui.QLabel('Unit System:')
        self.cb_units = QtGui.QComboBox(self)
        self.cb_units.addItem('Metric')
        self.cb_units.addItem('English')
        self.cb_units.activated.connect(self._on_units)
        grid = form_line(self.cb_units_label, self.cb_units)
        vbox.addLayout(grid)

        self.le_num_incr_label = QtGui.QLabel(self.units_label(self.config.metric))
        self.le_num_incr = QtGui.QLineEdit(w)
        self.le_num_incr.setFixedWidth(self.line_edit_width)
        self.le_num_incr.editingFinished.connect(self._on_num_incr)
        tt = 'The number of increments per unit length.'
        grid = form_line(self.le_num_incr_label, self.le_num_incr, tt)
        vbox.addLayout(grid)
        vbox.addStretch(1)

        w.setLayout(vbox)
        return w

    def set_wood_combobox(self):
        '''
        Sets the entries for the wood combox box, and resets the default wood.
        '''
        (woods, patterns) = qt_utils.create_wood_dict(self.new_config['wood_images'])
        woodnames = woods.keys()
        woodnames.extend(patterns.keys())
        self.cb_wood.clear()
        self.cb_wood.addItems(woodnames)
        i = self.cb_wood.findText(self.new_config['default_wood'])
        if i < 0:
            self.cb_wood.setCurrentIndex(0)
            self.new_config['default_wood'] = str(self.cb_wood.currentText())
        else:
            self.cb_wood.setCurrentIndex(i)

    def create_boards(self):
        '''Creates the layout for boards preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        us = self.units.units_string(withParens=True)
        self.le_board_width_label = QtGui.QLabel('Initial Board Width{}:'.format(us))
        self.le_board_width = QtGui.QLineEdit(w)
        self.le_board_width.setFixedWidth(self.line_edit_width)
        self.le_board_width.editingFinished.connect(self._on_board_width)
        tt = 'The initial board width when pyRouterJig starts.'
        grid = form_line(self.le_board_width_label, self.le_board_width, tt)
        vbox.addLayout(grid)

        self.le_db_thick_label = QtGui.QLabel('Initial Double Board Thickness{}:'.format(us))
        self.le_db_thick = QtGui.QLineEdit(w)
        self.le_db_thick.setFixedWidth(self.line_edit_width)
        self.le_db_thick.editingFinished.connect(self._on_db_thick)
        tt = 'The initial double-board thickness when pyRouterJig starts.'
        grid = form_line(self.le_db_thick_label, self.le_db_thick, tt)
        vbox.addLayout(grid)

        (woods, patterns) = qt_utils.create_wood_dict(self.config.wood_images)
        woodnames = woods.keys()
        woodnames.extend(patterns.keys())
        self.cb_wood_label = QtGui.QLabel('Default Wood Fill:')
        self.cb_wood = QtGui.QComboBox(self)
        self.set_wood_combobox()
        self.cb_wood.activated.connect(self._on_wood)
        tt = 'The default wood fill for each board.'
        grid = form_line(self.cb_wood_label, self.cb_wood, tt)
        vbox.addLayout(grid)

        self.le_wood_images_label = QtGui.QLabel('Wood Images Folder:')
        self.le_wood_images = QtGui.QLineEdit(w)
        self.le_wood_images.editingFinished.connect(self._on_wood_images)
        tt = 'Location of wood images.'
        self.le_wood_images.setToolTip(tt)
        grid = QtGui.QGridLayout()
        grid.addWidget(qt_utils.create_vline(), 0, 0, 4, 1)
        grid.addWidget(qt_utils.create_vline(), 0, 3, 4, 1)
        grid.addWidget(qt_utils.create_hline(), 0, 0, 1, 4)
        grid.addWidget(self.le_wood_images_label, 1, 1)
        grid.addWidget(self.le_wood_images, 2, 1)
        grid.addWidget(qt_utils.create_hline(), 3, 0, 1, 4)
        vbox.addLayout(grid)
        vbox.addWidget(self.le_wood_images)
        vbox.addStretch(1)

        w.setLayout(vbox)
        return w

    def create_bit(self):
        '''Creates the layout for bit preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        us = self.units.units_string(withParens=True)
        self.le_bit_width_label = QtGui.QLabel('Initial Bit Width{}:'.format(us))
        self.le_bit_width = QtGui.QLineEdit(w)
        self.le_bit_width.setFixedWidth(self.line_edit_width)
        self.le_bit_width.editingFinished.connect(self._on_bit_width)
        tt = 'The initial bit width when pyRouterJig starts.'
        grid = form_line(self.le_bit_width_label, self.le_bit_width, tt)
        vbox.addLayout(grid)

        self.le_bit_depth_label = QtGui.QLabel('Initial Bit Depth{}:'.format(us))
        self.le_bit_depth = QtGui.QLineEdit(w)
        self.le_bit_depth.setFixedWidth(self.line_edit_width)
        self.le_bit_depth.editingFinished.connect(self._on_bit_depth)
        tt = 'The initial bit depth when pyRouterJig starts.'
        grid = form_line(self.le_bit_depth_label, self.le_bit_depth, tt)
        vbox.addLayout(grid)

        self.le_bit_angle_label = QtGui.QLabel('Initial Bit Angle (deg.):')
        self.le_bit_angle = QtGui.QLineEdit(w)
        self.le_bit_angle.setFixedWidth(self.line_edit_width)
        self.le_bit_angle.editingFinished.connect(self._on_bit_angle)
        tt = 'The initial bit angle when pyRouterJig starts.'
        grid = form_line(self.le_bit_angle_label, self.le_bit_angle, tt)
        vbox.addLayout(grid)
        vbox.addStretch(1)

        w.setLayout(vbox)
        return w

    def create_output(self):
        '''Creates the layout for output preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        self.cb_show_caul = QtGui.QCheckBox('Show Caul Template', w)
        self.cb_show_caul.stateChanged.connect(self._on_show_caul)
        self.cb_show_caul.setToolTip('Display the template for clamping cauls')
        vbox.addWidget(self.cb_show_caul)

        self.cb_show_finger_widths = QtGui.QCheckBox('Show Finger Widths', w)
        self.cb_show_finger_widths.stateChanged.connect(self._on_show_finger_widths)
        self.cb_show_finger_widths.setToolTip('Display the width of each finger')
        vbox.addWidget(self.cb_show_finger_widths)

        self.cb_show_fit = QtGui.QCheckBox('Show Fit', w)
        self.cb_show_fit.stateChanged.connect(self._on_show_caul)
        self.cb_show_fit.setToolTip('Display fit of joint')
        vbox.addWidget(self.cb_show_fit)

        self.cb_rpid = QtGui.QCheckBox('Show Router Pass Identifiers', w)
        self.cb_rpid.stateChanged.connect(self._on_rpid)
        self.cb_rpid.setToolTip('On each router pass, label its identifier')
        vbox.addWidget(self.cb_rpid)

        self.cb_rploc = QtGui.QCheckBox('Show Router Pass Locations', w)
        self.cb_rploc.stateChanged.connect(self._on_rploc)
        self.cb_rploc.setToolTip('On each router pass, label its distance from the right edge')
        vbox.addWidget(self.cb_rploc)

        self.le_printsf_label = QtGui.QLabel('Print Scale Factor:')
        self.le_printsf = QtGui.QLineEdit(w)
        self.le_printsf.setFixedWidth(self.line_edit_width)
        self.le_printsf.editingFinished.connect(self._on_printsf)
        tt = 'Scale output by this factor when printing.'
        grid = form_line(self.le_printsf_label, self.le_printsf, tt)
        vbox.addLayout(grid)

        self.le_min_image_label = QtGui.QLabel('Min Image Width (pixels):')
        self.le_min_image = QtGui.QLineEdit(w)
        self.le_min_image.setFixedWidth(self.line_edit_width)
        self.le_min_image.editingFinished.connect(self._on_min_image)
        tt = 'On save image, minimum width of image.'
        grid = form_line(self.le_min_image_label, self.le_min_image, tt)
        vbox.addLayout(grid)

        self.le_max_image_label = QtGui.QLabel('Max Image Width (pixels):')
        self.le_max_image = QtGui.QLineEdit(w)
        self.le_max_image.setFixedWidth(self.line_edit_width)
        self.le_max_image.editingFinished.connect(self._on_max_image)
        tt = 'On save image, maximum width of image.'
        grid = form_line(self.le_max_image_label, self.le_max_image, tt)
        vbox.addLayout(grid)

        w.setLayout(vbox)
        return w

    def create_misc(self):
        '''Creates the layout for misc preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        us = self.units.units_string(withParens=True)
        self.le_min_finger_width_label = QtGui.QLabel('Min Finger Width{}:'.format(us))
        self.le_min_finger_width = QtGui.QLineEdit(w)
        self.le_min_finger_width.setFixedWidth(self.line_edit_width)
        self.le_min_finger_width.editingFinished.connect(self._on_min_finger_width)
        tt = 'The minimum allowable finger width.  Currently, only enforced for Equal Spacing.'
        grid = form_line(self.le_min_finger_width_label, self.le_min_finger_width, tt)
        vbox.addLayout(grid)

        self.le_caul_trim_label = QtGui.QLabel('Caul Trim{}:'.format(us))
        self.le_caul_trim = QtGui.QLineEdit(w)
        self.le_caul_trim.setFixedWidth(self.line_edit_width)
        self.le_caul_trim.editingFinished.connect(self._on_caul_trim)
        tt = 'The distance from the edge of each finger to the edge of the corresponding caul finger.'
        grid = form_line(self.le_caul_trim_label, self.le_caul_trim, tt)
        vbox.addLayout(grid)
        vbox.addStretch(1)

        w.setLayout(vbox)
        return w

    def create_buttons(self):
        '''Creates the layout for the buttons'''
        hbox_btns = QtGui.QHBoxLayout()
        
        btn_cancel = QtGui.QPushButton('Cancel', self)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_cancel.setAutoDefault(False)
        btn_cancel.setFocusPolicy(QtCore.Qt.ClickFocus)
        btn_cancel.setToolTip('Discard any preference changes and continue.')
        hbox_btns.addWidget(btn_cancel)
        
        self.btn_save = QtGui.QPushButton('Save', self)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_save.setAutoDefault(False)
        self.btn_save.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.btn_save.setEnabled(False)
        self.btn_save.setToolTip('Save preference changes permanently to your configuration file.')
        hbox_btns.addWidget(self.btn_save)
        return hbox_btns

    def initialize(self):
        '''
        Initializes certain widgets to their current values in the config object.
        '''
        self.change_state_on_init = self.change_state

        if self.config.metric:
            self.cb_units.setCurrentIndex(0)
        else:
            self.cb_units.setCurrentIndex(1)

        self.le_num_incr.setText(str(self.config.num_increments))
        self.le_wood_images.setText(str(self.config.wood_images))
        self.cb_show_finger_widths.setChecked(self.config.show_finger_widths)
        self.cb_show_caul.setChecked(self.config.show_caul)
        self.cb_show_fit.setChecked(self.config.show_fit)
        self.cb_rpid.setChecked(self.config.show_router_pass_identifiers)
        self.cb_rploc.setChecked(self.config.show_router_pass_locations)
        self.le_printsf.setText(str(self.config.print_scale_factor))
        self.le_min_image.setText(str(self.config.min_image_width))
        self.le_max_image.setText(str(self.config.max_image_width))
        self.le_board_width.setText(str(self.config.board_width))
        self.le_db_thick.setText(str(self.config.double_board_thickness))
        self.le_bit_width.setText(str(self.config.bit_width))
        self.le_bit_depth.setText(str(self.config.bit_depth))
        self.le_bit_angle.setText(str(self.config.bit_angle))
        self.le_min_finger_width.setText(str(self.config.min_finger_width))
        self.le_caul_trim.setText(str(self.config.caul_trim))
        self.set_wood_combobox()

    def update_state(self, key, state=1):
        '''
        Updates the change state of the configuration
        '''
        if self.config.__dict__[key] != self.new_config[key]:
            if self.config.debug:
                print('qt_config:update_state {} {}'.format(key, self.new_config[key]))
            self.change_state = max(state, self.change_state)
            self.btn_save.setEnabled(True)

    def units_label(self, metric):
        label = 'Increments per '
        if metric:
            label += 'mm'
        else:
            label += 'inch'
        label +=':'
        return label

    @QtCore.pyqtSlot()
    def _on_cancel(self):
        '''
        Handles Cancel button events.
        '''
        if self.config.debug:
            print('qt_config:_on_cancel')
        self.setResult(0)
        # Set state back to the current configuration
        self.new_config = self.config.__dict__.copy()
        self.change_state = self.change_state_on_init
        self.close()

    @QtCore.pyqtSlot()
    def _on_save(self):
        '''
        Handles Save button events.
        '''
        if self.config.debug:
            print('qt_config:_on_save')
        do_save_config = False
        do_restart = False
        if self.change_state == 2:
            # Units were changes, so ask for a restart
            box = QtGui.QMessageBox(self)
            box.setTextFormat(QtCore.Qt.RichText)
            box.setIcon(QtGui.QMessageBox.NoIcon)
            box.setText('<font size=5 color=red>Warning!</font>')
            question = '<font size=5>You have changed a Units setting, which'\
                       ' requires <i>pyRouterJig</i> to restart to take effect.'\
                       ' Your current joint will be lost, unless you have already saved it. <p>'\
                       ' Press <b>Restart</b> to save the settings and restart.<p>'\
                       ' Press <b>Cancel</b> to discard the changes to preferences that'\
                       ' you have made.</font>'
            box.setInformativeText(question)
            buttonRestart = box.addButton('Restart', QtGui.QMessageBox.AcceptRole)
            buttonCancel = box.addButton('Cancel', QtGui.QMessageBox.AcceptRole)
            box.setDefaultButton(buttonCancel)
            box.raise_()
            box.exec_()
            if box.clickedButton() == buttonRestart:
                do_save_config = True
                do_restart = True
            else:
                self._on_cancel()
        elif self.change_state == 1:
            # Units were not changed
            do_save_config = True
        if do_save_config:
            config_file.set_default_dimensions(self.new_config)
            self.config.__dict__.update(self.new_config)
            c = config_file.Configuration()
            c.write_config(self.new_config)
        if do_restart:
            os.execv(sys.argv[0], sys.argv)
        self.setResult(1)
        self.change_state = 0
        self.btn_save.setEnabled(False)
        self.close()

    def closeEvent(self, event):
        '''
        This is called on save, cancel, and if user closes the window.
        '''
        if self.config.debug:
            print('qt_config:closeEvent')
        self.btn_save.setEnabled(self.change_state > 0)

    @QtCore.pyqtSlot(int)
    def _on_units(self, index):
        if self.config.debug:
            print('qt_config:_on_units', index)
        s = str(self.cb_units.itemText(index))
        metric = (s == 'Metric')
        if metric != self.config.metric:
            self.new_config['metric'] = metric
            self.update_state('metric', 2)
            if metric:
                 self.le_num_incr.setText('1')
            else:
                 self.le_num_incr.setText('32')
            self.le_num_incr_label.setText(self.units_label(metric))

    @QtCore.pyqtSlot()
    def _on_num_incr(self):
        if self.config.debug:
            print('qt_config:_on_num_incr')
        if self.le_num_incr.isModified():
            text = str(self.le_num_incr.text())
            self.new_config['num_increments'] = int(text)
            self.update_state('num_increments', 2)

    @QtCore.pyqtSlot()
    def _on_bit_width(self):
        if self.config.debug:
            print('qt_config:_on_bit_width')
        val = qt_utils.set_router_value(self.le_bit_width, self.bit, 'width',
                                        'set_width_from_string')
        if val is not None:
            self.new_config['bit_width'] = val
            self.update_state('bit_width')

    @QtCore.pyqtSlot()
    def _on_bit_depth(self):
        if self.config.debug:
            print('qt_config:_on_bit_depth')
        val = qt_utils.set_router_value(self.le_bit_depth, self.bit, 'depth',
                                        'set_depth_from_string')
        if val is not None:
            self.new_config['bit_depth'] = val
            self.update_state('bit_depth')

    @QtCore.pyqtSlot()
    def _on_bit_angle(self):
        if self.config.debug:
            print('qt_config:_on_bit_angle')
        val = qt_utils.set_router_value(self.le_bit_angle, self.bit, 'angle',
                                        'set_angle_from_string', True)
        if val is not None:
            self.new_config['bit_angle'] = val
            self.update_state('bit_angle')

    @QtCore.pyqtSlot()
    def _on_board_width(self):
        if self.config.debug:
            print('qt_config:_on_board_width')
        val = qt_utils.set_router_value(self.le_board_width, self.board, 'width',
                                        'set_width_from_string')
        if val is not None:
            self.new_config['board_width'] = val
            self.update_state('board_width')

    @QtCore.pyqtSlot()
    def _on_db_thick(self):
        if self.config.debug:
            print('qt_config:_on_db_thick')
        val = qt_utils.set_router_value(self.le_db_thick, self.board, 'dheight',
                                        'set_height_from_string', bit=self.bit)
        if val is not None:
            self.new_config['double_board_thickness'] = val
            self.update_state('double_board_thickness')

    @QtCore.pyqtSlot(int)
    def _on_wood(self, index):
        if self.config.debug:
            print('qt_config:_on_wood', index)
        s = str(self.cb_wood.itemText(index))
        if s != self.config.default_wood:
            self.new_config['default_wood'] = s
            self.update_state('default_wood')

    @QtCore.pyqtSlot()
    def _on_wood_images(self):
        if self.config.debug:
            print('qt_config:_on_wood_images')
        if self.le_wood_images.isModified():
            text = str(self.le_wood_images.text())
            self.new_config['wood_images'] = text
            self.set_wood_combobox()
            self.update_state('wood_images')

    @QtCore.pyqtSlot()
    def _on_show_finger_widths(self):
        if self.config.debug:
            print('qt_config:_on_show_finger_widths')
        self.new_config['show_finger_widths'] = self.cb_show_finger_widths.isChecked()
        self.update_state('show_finger_widths')

    @QtCore.pyqtSlot()
    def _on_show_caul(self):
        if self.config.debug:
            print('qt_config:_on_show_caul')
        self.new_config['show_caul'] = self.cb_show_caul.isChecked()
        self.update_state('show_caul')

    @QtCore.pyqtSlot()
    def _on_show_fit(self):
        if self.config.debug:
            print('qt_config:_on_show_fit')
        self.new_config['show_fit'] = self.cb_show_fit.isChecked()
        self.update_state('show_fit')

    @QtCore.pyqtSlot()
    def _on_rpid(self):
        if self.config.debug:
            print('qt_config:_on_rpid')
        self.new_config['show_router_pass_identifiers'] = self.cb_rpid.isChecked()
        self.update_state('show_router_pass_identifiers')

    @QtCore.pyqtSlot()
    def _on_rploc(self):
        if self.config.debug:
            print('qt_config:_on_rploc')
        self.new_config['show_router_pass_locations'] = self.cb_rploc.isChecked()
        self.update_state('show_router_pass_locations')

    @QtCore.pyqtSlot()
    def _on_printsf(self):
        if self.config.debug:
            print('qt_config:_on_printsf')
        if self.le_printsf.isModified():
            if self.config.debug:
                print('  _on_printsf modified')
            self.le_printsf.setModified(False)
            s = str(self.le_printsf.text())
            ok = True
            try:
                new_value = float(s)
                if new_value <= 0:
                    ok = False
            except:
                ok = False
            if ok:
                self.new_config['print_scale_factor'] = float(s)
                self.update_state('print_scale_factor')
            else:
                msg = 'Unable to set Print Scale Factor to: {}<p>'\
                      'Set to a positive number.'.format(s)
                QtGui.QMessageBox.warning(self, 'Error', msg)
                self.le_printsf.setText(str(self.new_config['print_scale_factor']))

    @QtCore.pyqtSlot()
    def _on_min_image(self):
        if self.config.debug:
            print('qt_config:_on_min_image')
        if self.le_min_image.isModified():
            self.le_min_image.setModified(False)
            s = str(self.le_min_image.text())
            ok = True
            try:
                new_value = int(s)
                if new_value <= 0:
                    ok = False
            except:
                ok = False
            if ok:
                self.new_config['min_image_width'] = int(s)
                self.update_state('min_image_width')
            else:
                msg = 'Unable to set Min Image Width to: {}<p>'\
                      'Set to a positive integer.'.format(s)
                QtGui.QMessageBox.warning(self, 'Error', msg)
                self.le_min_image.setText(str(self.new_config['min_image_width']))

    @QtCore.pyqtSlot()
    def _on_max_image(self):
        if self.config.debug:
            print('qt_config:_on_max_image')
        if self.le_max_image.isModified():
            self.le_max_image.setModified(False)
            s = str(self.le_max_image.text())
            ok = True
            min_value = int(self.new_config['min_image_width'])
            try:
                new_value = int(s)
                if new_value <= min_value:
                    ok = False
            except:
                ok = False
            if ok:
                self.new_config['max_image_width'] = int(s)
                self.update_state('max_image_width')
            else:
                msg = 'Unable to set Max Image Width to: {}<p>'\
                      'Set to a positive integer >= Min Image Width ({})'.format(s, min_value)
                QtGui.QMessageBox.warning(self, 'Error', msg)
                self.le_max_image.setText(str(self.new_config['max_image_width']))

    @QtCore.pyqtSlot()
    def _on_min_finger_width(self):
        if self.config.debug:
            print('qt_config:_on_min_finger_width')
        i = self.units.abstract_to_increments(self.new_config['min_finger_width'])
        v = Misc_Value(i, self.units, 'Min Finger Width')
        val = qt_utils.set_router_value(self.le_min_finger_width, v, 'value',
                                        'set_value_from_string')
        if val is not None:
            self.new_config['min_finger_width'] = s
            self.update_state('min_finger_width')

    @QtCore.pyqtSlot()
    def _on_caul_trim(self):
        if self.config.debug:
            print('qt_config:_on_caul_trim')
        i = self.units.abstract_to_increments(self.new_config['caul_trim'])
        v = Misc_Value(i, self.units, 'Caul Trim')
        val = qt_utils.set_router_value(self.le_caul_trim, v, 'value',
                                        'set_value_from_string')
        if val is not None:
            self.new_config['caul_trim'] = val
            self.update_state('caul_trim')