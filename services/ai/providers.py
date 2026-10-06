"""Customer AI provider profiles (HD-P21-20 / HD-P21-AI-01..04).

One place owns every provider-specific fact (endpoint, default model, credential
reference, protocol mode, locality). Customer UI only ever sees ``display_name``,
a short description, whether the service is 云端/本地 and whether it needs a
credential — never a URL, model id or protocol.

HD-P21-AI-02: for LOCAL providers this file only supplies the *endpoint*; the
authoritative model list is the runtime host's own ``GET /v1/models``.
"""

from __future__ import annotations

from dataclasses import dataclass

PROTOCOL_OPENAI_COMPATIBLE = "openai-compatible"
#: OpenAI's own Responses API.
MODE_RESPONSES = "responses"
#: Chat Completions — DeepSeek / Qwen / GLM / Kimi / MiniMax / Ollama / LM Studio.
MODE_CHAT_COMPLETIONS = "chat-completions"
#: The only protocol modes the adapter can express (fail-closed; no implicit default).
MODES = (MODE_RESPONSES, MODE_CHAT_COMPLETIONS)

LOCALITY_CLOUD = "cloud"
LOCALITY_LOCAL = "local"

#: Whether the customer must supply a credential ('required'), may ('optional'), or must not.
AUTH_REQUIRED = "required"
AUTH_OPTIONAL = "optional"
AUTH_NONE = "none"

# The loopback allowlist + validator live in ``infrastructure.ai.adapters``: URL and
# transport reasoning belong to the transport layer, and only that layer may import
# a transport module (tests/architecture/test_p16_boundaries).


@dataclass(frozen=True)
class ProviderProfile:
    key: str
    display_name: str
    adapter: str
    base_url: str
    default_model: str
    secret_ref: str | None
    description: str
    mode: str = MODE_CHAT_COMPLETIONS
    protocol: str = PROTOCOL_OPENAI_COMPATIBLE
    locality: str = LOCALITY_CLOUD
    auth: str = AUTH_REQUIRED


PROVIDER_PROFILES: tuple[ProviderProfile, ...] = (
    ProviderProfile(
        key="openai",
        display_name="OpenAI",
        adapter="openai_compatible",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        secret_ref="env:UAP_AI_API_KEY_OPENAI",
        description="适合英文与多语言对话、分析与工作助手",
        mode=MODE_RESPONSES,  # unchanged: the OpenAI path that already works
    ),
    ProviderProfile(
        key="deepseek",
        display_name="DeepSeek",
        adapter="openai_compatible",
        base_url="https://api.deepseek.com",  # no /v1 auto-append
        default_model="deepseek-chat",
        secret_ref="env:UAP_AI_API_KEY_DEEPSEEK",
        description="适合中文对话、分析与工作助手",
    ),
    ProviderProfile(
        key="qwen",
        display_name="通义千问",
        adapter="openai_compatible",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-plus",
        secret_ref="env:UAP_AI_API_KEY_QWEN",
        description="适合中文办公与企业场景",
    ),
    ProviderProfile(
        key="zhipu",
        display_name="智谱 GLM",
        adapter="openai_compatible",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-4-flash",
        secret_ref="env:UAP_AI_API_KEY_ZHIPU",
        description="适合中文办公与知识问答",
    ),
    ProviderProfile(
        key="moonshot",
        display_name="Kimi",
        adapter="openai_compatible",
        base_url="https://api.moonshot.cn/v1",
        default_model="moonshot-v1-8k",
        secret_ref="env:UAP_AI_API_KEY_MOONSHOT",
        description="适合长文本与知识处理",
    ),
    ProviderProfile(
        key="minimax",
        display_name="MiniMax",
        adapter="openai_compatible",
        base_url="https://api.minimax.chat/v1",
        default_model="abab6.5s-chat",
        secret_ref="env:UAP_AI_API_KEY_MINIMAX",
        description="适合中文对话与内容生成",
    ),
    # ---------------------------------------------------------------- LOCAL
    # HD-P21-AI-01/-02/-03: the service on the UAP runtime host. No customer URL,
    # no stored credential, no persistent route.
    ProviderProfile(
        key="ollama-local",
        display_name="Ollama（本机）",
        adapter="openai_compatible",
        base_url="http://127.0.0.1:11434/v1",
        default_model="",
        secret_ref=None,
        description="使用这台电脑上已经安装的 Ollama",
        mode=MODE_CHAT_COMPLETIONS,
        locality=LOCALITY_LOCAL,
        auth=AUTH_NONE,
    ),
    ProviderProfile(
        key="lmstudio-local",
        display_name="LM Studio（本机）",
        adapter="openai_compatible",
        base_url="http://127.0.0.1:1234/v1",
        default_model="",
        secret_ref=None,
        description="使用这台电脑上已经安装的 LM Studio",
        mode=MODE_CHAT_COMPLETIONS,
        locality=LOCALITY_LOCAL,
        auth=AUTH_OPTIONAL,
    ),
)

_BY_KEY = {profile.key: profile for profile in PROVIDER_PROFILES}


def get_profile(key: str | None) -> ProviderProfile | None:
    return _BY_KEY.get(str(key or "").strip().lower())


def is_local(key: str | None) -> bool:
    profile = get_profile(key)
    return profile is not None and profile.locality == LOCALITY_LOCAL


def locality_of(key: str | None) -> str:
    profile = get_profile(key)
    return profile.locality if profile is not None else LOCALITY_CLOUD


def customer_provider_list() -> list[dict[str, object]]:
    """Customer-safe list: display name, one line, 云端/本地 and credential need."""
    return [
        {
            "key": p.key,
            "display_name": p.display_name,
            "description": p.description,
            "locality": p.locality,
            "auth": p.auth,
        }
        for p in PROVIDER_PROFILES
    ]


__all__ = [
    "AUTH_NONE",
    "AUTH_OPTIONAL",
    "AUTH_REQUIRED",
    "LOCALITY_CLOUD",
    "LOCALITY_LOCAL",
    "MODES",
    "MODE_CHAT_COMPLETIONS",
    "MODE_RESPONSES",
    "PROTOCOL_OPENAI_COMPATIBLE",
    "PROVIDER_PROFILES",
    "ProviderProfile",
    "customer_provider_list",
    "get_profile",
    "is_local",
    "locality_of",
]
