# UAP — P15 IMPLEMENTATION PREP
> 轮次 = P15 OPEN DECISIONS FREEZE + CONTRACT FINALIZATION（2026-09-28）
> 状态 = **IMPLEMENTATION PREP = PASS** · `P15 IMPLEMENTATION = NOT AUTHORIZED`
## P15 Theme
C-5 Events / Outbox Consumer Runtime Slice（补齐异步执行层：claim → execute → record outcome → bounded retry → terminal failure）。
## Implementation scope（IN）
`apps/worker/**`（专用 consumer 入口）· `services/**` 新增 consumer service/use-case（不改既有 service 语义）· consumer infrastructure（claim/lease/heartbeat/retry/idempotency/observability）· 对应测试（allowlist 逐文件）。
## Contract authority
`P15_EVENT_OUTBOX_CONSUMER_IMPLEMENTATION_CONTRACT.md`（**FROZEN**）：23 节 + §24 O-1…O-6 冻结值。PDL 附录 R（DEC-01…06）+ 附录 S（O-1…O-6）为 canonical。
## Schema authority
`Schema Decision = RESOLVED FOR CURRENT SCOPE`：使用现有 `events` / `events_202609`（status 4 态 · worker_id · claimed_at · lease_expires_at · attempts≤100 · next_attempt_at · last_error · delivered_at · ix_events_dispatch）。**禁 0018 / 新表 / 新列 / 新索引 / 新触发器 / 新函数 / 新 enum**；不足 ⇒ SCHEMA CHANGE REQUIRED → 停止。
## Security authority
沿用继承边界：uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 · uap_migrator 245 · default_acl 0。Worker DB 身份 = **uap_runtime**；禁止 GRANT/REVOKE/新 principal；授权不足 ⇒ STOP · SECURITY IMPLEMENTATION GATE REQUIRED。
## Authorization authority
继承 P14 Stage 2；**不新增 subject/action/role/permission/effect**；actor = 事件 originating actor；需用户授权的 use-case 必须过 Stage 2；若必须新增 subject ⇒ STOP · AUTHORIZATION DECISION REQUIRED。
## Worker boundary
负责：claim eligible item → execute bounded use-case → record outcome → bounded retry → 按 policy 停止。不负责：auth/login/enrollment/session/policy/vocabulary/schema/migration/arbitrary SQL/business rule invention。与 `apps/api` 并列（均只做 adaptation + 调 use-case）。
## Repository boundary
读取必须走 `services/reads.SafeReader`（D-01 defective helper 禁止使用）；worker 不拥有事务所有权。
## Service / use-case boundary
use-case 拥有事务边界（沿用 P14 DC-16/17/18）；状态推进与业务副作用**同一事务**；handler 无 SQL、不做授权决策。
## Test strategy
见 `P15_ACCEPTANCE_MATRIX_PREP.md`（25 类别 · 设计冻结）。执行治理：CF-C-4 逐文件 allowlist · 禁目录级 pytest · integration/security 测试用 `UAP_RUNTIME_TEST_DSN` · 审计用 delta 断言。
## Execution governance
Wave 1（211 含 D-02 历史记录）+ Wave 2（72）回归必须保持 PASS；正式库 `uap` 只读且 prestate == poststate；测试库边界锚点不变。
## Forbidden changes
worker/consumer 代码以外的一切越界：schema/migration/DDL/DML/GRANT/REVOKE/ROLE/principal/authorization 词表/API 端点/P14 修改/commit/tag/push/P16+。
## Implementation entry conditions（全部满足才可开始）
```text
Decision Completion = PASS · Implementation Contract = FROZEN · Acceptance Matrix = FROZEN ·
Security Contract = FROZEN · Schema Contract = FROZEN · Worker Contract = FROZEN
⇒ 五/六项均已满足；但 P15 IMPLEMENTATION 仍需 Human 的显式 implementation 授权
```
**END OF P15 IMPLEMENTATION PREP（2026-09-28 · PREP = PASS · P15 IMPLEMENTATION = NOT AUTHORIZED · HARD STOP ACTIVE）**
