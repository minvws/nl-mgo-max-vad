from pydantic import BaseModel, Field


class GetVadPdnResponse(BaseModel):
    pdn: str = Field(
        description="VAD pseudonym belonging to the BSN it was created with. PRS exchanges this PDN for a RID."
    )
