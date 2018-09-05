

import tkinter as tk
from enum import Enum
from tkinter import filedialog, simpledialog, font
import PIL
from PIL import Image, ImageTk
import clyngor
from gui_desk_dialog import DeskDialog


WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600

class ActionState(Enum):
    Nothing = 0
    PlaceDesk = 1
    RemoveDesk = 2
    EditDesk = 3

def load_humans() -> (str, str):
    "Yield pairs of (name, team)"
    for model in clyngor.solve('humans.lp').by_predicate:
        for args in model['human']:
            if len(args) == 1:
                yield args[0], None
            elif len(args) == 2:
                yield args
            elif len(args) >= 3 or not args:
                print(f'ERROR: unhandled human "{args}"')

def load_desks() -> [(int, int), (str, str)]:
    "Yield (room name, desk name, position x, position y) found in export-offices.lp"
    for model in clyngor.solve('export-offices.lp').by_predicate:
        for args in model.get('desk_px', ()):
            if len(args) == 4:
                room, name, x, y = args
                yield (int(x), int(y)), (room.strip('"'), name.strip('"'))
            else:
                print(f'ERROR: unhandled desk "{args}"')

def call_placement_engine():
    models = clyngor.solve(('humans.lp', 'offices.lp', 'engine.lp'))
    for model in models.by_predicate:
        yield model


class MainWindow(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.geometry('{}x{}'.format(*WINDOW_SIZE))
        self.parent.title("Cathplace")
        self.desks = dict(load_desks())  # position: metadata (room, name)
        self.placement = {}  # desk position: human occupying the place
        self.humans = tuple(load_humans())
        self.__build_widgets()
        self._reset_action_state()

    def number_of_unassigned_humans(self) -> int:
        return len(self.humans) - self.number_of_assigned_humans()
    def number_of_assigned_humans(self) -> int:
        return len(set(self.placement.values()) - {None})

    def build_a_placement(self):
        pass

    def __build_widgets(self):
        raw_image = Image.open('plan-patio.png')
        raw_image = raw_image.resize(WINDOW_SIZE, PIL.Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(raw_image)
        self.image.rawdata = raw_image
        self.canvas = tk.Canvas(self)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-2>", self._reset_action_state)
        self.canvas.bind("<Button-3>", lambda e: self.on_canvas_click(e, True))
        self.canvas.pack(fill=tk.BOTH, expand=1)
        self.paint()

        self.but_state_place_desk = tk.Button(self, text='Place desks', command=lambda: self.set_action_state(ActionState.PlaceDesk))
        self.but_state_place_desk.pack()
        self.but_state_remove_desk = tk.Button(self, text='Remove desks', command=lambda: self.set_action_state(ActionState.RemoveDesk))
        self.but_state_remove_desk.pack()
        self.but_state_edit_desk = tk.Button(self, text='Edit desks', command=lambda: self.set_action_state(ActionState.EditDesk))
        self.but_state_edit_desk.pack()
        self.but_export_desk = tk.Button(self, text='Export desks', command=self.export_desks)
        self.but_export_desk.pack()

        self.pack(fill=tk.BOTH, expand=1)


    def set_action_state(self, state):
        assert state in ActionState
        self.action_state = state
    def _reset_action_state(self, _=None):
        self.set_action_state(ActionState.Nothing)

    def on_canvas_click(self, event, unclick=False):
        pos = posx, posy = event.x, event.y
        # compute the action state
        action_state = self.action_state
        if unclick and action_state is ActionState.PlaceDesk:
            action_state = ActionState.RemoveDesk
        elif unclick and action_state is ActionState.RemoveDesk:
            action_state = ActionState.PlaceDesk
        # apply the action
        if action_state is ActionState.PlaceDesk:
            self.desks[pos] = None
            self.build_desk_metadata(pos)
        elif action_state is ActionState.RemoveDesk:
            for x, y in tuple(self.desks):
                if (posx - x) ** 2 + (posy - y) ** 2 < 60:
                    del self.desks[x, y]
                    return
        elif action_state is ActionState.EditDesk:
            for x, y in tuple(self.desks):
                if (posx - x) ** 2 + (posy - y) ** 2 < 60:
                    self.build_desk_metadata((x, y), *self.desks[x, y])
        else:
            assert action_state is ActionState.Nothing
        self.paint()


    def paint(self, event=None):
        self.canvas.create_image(WINDOW_WIDTH//2, WINDOW_HEIGHT//2, image=self.image)
        for (x, y), metadata in self.desks.items():
            occupant = self.placement.get((x, y))
            color = name_to_color(occupant)
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=color)
            if metadata:
                txt = self.canvas.create_text(x, y-10, text=' '.join(metadata), fill='white')
            if occupant:
                self.canvas.create_text(x, y+10, text=occupant, fill=color)


    def export_desks(self):
        with open('export-offices.lp', 'w') as fd:
            for (x, y), metadata in self.desks.items():
                if metadata is None:
                    continue
                if len(metadata) == 2:
                    room, name = metadata
                    if name:
                        fd.write(f'desk("{room}","{name}").\n')
                    else:
                        fd.write(f'room("{room}").\n')
                    fd.write(f'desk_px("{room}","{name}",{x},{y}).\n')

    def build_desk_metadata(self, deskpos:(int, int), room:str='', name:str=''):
        def update(metadata):
            self.desks[deskpos] = metadata['room name'], metadata['desk name']
        dialog = DeskDialog(self, {'room name': room, 'desk name': name}, update, can_cancel=True)
        self.wait_window(dialog)  # window could modify self.server_config


def name_to_color(name:str) -> str:
    return 'red'  # sorry


if __name__ == '__main__':
    root = tk.Tk()
    # Be sure to use a monospaced font
    default_font = font.nametofont('TkFixedFont')
    default_font.configure(size=13, weight='bold')
    root.option_add('*Font', default_font)
    MainWindow(root)
    root.mainloop()
