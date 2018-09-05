
from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui as qt
from PyQt5 import QtCore as qc
import qtgui.qtbuilders as build

class DeskDialog(qw.QDialog):

    def __init__(self, parent, fields:dict, config_updater:callable):
        super().__init__(parent)
        self.config_updater = config_updater
        self.__config_to_widgets(fields)


    def __config_to_widgets(self, fields:dict):
        parent = self

        self.lab_room = qw.QLabel(parent=parent, text='Room name')
        self.ent_room = qw.QLineEdit(fields['room name'], parent)
        self.lab_desk = qw.QLabel(parent=parent, text='Desk name')
        self.ent_desk = qw.QLineEdit(fields['desk name'], parent)
        self.but_cancel = build.button('Cancel', self, onclick=self.reject)
        self.but_accept = build.button('Apply', self, onclick=self.accept)

        lay_room = qw.QHBoxLayout()
        lay_room.addWidget(self.lab_room)
        lay_room.addWidget(self.ent_room)

        lay_desk = qw.QHBoxLayout()
        lay_desk.addWidget(self.lab_desk)
        lay_desk.addWidget(self.ent_desk)

        lay_buttons = qw.QHBoxLayout()
        lay_desk.addWidget(self.but_cancel)
        lay_desk.addWidget(self.but_accept)

        lay_dialog = qw.QVBoxLayout()
        lay_dialog.addLayout(lay_room)
        lay_dialog.addLayout(lay_desk)
        lay_dialog.addLayout(lay_buttons)
        self.setLayout(lay_dialog)

    def accept(self):
        self.config_updater({'room name': self.ent_room.text(), 'desk name': self.ent_desk.text()})
        super().accept()
