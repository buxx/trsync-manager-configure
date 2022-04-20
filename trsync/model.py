import dataclasses


@dataclasses.dataclass
class Instance:
    address: str
    username: str
    password: str
