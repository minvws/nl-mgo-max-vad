import json
from typing import Optional
from uuid import UUID

from inject import autoparams

from app.models.auth_session import AuthSession
from app.models.authentication_context import AuthenticationContext
from app.models.saml.artifact_response import ArtifactResponse
from app.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from app.services.userinfo.userinfo_service import UserinfoService
from app.storage.auth_session_cache import AuthSessionCache
from app.vad.brp.schemas import PersonDTO
from app.vad.brp.service import BrpService
from app.vad.prs.repositories import PrsRepository
from app.vad.schemas import AuthSessionContextDTO, UserInfoDTO


class UserinfoProvider:
    @autoparams()
    def __init__(
        self,
        prs_repository: PrsRepository,
        brp_service: BrpService,
        auth_session_cache: AuthSessionCache,
        auth_session_encrypter: AuthSessionEncrypter,
    ) -> None:
        self.__prs_repository = prs_repository
        self.__brp_service = brp_service
        self.__auth_session_cache = auth_session_cache
        self.__auth_session_encrypter = auth_session_encrypter

    def exchange_bsn(self, bsn: str, auth_session_id: Optional[UUID]) -> UserInfoDTO:
        vad_pdn = self.__prs_repository.get_vad_pdn_by_bsn(bsn)
        rid = self.__prs_repository.get_rid_by_vad_pdn(vad_pdn)
        person: PersonDTO = self.__brp_service.get_person_info(bsn)

        if auth_session_id:
            self.__auth_session_cache.set(
                str(auth_session_id),
                {
                    "vad_pdn": vad_pdn,
                    "person": person.model_dump(),
                },
            )

        return UserInfoDTO(
            rid=rid,
            person=person,
            sub=(
                self.__auth_session_encrypter.encrypt(auth_session_id)
                if auth_session_id
                else ""
            ),
        )

    def exchange_session(self, auth_session: AuthSession) -> UserInfoDTO:
        auth_session_id = auth_session.get_auth_session_id()

        auth_session_context = AuthSessionContextDTO(
            **self.__auth_session_cache.get(str(auth_session_id)) or {}
        )

        rid = self.__prs_repository.get_rid_by_vad_pdn(auth_session_context.vad_pdn)

        return UserInfoDTO(
            rid=rid,
            person=auth_session_context.person,
            sub=self.__auth_session_encrypter.encrypt(auth_session_id),
        )


class VadUserinfoService(UserinfoService):
    @autoparams()
    def __init__(
        self,
        userinfo_provider: UserinfoProvider,
    ) -> None:
        self.__userinfo_provider: UserinfoProvider = userinfo_provider

    def request_userinfo_for_digid_artifact(
        self,
        authentication_context: AuthenticationContext,
        artifact_response: ArtifactResponse,
        subject_identifier: str,
        auth_session_id: Optional[UUID],
    ) -> str:
        bsn = artifact_response.get_bsn(authorization_by_proxy=True)
        userinfo = self.__userinfo_provider.exchange_bsn(bsn, auth_session_id)

        return json.dumps(userinfo.model_dump())

    def request_userinfo_for_exchange_token(
        self, authentication_context: AuthenticationContext, subject_identifier: str
    ) -> str:
        raise NotImplementedError()

    def request_userinfo_for_session(self, auth_session: AuthSession) -> str:
        userinfo = self.__userinfo_provider.exchange_session(auth_session)

        return json.dumps(userinfo.model_dump())
