import collections
import configparser
import pathlib
import threading
import tkinter as tk
from tkinter import ttk
import typing
from trsync.client import Client
from tkinter import messagebox

from trsync.model import Instance, Workspace
from trsync.tab import TabFrame


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()

        # trsync stuffs
        self._config_file_path = pathlib.Path.home() / ".trsync.conf"
        self._config_track_file_path = pathlib.Path.home() / ".trsync.conf.track"
        self._config = configparser.ConfigParser()
        self._config.read(self._config_file_path)
        self._instances: typing.List[Instance] = []

        # window stuffs
        self._tabs_control = ttk.Notebook(self)
        self._tabs_frames: typing.Dict[typing.Optional[str], ttk.Frame] = {}
        self._set_wait_message()

        # First tab is for add a new instance
        new_tab_frame = self._build_tab_frame(None)

        threading.Thread(target=self._update_from_config).start()

    def _set_wait_message(self) -> None:
        self._wait_message = tk.Label(self, text="Récupération des informations ...")
        self._wait_message.pack()

    def _destroy_wait_message(self) -> None:
        self._wait_message.destroy()

    def _update_from_config(self) -> None:
        # FIXME : message label en cas d'erreur
        for instance_name in [
            instance_name.strip()
            for instance_name in self._config.get(
                "server", "instances", fallback=""
            ).split(",")
        ]:
            instance = self._read_config_instance(instance_name)
            self._instances.append(instance)

            try:
                tab_frame = self._tabs_frames[instance.address]
            except KeyError:
                tab_frame = self._build_tab_frame(instance)

        self._destroy_wait_message()
        self._tabs_control.pack(expand=1, fill="both")
        # tab_frame.pack()

    def _read_config_instance(self, instance_name: str) -> None:
        section_name = f"instance.{instance_name}"
        address = self._config[section_name]["address"]
        username = self._config[section_name]["username"]
        password = self._config[section_name]["password"]
        unsecure = self._config[section_name]["unsecure"]
        workspaces_ids = [
            int(workspace_id.strip())
            for workspace_id in self._config[section_name]["workspaces_ids"].split(",")
        ]
        instance = Instance(
            address=address,
            username=username,
            password=password,
            unsecure=unsecure,
            enabled_workspaces=workspaces_ids,
            all_workspaces=[],
        )
        all_workspaces = self._get_workspaces(instance)
        instance.all_workspaces = all_workspaces
        return instance

    def _get_workspaces(self, instance: Instance) -> typing.List[Workspace]:
        user_id = Client.check_credentials(instance)
        return Client(instance, user_id=user_id).get_workspaces()

    def _build_tab_frame(self, instance: typing.Optional[Instance]) -> ttk.Frame:
        tab_frame = TabFrame(self._tabs_control, self, instance)
        self._tabs_frames[
            instance.address if instance is not None else None
        ] = tab_frame
        self._tabs_control.add(
            tab_frame, text=instance.address if instance is not None else "Ajouter"
        )
        return tab_frame

    def _add_instance(
        self, address: str, username: str, password: str, unsecure: bool
    ) -> None:
        instance = Instance(
            address=address,
            username=username,
            password=password,
            unsecure=unsecure,
            all_workspaces=[],
            enabled_workspaces=[],
        )
        self._instances.append(instance)
        self._build_tab_frame(instance)
