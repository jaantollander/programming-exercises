from datetime import datetime, timedelta
from typing import Any

import requests
from jose import JWTError, jwt
from pydantic import BaseModel


class OIDCProvider(BaseModel):
    name: str
    issuer: str
    client_id: str
    jwks_uri: str | None = None
    algorithms: list[str] = ["RS256"]


class OIDCConfig:
    def __init__(self):
        self.providers: dict[str, OIDCProvider] = {}
        self.jwks_cache: dict[str, dict] = {}
        self.jwks_cache_expiry: dict[str, datetime] = {}

    def add_provider(self, provider: OIDCProvider):
        self.providers[provider.name] = provider
        if provider.jwks_uri:
            self._fetch_jwks(provider.name, provider.jwks_uri)
        else:
            # Attempt to discover JWKS URI from well-known endpoint
            self._discover_jwks(provider.name, provider.issuer)

    def _discover_jwks(self, provider_name: str, issuer: str):
        try:
            well_known_url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
            response = requests.get(well_known_url, timeout=10)
            response.raise_for_status()
            config = response.json()

            if "jwks_uri" in config:
                self.providers[provider_name].jwks_uri = config["jwks_uri"]
                self._fetch_jwks(provider_name, config["jwks_uri"])

        except Exception as e:
            print(f"Failed to discover OIDC configuration for {provider_name}: {e}")

    def _fetch_jwks(self, provider_name: str, jwks_uri: str):
        try:
            response = requests.get(jwks_uri, timeout=10)
            response.raise_for_status()
            jwks = response.json()

            self.jwks_cache[provider_name] = jwks
            # Cache for 1 hour
            self.jwks_cache_expiry[provider_name] = datetime.utcnow() + timedelta(
                hours=1
            )

        except Exception as e:
            print(f"Failed to fetch JWKS for {provider_name}: {e}")

    def _get_jwks(self, provider_name: str) -> dict | None:
        if provider_name not in self.jwks_cache:
            return None

        # Check if cache is expired
        if (
            provider_name in self.jwks_cache_expiry
            and datetime.utcnow() > self.jwks_cache_expiry[provider_name]
        ):
            # Refresh JWKS
            provider = self.providers.get(provider_name)
            if provider and provider.jwks_uri:
                self._fetch_jwks(provider_name, provider.jwks_uri)

        return self.jwks_cache.get(provider_name)

    def validate_token(self, token: str) -> dict[str, Any] | None:
        """
        Validate an OIDC JWT token against all configured providers
        Returns the decoded payload if valid, None otherwise
        """
        # First try to decode without verification to get the issuer
        try:
            unverified_payload = jwt.get_unverified_claims(token)
            issuer = unverified_payload.get("iss")

            if not issuer:
                return None

            # Find matching provider
            provider = None
            for p in self.providers.values():
                if p.issuer == issuer:
                    provider = p
                    break

            if not provider:
                return None

            # Get JWKS for this provider
            jwks = self._get_jwks(provider.name)
            if not jwks:
                return None

            # Get the key ID from token header
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            # Find the matching key
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break

            if not key:
                return None

            # Verify and decode the token
            payload = jwt.decode(
                token,
                key,
                algorithms=provider.algorithms,
                audience=provider.client_id,
                issuer=provider.issuer,
                options={"verify_exp": True},
            )

            return payload

        except JWTError as e:
            print(f"JWT validation error: {e}")
            return None
        except Exception as e:
            print(f"Token validation error: {e}")
            return None


# Global OIDC configuration instance
oidc_config = OIDCConfig()
