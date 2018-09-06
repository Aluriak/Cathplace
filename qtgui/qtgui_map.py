import sys
from enum import Enum
from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui as qt
from PyQt5 import QtCore as qc
from functions import name_to_color

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600


class ActionState(Enum):
    Nothing = 0
    PlaceDesk = 1
    RemoveDesk = 2
    EditDesk = 3


class MapWidget(qw.QWidget):
    "Show the map found in given file"

    def __init__(self, parent, mapfile:str, desks:dict, placement:dict, humans:dict):
        super().__init__(parent=parent)
        self.action_state = ActionState.Nothing  # modified by parent
        self.raw_data = qt.QImage(mapfile).scaled(*WINDOW_SIZE, aspectRatioMode=qc.Qt.KeepAspectRatioByExpanding)
        self.setGeometry(*WINDOW_SIZE, 280, 170)
        self.show()
        # reference to attributes of mother class
        self.desks, self.humans = desks, humans

    @property  # need special treatment because the dict is deleted when a new placement is found by parent
    def placement(self) -> dict: return self.parent().placement

    def mousePressEvent(self, event):
        pos = posx, posy = event.pos().x(), event.pos().y()
        unclick = event.button() == 3
        # compute the action state
        action_state = self.action_state
        if unclick and action_state is ActionState.PlaceDesk:
            action_state = ActionState.RemoveDesk
        elif unclick and action_state is ActionState.RemoveDesk:
            action_state = ActionState.PlaceDesk
        # apply the action
        if action_state is ActionState.PlaceDesk:
            self.desks[pos] = None
            self.parent().build_desk_metadata(pos)
        elif action_state is ActionState.RemoveDesk:
            for x, y in tuple(self.desks):
                if (posx - x) ** 2 + (posy - y) ** 2 < 60:
                    del self.desks[x, y]
                    break
        elif action_state is ActionState.EditDesk:
            for x, y in tuple(self.desks):
                if (posx - x) ** 2 + (posy - y) ** 2 < 60:
                    self.parent().build_desk_metadata((x, y), *self.desks[x, y])
        else:
            assert action_state is ActionState.Nothing
        self.update()

    def paintEvent(self, event):
        draw = self.canvas = qt.QPainter(self)
        draw.drawImage(qc.QPoint(0, 0), self.raw_data)
        draw.setFont(qt.QFont('Mono', 10))
        for (x, y), metadata in self.desks.items():
            occupant = self.placement.get((x, y))
            color = qt.QColor(name_to_color(occupant))
            draw.setBrush(qt.QBrush(color))
            draw.drawEllipse(x-3, y-3, 6, 6)
            if metadata:
                draw.setPen(qt.QColor('white'))
                txt = draw.drawText(x, y-10, ' '.join(metadata))
            if occupant:
                draw.setPen(color)
                self.canvas.drawText(x, y+10, occupant)
        draw.end()


if __name__ == '__main__':
    app = qw.QApplication(sys.argv)
    ex = MapWidget()
    sys.exit(app.exec_())
