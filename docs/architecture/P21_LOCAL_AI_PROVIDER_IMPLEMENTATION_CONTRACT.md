# P21 LOCAL AI PROVIDER — IMPLEMENTATION CONTRACT

Status: **CONTRACT PREPARED**（本合约由 Human Decision 授权「preparation」，本身不构成实现授权）
Base: `e20b35f83a1912b0f051d8d0d2d7009f0ee6f7f9` = `UAP-V0.1.19-P21-AUTH-UX-CORRECTIONS`
Parent: `7ff9ebc204716a2c1cd36a927e361a7d27e41df2`
Produced by: `UAP P21 LOCAL AI PROVIDER — HUMAN DECISION FREEZE / MODEL SELECTION + LOCAL AI SEMANTICS`
Date: 2026-10-05

> 本合约承载 Human Decision Freeze 的冻结语义。它**不**等于 Implementation PASS、Acceptance
> PASS、Release AUTHORIZATION、Production AI AUTHORIZATION 或 P22 AUTHORIZATION。

---

## 1. Governing Frozen Decisions

### HD-P21-AI-01 — LM Studio Authentication = **OPTION B**

```
LM Studio Local Provider：authentication = optional
未要求认证  → 直连本地
要求认证    → 客户手工输入 local token
```

Token 规则：memory-only · actor-scoped · tenant-scoped · connection-scoped ·
TTL 沿用现有 ephemeral AI connection 模型。

禁止：filesystem auto-read · environment auto-read · DB persistence · localStorage ·
sessionStorage · cookie · URL · logs · browser console · cloud forwarding。
**不得自动读取用户机器上的任何本地凭证。**

### HD-P21-AI-02 — Local Model Catalog = **OPTION A**

```
Local Runtime 实际可用模型以本地 Provider 实时 Model Discovery 为权威：
Ollama / LM Studio → GET /v1/models → actual available models
```

`ai_models` **不是** Local Host 当前实际安装模型的唯一权威；其用途限于
provider model metadata / capabilities / classification / privacy / platform metadata。
客户只能选择当前 Local Host 实际发现的模型；不存在的本地模型不得显示为可用。

### HD-P21-AI-03 — Local `ai_routes` = **OPTION C**

```
P21 Local AI 第一版：NO new persistent Local ai_routes
                     NO migration
                     NO new route rows required for local discovery
```

`ai_routes` = stable platform routing semantics；
Local Model Discovery = Runtime Host ephemeral capability。

客户所选 Local Model 通过
`actor + tenant + ephemeral local connection + provider + model` 绑定；
不因本机模型变化而写入持久化 `ai_routes`。

### HD-P21-AI-04 — Universal Model Selection = **FROZEN**

All AI Providers MUST expose explicit Model Selection.

```
Provider Selection
        ↓
Model Selection
        ↓
Credential / Connection
        ↓
Enable
```

No Provider may silently choose the customer's model when a selectable model catalog
exists. Provider 与 Model 是两个独立语义：
`Provider = AI service` · `Model = concrete model under that service`。

适用于 OpenAI / DeepSeek / Qwen / Zhipu GLM / Kimi(Moonshot) / MiniMax（catalog）
以及 Ollama / LM Studio（real-time local discovery）。

前端 **MUST NOT** 发明 model identifier；model display name 与 model key 必须来自
provider catalog **或** real-time local discovery（依 provider 能力）。

### Model Qualification Rule

Provider qualification MUST NOT imply model qualification。

```
Provider
   ├── Model A → (PASS | BLOCKED | FAIL | N/E)
   ├── Model B → (PASS | BLOCKED | FAIL | N/E)
   └── Model C → (PASS | BLOCKED | FAIL | N/E)
```

`DeepSeek Provider PASS ≠ 所有 DeepSeek 模型 PASS`。

### 客户 UX Rule / Security Rule / Database Rule（冻结）

客户只看到：`连接 AI → 选择服务 → 选择模型 → 输入必要信息 → 一键启用`。
客户 **MUST NOT** 被要求理解 Adapter / Base URL / Protocol / Secret Ref / Runtime /
Agent / Tool / Tenant / Space / ai_route。

必须无静默云端回退：Local 不可用 → fail closed；Local 模型不可用 → fail closed；
Local 需要认证 → 询问客户；Local 请求失败 → fail closed。
**永不** `Local failure → silently send request to cloud Provider`。

这些决策 **不授权** migration / DDL / DML / new ai_routes / new persistent local
credentials。实现必须保持 `Core → Domain = 0` 与 `Schema change = 0 unless separately
authorized`。

---

## 2. Scope

V1 支持两个本地运行时，均复用既有 `openai-compatible` provider 通路：

```
Ollama     http://127.0.0.1:11434/v1
LM Studio  http://127.0.0.1:1234/v1
```

LOCAL 是 **provider type = LOCAL**，不是第二套 AI 架构。

### Non-Scope

LAN AI · Remote / GPU AI · RLS · API versioning · AuditWriter refactor · Authorization
redesign · Redis redesign · NOTIFY · Production Event activation · Worker implementation ·
new database tables · new migrations · new permissions · new authorization engine ·
generic CRUD framework · plugin engine · 前端单体重构 · P22。

---

## 3. Architecture

```
Customer UI（连接 AI → 选择服务 → 选择模型 → 输入必要信息 → 一键启用）
        ↓
HTTP Adapter（apps/api/routes/ai.py）
        ↓  （无 SQL / 无授权判定 / 无 provider SDK）
Ephemeral AI connection（per-(actor, tenant) · memory-only · TTL）
        ↓  绑定：provider + model（+ 可选 local token）
Agent / Company Use Case（services/agent/use_cases.py）
        ↓
Agent Runtime（services/agent/runtime.py）— provider + model 选择，fail-closed
        ↓
AI Gateway（services/ai/gateway.py）— 显式 mode，无隐式默认
        ↓
Adapter（infrastructure/ai/adapters.py）→ 本地 / 云端 HTTP
        ↓
ToolGate / ToolAuthorizationFacade → ToolExecutor → AuthorizationService（tenant/space）
```

复用不变：ProviderProfile · Adapter · Gateway · Runtime · Agent · Tool · Authorization ·
Tenant · Space。新增/修改：profile 的 LOCAL 形态、adapter 的 model discovery、显式 mode、
connection 的 model 绑定、LOCAL API 面、模型选择 UI、per-model 资格粒度。

`FORBIDDEN_DIRECT_IMPORTS = ("openai","anthropic","deepseek","ollama")` 保持——本地接入只能
走 HTTP adapter，不得引入厂商 SDK。

---

## 4. Endpoint Rules（冻结）

```
允许 host   ：localhost / 127.0.0.1 / ::1
允许 port   ：11434（Ollama） / 1234（LM Studio）
允许 scheme ：http
```

拒绝：任意其他 host · 任意公网 URL/主机 · 任意 LAN IP · `0.0.0.0` · `169.254.x.x`
（含 `169.254.169.254`）· RFC1918（`10/8`,`172.16/12`,`192.168/16`）· CGNAT `100.64/10` ·
IPv6 ULA `fc00::/7` · IPv4-mapped IPv6 `::ffff:a.b.c.d` · 以及任何解析到非 loopback 的名称。

* 校验发生在构造请求**之前**：先解析 → pin 解析出的 IP → 断言 loopback → 再连接。
* **禁止跟随 redirect**：本地服务返回 30x = 硬失败 `LOCAL_PROVIDER_PROTOCOL_ERROR`。
* `LOCAL = UAP Runtime 所在主机`。浏览器设备**不是**权威；浏览器 MUST NOT 发起 loopback 请求。

---

## 5. Discovery

```
Detect service（server-side · fail-fast · 有界超时）
        ↓
GET {base}/v1/models
        ↓
Customer selects model
        ↓
Run qualification
```

* 检测为服务端行为；不得成为长阻塞调用。
* Discovery MUST NOT 触发模型下载 / pull / 任意模型执行。
* 未检测到 → 客户可见「未检测到本地 AI」。
* 硬编码推荐模型可以作为提示，但**不得**成为唯一可运行模型。

---

## 6. Provider Model

新增 LOCAL profile 形态（server-side，客户不可见 URL / protocol / model id / secret ref）：

```
key          = "ollama-local" | "lmstudio-local"
locality     = "local"
adapter      = "openai_compatible"
base_url     = 固定 loopback 常量（服务端）
mode         = "chat-completions"     # 必填，无默认
secret_ref   = null                   # LOCAL 无凭证
display_name = 客户可见名称
description  = 客户可见一行说明
```

云端 provider 保持 catalog 形态；两类 provider 对客户呈现同一套「服务 → 模型」选择语义
（HD-P21-AI-04）。

---

## 7. Model Discovery & Universal Model Selection

```
云端：ai_models catalog（enabled models of that provider）→ 客户选择
本地：GET /v1/models 实时发现 → 客户选择
```

* 客户所选 model 随 connection 以 `(actor, tenant)` 绑定，并在运行时作为
  `AIRequest.model` 传给 provider（现运行时恒传 `model=None`，须改为使用选定 model）。
* 前端不得杜撰 model id / display name；一律来自 catalog 或实时发现。
* `ai_models` 只承载 metadata/capabilities/classification/privacy，不是本地实装模型的唯一权威
  （HD-P21-AI-02）。
* 不存在的模型不得显示为可用；选择后模型消失 → `LOCAL_MODEL_NOT_FOUND` / fail-closed。

---

## 8. Adapter Behavior

* `chat-completions`：`POST {base}/chat/completions`，body `{model, messages}`（两家本地运行时）。
* `responses`：LOCAL v1 **不假设**支持；如使用须先 probe 并单独冻结。
* 新增 opt-in `list_models()` 能力（`GET {base}/models`）；`complete()` 语义不变。
* **mode 必须显式**：缺失 mode = 配置错误，禁止静默回落 `"responses"`
  （修复 PREP `F-P21-LOCAL-AI-01`）。
* transport 必须加 scheme/host 白名单 + 禁止跟随 30x（修复 PREP `F-P21-LOCAL-AI-02`）。

---

## 9. Failure Semantics（fail-closed）

| 条件 | 代码 |
| --- | --- |
| 本地服务未运行 | `LOCAL_AI_UNAVAILABLE` |
| 本地服务无模型 | `LOCAL_MODEL_UNAVAILABLE` |
| 所选模型不存在 | `LOCAL_MODEL_NOT_FOUND` |
| 非 OpenAI-compatible 响应 / 协议漂移 | `LOCAL_PROVIDER_PROTOCOL_ERROR` |
| 本地服务要求认证 | `LOCAL_PROVIDER_AUTH_REQUIRED` |

禁止：`LOCAL failure → silent fallback → OpenAI`；`LOCAL failure → 自动把用户请求发送到云端`。

---

## 10. Security

威胁面（PREP 报告 §C T1–T14）：SSRF · LAN exposure · public URL injection · redirect ·
DNS rebinding · credential leakage · local token leakage · cloud fallback · cross-tenant ·
cross-space · tool escape · browser leakage · 提示词落入本地日志 · 模型供应链 · 可用性滥用。

不可协商：SSRF allowlist（先校验后请求）· 禁止 redirect · fail-closed mode · 不伪造凭证 ·
token 仅走 ephemeral `(actor, tenant)` store（若启用）· 浏览器不得访问 loopback ·
`ai_request_logs` 仅写白名单字段。

---

## 11. Customer UX

```
连接 AI
  ├── 云端 AI  → 选择服务 → 选择模型 → 输入 API Key → 一键启用
  └── 本地 AI  → 正在检测本机 AI 服务…
                    ├── ✓ Ollama / ✓ LM Studio → 选择模型 → [ 使用本地 AI ]
                    │        └─（若本地服务要求认证 → 手工输入 local token）
                    └── 未检测到本地 AI
```

必须真实：loading / empty / error / 401 / 403 / validation / action confirmation /
responsive layout / keyboard accessibility。
禁止：mock production data · fake success state · no-op buttons · placeholder API handlers ·
silent authorization bypass · localStorage token storage。

---

## 12. Agent Integration

```
Customer → LOCAL/Cloud Provider → UAP Agent Runtime → company.employee_list
        → AuthorizationService → Tenant / Space scope → Result
```

禁止 `Local Model → direct SQL` / `shell` / `filesystem` / `arbitrary network`。
Local AI 只是模型 Provider；权限仍由 UAP 控制。

## 13. Tool Integration

不变：tool proposal 为封闭形状 → ToolGate 授权 → `ToolExecutor` 执行受信 handler。
模型（本地或云端）不获得任何额外能力。

## 14. Authorization

单一 authorization engine，无旁路。tenant / space / role 来自会话；model 选择**不**覆盖授权。
`403` 保持统一拒绝语义。

## 15. Tenant / Space

provider + model 选择以 `(actor, tenant)` 绑定，一租户的选择对另一租户不可见。
Space 生命周期行为不变（沿用 HD-P20D-06 = C）。

---

## 16. Data Boundary（DB Rule）

```
Schema change = 0（除非另行授权）
Migration     = NOT AUTHORIZED
DDL           = NOT AUTHORIZED
DML           = NOT AUTHORIZED
new ai_routes = NOT AUTHORIZED（Local 第一版）
new persistent local credentials = NOT AUTHORIZED
```

证据：`ai_providers.privacy_tier` 已含 `'self_hosted'`；`ai_models.is_private` 存在；
`ai_providers` 为平台级 ROOT（无 `tenant_id`）——与「Local AI belongs to the UAP Runtime
host」一致；`secret_ref` nullable → NULL 即「无凭证」。

模型选择所需的一切读取（云端 catalog / 本地 discovery）都不要求 schema 变更。

---

## 17. Testing

仅 allowlist；禁止无差别 `pytest tests/`。静态架构依赖检查 · 配置检查 · 端点文档核验；
资格阶段才在隔离 synthetic 环境启动本地运行时做 live probe。禁止改写正式 DB / production 配置。

---

## 18. Acceptance Matrix

Provider × Model 粒度：

| Provider | Model | Discovery | Chat | AgentRun | Tool | AuthZ | Tenant | Space | Security | UX |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ollama | （discovered A/B/…） | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E |
| LM Studio | （discovered A/B/…） | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E |
| OpenAI | （catalog） | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E |
| DeepSeek | （catalog） | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E |
| Qwen / GLM / Kimi / MiniMax | （catalog） | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E | N/E |

不继承任何既有 Provider PASS。

---

## 19. Release Boundary

本合约不授权 commit / tag / push / release / production activation。

## 20. Open Items carried into the implementation authorization round

```
OQ-A 云端「服务→模型」选择的服务端读取点（现有 load_provider_by_key 只取第一个 enabled model）
OQ-B 模型选择的 API 形态（同一 endpoint 传 model vs. 独立 model 列表 endpoint）
OQ-C 本地 discovery 的缓存/刷新策略与检测超时（不写库）
OQ-D 本地 token 的 UI 呈现（何时询问、失败重试语义）
OQ-E PDL 是否为本组 HD-P21-AI-01..04 追加正式附录（本轮未获指令）
```
