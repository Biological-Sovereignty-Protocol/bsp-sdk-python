"""AccessManager — Manage consent tokens for BSP data access."""

from typing import Optional
from .types import ConsentToken, BSPIntent


class AccessManager:
    """
    Manage consent tokens enforced by the AccessControl smart contract on Arweave.

    Example:
        manager = AccessManager(ieo_id="my-lab.bsp")
        token = manager.get_token(beo_id)
        if not token or not token.is_valid():
            request = manager.request_consent(beo_id, intents=["SUBMIT_BIORECORD"], categories=["BSP-GL"])
            token = manager.wait_for_approval(request["request_id"])
    """

    def __init__(self, ieo_id: str):
        self.ieo_id = ieo_id

    def get_token(self, beo_id: str) -> Optional[ConsentToken]:
        raise NotImplementedError("Install bsp-sdk from PyPI when published")

    def request_consent(
        self,
        beo_id: str,
        intents: list[BSPIntent],
        categories: list[str],
        expires_in: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> dict:
        raise NotImplementedError("Install bsp-sdk from PyPI when published")

    def wait_for_approval(self, request_id: str, timeout_s: int = 3600) -> ConsentToken:
        raise NotImplementedError("Install bsp-sdk from PyPI when published")

    def revoke_token(self, token_id: str) -> None:
        raise NotImplementedError("Install bsp-sdk from PyPI when published")
