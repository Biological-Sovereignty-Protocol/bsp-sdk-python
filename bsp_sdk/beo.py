"""BEOClient — Create and manage Biological Entity Objects on Arweave."""

from typing import Optional
from .types import BEO, Guardian


class BEOClient:
    """
    Create and manage Biological Entity Objects.

    BEO creation is open to anyone. No permission from the Ambrósio Institute
    or any authority is required.

    Example:
        client = BEOClient()
        beo = client.create(domain="andre.bsp")
    """

    def create(self, domain: str, guardians: Optional[list[dict]] = None) -> BEO:
        """
        Create a new BEO and register it on Arweave.

        Args:
            domain: The desired .bsp domain (e.g. "andre.bsp")
            guardians: Optional list of guardian configurations

        Returns:
            BEO: The created Biological Entity Object
        """
        raise NotImplementedError("Install bsp-sdk from PyPI when published")

    def resolve(self, domain: str) -> BEO:
        """Resolve a .bsp domain to its BEO."""
        raise NotImplementedError("Install bsp-sdk from PyPI when published")

    def get(self, beo_id: str) -> BEO:
        """Fetch a BEO from Arweave by its ID."""
        raise NotImplementedError("Install bsp-sdk from PyPI when published")

    def is_available(self, domain: str) -> bool:
        """Check if a .bsp domain is available."""
        raise NotImplementedError("Install bsp-sdk from PyPI when published")
