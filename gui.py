

import tkinter as tk
from enum import Enum
from tkinter import filedialog, simpledialog, font
import PIL
from PIL import Image, ImageTk
from pprint import pprint
import clyngor
from gui_desk_dialog import DeskDialog
from tooltip import Tooltip


WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
JUMP_QUANTITY = 20

class ActionState(Enum):
    Nothing = 0
    PlaceDesk = 1
    RemoveDesk = 2
    EditDesk = 3

def load_humans() -> (str, str):
    "Yield pairs of (name, team)"
    for model in clyngor.solve('humans.lp').by_predicate.careful_parsing.int_not_parsed:
        for args in model['human']:
            if len(args) == 1:
                yield args[0], None
            elif len(args) == 2:
                yield args
            elif len(args) >= 3 or not args:
                print(f'ERROR: unhandled human "{args}"')

def load_desks() -> [(int, int), (str, str)]:
    "Yield (room name, desk name, position x, position y) found in export-offices.lp"
    for model in clyngor.solve('export-offices.lp').by_predicate.careful_parsing.int_not_parsed:
        for args in model.get('desk_px', ()):
            if len(args) == 4:
                room, name, x, y = args
                yield (int(x), int(y)), (room.strip('"'), name.strip('"'))
            else:
                print(f'ERROR: unhandled desk "{args}"')

def call_placement_engine():
    models = clyngor.solve(('humans.lp', 'offices.lp', 'engine.lp'), options='--opt-mode=optN')
    for model in models.by_predicate.careful_parsing.int_not_parsed:
        yield model['place']


class MainWindow(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        # self.parent.geometry('{}x{}'.format(*WINDOW_SIZE))
        self.parent.title("Cathplace")
        self.desks = dict(load_desks())  # position: metadata (room, name)
        self.placement = {}  # desk position: human occupying the place
        self.humans = tuple(load_humans())
        self.__build_widgets()
        self._reset_action_state()
        self.models = iter(())  # iterable over models found by the solver

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
        self.paint()

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
        self.paint()


    def __build_widgets(self):
        raw_image = Image.open('plan-patio.png')
        raw_image = raw_image.resize(WINDOW_SIZE, PIL.Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(raw_image)
        self.image.rawdata = raw_image
        self.canvas = tk.Canvas(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-2>", self._reset_action_state)
        self.canvas.bind("<Button-3>", lambda e: self.on_canvas_click(e, True))
        self.paint()
        self.canvas.grid(row=0, column=0, rowspan=2, columnspan=3, sticky=tk.EW)

        frame = self.frame_desk = tk.LabelFrame(self, text='Desks/Rooms', padx=7, pady=7)
        self.but_state_place_desk = tk.Button(frame, text='Place desks', command=lambda: self.set_action_state(ActionState.PlaceDesk))
        Tooltip.on(self.but_state_place_desk, 'click on a place on the map to add a desk')
        self.but_state_place_desk.pack(fill=tk.X)
        self.but_state_remove_desk = tk.Button(frame, text='Remove desks', command=lambda: self.set_action_state(ActionState.RemoveDesk))
        Tooltip.on(self.but_state_remove_desk, 'click on an existing desk to delete it')
        self.but_state_remove_desk.pack(fill=tk.X)
        self.but_state_edit_desk = tk.Button(frame, text='Edit desks', command=lambda: self.set_action_state(ActionState.EditDesk))
        Tooltip.on(self.but_state_edit_desk, 'click on an existing desk to modify it')
        self.but_state_edit_desk.pack(fill=tk.X)
        self.but_export_desk = tk.Button(frame, text='Export desks', command=self.export_desks)
        Tooltip.on(self.but_export_desk, 'write export-offices.lp file with existing desks')
        self.but_export_desk.pack(fill=tk.X)
        self.frame_desk.grid(row=2, column=0, sticky=tk.NS)

        frame = self.frame_solutions = tk.LabelFrame(self, text='Solutions', padx=7, pady=7)
        self.but_build_solutions = tk.Button(frame, text='Build solutions', command=self.build_placement)
        Tooltip.on(self.but_build_solutions, 'compute possible (optimal) solutions, show the first one')
        self.but_build_solutions.pack(fill=tk.X)
        self.but_next_solution = tk.Button(frame, text='Show next solution', command=self.show_next_placement)
        Tooltip.on(self.but_next_solution, 'show next available solution, if any')
        self.but_next_solution.pack(fill=tk.X)
        self.but_jump_solution = tk.Button(frame, text='Pass solutions', command=self.jump_placements)
        Tooltip.on(self.but_jump_solution, f'Ignore {JUMP_QUANTITY} solutions, show the next one, if any')
        self.but_jump_solution.pack(fill=tk.X)
        self.but_write_solution = tk.Button(frame, text='Write solution', command=self.write_solution)
        Tooltip.on(self.but_write_solution, 'Write current solution in solution.lp')
        self.but_write_solution.pack(fill=tk.X)
        self.but_read_solution = tk.Button(frame, text='Read solution', command=self.load_solution)
        Tooltip.on(self.but_read_solution, 'Read solution in solution.lp, and show it')
        self.but_read_solution.pack(fill=tk.X)
        self.frame_solutions.grid(row=2, column=1, sticky=tk.NS)

        frame = self.frame_program = tk.LabelFrame(self, text='Program', padx=7, pady=7)
        self.but_quit = tk.Button(frame, text='Quit', command=self.build_placement)
        Tooltip.on(self.but_quit, 'Good bye !')
        self.but_quit.pack(fill=tk.X)
        self.frame_program.grid(row=2, column=2, sticky=tk.NS)


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
        dialog = DeskDialog(self, {'room name': room, 'desk name': name}, update, can_cancel=True)
        self.wait_window(dialog)  # window could modify self.server_config


def name_to_color(name:str) -> str:
    return 'red'  # sorry
def string_to_asp(string:str) -> str:
    string = string.strip()
    if not string:
        return '""'
    first = string[0]
    if first.isupper() or (first.isdigit() and not all(c.isdigit() for c in string)) or first == '_':
        return '"' + string + '"'
    else:
        return string


if __name__ == '__main__':
    root = tk.Tk()
    # Be sure to use a monospaced font
    default_font = font.nametofont('TkFixedFont')
    default_font.configure(size=11, weight='bold')
    root.option_add('*Font', default_font)
    MainWindow(root)
    root.mainloop()
