# P10 — IMPLEMENTATION CONTRACT（Event / Audit）

> ## 状态
>
> ```text
> DESIGN FROZEN
> IMPLEMENTATION AUTHORIZED（2026-09-25 Human Authorization）
> IMPLEMENTED · ACCEPTED（0013_p10_event_audit）
> ```
>
> 本文件是设计契约。**契约轮**（2026-09-25 早）时为零实施；**实施轮**（同日）已按
> `UAP P10 — IMPLEMENTATION AUTHORIZATION` 落地全部 `IMPLEMENT` 条目（`P10-F01`…`P10-F14`），
> 见 **§16 实施记录**。`DEFER` / `OUT OF SCOPE` 条目**未**因此转为实施。
> `P11 IMPLEMENTATION = NOT AUTHORIZED` · `P12 IMPLEMENTATION = NOT AUTHORIZED` ·
> `P13 = NOT AUTHORIZED` · `Runtime Implementation Gate = CLOSED`。
>
> **基线**：`HEAD = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` · `TAG = UAP-V0.1.8-AUTHORIZATION` ·
> `ALEMBIC HEAD = 0012_authz_enforcement` · `0013+ = ABSENT` ·
> `D-PLAT-09 = P10 → P11 → P12 → P13 → Runtime`（FROZEN / 未 supersede）。

---

## 1. 冻结依据与跨决策扫描（`§1` 要求）

### 1.1 已读取的权威来源

```text
PLATFORM_DECISION_LOG.md          （D-PLAT-01..17 · D-AUTH-01..25 · D-AGENT-01..16 ·
                                     D-P10-01..18 · D-P11-01..14 · D-P12-01..15 + 附录 G/H/I）
P10_DECISION_RESOLUTION.md · P10_PREP_REPORT.md · P10_ACCEPTANCE_MATRIX.md
STEP1B_EVENT_OUTBOX.md            （§1 表结构/状态机 · §2 CAS claim · §3 Lease Reaper ·
                                     §4 崩溃场景 · §5 幂等 · §6 死信 · §7 事务原子性）
STEP1B_SCHEMA_DEPENDENCY.md       （§1.7 无强制 FK · §9 分区表注意事项 · :171 P10 定义 · :241 trigger 归属）
STEP1B_CONSTRAINT_MATRIX.md §7    （Event / Audit 域：PK / CK / NN / NULL）
STEP1B_INDEX_STRATEGY.md          （§1 events/audit_logs 索引 → 归 P12）
STEP1B_TRIGGER_INVENTORY.md       （§L = tg_audit_immutable · §M = events 无 trigger）
CORE_DOMAIN_MODEL.md              （§1.6 Event/Audit 域 · §7 分级 · §11 保留 · §13 安全三角色）
ER_MODEL.md §6                    （Event / Audit 字段图）
```

### 1.2 跨决策扫描（Charter §7）

| 检查类 | 结果 |
|---|---|
| `D-PLAT-09` | **未 supersede**；路线 A 顺序不变；本轮不扩张 P10 为 Runtime/worker/Gateway |
| `D-AUTH-01..25` | **未被 supersede**；`D-AUTH-15`（授权审计 persistence → P10）仍逐字在位；`D-AUTH-22`（UUIDv7）为本契约 `§7` 依据 |
| `D-AGENT-01..16` | **未被 supersede**；`D-AGENT-13`（`agent_runs` 独立于 P10）/`D-AGENT-15`（可观测面 → P10）构成 `D-P10-16` 依据 |
| `D-P11-01..14` | **未被 supersede**；`L` = **P10-owned**（`D-P10-11`）与本契约 `§3` 一致；G/H/I/J 归 P11 |
| `D-P12-01..15` | **未被 supersede**；`D-P12-08` 明定 `ix_events_*`/`ix_audit_*`（7）= **P12**，本契约 `§11.5` 据此**不**把索引写入 P10 migration |
| `ACTIVE vs FROZEN` / `FROZEN vs FROZEN` 冲突 | **0** |
| `SCHEMA vs DECISION` 冲突 | **2 项登记**（`DISC-1`/`DISC-2`，见 §12）· **1 项编号冲突**（`NUM-1`，见 §13） |
| supersession 总数 | **恒 = 1**（`D-B14-08`）；本轮新增 **0** |

---

## 2. P10 Scope（**锁定，不扩张**）

```text
P10 = Event / Audit persistence
    + Outbox durable delivery model（表 + 状态机契约 + 运维 runbook）
    + audit-local immutability（tg_audit_immutable）
```

**必须保持（冻结语义）**

```text
Domain Event ID        = UUIDv7
Outbox                 = durable / reliable delivery authority
EventBus               = optional in-process auxiliary
EventBus != Outbox
Authorization Audit 五语义维度（subject / delegator / decision / policy / approval）
                       = structured metadata（不新增 first-class column）
```

**OUT OF SCOPE（P10 不得吞入）**

```text
投递 worker（→ Runtime，D-P10-18）· 队列框架绑定（D-AGENT-12）· RLS（D-P10-15）
`event_types` 注册表（D-P10-04）· events↔audit_logs linkage 列（D-P10-12）
7 条查询索引（→ P12，D-P12-08）· partition 自动化（D-P10-10 手工运维）
G/H/I/J（→ P11）· Agent Runtime persistence（D-P10-16）· 权限体系 / GRANT（OPEN-P10-1）
```

---

## 3. P10 / P11 边界（冻结原文）

```text
P10 = Event / Audit persistence + tg_audit_immutable
P11 = remaining trigger / cross-table constraints

tg_audit_immutable = P10-owned

P11 does NOT create or replace tg_audit_immutable
P10 does NOT implement G/H/I/J
（G/H/I/J = tg_acl_subject_exists · tg_acl_user_hard_delete ·
          tg_acl_role_delete_block · tg_agent_acl_expire —— 全部属 P11）
```

**硬约束**：`audit_logs` 的**基础不可变性**不得依赖 P11（`D-P10-11`；消除
"P10 implemented → audit exists but mutable → P11 later fixes immutability" 窗口）。

---

## 4. Event Model Contract（`events`）

> 字段以 **CORE §1.6 + `STEP1B_EVENT_OUTBOX` §1 + `CONSTRAINT_MATRIX` §7** 为权威（三者一致）；
> **不自行补字段**。

### 4.1 表级

| 项 | 值 | 来源 |
|---|---|---|
| table | `events` | `SD:171` |
| 分区 | **`PARTITION BY RANGE (occurred_at)`**（月分区） | `D-P10-09` · `CORE §11` |
| PK | `(id, occurred_at)` | `CONSTRAINT_MATRIX §7` · `D-P10-01` |
| UQ | **无**（PK 即 event_id） | `CONSTRAINT_MATRIX §7` |
| FK | **无强制 FK**（`tenant_id`/`space_id` 不设 FK） | `SD:82` · `SD:269` ⚠ `DISC-1` |
| trigger | **无**（claim 走应用层 CAS） | `TRIGGER_INVENTORY §M` · `D-P10-01` |
| 索引 | **7 条中 2 条归 P12**（`ix_events_dispatch` · `ix_events_tenant_type_time`） | `D-P12-08` |
| retention | **投递后 30 天**（分区 drop）；`dead` 行保留 **90 天** | `CORE §11` · `EVENT_OUTBOX §6` |

### 4.2 字段级

| # | column | type | NOT NULL | default | PK | FK | CHECK | UQ | 分区相关 | retention 相关 | 安全分级 | 来源 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-01 | `id` | `uuid`（**UUIDv7**） | ✔ | — | ✔ | — | — | — | PK 组成 | — | internal | `D-P10-02` · `D-AUTH-22` |
| E-02 | `occurred_at` | `timestamptz(3)` | ✔ | — | ✔ | — | — | — | **分区键** | 分区 drop 依据 | internal | `D-P10-09` · `CORE §10` |
| E-03 | `event_type` | `text` | ✔ | — | — | — | ✔ 正则 `^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$` | — | — | — | internal | `CONSTRAINT_MATRIX §7` |
| E-04 | `schema_version` | `int` | ✔ | — | — | — | — | — | — | — | internal | `CONSTRAINT_MATRIX §7` |
| E-05 | `tenant_id` | `uuid` | ✗ NULL | — | — | **无 FK** | — | — | 隔离谓词 | — | tenant-scoped | `SD:82` |
| E-06 | `space_id` | `uuid` | ✗ NULL | — | — | **无 FK** | — | — | 隔离谓词 | — | space-scoped | `SD:82` |
| E-07 | `actor_type` | `text` | ✗ NULL | — | — | — | — | — | — | — | internal | `CORE §1.6` |
| E-08 | `actor_id` | `uuid` | ✗ NULL | — | — | — | — | — | — | — | internal | `CORE §1.6` |
| E-09 | `subject_type` | `text` | ✗ NULL | — | — | — | — | — | — | — | internal | `CORE §1.6` |
| E-10 | `subject_id` | `uuid` | ✗ NULL | — | — | — | — | — | — | — | internal | `CORE §1.6` |
| E-11 | `payload` | `jsonb` | ✔ | — | — | — | — | — | — | — | **写入前须 redaction 纪律** | `CORE §1.6` · `D-P10-08` |
| E-12 | `correlation_id` | `uuid` | ✗ NULL | — | — | — | — | — | — | — | internal | `D-P10-16` |
| E-13 | `causation_id` | `uuid` | ✗ NULL | — | — | — | — | — | — | — | internal | `CORE §1.6` |
| E-14 | `status` | `text` | ✔ | — | — | — | ✔ `IN ('pending','claimed','delivered','dead')` | — | — | claim 扫描 | internal | `CONSTRAINT_MATRIX §7` · `D-P10-01` |
| E-15 | `worker_id` | `text` | ✗ NULL | — | — | — | — | — | — | — | internal | `D-P10-01` |
| E-16 | `claimed_at` | `timestamptz(3)` | ✗ NULL | — | — | — | — | — | — | — | internal | `D-P10-01` |
| E-17 | `lease_expires_at` | `timestamptz(3)` | ✗ NULL | — | — | — | — | — | — | Reaper 依据 | internal | `D-P10-01` |
| E-18 | `attempts` | `int` | ✔ | `0` | — | — | ✔ `>= 0` · `<= 100` | — | — | dead 判定 | internal | `CONSTRAINT_MATRIX §7` |
| E-19 | `next_attempt_at` | `timestamptz(3)` | ✗ NULL | — | — | — | — | — | — | claim 就绪性 | internal | `D-P10-01` |
| E-20 | `last_error` | `text` | ✗ NULL | — | — | — | — | — | — | — | **可能含外部错误串 ⇒ redaction** | `D-P10-01` |
| E-21 | `delivered_at` | `timestamptz(3)` | ✗ NULL | — | — | — | — | — | — | 30d 起算点 | internal | `D-P10-01` |
| E-22 | `created_at` | `timestamptz(3)` | ✔ | `now()` | — | — | — | — | — | — | internal | `CONSTRAINT_MATRIX §7` |

**`D-P10-01` 硬约束**：`status` · `worker_id` · `claimed_at` · `lease_expires_at` · `attempts` ·
`next_attempt_at` · `last_error` · `delivered_at` **全部属 P10 DDL，一次建齐**；
**不得**拆分成后续阶段加列；**不得**新增第三张表（`events` **即** outbox 载体）。

---

## 5. Audit Model Contract（`audit_logs`）

### 5.1 表级

| 项 | 值 | 来源 |
|---|---|---|
| table | `audit_logs` | `SD:171` |
| 分区 | **`PARTITION BY RANGE (occurred_at)`**（月分区） | `D-P10-09` |
| PK | `(id, occurred_at)` | `CONSTRAINT_MATRIX §7` |
| UQ | **无** | `CONSTRAINT_MATRIX §7` |
| FK | **无强制 FK** | `SD:83` |
| trigger | **仅 `tg_audit_immutable`**（`BEFORE UPDATE` / `BEFORE DELETE` → `RAISE`） | `D-P10-11` · `TRIGGER_INVENTORY §L` |
| 索引 | **5 条归 P12** | `D-P12-08` |
| retention | **365 天（可配置）**；**不做行级删除**（整分区 drop） | `CORE §11` · `CONSTRAINT_MATRIX §7` |
| 不可变 | 无 `updated_at` / 无 `deleted_at`；仅 `INSERT, SELECT` | `CORE §1.6` · `CORE §13` |

### 5.2 字段级

| # | column | type | NOT NULL | default | PK | FK | CHECK | UQ | 分区相关 | retention 相关 | 安全分级 | 来源 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-01 | `id` | `uuid`（**UUIDv7**） | ✔ | — | ✔ | — | — | — | PK 组成 | — | internal | `D-AUTH-22` |
| A-02 | `occurred_at` | `timestamptz(3)` | ✔ | — | ✔ | — | — | — | **分区键** | 分区 drop 依据 | internal | `D-P10-09` |
| A-03 | `tenant_id` | `uuid` | ✗ NULL | — | — | 无 FK | — | — | 隔离谓词 | — | tenant-scoped | `CONSTRAINT_MATRIX §7` |
| A-04 | `space_id` | `uuid` | ✗ NULL | — | — | 无 FK | — | — | 隔离谓词 | — | space-scoped | 同上 |
| A-05 | `actor_type` | `text` | ✔ | — | — | — | — | — | — | — | internal | `CONSTRAINT_MATRIX §7` |
| A-06 | `actor_id` | `uuid` | ✗ NULL | — | — | — | — | — | — | — | internal | 同上 |
| A-07 | `actor_ip` | `inet` | ✗ NULL | — | — | — | — | — | — | — | **PII ⇒ redaction/最小化** | `CORE §1.6` |
| A-08 | `actor_user_agent` | `text` | ✗ NULL | — | — | — | — | — | — | — | **PII** | `CORE §1.6` |
| A-09 | `action` | `text` | ✔ | — | — | — | — | — | — | — | internal | `CONSTRAINT_MATRIX §7` |
| A-10 | `resource_type` | `text` | ✗ NULL | — | — | — | — | — | — | — | internal | 同上 |
| A-11 | `resource_id` | `uuid` | ✗ NULL | — | — | — | — | — | — | — | internal | 同上 |
| A-12 | `classification` | `text` | **可空** | — | — | — | ✔ 四级（可空时按策略） | — | — | — | **分级** | `D-P10-14` |
| A-13 | `result` | `text` | ✔ | — | — | — | ✔ `IN ('success','denied','error')` | — | — | — | internal | `CONSTRAINT_MATRIX §7` |
| A-14 | `risk_level` | `text` | ✔ | — | — | — | ✔ `IN ('LOW','MEDIUM','HIGH','CRITICAL')` | — | — | 告警扫描 | security | 同上 |
| A-15 | `reason` | `text` | ✗ NULL | — | — | — | — | — | — | — | internal | 同上 |
| A-16 | `correlation_id` | `uuid` | ✗ NULL | — | — | — | — | — | — | — | **跨面关联（Runtime 关联键载体）** | `D-P10-16` |
| A-17 | `request_id` | `uuid` | ✗ NULL | — | — | — | — | — | — | — | 链路追踪 | `CONSTRAINT_MATRIX §7` |
| A-18 | `metadata` | `jsonb` | ✔ | — | — | — | — | — | — | — | **写入前已脱敏**（`D-P10-08` 应用层单点） | `CORE §1.6` |
| A-19 | `created_at` | `timestamptz(3)` | ✔ | — | — | — | — | — | — | — | internal | `CONSTRAINT_MATRIX §7` |

### 5.3 Authorization Audit 五语义维度（`D-P10-05`）

```text
subject · delegator · decision · policy · approval
   ⇒ 采用 **结构化 metadata**（audit_logs.metadata）表达
   ⇒ **不新增 first-class column**
   ⇒ 不产生 `D-AUTH-15` supersession
约束：metadata 必须**结构化 / 可验证 / 可追踪**；
      不得视为非结构化文本垃圾桶；不得作为**绕过 canonical audit fields** 的手段
```

### 5.4 三类审计分离（**不得合并**）

```text
Authorization Decision Audit   ≠   Agent Run Audit   ≠   Tool Execution Audit
（D-AUTH-15 · D-AGENT-13 · P10 GP-12）
⇒ 不得把三者合成单一 runtime record；run 细节归 `agent_runs`（Runtime，非 P10）
```

---

## 6. Outbox Contract（`STEP1B_EVENT_OUTBOX` 为权威，**单一 canonical 模型**）

### 6.1 身份与引用

| 项 | 实现映射 | 来源 |
|---|---|---|
| outbox identity | `events.id`（= `event_id`，**同时**是幂等键） | `EVENT_OUTBOX §1` · §5 |
| event reference | 无独立引用列（表即事件本身） | `D-P10-04`（不建 `event_types` 注册表） |
| aggregate/subject reference | `subject_type` / `subject_id`（可空） | `CORE §1.6` |
| payload | `payload jsonb NOT NULL` | `EVENT_OUTBOX §1` |
| status | `status text NOT NULL`（`pending\|claimed\|delivered\|dead`） | `CONSTRAINT_MATRIX §7` |
| available_at | **`next_attempt_at timestamptz NULL`**（冻结命名，非 `available_at`） | `EVENT_OUTBOX §1` |
| attempts | `attempts int NOT NULL DEFAULT 0`（`CHECK BETWEEN 0 AND 100`） | 同上 |
| lease / claim fields | `worker_id` · `claimed_at` · `lease_expires_at` | 同上 |
| created_at | `created_at timestamptz NOT NULL DEFAULT now()` | 同上 |
| processed_at | **`delivered_at timestamptz NULL`**（冻结命名，非 `processed_at`） | 同上 |
| error | `last_error text NULL` | 同上 |

> **命名口径**：权威文档使用 `next_attempt_at` / `delivered_at`；指令 §6 中的 `available_at` /
> `processed_at` **映射**到这两个冻结列名，**不新增列**。

### 6.2 状态机（冻结）

```text
pending ──CAS claim──→ claimed ──投递成功──→ delivered
   ▲                      │
   │                      ├── 失败可重试 ──→ pending（attempts++ · 指数退避 `1s * 2^attempts`）
   │                      ├── attempts >= 8 ─→ dead（+ 告警）
   └── lease 过期 ──Reaper──┘
```

### 6.3 操作契约（**application-level CAS，**不是** DB trigger**）

| 操作 | 契约 | 来源 |
|---|---|---|
| **claim** | 单行 `UPDATE … SET status='claimed', worker_id=$w, claimed_at=now(), lease_expires_at=now()+interval '60 seconds' WHERE status='pending' AND next_attempt_at <= now()` ⇒ **status 条件即乐观锁** | `EVENT_OUTBOX §2` |
| `FOR UPDATE SKIP LOCKED` | **仅性能优化**（减少锁等待），**非正确性保证** —— CAS 才是正确性来源 | `EVENT_OUTBOX §2` |
| **success** | `SET status='delivered', delivered_at=now(), lease_expires_at=NULL WHERE id=$id AND status='claimed' AND worker_id=$w` | 同上 |
| **retry** | `SET status='pending', attempts=attempts+1, next_attempt_at=now()+backoff, last_error=$err, lease_expires_at=NULL`（同 `worker_id` 条件） | 同上 |
| **dead** | `SET status='dead', lease_expires_at=NULL, last_error='max_attempts_exceeded' WHERE … AND attempts >= 8` | 同上 |
| **reclaim / reaper** | 周期 job（建议 30s）：`SET status='pending', next_attempt_at=now(), last_error=COALESCE(last_error,'')||'lease_expired:', lease_expires_at=NULL WHERE status='claimed' AND lease_expires_at < now()` | `EVENT_OUTBOX §3` |
| **failure → 死信** | `dead`：`attempts >= 8` ⇒ 写 `audit_logs(result='error', action='event.delivery.failed', risk_level='HIGH')` + 告警；人工复投 = `attempts=0, status='pending', next_attempt_at=now()` | `EVENT_OUTBOX §6` |
| 崩溃场景 A/B/C | A: lease 过期→Reaper 接管 · B: 已发未标 delivered ⇒ **必然重发**（消费方按 `event_id` 去重）· C: 两 worker 同 claim ⇒ 仅 1 成功 | `EVENT_OUTBOX §4` |

**硬约束**

```text
claim = application-level CAS      （NOT DB trigger；`TRIGGER_INVENTORY §M`：events 无 trigger）
绝不承诺 exactly-once              （D-P10-18 · EVENT_OUTBOX 首行）
事件写入必须与业务写入**同事务**    （EVENT_OUTBOX §7）；禁止把投递放进业务事务
worker 实施 = **OUT OF SCOPE**      （→ Runtime，D-P10-18）
历史材料中的 outbox 模型：`STEP1B_EVENT_OUTBOX.md` = **唯一 canonical 来源**，不与其他描述合并
```

---

## 7. UUIDv7 Implementation Requirement（`D-P10-02` · `D-AUTH-22`）

```text
DomainEvent.id = UUIDv7（canonical）
```

**已登记的 implementation defect**

```text
core/event/interfaces.py
  DomainEvent.id 生成 = uuid.uuid4()      ← 遗留，非最终 P10 Event identity contract
  附带：tenant_id 为「非空」（冻结 schema 允许 NULL）
```

**实施期义务**：future implementation **MUST** replace `uuid4()` with **canonical UUIDv7 generation**
（应用层 `uap_uuid_v7()` 语义一致）。

**本轮**：

```text
DO NOT MODIFY core/event/interfaces.py      （本轮零实施）
```

---

## 8. Audit Immutability Contract（`tg_audit_immutable` · **P10-owned**）

### 8.1 职责（冻结）

```text
BEFORE UPDATE ON audit_logs  →  RAISE
BEFORE DELETE ON audit_logs  →  RAISE
⇒ audit_logs = append-only（仅 INSERT, SELECT）
```

### 8.2 必须核查项（指令 §8）

| 项 | 设计结论 | 依据 |
|---|---|---|
| **function ownership** | **P10 创建**（属 P10-owned）—— 不得留给 P11 | `D-P10-11` |
| **trigger ownership** | **P10 创建**；P11 **不得** create / replace / modify | `D-P10-11` · `D-P11-01`（`L` = P10-owned ⇒ OUT OF P11） |
| **failure semantics** | `RAISE` ⇒ 语句失败 ⇒ 事务回滚；**禁** silent ignore / warn-only / best-effort | `D-P11-04` 同构原则 |
| **upgrade ordering** | 表 → **function** → **trigger**（function 先于 trigger） | `0011` 既有先例 |
| **downgrade ordering** | **先 `DROP TRIGGER` 再 `DROP FUNCTION`**；不得留下悬空函数/触发器 | `0011` 既有先例 |
| **recursion** | 无（`audit_logs` 上仅此一个 trigger；trigger 内不做 DML） | `D-P10-08`（不得引入**该 trigger 以外**的 trigger） |
| **privilege model** | 见 §9；**不得**依赖 `GRANT` 才具不可变性 | `D-P10-11`（消除可变窗口） |
| **`search_path`** | 不得依赖调用方 `search_path` ⇒ 函数体内**限定对象名**；既有限仓先例 `SECURITY DEFINER = 0` | `P11_PREP`（全仓 0 例） |

**不得依赖 P11**：`audit_logs` 的**基础**不可变性必须在 **P10** 内成立。

---

## 9. Security Contract（指令 §9）

| 主题 | 设计 | 依据 |
|---|---|---|
| `SECURITY INVOKER` / `DEFINER` | **`SECURITY INVOKER` = canonical**；**禁止**引入 `SECURITY DEFINER`（既有限仓先例 = 0 例） | `P11_PREP` 实测 · `D-P11-08` 同构 |
| `search_path` | 函数内**限定对象名**；不依赖调用方 `search_path`；不得以 `SET search_path` 作为隐蔽配置 | 同上 |
| privilege ownership | **应用运行时不持有 DDL 权限**；三角色模型 `uap_app`(DML) · `uap_migrator`(DDL，仅迁移窗口) · `uap_readonly` | `CORE §13` · `D-P10-10` |
| `audit_logs` 权限 | **仅 `INSERT, SELECT`** | `CORE §13` |
| tenant isolation | tenant 谓词 + 应用层强制断言 + 越权写入审计（**不引入 RLS**） | `D-P10-15` |
| space isolation | space 谓词（同上） | 同上 |
| payload sensitivity | 写入前 **redaction 纪律**；`payload` 不得含 secret | `D-P10-08` |
| secret redaction | **应用层强制单点**（沿用 `infrastructure/logging/redaction.py`）+ **测试守卫**（AK/SK / token / PII 模式扫描）；**DB 侧不加转换逻辑** | `D-P10-08` |
| audit tamper resistance | `tg_audit_immutable`（§8）+ 仅 `INSERT, SELECT` + 三角色最小权限 | `CORE §13` |
| 分级 | 分级**只升不降**；降级必须写 `audit_logs` 并注明 `reason`；**CRITICAL 只存摘要**（契约纪律，不新增列） | `D-P10-14` · `CORE §7` |

**明令禁止（不得因实现便利）**

```text
introduce SECURITY DEFINER
introduce unrestricted role
introduce arbitrary GRANT
⇒ DB `GRANT` = 0 的历史事实保留为 **OPEN-P10-1（DEFER）**，本轮**不得**偷偷形成权限体系（D-P10-13）
```

---

## 10. Partition / Retention Contract

| 项 | 冻结值 | 来源 |
|---|---|---|
| partitioned table | `events` · `audit_logs`（**均为分区父表**） | `SD:171` |
| partition key | **`occurred_at`**（`RANGE`） | `D-P10-09` |
| partition 粒度 | **UTC 月分区**（calendar month） | `D-P10-09` · `D-P12` 契约 IDX-13..19 同源先例 |
| 初始子分区 | **仅当月**（建父表 + 当月子分区） | `SD:171` · `D-P10-09` |
| partition 命名 | 沿用 B1-6 先例形态 `ai_request_logs_<YYYYMM>` ⇒ `events_<YYYYMM>` / `audit_logs_<YYYYMM>` | `0010 DC-1` |
| partition 创建责任 | **手工运维**（未来月份创建 + 到期 `DROP`）；P10 交付 **runbook**；**不引入** `pg_partman` 等组件 | `D-P10-10` |
| `DEFAULT` 分区 | **不建立** | `D-P10-09` |
| retention — `events` | **投递后 30 天**；`dead` 行 **90 天**供人工复盘 | `CORE §11` · `EVENT_OUTBOX §6` |
| retention — `audit_logs` | **365 天（可配置）**；**不做行级删除** | `CORE §11` |
| purge semantics | **整分区 drop**（避免大表 `DELETE` 的锁与膨胀） | `CORE §13` |
| archive semantics | 审计为**合规留存**（immutable + 分区 drop），无归档改写 | `CORE §11` |
| PK 语义 | `(id, occurred_at)` —— 分区键**进 PK**；两表 **UQ = 无** ⇒ 不触发「分区表唯一索引必须含分区键」 | `CONSTRAINT_MATRIX §7` |

**不得改动（冻结）**：partition strategy · retention semantics · primary key semantics ·
manual-vs-automated maintenance ownership。

---

## 11. Migration Design（**DESIGN ONLY** · `0013` 本轮 MUST NOT 创建）

### 11.1 revision 契约

```text
filename / revision id : 0013_p10_event_audit      （23 字符 ≤ 32 上限 ✅）
down_revision          : 0012_authz_enforcement
single-head expectation: upgrade 后 alembic heads = 0013_p10_event_audit（单头）
                         0014+ = 0
```

### 11.2 upgrade 顺序（设计）

```text
[1] 分区父表 `events`（含 outbox 状态列**一次建齐**，D-P10-01）
[2] 分区父表 `audit_logs`
[3] 当月子分区（events_<YYYYMM> · audit_logs_<YYYYMM>）        ← 父表之后
[4] 约束核验（PK / CHECK / NN；**UQ = 0**；**FK = 0**）
[5] 函数：tg_audit_immutable 所用 function（**先函数**）
[6] 触发器：`tg_audit_immutable`（**后触发器**）
[7] （**不**建索引 —— 7 条 `ix_events_*`/`ix_audit_*` 归 **P12**，D-P12-08）
```

### 11.3 downgrade 顺序（设计）

```text
逆序：[1] DROP TRIGGER tg_audit_immutable
      [2] DROP FUNCTION（immutability function）
      [3] DROP 子分区（先子后父）
      [4] DROP TABLE audit_logs / events（父表）
⇒ 零残留（`pg_class` / `pg_proc` / `pg_trigger` 无孤儿）
⇒ **禁止** downgrade 删除审计/不可变数据（分区按保留期 drop，不随版本回滚）—— `P10 GP-14`
```

### 11.4 依赖顺序核验（指令 §11）

```text
function-before-trigger dependency  = 满足（§11.2 [5] → [6]）
partition creation order            = 父表 → 子分区（§11.2 [1][2] → [3]）
index dependency                    = **P10 内 0 索引**；P12 指数须在 P10 之后（`D-P12-08`）
与 P12 的关系                        = **P10 tables first · P12 indexes later** ✅
```

### 11.5 不写入的内容（本轮）

```text
不创建 migrations_alembic/versions/0013_p10_event_audit.py
不修改 alembic.ini / env.py / 任何既有 migration
不执行 alembic upgrade / downgrade
**不提前把 P12 索引写进 P10 migration**
```

---

## 12. `DISC-1` / `DISC-2` — 文章不一致登记（**只登记，不静默重设计**）

| ID | 事项 | 事实 | 处置 |
|---|---|---|---|
| `DISC-1` | `ER_MODEL.md` §6 在 `events`/`audit_logs` 上把 `tenant_id`/`space_id` 标注为 **`FK "nullable"`** | `STEP1B_SCHEMA_DEPENDENCY:82-83` 与 `:269`、`CONSTRAINT_MATRIX §7` 均明定 **无强制 FK**（事实日志，避免租户历史阻塞 purge） | **以 SCHEMA/CONSTRAINT 为准**（无 FK）；`ER_MODEL` 图注**不予静默改写**，登记待后续独立澄清 |
| `DISC-2` | `ER_MODEL.md` §6 的 `audit_logs` **缺 `created_at`**（`events` 亦缺 `created_at`） | `CORE §1.6` 与 `CONSTRAINT_MATRIX §7` 的 NN 列表**均含 `created_at`** | 以 **CORE/CONSTRAINT 为准**（`created_at` NOT NULL）；ER 图**不完整**，登记 |

---

## 13. `NUM-1` — revision 编号冲突（**`NUM-1` = APPROVED ⇒ RESOLVED**）

**冲突事实**

```text
P10_PREP_REPORT.md（冻结材料）已把 P10 实施 migration 记为 `0013`
                              （:123「P10 实施（migration `0013`）」· :129「P10 (0013, 待授权)」）
本轮指令 §11                 指定 P10 = `0013_p10_event_audit`
P12_IMPLEMENTATION_CONTRACT.md（上一轮我的交付物）却把 P12 写作 `0013_p12_indexes`  ← **错误的编号**
```

**按 `D-PLAT-09` 冻结顺序（P10 → P11 → P12 → P13）应有的编号**

```text
P10 = 0013_p10_event_audit        ← 与本轮指令一致
P11 = 0014_p11_triggers
P12 = 0015_p12_indexes            ← P12 契约已由 0013 更正为 0015（2026-09-25 Human Decision）
```

**性质**：**我上一轮在 P12 契约中自行引入的编号错误**（P12 契约 §11.1 及矩阵 `MIG-01`/`MIG-03` 受其影响）。
**处置**：

```text
① 本轮（该契约轮）**不修改** P12 契约与矩阵（不在该轮授权面内）；
② 登记为本项，提请 Human 在下一步授权时一并裁定；
③ 更正为 `0015_p12_indexes` 属**纯命名更正**（不改任何 P12 冻结决策语义）；
④ 在更正落地前，任何 P12 实施不得启动（避免 revision 冲突）。
```

**后续注记（2026-09-25 · `NUM-1` = APPROVED ⇒ RESOLVED）**

```text
P10 = 0013_p10_event_audit
P11 = 0014_p11_triggers
P12 = 0015_p12_indexes

P12 侧更正已落地（P12_IMPLEMENTATION_CONTRACT §11.1 · P12_IMPLEMENTATION_ACCEPTANCE_MATRIX MIG-01/03）；
校正以 append-only 登记于 PLATFORM_DECISION_LOG.md 附录 I.9；
本条记的「须 Human 裁定」状态**终结**；§14 `P10-F01…` 的 migration location `0013` 保持不变（仍属 P10）。
```

---

## 14. Implementation Scope Table（`P10-F01` … `P10-F22`）

> `status` **仅允许** `IMPLEMENT` / `DEFER` / `OUT OF SCOPE`。
> **不得把 `DEFER` 自动变为 `IMPLEMENT`。**

| ID | artifact | implementation action | dependency | migration location | test | acceptance evidence | rollback | status |
|---|---|---|---|---|---|---|---|---|
| `P10-F01` | `events` 分区父表 | `CREATE TABLE … PARTITION BY RANGE (occurred_at)` | P09 ✅ / 单头 `0012` ✅ | `0013` | `test_p10_event_audit_schema` | `pg_class.relkind='p'` | `DROP TABLE` | **IMPLEMENT** |
| `P10-F02` | `audit_logs` 分区父表 | 同上 | 同上 | `0013` | 同上 | 同上 | `DROP TABLE` | **IMPLEMENT** |
| `P10-F03` | 当月子分区 | `CREATE TABLE <t>_<YYYYMM> PARTITION OF <t>` | F01/F02 | `0013` | 子分区存在性 | `pg_inherits` | 先 `DROP` 子分区 | **IMPLEMENT** |
| `P10-F04` | `events` 约束 | PK `(id, occurred_at)` + 3 CK（`event_type` 正则 / `status` / `attempts` 区间）+ NN | F01 | `0013` | CK/PK 断言 | `pg_constraint` | 随表 `DROP` | **IMPLEMENT** |
| `P10-F05` | `audit_logs` 约束 | PK `(id, occurred_at)` + CK（`result` / `risk_level` / `classification`）+ NN | F02 | `0013` | 同上 | 同上 | 随表 `DROP` | **IMPLEMENT** |
| `P10-F06` | `events` outbox 状态列 | **8 列一次建齐**（`D-P10-01`） | F01 | `0013` | 列集合断言 | `information_schema` | 随表 `DROP` | **IMPLEMENT** |
| `P10-F07` | `audit_logs.metadata` | `jsonb NOT NULL`（结构化承载五语义维度） | F02 · `D-P10-05` | `0013` | metadata 形态断言 | 同上 | 随表 `DROP` | **IMPLEMENT** |
| `P10-F08` | immutability function | `SECURITY INVOKER` · 限定对象名 · `RAISE` | F02 | `0013` | 触发即异常 | `pg_proc` + 行为测试 | `DROP FUNCTION` | **IMPLEMENT** |
| `P10-F09` | `tg_audit_immutable` | `BEFORE UPDATE OR DELETE` → `RAISE` | F08 | `0013` | UPDATE/DELETE 被拒 | `pg_trigger` + 行为测试 | 先 `DROP TRIGGER` | **IMPLEMENT** |
| `P10-F10` | `core/event` 写入契约（UUIDv7） | 以 **UUIDv7** 取代 `uuid4()`；`tenant_id` 可空性对齐 | `D-P10-02`/`03` | 非 migration（core 契约） | 契约测试 | 测试通过 | 代码回退 | **IMPLEMENT** |
| `P10-F11` | outbox 状态机契约 | contract 文档化（claim/lease/retry/reclaim/reaper/success/failure） | F06 | — | 语义测试（应用层） | 契约核对 | — | **IMPLEMENT** |
| `P10-F12` | 运维 runbook | 月分区创建 / 到期 drop / dead 复盘 | `D-P10-10` | — | 文档存在性 | 文档 | — | **IMPLEMENT** |
| `P10-F13` | redaction 单点 + 测试守卫 | 沿用 `infrastructure/logging/redaction.py`；AK/SK/token/PII 扫描守卫 | `D-P10-08` | 非 migration | 守卫测试 | 守卫通过 | 代码回退 | **IMPLEMENT** |
| `P10-F14` | 五类承载面边界守卫 | `tests/architecture/` 守卫（event→`events`·audit→`audit_logs`·其余非 P10） | `D-P10-17` | 非 migration | 守卫测试 | 守卫通过 | 代码回退 | **IMPLEMENT** |
| `P10-F15` | 查询索引 7 条 | `ix_events_*` 2 + `ix_audit_*` 5 | **P12** | **不在 `0013`** | P12 测试 | — | — | **OUT OF SCOPE**（`D-P12-08`） |
| `P10-F16` | 投递 worker | outbox 投递执行体 | Runtime（`P13` 后） | — | — | — | — | **OUT OF SCOPE**（`D-P10-18`） |
| `P10-F17` | `events` ↔ `audit_logs` linkage 列 | 不建 | `D-P10-12` | — | — | — | — | **OUT OF SCOPE** |
| `P10-F18` | `event_types` 注册表 | 不建 | `D-P10-04` | — | — | — | — | **OUT OF SCOPE** |
| `P10-F19` | RLS | 不引入 | `D-P10-15` | — | — | — | — | **OUT OF SCOPE** |
| `P10-F20` | partition 自动化（`pg_partman` 等） | 不引入（手工运维） | `D-P10-10` | — | — | — | — | **OUT OF SCOPE** |
| `P10-F21` | DB 角色 / `GRANT` 体系 | 授权粒度过细、跨阶段 | `OPEN-P10-1` · `D-P10-13` | — | — | — | — | **DEFER** |
| `P10-F22` | G/H/I/J（P11 触发器） | 属 P11 | `D-P11-01` | `0014` | — | — | — | **OUT OF SCOPE** |

**汇总**

```text
IMPLEMENT    = 14（F01–F14）
DEFER        =  1（F21）
OUT OF SCOPE =  7（F15–F20, F22）
合计          = 22
```

---

## 15. Zero Implementation Check（**契约轮**实测 · 历史记录）

```text
migration files added = 0 · migration files changed = 0
DDL = 0 · DML = 0
CREATE TABLE = 0 · CREATE TRIGGER = 0 · CREATE FUNCTION = 0 · CREATE INDEX = 0
code = 0 · tests = 0 · config = 0
commit = 0 · tag = 0 · push = 0
```

见 `P10_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` 与 `p10_contract_gate.log`。

---

## 16. 实施记录（2026-09-25 · IMPLEMENTATION AUTHORIZATION）

```text
revision                 = 0013_p10_event_audit
down_revision            = 0012_authz_enforcement
single head              = 0013_p10_event_audit（0014+ = ABSENT）

tables（新建）            = events · audit_logs（均为 PARTITION BY RANGE (occurred_at)）
child partitions         = events_<YYYYMM> · audit_logs_<YYYYMM>（仅当月）
columns                  = events 22 · audit_logs 19 = 41
PK                       = 2（均为 (id, occurred_at)）
FK = 0 · UQ = 0 · CHECK  = 6（events 3 + audit_logs 3）
index                    = 0（7 条 ix_events_* / ix_audit_* 归 P12，D-P12-08）
trigger                  = 1（tg_audit_immutable，建在 audit_logs）
function（新建）          = 1（enforce_audit_logs_immutable，SECURITY INVOKER）
seed = 0 · GRANT = 0 · RLS = 0 · DEFAULT partition = 0
```

**范围表落实**

```text
IMPLEMENT（F01–F14） = 全部落地
DEFER（F21 GRANT）   = 保持 DEFER（OPEN-P10-1）
OUT OF SCOPE         = F15 索引→P12 · F16 worker→Runtime · F17 linkage 列 ·
                       F18 event_types · F19 RLS · F20 分区自动化 · F22 G/H/I/J→P11
```

**code 侧（非 migration）**

```text
P10-F10  core/event/interfaces.py：DomainEvent.id 由 uuid4() 改为 canonical UUIDv7
         （委托 core.audit.interfaces.new_event_id，与 DB uap_uuid_v7() 同语义）；
         tenant_id 由必填改为可空（对齐冻结 schema 允许 NULL）；docstring 声明 EventBus != Outbox
P10-F14  tests/architecture/test_p10_event_audit_boundary.py：五类承载面边界守卫（新增）
         并在 DEPENDENCY_RULES.md 追加形式化声明（D-P10-17 的「声明」义务）
```

**验收**：见 `P10_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` §19 与仓库外证据
`p10_impl_acceptance.log` · `p10_impl_smoke.log`。

**END OF P10 IMPLEMENTATION CONTRACT（2026-09-25 · DESIGN FROZEN · IMPLEMENTATION AUTHORIZED → IMPLEMENTED）**
