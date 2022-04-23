import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import typing
from trsync.client import Client
from trsync.error import AuthenticationError, CommunicationError

from trsync.model import Instance
from trsync.utils import DoubleLists


class TabFrame(ttk.Frame):
    def __init__(self, parent, app, instance: typing.Optional[Instance], **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)

        self._app = app
        self._instance = instance
        self._address_label = tk.Label(self, text="Adresse")
        self._address_label.grid(row=0, column=0)
        self._username_label = tk.Label(self, text="Username")
        self._username_label.grid(row=1, column=0)
        self._password_label = tk.Label(self, text="Mot de passe")
        self._password_label.grid(row=2, column=0)
        self._secure_label = tk.Label(self, text="Sécurisé")
        self._secure_label.grid(row=3, column=0)
        self._address_val = tk.StringVar(
            value=self._instance.address if self._instance is not None else ""
        )
        self._address_entry = tk.Entry(self, textvariable=self._address_val)
        self._address_entry.grid(row=0, column=1)
        self._username_val = tk.StringVar(
            value=self._instance.username if self._instance is not None else ""
        )
        self._username_entry = tk.Entry(self, textvariable=self._username_val)
        self._username_entry.grid(row=1, column=1)
        self._password_val = tk.StringVar(
            value=self._instance.password if self._instance is not None else ""
        )
        self._password_entry = tk.Entry(self, show="*", textvariable=self._password_val)
        self._password_entry.grid(row=2, column=1)
        self._secure_var = tk.IntVar(
            self,
            value=0 if self._instance is not None and self._instance.unsecure else 1,
        )
        self._secure_entry = ttk.Checkbutton(
            self,
            variable=self._secure_var,
            onvalue=1,
            offvalue=0,
        )
        self._secure_entry.grid(
            row=3,
            column=1,
        )

        def validate():
            address = self._address_entry.get()
            username = self._username_entry.get()
            password = self._password_entry.get()
            unsecure = self._secure_var.get() == 0

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

            if self._instance is not None:
                self._app._update_instance(address, username, password, unsecure)
            else:
                self._app._set_wait_message()
                self._app._add_instance(address, username, password, unsecure)
                self._app._destroy_wait_message()

        self._validate_button = ttk.Button(
            self,
            text="Enregistrer" if self._instance is not None else "Ajouter",
            command=validate,
        )
        self._validate_button.grid(row=4, column=0)

        if self._instance is not None:
            self._workspace_lists = DoubleLists(
                self,
                left_label="Espaces non synchronisés",
                right_label="Espaces synchronisés",
            )
            self._workspace_lists.grid(row=5, column=0)

            try:
                user_id = Client.check_credentials(self._instance)
                workspaces = Client(self._instance, user_id=user_id).get_workspaces()
                for workspace in workspaces:
                    if workspace.id in self._instance.enabled_workspaces:
                        self._workspace_lists.add_right(workspace.name)
                    else:
                        self._workspace_lists.add_left(workspace.name)

            except (CommunicationError, AuthenticationError) as exc:
                # FIXME : display error
                pass