# UAP — P15 HUMAN DECISION SHEET

> 轮次 = STEP 3 · P15 PREP（决策清单 · **未做任何选择**）
> “Recommended neutral default”仅用于降低后续决策成本，**不代替** Human 最终决定；证据不足者标 `UNKNOWN`

## P15-DEC-01 — P15 主题 / scope 组成

```text
Question              : P15 的主题是什么？（平台下一批能力的选择）
Why it exists         : P14 已发布；P15 scope 尚未定义；候选见 P15_CANDIDATE_SCOPE_DISCOVERY.md
Current alternatives  : Option A 运行时/后台能力（C-5 outbox consumer + C-8 审计深化）
                        Option B 平台管理能力（C-2 管理类身份/设备/会话）
                        Option C 基础设施与集成（C-4 Bootstrap CLI 或 C-6 AI 启用）· Option D CUSTOM
Security impact       : 取决于选项（B/C 触及授权/特权边界 ⇒ 需 security decision）
Schema impact         : 取决于选项（B 可能需词表；其余 No）
Runtime impact        : 取决于选项 · Authorization impact：取决于选项
Migration impact      : 当前判定 No（0017 为 truth）；若 B 触发 SCHEMA DECISION 再评估
Recommended neutral default : 先冻结 scope 与顺序，再逐项授权实现（不预设主题）
Evidence              : P15_CANDIDATE_SCOPE_DISCOVERY.md · P14 OVERALL/RELEASE 报告 · PDL 附录 O/P/Q
```

## P15-DEC-02 — 管理类能力与 authorization 词表

```text
Question              : 是否引入 admin-on-behalf-of-user（管理他人 device/session/credential）？
Why it exists         : FINDING-AUTHZ-1（P14 明确 DEFERRED）；canonical ACTIONS 仅 12 个
Current alternatives  : Option A 不引入（保持自助 + 归属校验）
                        Option B 引入并新增 canonical action（需 Security/Authorization Decision）
                        Option C 引入但走独立 Approval/Decision model（不改 effect 词表）· Option D CUSTOM
Security impact       : **Authorization impact**（新增词表或新模型 ⇒ SECURITY DECISION REQUIRED）
Schema impact         : B 可能需 role_permissions 新 effect / 新 action 行（⇒ SCHEMA DECISION REQUIRED）
Runtime impact        : service 层新增 use-case · API impact：新增受控端点
Migration impact      : 若需 seed 新 action/role ⇒ migration（当前 FORBIDDEN）
Recommended neutral default : 保持 Option A（现状）直到明确需求与安全裁决
Evidence              : P14 Wave2 报告 FINDING-AUTHZ-1 · core/permission/vocabulary.py ACTIONS=12
```

## P15-DEC-03 — Bootstrap CLI 时机（RTA-09 = OPTION B）

```text
Question              : 是否在 P15 实现 Bootstrap CLI（一次性本地 bootstrap）？
Why it exists         : uap_bootstrap 6 项授权已就位但无任何代码使用；P14 明示独立授权
Current alternatives  : Option A 本轮不实现（继续保持 DB 层就绪、无代码）
                        Option B 实现（需独立授权 + 一次性语义 + 不可重开验证）· Option C CUSTOM
Security impact       : **Privilege boundary impact**（新增一次性特权路径 ⇒ SECURITY DECISION REQUIRED）
Schema impact         : No（platform_state / platform_memberships 已具备）
Runtime impact        : 独立于 normal runtime（不得成为 runtime dependency）· API impact：No（CLI 非 API）
Migration impact      : No
Recommended neutral default : 保持 Option A（不实现）直到独立授权
Evidence              : P14 authorization closure report（RTA-09 = OPTION B）· SEC-P14-11/12/13
```

## P15-DEC-04 — D-01 foundation maintenance

```text
Question              : 是否修复 infrastructure/database/persistence.py 的两处缺陷？
Why it exists         : P14 登记 D-01 = DEFERRED / NON-BLOCKING（Wave 1 冻结文件）
Current alternatives  : Option A 继续 DEFERRED（SafeReader 为 approved path）
                        Option B 纳入 P15 并重新授权 foundation change（两行修复 + Wave 1 回归）
                        Option C CUSTOM
Security impact       : No（不涉及授权面；但属 Wave 1 冻结实现 ⇒ FOUNDATION CHANGE REQUIRED 流程）
Schema impact         : No · Runtime impact：读取路径（defective helper 未被 active path 使用）
Authorization impact  : No · Migration impact：No
Recommended neutral default : Option A（保持 DEFERRED）——修复须单独 foundation 授权
Evidence              : P14 OVERALL OI CLOSURE MATRIX「D-01 证据」· persistence.py sha 69d2c140…
```

## P15-DEC-05 — FINDING-ENGINE-1（engine 双轨）

```text
Question              : 是否统一 /ready 探针与 RuntimeDatabase 的 engine？
Why it exists         : P14 登记 ACCEPTED COMPATIBILITY FINDING（不重构，避免触碰 health 契约）
Current alternatives  : Option A 保持现状（接受兼容性差异）· Option B 统一（需 health 契约影响评估）
                        Option C CUSTOM
Security impact       : No · Schema impact：No · Runtime impact：health/readiness 面
Authorization impact  : No · Migration impact：No
Recommended neutral default : Option A（保持现状）
Evidence              : P14 Wave2 报告 FINDING-ENGINE-1 · apps/api/routes/health.py
```

## P15-DEC-06 — 事件 / outbox consumer 与后台执行面

```text
Question              : 是否在 P15 引入 events/outbox 消费（后台执行者）？
Why it exists         : events 表与 runtime S/I/U 已就位，无 consumer；apps/worker 为 generic scheduler
Current alternatives  : Option A 不引入（保持 outbox 只写不消费）
                        Option B 引入专用 consumer（需 worker 边界 + 授权 + 幂等/重放语义）
                        Option C CUSTOM
Security impact       : **Runtime security impact**（新增后台写入者 ⇒ 幂等/重放/审计需求）
Schema impact         : No（表已存在）· Runtime impact：是 · API impact：No
Authorization impact  : 是（service 身份与 subject 语义）· Migration impact：No
Recommended neutral default : 先冻结 worker 边界与幂等契约，再授权实现
Evidence              : migrations 0013（P10 event/audit）· P14 Wave2 报告 §6/§9（events 授 S/I/U）
```

## 汇总

```text
Decision 总数            = 6
Open Human Decisions     = 6（全部 UNRESOLVED）
Unknowns                 = 1（P15-DEC-01 的最终主题选择 = UNKNOWN，须 Human 裁定）
Schema Decisions Required   = 1（P15-DEC-02 若选 B）
Security Decisions Required = 3（P15-DEC-02 / P15-DEC-03 / P15-DEC-06 的 security 面）
Authorization Decisions Required = 2（P15-DEC-02 / P15-DEC-06）
```

**END OF P15 HUMAN DECISION SHEET（2026-09-28 · 6 decisions · 0 resolved · 未做选择 · HARD STOP ACTIVE）**
