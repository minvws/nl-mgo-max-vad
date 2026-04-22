# mypy: ignore-errors
from pyop.userinfo import Userinfo


class EmptyUserinfo(Userinfo):
    """
    A virtual user info database that returns None for any fetched `sub` claim.
    This forces the PyOP library to generate the `sub`, ensuring consistency
    across the entire OIDC flow.
    """

    def __init__(self, db=None):
        super().__init__({})

    def get_claims_for(self, user_id, requested_claims, userinfo=None):
        return {}

    def __getitem__(self, item):
        return {}

    def __contains__(self, item):
        return False
