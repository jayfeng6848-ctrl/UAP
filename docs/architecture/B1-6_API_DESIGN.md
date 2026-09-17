# B1-6 API Design

**Stage**: B1-6（= P08 AI Gateway）· **Status**: DESIGN
**输入**: `B1-6_DECISION_LOG.md`（D-B16-01 ～ D-B16-11 FROZEN）· `B1-6_SCHEMA_DESIGN.md`
**边界**: 本文档**不是** API 实现。**不编写 API 代码、不编写 endpoint、不接入 provider、不调用外部 AI API、不加载 adapter、不注册 provider runtime。**

---

## 1. 结论先行

```
本阶段 API / 服务端实现面：
    HTTP API        = 0
    Socket.IO       = 0
    gRPC            = 0
    service 层实现   = 0
    provider 调用    = 0
    adapter 加载     = 0
    registry 注册    = 0
```

**P08 是数据模型阶段。** 本文件只界定 **边界** 与 **未来契约**。

---

## 2. 理由

1. **P08 的交付物是 schema**：5 张表 + 约束/索引/触发器/分区（见 `B1-6_SCHEMA_DESIGN.md`），
   其价值在于把"厂商是数据行而非代码分支"（架构铁律 3）变为**可存储的结构**。
2. **调用链尚未就位**：`Agent → Policy → Tool → Service → DB` 的 Policy 侧（P09）与 Agent 侧（P09）均未交付；
   此时暴露 AI Gateway 的运行时接口没有消费者。
3. **adapter 的语义边界已冻结**：**D-B16-06 = FROZEN — A** —— `adapter` 仅文本引用，
   P08 **不引入**解析 / 加载 / 注册 / 动态导入 / 运行时发现。
   任何"按 `adapter` 值加载实现"的接口都会**越界**。
4. **不引入 secret 解析**：`secret_ref` 只存引用（`CORE:1047`）；本阶段不实现密钥管理与取用。
5. **不引入授权求值**：`ai_policies` 的分级/准入/预算字段为 **storage-only**；
   本阶段不做 policy 求值、不做路由选择、不做 fallback 执行。

---

## 3. 后续阶段的接口契约（**冻结输入，非本阶段实现**）

> 以下为**契约方向的记录**，供后续阶段设计时参照。**本阶段一律不实现，不定义函数签名，不定义 endpoint 路径。**

| 契约方向 | 消费者 | 本阶段提供的结构 | 后续阶段需自行决定 |
|---|---|---|---|
| 厂商/模型目录读取 | 后续 AI Gateway 实现 | `ai_providers` / `ai_models`（数据行） | 读取接口形态、缓存策略、健康检查触发 |
| 路由选择 | 后续（P09 之后） | `ai_routes`（capability / priority / fallback_chain） | 选择算法、优先级解析、fallback 执行 |
| 分级/准入决策 | 后续授权层 | `ai_policies`（分级 / 准入 / 预算 / 延迟 / redaction） | 求值语义、DENY 优先、与 Authorization Layer 的接合点 |
| 模型调用 | 后续 AI Gateway 实现 | `ai_providers.adapter`（注册键，**纯文本**） | 适配器注册表如何被填充、厂商 SDK 如何被隔离 |
| 调用观测 | 后续（可观测/成本） | `ai_request_logs`（分区表） | 写入时机、聚合口径、保留期执行方式（**D-3 = D FROZEN：分区维护与保留清理为手工运维**） |
| Agent 绑定路由 | **P09** | `ai_routes.id`（被引用目标） | `agents.default_route_id` 的建立（**P09 侧**） |

**共性约束（冻结）**

```
· 厂商 SDK 不得被 core 或 intelligence 直接 import（架构铁律 3，tests/architecture 强制）
· 密钥不得进入任何表列（secret_ref 仅引用）
· jsonb 列（capabilities / config / fallback_chain / allowed_privacy_tiers / denied_providers）
  在本阶段为 storage-only，不定义其内部 schema 的解析契约
```

---

## 4. 与后续阶段的依赖

| 阶段 | 关系 |
|---|---|
| **P09 Agent** | `agents.default_route_id → ai_routes.id ON DELETE SET NULL` 由 **P09 建立**；P08 只需保证 `ai_routes` 存在且 `id` 稳定 |
| **P09 Agent** | `agents.current_version_id` deferred FK 属 **P09**（`SCHEMA_DEPENDENCY:170`）；`:136` 的「Phase 08」为陈旧引用，见 `B1-6_DEPENDENCY.md` §5.1 |
| **P10 Event / Audit** | `events` / `audit_logs` 与 `ai_request_logs` 同为分区表，约定共用；P08 不写 `events`，不写 `audit_logs` |
| **P11 / P12** | B1-6 内联建立的 UQ 索引与 `ix_airl_tenant_occurred` 之外**无其他索引**（**D-2 = B FROZEN**：`ix_aimodels_capability` 不建立，见 `B1-6_DECISION_LOG.md` §9.3）；其余查询索引留待后续 phase |
| **P13 Seed** | P08 零 seed（D-B16-11 = A）；provider 行由运维/后续管理面写入，**不在本阶段** |

---

## 5. 边界声明

```
本阶段明确【不做】：
  × 编写任何 API 路由 / controller / service / DTO
  × 编写任何 endpoint（路径、方法、请求/响应结构）
  × 接入任何 provider（OpenAI / Anthropic / DeepSeek / Qwen / GLM / Ollama / vLLM / …）
  × 调用任何外部 AI API
  × 加载 / 实例化 adapter；不触碰 intelligence/providers 的 ProviderRegistry
  × 注册 provider runtime；不做动态导入；不做运行时发现
  × 解析 secret_ref；不实现密钥管理
  × 求值 ai_policies；不做路由选择 / fallback 执行 / 预算计算 / 延迟预算执行
  × 写入 ai_request_logs（无调用方）；不实现日志写入路径
  × 启用 RLS / 授权求值 / ABAC
  × 修改任何代码或测试

本阶段明确【交付】：
  √ 上述 5 张表的设计（DESIGN 层）
  √ 边界与未来契约的文字记录（本文件）
```

**API DESIGN ≠ implementation。** 本文件的存在不构成任何实现授权；
P08 的实现授权需经后续显式的 Implementation Gate。

---

## 6. Gate

```
B1-6 API_DESIGN = DESIGN（API = 0 · Socket = 0 · service 实现 = 0）
0010 = ABSENT
DESIGN DECISION FREEZE = PASS（D-1 = B · D-2 = B · D-3 = D · D-4 = A · DC-1 = A · T-1 = DEFERRED）
IMPLEMENTATION = BLOCKED
```
