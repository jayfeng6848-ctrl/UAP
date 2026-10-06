# P20 EVENT CANDIDATE MATRIX

```text
性质 = P20 PREP 附件（候选事件 × P19 Event Authority 逐项对齐）· 全部标记 DESIGN PROPOSAL / NOT FROZEN
```

## 1. 候选 event type（提案 · 未冻结）

```text
候选 A（Company 例）：company.employee.assigned / company.employee.removed
候选 B（Commercial 例）：commercial.order.placed / commercial.order.paid / commercial.order.refunded
候选 C（Entertainment 例）：entertainment.content.published / entertainment.content.retracted
状态：全部 NOT FROZEN · 未定义 payload 契约 · 未注册 handler · 未激活
```

## 2. 对齐矩阵（对任一候选 type 均须逐项成立）

| 决策 | 要求 | 当前状态 | 证据来源 |
|---|---|---|---|
| D02 | 10 项 eligibility 齐备 | **OPEN** | 无模块被选定 ⇒ 无 type/version/producer/handler/语义 |
| D03 | real production producer | **OPEN** | 全仓非测试代码 `INSERT INTO events` = 0 |
| D04 | qualified handler（四项资格） | **OPEN** | production_allowlist() = 空 |
| D05 | actor = 真实认证主体 | PARTIAL | 平台已有 actor 边界（P17/P18）；业务未定义 |
| D06 | canonical 12 action 映射 | PARTIAL | 词表已冻结（P13）；业务 resource_type 未定义 |
| D07 | tenant/space 语义 | **OPEN** | 模块未选定 ⇒ 公司/门店/频道映射未定 |
| D08 | 与 P18-D14 生命周期一致 | PARTIAL | 平台门禁已实现；业务对非 ACTIVE 的处置未定义 |
| D09 | 可证明幂等 | **OPEN** | 无业务自然键/去重语义 |
| D10 | 沿用 P15 retry/lease | PASS | P15 kernel 冻结值（10 · 5×2≤600 · lease 120 · hb 40） |
| D11 | type + schema_version 策略 | **OPEN** | 未定义 |
| D12 | event ≠ audit | PASS | P19-D12 冻结 · 平台现状遵守（audit 独立） |
| D13 | 控制面只写 audit | PASS | P18 契约（结构变更只写 audit） |
| D14 | 消费不得绕 canonical 授权 | PASS（平台侧） | 授权引擎唯一（P13/P16/P18 守卫） |
| D15 | payload 安全 | **OPEN** | 无 payload 契约 |
| D16 | 沿用 P15 六种终态 | PASS | kernel 冻结终态原因 |
| D17 | 可观测 | PARTIAL | events 列具备 status/attempts/next_attempt_at/last_error |
| D18 | 首次激活门（六项齐备） | **OPEN** | producer/handler/幂等/授权/租户语义/acceptance 全部缺失 |

```text
结论：候选事件当前均**不满足**激活资格；不得注册 handler、不得修改 allowlist。
```

## 3. Envelope PREP（候选字段 · 未冻结）

```text
event_type · schema_version · occurred_at · tenant_id · space_id ·
actor_type/actor_id · subject_type/subject_id · correlation_id · causation_id ·
payload（业务最小集 · 禁 secret/token/凭据/SQL/stack）
说明：envelope 已由 P15 events 表列结构承载（无需新表/新列）；仅 payload 契约待模块冻结时定义。
```

**END OF P20 EVENT CANDIDATE MATRIX（全部候选 NOT eligible · DESIGN PROPOSAL；2026-10-01）**
