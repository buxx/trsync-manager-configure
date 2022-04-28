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

        threading.Thread(target=self._load_from_config).start()

    def _set_wait_message(self) -> None:
        self._wait_message = tk.Label(self, text="Récupération des informations ...")
        self._wait_message.pack()

    def _destroy_wait_message(self) -> None:
        self._wait_message.destroy()

    def _load_from_config(self) -> None:
        # FIXME : message label en cas d'erreur
        for instance_name in [
            instance_name.strip()
            for instance_name in self._config.get(
                "server", "instances", fallback=""
            ).split(",")
        ]:
            instance = self._read_config_instance(instance_name)
            self._instances.append(instance)

            # TODO : think about on instance by thread (to avoid blocking)
            try:
                tab_frame = self._tabs_frames[instance.address]
            except KeyError:
                tab_frame = self._build_tab_frame(instance)

        self._destroy_wait_message()
        self._tabs_control.pack(expand=1, fill="both")

    def _save_to_config(self) -> None:
        local_folder = self._config.get("server", "local_folder")
        trsync_bin_path = self._config.get("server", "trsync_bin_path")
        self._config.clear()
        self._config.add_section("server")
        self._config.set(
            "server",
            "instances",
            ",".join(instance.address for instance in self._instances),
        )
        self._config.set("server", "local_folder", local_folder)
        self._config.set("server", "trsync_bin_path", trsync_bin_path)
        for instance in self._instances:
            section_name = f"instance.{instance.address}"
            self._config.add_section(section_name)
            self._config.set(section_name, "address", instance.address)
            self._config.set(section_name, "username", instance.username)
            self._config.set(section_name, "password", instance.password)
            self._config.set(section_name, "unsecure", str(instance.unsecure))
            self._config.set(
                section_name,
                "workspaces_ids",
                ",".join(
                    str(workspace_id) for workspace_id in instance.enabled_workspaces
                ),
            )
        with self._config_file_path.open("w") as config_file:
            self._config.write(config_file)

        with self._config_track_file_path.open("w") as config_track_file:
            config_track_file.write("")

    def _read_config_instance(self, instance_name: str) -> None:
        section_name = f"instance.{instance_name}"
        address = self._config[section_name]["address"]
        username = self._config[section_name]["username"]
        password = self._config[section_name]["password"]
        unsecure = self._config.getboolean(section_name, "unsecure")
        workspaces_ids = [
            int(workspace_id.strip())
            for workspace_id in self._config[section_name]["workspaces_ids"].split(",")
            if workspace_id.strip()
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
        self._save_to_config()

    def _update_instance(
        self,
        instance: Instance,
        address: str,
        username: str,
        password: str,
        unsecure: bool,
    ) -> None:
        instance.address = address
        instance.username = username
        instance.password = password
        instance.unsecure = unsecure
        self._save_to_config()

    def _delete_instance(self, instance: Instance) -> None:
        self._instances.remove(instance)
        self._tabs_frames[instance.address].destroy()
        self._save_to_config()
