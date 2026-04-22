from hashlib import sha256
from typing import Any, Dict
import uuid

import pytest
from faker import Faker

from max_core.models.auth_session import AuthSession
from max_core.models.saml.artifact_response import ArtifactResponse
from max_core.models.userinfo import Userinfo
from pytest_mock import MockerFixture
from pydantic import ValidationError

from app.userinfo.services import UserinfoProvider, VadUserinfoService
from app.brp.schemas import NameDTO, PersonDTO
from app.prs.repositories import PrsRepository
from app.brp.service import BrpService
from app.schemas import UserInfoDTO

faker = Faker()


class TestUserinfoProvider:

    @pytest.fixture
    def mock_prs_repository(self, mocker) -> PrsRepository:
        return mocker.Mock(spec=PrsRepository)

    @pytest.fixture
    def mock_brp_service(self, mocker) -> BrpService:
        return mocker.Mock(spec=BrpService)

    @pytest.fixture
    def mock_auth_session_cache(self, mocker) -> Any:
        return mocker.Mock()

    @pytest.fixture
    def userinfo_provider(
        self,
        mock_prs_repository: PrsRepository,
        mock_brp_service: BrpService,
        mock_auth_session_cache: Any,
    ) -> UserinfoProvider:
        return UserinfoProvider(
            prs_repository=mock_prs_repository,
            brp_service=mock_brp_service,
            auth_session_cache=mock_auth_session_cache,
        )

    @pytest.fixture
    def fake_person(self) -> PersonDTO:
        return PersonDTO(
            age=faker.random_int(min=18, max=90),
            name=NameDTO(first=faker.first_name(), last=faker.last_name()),
        )

    def test_exchange_bsn_sets_cache_and_returns_userinfo(
        self,
        userinfo_provider: UserinfoProvider,
        mock_prs_repository: PrsRepository,
        mock_brp_service: BrpService,
        mock_auth_session_cache: Any,
        fake_person: PersonDTO,
    ) -> None:
        bsn = str(faker.unique.random_number(digits=9, fix_len=True))
        auth_session_id: str = str(uuid.uuid4())
        user_id: str = str(uuid.uuid4())
        subject_identifier: str = str(uuid.uuid4())
        vad_pdn: str = str(uuid.uuid4())
        rid: str = str(uuid.uuid4())

        mock_prs_repository.get_vad_pdn_by_bsn.return_value = vad_pdn
        mock_prs_repository.get_rid_by_vad_pdn.return_value = rid
        mock_brp_service.get_person_info.return_value = fake_person

        result: UserInfoDTO = userinfo_provider.exchange_bsn(
            bsn, auth_session_id, user_id, subject_identifier
        )

        mock_prs_repository.get_vad_pdn_by_bsn.assert_called_once_with(bsn)
        mock_prs_repository.get_rid_by_vad_pdn.assert_called_once_with(vad_pdn)
        mock_brp_service.get_person_info.assert_called_once_with(bsn)
        mock_auth_session_cache.set.assert_called_once_with(
            auth_session_id,
            {
                "vad_pdn": vad_pdn,
                "person": fake_person.model_dump(),
                "user_id": user_id,
            },
        )

        assert result.rid == rid
        assert result.person == fake_person
        assert result.sub == subject_identifier

    def test_exchange_session_reads_cache_and_returns_userinfo(
        self,
        userinfo_provider: UserinfoProvider,
        mock_prs_repository: PrsRepository,
        mock_auth_session_cache: Any,
        fake_person: PersonDTO,
    ) -> None:
        auth_session_id: str = str(uuid.uuid4())
        vad_pdn: str = str(uuid.uuid4())
        cached_data: Dict[str, Any] = {
            "vad_pdn": vad_pdn,
            "person": fake_person.model_dump(),
            "user_id": str(uuid.uuid4()),
        }

        mock_auth_session_cache.get.return_value = cached_data
        rid: str = str(uuid.uuid4())
        mock_prs_repository.get_rid_by_vad_pdn.return_value = rid

        auth_session: AuthSession = AuthSession(auth_session_id=auth_session_id)
        result: UserInfoDTO = userinfo_provider.exchange_session(
            auth_session, str(uuid.uuid4())
        )

        mock_auth_session_cache.get.assert_called_once_with(auth_session_id)
        mock_prs_repository.get_rid_by_vad_pdn.assert_called_once_with(vad_pdn)

        assert result.rid == rid
        assert result.person == fake_person

    def test_exchange_session_returns_empty_when_cache_missing(
        self,
        userinfo_provider: UserinfoProvider,
        mock_prs_repository: PrsRepository,
        mock_auth_session_cache: Any,
    ) -> None:
        auth_session_id: str = str(uuid.uuid4())
        mock_auth_session_cache.get.return_value = None

        auth_session: AuthSession = AuthSession(auth_session_id=auth_session_id)
        with pytest.raises(ValidationError):
            userinfo_provider.exchange_session(auth_session, str(uuid.uuid4()))

        mock_auth_session_cache.get.assert_called_once_with(auth_session_id)
        mock_prs_repository.get_rid_by_vad_pdn.assert_not_called()


class TestVadUserinfoService:

    @pytest.fixture
    def userinfo_provider(self, mocker) -> UserinfoProvider:
        return mocker.Mock(spec=UserinfoProvider)

    @pytest.fixture
    def vad_userinfo_service(
        self, userinfo_provider: UserinfoProvider
    ) -> VadUserinfoService:
        return VadUserinfoService(userinfo_provider=userinfo_provider)

    @pytest.fixture
    def fake_person(self) -> PersonDTO:
        return PersonDTO(
            age=faker.random_int(min=18, max=90),
            name=NameDTO(first=faker.first_name(), last=faker.last_name()),
        )

    def test_request_userinfo_for_saml_artifact(
        self,
        vad_userinfo_service: VadUserinfoService,
        userinfo_provider: UserinfoProvider,
        mocker: MockerFixture,
        fake_person: PersonDTO,
    ) -> None:
        bsn: str = str(faker.unique.random_number(digits=9, fix_len=True))
        subject_identifier: str = str(uuid.uuid4())
        auth_session_id = str(uuid.uuid4())

        artifact_response: ArtifactResponse = mocker.Mock(spec=ArtifactResponse)
        artifact_response.get_bsn.return_value = bsn

        userinfo_dto = UserInfoDTO(
            rid=str(uuid.uuid4()), person=fake_person, sub=subject_identifier
        )

        userinfo_provider.exchange_bsn.return_value = userinfo_dto
        mocker.patch("uuid.uuid4", return_value=uuid.UUID(auth_session_id))

        result: Userinfo = vad_userinfo_service.request_userinfo_for_saml_artifact(
            authentication_context=mocker.Mock(),
            artifact_response=artifact_response,
            subject_identifier=subject_identifier,
        )

        expected_user_id: str = sha256(bsn.encode("utf-8")).hexdigest()
        userinfo_provider.exchange_bsn.assert_called_once_with(
            bsn, auth_session_id, expected_user_id, subject_identifier
        )

        assert result.body == userinfo_dto.model_dump_json()
        assert result.content_type == "application/json"
        assert result.auth_session_id == auth_session_id

    def test_provide_userinfo_from_active_auth_session(
        self,
        vad_userinfo_service: VadUserinfoService,
        userinfo_provider: UserinfoProvider,
        fake_person: PersonDTO,
    ) -> None:
        auth_session_id: str = str(uuid.uuid4())
        auth_session: AuthSession = AuthSession(auth_session_id=auth_session_id)
        subject_identifier: str = str(uuid.uuid4())

        userinfo_dto: UserInfoDTO = UserInfoDTO(
            rid=str(uuid.uuid4()), person=fake_person, sub=subject_identifier
        )

        userinfo_provider.exchange_session.return_value = userinfo_dto

        result: Userinfo = (
            vad_userinfo_service.provide_userinfo_from_active_auth_session(
                auth_session, subject_identifier
            )
        )

        userinfo_provider.exchange_session.assert_called_once_with(
            auth_session, subject_identifier
        )
        assert result.body == userinfo_dto.model_dump_json()
        assert result.content_type == "application/json"
        assert result.auth_session_id == auth_session_id
