import configparser
import pathlib
import threading
import tkinter as tk
import typing
from trsync.client import Client

from trsync.model import Instance, Workspace


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
        threading.Thread.start(self._update_from_config())

        # window stuffs
        self.entrythingy = tk.Entry()
        self.entrythingy.pack()

        # Create the application variable.
        self.contents = tk.StringVar()
        # Set it to some value.
        self.contents.set("this is a variable")
        # Tell the entry widget to watch this variable.
        self.entrythingy["textvariable"] = self.contents

        # Define a callback for when the user hits return.
        # It prints the current value of the variable.
        self.entrythingy.bind("<Key-Return>", self.print_contents)

    def print_contents(self, event):
        print("Hi. The current entry content is:", self.contents.get())

    def _update_from_config(self) -> None:
        for instance_name in [
            instance_name.strip()
            for instance_name in self._config.get(
                "server", "instances", fallback=""
            ).split(",")
        ]:
            instance = self._read_config_instance(instance_name)
            self._instances.append(instance)

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
