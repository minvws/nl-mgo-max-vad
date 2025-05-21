from pydantic_core import ValidationError
from pytest import raises
from faker.proxy import Faker
from hashlib import sha256
from httpx import Client, HTTPStatusError, RequestError
from pytest_mock import MockerFixture

from app.vad.prs.repositories import ApiPrsRepository, MockPrsRepository


class TestMockPrsRepository:
    def test_get_vad_pdn_by_bsn_returns_mock_pdn(self, faker: Faker) -> None:
        repository: MockPrsRepository = MockPrsRepository()
        bsn: str = faker.numerify(text="#########")

        pdn: str = repository.get_vad_pdn_by_bsn(bsn)

        assert pdn == sha256(bsn.encode("utf-8")).hexdigest()

    def test_get_rid_by_vad_pdn_returns_mock_rid(self, faker: Faker) -> None:
        repository: MockPrsRepository = MockPrsRepository()
        vad_pdn: str = faker.sha256(raw_output=False)

        rid: str = repository.get_rid_by_vad_pdn(vad_pdn)

        assert rid == sha256(vad_pdn.encode("utf-8")).hexdigest()


class TestApiPrsRepository:
    def test_get_vad_pdn_by_bsn_returns_pdn(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        pass

    def test_get_vad_pdn_by_bsn_handles_http_status_error(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_client = mocker.Mock(spec=Client)
        error_code = faker.numerify("4##")
        error_text = faker.sentence()
        repository: ApiPrsRepository = ApiPrsRepository(
            mock_client, faker.uri_path(), faker.uuid4()
        )

        mock_client.post.side_effect = HTTPStatusError(
            faker.sentence(),
            request=mocker.Mock(),
            response=mocker.Mock(status_code=error_code, text=error_text),
        )

        with raises(
            RuntimeError, match=f"HTTP error occurred: {error_code} - {error_text}"
        ):
            repository.get_vad_pdn_by_bsn(faker.numerify(text="#########"))

    def test_get_vad_pdn_by_bsn_handles_request_error(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_client = mocker.Mock(spec=Client)
        error_text = faker.sentence()
        repository: ApiPrsRepository = ApiPrsRepository(
            mock_client, faker.uri_path(), faker.uuid4()
        )

        mock_client.post.side_effect = RequestError(error_text)

        with raises(RuntimeError, match=f"Request error occurred: {error_text}"):
            repository.get_vad_pdn_by_bsn(faker.numerify(text="#########"))

    def test_get_vad_pdn_by_bsn_handles_generic_exception(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_client = mocker.Mock(spec=Client)
        error_text = faker.sentence()
        repository: ApiPrsRepository = ApiPrsRepository(
            mock_client, faker.uri_path(), faker.uuid4()
        )

        mock_client.post.side_effect = Exception(error_text)

        with raises(RuntimeError, match=f"An unexpected error occurred: {error_text}"):
            repository.get_vad_pdn_by_bsn(faker.numerify(text="#########"))

    def test_get_vad_pdn_by_bsn_handles_empty_response(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_client = mocker.Mock(spec=Client)
        repository: ApiPrsRepository = ApiPrsRepository(
            mock_client, faker.uri_path(), faker.uuid4()
        )

        mock_client.post.return_value.json.return_value = None

        with raises(ValidationError, match=r"pdn"):
            repository.get_vad_pdn_by_bsn(faker.numerify(text="#########"))

    def test_get_vad_pdn_by_bsn_handles_invalid_response_json_structure(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_client = mocker.Mock(spec=Client)
        repository: ApiPrsRepository = ApiPrsRepository(
            mock_client, faker.uri_path(), faker.uuid4()
        )

        mock_client.post.return_value.json.return_value = {"invalid": "structure"}

        with raises(ValidationError, match=r"pdn"):
            repository.get_vad_pdn_by_bsn(faker.numerify(text="#########"))

    def test_get_vad_pdn_by_bsn_constructs_prs_endpoint(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_client = mocker.Mock(spec=Client)
        repo_base_url = faker.uri_path()
        organisation_id = faker.uuid4()
        bsn = faker.numerify(text="#########")
        repository: ApiPrsRepository = ApiPrsRepository(
            mock_client, repo_base_url, organisation_id
        )

        mock_client.post.return_value.json.return_value = {"pdn": faker.sha256()}

        repository.get_vad_pdn_by_bsn(bsn)

        mock_client.post.assert_called_once_with(
            f"{repo_base_url}/org_pseudonym?bsn={bsn}&org_id={organisation_id}"
        )

    def test_get_rid_by_vad_pdn_not_implemented(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        repository: ApiPrsRepository = ApiPrsRepository(
            mocker.Mock(spec=Client), faker.uri_path(), faker.uuid4()
        )

        with raises(NotImplementedError):
            repository.get_rid_by_vad_pdn(faker.sha256(raw_output=False))
