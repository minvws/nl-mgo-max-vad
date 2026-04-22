from hashlib import sha256
import uuid

from inject import autoparams
from max_core.models.auth_session import AuthSession
from max_core.models.authentication_context import AuthenticationContext
from max_core.models.saml.artifact_response import ArtifactResponse
from max_core.models.userinfo import Userinfo
from max_core.services.userinfo.auth_session_based_userinfo_service import (
    AuthSessionBasedUserinfoService,
)
from max_core.storage.auth_session_cache import AuthSessionCache

from app.brp.schemas import PersonDTO
from app.brp.service import BrpService
from app.prs.repositories import PrsRepository
from app.schemas import AuthSessionContextDTO, UserInfoDTO


class UserinfoProvider:
    @autoparams()
    def __init__(
        self,
        prs_repository: PrsRepository,
        brp_service: BrpService,
        auth_session_cache: AuthSessionCache,
    ) -> None:
        self.__prs_repository = prs_repository
        self.__brp_service = brp_service
        self.__auth_session_cache = auth_session_cache

    def exchange_bsn(
        self, bsn: str, auth_session_id: str, user_id: str, subject_identifier: str
    ) -> UserInfoDTO:
        vad_pdn = self.__prs_repository.get_vad_pdn_by_bsn(bsn)
        rid = self.__prs_repository.get_rid_by_vad_pdn(vad_pdn)
        person: PersonDTO = self.__brp_service.get_person_info(bsn)

        self.__auth_session_cache.set(
            auth_session_id,
            {
                "vad_pdn": vad_pdn,
                "person": person.model_dump(),
                "user_id": user_id,
            },
        )

        return UserInfoDTO(
            rid=rid,
            person=person,
            sub=subject_identifier,
        )

    def exchange_session(
        self, auth_session: AuthSession, subject_identifier: str
    ) -> UserInfoDTO:
        auth_session_context = AuthSessionContextDTO(
            **self.__auth_session_cache.get(auth_session.auth_session_id) or {}
        )

        rid = self.__prs_repository.get_rid_by_vad_pdn(auth_session_context.vad_pdn)

        return UserInfoDTO(
            rid=rid,
            person=auth_session_context.person,
            sub=subject_identifier,
        )


class VadUserinfoService(AuthSessionBasedUserinfoService):
    CONTENT_TYPE = "application/json"

    @autoparams("userinfo_provider")
    def __init__(self, userinfo_provider: UserinfoProvider) -> None:
        self.__userinfo_provider = userinfo_provider

    def request_userinfo_for_saml_artifact(
        self,
        authentication_context: AuthenticationContext,
        artifact_response: ArtifactResponse,
        subject_identifier: str,
    ) -> Userinfo:
        bsn = artifact_response.get_bsn(authorization_by_proxy=True)
        user_id = sha256(bsn.encode("utf-8")).hexdigest()

        auth_session_id = str(uuid.uuid4())
        userinfo_body = self.__userinfo_provider.exchange_bsn(
            bsn, auth_session_id, user_id, subject_identifier
        )

        return Userinfo(
            body=userinfo_body.model_dump_json(),
            content_type=self.CONTENT_TYPE,
            auth_session_id=auth_session_id,
        )

    def provide_userinfo_from_active_auth_session(
        self, auth_session: AuthSession, subject_identifier: str
    ) -> Userinfo:
        userinfo = self.__userinfo_provider.exchange_session(
            auth_session, subject_identifier
        )

        return Userinfo(
            body=userinfo.model_dump_json(),
            content_type=self.CONTENT_TYPE,
            auth_session_id=auth_session.auth_session_id,
        )
