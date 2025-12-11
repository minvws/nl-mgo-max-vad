import json
from abc import ABC, abstractmethod
from os import W_OK, access, path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence

from jwcrypto.jwk import JWK
from max_core.services.client_repository import ClientMapping, ClientRepository

from app.cbp.models import CbpClient


class CbpClientRepository(ClientRepository, ABC):
    @abstractmethod
    def get_by_id(self, client_id: str) -> CbpClient: ...

    @abstractmethod
    def find_by_id(self, client_id: str) -> Optional[CbpClient]: ...

    @abstractmethod
    def get_all(self) -> Sequence[CbpClient]: ...

    @abstractmethod
    def update(self, clients: Sequence[CbpClient]) -> None: ...


class FilesystemCbpClientRepository(CbpClientRepository):
    def __init__(self, filepath: str) -> None:
        self.__filepath = filepath
        self.__clients: Mapping[str, CbpClient] = {}
        self.__clients_as_mapping: MutableMapping[str, ClientMapping] = {}

        file_dir, _ = path.split(self.__filepath)
        if not path.isdir(file_dir) or not access(file_dir, W_OK):
            raise ValueError(f"Cannot write to directory: {file_dir}")

        if path.isfile(self.__filepath) and path.getsize(self.__filepath) > 0:
            self.__update_clients(
                {
                    client_data["id"]: CbpClient(**client_data)
                    for client_data in self.__load_clients_from_file()
                }
            )

    def __load_clients_from_file(self) -> List[Dict[str, Any]]:
        with open(self.__filepath, "r", encoding="utf-8") as file:
            clients: List[Dict[str, Any]] = json.load(file)

        for client in clients:
            k = client["public_key"]
            client["public_key"] = JWK(
                kty=k["kty"], n=k["n"], e=k["e"], kid=k.get("kid")
            )

        return clients

    def __write_clients_to_file(self, clients: Sequence[CbpClient]) -> None:
        with open(self.__filepath, "w", encoding="utf-8") as file:
            json.dump(
                [client.model_dump() for client in clients],
                file,
                ensure_ascii=False,
                indent=2,
            )

    def get_by_id(self, client_id: str) -> CbpClient:
        return self.__clients[client_id]

    def find_by_id(self, client_id: str) -> Optional[CbpClient]:
        return self.__clients.get(client_id)

    def get_all(self) -> Sequence[CbpClient]:
        return list(self.__clients.values())

    def update(self, clients: Sequence[CbpClient]) -> None:
        self.__write_clients_to_file(clients)
        self.__update_clients({client.id: client for client in clients})

    def __update_clients(self, clients: Mapping[str, CbpClient]) -> None:
        self.__clients = clients
        # Sync the __clients_as_mapping attribute with the updated __clients attribute.
        # This attribute is added (temporarily) to accommodate the `Provider` from PyOP, that only accepts a dictionary.
        # Important: update the existing dictionary instead of reassigning it, to ensure the reference passed to PyOP is kept intact.
        self.__clients_as_mapping.clear()
        self.__clients_as_mapping.update(
            {client.id: client.model_dump() for client in self.__clients.values()}
        )

    @property
    def clients_as_mapping(self) -> MutableMapping[str, ClientMapping]:
        return self.__clients_as_mapping
