import dataclasses
import typing


@dataclasses.dataclass
class Workspace:
    id: str
    name: str


@dataclasses.dataclass
class Instance:
    address: str
    username: str
    password: str
    unsecure: bool
    all_workspaces: typing.List[Workspace]
    enabled_workspaces: typing.List[int]

    def url(self) -> str:
        scheme = "https" if not self.unsecure else "http"
        return f"{scheme}://{self.address}"
