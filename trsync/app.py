import collections
import configparser
import pathlib
import threading
import tkinter as tk
from tkinter import ttk
import typing
from trsync.client import Client
from tkinter import messagebox
from trsync.error import AuthenticationError, CommunicationError

from trsync.model import Instance, Workspace
from trsync.utils import DoubleLists, ScrollableFrame


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
        tab_frame = ttk.Frame(self._tabs_control)
        self._tabs_frames[
            instance.address if instance is not None else None
        ] = tab_frame
        self._tabs_control.add(
            tab_frame, text=instance.address if instance is not None else "Ajouter"
        )

        address_label = tk.Label(tab_frame, text="Adresse")
        address_label.grid(row=0, column=0)
        username_label = tk.Label(tab_frame, text="Username")
        username_label.grid(row=1, column=0)
        password_label = tk.Label(tab_frame, text="Mot de passe")
        password_label.grid(row=2, column=0)
        secure_label = tk.Label(tab_frame, text="Sécurisé")
        secure_label.grid(row=3, column=0)
        address_val = tk.StringVar(
            value=instance.address if instance is not None else ""
        )
        address_entry = tk.Entry(tab_frame, textvariable=address_val)
        address_entry.grid(row=0, column=1)
        username_val = tk.StringVar(
            value=instance.username if instance is not None else ""
        )
        username_entry = tk.Entry(tab_frame, textvariable=username_val)
        username_entry.grid(row=1, column=1)
        password_val = tk.StringVar(
            value=instance.password if instance is not None else ""
        )
        password_entry = tk.Entry(tab_frame, show="*", textvariable=password_val)
        password_entry.grid(row=2, column=1)
        secure_var = tk.IntVar(
            tab_frame, value=0 if instance is not None and instance.unsecure else 1
        )
        secure_entry = ttk.Checkbutton(
            tab_frame,
            variable=secure_var,
            onvalue=1,
            offvalue=0,
        )
        secure_entry.grid(
            row=3,
            column=1,
        )

        def validate():
            address = address_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            unsecure = secure_var.get() == 0

            if not address.strip() or not username.strip() or not password.strip():
                messagebox.showinfo(
                    "Informations incomplètes", "Veuillez saisir toute les informations"
                )

            try:
                Client.check_credentials(
                    Instance(
                        address=address,
                        username=username,
                        password=password,
                        unsecure=unsecure,
                        all_workspaces=[],
                        enabled_workspaces=[],
                    )
                )
            except CommunicationError:
                messagebox.showerror(
                    "Erreur de connection",
                    "Erreur dans l'adresse ou pas de connexion",
                )
            except AuthenticationError:
                messagebox.showerror(
                    "Erreur d'authentification",
                    "Erreur dans l'username ou le mot de passe",
                )

            if instance is not None:
                self._update_instance(address, username, password, unsecure)
            else:
                self._set_wait_message()
                self._add_instance(address, username, password, unsecure)
                self._destroy_wait_message()

        validate_button = ttk.Button(
            tab_frame,
            text="Enregistrer" if instance is not None else "Ajouter",
            command=validate,
        )
        validate_button.grid(row=4, column=0)

        if instance is not None:
            workspace_lists = DoubleLists(
                tab_frame,
                left_label="Espaces non synchronisés",
                right_label="Espaces synchronisés",
            )
            workspace_lists.grid(row=5, column=0)

            try:
                user_id = Client.check_credentials(instance)
                workspaces = Client(instance, user_id=user_id).get_workspaces()
                for workspace in workspaces:
                    if workspace.id in instance.enabled_workspaces:
                        workspace_lists.add_right(workspace.name)
                    else:
                        workspace_lists.add_left(workspace.name)

            except (CommunicationError, AuthenticationError) as exc:
                # FIXME : display error
                pass

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
