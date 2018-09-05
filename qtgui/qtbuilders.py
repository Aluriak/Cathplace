"""Provides high level interface to various builders.

"""
from PyQt5 import QtWidgets as qw
from PyQt5 import QtCore as qc


def grid_options_qt(row, column):
    return (row, column, qc.Qt.AlignRight | qc.Qt.AlignLeft)


def label(text, grid=None, row:int=0, column:int=0, tooltip:str=None,
          parent=None, grid_options:callable=grid_options_qt):
    """Build and return a label following given data"""
    lab = qw.QLabel(text=text, parent=parent)
    if tooltip: lab.setToolTip(tooltip)
    if grid: grid.addWidget(lab, *grid_options(row, column))
    return lab


def button(text, parent=None, grid=None, row:int=0, column:int=0, tooltip:str=None,
           onclick=None, grid_options:callable=grid_options_qt):
    but = qw.QPushButton(text, parent=parent)
    if onclick: but.clicked.connect(onclick)
    if tooltip: but.setToolTip(tooltip)
    if grid: grid.addWidget(but, *grid_options(row, column))
    return but

def checkbox(text, grid=None, row:int=0, column:int=0, tooltip:str=None,
             state:bool=False, onclick=None, parent=None,
             grid_options:callable=grid_options_qt):
    """Build and return a check button following given data"""
    chk = qw.QCheckBox(text, parent=parent)
    chk.setTristate(False)
    chk.setCheckState(2 if state else 0)  # despite no trisate, True == 1 == partial check ; therefore you can't use boolean directly
    if onclick: chk.stateChanged.connect(onclick)
    if tooltip: chk.setToolTip(tooltip)
    if grid: grid.addWidget(chk, *grid_options(row, column))
    chk.get = lambda chk=chk: chk.checkState()
    return chk

def combobox(values:iter, grid=None, row:int=0, column:int=0,
             start_value:str=None, tooltip:str=None,
             on_change:callable=None, parent=None,
             grid_options:callable=grid_options_qt):
    cmb = qw.QComboBox(parent=parent)
    cmb.addItems(values)
    cmb.setCurrentIndex(cmb.findText(start_value) if start_value in values else 0)
    if on_change: cmb.currentTextChanged.connect(on_change)
    if grid: grid.addWidget(cmb, *grid_options(row, column))
    def assign_values(values, cmb=cmb, on_change=on_change):
        # TODO: avoid useless signals sending (one per item added)
        while cmb.count() > 0: cmb.removeItem(0)
        cmb.addItems(values)
    cmb.setValues = assign_values
    cmb.get = lambda cmb=cmb: cmb.currentText()
    return cmb

def spinbox(value:int, grid=None, row:int=0, column:int=0,
            tooltip:str=None, on_change:callable=None, parent=None,
            step:int=1, grid_options:callable=grid_options_qt,
            min=None, max=None):
    spn = qw.QSpinBox(parent=parent, value=value)
    spn.setSingleStep(step)
    if min: spn.setMinimum(min)
    if max: spn.setMaximum(max)
    if tooltip: spn.setToolTip(tooltip)
    if grid: grid.addWidget(spn, *grid_options(row, column))
    if on_change: spn.valueChanged.connect(on_change)
    spn.get = lambda spn=spn: spn.value()
    return spn
