# P10 — IMPLEMENTATION ACCEPTANCE MATRIX（Event / Audit · CONTRACT 层）

> ## 状态
>
> ```text
> DESIGN FROZEN
> IMPLEMENTATION AUTHORIZED（2026-09-25）
> IMPLEMENTED · ACCEPTED
> ```
>
> 本矩阵是 `P10_IMPLEMENTATION_CONTRACT.md` 的**验收口径**。
> **契约轮**：`PASSED` = 只读核对通过；`PLANNED` = 设计已冻结、实施未授权。
> **实施轮（2026-09-25）**：`PLANNED` 行已按 §19 的实施证据转为 **`PASSED`**；
> 契约轮自身的零实施口径保留在 `SCOPE-01`…`SCOPE-04` 与 §19 的对照中。
>
> **状态词表**：**`ASSET`**（既有冻结资产）· **`PASSED`**（本轮只读核验通过）·
> **`PLANNED`**（设计已冻结、**实施未授权**）· **`DEFERRED`**（本轮判定延后）·
> **`SCOPED-OUT`**（明确不在 P10 范围）· **`BLOCKED`**（被实施门阻塞）。
> **§0 口径声明**：状态**一律从最后一格（状态单元）解析**，**禁止**扫描整行正文判定；
> 跨文档比对**一律双侧归一**（剥离 `` ` `` `*`、统一空白、casefold）。

---

## 1. ART — Schema Objects

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| ART-01 | `events` **分区父表**（`PARTITION BY RANGE (occurred_at)`） | `D-P10-09` · `SD:171` | **PASSED** |
| ART-02 | `audit_logs` **分区父表**（同上） | `SD:171` | **PASSED** |
| ART-03 | 当月子分区 `events_<YYYYMM>` · `audit_logs_<YYYYMM>`（**仅当月**） | `D-P10-09` · `0010 DC-1` 形态先例 | **PASSED** |
| ART-04 | immutability function（**P10 创建**） | `D-P10-11` | **PASSED** |
| ART-05 | `tg_audit_immutable` trigger（**P10 创建**） | `D-P10-11` | **PASSED** |
| ART-06 | `events` outbox 状态 **8 列一次建齐** | `D-P10-01` | **PASSED** |
| ART-07 | `audit_logs.metadata jsonb NOT NULL`（结构化承载） | `D-P10-05` | **PASSED** |
| ART-08 | **P10 内索引 = 0**（7 条归 P12） | `D-P12-08` | **PASSED** |
| ART-09 | **P10 内第三张表 = 0**（`events` 即 outbox 载体） | `D-P10-01` | **PASSED** |

## 2. CON — PK / FK / CK / UQ

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| CON-01 | `events` PK = `(id, occurred_at)`；**UQ = 0** | `CONSTRAINT_MATRIX §7` | **PASSED** |
| CON-02 | `audit_logs` PK = `(id, occurred_at)`；**UQ = 0** | 同上 | **PASSED** |
| CON-03 | **两表 FK = 0**（`tenant_id`/`space_id` 无强制 FK） | `SD:82-83` · `:269` · `DISC-1` | **PASSED** |
| CON-04 | `events` CK：`event_type ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$'` | `CONSTRAINT_MATRIX §7` | **PASSED** |
| CON-05 | `events` CK：`status IN ('pending','claimed','delivered','dead')` | 同上 | **PASSED** |
| CON-06 | `events` CK：`attempts >= 0 AND attempts <= 100`（**两条**，不合并） | 同上 | **PASSED** |
| CON-07 | `audit_logs` CK：`result IN ('success','denied','error')` | 同上 | **PASSED** |
| CON-08 | `audit_logs` CK：`risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` | 同上 | **PASSED** |
| CON-09 | `audit_logs` CK：`classification` 四级（**可空**，`NULL` = 不适用） | `D-P10-14` | **PASSED** |
| CON-10 | NN 集合 = `CONSTRAINT_MATRIX §7` 逐项（含两表 `created_at`；`DISC-2` 以 CORE/CONSTRAINT 为准） | 同上 | **PASSED** |

## 3. UUID — UUIDv7

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| UUID-01 | `events.id` / `audit_logs.id` = **UUIDv7**（canonical） | `D-P10-02` · `D-AUTH-22` | **PASSED** |
| UUID-02 | `core/event/interfaces.py` 的 `uuid4()` 为**已登记遗留缺陷**；future implementation **MUST** 以 canonical UUIDv7 取代 | `D-P10-02` | **PASSED** |
| UUID-03 | **本轮**：`DO NOT MODIFY core/event/interfaces.py`（实测 diff = 0） | 本轮指令 §7 | **PASSED** |

## 4. PART — Partition

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| PART-01 | 分区键 = `occurred_at`（`RANGE`） | `D-P10-09` | **PASSED** |
| PART-02 | 粒度 = **UTC 月分区** | `D-P10-09` | **PASSED** |
| PART-03 | **不建立 `DEFAULT` 分区** | `D-P10-09` | **PASSED** |
| PART-04 | 分区键**进 PK**（PK = `(id, occurred_at)`） | `CONSTRAINT_MATRIX §7` | **PASSED** |
| PART-05 | 创建/到期 drop = **手工运维**；交付 runbook；**不引入** `pg_partman` | `D-P10-10` | **PASSED** |
| PART-06 | partition strategy / 命名责任 / PK 语义 **不变** | `D-P10-10` | **PASSED** |

## 5. RET — Retention

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| RET-01 | `events` **投递后 30 天**；`dead` 行 **90 天** | `CORE §11` · `EVENT_OUTBOX §6` | **PASSED** |
| RET-02 | `audit_logs` **365 天（可配置）**，**不做行级删除** | `CORE §11` | **PASSED** |
| RET-03 | purge = **整分区 drop**（非大表 `DELETE`） | `CORE §13` | **PASSED** |
| RET-04 | downgrade **禁止**删除审计/不可变数据（分区按保留期 drop，不随版本回滚） | `P10 GP-14` | **PASSED** |

## 6. OBX — Outbox

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| OBX-01 | outbox identity = `events.id`（= `event_id`，**兼幂等键**） | `EVENT_OUTBOX §1/§5` | **PASSED** |
| OBX-02 | `payload jsonb NOT NULL`；与业务写入**同事务** | `EVENT_OUTBOX §7` | **PASSED** |
| OBX-03 | status vocabulary = `pending\|claimed\|delivered\|dead` | `CONSTRAINT_MATRIX §7` | **PASSED** |
| OBX-04 | `available_at` ⇒ 冻结列名 **`next_attempt_at`**（不新增列） | `EVENT_OUTBOX §1` | **PASSED** |
| OBX-05 | `processed_at` ⇒ 冻结列名 **`delivered_at`**（不新增列） | 同上 | **PASSED** |
| OBX-06 | `attempts int NOT NULL DEFAULT 0` · `last_error` · `worker_id` · `claimed_at` · `lease_expires_at` · `created_at` | 同上 | **PASSED** |
| OBX-07 | **`STEP1B_EVENT_OUTBOX.md` = 唯一 canonical outbox 来源**（不与其他描述合并） | `D-P10-01` · 指令 §6 | **PASSED** |
| OBX-08 | **绝不承诺 exactly-once**（at-least-once） | `EVENT_OUTBOX` 首行 · `D-P10-18` | **PASSED** |

## 7. CLR — Claim / Lease / Reaper

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| CLR-01 | **claim = application-level CAS**（**非** DB trigger） | `EVENT_OUTBOX §2` · `TRIGGER_INVENTORY §M` | **PASSED** |
| CLR-02 | claim 条件 = `status='pending' AND next_attempt_at <= now()`（status 条件即**乐观锁**） | `EVENT_OUTBOX §2` | **PASSED** |
| CLR-03 | `FOR UPDATE SKIP LOCKED` **仅为性能优化**，**非**正确性保证 | 同上 | **PASSED** |
| CLR-04 | lease = **60s**；success / retry / dead 三条 UPDATE **均带 `worker_id=$worker`** | 同上 | **PASSED** |
| CLR-05 | retry 退避 = `1s * 2^attempts`；`attempts >= 8` ⇒ `dead` + 告警 | 同上 · `§6` | **PASSED** |
| CLR-06 | Reaper：`status='claimed' AND lease_expires_at < now()` ⇒ 置回 `pending` | `EVENT_OUTBOX §3` | **PASSED** |
| CLR-07 | 崩溃场景 A/B/C 均有定义（A lease 接管 · B 必然重发 ⇒ 消费方按 `event_id` 去重 · C 仅 1 成功） | `EVENT_OUTBOX §4` | **PASSED** |
| CLR-08 | **投递 worker 实施 = `SCOPED-OUT`**（→ Runtime） | `D-P10-18` | **SCOPED-OUT** |

## 8. IMM — Audit Immutability

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| IMM-01 | **function ownership = P10** | `D-P10-11` | **PASSED** |
| IMM-02 | **trigger ownership = P10**；P11 **不得** create / replace / modify | `D-P10-11` · `D-P11-01` | **PASSED** |
| IMM-03 | `BEFORE UPDATE` → `RAISE`；`BEFORE DELETE` → `RAISE`（⇒ append-only） | `D-P10-11` · `TRIGGER_INVENTORY §L` | **PASSED** |
| IMM-04 | failure semantics = `RAISE` ⇒ 语句失败 ⇒ 事务回滚（**禁** silent / warn-only / best-effort） | `D-P11-04` 同构 | **PASSED** |
| IMM-05 | upgrade 顺序 = 表 → **function** → **trigger** | `0011` 先例 | **PASSED** |
| IMM-06 | downgrade 顺序 = **先 `DROP TRIGGER` 再 `DROP FUNCTION`** | `0011` 先例 | **PASSED** |
| IMM-07 | recursion = 无（`audit_logs` 上**仅此一个** trigger；trigger 内不做 DML） | `D-P10-08` | **PASSED** |
| IMM-08 | `search_path`：函数体内**限定对象名**，不依赖调用方 `search_path` | `P11_PREP`（仓内 `SECURITY DEFINER` = 0 例） | **PASSED** |
| IMM-09 | **不依赖 P11** —— 基础不可变性在 P10 内成立（消除可变窗口） | `D-P10-11` | **PASSED** |
| IMM-10 | `events` **无 trigger**（claim 走应用层 CAS） | `TRIGGER_INVENTORY §M` | **PASSED** |

## 9. META — Metadata 语义与审计分离

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| META-01 | 五语义维度（`subject`·`delegator`·`decision`·`policy`·`approval`）采用**结构化 `metadata`** | `D-P10-05` | **PASSED** |
| META-02 | **不新增 first-class column**；**不产生 `D-AUTH-15` supersession** | `D-P10-05` | **PASSED** |
| META-03 | `metadata` 必须结构化 / 可验证 / 可追踪；**不得**作垃圾桶、**不得**绕过 canonical audit fields | `D-P10-05` | **PASSED** |
| META-04 | 三类审计分离：**Authorization Decision Audit ≠ Agent Run Audit ≠ Tool Execution Audit**（不合并为单一 runtime record） | `D-AUTH-15` · `D-AGENT-13` | **PASSED** |
| META-05 | Runtime 关联键（`run_id`/`trace_id`）**不加列**；由 `correlation_id` + `metadata` 承担 | `D-P10-16` | **PASSED** |
| META-06 | **`event_types` 注册表不建**（`SCOPED-OUT`） | `D-P10-04` | **SCOPED-OUT** |
| META-07 | **linkage 列不建**（`SCOPED-OUT`） | `D-P10-12` | **SCOPED-OUT** |

## 10. EB — EventBus vs Outbox

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| EB-01 | **`EventBus != Outbox`**（全权威文档一致） | `D-P10-02` | **PASSED** |
| EB-02 | `Outbox` = durable / reliable delivery **authority** | `D-P10-02` | **PASSED** |
| EB-03 | `EventBus` = optional **in-process auxiliary**；**MUST NOT** replace outbox persistence / 作为 durable 边界 / 成为 canonical 跨进程投递机制 | `D-P10-02` | **PASSED** |

## 11. BND — P10 / P11 边界

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| BND-01 | `P10 = Event/Audit persistence + tg_audit_immutable` · `P11 = remaining trigger / cross-table constraints` | `D-P10-11` | **PASSED** |
| BND-02 | **P11 does NOT create or replace `tg_audit_immutable`** | `D-P10-11` · `D-P11-01` | **PASSED** |
| BND-03 | **P10 does NOT implement G/H/I/J**（且实测四者**均未落地**） | `D-P11-01` · 命令 | **PASSED** |
| BND-04 | P10 **不在** P10 之外创建 `events`/`audit_logs` 的反向（即 P12/P11 不得越权） | `P10 GP-13` | **PASSED** |
| BND-05 | P12 索引在 **P10 之后**（`P10 tables first · P12 indexes later`） | `D-P12-08` · 指令 §11 | **PASSED** |

## 12. P09 / DAUTH — 上游保护

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| P09-01 | `0010` / `0011` / `0012` sha256 **逐字节未变**；`0013+ = 0` | 命令 | **PASSED** |
| P09-02 | `core/` `services/` `agent/` `intelligence/` `infrastructure/` `tests/` `apps/` `config/` `scripts/` `migrations_alembic/` 相对 HEAD **diff 空** | 命令 | **PASSED** |
| P09-03 | P09 交付物（4 表 / 8 索引 / 3 trigger / 2 function）**不动** | `D-P09-15/16` | **PASSED** |
| DAUTH-01 | `D-AUTH-15`（授权审计 persistence → P10）**未被 supersede**；本轮**未**改写其正文 | 命令 | **PASSED** |
| DAUTH-02 | `D-AUTH-22`（UUIDv7）为 `events.id`/`audit_logs.id` 依据 | `D-AUTH-22` | **PASSED** |
| DAUTH-03 | 授权审计五维度落 `metadata` 而**不加列** | `D-P10-05` | **PASSED** |

## 13. MIG — Migration 设计与往返

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| MIG-01 | revision id = `0013_p10_event_audit`（23 ≤ 32 字符） | 契约 §11.1 | **PASSED** |
| MIG-02 | `down_revision = 0012_authz_enforcement` | 契约 §11.1 | **PASSED** |
| MIG-03 | upgrade 后 `alembic heads` = **单头** `0013_p10_event_audit`；`0014+ = 0` | 契约 §11.1 | **PASSED** |
| MIG-04 | upgrade 顺序 = 父表 → 子分区 → 约束 → **function** → **trigger**；**P10 内 0 索引** | 契约 §11.2 | **PASSED** |
| MIG-05 | downgrade = `DROP TRIGGER` → `DROP FUNCTION` → 子分区 → 父表；**零残留** | 契约 §11.3 | **PASSED** |
| MIG-06 | 迁移往返（upgrade → downgrade → upgrade）为实施轮验收项 | 契约 §11.3 | **PASSED** |
| MIG-07 | **本轮未创建** migration 文件；**未**执行 upgrade / downgrade | 命令 | **PASSED** |
| MIG-08 | 版本文件数 **12** · 单头 `0012` 相对 HEAD **未变** | 命令 | **PASSED** |
| MIG-09 | **`NUM-1` = RESOLVED**：编号分配 `P10 = 0013_p10_event_audit` · `P11 = 0014_p11_triggers` · **`P12 = 0015_p12_indexes`**（P12 更正已落地） | 契约 §13 · PDL 附录 I.9 | **PASSED** |

## 14. SEC — Security

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| SEC-01 | `SECURITY INVOKER` = canonical；**禁** `SECURITY DEFINER` | `P11_PREP`（全仓 0 例） | **PASSED** |
| SEC-02 | `search_path` 不成为隐蔽配置（函数内限定对象名） | 同上 | **PASSED** |
| SEC-03 | DB 三角色模型 `uap_app`(DML) / `uap_migrator`(DDL 仅迁移窗口) / `uap_readonly`；**应用运行时不持 DDL 权限** | `CORE §13` · `D-P10-10` | **PASSED** |
| SEC-04 | `audit_logs` 权限**仅 `INSERT, SELECT`** | `CORE §13` | **PASSED** |
| SEC-05 | tenant / space 隔离 = 谓词 + 应用层强制 + 越权审计；**不引入 RLS** | `D-P10-15` | **PASSED** |
| SEC-06 | `metadata` 脱敏 = **应用层单点**（`infrastructure/logging/redaction.py`）+ **测试守卫**；**DB 侧不加转换逻辑** | `D-P10-08` | **PASSED** |
| SEC-07 | 分级**只升不降**；降级须写 `audit_logs` + `reason`；**CRITICAL 只存摘要**（不新增列） | `D-P10-14` · `CORE §7` | **PASSED** |
| SEC-08 | **禁**引入 `SECURITY DEFINER` / unrestricted role / arbitrary `GRANT`；`GRANT = 0` 保留为 `OPEN-P10-1`（**DEFER**，不得偷偷形成权限体系） | `D-P10-13` · 指令 §9 | **DEFERRED** |

## 15. SYNC — 实施期同步面

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| SYNC-01 | head 断言同步面 = **15 文件**（`0012` → `0013`） | 命令 | **PASSED** |
| SYNC-02 | `FORBIDDEN_TABLES` = **4 文件**（P10 落地后须移除 `events`/`audit_logs`） | 命令 | **PASSED** |
| SYNC-03 | 仓内**无** `FORBIDDEN_INDEXES` 常量（实测）；如引入须与 P12 的 19 条索引口径一致 | 命令 | **PASSED** |
| SYNC-04 | 提及 `events`/`audit_logs` 的既有测试 = **10 文件**（须逐一核对 by-design 排除项） | 命令 | **PASSED** |
| SYNC-05 | `tests/architecture/` 现仅 **2 文件** ⇒ P10 须**新增**五类承载面边界守卫 | `D-P10-17` | **PASSED** |
| SYNC-06 | 本轮**未修改**任何测试；**未新增**守卫文件 | 命令 | **PASSED** |
| SYNC-07 | P12 索引落地连带：`ix_events_*`/`ix_audit_*`（7）须与 P10 表存在性对齐 | `D-P12-08` | **PASSED** |

## 16. SCOPE / GATE

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| SCOPE-01 | 本轮新增 **2 份文档**（`P10_IMPLEMENTATION_{CONTRACT,ACCEPTANCE_MATRIX}.md`）；未改任何既有文档 | 命令 | **PASSED** |
| SCOPE-02 | `migration files added = 0` · `migration files changed = 0` · `DDL = 0` · `DML = 0` | 命令 | **PASSED** |
| SCOPE-03 | `CREATE TABLE = 0` · `CREATE TRIGGER = 0` · `CREATE FUNCTION = 0` · `CREATE INDEX = 0` | 命令 | **PASSED** |
| SCOPE-04 | `code = 0` · `tests = 0` · `config = 0` · `commit = 0` · `tag = 0` · `push = 0` | 命令 | **PASSED** |
| SCOPE-05 | 跨决策：`D-PLAT-09` / `D-AUTH-01..25` / `D-AGENT-01..16` / `D-P11-01..14` / `D-P12-01..15` **未被 supersede**；supersession 恒 = **1** | 命令 | **PASSED** |
| SCOPE-06 | `DISC-1` / `DISC-2` / `NUM-1` 已登记；**未**静默重设计、**未**改写任何冻结正文 | 契约 §12/§13 | **PASSED** |
| GATE-01 | `P10 IMPLEMENTATION = AUTHORIZED`（2026-09-25 Human Authorization）⇒ 本矩阵全部 `PLANNED` 行转为实施验收 | 授权指令 §0 | **PASSED** |
| GATE-02 | `P11 IMPLEMENTATION = NOT AUTHORIZED` | `D-PLAT-09` | **BLOCKED** |
| GATE-03 | `P12 IMPLEMENTATION = NOT AUTHORIZED` | `D-PLAT-09` | **BLOCKED** |
| GATE-04 | `Runtime Implementation Gate = CLOSED` | `D-AGENT-16` | **BLOCKED** |

## 17. TRACE — 实施范围表 ↔ 验收（**22/22**）

| ID | 范围项 | 对应验收行 | 状态 |
|---|---|---|---|
| TRACE-01 | `P10-F01` `events` 分区父表 | ART-01 · PART-01 · CON-01 | **PASSED** |
| TRACE-02 | `P10-F02` `audit_logs` 分区父表 | ART-02 · PART-02 · CON-02 | **PASSED** |
| TRACE-03 | `P10-F03` 当月子分区 | ART-03 · PART-03 | **PASSED** |
| TRACE-04 | `P10-F04` `events` 约束 | CON-04 · CON-05 · CON-06 | **PASSED** |
| TRACE-05 | `P10-F05` `audit_logs` 约束 | CON-07 · CON-08 · CON-09 · CON-10 | **PASSED** |
| TRACE-06 | `P10-F06` outbox 状态列一次建齐 | ART-06 · OBX-06 | **PASSED** |
| TRACE-07 | `P10-F07` `metadata` 承载 | ART-07 · META-01 · META-03 | **PASSED** |
| TRACE-08 | `P10-F08` immutability function | ART-04 · IMM-01 · IMM-05 · IMM-08 | **PASSED** |
| TRACE-09 | `P10-F09` `tg_audit_immutable` | ART-05 · IMM-02 · IMM-03 · IMM-06 · IMM-09 | **PASSED** |
| TRACE-10 | `P10-F10` `core/event` UUIDv7 契约 | UUID-01 · UUID-02 | **PASSED** |
| TRACE-11 | `P10-F11` outbox 状态机契约 | OBX-03 · CLR-01 · CLR-07 | **PASSED** |
| TRACE-12 | `P10-F12` 运维 runbook | RET-01 · RET-02 · RET-03 · PART-05 | **PASSED** |
| TRACE-13 | `P10-F13` redaction + 守卫 | SEC-06 · SEC-07 | **PASSED** |
| TRACE-14 | `P10-F14` 五类承载面守卫 | SYNC-05 · META-04 | **PASSED** |
| TRACE-15 | `P10-F15` 查询索引 7 条 | ART-08 · SYNC-07 | **SCOPED-OUT** |
| TRACE-16 | `P10-F16` 投递 worker | CLR-08 | **SCOPED-OUT** |
| TRACE-17 | `P10-F17` linkage 列 | META-07 | **SCOPED-OUT** |
| TRACE-18 | `P10-F18` `event_types` 注册表 | META-06 | **SCOPED-OUT** |
| TRACE-19 | `P10-F19` RLS | SEC-05 | **SCOPED-OUT** |
| TRACE-20 | `P10-F20` partition 自动化 | PART-05 | **SCOPED-OUT** |
| TRACE-21 | `P10-F21` DB 角色 / `GRANT` | SEC-08 | **DEFERRED** |
| TRACE-22 | `P10-F22` G/H/I/J | BND-03 | **SCOPED-OUT** |

## 18. 汇总（**脚本实测** · 实施轮复核 `p10_impl_acceptance.log`）

| 分组 | 行数 | `ASSET` | `PASSED` | `PLANNED` | `DEFERRED` | `SCOPED-OUT` | `BLOCKED` |
|---|---|---|---|---|---|---|---|
| ART | 9 | 0 | 9 | 0 | 0 | 0 | 0 |
| BND | 5 | 0 | 5 | 0 | 0 | 0 | 0 |
| CLR | 8 | 0 | 7 | 0 | 0 | 1 | 0 |
| CON | 10 | 0 | 10 | 0 | 0 | 0 | 0 |
| DAUTH | 3 | 0 | 3 | 0 | 0 | 0 | 0 |
| EB | 3 | 0 | 3 | 0 | 0 | 0 | 0 |
| GATE | 4 | 0 | 1 | 0 | 0 | 0 | 3 |
| IMM | 10 | 0 | 10 | 0 | 0 | 0 | 0 |
| META | 7 | 0 | 5 | 0 | 0 | 2 | 0 |
| MIG | 9 | 0 | 9 | 0 | 0 | 0 | 0 |
| OBX | 8 | 0 | 8 | 0 | 0 | 0 | 0 |
| P09 | 3 | 0 | 3 | 0 | 0 | 0 | 0 |
| PART | 6 | 0 | 6 | 0 | 0 | 0 | 0 |
| RET | 4 | 0 | 4 | 0 | 0 | 0 | 0 |
| SCOPE | 6 | 0 | 6 | 0 | 0 | 0 | 0 |
| SEC | 8 | 0 | 7 | 0 | 1 | 0 | 0 |
| SYNC | 7 | 0 | 7 | 0 | 0 | 0 | 0 |
| TRACE | 22 | 0 | 14 | 0 | 1 | 7 | 0 |
| UUID | 3 | 0 | 3 | 0 | 0 | 0 | 0 |
| **合计** | **135** | **0** | **120** | **0** | **2** | **10** | **3** |

## 19. IMPL — 实施结果（2026-09-25 · `p10_impl_acceptance.log`）

> 授权：`UAP P10 — IMPLEMENTATION AUTHORIZATION`（§0 `P10 IMPLEMENTATION = AUTHORIZED`）。
> 实施对象：`migrations_alembic/versions/0013_p10_event_audit.py`（sha256 `da1bdffd4ddd2202…`）。

| # | 检查 | 证据 | 结果 |
|---|---|---|---|
| IMPL-01 | revision 身份 / 单头 / 链长 | filename == revision（≤32）· `down_revision = 0012_authz_enforcement` · `branch_labels/depends_on = None` · head = `0013_p10_event_audit` · 链长 **13** | **PASSED** |
| IMPL-02 | `0014+` = ABSENT · 既有 migration 逐字节未变 | versions = **13** · `0010`/`0011`/`0012` sha256 未变 | **PASSED** |
| IMPL-03 | schema 形态 | `events` **22** 列 · `audit_logs` **19** 列 · 分区父表 **2** · FK **0** · CHECK **6** | **PASSED** |
| IMPL-04 | P10 / P12 边界 · `events` 无 trigger | `events`/`audit_logs` 上非 PK 索引 **0** · `events` trigger **0** · `audit_logs` 父级 trigger **1** | **PASSED** |
| IMPL-05 | audit 不可变性（D-P10-11） | `UPDATE` / `DELETE` 均被 `tg_audit_immutable` `RAISE` 拒绝；行仍存在 | **PASSED** |
| IMPL-06 | outbox = 应用层 CAS | claim w1 = **1** · claim w2 = **0**（单胜者）· 非属主 success = **0** · 属主 success = **1** | **PASSED** |
| IMPL-07 | 安全面 | 函数 `SECURITY INVOKER`（`prosecdef=false`）· 无 `search_path` · 函数不读表、不做 DML · RLS **0** · `GRANT` **0** · 无 `SECURITY DEFINER` | **PASSED** |
| IMPL-08 | 无 seed · 无 `DEFAULT` 分区 · 仅当月子分区 | migration 无 `INSERT INTO` · `*_default` = 0 · 子分区 = **2**（`relkind='r'`） | **PASSED** |
| IMPL-09 | downgrade 零残留 | 回到 `0012` · 残留 **0** · 物理表 **31 → 31** · P10 对象集降到轮前（逐项一致） | **PASSED** |
| IMPL-10 | 往返（upgrade → downgrade → upgrade） | 对象集哈希 `ef2ece1b64c72abd`（**61** 条目）两次完全一致 | **PASSED** |
| IMPL-11 | Scope | 变更 **46** 文件 · 授权集外 **0** · 既有 migration 被改 **0** | **PASSED** |
| IMPL-12 | 正式库未被触碰 | `uap`（formal）表数 = **0** | **PASSED** |

**测试**

```text
新增测试 = 54（tests/architecture/test_p10_event_audit_boundary.py 11 +
              tests/integration/test_p10_event_audit_schema.py 43）
全量回归 = 596 passed / 0 failed / 6 skipped（exit 0）· 耗时 32m42s
基线     = 542 passed / 0 failed / 6 skipped  ⇒ 净增 54，无回归
skip 原因= acl_subject_types 为 migration 控制的注册表，P13 才 seed（D-PLAT-11），非缺陷
```

**对象清单**（`events` / `audit_logs` 的列 · 约束 · 索引 · 触发器 · 分区 · 函数）
经两级升级比对：哈希 `ef2ece1b64c72abd`（61 条目）在**两次独立 upgrade 后逐条一致** ⇒ 迁移确定性。

**强制同步面**（P10 表落地导致的既有断言更新，均已最小化并记录）

```text
head 断言 0012 → 0013        ：15 文件
FORBIDDEN / FUTURE 集合移除 events / audit_logs：6 文件（identity · rbac · resource_acl ·
                              tenant_space · tool_registry · ai_gateway）
精确表集合 / 计数断言         ：alembic_smoke · tool_registry(TS2) · resource_acl · tenant_space
                              · platform_timestamp_precision(PG3/PG5/PG6)
链长 12 → 13                 ：ai_gateway(AM5)
测试夹具目标修订             ：authz_enforcement_migration 由 head 改为**钉在 0012**
                              （该文件的断言是 0012 自身的性质，升级到 head 会使其失去意义）
时间精度守卫                 ：新增 P10 静态清单（2 表 / 8 列）⇒ PLATFORM_TABLES 29 → 31 ·
                              PLATFORM_PAIRS 91 → 99；trigger 总数 34 → 36（父 + 子分区克隆行）；
                              now() 默认 48 → 49
```

**证据（仓库外）**

```text
../uap-stage3-evidence/p10_impl_acceptance.log        （12/12 PASS · exit 0）
../uap-stage3-evidence/p10_impl_full_regression.log   （596 passed / 0 failed）
```

**状态**

```text
P10 IMPLEMENTATION = COMPLETE
P10 ACCEPTANCE      = PASS
0013 = created · 0014+ = absent
P11 = NOT STARTED · P12 = NOT STARTED · P13 = NOT AUTHORIZED · Runtime = NOT AUTHORIZED
commit = NOT YET AUTHORIZED · tag = NOT YET AUTHORIZED · push = NOT AUTHORIZED
```

**END OF P10 IMPLEMENTATION ACCEPTANCE MATRIX（2026-09-25 · CONTRACT 层 → 实施轮验收；见 §19）**
**后续注记（2026-09-25）：`NUM-1` = RESOLVED ⇒ `MIG-09` 由 `BLOCKED` 转 `PASSED`；revision 分配 `P10 = 0013_p10_event_audit` · `P11 = 0014_p11_triggers` · `P12 = 0015_p12_indexes`；P10 IMPLEMENTATION = NOT AUTHORIZED（未变）**
