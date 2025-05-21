from uuid import UUID, uuid4

from faker.proxy import Faker
from pydantic_core import ValidationError
from pytest import mark, raises
from pytest_mock import MockerFixture

from app.models.auth_session import AuthSession
from app.models.authentication_context import AuthenticationContext
from app.models.saml.artifact_response import ArtifactResponse
from app.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from app.storage.auth_session_cache import AuthSessionCache
from app.vad.brp.schemas import NameDTO, PersonDTO
from app.vad.brp.service import BrpService
from app.vad.prs.repositories import PrsRepository
from app.vad.schemas import UserInfoDTO
from app.vad.services import UserinfoProvider, VadUserinfoService


class TestUserinfoProvider:
    @mark.parametrize("has_auth_session_id", [False, True])
    def test_exchange_bsn_with_and_without_auth_session_id(
        self, mocker: MockerFixture, faker: Faker, has_auth_session_id: bool
    ) -> None:
        mock_prs_repository = mocker.Mock(spec=PrsRepository)
        mock_brp_service = mocker.Mock(spec=BrpService)
        mock_auth_session_cache = mocker.Mock(spec=AuthSessionCache)
        mock_auth_session_encrypter = mocker.Mock(spec=AuthSessionEncrypter)
        mock_person = mocker.Mock(spec=PersonDTO)
        person_dict = {"person_dump"}
        mock_person.model_dump.return_value = person_dict

        bsn = faker.numerify(text="#########")
        auth_session_id = faker.uuid4(cast_to=None) if has_auth_session_id else None
        vad_pdn = faker.sha256()
        rid = faker.sha256()
        encrypted_auth_session_id = faker.pystr()

        userinfo_provider = UserinfoProvider(
            mock_prs_repository,
            mock_brp_service,
            mock_auth_session_cache,
            mock_auth_session_encrypter,
        )

        mock_prs_repository.get_vad_pdn_by_bsn.return_value = vad_pdn
        mock_prs_repository.get_rid_by_vad_pdn.return_value = rid
        mock_brp_service.get_person_info.return_value = mock_person
        mock_auth_session_encrypter.encrypt.return_value = encrypted_auth_session_id

        userinfo_dto = userinfo_provider.exchange_bsn(
            bsn=bsn,
            auth_session_id=(auth_session_id if has_auth_session_id else None),
        )

        assert userinfo_dto.rid == rid
        assert userinfo_dto.person == mock_person

        mock_prs_repository.get_vad_pdn_by_bsn.assert_called_once_with(bsn)
        mock_prs_repository.get_rid_by_vad_pdn.assert_called_once_with(vad_pdn)
        mock_brp_service.get_person_info.assert_called_once_with(bsn)

        if has_auth_session_id:
            assert userinfo_dto.sub == encrypted_auth_session_id

            mock_auth_session_cache.set.assert_called_once_with(
                str(auth_session_id),
                {
                    "vad_pdn": vad_pdn,
                    "person": person_dict,
                },
            )
            mock_auth_session_encrypter.encrypt.assert_called_once_with(auth_session_id)
        else:
            assert userinfo_dto.sub == ""

            mock_auth_session_cache.set.assert_not_called()
            mock_auth_session_encrypter.encrypt.assert_not_called()

    def test_exchange_session_with_valid_auth_session(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_prs_repository = mocker.Mock(spec=PrsRepository)
        mock_auth_session_cache = mocker.Mock(spec=AuthSessionCache)
        mock_auth_session_encrypter = mocker.Mock(spec=AuthSessionEncrypter)
        auth_session_id = uuid4()
        auth_session = AuthSession(auth_session_id)
        mock_person = mocker.Mock(spec=PersonDTO)
        vad_pdn = faker.sha256()
        rid = faker.sha256()
        encrypted_auth_session_id = faker.pystr()

        userinfo_provider = UserinfoProvider(
            mock_prs_repository,
            mocker.Mock(spec=BrpService),
            mock_auth_session_cache,
            mock_auth_session_encrypter,
        )

        mock_auth_session_cache.get.return_value = {
            "vad_pdn": vad_pdn,
            "person": mock_person,
        }
        mock_prs_repository.get_rid_by_vad_pdn.return_value = rid
        mock_auth_session_encrypter.encrypt.return_value = encrypted_auth_session_id

        userinfo_dto = userinfo_provider.exchange_session(auth_session)

        assert userinfo_dto.rid == rid
        assert userinfo_dto.person == mock_person
        assert userinfo_dto.sub == encrypted_auth_session_id

        mock_auth_session_cache.get.assert_called_once_with(str(auth_session_id))
        mock_prs_repository.get_rid_by_vad_pdn.assert_called_once_with(vad_pdn)
        mock_auth_session_encrypter.encrypt.assert_called_once_with(auth_session_id)

    def test_exchange_session_with_invalid_cache_data(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_prs_repository = mocker.Mock(spec=PrsRepository)
        mock_auth_session_cache = mocker.Mock(spec=AuthSessionCache)
        mock_auth_session_encrypter = mocker.Mock(spec=AuthSessionEncrypter)
        auth_session_id = str(faker.uuid4())
        auth_session = AuthSession(UUID(auth_session_id))

        userinfo_provider = UserinfoProvider(
            mock_prs_repository,
            mocker.Mock(spec=BrpService),
            mock_auth_session_cache,
            mock_auth_session_encrypter,
        )

        mock_auth_session_cache.get.return_value = {}

        with raises(ValidationError) as ei:
            userinfo_provider.exchange_session(auth_session)

        assert ei.value.error_count() == 2
        assert all(s in ei.exconly().split("\n") for s in ["vad_pdn", "person"])

        mock_prs_repository.get_rid_by_vad_pdn.assert_not_called()
        mock_auth_session_encrypter.encrypt.assert_not_called()


class TestVadUserinfoService:
    def test_request_userinfo_for_digid_artifact(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_userinfo_provider = mocker.Mock(spec=UserinfoProvider)
        mock_artifact_response = mocker.Mock(spec=ArtifactResponse)
        mock_userinfo_dto = mocker.Mock(spec=UserInfoDTO)
        bsn = faker.numerify(text="#########")
        auth_session_id = uuid4()

        vad_userinfo_service = VadUserinfoService(mock_userinfo_provider)

        mock_artifact_response.get_bsn.return_value = bsn
        mock_userinfo_provider.exchange_bsn.return_value = mock_userinfo_dto
        mock_userinfo_dto.model_dump.return_value = {"foo": "bar"}

        userinfo = vad_userinfo_service.request_userinfo_for_digid_artifact(
            mocker.Mock(spec=AuthenticationContext),
            mock_artifact_response,
            str(faker.uuid4()),
            auth_session_id,
        )

        assert userinfo == '{"foo": "bar"}'
        mock_artifact_response.get_bsn.assert_called_once_with(
            authorization_by_proxy=True
        )
        mock_userinfo_provider.exchange_bsn.assert_called_once_with(
            bsn, auth_session_id
        )
        mock_userinfo_dto.model_dump.assert_called_once()

    def test_request_userinfo_for_session_returns_userinfo(
        self, mocker: MockerFixture, faker: Faker
    ) -> None:
        mock_userinfo_provider = mocker.Mock(spec=UserinfoProvider)
        rid = faker.sha256()
        age = faker.random_int(min=18, max=99)
        person = PersonDTO(
            age=age,
            name=NameDTO(last_name=faker.last_name()),
        )
        auth_session_id = uuid4()
        vad_userinfo_service = VadUserinfoService(
            userinfo_provider=mock_userinfo_provider
        )

        mock_userinfo_provider.exchange_session.return_value = UserInfoDTO(
            rid=rid, person=person, sub=str(auth_session_id)
        )

        auth_session = AuthSession(auth_session_id)
        user_info_json = vad_userinfo_service.request_userinfo_for_session(auth_session)

        assert (
            user_info_json
            == '{"rid": "%s", "person": {"age": %d, "name": {"first_name": null, "prefix": null, "last_name": "%s", "initials": null, "full_name": null}}, "sub": "%s"}'
            % (rid, age, person.name.last_name, str(auth_session_id))
        )
