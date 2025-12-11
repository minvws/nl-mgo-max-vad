import uuid

from inject import autoparams
from max_core.models.auth_session import AuthSession
from max_core.models.authentication_context import AuthenticationContext
from max_core.models.saml.artifact_response import ArtifactResponse
from max_core.models.userinfo import Userinfo
from max_core.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from max_core.services.userinfo.userinfo_service import UserinfoService
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
        auth_session_encrypter: AuthSessionEncrypter,
    ) -> None:
        self.__prs_repository = prs_repository
        self.__brp_service = brp_service
        self.__auth_session_cache = auth_session_cache
        self.__auth_session_encrypter = auth_session_encrypter

    def exchange_bsn(self, bsn: str, auth_session_id: str) -> UserInfoDTO:
        vad_pdn = self.__prs_repository.get_vad_pdn_by_bsn(bsn)
        rid = self.__prs_repository.get_rid_by_vad_pdn(vad_pdn)
        person: PersonDTO = self.__brp_service.get_person_info(bsn)

        self.__auth_session_cache.set(
            auth_session_id,
            {
                "vad_pdn": vad_pdn,
                "person": person.model_dump(),
            },
        )

        return UserInfoDTO(
            rid=rid,
            person=person,
            sub=self.__auth_session_encrypter.encrypt(auth_session_id),
        )

    def exchange_session(self, auth_session: AuthSession) -> UserInfoDTO:
        auth_session_context = AuthSessionContextDTO(
            **self.__auth_session_cache.get(auth_session.auth_session_id) or {}
        )

        rid = self.__prs_repository.get_rid_by_vad_pdn(auth_session_context.vad_pdn)

        return UserInfoDTO(
            rid=rid,
            person=auth_session_context.person,
            sub=self.__auth_session_encrypter.encrypt(auth_session.auth_session_id),
        )


class VadUserinfoService(UserinfoService):
    CONTENT_TYPE = "application/json"

    @autoparams()
    def __init__(
        self,
        userinfo_provider: UserinfoProvider,
    ) -> None:
        self.__userinfo_provider: UserinfoProvider = userinfo_provider

    def request_userinfo_for_saml_artifact(
        self,
        authentication_context: AuthenticationContext,
        artifact_response: ArtifactResponse,
        subject_identifier: str,
    ) -> Userinfo:
        bsn = artifact_response.get_bsn(authorization_by_proxy=True)
        auth_session_id = str(uuid.uuid4())
        userinfo_body = self.__userinfo_provider.exchange_bsn(bsn, auth_session_id)

        return Userinfo(
            body=userinfo_body.model_dump_json(),
            content_type=self.CONTENT_TYPE,
            auth_session_id=auth_session_id,
        )

    def request_userinfo_for_session(self, auth_session: AuthSession) -> Userinfo:
        userinfo = self.__userinfo_provider.exchange_session(auth_session)

        return Userinfo(
            body=userinfo.model_dump_json(),
            content_type=self.CONTENT_TYPE,
            auth_session_id=auth_session.auth_session_id,
        )
