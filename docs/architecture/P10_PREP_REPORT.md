# P10 — EVENT / AUDIT（`events` → `audit_logs`）PREP REPORT

> **状态（先读这个）**
>
> ```text
> 本文档 = READ-ONLY PREP / DESIGN / DISCOVERY 产物
> 本文档 ≠ FROZEN ≠ APPROVED ≠ IMPLEMENTED ≠ AUTHORIZED
> ```
>
> 本轮（`UAP P10 PREP — EVENT / AUDIT · READ-ONLY DESIGN / PREPARATION GATE`）**仅允许**
> READ-ONLY / DISCOVERY / DESIGN / EVIDENCE COLLECTION / PREP REPORT / DECISION PACKAGE PREPARATION。
>
> **本轮实测**：`DDL = 0` · `DML = 0` · `migration 创建 = 0` · `schema 实施 = 0` · `runtime 实施 = 0` ·
> `API 实施 = 0` · `worker 实施 = 0` · `测试代码修改 = 0` · `应用代码修改 = 0` · `配置修改 = 0` ·
> `commit = 0` · `tag = 0` · `push = 0` · `既有文档修改 = 0`。
>
> **全部设计内容为 PROPOSED**；`OQ-P10-01`…`OQ-P10-18` 的 `HUMAN DECISION` **一律 `PENDING`**。
> **RECOMMENDED ≠ FROZEN**（本轮指令 §8）。

---

## 1. Executive Summary

P10 = **Event / Audit**，交付 **`events` → `audit_logs`**（分区父表 + 初始子分区）。
本轮为 UAP 第一个 **持久化事件/审计承载面** 建立 PREP 基础：范围与边界、阶段依赖（四类分离）、
现有 substrate 实测、schema 提案（**继承已冻结设计**，非新造）、分区/保留/安全不变式、
`events` ↔ `audit_logs` 语义边界、三类审计分离、Runtime 接口关系、连带同步面、以及 **18 项 OQ**。

**三条最重的发现（全部为 REPORT-ONLY，未修改任何文件）**：

1. **契约漂移（真）**：`core/event/interfaces.py` 的 `DomainEvent.id` 仍用 **`uuid.uuid4()`**，
   而冻结数据律要求 **UUIDv7**（`STEP1B_UUID_STRATEGY` §6 · `CORE_DOMAIN_MODEL` §9 · `D-AUTH-22`；
   分区表 PK = `(id uuidv7, occurred_at)`）。**`D-AUTH-22` 原文称"`core/audit._new_id()` 使用 `uuid.uuid4()`，
   为唯一异形方"，该描述已过期** —— STAGE 2 已把 `core/audit` 修为 UUIDv7（`new_event_id()`），
   异形方**转移到 `core/event`**。另：`DomainEvent.tenant_id` **不可空**，冻结 schema 为 `NULL` 允许。
2. **契约/设计错位（真）**：`core/event.EventBus`（`publish` / `subscribe` 内存总线）与冻结的
   **transactional outbox**（表 + CAS claim + lease + Reaper）**不是同一投递模型**；
   P10 须裁定 EventBus 的存续形态（见 `OQ-P10-02`）。
3. **决策覆盖缺口（候选冲突）**：`D-AUTH-15` 要求 Authorization Audit **至少可表达**
   `subject` · `delegator` · `decision` · `reason` · `policy` · `risk` · `approval` 七类字段；
   冻结的 `audit_logs` 列集**不含** `subject_type/subject_id` · `delegator` · `decision` · `policy` · `approval`
   （仅有 `reason` / `risk_level` / `metadata`）。⇒ 须裁定这七类**落列**还是**落 `metadata`**（见 `OQ-P10-05`，**候选 FROZEN vs SCHEMA 冲突**）。

**零陈旧声明**：全仓扫描"P10 已实现 / events 已建表 / audit_logs 已落库" = **0 命中**（§16）。

---

## 2. Baseline（§3 实测 · 2026-09-25）

| 项 | 值 | 证据 |
|---|---|---|
| `git log -1 --oneline` | `034ee97 feat(authz): implement authorization model and enforcement` | 命令 |
| HEAD（full） | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` | 命令 |
| `git tag --list` | **8** 个（含 `UAP-V0.1.8-AUTHORIZATION`） | 命令 |
| `git remote -v` | **空**（remote = none；从未 push） | 命令 |
| `alembic heads` | **`0012_authz_enforcement (head)`**（单头） | 命令 |
| `alembic history` | **12** 个 revision，线性链 `<base> → 0001 → … → 0012` | 命令 |
| `alembic current` | **NOT EXECUTED**（PostgreSQL 未运行：`connection to server at 127.0.0.1:5432 failed`）—— 环境限制，非缺陷 | 命令（stderr） |
| `git status --short` | 9 项，**全部为 `.md`**（4 `M` + 5 `??`），均为**前序已授权轮的 STAGE 3 文档**，非本轮产物 | 命令 |

**受保护迁移 SHA-256（§3 要求逐项记录）**：

```text
0010_b1_6_ai_gateway.py                 6d9907237f80e9da4acdff86c8da371af721fec3dccbe00d7e1c3035ab1b0322
0011_p09_agent_tool_permission.py       cdaf8383630335db92cfe54f12e6b65385ea1b4273e86653026afc80893f9f57
0012_authz_enforcement.py               5ecd1ef30b403fb432a497cb9cf70d32c6c49708d341ab6ad029c19b22b3171a
```

> `0010` / `0011` 与前序轮记录值**逐字节一致**；`0012` 自 STAGE 2 落库后未变。**无 hash 变化 ⇒ 无 HARD STOP**。

---

## 3. P10 SCOPE（冻结继承，非本轮发明）

### 3.1 权威定义（原文）

| 来源 | 原文 |
|---|---|
| `STEP1B_SCHEMA_DEPENDENCY.md:171` | **P10** \| **Event / Audit** \| `events` → `audit_logs`（**分区父表 + 初始子分区**） |
| `D-PLAT-09`（FROZEN） | 阶段顺序 **`P10 → P11 → P12 → P13 → Runtime`**（路线 A） |
| `STEP1B_SCHEMA_DEPENDENCY.md:172` | **P11** = Triggers / 跨表约束；**必须在 seed 前全部就位** |
| `STEP1B_SCHEMA_DEPENDENCY.md:173` | **P12** = Indexes（非 PK 索引） |
| `STEP1B_SCHEMA_DEPENDENCY.md:174` | **P13** = Seed / built-in data |
| `STEP1B_SCHEMA_DEPENDENCY.md:193` | `P00-P10 均无 seed 需求；P13 才有 seed。所有 trigger（P11）必须先于 P13 seed。` |
| `CORE_DOMAIN_MODEL` §1.6 | Event / Audit 域 = `events`（**at-least-once** 事务性 outbox + 事件日志）· `audit_logs`（合规审计，**不可变**） |

### 3.2 IN SCOPE（P10 交付面）

```text
events      —— 分区父表 + 初始子分区（含 outbox 状态列，见 OQ-P10-01）
audit_logs  —— 分区父表 + 初始子分区（不可变）
两者 PK = (id, occurred_at)，PARTITION BY RANGE (occurred_at)
建表级约束：PK / CK / NN / NULL 策略（按 STEP1B_CONSTRAINT_MATRIX §7 冻结值）
```

### 3.3 OUT OF SCOPE（**严格排除**，除非既有权威文档明确证明属于 P10）

```text
✗ authorization implementation           （已属 STAGE 2，已交付）
✗ tool execution 实施                    （属 Tool Runtime）
✗ agent runtime persistence              （属 D-AGENT-13：agent_runs / agent_run_steps，非 P10）
✗ worker framework                       （D-AGENT-12：禁 Celery / Redis Queue / RabbitMQ）
✗ AI Gateway runtime                     （0010 仅 schema；runtime 独立）
✗ business event implementation          （Domain 面未定义）
✗ outbox 投递 worker 实施                 （阶段归属见 OQ-P10-18；本轮禁 worker implementation）
✗ API 实施 / 审计查询端点                  （API implementation 本轮禁止）
✗ approval 载体                           （D-AUTH-11：归 Tool Runtime / P10 边界待裁）
```

> **边界纪律**：§1 明令"不得把 P10 扩展成 …… 除非现有权威文档明确证明其属于 P10 已冻结范围"。
> 上列 OUT 项**均无**权威文档支持其属 P10 ⇒ **一律排除**。

---

## 4. Dependencies（四类严格分离 · §5 要求）

> 指令 §5 要求严格区分 `design dependency` / `implementation dependency` / `schema dependency` / `runtime dependency`。

| 类型 | 内容 | 证据 |
|---|---|---|
| **schema dependency** | `events` / `audit_logs` 依赖 **`users`（P01）** 存在（拓扑必须）；`tenant_id` / `space_id` **无强制 FK**（事实日志，避免租户长期历史阻塞 purge）⇒ **不构成对 tenants/spaces 的强依赖** | `STEP1B_SCHEMA_DEPENDENCY.md:82-83` · `:269` |
| **design dependency** | P10 表定义依赖 STEP 1-A 冻结设计（`CORE_DOMAIN_MODEL` §1.6/§8/§11/§12 · `ER_MODEL` §6 · `STEP1B_EVENT_OUTBOX.md`）；P10 **依赖 P11 交付 `tg_audit_immutable`**（见 `OQ-P10-11`）；P12 索引依赖 P10 表存在 | 文档 |
| **implementation dependency** | P10 实施（migration `0013`）**依赖 P09 完成**（已 ✅）与 Alembic 单头状态（已 ✅ `0012`） | 命令 |
| **runtime dependency** | **P10 不依赖任何 Runtime**；反之 **Agent Runtime 依赖 P10**（`D-AGENT-15`：事件/审计面 → P10；`D-AUTH-15`：授权审计 persistence → P10；`D-AUTH-22`：ID persistence → P10）⇒ **单向**：`Runtime → P10`，**不存在 P10 被 Runtime 反向依赖** | `D-AGENT-15` · `D-AUTH-15/22` |

**阶段顺序依赖（实测与冻结一致）**：

```text
P09 (0011) ✅ ──▶ P10 (0013, 待授权) ──▶ P11 triggers ──▶ P12 indexes ──▶ P13 seed
                   ▲                                      ▲
                   └── P10 必须先于 P11 存在（triggers 引用的表）
                       P10 必须先于 P12 存在（ix_events_* / ix_audit_* 建在 P10 表上）
                       P10 无 seed（P00–P10 无 seed）
```

---

## 5. Existing Substrate（§5 实测 · 已存在但未实施）

> **关键结论**：P10 的 **表与 migration = 0**；但**契约层与承载面已有部分实现**。
> 以下为**只读实测**，逐项标注"已存在 / 未实施"。

| 对象 | 状态 | 实测内容 |
|---|---|---|
| `core/event/interfaces.py` | **已存在（契约）** | `DomainEvent`（`type` / `tenant_id`（**非空**）/ `actor_id?` / `space_id?` / `payload` / `id` / `occurred_at` / `schema_version`）；`EventBus` Protocol（`publish` / `subscribe`）；`_new_id()` 用 **`uuid.uuid4()`** ⚠ |
| `core/audit/interfaces.py` | **已存在（契约）** | `new_event_id()` = **UUIDv7**（`millis<<80 | ver7 | rand_a | var10 | rand_b`）；`AuditEvent`（含 `subject_id`/`subject_type`、`outcome`、`target_type`/`target_id`、`metadata`）；`AUDIT_OUTCOMES`；`AuditSink` Protocol；`AuthorizationDecisionAudit` |
| `services/authorization/audit.py` | **已存在（服务层，非持久）** | `AuditBoundary`：**有界内存窗口**（`deque(maxlen=capacity)`）+ 可选 `AuditSink`；自述 *"not a durable audit trail"* |
| `services/authorization/service.py` | **已存在** | 每次决策调用 `self._audit.record(...)`（`D-AUTH-15` 的 decision/reason/policy/risk/approval 面） |
| `apps/worker/main.py` | **已存在（placeholder）** | STEP 0 占位：无 job 注册，只证明进程可 boot / 收 SIGTERM / 干净退出（`"No queues are wired in STEP 0"`） |
| `infrastructure/queue/interfaces.py` | **已存在（契约）** | `QueueMessage` / `QueueClient`（`publish`/`consume`/`ack`）/ `NullQueue`；**无 broker** |
| `events` 表 / `audit_logs` 表 | **不存在** | 全仓 `*.py` / `*.sql` 中 `CREATE TABLE … events\|audit_logs` = **0 命中** |
| `migration 0013+` | **不存在** | `ls migrations_alembic/versions/` = 12 文件；匹配 `0013+` = **0** |
| `infrastructure/events*` / `infrastructure/audit*` | **不存在** | `infrastructure/` = `cache database logging monitoring queue storage`（无 events/audit） |

**既有 migration 的显式排除（原文，证明 P10 未被实施）**：

```text
0007  * 不创建 permissions / groups / audit_logs / agents / tools / AI / events / Domain 表
0008  * 不创建 agents / agent_versions / agent_permissions / ai_* / events / audit_logs / Domain 表
0010  * 不含 events / audit_logs（P10）· 不含 resource_relations
0011  * 不创建 events / audit_logs（P10）· 不创建 Domain 表 · 不改动 0001–0010 建立的任何对象
0012  * 不创建 events / audit_logs / approval_requests（P10 / Tool Runtime）
```

**冻结决策的显式未实施声明**：

```text
D-AUTH-15  当前 Audit Persistence：DEFERRED TO P10。  禁止：本轮不得创建 events / audit_logs。
D-AUTH-22  具体 persistence implementation 属 P10。     禁止：不得在 P10 之外创建 events / audit_logs。
D-AGENT-13 不得把 Audit Event 与 Run Step 混成一个表；events / audit_logs 归 P10，保持独立。
D-AGENT-15 不得提前创建 P10 persistence。
```

---

## 6. Schema Proposal（**继承冻结设计**，非新造）

> 以下**逐字段来自既有权威文档**，本轮**不改写、不新增**。
> 标注 `[继承]` = 冻结文档已定；`[待裁]` = 本 PREP 提出的 OQ 点。

### 6.1 `events`（at-least-once transactional outbox + 事件日志）

| 项 | 内容 | 来源 |
|---|---|---|
| PK | `(id, occurred_at)` | `CORE` §1.6 · `CONSTRAINT` §7 |
| 分区 | `PARTITION BY RANGE (occurred_at)` | `DEPENDENCY` §9 |
| 字段 | `event_type` · `schema_version int` · `tenant_id NULL` · `space_id NULL` · `actor_type NULL` · `actor_id NULL` · `subject_type NULL` · `subject_id NULL` · `payload jsonb NOT NULL` · `correlation_id NULL` · `causation_id NULL` · `occurred_at` · `status` · `worker_id NULL` · `claimed_at NULL` · `lease_expires_at NULL` · `attempts int DEFAULT 0` · `next_attempt_at NULL` · `last_error NULL` · `delivered_at NULL` · `created_at` | `CORE` §1.6 · `EVENT_OUTBOX` §1 |
| CK | `event_type ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$'` · `status IN ('pending','claimed','delivered','dead')` · `attempts >= 0 AND attempts <= 100` | `CONSTRAINT` §7 |
| NN | `id, event_type, schema_version, payload, occurred_at, status, attempts, created_at` | `CONSTRAINT` §7 |
| trigger | **无**（M：claim 状态迁移由应用层 CAS 完成，不加 trigger） | `TRIGGER_INVENTORY` §M |
| FK | **无强制 FK**（`tenant_id` / `space_id` 仅记录） | `DEPENDENCY` §1.7 · `:269` |
| 状态机 | `pending → claimed → delivered`；`pending → claimed → pending`（重试，`attempts++`）；`pending → claimed → dead`（超阈值） | `CORE` §8.2 |
| 投递 | **CAS claim**（单行 `UPDATE … WHERE status='pending'` 兼作乐观锁）；`FOR UPDATE SKIP LOCKED` 仅性能优化；lease 60s；Reaper 30s 周期回收 | `EVENT_OUTBOX` §2/§3 |
| 承诺 | **at-least-once**，**绝不承诺 exactly-once**；消费方按 `event_id` 幂等 | `EVENT_OUTBOX` 首行 · `CORE` §8.2 |
| `[待裁]` | outbox 状态列是否全部属 P10 DDL（`OQ-P10-01`）· 生产者写入契约（`OQ-P10-03`）· `event_type` 命名空间与 `schema_version` 兼容（`OQ-P10-04`） | — |

### 6.2 `audit_logs`（合规审计 · 不可变）

| 项 | 内容 | 来源 |
|---|---|---|
| PK | `(id, occurred_at)` | `CORE` §1.6 · `CONSTRAINT` §7 |
| 分区 | 按月 | `CORE` §1.6 |
| 字段 | `occurred_at` · `tenant_id NULL` · `space_id NULL` · `actor_type` · `actor_id NULL` · `actor_ip inet NULL` · `actor_user_agent text NULL` · `action` · `resource_type NULL` · `resource_id NULL` · `classification` · `result` · `risk_level` · `reason NULL` · `correlation_id NULL` · `request_id NULL` · `metadata jsonb`（**写入前已脱敏**）· `created_at` | `CORE` §1.6 · `CONSTRAINT` §7 |
| CK | `result IN ('success','denied','error')` · `risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` · `classification IN (四级)`（可空按策略） | `CONSTRAINT` §7 |
| NN | `id, occurred_at, actor_type, action, result, risk_level, metadata, created_at` | `CONSTRAINT` §7 |
| 不变性 | **无 `updated_at` / 无 `deleted_at`**；DB 角色**仅 `INSERT, SELECT`**；`tg_audit_immutable`（BEFORE UPDATE/DELETE ⇒ RAISE）**双保险** | `CORE` §1.6 · §13 · `TRIGGER_INVENTORY` §L |
| `[待裁]` | `D-AUTH-15` 七类字段（`subject`/`delegator`/`decision`/`policy`/`approval` 等）落列 vs 落 `metadata`（**`OQ-P10-05`，候选冲突**）· 写入同步/异步（`OQ-P10-07`）· 脱敏执行点（`OQ-P10-08`） | — |

### 6.3 次要文档不一致（**仅登记，本轮不修改任何文件**）

| # | 事项 | 证据 |
|---|---|---|
| D-1 | `ER_MODEL` §6 的 `events` 字段列表**未列 `created_at`**，而 `CONSTRAINT_MATRIX` §7 的 `NN` **含 `created_at`** | 两文档对照 |
| D-2 | `ER_MODEL` §6 把 `tenant_id` / `space_id` 标注为 `FK "nullable"`，而 `DEPENDENCY` §1.7 / §9 明确 **"无强制 FK"** | 两文档对照 |
| D-3 | `D-AUTH-22` 的**理由**段称"现 `core/audit._new_id()` 使用 `uuid.uuid4()`，为唯一异形方" —— **已过期**（STAGE 2 已修为 UUIDv7）；当前异形方为 **`core/event`** | `core/audit/interfaces.py` · `core/event/interfaces.py` |

> 依指令 §5：**先记录证据，不得擅自修改**；上表**不修改**任何文档，仅作为 `OQ-P10-02` / 契约层的输入。

---

## 7. Partition Proposal（继承 + 待裁）

**继承（冻结）**：

```text
① 建父表 PARTITION BY RANGE (occurred_at) + 【当月子分区】
② 子分区继承 PK (id, occurred_at)
③ 部分唯一索引 / 查询索引建在父表（PG 自动下推子分区）
④ events / audit_logs 的 tenant_id / space_id 【不设强制 FK】
⑤ migration downgrade：先 DROP 子分区，再 DROP 父表
⑥ 到期整分区 drop（避免大表 DELETE 的锁与膨胀）
```

来源：`STEP1B_SCHEMA_DEPENDENCY.md:265-270` · `CORE_DOMAIN_MODEL` §13（「分区与留存」行）。

**待裁**：

| # | 问题 |
|---|---|
| `OQ-P10-09` | 分区粒度确认（月）· 初始子分区范围（当月起多少个月）· **是否建立 `DEFAULT` 分区**兜底（影响 attach/detach 与 `occurred_at` 越界写入行为） |
| `OQ-P10-10` | 分区创建与 retention 执行的**运维模型**：沿用 B1-6 先例 **`D-3 = D`（分区维护与保留清理 = 手工运维，自动化延后）** 还是 P10 交付脚本？ |

---

## 8. Retention Proposal（继承 · 已冻结数值）

| 对象 | 策略 | 保留期 | 来源 |
|---|---|---|---|
| `events` | **hard delete**（分区） | **投递后 30 天**（`delivered` 后清理）；**`dead` 行保留 90 天**供人工复盘 | `CORE` §11 · §1.6 · `EVENT_OUTBOX` §6 |
| `audit_logs` | **immutable + 分区 drop**（**不做行级删除**） | **默认 365 天（可配置）** | `CORE` §11 · `CONSTRAINT` §7 |
| 全局保留默认值 | audit **365d** · events **30d** · tool_executions 90d · ai_request_logs 90d · 软删 30d 后 purge · 归档 90d 后 purge | — | `CORE` §11 |

**关键约束（`STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` §10）**：

```text
【禁止】downgrade 删除审计/不可变类数据
（audit_logs 分区按保留期 drop，【不随版本回滚】）
```

**待裁**：`OQ-P10-10`（谁执行 drop、以何权限执行）· 开放项 `CORE` §14 **Q5**（"审计保留期 365 天是否满足合规要求？**需业务方确认**"）—— 该问题**早于本轮已登记为开放项**，本轮**不代为裁定**。

---

## 9. Security Invariants（继承 · 强制）

| # | 不变式 | 来源 |
|---|---|---|
| S-1 | **最小权限 DB 角色**：`uap_app`（DML）/ `uap_migrator`（DDL，仅迁移窗口）/ `uap_readonly`；应用运行时不持 DDL | `CORE` §13 |
| S-2 | **审计不可变**：`audit_logs` 仅授予 `INSERT, SELECT`；`BEFORE UPDATE/DELETE` trigger 抛异常（双保险） | `CORE` §13 · `TRIGGER_INVENTORY` §L |
| S-3 | **FAIL CLOSED**：授权/策略失败 ⇒ `DENY`（`D-AUTH-12`），**不得**因审计写入失败放行受控操作 | `D-AUTH-12` |
| S-4 | **租户隔离**：`tenant_id` 复合索引 + 应用层强制断言 + 越权写入审计（RLS 可选，见 `OQ-P10-15`） | `CORE` §2.8 · §13 |
| S-5 | **脱敏**：`audit_logs.metadata` **写入前已脱敏**；与日志统一走 `redaction`；**CRITICAL 只存摘要** | `CORE` §13 · §1.6 |
| S-6 | **密钥/秘密**：任何表**不得**存 API Key 明文（CI 扫描 + 测试守卫）；`actor_ip` / `user_agent` 属 PII 面 | `CORE` §13 |
| S-7 | **三类审计分离**（`D-AUTH-15` / `D-AGENT-13`）：**Agent Run Audit** ≠ **Authorization Decision Audit** ≠ **Tool Execution Audit**；以 `run_id` / `correlation_id` 关联但 **不得合并为同一载体** | `D-AUTH-15` · `D-AGENT-13` |
| S-8 | **`resource_scope` 不得进入事件/审计载荷的授权语义**（Legacy Opaque，`D-AUTH-23`） | `D-AUTH-23` |

---

## 10. Audit / Event Semantic Boundary（§8.1 冻结）

| 维度 | `events`（Event） | `audit_logs`（Audit） |
|---|---|---|
| 语义 | "发生了什么"（**事实**） | "谁对什么做了什么、结果如何"（**责任**） |
| 消费方 | 系统内部（投递 / 集成 / Webhook） | 合规 / 安全 / 用户可见历史 |
| 可否删除 | **投递后可清理**（30d） | **不可变**，只按保留期整分区 drop（365d） |
| 是否重放 | **可** | **不可**（重放会产生误导） |
| 是否含决策理由 | **否** | **是**（`reason` / `risk_level`） |
| 载体 | `events`（outbox） | `audit_logs` |
| ER 关系 | `events ||--o| audit_logs : "may be mirrored by"`（**弱关系，无 FK**） | 同左 |

来源：`CORE_DOMAIN_MODEL` §8.1 · `ER_MODEL` §6。

**待裁**：`OQ-P10-12`（是否设**显式 linkage 列**，如 `audit_logs.event_id` / `events.audit_id`）。

### 10.1 五类承载面分类（§4 要求 · 不得混为一体）

| 类别 | 载体 | P10 范围 | 说明 |
|---|---|---|---|
| **Event** | `events` 表 | ✅ **P10** | 领域事实 + outbox；at-least-once；可重放 |
| **Audit** | `audit_logs` 表 | ✅ **P10** | 合规不可变；不可重放；含 reason/risk |
| **Operational log** | `infrastructure/logging`（structured JSON + redaction） | ❌ **非 P10** | 运行期诊断；可丢弃；**不入 DB 表** |
| **Trace** | `trace_id`（日志信封字段） | ❌ **非 P10** | 关联标识，非载体；P10 仅承接列 `correlation_id` / `request_id` |
| **Metric** | 未定义（未来 monitoring 面） | ❌ **非 P10** | 非 P10 授权面 |

> **纪律**：`event` / `audit` **不得**与 operational log 混为一体（本轮指令 §4）。
> 待裁：`OQ-P10-17`（边界的形式化声明与守卫）。

---

## 11. Runtime Integration（**仅接口关系，不实施** · §4 要求）

```text
Agent    Runtime ──▶ P10  （D-AGENT-15：run 观测需可关联；事件/审计面 → P10）
Authorization    ──▶ P10  （D-AUTH-15：Authorization Decision Audit persistence = DEFERRED TO P10）
Tool     Runtime ──▶ P10  （D-AUTH-15：Tool Execution Audit 边界；载体待 Tool Runtime 裁定）
future business  ──▶ P10  （业务事件经 events 表写入，事务内）
```

| 关系 | 方向 | 性质 | 依据 |
|---|---|---|---|
| P10 → Agent Runtime | **无** | 不存在反向依赖 | 实测：P10 无 Runtime 前置 |
| Agent Runtime → P10 | 单向 | **runtime dependency**（关联键面） | `D-AGENT-15` |
| Authorization → P10 | 单向 | **persistence dependency**（已实现契约，未落库） | `D-AUTH-15` |
| Tool Runtime → P10 | 单向 | **边界待裁** | `D-AUTH-15` |
| P10 → P11 | P11 依赖 P10 | **schema + trigger dependency**（`tg_audit_immutable`） | `TRIGGER_INVENTORY` §L |
| P10 → P12 | P12 依赖 P10 | **index dependency**（`ix_events_*` / `ix_audit_*`） | `INDEX_STRATEGY` |

**待裁**：`OQ-P10-16`（`run_id` 等 Runtime 关联键的载体：列 vs `metadata`）。

---

## 12. 连带同步面（P10 落地时**必须**同步 · 血泪教训 §4）

> 前序轮实测教训：**阶段推进的连带同步面大于文档预估**。以下为 P10 落地时的**已知**同步面（**本轮不修改任何文件**）。

| # | 同步面 | 数量 | 证据 |
|---|---|---|---|
| 1 | `FORBIDDEN_TABLES` 含 `events` / `audit_logs` 的既有集成测试 | **8** 文件 | `test_{identity,rbac,tenant_space,resource_acl,tool_registry,ai_gateway,agent_tool_permission,authz_enforcement}*_schema.py`（其中 4 处为命名常量 `FORBIDDEN_TABLES`） |
| 2 | 断言 alembic head = `0012_authz_enforcement` 的测试 | **15** 文件 | `grep -rln 0012_authz_enforcement tests/`（含 `test_alembic_smoke` / `test_migration_lock` / `test_generate_build_info`） |
| 3 | 迁移 docstring 中的"不含 events / audit_logs"声明 | **5** migration（0007/0008/0010/0011/0012） | 原文见 §5 |
| 4 | 架构守卫（`tests/architecture/`） | 现有 **2** 文件，**无** event/audit 相关守卫 ⇒ P10 实施期需新增 | `ls tests/architecture/` |
| 5 | `tests/` 总规模 | **35** 文件（全量回归基线 542 passed） | 命令 |

---

## 13. Consistency Check（§5 要求 · 实测）

| 检查 | 结果 | 证据 |
|---|---|---|
| `events` **已实现**？ | **否** | `CREATE TABLE … events` 命中 0 |
| `audit_logs` **已实现**？ | **否** | 同上 |
| **P10 已实现**？ | **否** | 无 `0013+`；无 P10 gate 报告 |
| **P10 migration 已存在**？ | **否** | 12 文件，最大 `0012` |
| **audit persistence 已存在**？ | **否**（仅**内存**窗口） | `services/authorization/audit.py` 自述 *"not a durable audit trail"* |
| 陈旧"P10 已实现"描述 | **0 命中** | `grep -rniE "P10.{0,60}(implemented\|已实现\|已实施\|已完成)" docs/` = 0 |
| 陈旧"events/audit_logs 已建表"描述 | **0 命中** | 同向 grep = 0 |
| 陈旧描述处置 | **仅记录证据，未修改任何文件** | 指令 §5 |

**候选冲突（建议单列裁定，本轮不代裁）**：

| ID | 冲突 | 性质 |
|---|---|---|
| **`C-1`** | `D-AUTH-15`（要求 audit **至少可表达** 7 类字段）vs 冻结 `audit_logs` 列集（**不含** subject/delegator/decision/policy/approval） | **`FROZEN` vs `SCHEMA` 候选冲突** ⇒ `OQ-P10-05` |
| **`C-2`** | `D-AUTH-22` 理由段（"`core/audit` 为唯一异形方"）vs 实测（`core/audit` 已 UUIDv7；`core/event` 仍 uuid4） | **`DECISION` 描述 vs `CODE` 现状** ⇒ `OQ-P10-02` |
| **`C-3`** | `core/event.EventBus`（内存总线）vs 冻结 outbox（表 + CAS claim） | **`CONTRACT` vs `SCHEMA DESIGN`** ⇒ `OQ-P10-02` |
| **`C-4`** | `D-PLAT-10` 待办「`L`（`tg_audit_immutable`）**属 P10，须与 P11 明确分界**」—— 分界尚未定义 | **`DECISION` 待办未闭合** ⇒ `OQ-P10-11` |

> 依 **`PLATFORM_DECISION_LOG.md` Charter §7**（跨决策扫描义务）：上述 4 项已登记；**P10 Decision Freeze 前必须完成正式跨决策扫描**（本轮为 PREP，扫描结果见本表 + 验收矩阵）。

---

## 14. Open Questions（`OQ-P10-01` … `OQ-P10-18` · 全部 `PENDING`）

> **全部 `HUMAN DECISION = PENDING` / `STATUS = PROPOSED`**。已冻结者**不重复设 OQ**：
> 表结构/约束（`CORE` §1.6 + `CONSTRAINT` §7）· 分区方式（`DEPENDENCY` §9）· 保留期数值（`CORE` §11）·
> 索引清单（`INDEX_STRATEGY` §2）· 不可变性（`TRIGGER_INVENTORY` §L）· UUIDv7（`D-AUTH-22`）·
> 阶段顺序（`D-PLAT-09`）· 三类审计分离（`D-AUTH-15`/`D-AGENT-13`）。

| OQ | 领域 | 问题 | 建议方向（**仅技术后果**） |
|---|---|---|---|
| `OQ-P10-01` | Event | outbox 状态列（`status`/`worker_id`/`claimed_at`/`lease_expires_at`/`attempts`/`next_attempt_at`/`last_error`/`delivered_at`）**是否全部属 P10 DDL** | 全属（冻结设计已含）⇒ 一次建齐，避免后续加列 |
| `OQ-P10-02` | Event | `core/event` 契约对齐：`uuid4 → UUIDv7`；`EventBus` 与 outbox 的存续关系 | 对齐 UUIDv7；`EventBus` 降为**进程内**契约，投递**只能**经 outbox |
| `OQ-P10-03` | Event | **生产者边界**：P10 是否定义 events **写入契约**（谁写、强制同事务） | 定义契约，不改任何调用方 |
| `OQ-P10-04` | Event | `event_type` 命名空间注册 与 `schema_version` 兼容策略 | 命名空间沿用 CK 正则（不建注册表）；`schema_version` 仅单调递增 |
| `OQ-P10-05` | Audit | **`C-1`**：`D-AUTH-15` 七类字段 —— **落列**还是**落 `metadata`** | 落 `metadata`（`audit_logs` 列集冻结，不动 schema）；**或** Human 裁定加列 ⇒ 须显式 supersession |
| `OQ-P10-06` | Audit | `core/audit.AuditEvent` **契约扩字段**（`D-AUTH-15` 影响范围）的落地形态 | 扩契约对象，保持与 `audit_logs` 列 + `metadata` 的映射显式 |
| `OQ-P10-07` | Audit | audit 写入**同步 / 异步**策略（`STEP1A` R6：HIGH/CRITICAL 同步，LOW 异步批量 + outbox 补偿） | 采纳 R6（风险分级）；**FAIL CLOSED 不受影响** |
| `OQ-P10-08` | Audit | `metadata` **脱敏执行点**（应用层 redaction）与 DB 侧保护 | 应用层强制 + 测试守卫；DB 侧不加转换逻辑 |
| `OQ-P10-09` | Storage | 分区粒度 / 初始子分区范围 / **`DEFAULT` 分区**兜底 | 月分区 + 初始当月；`DEFAULT` 分区**需谨慎**（影响 attach），倾向不建 |
| `OQ-P10-10` | Storage/OPS | 分区创建 + retention 执行的**运维模型**（沿用 `D-3 = D` 手工？） | 沿用 B1-6 先例（手工运维，自动化延后），保持平台一致 |
| `OQ-P10-11` | Storage | **`C-4`**：`tg_audit_immutable`（L）落点 —— P10 内联 vs P11 集中 | 按 `D-PLAT-10` 集中 P11；**但须显式写"分界"**（本 OQ 即该待办） |
| `OQ-P10-12` | Storage | `events` ↔ `audit_logs` **显式 linkage 列** | 不建（ER 已定义为弱关系 `may be mirrored by`）；靠 `correlation_id` 关联 |
| `OQ-P10-13` | Storage | **DB 角色与 `GRANT`** 归属（`audit_logs` 仅 `INSERT/SELECT`） | P10 migration 内 `GRANT`（迁移期一次性）；或运维脚本 —— 需裁定 |
| `OQ-P10-14` | Security | `classification` 在 audit 的存储 + **CRITICAL 只存摘要** | 沿用 `CORE` §13（摘要）；HIGHLY_CONFIDENTIAL **禁降级** |
| `OQ-P10-15` | Security | 是否在 P10 **引入 RLS** | 倾向**不引入**（`CORE` §13 标"可选 Q1"；既有 `D-B14` 边界亦声明"不引入 RLS"） |
| `OQ-P10-16` | Runtime | Runtime 关联键（`run_id` 等）的载体：列 vs `metadata` | 落 `metadata` + `correlation_id`（不动冻结列集） |
| `OQ-P10-17` | Boundary | 五类承载面（event/audit/log/trace/metric）边界的形式化 + 守卫 | 形式化声明 + 新增 `tests/architecture` 守卫 |
| `OQ-P10-18` | Boundary | outbox **投递 worker** 的阶段归属与 P10 交付边界 | P10 = 表 + 状态机契约；**worker 实施归后续阶段**（`D-AGENT-12` 禁 framework） |

---

## 15. Implementation Gate

```text
P10 PREP（本轮）              = ALLOWED（本报告 + 决策包 + 验收矩阵）
P10 DECISION FREEZE           = NOT YET（18 项 OQ 全部 PENDING）
P10 IMPLEMENTATION            = NOT AUTHORIZED

D-PLAT-09 路线 A（未 supersede）：P10 → P11 → P12 → P13 → Runtime
Runtime Implementation Gate  = CLOSED（D-AGENT-16；与本轮无关但继续有效）

实施前置（全部满足方可开启）：
  ① Human Decision Freeze（OQ-P10-01…18 全部裁定）
  ② 显式实施授权
  ③ 跨决策扫描（Charter §7）已完成并留档
  ④ P09 保护面复核（0010/0011/0012 逐字节未变）
```

---

## 16. 本轮禁止面（§6）与实测结果

| 禁止项 | 实测 |
|---|---|
| 创建 `events` 表 | **未发生**（`CREATE TABLE … events` = 0） |
| 创建 `audit_logs` 表 | **未发生** |
| 创建 partition / index / trigger | **未发生**（无 0013+；无 DDL 脚本） |
| 创建 migration `0013` | **未发生**（versions/ = 12 文件） |
| `alembic upgrade` / `downgrade` | **未执行**（仅 `heads` / `history`；`current` 因 DB 未运行而 NOT EXECUTED） |
| 写入 seed | **未发生** |
| 修改 `services/` / `infrastructure/` / `tests/` | **未发生**（`git diff` 全空） |
| 修改 application code / configuration | **未发生** |
| commit / tag / push | **未发生**（HEAD 仍 `034ee97`；tags 仍 8） |
| 修改既有文档 | **未发生**（既有 9 份 `.md` 的改动**全部来自前序已授权轮**，本轮 **0 追加**） |

---

## 17. Exit Criteria

✓ Baseline verified ✓ P10 scope 与边界明确（含 OUT 面）✓ 四类依赖分离 ✓ Existing substrate 实测 ✓
Schema 提案（继承，非新造）✓ 分区提案 ✓ 保留期提案 ✓ 安全不变式 ✓ Event/Audit 语义边界 ✓
五类承载面分类 ✓ Runtime 接口关系（仅设计）✓ 连带同步面登记 ✓ 一致性核查（0 陈旧声明 + 4 候选冲突）✓
OQ 18 项（全 PENDING）✓ **零实施**

---

## 18. HARD STOP 触发面（本轮实测未触发）

`DDL / DML` · `migration 创建或修改` · `schema / runtime / API / worker 实施` · `测试代码修改` ·
`应用代码修改` · `配置修改` · `commit / tag / push` · `修改既有文档` —— **本轮零命中**。

---

## 19. FINAL

```text
P10 PREP = COMPLETE
P10 DECISION FREEZE = NOT YET
P10 IMPLEMENTATION  = NOT AUTHORIZED
DDL / DML / migration / code / test / config / commit / tag / push = 0
```

---

**配套文档**：[`P10_DECISION_RESOLUTION.md`](./P10_DECISION_RESOLUTION.md)（18 项 OQ 逐项决议材料 ·
`HUMAN DECISION = PENDING` ×18）· [`P10_ACCEPTANCE_MATRIX.md`](./P10_ACCEPTANCE_MATRIX.md)（脚本实测）。

**END OF P10 PREP REPORT（2026-09-25 · READ-ONLY）**

---

## 20. 后续注记（**append-only** · 遵 `PLATFORM_DECISION_LOG.md` Charter §5.2）

> **[`D-P10-01`…`D-P10-18` 注记 · 2026-09-25]** P10 Decision Freeze 完成：18 项 OQ 全部冻结；
> 本 PREP 的全部 PROPOSED 内容据此进入契约层。
> 关联：本文档 §13（一致性核查）· §14（OQ 表）· §15（Implementation Gate）· §19（FINAL）。
> 性质：**状态更新 + 交叉引用**。**不修改本文档既有段落、表格行或任何结论。**

**状态更新对照**：

| 项 | 本文档原状（2026-09-25 PREP） | **Decision Freeze 终态（2026-09-25）** | 冻结条目 |
|---|---|---|---|
| §14 18 项 OQ | `HUMAN DECISION = PENDING`（`PROPOSED`） | **18 / 18 `FROZEN`** | `D-P10-01`…`D-P10-18` |
| §13 `C-1`（`D-AUTH-15` 五类字段 vs 列集） | 候选冲突（未代裁） | **RESOLVED** —— 采用**结构化 `metadata`**；**不加 first-class column**；**不产生 `D-AUTH-15` supersession** | `D-P10-05` |
| §13 `C-2`（`D-AUTH-22` 理由段过期） | 登记 | **CLARIFIED** —— append-only clarification：现行实现契约已 UUIDv7 对齐；历史 "`core/audit` exception" 表述作废 | `D-P10-02` + `D-AUTH-22` 注记 |
| §13 `C-3`（`EventBus` vs outbox） | 登记 | **RESOLVED** —— 冻结 `EventBus != Outbox`；Outbox = durable authority；`EventBus` = 可选进程内辅助（三项 MUST NOT） | `D-P10-02` |
| §13 `C-4`（`L` 与 P11 分界） | 登记（`D-PLAT-10` 待办 ④） | **RESOLVED** —— **`tg_audit_immutable` = P10-owned**；`P10 = persistence + audit-local immutability`；**消除可变窗口** | `D-P10-11` |
| §5 `core/event` 漂移 | 发现（uuid4 + `EventBus`） | **冻结裁定**：ID = **UUIDv7 canonical**（`uuid4()` = 遗留，**实施期**修正）；**本轮不得修改 `core/event/interfaces.py`** | `D-P10-02` |
| §19 FINAL `P10 DECISION FREEZE = NOT YET` | `NOT YET` | **`PASSED`** | — |
| §19 FINAL `P10 IMPLEMENTATION = NOT AUTHORIZED` | `NOT AUTHORIZED` | **不变**（仍 `NOT AUTHORIZED`；**新增** `P11 = NOT AUTHORIZED`） | — |

**注记新增的契约层内容（来源 = Human Decision 正文，非本 PREP 的追认）**：

```text
① P10 交付面**扩张**至含 Audit-local immutability protection
   （tg_audit_immutable = P10-owned）—— 消除 "audit exists but mutable" 窗口
② EventBus 与 Outbox 的**关系冻结**（EventBus != Outbox；三项 MUST NOT）
③ OQ-P10-05 采用结构化 metadata 的**三条强约束**（结构化/可验证/可追踪 · 非垃圾桶 · 不绕过 canonical fields）
④ Domain Event ID = UUIDv7 canonical 的**实施期修正义务**（本轮不改 core/event）
```

**新增配套内容**：`PLATFORM_DECISION_LOG.md` 的 P10/P11 边界节 · EventBus≠Outbox 节 · 附录 G（含 `G.7` 跨决策扫描）。

**未触碰**：`DDL` / `DML` / migration（含 0013+）· `core/` / `services/` / `infrastructure/` / `tests/` /
`apps/` / `config` · `0010` / `0011` / `0012` · `events` / `audit_logs` / outbox 表 · `commit` / `tag` / `push`。

**END OF P10 PREP REPORT（2026-09-25 · READ-ONLY）**
**后续注记追加：P10 Decision Freeze（`D-P10-01`…`D-P10-18` 全部 `FROZEN`；`C-1`…`C-4` 已处置），2026-09-25**
