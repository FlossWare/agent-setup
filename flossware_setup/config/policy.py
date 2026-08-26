"""Re-export policy from the configuration contract package."""
from flossware_setup.config_contract.policy import Policy, PolicyError

__all__ = ["Policy", "PolicyError"]
