from pydantic import BaseModel, Field

from app.brp.schemas import PersonDTO


class UserInfoDTO(BaseModel):
    rid: str
    person: PersonDTO
    sub: str = Field(description="Subject identifier containing the auth session id.")


class AuthSessionContextDTO(BaseModel):
    vad_pdn: str = Field(
        description="VAD pseudonym belonging to the BSN it was created with. PRS exchanges this PDN for a RID."
    )
    person: PersonDTO
