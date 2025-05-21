from uuid import UUID


class AuthSession:
    def __init__(self, auth_session_id: UUID):
        self.__auth_session_id = auth_session_id

    def get_auth_session_id(self) -> UUID:
        return self.__auth_session_id
