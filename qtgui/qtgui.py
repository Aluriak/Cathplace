"""GUI reboot, using Qt"""

import sys
import threading
from enum import Enum
from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui as qt
from PyQt5 import QtCore as qc
import PIL
from PIL import Image, ImageTk
import clyngor
from qtgui import qtbuilders as build
from functions import load_humans, load_desks, call_placement_engine, string_to_asp
from qtgui.qtgui_map import MapWidget, ActionState, WINDOW_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from qtgui.qtgui_desk import DeskDialog


DEFAULT_WM_TITLE = 'Cathplace'
WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = WINDOW_WIDTH+20, WINDOW_WIDTH+30
JUMP_QUANTITY = 20


class Application(qw.QMainWindow):
    """Main GUI object, aggregating all others"""

    def __init__(self, parent=None):
        # work related attributes
        self.desks = dict(load_desks())  # position: metadata (room, name)
        self.placement = {}  # desk position: human occupying the place
        self.humans = tuple(load_humans())
        self.models = iter(())  # iterable over models found by the solver
        # GUI related attributes
        super().__init__(parent)
        self.setWindowTitle(DEFAULT_WM_TITLE)
        self.setMinimumSize(*WINDOW_SIZE)
        self.__create_widgets()
        self.__create_main_window()
        self.__reset_action_state()


    def __create_main_window(self):
        # Create toolbar
        toolbar = self.addToolBar('Toolbar')
        toolbar.setFloatable(False)
        toolbar.setMovable(False)

        # solutions related actions
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_DialogSaveButton),
                          "Save the current solution in solution.lp file",
                          self.write_solution)
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_DialogOpenButton),
                          "Open the solution found in solution.lp file",
                          self.load_solution)
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_MediaPlay),
                          "compute possible (optimal) solutions, show the first one",
                          self.build_placement)
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_ArrowRight),
                          "show next available solution, if any",
                          self.show_next_placement)
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_MediaSeekForward),
                          f"Ignore {JUMP_QUANTITY} solutions, show the next one, if any",
                          self.jump_placements)

        # desk related actions
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_FileDialogNewFolder),
                          "click on a place on the map to add a desk",
                          lambda: self.set_action_state(ActionState.PlaceDesk))
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_DialogDiscardButton),
                          "click on an existing desk to delete it",
                          lambda: self.set_action_state(ActionState.RemoveDesk))
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_FileDialogInfoView),
                          "click on an existing desk to modify it",
                          lambda: self.set_action_state(ActionState.EditDesk))
        toolbar.addAction(self.style().standardIcon(qw.QStyle.SP_DialogApplyButton),
                          "write export-offices.lp file with existing desks",
                          self.export_desks)

        # Create menu bar
        self.setMenuBar(qw.QMenuBar())
        menu_prgm = self.menuBar().addMenu("&Program")
        menu_soln = self.menuBar().addMenu("&Solutions")
        menu_desk = self.menuBar().addMenu("&Desks and rooms")
        menu_pers = self.menuBar().addMenu("&Persistance")

        menu_prgm.addAction("&Quit", self.close)

        menu_soln.addAction("&Search solutions", self.build_placement)
        menu_soln.addAction("Show &next solution", self.show_next_placement)
        menu_soln.addAction("&Pass solutions", self.jump_placements)

        menu_desk.addAction("&Add", lambda: self.set_action_state(ActionState.PlaceDesk))
        menu_desk.addAction("&Remove", lambda: self.set_action_state(ActionState.RemoveDesk))
        menu_desk.addAction("&Edit", lambda: self.set_action_state(ActionState.EditDesk))
        menu_desk.addAction("E&xport all", self.export_desks)

        menu_pers.addAction("&Load saved solution", self.load_solution)
        menu_pers.addAction("&Export current solution", self.write_solution)
        menu_pers.addAction("Export &Desks", self.export_desks)

    def __create_widgets(self):
        self.wid_canvas = MapWidget(self, 'plan-patio.png', self.desks, self.placement, self.humans)
        # self.wid_visual = gui.visual.VisualWidget(self)
        # self.wid_program = gui.program.ProgramWidget(self, clingo_bin_path=self.__clingo_bin_path)

        # self.wid_central.addWidget(self.wid_program)
        # self.wid_central.addWidget(self.wid_visual)

        # lay_buttons = qw.QHBoxLayout()

        # parent = self.grp_desks = qw.QGroupBox(parent=self, title='Desks/Rooms')
        # grid = qw.QVBoxLayout()
        # self.but_quit = build.button('Quit', parent, grid, 0, 0, 'Good Bye, user !', self.close)
        # self.but_quit2 = build.button('Quit', parent, grid, 0, 1, 'Good Bye, user !', self.close)
        # parent.setLayout(grid)
        # lay_buttons.addWidget(parent)

        # parent = self.grp_solution = qw.QGroupBox(parent=self, title='Solution')
        # grid = qw.QVBoxLayout()
        # self.but_solve = build.button('Solve', parent, grid, 0, 0, 'Run solving !', self.close)
        # self.but_solve2 = build.button('Solve', parent, grid, 0, 1, 'Run solving !', self.close)
        # parent.setLayout(grid)
        # lay_buttons.addWidget(parent)


        # lay_central = qw.QVBoxLayout()
        # lay_central.addWidget(self.wid_canvas)
        # lay_central.addLayout(lay_buttons)


        self.setCentralWidget(self.wid_canvas)
        # self.setLayout(lay_buttons)
        # self.wid_central.addWidget(self.grp_desks)
        # self.wid_central.setStretchFactor(0,30)
        # self.wid_central.setStretchFactor(1,70)


    def set_action_state(self, state:ActionState):
        assert state in ActionState
        self.wid_canvas.action_state = state
    def __reset_action_state(self, _=None):
        self.set_action_state(ActionState.Nothing)


    def log(self, msg:str):
        """Write given message in logs"""
        print('LOGGING:', msg)
        # self.txt_log.set(msg)  # TODO Qt
        # self.update_idletasks()  # TODO Qt


    @staticmethod
    def run(**kwargs):
        """Instanciate and run the main application"""
        app = qw.QApplication([])
        app.setApplicationName(DEFAULT_WM_TITLE)
        ex = Application(**kwargs)
        ex.show()
        sys.exit(app.exec_())


    def number_of_unassigned_humans(self) -> int:
        return len(self.humans) - self.number_of_assigned_humans()
    def number_of_assigned_humans(self) -> int:
        return len(set(self.placement.values()) - {None})

    @property
    def reverse_desks(self) -> dict:
        "Return the mapping metadata -> positions"
        ret = {}
        for pos, meta in self.desks.items():
            if meta in ret:
                print(f'ERROR: desk of metadata "{meta}" is a doublon: found at {ret[meta]} and now at {pos}…')
            ret[meta] = pos
        return ret

    def build_placement(self):
        self.models = call_placement_engine()
        self.show_next_placement()

    def show_next_placement(self):
        reverse_desks = self.reverse_desks
        self.placement = {}  # empty placement
        model = next(self.models, ())
        if not model:
            print('ERROR: no more model')
            return
        for human, (_, (room, desk)) in model:
            deskpos = reverse_desks[room.strip('"'), desk.strip('"')]
            self.placement[deskpos] = human
        self.wid_canvas.update()

    def jump_placements(self):
        for _ in range(JUMP_QUANTITY):
            next(self.models, ())
        self.show_next_placement()

    def write_solution(self):
        with open('solution.lp', 'w') as fd:
            for deskpos, human in self.placement.items():
                room, desk = self.desks[deskpos]
                fd.write(f'place(({string_to_asp(room)},{string_to_asp(desk)}),{string_to_asp(human)}).\n')

    def load_solution(self):
        model = next(clyngor.solve('solution.lp', nb_model=1).by_predicate.careful_parsing.int_not_parsed, None)
        if model is None:
            print('ERROR: no solution written in solution.lp')
            return
        reverse_desks = self.reverse_desks
        for args in model.get('place', ()):
            if len(args) == 2:
                (_, (room, desk)), human = args
                deskpos = reverse_desks[room.strip('"'), desk.strip('"')]
                self.placement[deskpos] = human.strip('"')
            else:
                print(f'ERROR: invalid atom place/{len(args)} with arguments "{args}" not handled.')
        self.wid_canvas.update()


    def export_desks(self):
        with open('export-offices.lp', 'w') as fd:
            fd.write('% Export from GUI:\n')
            for (x, y), metadata in self.desks.items():
                if metadata is None:
                    continue
                if len(metadata) == 2:
                    room, name = map(string_to_asp, metadata)
                    if name:
                        fd.write(f'desk({room},{name}).\n')
                    else:
                        fd.write(f'room({room}).\n')
                    fd.write(f'desk_px({room},{name or ""},{x},{y}).\n\n')

    def build_desk_metadata(self, deskpos:(int, int), room:str='', name:str=''):
        def update(metadata):
            self.desks[deskpos] = metadata['room name'], metadata['desk name']
        dialog = DeskDialog(self, {'room name': room, 'desk name': name}, update)
        dialog.exec()
        if self.desks[deskpos] is None:
            del self.desks[deskpos]
        self.update()
