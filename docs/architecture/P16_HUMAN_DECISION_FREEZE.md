# P16 HUMAN DECISION FREEZE

```text
性质   = 决策冻结登记（与 PDL 附录 V 同源；本文件为便于检索的摘要，不替代 PDL）
权威   = docs/architecture/PLATFORM_DECISION_LOG.md 附录 V（append-only canonical registration）
日期   = 2026-09-28
```

## 1. 决策结果（FROZEN）

| Decision | Topic | Verdict |
|---|---|---|
| P16-D01 | Runtime ownership | ACCEPT（现有 `uap_runtime`；不新建 principal） |
| P16-D02 | Agent execution model | ACCEPT（request-scoped synchronous run + `agent_runs`；无 `agent_run_steps`） |
| P16-D03 | Provider abstraction | ACCEPT（AIProvider / ProviderAdapter / ProviderRegistry 三层） |
| P16-D04 | Model routing | ACCEPT（Task→Capability→Policy→Route→Provider→Model；显式 fallback） |
| P16-D05 | Actor propagation | ACCEPT（originating actor immutable；Actor ∧ Agent 双边授权） |
| P16-D06 | Tool authorization / execution | ACCEPT（ToolGate 唯一闸门；`handler_ref` 仅作 registry key） |
| P16-D07 | Credential boundary | ACCEPT（`secret_ref` opaque；env-backed resolver；永不外泄） |
| P16-D08 | First production event | **REJECT production activation**（allowlist 保持 EMPTY · handlers 0） |
| P16-D09 | Idempotency | ACCEPT（event_id 主身份；禁新增 dedup 表；禁 provider 自动重试） |
| P16-D10 | Tenant semantics | ACCEPT（`agents.tenant_id` NOT NULL；无 platform Agent；`run.tenant_id` NOT NULL） |
| P16-D11 | Runtime principal | ACCEPT（只扩展 `uap_runtime`） |
| P16-D12 | Schema mutation | ACCEPT LIMITED（仅新增 `agent_runs` + correlation 列） |
| P16-D13 | API surface | ACCEPT（`POST /agents/{agent_id}/runs` · `GET /agent-runs/{run_id}`；禁 tool 直调） |
| P16-D14 | Test acceptance | ACCEPT（unit / architecture / security / integration + P14/P15 regression 不变） |
| Governance Reconciliation | F-P16-03 处置 | ACCEPT（不复活旧 `AGENT_RUNTIME_*`；新建 P16 Contract 作为 rules authority） |

## 2. 继承不变式

```text
Core → Domain = 0 · Actor ≠ Agent ≠ Worker ≠ DB principal · USER/ROLE/AGENT ·
12 canonical actions · DENY>ALLOW · fail-closed · approval ≠ ALLOW ·
UUIDv7 canonical event identity · tenant_id = str | None（NULL = platform-scoped）·
P15 consumer 语义 · D-01 DEFERRED · OI-G-4 BATCH-D · F-RP-06 hash basis
```

## 3. 本轮不授权

```text
NO P17 · NO P16 RELEASE · NO COMMIT · NO TAG · NO PUSH
（后续必须依次通过 P16 IMPLEMENTATION GATE → ACCEPTANCE GATE → RELEASE PREPARATION →
  COMMIT+TAG GATE → REMOTE PUSH GATE）
```

**END OF P16 HUMAN DECISION FREEZE（摘要 · 权威见 PDL 附录 V）**
