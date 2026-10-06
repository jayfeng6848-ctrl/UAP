# P10 — DECISION RESOLUTION PACKAGE（Event / Audit）

> **状态声明（先读）**
>
> ```text
> 本文档 = DECISION RESOLUTION PACKAGE（PREP 层）
> 本文档 = DECISION FREEZE APPLIED（2026-09-25）
> ```
>
> **更新（2026-09-25）**：Human 通过 `UAP P10 — HUMAN DECISION RESOLUTION` 逐项裁定 ——
> **18 项 OQ 全部 `FROZEN`，0 项未决**。本文件已据此同步：`HUMAN DECISION` 由 `PENDING` 更新为**选定决策**，
> `STATUS` 由 `PROPOSED` 更新为 `FROZEN`（**18 / 18**）。
> **冻结正文写入 `PLATFORM_DECISION_LOG.md` 的 `D-P10-01`…`D-P10-18` —— 该处为唯一权威。**
>
> **本轮 B / C 段明确裁定**（非 Recommended 默认）：`OQ-P10-02`（UUIDv7 canonical + Outbox/EventBus 边界 ·
> `C-2`/`C-3`）· `OQ-P10-05`（结构化 `metadata` · `C-1`）· `OQ-P10-11`（`tg_audit_immutable` = P10-owned · `C-4`）。
> 其余 15 项按 PREP Recommended Direction 冻结（**已逐项通过冲突核对**：`D-PLAT-09` / `D-AUTH-01..25` /
> P09 frozen schema / migration contract / P10-P11 边界 —— **无真实冲突**，见验收报告）。
>
> **历史记录（上一轮原状，保留不改）**：本文件初次产出时，指令 §8 规定 **`RECOMMENDED ≠ FROZEN`**、
> 未获 Human Decision 的 OQ 一律 `PENDING`，故当时 18 项 `HUMAN DECISION = PENDING` / `STATUS = PROPOSED`，
> **未写入** `PLATFORM_DECISION_LOG.md`。
>
> ⚠ **阅读约定**：§2–§19 的 `Current Evidence` / `Option A·B·C` / `Impact` / `Recommended Direction`
> 均为**过程分析材料**（保留原貌）；其**结论**一律以 `PLATFORM_DECISION_LOG.md` 的 `D-P10-*` 与本节 `选定` 为准。
---

## 0.1 OQ 状态总表

| OQ | 主题 | HUMAN DECISION | STATUS |
|---|---|---|---|
| `OQ-P10-01` | outbox 状态列是否全属 P10 DDL | **FROZEN** | `FROZEN` |
| `OQ-P10-02` | `core/event` 契约对齐（UUIDv7 · EventBus vs outbox） | **FROZEN** | `FROZEN` |
| `OQ-P10-03` | events 生产者边界与写入契约 | **FROZEN** | `FROZEN` |
| `OQ-P10-04` | `event_type` 命名空间与 `schema_version` 兼容 | **FROZEN** | `FROZEN` |
| `OQ-P10-05` | **`C-1`** audit `D-AUTH-15` 七类字段：列 vs `metadata` | **FROZEN** | `FROZEN` |
| `OQ-P10-06` | `core/audit.AuditEvent` 契约扩字段形态 | **FROZEN** | `FROZEN` |
| `OQ-P10-07` | audit 写入同步 / 异步策略 | **FROZEN** | `FROZEN` |
| `OQ-P10-08` | audit `metadata` 脱敏执行点与 DB 侧保护 | **FROZEN** | `FROZEN` |
| `OQ-P10-09` | 分区粒度 / 初始子分区 / `DEFAULT` 分区 | **FROZEN** | `FROZEN` |
| `OQ-P10-10` | 分区创建与 retention 的运维模型 | **FROZEN** | `FROZEN` |
| `OQ-P10-11` | **`C-4`** `tg_audit_immutable`（L）落点：P10 vs P11 | **FROZEN** | `FROZEN` |
| `OQ-P10-12` | `events` ↔ `audit_logs` 显式 linkage 列 | **FROZEN** | `FROZEN` |
| `OQ-P10-13` | DB 角色与 `GRANT` 归属 | **FROZEN** | `FROZEN` |
| `OQ-P10-14` | `classification` 存储与 CRITICAL 摘要策略 | **FROZEN** | `FROZEN` |
| `OQ-P10-15` | 是否引入 RLS | **FROZEN** | `FROZEN` |
| `OQ-P10-16` | Runtime 关联键（`run_id` 等）载体 | **FROZEN** | `FROZEN` |
| `OQ-P10-17` | 五类承载面边界形式化与守卫 | **FROZEN** | `FROZEN` |
| `OQ-P10-18` | outbox 投递 worker 的阶段归属 | **FROZEN** | `FROZEN` |

> **统计**：`PENDING` **18** / `FROZEN` **0** / `DEFERRED` **0** / `SUPERSEDED` **0**。

---

## 1. 已由冻结材料确定、**不设 OQ** 的约束（继承面）

> 依指令 §1「除非现有权威文档明确证明其属于 P10 已冻结范围」—— 以下为**已冻结**，本轮**只继承、不重开**。

| ID | 内容 | 来源 | 性质 |
|---|---|---|---|
| **GP-1** | P10 = **Event / Audit**，交付 `events` → `audit_logs`（**分区父表 + 初始子分区**） | `STEP1B_SCHEMA_DEPENDENCY.md:171` | 冻结范围 |
| **GP-2** | 阶段顺序 **`P10 → P11 → P12 → P13 → Runtime`** | `D-PLAT-09`（FROZEN） | 冻结顺序 |
| **GP-3** | `P00–P10 均无 seed 需求；P13 才有 seed`；**所有 trigger（P11）必须先于 P13 seed** | `STEP1B_SCHEMA_DEPENDENCY.md:193` | 冻结纪律 |
| **GP-4** | 两表 PK = `(id, occurred_at)` · `PARTITION BY RANGE (occurred_at)` · `tenant_id`/`space_id` **无强制 FK** · downgrade 先 DROP 子分区再 DROP 父表 | `DEPENDENCY` §9 `:265-270` | 冻结 schema 规则 |
| **GP-5** | 约束集（CK / NN / NULL）逐项 | `STEP1B_CONSTRAINT_MATRIX` §7 | 冻结 schema |
| **GP-6** | 索引清单（`ix_events_dispatch` · `ix_events_tenant_type_time` · `ix_audit_*` 5 条） | `STEP1B_INDEX_STRATEGY` §2 | 冻结索引 |
| **GP-7** | 保留期：`events` 投递后 **30d**（dead 90d）· `audit_logs` **365d（可配置）**、**不做行级删除** | `CORE` §11 · `CONSTRAINT` §7 | 冻结保留期 |
| **GP-8** | `events` = **at-least-once** outbox，**绝不承诺 exactly-once**；消费方按 `event_id` 幂等 | `CORE` §8.2 · `EVENT_OUTBOX` 首行 | 冻结语义 |
| **GP-9** | `audit_logs` **不可变**（无 `updated_at`/`deleted_at`；仅 `INSERT, SELECT`；trigger 双保险） | `CORE` §1.6/§13 · `TRIGGER_INVENTORY` §L | 冻结不变式 |
| **GP-10** | `events` **无 DB trigger**（claim 走应用层 CAS） | `TRIGGER_INVENTORY` §M | 冻结设计 |
| **GP-11** | ID = **UUIDv7**；分区表 PK = `(id uuidv7, occurred_at)` | `D-AUTH-22` · `UUID_STRATEGY` §6 | 冻结数据律 |
| **GP-12** | 三类审计分离：**Agent Run Audit ≠ Authorization Decision Audit ≠ Tool Execution Audit** | `D-AUTH-15` · `D-AGENT-13` | 冻结边界 |
| **GP-13** | 授权审计 persistence = **DEFERRED TO P10**；**不得在 P10 之外创建 `events`/`audit_logs`** | `D-AUTH-15` · `D-AUTH-22` | 冻结归属 |
| **GP-14** | **禁止** downgrade 删除审计/不可变数据（分区按保留期 drop，不随版本回滚） | `MIGRATION_CONTRACT` §10 | 冻结纪律 |
| **GP-15** | `D-PLAT-09` **本轮不 supersede**；P10 不得因此扩张为 Runtime / worker / AI Gateway runtime | 指令 §1 ・ `D-PLAT-09` | 冻结边界 |

---

## 2. `OQ-P10-01` — outbox 状态列是否全部属 P10 DDL

| 字段 | 内容 |
|---|---|
| **Question** | `events` 的 outbox 状态列（`status` / `worker_id` / `claimed_at` / `lease_expires_at` / `attempts` / `next_attempt_at` / `last_error` / `delivered_at`）是否**全部**在 P10 一次建齐，还是分阶段加列？ |
| **Current Evidence** | `CORE` §1.6 与 `ER_MODEL` §6 与 `STEP1B_EVENT_OUTBOX.md` §1 **三处一致**地把这些列列为 `events` 表字段；`CONSTRAINT` §7 已冻结其 CK（`status IN (…)`、`attempts BETWEEN 0 AND 100`） |
| **Option A** | **一次建齐**（含全部 outbox 列） |
| **Option B** | 仅建事实列（`occurred_at`/`event_type`/`payload`/…），outbox 状态列延后 |
| **Engineering Impact** | A：与三份冻结文档逐字段一致，一次收敛；B：**与冻结 schema 冲突**，且 CK/NN 需二次变更（`ALTER TABLE` 在分区表上代价更高） |
| **Security Impact** | A：`attempts <= 100` 等护栏一次到位；B：延后期内 outbox 无状态约束 |
| **Migration Impact** | A：单一 migration（0013）；B：需要第二个 migration（列 + CK + 索引） |
| **Future Runtime Impact** | A：outbox 投递契约可立即被后续阶段消费；B：投递实现被阻塞 |
| **Recommended Direction** | **Option A**（技术后果：唯一与冻结文档一致的选项；避免分区表二次 DDL） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — outbox 状态列（`status`/`worker_id`/`claimed_at`/`lease_expires_at`/`attempts`/`next_attempt_at`/`last_error`/`delivered_at`）**全部属 P10 DDL，一次建齐**（`events` **即** outbox 载体，不新增第三张表） |
| **Status** | `FROZEN` |

---

## 3. `OQ-P10-02` — `core/event` 契约对齐（UUIDv7 · EventBus vs outbox）

| 字段 | 内容 |
|---|---|
| **Question** | 既有 `core/event` 契约如何与冻结的 UUIDv7 数据律及 outbox 投递模型对齐？ |
| **Current Evidence** | **实测**：① `core/event/interfaces.py` 的 `_new_id()` = **`uuid.uuid4()`** ⇒ 与 `GP-11`（UUIDv7）**冲突**；② 同文件 `DomainEvent.tenant_id` **非空**，冻结 schema 为 `NULL` 允许；③ 同文件定义 `EventBus`（`publish` / `subscribe`）**内存总线**，而冻结投递模型是 **outbox 表 + CAS claim + lease + Reaper**；④ `core/audit/interfaces.py` 已用 UUIDv7（`new_event_id()`），故 `D-AUTH-22` 理由段"`core/audit` 为唯一异形方"**已过期**（见 `C-2`） |
| **Option A** | `EventBus` **保留为进程内契约**；持久化投递**只能**经 `events` outbox；`DomainEvent.id` 改用 **UUIDv7**；`tenant_id` 改为可空 |
| **Option B** | 以 `EventBus` **取代** outbox（内存投递） |
| **Option C** | 删除 `core/event`，全部语义移入 outbox 契约 |
| **Engineering Impact** | A：契约与数据律一致、投递语义唯一；B：**与 `GP-8` 冲突**（at-least-once 需要持久化）；C：破坏既有 import 面 |
| **Security Impact** | A：跨租户隔离不受内存总线影响（持久化 + tenant 谓词）；B：进程内总线无审计面、重启即丢 ⇒ 不可接受 |
| **Migration Impact** | A：仅契约文字（0 DDL）；B：0；C：删包 |
| **Future Runtime Impact** | A：Runtime 通过 outbox 接事件，语义稳定；B：Runtime 会绑上内存总线 |
| **Recommended Direction** | **Option A**（技术后果：唯一同时满足 `GP-8` + `GP-11` 的选项；`EventBus` 不得作为跨进程投递机制） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A + Human 强化** — **Domain Event ID = UUIDv7 canonical**；`uuid.uuid4()` **不属于**最终 P10 Event identity contract（**仅实现遗留，实施期修正**）；**`Outbox` = durable / reliable event delivery authority**；**`EventBus` = optional in-process auxiliary mechanism**（**MUST NOT** replace outbox persistence / be the durable delivery boundary / become the canonical cross-process delivery mechanism）；outbox claim/lease/reaper/retry 沿既有权威设计作为后续 Implementation Contract 依据；含 **`C-2`**（append-only clarification）与 **`C-3`**（`EventBus != Outbox`） |
| **Status** | `FROZEN` |

---

## 4. `OQ-P10-03` — events 生产者边界与写入契约

| 字段 | 内容 |
|---|---|
| **Question** | P10 是否定义 `events` 的**写入契约**（谁写、是否强制与业务写入同事务、是否提供写入 API）？ |
| **Current Evidence** | `EVENT_OUTBOX` §7 已冻结**写入模式**（`BEGIN; 业务写入; INSERT events; COMMIT;`）并**禁止**把投递放入业务事务；但**未**定义写入契约的载体与责任方。`D-AUTH-16` 模式 = `core` 契约 + `services` 实现 |
| **Option A** | P10 定义 **`core/event` 写入契约**（值对象 + 校验），实现留 `services/`（后续阶段） |
| **Option B** | P10 只建表，写入方式完全由调用方自行决定 |
| **Option C** | P10 交付完整 event service 实现 |
| **Engineering Impact** | A：契约先行、责任清晰；B：**无强制同事务** ⇒ at-least-once 前提被破坏；C：**越界**（本轮禁 runtime/API 实施） |
| **Security Impact** | A：写入面可加租户/脱敏校验；B：无校验点；C：超范围 |
| **Migration Impact** | 全 0（契约层） |
| **Future Runtime Impact** | 决定 Runtime / 业务模块如何产生事件 |
| **Recommended Direction** | **Option A**（技术后果：与 `D-AUTH-16` 分层一致；保证"业务成功 ⇔ 事件存在"） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — P10 定义 **`core/event` 写入契约**（值对象 + 校验 + 与业务写入同事务）；**实现留 `services/`**（后续阶段） |
| **Status** | `FROZEN` |

---

## 5. `OQ-P10-04` — `event_type` 命名空间与 `schema_version` 兼容

| 字段 | 内容 |
|---|---|
| **Question** | `event_type` 是否需要**注册表**？`schema_version` 的兼容/演进策略？ |
| **Current Evidence** | CK 已冻结格式：`^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$`（=`namespace.aggregate.action`）；`ER_MODEL` 注释 `schema_version int`；**无**注册表设计（对比：`acl_subject_types` 有注册表 + CK 白名单 + 保护 trigger） |
| **Option A** | **不建注册表**：仅 CK 正则 + 命名约定（平台内约定式） |
| **Option B** | 建 `event_types` 注册表（镜像 `acl_subject_types` 模式） |
| **Option C** | 先 A，量级上来再 B（注册表后置） |
| **Engineering Impact** | A：0 新表、0 DDL（与 P10 两张表范围一致）；B：**新增第三张表** ⇒ 超出 P10 冻结交付面；C：可演进但需未来 migration |
| **Security Impact** | A：无集中治理点（但事件非授权面）；B：可治理但引入 registry 生命周期复杂度 |
| **Migration Impact** | A：0；B：+1 表；C：未来 +1 表 |
| **Future Runtime Impact** | 决定 event_type 的治理强度 |
| **Recommended Direction** | **Option A**（技术后果：**P10 冻结交付面只有两张表**；新增 `event_types` 表须新的 Human Decision，不得隐含扩张） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — **不建** `event_types` 注册表；仅 CK 正则 + 命名约定；`schema_version` 仅**单调递增** |
| **Status** | `FROZEN` |

---

## 6. `OQ-P10-05` — **`C-1`** audit `D-AUTH-15` 七类字段：列 vs `metadata`

| 字段 | 内容 |
|---|---|
| **Question** | `D-AUTH-15` 要求 Authorization Audit **至少可表达** `subject` · `delegator` · `tenant` · `space` · `resource` · `action` · `decision` · `reason` · `policy` · `risk` · `approval` · `timestamp`；其中 `subject` / `delegator` / `decision` / `policy` / `approval` **不在**冻结 `audit_logs` 列集内 —— 应**加列**还是**落 `metadata`**？ |
| **Current Evidence** | 冻结 `audit_logs` 列集（`CORE` §1.6 · `CONSTRAINT` §7 · `ER_MODEL` §6）**无**这 5 类列；仅有 `reason` / `risk_level` / `correlation_id` / `request_id` / `metadata jsonb`。`D-AUTH-15` 影响范围原文：**「`core/audit.AuditEvent`（契约扩字段）· 未来 `audit_logs`（P10）」** ⇒ `D-AUTH-15` **明确把 `audit_logs` 列入影响范围**，但**未**指定落列。`core/audit.AuditEvent` 当前**已含** `subject_id` / `subject_type` |
| **Option A** | **落 `metadata`**：`audit_logs` 列集**保持冻结不变**；七类字段（缺列者）写 `metadata jsonb`（写入前脱敏） |
| **Option B** | **加列**：在 P10 为 `subject_type` / `subject_id` / `decision` / `policy` / `approval_*` 增列 |
| **Option C** | 混合：`subject_*` 加列（高频查询），其余落 `metadata` |
| **Engineering Impact** | A：不动冻结列集、0 争议；但按 `subject` / `decision` 的**索引化查询**受限。B：查询最优；但**改变冻结 schema**（`CORE`/`CONSTRAINT`/`ER_MODEL` 三份文档需同步）。C：折中，但同样改 schema |
| **Security Impact** | A：脱敏路径统一（`metadata` 已定义"写入前脱敏"）；B/C：新列需各自的脱敏/分级策略 |
| **Migration Impact** | A：0 schema 变更；B/C：需同步修改三份冻结 schema 文档 + migration 加列 |
| **Future Runtime Impact** | 决定审计查询能力（"某 subject 的全部决策"是否可走索引） |
| **Recommended Direction** | **先 A，并单列 Human Decision 记录取舍**（技术后果：A 使 P10 **不触碰任何冻结 schema**；若 Human 选 B/C，**须走显式 supersession**，不得静默改冻结列集） |
| **性质提示** | **`C-1` = 候选 `FROZEN` vs `SCHEMA` 冲突**；**必须**由 Human 裁定，本轮**不代裁**（`PLATFORM_DECISION_LOG.md` Charter §2.3 / §7） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — Authorization Audit 的 `subject`/`delegator`/`decision`/`policy`/`approval` 五类语义**采用结构化 `metadata` 表达**（`audit_logs.metadata`）；**不自动增加 first-class columns**；`metadata` 必须**结构化、可验证、可追踪**，**不得**作非结构化垃圾桶、**不得**绕过 canonical audit fields；**不产生 `D-AUTH-15` supersession** ⇒ **`C-1` = RESOLVED** |
| **Status** | `FROZEN` |

---

## 7. `OQ-P10-06` — `core/audit.AuditEvent` 契约扩字段形态

| 字段 | 内容 |
|---|---|
| **Question** | `D-AUTH-15` 影响范围所述"`core/audit.AuditEvent`（契约扩字段）"在 P10 的落地形态？ |
| **Current Evidence** | 实测 `core/audit/interfaces.py` 已含：`action` · `outcome` · `actor_id` · `tenant_id` · `space_id` · `target_type` · `target_id` · `metadata` · `id`（UUIDv7）· `occurred_at` · `subject_id` · `subject_type`；**缺** `delegator` · `decision` · `policy` · `risk` · `approval`（部分在 `AuthorizationDecisionAudit` 内）。`services/authorization/audit.py` 已产出 decision 审计但**不持久化** |
| **Option A** | P10 **对齐契约与 `audit_logs` 列 + `metadata` 的显式映射**（契约字段 ↔ 列/`metadata` 路径一对一） |
| **Option B** | P10 只建表，契约对齐延后 |
| **Option C** | P10 顺带重设计 audit 契约 |
| **Engineering Impact** | A：映射显式、可测；B：契约与表脱节（易漂移）；C：超 P10 范围 |
| **Security Impact** | A：可断言"每个契约字段都有落点且已脱敏"；B：无保证 |
| **Migration Impact** | 0（契约/映射层） |
| **Future Runtime Impact** | 决定 P10 与 `services/authorization` 的衔接 |
| **Recommended Direction** | **Option A**（技术后果：把 `D-AUTH-15` 的"影响范围"落地为可测映射） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — `core/audit.AuditEvent` ↔ `audit_logs`（**列 + `metadata` 路径**）映射**显式化**（一对一可测） |
| **Status** | `FROZEN` |

---

## 8. `OQ-P10-07` — audit 写入同步 / 异步策略

| 字段 | 内容 |
|---|---|
| **Question** | 审计写入是同步（阻塞主流程）还是异步（批量 + outbox 补偿）？ |
| **Current Evidence** | `STEP1A_DESIGN_REPORT.md` **R6**（原文）：*「**审计全量写入放大** \| 中 \| HIGH/CRITICAL **同步写**，LOW **异步批量**；写入失败进 outbox 补偿，不阻塞主流程」* |
| **Option A** | 采纳 **R6**（按风险分级） |
| **Option B** | 全部同步（最强一致性，写入放大） |
| **Option C** | 全部异步（吞吐最优，丢审计风险） |
| **Engineering Impact** | A：风险分级、可演进；B：主流程延迟 + 放大；C：**审计可丢失** |
| **Security Impact** | A：HIGH/CRITICAL 同步 ⇒ 证据不丢；B：最安全但成本高；C：**合规不可接受** |
| **Migration Impact** | 0 |
| **Future Runtime Impact** | 决定 Runtime 审计调用路径的阻塞语义 |
| **Recommended Direction** | **Option A**（技术后果：与 `STEP1A` R6 一致，且 **FAIL CLOSED 语义不受影响**——审计写入失败不得放行受控操作，`D-AUTH-12`） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — 采纳 `STEP1A_DESIGN_REPORT.md` **`R6`**：**HIGH / CRITICAL 同步写 · LOW 异步批量**；失败进 outbox 补偿，不阻塞主流程（**FAIL CLOSED 语义不变**） |
| **Status** | `FROZEN` |

---

## 9. `OQ-P10-08` — audit `metadata` 脱敏执行点与 DB 侧保护

| 字段 | 内容 |
|---|---|
| **Question** | `metadata` 的脱敏在哪一层强制？DB 侧是否加保护？ |
| **Current Evidence** | 冻结：`metadata jsonb`（**写入前已脱敏**，`CORE` §1.6）；"审计 `metadata` 与日志统一走 `redaction`；CRITICAL 只存摘要"（`CORE` §13）。既有基线：`infrastructure/logging/redaction.py`（双重脱敏） |
| **Option A** | **应用层强制脱敏** + 测试守卫（AK/SK / token / PII 模式扫描）；DB 侧**不加**转换逻辑 |
| **Option B** | DB 侧 trigger/函数强制脱敏 |
| **Option C** | 仅约定，无强制 |
| **Engineering Impact** | A：与既有基线一致、可测；B：脱敏规则入 DB（难维护、与 `redaction` 双份权威）；C：**不可接受** |
| **Security Impact** | A：单点权威（`redaction`）+ 守卫；B：双权威、易漂移；C：有泄漏面 |
| **Migration Impact** | A：0；B：+1 trigger/函数（与 `GP-10`/`GP-9` 的"仅 `tg_audit_immutable`"边界冲突） |
| **Future Runtime Impact** | 决定审计写入路径的组件责任 |
| **Recommended Direction** | **Option A**（技术后果：沿用既有 `redaction` 单点权威；**不引入** audit 上的第二类 trigger） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — `metadata` 脱敏 = **应用层强制**（沿用 `redaction` 单点权威）+ **测试守卫**；**DB 侧不加转换逻辑**（不引入 `tg_audit_immutable` 以外的 trigger） |
| **Status** | `FROZEN` |

---

## 10. `OQ-P10-09` — 分区粒度 / 初始子分区 / `DEFAULT` 分区

| 字段 | 内容 |
|---|---|
| **Question** | 分区粒度、初始子分区数量/范围、是否建立 `DEFAULT` 分区？ |
| **Current Evidence** | 冻结：`PARTITION BY RANGE (occurred_at)` + **当月子分区**（`DEPENDENCY` §9）；`events`/`audit_logs` 均按月（`CORE` §1.6）；"到期整分区 drop"（`CORE` §13） |
| **Option A** | 月分区 + 仅**当月**子分区，**不建 `DEFAULT` 分区** |
| **Option B** | 月分区 + 当月 + **预建未来 N 个月**，不建 `DEFAULT` |
| **Option C** | 月分区 + `DEFAULT` 分区兜底 |
| **Engineering Impact** | A：与冻结一致、最小；B：减少运维频率（但与"手工运维"模型需对齐 `OQ-P10-10`）；C：**`DEFAULT` 分区**使 `ATTACH PARTITION` 需先扫描/移动行，且可能掩盖越界写入 |
| **Security Impact** | A/B：越界写入**直接失败**（fail closed）；C：越界写入**静默落入 DEFAULT** ⇒ 与"审计不得静默"精神相悖 |
| **Migration Impact** | A/B：`CREATE TABLE … PARTITION OF` 子分区；C：+ `DEFAULT` 分区 |
| **Future Runtime Impact** | 决定 retention drop 的可执行单元 |
| **Recommended Direction** | **Option A**（技术后果：与冻结"当月子分区"逐字一致；`DEFAULT` 分区倾向**不建**以避免静默捕获） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — 月分区 + **仅当月子分区**；**不建立 `DEFAULT` 分区**（避免静默捕获越界写入） |
| **Status** | `FROZEN` |

---

## 11. `OQ-P10-10` — 分区创建与 retention 的运维模型

| 字段 | 内容 |
|---|---|
| **Question** | 未来月份分区的创建与到期 `DROP` 由谁执行？自动化还是手工？ |
| **Current Evidence** | **既有先例（B1-6 `D-3 = D`，FROZEN）**：*"Future partition creation and retention cleanup are **manual operational responsibilities** in P08. Automation is deferred to a future operational/runtime phase."*（`B1-6_DECISION_LOG.md:363`）；`B1-6_TEST_MATRIX.md` **RF5** 同义（"仍不计入 canonical"） |
| **Option A** | **沿用 B1-6 先例**：手工运维，自动化延后（平台一致） |
| **Option B** | P10 交付自动化脚本（`pg_partman` 或自研 job） |
| **Option C** | P10 交付手工 runbook + 未来自动化立项 |
| **Engineering Impact** | A：与 P08 一致、0 新组件；B：**引入新组件/依赖**（与"最小扩展"`DEPENDENCY` §10 及本轮禁 worker 实施冲突）；C = A + 文档 |
| **Security Impact** | A/C：`DROP` 走迁移/运维权限（`uap_migrator` 级），**不给应用 DDL 权限**（`GP`: `CORE` §13）；B：需长期授权高权限 job |
| **Migration Impact** | A：0（运维动作在 migration 之外）；B：额外脚本/扩展 |
| **Future Runtime Impact** | 决定运维面形态（与"Runtime 不含 worker framework"一致） |
| **Recommended Direction** | **Option C**（= A 的运维模型 + 交付 runbook；技术后果：与 B1-6 先例一致，且不引入新组件） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**C** — **手工运维模型**（沿用 B1-6 先例 `D-3 = D`）+ P10 交付 **runbook**；自动化延后至未来 operational/runtime 阶段 |
| **Status** | `FROZEN` |

---

## 12. `OQ-P10-11` — **`C-4`** `tg_audit_immutable`（L）落点：P10 vs P11

| 字段 | 内容 |
|---|---|
| **Question** | `tg_audit_immutable` 在 **P10（建表时内联）** 还是 **P11（集中）** 创建？ |
| **Current Evidence** | `TRIGGER_INVENTORY` §L："`tg_audit_immutable` \| audit_logs \| BEFORE UPDATE OR DELETE \| **最早 phase = P10**"；`SCHEMA_DEPENDENCY:241` 同。**同时** `D-PLAT-10`（FROZEN）**待办④** 原文：*「`L`（`tg_audit_immutable`）**属 P10**，须与 P11 明确分界」* ⇒ **该分界至今未定义**（= `C-4`） |
| **Option A** | **P11 集中**（与 `D-PLAT-10` 的"G/H/I/J 按 P11 集中"精神一致；P10 只建表） |
| **Option B** | **P10 内联**（表建时即挂，immutability 不出现窗口期） |
| **Option C** | P10 建表 + P10 内联 **且** 在 `TRIGGER_INVENTORY`/PDL 中显式登记分界结论 |
| **Engineering Impact** | A：集中易审计，但 **P10→P11 之间存在不可变窗口**（P10 完成至 P11 完成期间 audit 可被 UPDATE 删改）；B：无窗口，但与"集中"惯例分叉；C：无窗口 + 留痕 |
| **Security Impact** | **A 有真实安全窗口**（`audit_logs` 在同一窗口内可被非法改写）；B/C 无窗口 ⇒ 更安全 |
| **Migration Impact** | A：trigger 落 0014+；B/C：trigger 落 0013（同一 migration） |
| **Future Runtime Impact** | 决定 P11 的 trigger 清单边界（`L` 是否计入 P11） |
| **Recommended Direction** | **Option C**（技术后果：消除不可变窗口，且闭合 `D-PLAT-10` 的显式待办；**须在 PDL 登记分界结论**，不得静默） |
| **性质提示** | 本 OQ **即 `D-PLAT-10` 待办的闭合**；裁定须写入 `PLATFORM_DECISION_LOG.md`（**本轮未写入**） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**C + Human 强裁定** — **`tg_audit_immutable` = P10-owned**；`P10 = Event/Audit persistence + Audit-local immutability protection`；`P11 = remaining trigger / cross-table constraint layer`；**P11 不得成为 `audit_logs` 基础 immutable security property 的前置条件**；**禁止** `P10 implemented → audit exists but mutable → P11 later fixes immutability`，**该窗口必须被消除** ⇒ **`C-4` = RESOLVED**（闭合 `D-PLAT-10` 待办 ④） |
| **Status** | `FROZEN` |

---

## 13. `OQ-P10-12` — `events` ↔ `audit_logs` 显式 linkage 列

| 字段 | 内容 |
|---|---|
| **Question** | 是否建立 `audit_logs.event_id` / `events.audit_id` 之类**显式 linkage 列**？ |
| **Current Evidence** | `ER_MODEL` §6：`events ||--o| audit_logs : "may be mirrored by"` —— **弱关系、无 FK**；`DEPENDENCY` §1.7 两表均"无强制 FK"；两表均有 `correlation_id`（可作为关联键） |
| **Option A** | **不建** linkage 列（靠 `correlation_id` / `request_id` 关联，与既有冻结一致） |
| **Option B** | `audit_logs` 加 `event_id` 列 |
| **Option C** | `events` 加 `audit_id` 列 |
| **Engineering Impact** | A：0 schema 变更、与 ER 一致；B/C：改冻结列集（需同步三份 schema 文档） |
| **Security Impact** | A：无新增关联面；B/C：新增可能的交叉推导面（审计↔事件互相指向） |
| **Migration Impact** | A：0；B/C：加列（分区表 ALTER） |
| **Future Runtime Impact** | 决定"从事件追到审计"的查询效率 |
| **Recommended Direction** | **Option A**（技术后果：ER 已把二者定义为弱关系；`correlation_id` 已能承担关联，避免改冻结 schema） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — **不建**显式 linkage 列；以 `correlation_id` / `request_id` 承担关联（ER 已定义为弱关系） |
| **Status** | `FROZEN` |

---

## 14. `OQ-P10-13` — DB 角色与 `GRANT` 归属

| 字段 | 内容 |
|---|---|
| **Question** | `audit_logs` 的 `GRANT INSERT, SELECT`（`uap_app`）由 P10 migration 执行，还是运维脚本？ |
| **Current Evidence** | `CORE` §13 冻结三角色模型（`uap_app` DML / `uap_migrator` DDL / `uap_readonly`）与"审计不可变：仅 `INSERT, SELECT`"；`MIGRATION_CONTRACT` §11 称迁移用 `uap_migrator`。**实测**：既有 12 个 migration 中**未见** `GRANT` 语句（角色体系尚未落地） |
| **Option A** | P10 migration 内 `GRANT`（一次到位） |
| **Option B** | 独立运维脚本（角色体系整体立项时统一做） |
| **Option C** | P10 只建表，`GRANT` 记为 **OPEN（非 P10）** |
| **Engineering Impact** | A：与"仅 INSERT/SELECT"一次收敛；B：与角色体系一并做，避免碎片；C：最小改动 |
| **Security Impact** | **A/C 间有真实差异**：若角色体系未落地，`audit_logs` 在无 `GRANT` 时对应用不可用（fail closed，安全但功能缺）；若误给宽权限则破坏不变性 |
| **Migration Impact** | A：migration 含 `GRANT`；B/C：0 |
| **Future Runtime Impact** | 决定应用能否立即写审计 |
| **Recommended Direction** | **Option C 并显式登记为 OPEN**（技术后果：避免在**角色体系尚未定义**的情况下于 P10 单方面发明权限模型；`GRANT` 归属随角色体系统一裁定） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**C** — `GRANT` **不属 P10 交付**，登记为 **OPEN**（`OPEN-P10-1`：DB 角色体系 + `GRANT` 归属；实测 12 个 migration 中 `GRANT` = 0）；`audit_logs` 不可变性由 `D-P10-11` 的 trigger 保证，**不依赖 `GRANT`** |
| **Status** | `FROZEN` |

---

## 15. `OQ-P10-14` — `classification` 存储与 CRITICAL 摘要策略

| 字段 | 内容 |
|---|---|
| **Question** | `audit_logs.classification` 的取值范围与可空性？CRITICAL 只存摘要如何落地？ |
| **Current Evidence** | CK 冻结为 `classification IN (四级)`（**可空则按策略**）；`CORE` §7 数据分级"只能升不能随意降，降级需写 `audit_logs` 并注明 `reason`"；`CORE` §13"CRITICAL 只存摘要"；`resources.classification` 四档含 `HIGHLY_CONFIDENTIAL`（禁降级） |
| **Option A** | `classification` **NOT NULL**（NULL 视为最低档） |
| **Option B** | `classification` **可空**（NULL = 不适用，如平台级事件） |
| **Option C** | 可空 + 另加 `payload_digest`（摘要列）显式承载"只存摘要" |
| **Engineering Impact** | A：统计口径明确；B：与冻结 CK 的"可空按策略"一致；C：新增列（改冻结列集） |
| **Security Impact** | A：强制分级；B：NULL 语义须有守卫；C：摘要可验证（防"只存摘要"沦为不可核验） |
| **Migration Impact** | A/B：0（CK 已冻结）；C：+1 列 |
| **Future Runtime Impact** | 决定审计内容的可核验性 |
| **Recommended Direction** | **Option B**（技术后果：与冻结 CK 原文"可空则按策略"一致；NULL 语义在契约层显式定义。**"CRITICAL 只存摘要"作为契约纪律落实，不新增列**） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**B** — `classification` **可空**（`NULL` = 不适用）且在**契约层显式定义 NULL 语义 + 守卫**；"**CRITICAL 只存摘要**"作为**契约纪律**落实，**不新增列** |
| **Status** | `FROZEN` |

---

## 16. `OQ-P10-15` — 是否引入 RLS

| 字段 | 内容 |
|---|---|
| **Question** | P10 是否在 `events` / `audit_logs` 上引入 Row Level Security？ |
| **Current Evidence** | `CORE` §13："租户隔离 \| 复合索引 + 应用层强制 + **RLS（可选，见 Q1）** + 越权审计"；`CORE` §14 **Q1** 为开放项。**既有边界先例**：`tg_resources_tenant_space_consistency` 与 `tg_acl_subject_types_protect` 均**强制声明**"**不引入 RLS**"（`D-B14-10` / `D-B14-12` 边界） |
| **Option A** | **不引入 RLS**（延续既有边界声明；隔离靠 tenant 谓词 + 应用层断言 + 越权审计） |
| **Option B** | P10 引入 RLS（DB 层强制隔离） |
| **Option C** | 先 A，RLS 单独立项（未来 phase） |
| **Engineering Impact** | A：与既有 boundary 声明一致、0 新机制；B：需角色/会话变量体系（与"角色体系未落地"耦合）；C：可演进 |
| **Security Impact** | B 在**配置错误时会 fail open 或全表可见**（RLS 依赖 `SET LOCAL` 会话变量，缺失即策略失配）；A 依赖应用层断言（有既有守卫与测试） |
| **Migration Impact** | A：0；B：policy 对象 + 角色配置 |
| **Future Runtime Impact** | 决定 DB 与应用的责任分界 |
| **Recommended Direction** | **Option C**（技术后果：延续既有"不引入 RLS"边界，避免与未落地的角色体系耦合；RLS 单独立项） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**C** — **不引入 RLS**；租户隔离继续依赖 tenant 谓词 + 应用层强制断言 + 越权写入审计；RLS **单独立项** |
| **Status** | `FROZEN` |

---

## 17. `OQ-P10-16` — Runtime 关联键（`run_id` 等）载体

| 字段 | 内容 |
|---|---|
| **Question** | `D-AGENT-15` 要求的 run 关联字段（`run_id` / `trace_id` / `latency` / `cost` / `tool_calls` 等）如何落到 P10？ |
| **Current Evidence** | `D-AGENT-15` 冻结 `run_id` / `request_id` / `trace_id` / `tenant` / `space` / `actor` / `agent` / `agent_version` / `model` / `state` / `latency` / `cost` / `tool_calls` / `error` 为 **run 观测**字段集，并冻结"Structured Logs First + Future Event/Audit Surface"（`logs` 先行，P10 面**延后补充**）。`audit_logs` 冻结列集含 `correlation_id` / `request_id` / `metadata`，**无** `run_id` / `trace_id` 列 |
| **Option A** | 落 **`metadata` + `correlation_id`**（`run_id` = `correlation_id` 约定值） |
| **Option B** | `audit_logs` 加 `run_id` / `trace_id` 列 |
| **Option C** | 由 `agent_runs`（`D-AGENT-13`，独立于 P10）承载 run 关联，P10 不重复 |
| **Engineering Impact** | A：0 schema 变更；B：改冻结列集；C：与 `D-AGENT-13` 明确分工，避免 P10 承担 Runtime 载荷 |
| **Security Impact** | C 最清晰（run 载荷的脱敏/访问控制权归 `agent_runs` 设计）；A 使 run 键在 `metadata`（脱敏面内） |
| **Migration Impact** | A/C：0；B：加列 |
| **Future Runtime Impact** | 决定 Runtime 审计与 P10 的接缝 |
| **Recommended Direction** | **Option A + C 组合**（技术后果：`correlation_id` 承担跨面关联；run 细节归 `agent_runs`；**P10 不扩张为 Runtime persistence**，符合指令 §1 的禁止项） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A + C** — Runtime 关联键由 **`correlation_id`（跨面关联）+ `metadata`** 承担；**不新增 `audit_logs` 列**；**run 细节归 `agent_runs`**（`D-AGENT-13`）；**P10 不得扩张为 Agent Runtime persistence** |
| **Status** | `FROZEN` |

---

## 18. `OQ-P10-17` — 五类承载面边界形式化与守卫

| 字段 | 内容 |
|---|---|
| **Question** | `event` / `audit` / `operational log` / `trace` / `metric` 的边界如何**形式化**并**可强制**？ |
| **Current Evidence** | `PREP` §10.1 已给出分类表（event ✅ / audit ✅ / log ❌ / trace ❌ / metric ❌）；`DEPENDENCY_RULES.md` 末节纪律："**写在文档而无测试的规则属文档，非强制**"；`tests/architecture/` 现有 **2** 个文件、**无** event/audit 相关守卫 |
| **Option A** | 形式化声明 + **新增 `tests/architecture/` 守卫**（如：禁止业务模块直写 `events` 绕过 outbox 契约；禁止把 operational log 写进 `audit_logs`） |
| **Option B** | 仅文档声明 |
| **Option C** | 形式化 + 守卫 + CI（**无 CI**，见 `D-PLAT-17`） |
| **Engineering Impact** | A：可强制（人工执行，符合"无 CI ⇒ 人工执行"`D-PLAT-17` ⑦）；B：= 非强制；C：需建 CI（**不在授权面**） |
| **Security Impact** | A：边界可被测试证伪；B：边界会漂移 |
| **Migration Impact** | 0（测试层，实施期） |
| **Future Runtime Impact** | 决定 P10 之后的漂移风险 |
| **Recommended Direction** | **Option A**（技术后果：使边界成为**强制**而非文档；守卫随实施提交同批落地） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — 五类承载面边界**形式化声明**（`event`→`events` · `audit`→`audit_logs` · 其余**非 P10**）+ **新增 `tests/architecture/` 守卫**使边界**可强制**（守卫随**实施提交**同批落地） |
| **Status** | `FROZEN` |

---

## 19. `OQ-P10-18` — outbox 投递 worker 的阶段归属

| 字段 | 内容 |
|---|---|
| **Question** | `events` 的 outbox 投递（CAS claim / lease / Reaper）由**哪个阶段**实施？P10 交付边界到哪？ |
| **Current Evidence** | `TRIGGER_INVENTORY` §M：*"events 的 claim 状态迁移由**应用层 CAS UPDATE** 完成 …… 依赖在**应用侧 worker 进程**"*；`apps/worker/main.py` 为 **placeholder**（"No queues are wired in STEP 0"）；`D-AGENT-12` 冻结 **Execution Abstraction Only**（**禁** Celery / Redis Queue / RabbitMQ）；`D-PLAT-09` 路线 A 把 **Runtime 排在 P13 之后** |
| **Option A** | **P10 仅交付表 + 状态机契约**；投递 worker 实施归 **Runtime 阶段**（P13 之后） |
| **Option B** | P10 顺带实现投递 worker |
| **Option C** | P10 交付表 + 契约 + **手工投递 runbook**，worker 归 Runtime |
| **Engineering Impact** | A：P10 收敛于 schema + 契约；B：**越界**（本轮/本阶段禁 worker 实施，且与 `D-AGENT-12` 张力）；C：A + 运维文档 |
| **Security Impact** | A/C：投递重试与幂等责任显式归 Runtime（消费方按 `event_id` 幂等，`GP-8`）；B：P10 承担跨进程执行面（审计/授权需在 worker 侧重验） |
| **Migration Impact** | A/C：0；B：0（但引入运行时组件） |
| **Future Runtime Impact** | **直接决定 Runtime 范围**（是否含 outbox 投递） |
| **Recommended Direction** | **Option C**（技术后果：P10 = 表 + 状态机契约 + runbook；worker 归 Runtime；**不与 `D-AGENT-12` 冲突**） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**C** — P10 仅交付 **表 + outbox 状态机契约 + 运维 runbook**；**投递 worker 实施归 Runtime 阶段**（`D-PLAT-09` 路线 A；`D-AGENT-12` 禁 framework） |
| **Status** | `FROZEN` |

---

## 20. 冻结请求包 —— **已执行（2026-09-25）**

原请求项（保留原貌）：若认可 §2–§19 的 Recommended Direction，**一次确认即可完成 18 项冻结**。

```text
2026-09-25 —— Human 已逐项裁定（`UAP P10 — HUMAN DECISION RESOLUTION`）。
其中 3 项按 Human 明确指令【改选/强化】（OQ-P10-02 / 05 / 11），其余 15 项按 Recommended Direction 冻结。
全部 18 项均通过冲突核对（D-PLAT-09 ・ D-AUTH-01..25 ・ P09 frozen schema ・ migration contract ・ P10/P11 边界）。
```

**已执行的动作**：

| 原计划动作 | 结果 |
|---|---|
| 写 `PLATFORM_DECISION_LOG.md`（`D-P10-01..18`，状态 `FROZEN`） | ✅ **已写入 18 条 `FROZEN`**（另新增 P10/P11 边界节 · EventBus≠Outbox 节 · 附录 G · `D-AUTH-22` 注记） |
| 同步 `P10_PREP_REPORT.md` | ✅ **append-only 注记（不改写既有结论）** |
| 同步 `P10_DECISION_RESOLUTION.md` | ✅ **本文件** |
| 同步 `P10_ACCEPTANCE_MATRIX.md` | ✅ **已完成** |
| 其他文档陈旧描述 | ✅ **append-only clarification**（`ARCHITECTURE.md` 的 `EventBus` 表述） |
| `P10 DECISION FREEZE = PASSED` | ✅ **PASSED**（验收项全 PASS） |

> **不变**：`DDL` / `DML` / `MIGRATION` / `code` / `test` / `config` / `commit` / `tag` / `push` = **NOT AUTHORIZED**。
> **`P10 IMPLEMENTATION = NOT AUTHORIZED`** · **`P11 IMPLEMENTATION = NOT AUTHORIZED`** · **`Runtime Implementation Gate = CLOSED`**。
---

## 21. EXIT CHECK（2026-09-25 终态）

| 条件 | 上一轮实测 | **本轮终态** |
|---|---|---|
| 18/18 OQ individually resolved | ❌ 0/18 | ✅ **18/18**（`HUMAN DECISION = FROZEN` × 18） |
| or explicitly DEFERRED | ❌ 0 项 | ✅ 条目级 DEFERRED **0**；**OPEN 显式登记 1**（`OPEN-P10-1` `GRANT` 归属，**非 OQ**） |
| No silent decision | ✅ 无静默决定 | ✅ **无静默决定**；3 项按 Human 明确指令改选，15 项按 Recommended 冻结 |
| Decision Log ↔ Architecture ↔ Contract ↔ Acceptance 一致 | ⚠ 未执行 | ✅ **已执行**（验收项全 PASS） |
| `D-PLAT-09` 未被 supersede | ✅ | ✅ **FROZEN / NOT SUPERSEDED**（路线 A 保持） |
| P10 未扩张至 Runtime / worker / AI Gateway runtime | ✅ | ✅ 未扩张（`D-P10-16` / `D-P10-18` 显式排除） |
| `C-1`/`C-2`/`C-3`/`C-4` 已登记 | ✅（未代裁） | ✅ **已处置**：`C-1` RESOLVED · `C-2` CLARIFIED · `C-3` RESOLVED · `C-4` RESOLVED |
| migration / DDL / DML / code / test / config 变更 | ✅ 全 0 | ✅ **全 0** |
| commit / tag / push | ✅ 全 0 | ✅ **全 0** |

⇒ **`P10 DECISION FREEZE = PASSED`**（2026-09-25）
⇒ **`P10 IMPLEMENTATION = NOT AUTHORIZED`** · **`P11 IMPLEMENTATION = NOT AUTHORIZED`** · **`Runtime Implementation Gate = CLOSED`**

---

**END OF P10 DECISION RESOLUTION（2026-09-25 · READ-ONLY PREP）**
**END OF P10 DECISION RESOLUTION（`DECISION FREEZE APPLIED` · `HUMAN DECISION` 18/18 `FROZEN`；冻结正文见 `PLATFORM_DECISION_LOG.md` 的 `D-P10-01`…`D-P10-18`，2026-09-25）**
