# UAP — P15 DECISION IMPACT MATRIX
> 轮次 = P15 HUMAN DECISION RESOLUTION + IMPLEMENTATION CONTRACT PREP（2026-09-28）
> 口径 = Human Decision FROZEN 之后的最终影响
| Decision | Architecture | Security | Authorization | Schema | Runtime | API | Migration |
|---|---|---|---|---|---|---|---|
| DEC-01 | C-5 selected（primary theme） | consumer boundary 需冻结 | inherited（复用 Stage 2） | 依 C-5 证据（本轮判定无需变更） | major（新增执行层） | indirect | none yet |
| DEC-02 | unchanged | no new admin path | Stage 2 unchanged（12 actions 不变） | none | unchanged | unchanged | none |
| DEC-03 | unchanged | bootstrap unchanged（就绪但未调用） | unchanged | none | no CLI | no public endpoint | none |
| DEC-04 | foundation preserved（sha 69d2c140…） | SafeReader 为 approved path | unchanged | none | no D-01 dependency | unchanged | none |
| DEC-05 | compatibility preserved | no new boundary | unchanged | none | /ready unchanged | health contract 不变 | none |
| DEC-06 | worker contract 先冻结 | worker security（授权不足 ⇒ SECURITY DECISION） | 必须继承 authorization · 不新增 subject | TBD（本轮判定现有 events 表足够） | primary（Consumer） | indirect | TBD（本轮 = 无） |
## 逐项说明
- DEC-01：P15 引入"异步执行层"，位于既有 Runtime/Service/Persistence 之上，不新增架构层；Schema 由 C-5 证据判定 ⇒ 本轮只读核验结论 = 无需变更。
- DEC-02：Option A ⇒ 无新 admin action / role / permission / grant / principal；Stage 2、canonical 12 actions、role_permissions、permissions、acl_subject_types 全不变 ⇒ 无 Authorization Decision。
- DEC-03：Option A ⇒ uap_bootstrap 保持就绪未调用；不新增特权路径 / 端点 / schema 对象。
- DEC-04：Option A（Keep Deferred）⇒ persistence.py 保持冻结（sha 69d2c140…）；P15 读取路径必须走 SafeReader；若无法避开 ⇒ STOP · FOUNDATION CHANGE REQUIRED。
- DEC-05：Option A ⇒ /ready 保持 Wave-0 process engine；RuntimeDatabase 保持 runtime 数据路径；不改 health contract。
- DEC-06：Option B + 契约前置 ⇒ Worker/Consumer 边界与职责须先在 Contract 冻结；worker DB 身份必须为 uap_runtime（已冻结边界），若授权不足 ⇒ 登记 SECURITY DECISION REQUIRED 并停止（不得 GRANT）；consumer 必须走 P14 authorization，如需 system/service/agent 新 subject ⇒ STOP · AUTHORIZATION DECISION REQUIRED。
## 边界
- 本文件为影响分析；不构成 implementation / migration / release 授权。
- Schema Mutation = 0 · Privilege Mutation = 0 · DB Mutation = 0。
**END OF P15 DECISION IMPACT MATRIX（2026-09-28 · 6 decisions · 未实施 · HARD STOP ACTIVE）**
