from json import dump, dumps
from pathlib import Path
from typing import List
from faker import Faker
from pytest import fixture, raises

from app.cbp.models import CbpClient
from app.cbp.repositories import (
    FilesystemCbpClientRepository,
)

from .fixtures import create_cbp_client


class TestFilesystemCbpClientRepository:
    @fixture
    def filepath(self, tmp_path: Path) -> Path:
        return tmp_path.joinpath("clients.json")

    @fixture
    def sut(self, filepath: Path) -> FilesystemCbpClientRepository:
        return FilesystemCbpClientRepository(str(filepath))

    def _set_clients_on_repository(self, sut, clients: List[CbpClient]):
        sut._FilesystemCbpClientRepository__clients = {
            client.id: client for client in clients
        }

    def test_get_by_id_raises_if_client_not_found(
        self, sut: FilesystemCbpClientRepository, faker: Faker
    ) -> None:
        id = faker.uuid4()

        with raises(KeyError, match=f"'{id}'"):
            sut.get_by_id(id)

    def test_get_by_id_returns_client_if_found(
        self, sut: FilesystemCbpClientRepository, faker: Faker
    ) -> None:
        id = faker.uuid4()
        client = create_cbp_client(id=id)
        self._set_clients_on_repository(sut, [client])

        assert sut.get_by_id(id) == client

    def test_find_by_id_returns_none_if_client_not_found(
        self, sut: FilesystemCbpClientRepository, faker: Faker
    ) -> None:
        assert sut.find_by_id(faker.uuid4()) is None

    def test_find_by_id_returns_client_if_found(
        self, sut: FilesystemCbpClientRepository, faker: Faker
    ) -> None:
        id = faker.uuid4()
        client = create_cbp_client(id=id)
        self._set_clients_on_repository(sut, [client])

        assert sut.find_by_id(id) == client

    def test_get_all_returns_all_clients(
        self, sut: FilesystemCbpClientRepository, faker: Faker
    ) -> None:
        client_a = create_cbp_client(id=faker.uuid4())
        client_b = create_cbp_client(id=faker.uuid4())
        self._set_clients_on_repository(sut, [client_a, client_b])

        result = sut.get_all()

        assert len(result) == 2
        assert client_a in result
        assert client_b in result

    def test_init_loads_clients_if_valid_file(
        self, filepath: Path, faker: Faker
    ) -> None:
        client = create_cbp_client(id=faker.uuid4())
        with open(filepath, mode="w", encoding="utf-8") as tmp_file:
            dump(
                [client],
                tmp_file,
                ensure_ascii=False,
                indent=2,
                default=lambda client: client.model_dump(),
            )
        sut = FilesystemCbpClientRepository(str(filepath))

        result = sut.get_all()

        assert len(result) == 1

    def test_init_does_not_load_clients_if_file_not_found(self, filepath: Path) -> None:
        sut = FilesystemCbpClientRepository(str(filepath))

        result = sut.get_all()

        assert len(result) == 0

    def test_init_does_not_load_clients_if_file_is_empty(self, filepath: Path) -> None:
        with open(filepath, mode="w", encoding="utf-8") as tmp_file:
            tmp_file.write("")
        sut = FilesystemCbpClientRepository(str(filepath))

        result = sut.get_all()

        assert len(result) == 0

    def test_init_raises_if_filepath_directory_is_not_writable(self) -> None:
        with raises(ValueError, match="Cannot write to directory"):
            FilesystemCbpClientRepository("/root/clients.json")

    def test_update_overwrites_class_property(
        self, sut: FilesystemCbpClientRepository, faker: Faker
    ) -> None:
        id_a = faker.uuid4()
        id_b = faker.uuid4()
        client_a = create_cbp_client(id=id_a)
        client_b = create_cbp_client(id=id_b)
        self._set_clients_on_repository(sut, [client_a])

        sut.update([client_b])

        assert sut._FilesystemCbpClientRepository__clients == {id_b: client_b}

    def test_update_overwrites_cache_file(self, filepath: Path, faker: Faker) -> None:
        id_a = faker.uuid4()
        id_b = faker.uuid4()
        client_a = create_cbp_client(id=id_a)
        client_b = create_cbp_client(id=id_b)
        with open(filepath, mode="w", encoding="utf-8") as tmp_file:
            dump(
                [client_a],
                tmp_file,
                ensure_ascii=False,
                indent=2,
                default=lambda client: client.model_dump(),
            )
        sut = FilesystemCbpClientRepository(str(filepath))

        sut.update([client_b])

        with open(filepath, mode="r", encoding="utf-8") as tmp_file:
            assert tmp_file.read() == dumps(
                [client_b],
                ensure_ascii=False,
                indent=2,
                default=lambda client: client.model_dump(),
            )
