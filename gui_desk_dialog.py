"""Small dialog allowing user to specify desk metadata"""

import tkinter as tk
from tkinter import filedialog, simpledialog, font



class DeskDialog(tk.Toplevel):

    def __init__(self, parent, fields:dict, config_updater:callable, can_cancel=True):
        self.parent = parent
        super().__init__(parent)
        self.config_updater = config_updater
        self.__config_to_widgets(fields, can_cancel=can_cancel)

    def __config_to_widgets(self, fields:dict, can_cancel:bool):
        parent = self

        def build_field(field, value, rowid, widget_type=tk.Entry, holder_type=tk.StringVar, var_param='textvariable', type=str, **widget_args):
            label = tk.Label(parent, text=field)
            value_holder = holder_type(value=value)
            kwargs = {var_param: value_holder}  # py 3.4 compatibility
            kwargs.update(widget_args)
            box = widget_type(parent, **kwargs)
            label.grid(row=rowid, column=0)
            box.grid(row=rowid, column=1)
            return value_holder

        self.value_holders = {
            field: build_field(field, default, idx)
            for idx, (field, default) in enumerate(fields.items())
        }

        if can_cancel:
            # Place the ending buttons
            rowid = len(fields)
            tk.Button(parent, text='Cancel', command=self.destroy).grid(row=rowid, column=0)
            tk.Button(parent, text='Apply', command=self.apply).grid(row=rowid, column=1)
        else:  # Place the only apply button
            rowid = len(fields)
            tk.Button(parent, text='Apply', command=self.apply).grid(row=rowid, column=0, columnspan=2)


    def __widgets_to_config(self) -> dict:
        return {
            field: holder.get()
            for field, holder in self.value_holders.items()
        }

    def apply(self):
        self.config_updater(self.__widgets_to_config())
        self.destroy()
