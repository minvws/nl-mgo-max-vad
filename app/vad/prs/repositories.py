from abc import ABC, abstractmethod
from typing import Dict, Any

import inject
from httpx import Client, HTTPStatusError, RequestError
from hashlib import sha256

from .schemas import GetVadPdnResponse


class PrsRepository(ABC):
    @abstractmethod
    def get_vad_pdn_by_bsn(self, bsn: str) -> str: ...  # pragma: no cover

    @abstractmethod
    def get_rid_by_vad_pdn(self, vad_pdn: str) -> str: ...  # pragma: no cover


class MockPrsRepository(PrsRepository):
    def get_vad_pdn_by_bsn(self, bsn: str) -> str:
        return self.__hashed(bsn)

    def get_rid_by_vad_pdn(self, vad_pdn: str) -> str:
        return self.__hashed(vad_pdn)

    @staticmethod
    def __hashed(data: str) -> str:
        return sha256(data.encode("utf-8")).hexdigest()


class ApiPrsRepository(PrsRepository):
    @inject.autoparams("client")
    def __init__(
        self, client: Client, repo_base_url: str, organisation_id: str
    ) -> None:
        self.__client = client
        self.__repo_base_url = repo_base_url
        self.__organisation_id = organisation_id

    def __handle_request(self, url: str) -> Dict[str, Any]:
        try:
            response = self.__client.post(url)
            response.raise_for_status()

            return response.json() or {}

        except HTTPStatusError as e:
            raise RuntimeError(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            ) from e
        except RequestError as e:
            raise RuntimeError(f"Request error occurred: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {str(e)}") from e

    def get_vad_pdn_by_bsn(self, bsn: str) -> str:
        vad_pdn_url = f"{self.__repo_base_url}/org_pseudonym?bsn={bsn}&org_id={self.__organisation_id}"
        vad_pdn_url_response = GetVadPdnResponse(**self.__handle_request(vad_pdn_url))

        return vad_pdn_url_response.pdn

    def get_rid_by_vad_pdn(self, vad_pdn: str) -> str:
        raise NotImplementedError()
