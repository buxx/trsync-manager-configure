import tkinter as tk
from tkinter import ttk
import typing


class DoubleLists(tk.Frame):
    def __init__(self, parent, left_label: str, right_label: str, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)

        self._left_label = tk.Label(self, text=left_label)
        self._left_label.grid(row=0, column=0)
        self._left_listbox = tk.Listbox(self)
        self._left_listbox.grid(row=1, column=0)
        self._left_listbox.bind("<<ListboxSelect>>", self._on_left_selected)
        self._left_values: typing.List[str] = []

        self._right_label = tk.Label(self, text=right_label)
        self._right_label.grid(row=0, column=1)
        self._right_listbox = tk.Listbox(self)
        self._right_listbox.grid(row=1, column=1)
        self._right_listbox.bind("<<ListboxSelect>>", self._on_right_selected)
        self._right_values: typing.List[str] = []

    def add_right(self, item: str) -> None:
        self._right_listbox.insert(tk.END, item)
        self._right_values.append(item)

    def add_left(self, item: str) -> None:
        self._left_listbox.insert(tk.END, item)
        self._left_values.append(item)

    def get_right_values(self) -> typing.List[str]:
        return self._right_values[:]

    def get_left_values(self) -> typing.List[str]:
        return self._left_values[:]

    def _on_left_selected(self, event) -> None:
        widget = event.widget
        selection = widget.curselection()
        if selection:
            selected_index = int(selection[0])
            selected_value = widget.get(selected_index)
            self.add_right(selected_value)
            self._left_listbox.delete(selected_index)
            self._left_values.remove(selected_value)

    def _on_right_selected(self, event) -> None:
        widget = event.widget
        selection = widget.curselection()
        if selection:
            selected_index = int(selection[0])
            selected_value = widget.get(selected_index)
            self.add_left(selected_value)
            self._right_listbox.delete(selected_index)
            self._right_values.remove(selected_value)


def normalize_workspace_name(name: str) -> str:
    return name.encode("ascii", "ignore").decode()
