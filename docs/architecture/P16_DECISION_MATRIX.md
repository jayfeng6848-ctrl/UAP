# P16 DECISION MATRIX

## 0. 性质

```text
本文件 = DECISION INPUT（NOT FROZEN · NOT ACCEPTED）
BOT 只能提出选项 / 风险 / 技术建议；不得自行冻结任何语义。
“建议”列仅为 BOT technical recommendation，不构成 Decision。
```

---

## 1. Decision Matrix

| Decision ID | Topic | Options | 建议（BOT technical recommendation） | Risk | Evidence | Needs Human Freeze |
|---|---|---|---|---|---|---|
| P16-D01 | Runtime ownership（谁承载 agent runtime） | A: services/ 内新增 runtime 包 · B: 扩展 apps/worker 为独立进程 · C: 复用 P15 consumer 进程 | analysis only | High | agent/ 契约 · apps/worker · P14 principal | YES |
| P16-D02 | Agent execution model（Run 对象与状态机落点） | A: 新增 agent_runs/agent_run_steps（需 migration）· B: 以 tool_executions 为唯一台账 · C: 混合（内存态 + tool_executions 落账） | analysis only | High | 未入库契约（DESIGN ONLY）· 0011 tool_executions | YES |
| P16-D03 | Provider abstraction（adapter 边界） | A: 保持 intelligence/providers 契约 + 新 adapter 实现 · B: 在 services 层实现 adapter · C: 直接调用 vendor SDK（违反既有守卫） | analysis only（A 与 FORBIDDEN_DIRECT_IMPORTS 守卫一致） | High | intelligence/* · DEPENDENCY_RULES §3 | YES |
| P16-D04 | Model routing（Task→Capability→Policy→Provider→Model） | A: 完全数据驱动（ai_routes/ai_policies）· B: 代码默认策略 + 数据覆盖 · C: 单 provider 单 model 最小实现 | analysis only | Medium | 0010 schema（capabilities/privacy_tier/max_classification/fallback_chain） | YES |
| P16-D05 | Actor propagation（originating actor 如何贯穿） | A: 由 AuthenticatedContext 直接透传 · B: 由 run 记录携带 · C: 由 event actor 字段承载（P15 语义） | analysis only（C 与 P15 冻结一致） | Critical | P13/P14/P15 · core/event · services/context | YES |
| P16-D06 | Tool authorization / execution boundary | A: 同进程 ToolGate + dispatcher · B: 隔离进程执行 · C: 仅授权不执行（本阶段不产生真实副作用） | analysis only | Critical | ToolGate · tool_* 表 · handler_ref 无解析点 | YES |
| P16-D07 | Credential boundary（secret_ref 解析与注入） | A: 进程环境注入 + adapter 内解析 · B: 外部 secret manager 引用 · C: 暂不接真实 provider（stub 边界） | analysis only | Critical | .env.example · secret_ref 无引用 · FORBIDDEN_DIRECT_IMPORTS | YES |
| P16-D08 | First production event（是否激活） | A: 激活 1 个 event + 1 个 handler · B: 不激活（以 tool_executions + audit 收尾）· C: 一次激活多个 | analysis only | High | P15 consumer 就绪 · allowlist EMPTY · O-6 幂等规则 | YES |
| P16-D09 | Idempotency（首个 handler 的幂等机制） | A: event_id 唯一性 + 天然幂等操作 · B: 事务内幂等键 · C: 本阶段不激活 handler | analysis only | High | P15 O-6（不得新增 dedup 表） | YES |
| P16-D10 | Tenant semantics（平台级 agent 是否存在） | A: agents.tenant_id 保持 NOT NULL · B: 允许平台级 agent（需 schema 决策）· C: 用占位 tenant（不建议） | analysis only | Critical | 0011 NOT NULL · 0013 NULLable · P15 NULL=platform | YES |
| P16-D11 | Runtime principal（谁执行） | A: 扩展 uap_runtime 的 grant · B: 新增专用 principal（如 uap_agent）· C: 维持现状（不可行：无 grant） | analysis only | Critical | 实测 grant：51 项 / 29 表 | YES |
| P16-D12 | Schema mutation（是否需要新表/列） | A: 零 schema（复用既有表）· B: 新增 run/step 表（0018+）· C: 仅新增索引/约束 | analysis only | High | 0008/0010/0011/0013 现有结构 | YES |
| P16-D13 | API surface（最小端点） | A: 新增 1 个 run 触发端点 · B: 复用现有端点 · C: 本阶段不暴露 API（内部/worker 触发） | analysis only | Medium | apps/api 现有 5 组路由 · handler-no-SQL 边界 | YES |
| P16-D14 | Test acceptance（P16 验收口径） | A: 新增逐文件 allowlist + 复用 P14/P15 frozen 集 · B: 仅 unit/architecture · C: 含全链 integration（需 test DB 与 grant） | analysis only | High | P14/P15 manifests · CF-C-4 denylist | YES |

---

## 2. 决策间依赖（约束图）

```text
P16-D11（principal/grant）   → 阻塞 D01（runtime ownership）与 D06（tool execution）
P16-D07（凭据边界）         → 阻塞 D03（provider abstraction）与 D04（routing 落地）
P16-D12（schema mutation）   → 受 D02（execution model）与 D08/D09（event/handler）影响
P16-D10（tenant 语义）       → 阻塞 D02/D06/D08 的最终形状
P16-D05（actor propagation） → 约束 D06/D08（event actor 字段与 provenance）
```

## 3. 每个决策的工程 / 发布后果（只计算，不执行）

| Decision | 需要 migration | 需要新 grant/role | 影响 release 版本 | 备注 |
|---|---|---|---|---|
| D01 | 否 | 视 D11 | 否 | 影响进程边界 |
| D02 | 可能（0018+） | 否 | 是 | Run 台账承载方式 |
| D03 | 否 | 否 | 否 | adapter 位置 |
| D04 | 否 | 否 | 否 | 数据 vs 代码策略 |
| D05 | 否 | 否 | 否 | 需与 P15 event actor 对齐 |
| D06 | 否 | 可能（tool_* 写） | 否 | 执行边界是安全重点 |
| D07 | 否 | 否（凭据不进 DB） | 否 | 凭据只经注入边界 |
| D08 | 否 | 否（events 已可写） | 是 | 首个生产事件 |
| D09 | 否（禁新增 dedup 表） | 否 | 否 | 幂等机制 |
| D10 | 是（若允许平台级 agent） | 否 | 是 | NULL 语义一致性 |
| D11 | 否 | 是 | 是 | P14 冻结面受影响 |
| D12 | 是 | 视方案 | 是 | 0018+ 需独立 Gate |
| D13 | 否 | 否 | 否 | API 暴露面 |
| D14 | 否 | 否 | 否 | 验收口径 |

```text
任何涉及 grant / role / schema 的选项都超出 P14/P13/P15 的冻结范围 ⇒
必须独立 Human Decision + 独立 Gate，不得作为 P16 实现的副作用发生
```

## 4. 本文件不提供

```text
不提供：best architecture / winner / score / ranking
不提供：FROZEN / ACCEPTED / FINAL 标签
不提供：BOT 自选方案
```

**END OF P16 DECISION MATRIX（DECISION INPUT ONLY）**
