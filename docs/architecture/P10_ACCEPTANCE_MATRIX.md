# P10 — ACCEPTANCE MATRIX（Event / Audit · DECISION FREEZE APPLIED）

> **状态（2026-09-25 更新）**：`OQ-P10-01`…`OQ-P10-18` 已**全部冻结**为 `D-P10-01`…`D-P10-18`
> （见 `PLATFORM_DECISION_LOG.md` 附录 G）；`C-1` RESOLVED · `C-2` CLARIFIED · `C-3` RESOLVED · `C-4` RESOLVED。
> 全部条目处于 **`FROZEN-DESIGN`（决策已冻结 → 待实施）** 或 **`ASSET`（既有冻结资产）** 或
> **`PASSED`（本轮只读实测通过）** 或 **`BLOCKED`（实施未授权）**。
> **数字为脚本实测**（按 ID 前缀分组、逐行主状态计数，**仅取状态列**），非估算。
> **仍不构成实现验收结论** —— 所有 `FROZEN-DESIGN` 行的验收须待实施阶段执行；
> **本轮零实施**（无表 / 无 migration / 无代码 / 无测试 / 无配置变更）。
> **`P10 / P11 IMPLEMENTATION = NOT AUTHORIZED`** · **`Runtime Implementation Gate = CLOSED`**。

## 0. ID 前缀映射

| 前缀 | 类别 | 前缀 | 类别 |
|---|---|---|---|
| `BASE-` | 基线与保护 | `PART-` | 分区模型 |
| `EVT-` | `events` 表 | `RET-` | 保留与删除 |
| `AUD-` | `audit_logs` 表 | `SEC-` | 安全不变式 |
| `REL-` | 语义边界与关联 | `MIG-` | 迁移完整性 |
| `BOUND-` | 五类承载面边界 | `DEP-` | 阶段依赖 |
| `INT-` | Runtime 集成（设计） | `CONS-` | 一致性核查 |
| `REG-` | 测试与回归 | `GATE-` | 门禁汇总 |

> **状态词表（2026-09-25 更新）**：`ASSET` = 既有冻结资产（本轮实测确认）· `PASSED` = 本轮只读实测通过 ·
> **`FROZEN-DESIGN`** = **决策已冻结**（`D-P10-01..18`），实施待授权 · `BLOCKED` = 被 **P10 / P11 / Runtime Gate** 明确阻塞。
>
> > **词表升级（语义映射 1:1）**：原 `PENDING`（待 Human Decision）→ **`FROZEN-DESIGN`**（决策已冻结、待实施）；
> > 原 `BLOCKED`（DECISION FREEZE 未通过）中 `GATE-01` → **`PASSED`**，`GATE-02` 保留 `BLOCKED`（实施未授权）。

---

## 1. BASE — 基线与保护

| ID | 要求 | 证据 | 状态 |
|---|---|---|---|
| BASE-01 | HEAD = `034ee97…` · tag `UAP-V0.1.8-AUTHORIZATION` 在位 · tags = 8 · remote = none | git | **PASSED** |
| BASE-02 | `alembic heads` = 单头 `0012_authz_enforcement` · `0013+ = 0` · history 12 线性 | 命令 | **PASSED** |
| BASE-03 | `0010` / `0011` / `0012` sha256 = 保护值（逐字节未变） | sha256sum | **PASSED** |
| BASE-04 | 本轮 0 migration / 0 DDL / 0 DML / 0 seed / 0 `alembic upgrade\|downgrade` | git + 命令 | **PASSED** |
| BASE-05 | 本轮 0 code / test / config 变更 | git diff | **PASSED** |
| BASE-06 | 本轮 0 既有文档修改 / 0 commit / 0 tag / 0 push | git status/log | **PASSED** |

## 2. EVT — `events` 表（冻结继承面）

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| EVT-01 | PK = `(id, occurred_at)` | `CORE` §1.6 · `CONSTRAINT` §7 | **ASSET** |
| EVT-02 | `PARTITION BY RANGE (occurred_at)` + 当月子分区 | `DEPENDENCY` §9 | **ASSET** |
| EVT-03 | 字段集 = 21 列（事实 + outbox 状态） | `CORE` §1.6 · `EVENT_OUTBOX` §1 | **ASSET** |
| EVT-04 | CK `event_type ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$'` | `CONSTRAINT` §7 | **ASSET** |
| EVT-05 | CK `status IN ('pending','claimed','delivered','dead')` | `CONSTRAINT` §7 | **ASSET** |
| EVT-06 | CK `attempts >= 0 AND attempts <= 100` | `CONSTRAINT` §7 | **ASSET** |
| EVT-07 | NN = `id, event_type, schema_version, payload, occurred_at, status, attempts, created_at` | `CONSTRAINT` §7 | **ASSET** |
| EVT-08 | **无 DB trigger**（claim 走应用层 CAS） | `TRIGGER_INVENTORY` §M | **ASSET** |
| EVT-09 | `tenant_id` / `space_id` **无强制 FK** | `DEPENDENCY` §1.7 · `:269` | **ASSET** |
| EVT-10 | **at-least-once**；**绝不承诺 exactly-once**；消费方按 `event_id` 幂等 | `CORE` §8.2 · `EVENT_OUTBOX` 首行 | **ASSET** |
| EVT-11 | outbox 状态列**是否全部**属 P10 DDL | `OQ-P10-01` | `FROZEN-DESIGN` |
| EVT-12 | events **生产者写入契约**边界 | `OQ-P10-03` | `FROZEN-DESIGN` |
| EVT-13 | `event_type` 命名空间 / `schema_version` 兼容策略 | `OQ-P10-04` | `FROZEN-DESIGN` |
| EVT-14 | `core/event` 契约对齐（UUIDv7 · `EventBus` vs outbox） | `D-P10-02` · `C-2`/`C-3` | `FROZEN-DESIGN` |
| EVT-15 | **Domain Event ID = UUIDv7 canonical**；`uuid.uuid4()` = **实现遗留**（实施期修正）；**本轮不得修改 `core/event/interfaces.py`** | `D-P10-02` | `FROZEN-DESIGN` |

## 3. AUD — `audit_logs` 表（冻结继承面）

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| AUD-01 | PK = `(id, occurred_at)` | `CORE` §1.6 | **ASSET** |
| AUD-02 | 月分区 | `CORE` §1.6 · §13 | **ASSET** |
| AUD-03 | 字段集 = 18 列（含 `metadata` 写入前脱敏） | `CORE` §1.6 · `ER_MODEL` §6 | **ASSET** |
| AUD-04 | CK `result IN ('success','denied','error')` | `CONSTRAINT` §7 | **ASSET** |
| AUD-05 | CK `risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` | `CONSTRAINT` §7 | **ASSET** |
| AUD-06 | CK `classification IN (四级)`（可空按策略） | `CONSTRAINT` §7 | **ASSET** |
| AUD-07 | NN = `id, occurred_at, actor_type, action, result, risk_level, metadata, created_at` | `CONSTRAINT` §7 | **ASSET** |
| AUD-08 | **无 `updated_at` / 无 `deleted_at`** | `CORE` §1.6 | **ASSET** |
| AUD-09 | 不可变：仅 `INSERT, SELECT` + `tg_audit_immutable`（BEFORE UPDATE/DELETE ⇒ RAISE） | `CORE` §13 · `TRIGGER_INVENTORY` §L | **ASSET** |
| AUD-10 | `D-AUTH-15` 七类字段：**落列 vs 落 `metadata`** | `OQ-P10-05` · **`C-1`** | `FROZEN-DESIGN` |
| AUD-11 | `core/audit.AuditEvent` ↔ 列/`metadata` 映射显式化 | `OQ-P10-06` | `FROZEN-DESIGN` |
| AUD-12 | audit 写入**同步 / 异步**策略（`STEP1A` R6） | `OQ-P10-07` | `FROZEN-DESIGN` |
| AUD-13 | `metadata` 脱敏**执行点**与 DB 侧保护 | `OQ-P10-08` | `FROZEN-DESIGN` |
| AUD-14 | `classification` 可空性与"CRITICAL 只存摘要"落地 | `D-P10-14` | `FROZEN-DESIGN` |
| AUD-15 | `metadata` 必须**结构化 / 可验证 / 可追踪**；**不得**作非结构化垃圾桶；**不得**绕过 canonical audit fields | `D-P10-05` | `FROZEN-DESIGN` |
| AUD-16 | `OQ-P10-05` **不产生** `D-AUTH-15` supersession（`D-AUTH-15` 保持 `FROZEN` 原状） | `D-P10-05` | `FROZEN-DESIGN` |

## 4. REL — 语义边界与关联

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| REL-01 | `events`（事实/可重放/可清理）≠ `audit_logs`（责任/不可重放/不可变） | `CORE` §8.1 | **ASSET** |
| REL-02 | ER 弱关系 `events \|\|--o\| audit_logs : "may be mirrored by"`（**无 FK**） | `ER_MODEL` §6 | **ASSET** |
| REL-03 | 三类审计分离（Agent Run ≠ Authorization Decision ≠ Tool Execution） | `D-AUTH-15` · `D-AGENT-13` | **ASSET** |
| REL-04 | 显式 linkage 列（`event_id` / `audit_id`） | `OQ-P10-12` | `FROZEN-DESIGN` |
| REL-05 | Runtime 关联键（`run_id` / `trace_id` 等）载体 | `D-P10-16` | `FROZEN-DESIGN` |
| REL-06 | **`EventBus != Outbox`** —— 二者**不得**被描述成同一种 delivery mechanism（全权威文档一致） | `D-P10-02` · `C-3` | `FROZEN-DESIGN` |
| REL-07 | `Outbox` = durable / reliable authoritative delivery；`EventBus` = optional in-process auxiliary（**MUST NOT** 替代 outbox 持久化 / 视为持久边界 / 成为跨进程投递机制） | `D-P10-02` · `C-3` | `FROZEN-DESIGN` |

## 5. BOUND — 五类承载面边界

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| BOUND-01 | **Event** → `events` 表（P10） | `CORE` §8.1 | **ASSET** |
| BOUND-02 | **Audit** → `audit_logs` 表（P10） | `CORE` §8.1 | **ASSET** |
| BOUND-03 | **Operational log** → `infrastructure/logging`（**非 P10**，不入 DB 表） | `infrastructure/logging/**` | **ASSET** |
| BOUND-04 | **Trace** → 日志信封字段（**非 P10**；P10 仅承接 `correlation_id`/`request_id` 列） | `structured.py` 信封 | **ASSET** |
| BOUND-05 | **Metric** → 未定义（**非 P10**） | `infrastructure/monitoring` | **ASSET** |
| BOUND-06 | 边界**形式化 + 守卫**（可强制，非仅文档） | `OQ-P10-17` | `FROZEN-DESIGN` |

## 6. PART — 分区模型

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| PART-01 | 月分区 `RANGE (occurred_at)`（两表一致） | `DEPENDENCY` §9 · `CORE` §1.6 | **ASSET** |
| PART-02 | 子分区**继承 PK** `(id, occurred_at)` | `DEPENDENCY` §9 | **ASSET** |
| PART-03 | 索引建在**父表**（PG 自动下推子分区） | `DEPENDENCY` §9 · `INDEX_STRATEGY` | **ASSET** |
| PART-04 | 初始子分区范围 / 是否建 `DEFAULT` 分区 | `OQ-P10-09` | `FROZEN-DESIGN` |

## 7. RET — 保留与删除

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| RET-01 | `events` = **投递后 30 天** hard delete（分区） | `CORE` §11 · §1.6 | **ASSET** |
| RET-02 | `events` 的 **`dead` 行保留 90 天**（人工复盘） | `CORE` §1.6 · `EVENT_OUTBOX` §6 | **ASSET** |
| RET-03 | `audit_logs` = **365 天（可配置）** · 整分区 drop | `CORE` §11 · `CONSTRAINT` §7 | **ASSET** |
| RET-04 | `audit_logs` **不做行级删除**（仅整分区 drop） | `CORE` §11 | **ASSET** |
| RET-05 | **禁止** downgrade 删除审计/不可变数据 | `MIGRATION_CONTRACT` §10 | **ASSET** |
| RET-06 | 分区创建与 retention 的**运维模型**（沿用 `D-3 = D` 手工？） | `OQ-P10-10` | `FROZEN-DESIGN` |

## 8. SEC — 安全不变式

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| SEC-01 | **FAIL CLOSED**：审计写入失败**不得**放行受控操作 | `D-AUTH-12` | **ASSET** |
| SEC-02 | 最小权限三角色（`uap_app` DML / `uap_migrator` DDL / `uap_readonly`） | `CORE` §13 | **ASSET** |
| SEC-03 | `audit_logs` 仅授予 `INSERT, SELECT` | `CORE` §13 | **ASSET** |
| SEC-04 | 租户隔离：复合索引 + 应用层强制断言 + 越权写入审计 | `CORE` §2.8 · §13 | **ASSET** |
| SEC-05 | 脱敏统一走 `redaction`（单点权威）；CRITICAL 只存摘要 | `CORE` §13 | **ASSET** |
| SEC-06 | 任何表不得存 API Key 明文（CI 扫描 + 测试守卫） | `CORE` §13 | **ASSET** |
| SEC-07 | 三类审计**不得合并**为同一载体 | `D-AUTH-15` · `D-AGENT-13` | **ASSET** |
| SEC-08 | `resource_scope` 不得进入事件/审计载荷的授权语义 | `D-AUTH-23` | **ASSET** |
| SEC-09 | 是否引入 **RLS** | `OQ-P10-15` | `FROZEN-DESIGN` |
| SEC-10 | DB 角色与 `GRANT` 归属 | `OQ-P10-13` | `FROZEN-DESIGN` |

## 9. MIG — 迁移完整性

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| MIG-01 | 本轮 migration = **0**（versions/ = 12 文件） | 命令 | **PASSED** |
| MIG-02 | 单头 `0012_authz_enforcement` · `0013+ = 0` | 命令 | **PASSED** |
| MIG-03 | `0010`/`0011`/`0012` sha256 逐字节未变 | 命令 | **PASSED** |
| MIG-04 | downgrade：**先 DROP 子分区再 DROP 父表** | `DEPENDENCY` §9 | **ASSET** |
| MIG-05 | **禁止** schema 与 seed 同 revision；data migration 独立 | `MIGRATION_CONTRACT` §9/§14 | **ASSET** |
| MIG-06 | P10 **无 seed**（`P00–P10` 无 seed；`P13` 才有） | `DEPENDENCY` §193 | **ASSET** |

## 10. DEP — 阶段依赖

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| DEP-01 | `D-PLAT-09` 路线 A（`P10→P11→P12→P13→Runtime`）**未 supersede** | `D-PLAT-09` | **ASSET** |
| DEP-02 | P10 **先于 P11**（triggers 引用已存在表；`tg_audit_immutable` 依赖 `audit_logs`） | `TRIGGER_INVENTORY` §L | **ASSET** |
| DEP-03 | P10 **先于 P12**（`ix_events_*` / `ix_audit_*` 建于 P10 表） | `INDEX_STRATEGY` | **ASSET** |
| DEP-04 | P10 **不依赖 P13**；P13 seed 依赖 P10 表已存在 | `DEPENDENCY` §193 | **ASSET** |
| DEP-05 | 四类依赖严格分离（design / implementation / schema / runtime） | 本 PREP §4 | **ASSET** |
| DEP-06 | **`tg_audit_immutable`（L）落点分界**（P10 内联 vs P11 集中） | `OQ-P10-11` · **`C-4`** | `FROZEN-DESIGN` |
| DEP-07 | outbox **投递 worker** 的阶段归属 | `D-P10-18` | `FROZEN-DESIGN` |
| DEP-08 | **`tg_audit_immutable` = P10-owned**；P10 **不得依赖 P11** 才具基础不可变性；**消除** `audit exists but mutable` 窗口 | `D-P10-11` · `C-4` | `FROZEN-DESIGN` |
| DEP-09 | P10/P11 冻结边界：`P10 owns audit-local immutability` · `P11 owns remaining trigger / cross-table constraints` | `D-P10-11` · `C-4` | `FROZEN-DESIGN` |

## 11. INT — Runtime 集成（**仅设计**）

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| INT-01 | P10 **无** Runtime 前置依赖（**无反向依赖**） | 实测 | **ASSET** |
| INT-02 | `Agent Runtime → P10`：事件/审计面（`runtime dependency`） | `D-AGENT-15` | **ASSET** |
| INT-03 | `Authorization → P10`：授权审计 persistence（`persistence dependency`） | `D-AUTH-15` | **ASSET** |
| INT-04 | `D-AUTH-22`：Audit / Event ID persistence 属 P10 | `D-AUTH-22` | **ASSET** |

## 12. CONS — 一致性核查

| ID | 要求 | 证据 | 状态 |
|---|---|---|---|
| CONS-01 | `events` **未被实现**（`CREATE TABLE … events` 命中 0） | grep | **PASSED** |
| CONS-02 | `audit_logs` **未被实现**（命中 0） | grep | **PASSED** |
| CONS-03 | **P10 未被实现**（无 `0013+`；无 P10 gate 报告） | 命令 | **PASSED** |
| CONS-04 | **audit persistence 未实现**（仅内存窗口，自述 *not a durable audit trail*） | 源码 | **PASSED** |
| CONS-05 | 陈旧"P10 已实现"声明 = **0 命中** | grep | **PASSED** |
| CONS-06 | 陈旧"events/audit_logs 已建表"声明 = **0 命中** | grep | **PASSED** |
| CONS-07 | 陈旧文档**未被修改**（保持一致，仅登记证据） | git status | **PASSED** |
| CONS-08 | `C-1` / `C-2` / `C-3` / `C-4` **已处置**（RESOLVED · CLARIFIED · RESOLVED · RESOLVED） | `D-P10-05` · `D-P10-02` · `D-P10-11` · 附录 G.2 | **PASSED** |

## 13. REG — 测试与回归

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| REG-01 | 全量回归基线 = **542 passed / 0 failed / 6 skipped**（2026-09-24 实测）——**本轮未复跑**（只读 PREP 轮；PostgreSQL 未运行） | 历史基线 | **ASSET** |
| REG-02 | P10 落地连带：**8** 个集成测试文件的 `FORBIDDEN_TABLES` 含 `events`/`audit_logs` ⇒ 须同步 | 实测 | `FROZEN-DESIGN` |
| REG-03 | P10 落地连带：**15** 个测试文件断言 head `0012` ⇒ 须同步至 `0013` | 实测 | `FROZEN-DESIGN` |
| REG-04 | 架构守卫：现有 `tests/architecture/` **2** 文件、**无** event/audit 守卫 ⇒ 实施期须新增 | 实测 · `OQ-P10-17` | `FROZEN-DESIGN` |

## 14. GATE — 门禁汇总

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| GATE-01 | `P10 DECISION FREEZE = PASSED`（18/18 OQ `FROZEN` ⇒ `D-P10-01..18`） | `PLATFORM_DECISION_LOG.md` 附录 G | **PASSED** |
| GATE-02 | `P10 IMPLEMENTATION = NOT AUTHORIZED` | 本轮指令 §E/§F | **BLOCKED** |
| GATE-03 | `commit` / `tag` / `push` = 未执行 | 命令 | **PASSED** |
| GATE-04 | `P11 IMPLEMENTATION = NOT AUTHORIZED` | 本轮 `D-P10-11` 边界 | **BLOCKED** |
| GATE-05 | `Runtime Implementation Gate = CLOSED`（`D-AGENT-16`） | `D-AGENT-16` | **BLOCKED** |

## 15. OQ ↔ Matrix 映射（18 项）

| OQ | 决策域 | 主要验收行 |
|---|---|---|
| `OQ-P10-01` | Event | `EVT-11` |
| `OQ-P10-02` | Event / 契约 | `EVT-14` · `CONS-08` |
| `OQ-P10-03` | Event | `EVT-12` |
| `OQ-P10-04` | Event | `EVT-13` |
| `OQ-P10-05` | Audit（**`C-1`**） | `AUD-10` |
| `OQ-P10-06` | Audit | `AUD-11` |
| `OQ-P10-07` | Audit | `AUD-12` |
| `OQ-P10-08` | Audit | `AUD-13` |
| `OQ-P10-09` | Storage / 分区 | `PART-04` |
| `OQ-P10-10` | Storage / OPS | `RET-06` |
| `OQ-P10-11` | Storage（**`C-4`**） | `DEP-06` |
| `OQ-P10-12` | Storage / 关联 | `REL-04` |
| `OQ-P10-13` | Storage / 权限 | `SEC-10` |
| `OQ-P10-14` | Security | `AUD-14` |
| `OQ-P10-15` | Security | `SEC-09` |
| `OQ-P10-16` | Runtime 集成 | `REL-05` |
| `OQ-P10-17` | 边界 | `BOUND-06` · `REG-04` |
| `OQ-P10-18` | 边界 / Worker | `DEP-07` |

> **追溯完备性**：`OQ-P10` 条目 **18** · 已映射 **18** · 覆盖矩阵前缀 **14 / 14**。

## 16. 汇总

| 分类 | 行数 | `ASSET` | `PASSED` | `FROZEN-DESIGN` | `BLOCKED` |
|---|---|---|---|---|---|
| BASE | 6 | 0 | 6 | 0 | 0 |
| EVT | 15 | 10 | 0 | 5 | 0 |
| AUD | 16 | 9 | 0 | 7 | 0 |
| REL | 7 | 3 | 0 | 4 | 0 |
| BOUND | 6 | 5 | 0 | 1 | 0 |
| PART | 4 | 3 | 0 | 1 | 0 |
| RET | 6 | 5 | 0 | 1 | 0 |
| SEC | 10 | 8 | 0 | 2 | 0 |
| MIG | 6 | 3 | 3 | 0 | 0 |
| DEP | 9 | 5 | 0 | 4 | 0 |
| INT | 4 | 4 | 0 | 0 | 0 |
| CONS | 8 | 0 | 8 | 0 | 0 |
| REG | 4 | 1 | 0 | 3 | 0 |
| GATE | 5 | 0 | 2 | 0 | 3 |
| **合计** | **106** | **56** | **19** | **28** | **3** |

> **计数口径**：按 **ID 前缀**分组、**逐行主状态**计数（**仅取状态列 = 行末单元格**；每行恰一个主状态 ⇒ 列和 = 行数 = **106**）。
> **一致性断言（脚本已验证）**：`ASSET + PASSED + FROZEN-DESIGN + BLOCKED == 行数合计`。
> `ASSET` = 既有冻结资产（继承面）· `PASSED` = 本轮只读实测通过。
> `FROZEN-DESIGN` = **决策已冻结**（`D-P10-01..18`），实施待授权（**无一项表示已实施**）。
> `BLOCKED` = 被 P10 / P11 / Runtime Gate 明确阻塞（实施未授权）。

---

**END OF P10 ACCEPTANCE MATRIX（2026-09-25 · READ-ONLY PREP · 全 97 行 = `ASSET` 56 + `PASSED` 17 + `PENDING` 22 + `BLOCKED` 2）**
**END OF P10 ACCEPTANCE MATRIX（P10 Decision Freeze 同步 · 词表升级 + 9 新行（`EVT-15` · `AUD-15/16` · `REL-06/07` · `DEP-08/09` · `GATE-04/05`）⇒ 实测 **106** 行 = `ASSET` 56 + `PASSED` 19 + `FROZEN-DESIGN` 28 + `BLOCKED` 3；`C-1..C-4` 已处置；2026-09-25）**
