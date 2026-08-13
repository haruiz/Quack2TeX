import os
from dataclasses import dataclass


SERVICE_NAME = "quack2tex"


@dataclass(frozen=True)
class ProviderCredential:
    name: str
    label: str
    env_var: str


PROVIDER_CREDENTIALS = (
    ProviderCredential("gemini", "Google Gemini", "GEMINI_API_KEY"),
    ProviderCredential("openai", "OpenAI", "OPENAI_API_KEY"),
    ProviderCredential("anthropic", "Anthropic", "ANTHROPIC_API_KEY"),
    ProviderCredential("groq", "Groq", "GROQ_API_KEY"),
)


class CredentialStoreError(RuntimeError):
    pass


class CredentialStore:
    """
    OS keychain-backed storage for model provider API keys.
    """

    @classmethod
    def providers(cls) -> tuple[ProviderCredential, ...]:
        return PROVIDER_CREDENTIALS

    @classmethod
    def provider(cls, name: str) -> ProviderCredential:
        for provider in PROVIDER_CREDENTIALS:
            if provider.name == name:
                return provider
        raise ValueError(f"Unknown provider: {name}")

    @classmethod
    def get_api_key(cls, provider_name: str, include_env: bool = True) -> str:
        provider = cls.provider(provider_name)
        if include_env:
            env_value = os.getenv(provider.env_var)
            if env_value:
                return env_value
        return cls._get_password(provider)

    @classmethod
    def has_stored_api_key(cls, provider_name: str) -> bool:
        provider = cls.provider(provider_name)
        return bool(cls._get_password(provider))

    @classmethod
    def set_api_key(cls, provider_name: str, api_key: str) -> None:
        provider = cls.provider(provider_name)
        value = api_key.strip()
        if not value:
            raise ValueError("API key cannot be empty.")
        cls._set_password(provider, value)
        os.environ[provider.env_var] = value

    @classmethod
    def delete_api_key(cls, provider_name: str) -> None:
        provider = cls.provider(provider_name)
        stored_value = cls._get_password(provider)
        cls._delete_password(provider)
        if stored_value and os.getenv(provider.env_var) == stored_value:
            os.environ.pop(provider.env_var, None)

    @classmethod
    def hydrate_environment(cls, overwrite: bool = False) -> None:
        """
        Copy stored keys into os.environ so existing provider clients can read them.
        """
        for provider in PROVIDER_CREDENTIALS:
            if os.getenv(provider.env_var) and not overwrite:
                continue
            try:
                api_key = cls._get_password(provider)
            except CredentialStoreError:
                continue
            if api_key:
                os.environ[provider.env_var] = api_key

    @classmethod
    def _get_password(cls, provider: ProviderCredential) -> str:
        try:
            import keyring

            return keyring.get_password(SERVICE_NAME, provider.env_var) or ""
        except Exception as exc:
            raise CredentialStoreError(str(exc)) from exc

    @classmethod
    def _set_password(cls, provider: ProviderCredential, value: str) -> None:
        try:
            import keyring

            keyring.set_password(SERVICE_NAME, provider.env_var, value)
        except Exception as exc:
            raise CredentialStoreError(str(exc)) from exc

    @classmethod
    def _delete_password(cls, provider: ProviderCredential) -> None:
        try:
            import keyring

            try:
                keyring.delete_password(SERVICE_NAME, provider.env_var)
            except keyring.errors.PasswordDeleteError:
                pass
        except Exception as exc:
            raise CredentialStoreError(str(exc)) from exc
