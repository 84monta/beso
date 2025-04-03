"""
Event handler module for BESO topology optimization GUI
This module contains event handling functions for the GUI
"""

import os
import sys
import datetime
import threading
import webbrowser
import FreeCADGui
import FreeCAD as App
from femtools import ccxtools

from beso_gui_config import write_config_file


def update_domains(self):
    """Update domain information"""
    # Get material objects and thickness objects
    self.materials = []
    self.thicknesses = []
    try:
        App.ActiveDocument.Objects
    except AttributeError:
        App.newDocument("Unnamed")
        print("Warning: Missing active document with FEM analysis. New document have been created.")
    
    # Collect material objects
    for obj in App.ActiveDocument.Objects:
        if obj.Name[:23] == "MechanicalSolidMaterial":
            self.materials.append(obj)
        elif obj.Name[:13] == "MaterialSolid":
            self.materials.append(obj)
        elif obj.Name[:13] == "SolidMaterial":
            self.materials.append(obj)
        elif obj.Name[:17] == "ElementGeometry2D":
            self.thicknesses.append(obj)
    
    # Update material combo boxes
    self.combo.clear()
    self.combo.addItem("None")
    self.combo1.clear()
    self.combo1.addItem("None")
    self.combo2.clear()
    self.combo2.addItem("None")
    self.combo0t.clear()
    self.combo0t.addItem("None")
    self.combo1t.clear()
    self.combo1t.addItem("None")
    self.combo2t.clear()
    self.combo2t.addItem("None")
    
    # Update list widgets
    self.widget.clear()
    self.widget.addItem("All defined")
    self.widget.addItem("Domain 0")
    self.widget.addItem("Domain 1")
    self.widget.addItem("Domain 2")
    self.widget.setCurrentItem(self.widget.item(0))
    
    self.widget1.clear()
    self.widget1.addItem("All defined")
    self.widget1.addItem("Domain 0")
    self.widget1.addItem("Domain 1")
    self.widget1.addItem("Domain 2")
    self.widget1.setCurrentItem(self.widget1.item(0))
    
    self.widget2.clear()
    self.widget2.addItem("All defined")
    self.widget2.addItem("Domain 0")
    self.widget2.addItem("Domain 1")
    self.widget2.addItem("Domain 2")
    self.widget2.setCurrentItem(self.widget2.item(0))
    
    # Add material objects to combo boxes
    for mat in self.materials:
        self.combo.addItem(mat.Label)
        self.combo1.addItem(mat.Label)
        self.combo2.addItem(mat.Label)
    
    # Add thickness objects to combo boxes
    for th in self.thicknesses:
        self.combo0t.addItem(th.Label)
        self.combo1t.addItem(th.Label)
        self.combo2t.addItem(th.Label)
    
    # Select the first material (if exists)
    if self.materials:
        self.combo.setCurrentIndex(1)


def on_domain_change(self, domain_idx, index):
    """Process domain selection change"""
    # Attribute names of widgets related to domain
    combo_t_attr = f"combo{domain_idx}t" if domain_idx else "combo0t"
    checkbox_attr = f"checkbox{domain_idx}" if domain_idx else "checkbox"
    textbox_attr = f"textbox{domain_idx}" if domain_idx else "textbox"
    
    # Set widget enabled/disabled state
    combo_t = getattr(self, combo_t_attr, None)
    checkbox = getattr(self, checkbox_attr, None)
    textbox = getattr(self, textbox_attr, None)
    
    if index == 0:  # None selection
        if combo_t:
            combo_t.setEnabled(False)
        if checkbox:
            checkbox.setEnabled(False)
        if textbox:
            textbox.setEnabled(False)
    else:
        if combo_t:
            combo_t.setEnabled(True)
        if checkbox:
            checkbox.setEnabled(True)
        if textbox:
            textbox.setEnabled(True)


def on_filter_change(self, filter_idx, index):
    """Process filter type change"""
    # Attribute names of widgets related to filter
    combo_r_attr = f"combo{6+filter_idx}r"
    textbox_range_attr = f"textbox{6+filter_idx}"
    textbox_dir_attr = f"textbox{9+filter_idx}"
    widget_attr = f"widget{filter_idx}" if filter_idx else "widget"
    
    # Get widgets
    combo_r = getattr(self, combo_r_attr, None)
    textbox_range = getattr(self, textbox_range_attr, None)
    textbox_dir = getattr(self, textbox_dir_attr, None)
    widget = getattr(self, widget_attr, None)
    
    if index == 0:  # None selection
        if combo_r:
            combo_r.setEnabled(False)
        if textbox_range:
            textbox_range.setEnabled(False)
        if textbox_dir:
            textbox_dir.setEnabled(False)
        if widget:
            widget.setEnabled(False)
    elif index == 2:  # casting selection
        if combo_r:
            combo_r.setEnabled(True)
        if textbox_dir:
            textbox_dir.setEnabled(True)
        if widget:
            widget.setEnabled(True)
        # Update range textbox state
        on_filter_range_change(self, filter_idx, combo_r.currentIndex() if combo_r else 0)
    else:  # simple selection
        if combo_r:
            combo_r.setEnabled(True)
        if textbox_dir:
            textbox_dir.setEnabled(False)
        if widget:
            widget.setEnabled(True)
        # Update range textbox state
        on_filter_range_change(self, filter_idx, combo_r.currentIndex() if combo_r else 0)


def on_filter_range_change(self, filter_idx, index):
    """Process filter range type change"""
    # Range textbox attribute name
    textbox_range_attr = f"textbox{6+filter_idx}"
    
    # Get textbox
    textbox_range = getattr(self, textbox_range_attr, None)
    
    if textbox_range:
        if index == 0:  # auto selection
            textbox_range.setEnabled(False)
        else:  # manual selection
            textbox_range.setEnabled(True)


def generate_config_callback(self):
    """Generate configuration file callback"""
    return write_config_file(self, os.path.join(self.beso_dir, "beso_conf.py"))


def edit_config_callback(self):
    """Edit configuration file callback"""
    conf_file_path = generate_config_callback(self)
    FreeCADGui.insert(os.path.normpath(conf_file_path))


def run_optimization_callback(self):
    """Run optimization callback"""
    # Generate configuration file in beso directory
    generate_config_callback(self)
    
    # Change working directory to input file directory
    if self.inp_file:
        output_file_path = os.path.normpath(os.path.dirname(self.inp_file))
        os.chdir(output_file_path)
        
        # Set file name as command line argument
        input_file = os.path.normpath(self.inp_file)
        sys.argv = [sys.argv[0], input_file]
    
    # Execute beso_main.py (with UTF-8 encoding explicitly specified)
    exec(open(os.path.join(self.beso_dir, "beso_main.py"), encoding="utf-8").read())


def run_threaded_optimization(self):
    """Run threaded optimization (non-blocking for FreeCAD)"""
    # Generate configuration file
    generate_config_callback(self)
    
    # Create and execute optimization thread
    optimization_thread = RunOptimization(self.beso_dir, self.inp_file)
    optimization_thread.start()


def open_example_callback(self):
    """Open example callback"""
    webbrowser.open_new_tab("https://github.com/fandaL/beso/wiki/Example-4:-GUI-in-FreeCAD")


def open_conf_comments_callback(self):
    """Open configuration comments callback"""
    webbrowser.open_new_tab("https://github.com/fandaL/beso/blob/master/beso_conf.py")


def open_log_file_callback(self):
    """Open log file callback"""
    if self.textbox_file_name.text() in ["None analysis file selected", ""]:
        print("None analysis file selected")
    else:
        log_file = os.path.normpath(self.textbox_file_name.text()[:-4] + ".log")
        try:
            FreeCADGui.open(log_file)
        except:
            print(f"No log file found at {log_file}")


class RunOptimization(threading.Thread):
    """Class to run optimization in a separate thread"""
    def __init__(self, beso_dir, inp_file=None):
        threading.Thread.__init__(self)
        self.beso_dir = beso_dir
        self.inp_file = inp_file

    def run(self):
        """Thread execution method"""
        # Change working directory to input file directory and set command line argument
        if self.inp_file:
            output_file_path = os.path.normpath(os.path.dirname(self.inp_file))
            os.chdir(output_file_path)
            
            # Set file name as command line argument
            input_file = os.path.normpath(self.inp_file)
            sys.argv = [sys.argv[0], input_file]
        
        # Execute beso_main.py
        exec(open(os.path.join(self.beso_dir, "beso_main.py"), encoding="utf-8").read())
