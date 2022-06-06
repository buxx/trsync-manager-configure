import os
import configparser
import pathlib
import threading
import tkinter as tk
from tkinter import ttk
import typing

import requests
from trsync.client import Client
from tkinter import messagebox
from trsync.error import AuthenticationError, FailToGetPassword, FailToSetPassword


from trsync.model import Instance, Workspace
from trsync.tab import ConfigFrame, TabFrame


class App(tk.Frame):
    def __init__(
        self,
        master,
        password_setter_port: typing.Optional[int] = None,
        password_setter_token: typing.Optional[str] = None,
    ):
        super().__init__(master)
        self._password_setter_port = password_setter_port
        self._password_setter_token = password_setter_token
        self.pack(expand=True, fill=tk.BOTH)

        # trsync stuffs
        if os.name == "nt":
            self._config_file_path = (
                pathlib.Path.home() / "AppData" / "Local" / "trsync.conf"
            )
            self._config_track_file_path = (
                pathlib.Path.home() / "AppData" / "Local" / "trsync.conf.track"
            )
        else:
            self._config_file_path = pathlib.Path.home() / ".trsync.conf"
            self._config_track_file_path = pathlib.Path.home() / ".trsync.conf.track"
        self._config = configparser.ConfigParser()
        self._config.read(self._config_file_path)
        self._instances: typing.List[Instance] = []

        # window stuffs
        self._tabs_control = ttk.Notebook(self)
        self._tabs_frames: typing.Dict[typing.Optional[str], ttk.Frame] = {}
        self._set_wait_message()

        self._build_config_frame()
        self._build_tab_frame(None)

        threading.Thread(target=self._load_from_config).start()

    def _set_wait_message(self) -> None:
        self._wait_message = tk.Label(self, text="Récupération des informations ...")
        self._wait_message.pack()

    def _destroy_wait_message(self) -> None:
        self._wait_message.destroy()

    def _load_from_config(self) -> None:
        print(f"Load config from {self._config_file_path}")
        # FIXME : message label en cas d'erreur
        for instance_name in [
            instance_name.strip()
            for instance_name in self._config.get(
                "server", "instances", fallback=""
            ).split(",")
            if instance_name
        ]:
            print(f"Read instance {instance_name}")
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
        print(f"Save config into {self._config_file_path}")
        local_folder = self._config.get("server", "local_folder")
        if not local_folder:
            messagebox.showerror(
                "Erreur de configuration",
                "Veuillez choisir un dossier local dans la configuration",
            )
            return
        self._config.set(
            "server",
            "instances",
            ",".join(instance.address for instance in self._instances),
        )
        self._config.set("server", "local_folder", local_folder)
        for instance in self._instances:
            section_name = f"instance.{instance.address}"
            if not self._config.has_section(section_name):
                self._config.add_section(section_name)
            self._config.set(section_name, "address", instance.address)
            self._config.set(section_name, "username", instance.username)
            if self._password_setter_port is not None:
                try:
                    self._set_password(instance.address, instance.password)
                except FailToSetPassword as exc:
                    messagebox.showerror(
                        "Erreur d'enregistrement",
                        (
                            "Impossible d'enregistrer le mot de "
                            f"passe pour l'instance '{instance.address}' : "
                            f"'{exc}'"
                        ),
                    )
                    continue
            else:
                self._config.set(section_name, "password", instance.password)
            self._config.set(section_name, "unsecure", str(instance.unsecure))
            print("Workspaces ids : ", instance.enabled_workspaces)
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
        try:
            password = self._get_password(instance_name)
        except FailToGetPassword as exc:
            print(f"Fail to get password for instance '{exc}': ", exc)
            password = ""
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
        try:
            all_workspaces = self._get_workspaces(instance)
            instance.all_workspaces = all_workspaces
        except AuthenticationError as exc:
            instance.all_workspaces = []
            messagebox.showerror(
                "Erreur de configuration",
                f"Une erreur est survenue lors de l'authentification auprès de {address}",
            )

        return instance

    def _get_workspaces(self, instance: Instance) -> typing.List[Workspace]:
        user_id = Client.check_credentials(instance)
        return Client(instance, user_id=user_id).get_workspaces()

    def _build_config_frame(self) -> None:
        config_frame = ConfigFrame(self._tabs_control, self)
        self._tabs_control.add(config_frame, text="Configuration")

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
        # TODO : errors can happens
        all_workspaces = self._get_workspaces(instance)
        instance.all_workspaces = all_workspaces
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

    def _set_password(self, instance_name: str, password: str) -> None:
        assert self._password_setter_port is not None
        try:
            response = requests.post(
                f"http://127.0.0.1:{self._password_setter_port}/password/{instance_name}",
                data=password,
                headers={"X-Auth-Token": self._password_setter_token},
            )
            if response.status_code != 201:
                raise FailToSetPassword(
                    f"Unexpected response status code '{response.status_code}'"
                )
        except Exception as exc:
            raise FailToSetPassword(str(exc))

    def _get_password(self, instance_name: str) -> str:
        try:
            response = requests.get(
                f"http://127.0.0.1:{self._password_setter_port}/password/{instance_name}",
                headers={"X-Auth-Token": self._password_setter_token},
            )
            if response.status_code != 200:
                raise FailToSetPassword(
                    f"Unexpected response status code '{response.status_code}'"
                )
            return response.text
        except Exception as exc:
            raise FailToGetPassword(str(exc))
