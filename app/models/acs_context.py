from pydantic import BaseModel


class AcsContext(BaseModel):
    client_id: str
    authentication_method: str
    userinfo: str

    def to_dict(self):
        return {
            "client_id": self.client_id,
            "authentication_method": self.authentication_method,
            "userinfo": self.userinfo,
        }

    @classmethod
    def from_dict(cls, dictonary: dict):
        return cls(
            client_id=dictonary["client_id"],
            authentication_method=dictonary["authentication_method"],
            userinfo=dictonary["userinfo"],
        )
