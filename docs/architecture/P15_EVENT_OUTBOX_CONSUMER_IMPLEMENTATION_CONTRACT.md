# UAP — P15 EVENT / OUTBOX CONSUMER IMPLEMENTATION CONTRACT

> 轮次 = P15 IMPLEMENTATION CONTRACT PREP → **FINALIZATION**（2026-09-28）· 状态 = **CONTRACT FROZEN**
> 冻结依据 = PDL 附录 S（O-1…O-6 FROZEN）· 全文对 OPEN DECISION 的引用一律以 §24 FROZEN 值为准
> OPEN DECISIONS = 0 · UNKNOWN = 0 · MAYBE = 0 · TBD = 0
> 依据 = PDL 附录 R（P15-DEC-01…06 FROZEN）· P14 release baseline（0.1.10 · commit 15feebad）
> 权限声明：本 Contract ≠ Implementation Authorization ≠ Migration Authorization ≠ Release Authorization

## 1. Purpose
P15 补齐"事件已产生但无受控、可靠、可观测、可重放受限、具幂等语义的 Consumer 执行层"。目标是在 0017 既有 events(outbox) 之上提供**claim → execute → record outcome → bounded retry → terminal failure** 的执行层，且不改变 P14 已验收边界。

## 2. Scope
IN：event discovery · eligibility · claiming · consumer execution · idempotency · retry · failure state · observability · authorization context · transaction boundary。
IN（实现载体）：`apps/worker/**`（专用 consumer 入口）· `services/**` 新增 consumer service/use-case · `infrastructure/**` 仅复用（不新 engine）。
NOT IN：frontend · AI feature activation · admin console · bootstrap CLI · D-01 repair · /ready redesign · audit redesign。

## 3. Non-goals
- 不新增 schema 对象（table/column/index/constraint/trigger/function/enum/status）。
- 不新增 role/grant/principal/RLS/default ACL。
- 不新增 authorization action/subject type/role/permission/effect。
- 不实现 dead-letter queue / manual replay / scheduled recovery（未来能力，须独立登记）。
- 不把 operational event 自动写成 audit row。

## 4. Event lifecycle
events.status 为持久化状态机（0017 约束 ck_events_status）：`pending → claimed → delivered`，失败路径 `claimed → pending`（bounded retry）或 `claimed → dead`（terminal）。
Producer 侧：event 由既有 use-case 通过 events INSERT 产生（P10 schema）；`pending` 为初始态；`occurred_at` + `id` 为非空无默认列 ⇒ 由 producer 显式提供。
Consumer 侧仅通过以下转移推进状态（同一事务内）：claim（pending→claimed）· success（claimed→delivered）· retry（claimed→pending，attempts+1，next_attempt_at 前推）· terminal（claimed→dead）。

## 5. Outbox lifecycle
outbox = events 表本身（P10 已建 outbox substrate）；无第二套事件模型（禁止并行 outbox 表）。
投递语义 = at-least-once + consumer 侧幂等（见 §8）。
`delivered_at` 仅在 durable success 后写入；`last_error` 仅记录脱敏后的失败摘要（不得含 secret）。

## 6. Worker boundary
Worker 负责：claim eligible item → execute bounded use-case → record outcome → handle retryable failure → 按 bounded policy 停止重试。
Worker 不负责：authentication · interactive login · identity/device enrollment · session creation · policy definition · authorization vocabulary · schema ownership · DB migration · arbitrary SQL · business rule invention。
Worker 边界与 P14 `apps/api` 边界**并列**（两者都只做 adaptation + 调 use-case）· 不得复用 API handler 逻辑。

## 7. Claim semantics
eligibility = `status='pending'` AND (`next_attempt_at IS NULL` OR `next_attempt_at <= now()`)；由既有索引 `ix_events_dispatch (status, next_attempt_at) WHERE status IN ('pending','claimed')` 支撑。
claim = 单条 UPDATE（同事务）：`SET status='claimed', worker_id=:wid, claimed_at=now(), lease_expires_at=now()+lease`
  `WHERE id=:eid AND occurred_at=:ts AND status='pending' AND (next_attempt_at IS NULL OR next_attempt_at<=now())`
  ⇒ 以受影响行数判定是否真正获得所有权（rowcount=1 才继续）。
lease 回收（OPEN DECISION O-1）：`claimed` 且 `lease_expires_at < now()` 的条目如何回到可 claim 状态 —— 需冻结为：(a) 回收为 `pending`（attempts 不变或 +1）· (b) 记为 `dead` · (c) 交由人工。**当前未冻结 ⇒ OPEN DECISION**。

## 8. Idempotency contract
必须冻结以下身份：event identity = `(id, occurred_at)`（= 主键）· delivery identity = 每次 claim 的 `(worker_id, claimed_at)` · attempt identity = `attempts` 计数 · consumer identity = `worker_id` · deduplication key = `(id, occurred_at, event_type, schema_version)`。
processing state = `status` · success state = `delivered` + `delivered_at` · retryable failure = 回到 `pending` 且 attempts 增加 · terminal failure = `dead`。
硬要求：同一 Event 被重复 delivery 时**不得产生不可接受的重复业务副作用**。因 events 表**无 processed/consumed 标记列**（只读核验结论），consumer 侧幂等必须由"业务副作用本身的幂等键"承担；若某 use-case 无法做到天然幂等 ⇒ 该 use-case **不得**纳入 P15 首批 consumer 范围（或需 OPEN DECISION 处理）。

## 9. Retry contract
retryable：连接/超时等瞬态基础设施失败（P14 Error Taxonomy 的 connection/persistence 类）。
non-retryable：authentication / authorization / security boundary / credential / validation / constraint（含 unique violation）失败（沿用 P14 NEVER_RETRY 语义与"安全失败绝不重试"）。
max attempts：`ck_events_attempts` 约束 attempts ≤ 100；P15 必须自设更小上界（建议值待冻结，见 OPEN DECISION O-2）。
backoff：`next_attempt_at = now() + backoff(attempts)`（具体曲线待冻结，见 O-2）。
terminal：达到上界后置 `dead` 并记录 `last_error`（脱敏）。
禁止：infinite retry · unbounded loop · 无限重试凭据失败 · 重试永久性校验错误。

## 10. Failure contract
顺序固定：read → validate → authorize → execute use-case → persist outcome。
失败必须：fail closed（不确定 ⇒ 不执行）· 需要时 rollback · 记录可观测结果（operational log + metrics；审计仅按既有语义）。
禁止：half-commit · swallow error · 在 durable 完成前标记 success · 无契约的情况下在非幂等部分副作用后重试。

## 11. Transaction contract
沿用 P14 规则：use-case 拥有事务边界（DC-16）· repository 不自行提交 · 事务由 `RuntimeDatabase.transaction()` 提供。
每个事件的处理 = 一个（或明确划分的多个）事务；状态推进与业务副作用必须**同一事务**，避免"副作用已提交但状态未推进"。

## 12. Authorization contract
Consumer 不得绕过 P14 authorization。每个可执行 use-case 必须回答：actor 是谁 · authorization context 是什么 · 执行哪个 use-case · 需要什么 permission · 适用哪些 ownership/tenant/space 检查。
"后台 Worker ≠ 天然拥有全部权限"。worker actor semantics 需明确（OPEN DECISION O-3）：现有 `SUBJECT_TYPES = (USER, ROLE, AGENT)`；若需要 system/service/platform actor 新语义 ⇒ **STOP · AUTHORIZATION DECISION REQUIRED**（不得自行创造 subject model）。

## 13. Tenant / space contract
继承 P14：`no tenant context → no cross-tenant execution`；`ambiguous context → deny / explicit resolution`。
禁止：random tenant selection · implicit global scope · cross-tenant fallback。
event 的 `tenant_id` / `space_id` 为可空列 ⇒ 缺失时必须 DENY（而非全局执行）。

## 14. Audit contract
`audit_logs` append-only（tg_audit_immutable）：不得 DELETE / UPDATE / truncate / cleanup。
Consumer 行为若需新 audit semantics ⇒ 先形成 decision（不得直接扩充 audit vocabulary）。
operational ≠ audit：每次 claim/attempt/retry 不得自动写 audit row。

## 15. Observability contract
继承 P14：correlation/request ID（适用处）· 结构化 operational logs · metrics · trace hooks · 无 secret · operational ≠ audit。
至少识别：event received · claim attempt · execution started · execution success · execution denied · execution retry · execution terminal failure。
日志字段沿用 P14 白名单（不得含 payload 原文中的敏感材料；`payload` 为 jsonb ⇒ 仅记录脱敏摘要与 correlation_id）。

## 16. Security boundary
Worker DB 身份必须为 **uap_runtime**（已冻结边界 · 51 row-grants）。不得使用 uap_migrator / uap_bootstrap / broad DB owner / superuser。
若现有 uap_runtime 授权不足（只读核验：events 已具 S/I/U；无 DELETE）⇒ **不得直接 GRANT**，必须登记 `SECURITY DECISION REQUIRED` 并停止。
D-01（DEC-04）：读取必须走 `services/reads.SafeReader`（approved path）；若无法避开 defective helper ⇒ STOP · FOUNDATION CHANGE REQUIRED。

## 17. Persistence boundary
0017 = persistence truth。只读核验结论：**现有 events 表已具备 consumer 所需全部字段与索引**（status/worker_id/claimed_at/lease_expires_at/attempts/next_attempt_at/last_error/delivered_at + ix_events_dispatch），且 events / events_202609 行数均为 0。
⇒ **NO SCHEMA CHANGE REQUIRED**（若实现期发现不足 ⇒ SCHEMA CHANGE REQUIRED → 立即停止 Implementation Prep，不得创建 0018）。
Domain ↔ Persistence 词表差异必须经显式 mapping（services/mapping）· 禁隐式 cast。

## 18. API boundary
P15 **不新增任何 API 端点**（API = transport/adaptation；consumer 不经 HTTP）。
若未来需要操作面（查看 dead letter / 手工重放）⇒ 独立 Decision（本轮不实现）。

## 19. Concurrency model
同一事件同一时刻至多一个 owner（由 §7 的条件 UPDATE + rowcount 判定）。
多 worker 并行仅按"不同事件"并行；**不引入** work-stealing / 分布式协调器 / 第二套锁机制（P14 既有 advisory lock 仅用于 migration，不属于 runtime）。
同一 tenant 的并发度、单 worker 的批量大小 = 部署参数（OPEN DECISION O-4）。

## 20. Shutdown semantics
graceful shutdown：停止 claim 新事件 → 等待在途 use-case 结束（有上界）→ 释放 lease（见 O-1 的回收策略）→ dispose RuntimeDatabase（沿用 Wave 1 `RuntimeApplication.stop()`）。
禁止：强制中断 DB 连接 · 泄漏 pool · 静默忽略 shutdown 失败。

## 21. Recovery semantics
崩溃恢复依赖 lease 过期 + 回收策略（O-1）。
"worker 在副作用后崩溃"的处理必须由 §8 的幂等契约承担（重复 delivery 不得产生不可接受副作用）。
DB 不可用：不 claim、不执行；按 bounded retry（若属瞬态）；不得降级执行。

## 22. Acceptance criteria
见 P15_ACCEPTANCE_MATRIX_PREP.md（C-5 具体化条目）：event eligibility · claim concurrency · duplicate delivery · idempotency · retry · terminal failure · transaction rollback · authorization denial · tenant/space isolation · shutdown · restart · DB unavailable · observability · audit semantics · regression · 以及 schema/privilege/DB 无变更检查。

## 23. Forbidden changes
新增 schema 对象 · migration（0018+）· new role/grant/revoke/principal/RLS/default ACL · 修改 Stage 2 或 12 canonical actions · 修改 C2/CC-7/P13 seed · 修改 P14 实现或 release commit/tag/payload · 修改 D-01 冻结文件 · 修改 /ready 与 health contract · 新增 API 端点 · 实现 dead-letter/manual replay · 启动 P16+。

## §28 契约必须回答的问题（对齐检查）
1. Who creates event? → 既有 use-case（producer），经 events INSERT（§4）。
2. Who owns event? → 平台（events 表为平台 outbox）；无 per-event owner 列（§5）。
3. When eligible? → status=pending 且 next_attempt_at 到期（§7）。
4. How claim? → 条件 UPDATE + rowcount=1（§7）。
5. How two workers avoid duplicate claim? → 条件 UPDATE 的原子性 + 状态守卫（§7/§19）。
6. Worker crashes after side effect? → 依赖幂等契约 + lease 回收（§8/§21 · O-1）。
7. What makes retry safe? → 幂等键 + non-retryable 分类（§8/§9）。
8. What makes an operation terminal? → 达到 attempts 上界 ⇒ `dead`（§9）。
9. How duplicate delivery detected? → 主键身份 + 业务幂等键（§8）。
10. How tenant/space preserved? → 缺失即 DENY，禁跨租户/隐式全局（§13）。
11. During shutdown? → §20。
12. When DB unavailable? → 不 claim/不执行 + bounded retry（§21）。
13. When use-case fails? → 按 §9/§10 分类并记录（rollback + 状态推进）。
14. How worker authenticate/authorize? → OPEN DECISION O-3（不得创造新 subject）。
15. How operational and audit separated? → operational 走 logs/metrics；audit 仅按既有语义（§14/§15）。

## 24. FROZEN RESOLUTIONS（O-1…O-6 · PDL 附录 S）
O-1 Lease Recovery = FROZEN：`claimed AND lease_expires_at < now()` ⇒ attempts<10 → pending（worker_id/claimed_at/lease_expires_at 置 NULL · **attempts 不变** · 保留 last_error 诊断）；attempts>=10 → dead（reason=`lease_expired_max_attempts`）。claim/recovery 一律条件 UPDATE + rowcount 检查（rowcount=0 ⇒ 不假设所有权、不执行）。禁止 claimed→claimed 无限占租、禁止未重新 claim 即执行。
O-2 Attempts / Backoff = FROZEN：MAX_ATTEMPTS=**10**（DB 硬上限 100 保留）；退避 = 确定性指数 base 5s ×2 cap 10min（5/10/20/40/80/160/320/640/600…）；attempt 10 失败 ⇒ dead；**无 jitter**；禁 infinite/random 重试。
O-3 Worker Actor = FROZEN：**不新增 subject vocabulary**（禁 system/service/platform/worker/consumer；保持 user/role/agent）；actor provenance = 事件**originating actor**；禁止 NULL actor 升级为 platform_admin、禁止借用 uap_bootstrap/uap_migrator；需用户授权的 use-case 必须 original actor valid ∧ tenant valid ∧ space valid ∧ ownership/membership valid ∧ Stage2 allows；actor 无效 ⇒ deny；若某 use-case 必须新增 subject ⇒ STOP · AUTHORIZATION DECISION REQUIRED。
O-4 Concurrency = FROZEN：worker=1 · concurrency=4 · batch≤10 · lease=120s · heartbeat=40s；claim atomic/conditional/bounded（禁 SELECT many → 逐个 UPDATE；ownership 由 DB 原子条件保证）；heartbeat 仅当 status=claimed ∧ worker_id=current ∧ lease 未终局过期才延长；rowcount≠1 ⇒ 失去所有权 ⇒ 必须安全停止执行；shutdown = stop claiming → 完成有界操作 → 持久化结果 → 释放所有权 → exit；hard crash 走 O-1。
O-5 Event Whitelist = FROZEN：**CLOSED ALLOWLIST**（禁 `*`/`%`/unknown/auto-discover/dynamic import）；只读证据显示仓库**无 event producer 代码**、events 行数 0、distinct event_type 0 ⇒ **ALLOWLIST = EMPTY（合法）**：P15 先实现 consumer infrastructure/claim/lease/retry/idempotency/observability，**不启用任何生产 handler**，不得创造 fake business event type；注册仅 code-level explicit mapping（禁 DB 动态注册）；未知类型 ⇒ dead · reason=`unsupported_event_type`。
O-6 Idempotency Exclusion = FROZEN：默认排除无法证明幂等的 use-case；可执行者须满足 A naturally idempotent ∨ B transactional idempotency key ∨ C existing schema 已保证 dedup/uniqueness；无法证明 ⇒ NOT ELIGIBLE；key 优先 `event_id`（更细粒度 = event_id + operation identity，须在 handler contract 显式定义）；禁 timestamp / retry 期随机 UUID / worker_id 作 duplicate identity。

**END OF P15 EVENT / OUTBOX CONSUMER IMPLEMENTATION CONTRACT（2026-09-28 · **CONTRACT FROZEN** · O-1…O-6 已冻结 · OPEN DECISIONS = 0 · 未实施 · HARD STOP ACTIVE）**
