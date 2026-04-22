from pydantic import BaseModel, Field

from app.brp.schemas import PersonDTO


class UserInfoDTO(BaseModel):
    rid: str
    person: PersonDTO
    sub: str


class AuthSessionContextDTO(BaseModel):
    vad_pdn: str = Field(
        description="VAD pseudonym belonging to the BSN it was created with. PRS exchanges this PDN for a RID."
    )
    person: PersonDTO
    user_id: str
