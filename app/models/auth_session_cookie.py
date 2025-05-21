from dataclasses import dataclass, field, asdict
from typing import Any, Dict
from app.constants import AUTH_SESSION_COOKIE


@dataclass(frozen=True)
class AuthSessionCookie:
    key: str = field(default=AUTH_SESSION_COOKIE, init=False)
    httponly: bool = field(default=True, init=False)
    expires: str
    secure: bool
    value: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
