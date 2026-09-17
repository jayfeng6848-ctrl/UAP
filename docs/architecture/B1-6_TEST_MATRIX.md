# B1-6 Test Matrix

**Stage**: B1-6（= P08 AI Gateway）· **Status**: **DESIGN SPECIFICATION ONLY**
**输入**: `B1-6_DECISION_LOG.md`（D-B16-01 ～ D-B16-11 FROZEN）· `B1-6_SCHEMA_DESIGN.md` · `B1-6_DEPENDENCY.md`
**边界**: **本阶段禁止创建或修改任何测试文件。** 本文件是规范，不是测试代码。`Implementation tests written = 0`

---

## 0. 状态模型与计数口径

### 0.1 编号空间（独立）

```
AS    Schema                        AF   FK / Delete Rule
AC    Constraint（UQ / CK）          AX   Index
AT    Trigger                       AP   Partition
AE    Seed                          AG   Guard / Architecture
AM    Migration                     AD   Decision-derived
RF    Registration（后续阶段，不计入 canonical）
```

> 独立编号空间：B1-4（canonical **84**）与 B1-5（canonical **39**）**不因 B1-6 改变**。
> 本矩阵**不重复** B1-4 / B1-5 已完成的测试。

### 0.2 Canonical 计数口径（沿用既有先例）

| 项 | 值 |
|---|---|
| **B1-6 Canonical Total（本版）** | **38** = 基础九类 **37** + §10 decision-derived **1** |
| §11 登记项（后续阶段） | **5 行**，**不计入** canonical |
| Implementation tests written（本阶段） | **0** |
| 设计层裁定（D-1 / D-2 / D-3 / D-4 / DC-1）对 canonical 的影响 | **无** —— canonical 保持 **38**（不新增/不删除条目） |

> **口径先例**：沿用 **B1-4 的 O-1 = FROZEN — A**（Canonical Total = 正式表格行数）与
> **B1-5 的 D-B15-07 = FROZEN — A**（canonical 与 registration / conditional 分离）。

### 0.3 必须显式登记的豁免

```
─────────────────────────────────────────────────────────────
  S5 类别（CHECK）对 `ai_request_logs.status` = **EXEMPT / NOT APPLICABLE**
  依据：D-B16-04 = FROZEN — A（零新增取值域 CHECK；不定义 status vocabulary）
  登记位置：§3 AC8（豁免断言）+ §10 AD1（decision-derived）
─────────────────────────────────────────────────────────────
```

---

## 1. Schema Tests（AS1–AS6，6）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AS1** | 5 张表存在：`ai_providers` / `ai_models` / `ai_routes` / `ai_policies` / `ai_request_logs` | `information_schema.tables` 计数 = 5 | 【B1-6】 |
| **AS2** | PK 形状：4 张单列 `id` + `ai_request_logs` 复合 `(id, occurred_at)` | `pg_constraint contype='p'` 逐表列顺序核对 | 【B1-6】 |
| **AS3** | 列集合与类型：逐表 15 / 15 / 10 / 16 / 17 列，类型映射（uuid / text / bool / int / numeric / jsonb / timestamptz） | `information_schema.columns` 逐列比对 | 【B1-6】 |
| **AS4** | 时间列全部为 `timestamp with time zone` 且 `datetime_precision = 3` | 复用平台 guard（`test_platform_timestamp_precision` PG1–PG2 覆盖面扩展至 ai_* 表） | 【B1-6 / 平台 guard】 |
| **AS5** | NULL / NOT NULL 集合与设计一致（`ai_request_logs` NN = id, capability, classification, status, occurred_at） | `is_nullable` 逐列比对 | 【B1-6】 |
| **AS6** | **`ai_providers` 无 `tenant_id` 列**（平台级 ROOT） | 列名集合差集断言 | 【B1-6】 |

---

## 2. FK / Delete Rule Tests（AF1–AF5，5）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AF1** | `ai_models.provider_id → ai_providers.id`，`confdeltype='c'`（**CASCADE**） | `pg_constraint` 逐条 | 【B1-6】 |
| **AF2** | `ai_routes.primary_model_id → ai_models.id`，`confdeltype='r'`（**RESTRICT**） | 同上 | 【B1-6】 |
| **AF3** | `ai_routes.tenant_id → tenants.id` **RESTRICT**；`ai_routes.space_id → spaces.id` **RESTRICT**（2 列） | 同上（D-B16-02 = A） | 【B1-6】 |
| **AF4** | `ai_policies.tenant_id → tenants.id` **RESTRICT**；`ai_policies.space_id → spaces.id` **RESTRICT**（2 列） | 同上（D-B16-02 = A） | 【B1-6】 |
| **AF5** | `ai_request_logs.provider_id → ai_providers.id` **RESTRICT**；`ai_request_logs.model_id → ai_models.id` **RESTRICT**（2 列） | 同上（D-B16-03 = A） | 【B1-6】 |

**AF 附带断言（并入 AF1–AF5 执行）**

```
· FK 总数 = 8；CASCADE = 1；RESTRICT = 7
· ai_providers 的 FK 行数 = 0
· ai_request_logs 的 FK 列表**不含** agent_id / actor_id / tenant_id / space_id
  （D-B16-03 = A 的"不得扩大"边界）
· 删除被引用的 tenants / spaces 行 → 被 RESTRICT 拒绝
· 删除被引用的 ai_providers / ai_models 行 → 被 RESTRICT 拒绝（在引用存在时）
· 删除 ai_providers 行：若其 models 无任何引用 → F1 CASCADE 生效；否则被 F2 / F8 拒绝
```

---

## 3. Constraint Tests（AC1–AC8，8）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AC1** | `uq_ai_providers_key ON (key)` 以 **UNIQUE CONSTRAINT** 形式存在（`contype='u'`） | `pg_constraint` 计数 | 【B1-6】 |
| **AC2** | `uq_ai_models ON (provider_id, model_key)` 以 **UNIQUE CONSTRAINT** 形式存在 | 同上 | 【B1-6】 |
| **AC3** | `uq_ai_routes` 为**表达式唯一索引**（`COALESCE(tenant_id,…), COALESCE(space_id,…), capability, priority`）；**不得**出现为 UNIQUE CONSTRAINT | `pg_indexes` 存在 + `pg_constraint contype='u'` 中**不计入**（D-B16-07 = A 口径） | 【B1-6】 |
| **AC4** | `uq_ai_policies` 为表达式唯一索引（含 `lower(name)`）；**不得**计入 UNIQUE CONSTRAINT | 同上 | 【B1-6】 |
| **AC5** | `ai_providers` CK ×3 生效：`privacy_tier` / `max_classification` / `health_status` 非法值被拒 | 逐 CK 反向插入 | 【B1-6】 |
| **AC6** | `ai_models` CK ×2 生效：`max_classification` 词表；`context_window > 0`（含 0 被拒） | 同上 | 【B1-6】 |
| **AC7** | `ai_routes` CK ×2 生效：`capability` 词表（7 值）；`priority >= 0`（含负值被拒） | 同上 | 【B1-6】 |
| **AC8** | **`ai_request_logs.status` 无 CHECK**（**S5 豁免**）：表上不存在针对 `status` 的 CHECK 约束；非法/任意 `status` 值**可写入**（本阶段不约束） | `pg_constraint contype='c'` 中 `ai_request_logs` 的 CK 计数 = **0**；写入任意 status 不报约束错误 | 【B1-6 · D-B16-04】 |

**AC 附带断言（并入 AC1–AC8 执行）**

```
· UNIQUE CONSTRAINT 总数（ai_* 段） = 2        （D-B16-07 = FROZEN — A）
· UNIQUE INDEX 总数（ai_* 段，表达式） = 2      （D-B16-07 = FROZEN — A）
· CK 总数（必做） = 8（ai_providers 3 · ai_models 2 · ai_routes 2 · ai_policies 1 · ai_request_logs 0）
· `ai_policies` 的 `allow_fallback = false OR fallback_preserves_classification = true` 必验：
    allow_fallback=true + fallback_preserves_classification=false → 拒绝（铁律 5 的 DB 层封死）
· 表达式唯一语义：`uq_ai_routes` 对 (NULL tenant, NULL space) 与 (NULL,'0…') 的 COALESCE 等价性验证
```

---

## 4. Index Tests（AX1–AX2，2）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AX1** | `ix_airl_tenant_occurred ON (tenant_id, occurred_at DESC)` 存在且建在**父表** | `pg_indexes`（父表）+ 分区下推验证 | 【B1-6】 |
| **AX2** | 非 PK 索引集合 = 5（含 2 个由 UNIQUE CONSTRAINT 隐式生成的索引） | `pg_indexes` 逐名比对（口径见 `B1-6_SCHEMA_DESIGN.md` §7 说明） | 【B1-6】 |

> `ix_aimodels_capability`（`INDEX_STRATEGY:139`）—— **D-2 = B FROZEN ⇒ 不建立** ⇒ 不入本计数；
> 其 B0 定义引用 `ai_models` 上不存在的列 ⇒ **T-1 = DEFERRED**（见 `B1-6_DECISION_LOG.md` §9.4 / §10）。

---

## 5. Trigger Tests（AT1–AT2，2）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AT1** | 4 个 trigger 存在且语义正确：`tg_ai_providers_set_updated_at` / `tg_ai_models_set_updated_at` / `tg_ai_routes_set_updated_at` / `tg_ai_policies_set_updated_at`（均 `BEFORE UPDATE`，`EXECUTE FUNCTION set_updated_at()`） | `pg_trigger` + 行为验证（UPDATE 后 `updated_at` 前移） | 【B1-6】 |
| **AT2** | `ai_request_logs` **无 trigger**（无 `updated_at`） | `pg_trigger` 计数 = 0 | 【B1-6】 |

**AT 附带断言（并入 AT1–AT2）**

```
· `set_updated_at()` 函数实例数仍为 1（**未重建**）
· 既有 27 个 trigger 数量不变（27 + 4 = 31）
· `ai_*` 表上不存在任何非 `updated_at` 语义的 trigger（无 G/H/I/J 提前引入）
```

---

## 6. Partition Tests（AP1–AP3，3）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AP1** | `ai_request_logs` 为**分区父表**：`relkind='p'`，`PARTITION BY RANGE (occurred_at)` | `pg_class` + `pg_partitioned_table` | 【B1-6】 |
| **AP2** | **当月子分区**存在，且子分区**继承 PK `(id, occurred_at)`** | `pg_inherits` + 子分区 `pg_constraint` | 【B1-6】 |
| **AP3** | 分区键边界 = **UTC 月边界**；索引建在父表并下推至子分区 | `pg_get_expr(relpartbound)` + 子分区索引可见性 | 【B1-6】 |

**AP 附带断言**

```
· 子分区命名符合 `ai_request_logs_<YYYYMM>` 约定（**DC-1 = A FROZEN**，见 SCHEMA_DESIGN §9 DC-1）
· 向父表 INSERT 可路由至当月子分区
· downgrade 顺序：先 DROP 子分区，再 DROP 父表（并入 AM3）
```

---

## 7. Seed Tests（AE1，1）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AE1** | 5 表 `seed rows = 0`（`ai_providers` / `ai_models` / `ai_routes` / `ai_policies` / `ai_request_logs` 均无内置行） | `count(*) = 0` 逐表 | 【B1-6 · D-B16-11 = A】 |

---

## 8. Guard / Architecture Tests（AG1–AG4，4）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AG1** | **Core → Domain = 0**；core / intelligence 不直接 import 厂商 SDK（`openai` / `anthropic` / `deepseek` / `ollama`） | 既有 `tests/architecture/test_dependency_rules.py`（9 条）继续通过 | 【平台 guard】 |
| **AG2** | core 无行业词汇（restaurant / company / entertainment / family / …） | 同上 | 【平台 guard】 |
| **AG3** | **实施轮连带同步**：5 个既有测试文件的 FORBIDDEN / FUTURE 集合移除 `ai_providers` / `ai_models` / `ai_routes` / `ai_policies` / `ai_request_logs`，**保留** `agents` / `agent_versions` / `agent_permissions` / `tool_executions` / `resource_relations` | 集合差集断言 | 【B1-6 实施轮】 |
| **AG4** | **Repository safety**：`0010` 存在且 `down_revision = 0009_timestamp_precision`；`formal uap` 表数 = 0（未在正式库执行）；`staged` 状态符合 Gate 要求 | 文件存在性 + `information_schema` + `git status` | 【B1-6 实施轮】 |

**AG3 目标文件（精确位置）**

```
tests/integration/test_identity_schema.py:44-47           FORBIDDEN_BUSINESS_TABLES
tests/integration/test_rbac_schema.py:37-40               FUTURE_TABLES
tests/integration/test_resource_acl_schema.py:91-94       （FORBIDDEN 集合）
tests/integration/test_tenant_space_schema.py:53-56       （EXPECTED 集合 / FORBIDDEN）
tests/integration/test_tool_registry_schema.py:71-74      FORBIDDEN_TABLES
  另：test_tool_registry_schema.py:304 TS8 docstring 提及 P08/P09/P10
```

---

## 9. Migration Tests（AM1–AM6，6）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AM1** | `0010` 存在，`down_revision = 0009_timestamp_precision`，`revision` 长度 ≤ 32 且 `filename == revision` | 文件/AST 解析 | 【B1-6 实施轮】 |
| **AM2** | **upgrade 顺序正确**：ai_providers → ai_models → ai_routes → ai_policies → ai_request_logs（父表）→ 子分区 → 4 trigger → 索引 | 空库 `upgrade head` 成功 + 逐步 catalog 核对 | 【B1-6 实施轮】 |
| **AM3** | **downgrade 逆序**：先 DROP 子分区 → 父表 → trigger → 表（严格逆序，无 orphan） | `downgrade 0009` 后 B1-6 对象残留 = 0 | 【B1-6 实施轮】 |
| **AM4** | **roundtrip**：`upgrade → downgrade → upgrade` 三次对象集逐项一致 | 三段式 catalog 快照比对 | 【B1-6 实施轮】 |
| **AM5** | **migration chain**：链长 = **10**（0001…0010）· 唯一 head = `0010` · duplicate = 0 · missing = 0 · `branch_labels`/`depends_on` 全 None | Alembic `ScriptDirectory` 静态解析 + DB `alembic_version` | 【B1-6 实施轮】 |
| **AM6** | 迁移内**无 seed 语句**（`INSERT` 计数 = 0） | 源码扫描 | 【B1-6 实施轮】 |

**AM 连带同步（并入 AM5）**：20 处 `current_revision() == "0009_timestamp_precision"` 断言 → `0010`（8 个文件）；
`test_alembic_smoke.py` 的期望表清单与注释同步。

---

## 10. Decision-Derived Tests（AD1，1）

| ID | 测试内容 | 断言方法 | 归属 |
|---|---|---|---|
| **AD1** | **S5 豁免登记**：Canonical Matrix 中 `ai_request_logs.status` 的 CHECK 检查标记为 **EXEMPT / NOT APPLICABLE**；测试需断言"该表无 status CHECK"而非"该表有 status CHECK" | 断言 `pg_constraint` 中 `ai_request_logs` 的 CK 数 = 0（正向断言豁免事实） | 【B1-6 · **D-B16-04 = FROZEN — A**】 |

> AD1 与 AC8 是同一事实的**两个视角**：AC8 在 §3 约束类内陈述，AD1 在 §10 记录其**决策来源与豁免登记**。
> 二者**同为一处断言的规范**，实施时以 AC8 为实现锚点。

---

## 11. 后续阶段登记（承接，**不在 B1-6 执行**，不计入 canonical）

| ID | 内容 | 归属 |
|---|---|---|
| **RF1** | `agents.default_route_id → ai_routes.id SET NULL` | **P09** |
| **RF2** | `fk_agents_current_version`（`agents.current_version_id`） | **P09**（**不是** P08 · `SCHEMA_DEPENDENCY:136` 的「Phase 08」为陈旧引用） |
| **RF3** | `G / H / I / J` ACL trigger 四件套 | **P09 后** |
| **RF4** | `events` / `audit_logs` 分区表与 outbox 语义 | **P10** |
| **RF5** | 分区维护机制（预建分区 job / pg_partman）与保留期执行 | **D-3 = D FROZEN ⇒ P08 为手工运维**；自动化延后至未来 operational/runtime 阶段（仍不计入 canonical） |

---

## 12. 优先级

| 级别 | 内容 |
|---|---|
| **P0（Gate 阻塞）** | AS1 · AS2 · AS3 · AF1–AF5（含 FK 计数）· AC1–AC8 · AM1–AM5 |
| **P1** | AS4 · AS5 · AS6 · AX1 · AX2 · AT1 · AT2 · AP1–AP3 · AE1 · AG4 · AM6 |
| **P2** | AG1 · AG2 · AG3（平台 guard 与连带同步，实施轮执行） |

---

## 13. 计数汇总

```
Schema Tests          = 6    (AS1–AS6)
FK / Delete Tests     = 5    (AF1–AF5)
Constraint Tests      = 8    (AC1–AC8，含 AC8 = status S5 豁免)
Index Tests           = 2    (AX1–AX2)
Trigger Tests         = 2    (AT1–AT2)
Partition Tests       = 3    (AP1–AP3)
Seed Tests            = 1    (AE1)
Guard / Arch Tests    = 4    (AG1–AG4)
Migration Tests       = 6    (AM1–AM6)
──────────────────────────────────────────
基础九类              = 37
Decision-derived      = 1    (AD1)
──────────────────────────────────────────
Canonical Total       = 38

Registration（后续阶段） = 5 行（RF1–RF5）—— 不计入 canonical

S5 对 ai_request_logs.status = EXEMPT / NOT APPLICABLE   ← D-B16-04 = FROZEN — A
```

## 14. Implementation tests written = 0（本阶段）

```
本阶段（DESIGN）禁止创建或修改任何测试文件。
Implementation tests written = 0
既有测试基线 = 195 个测试函数 / 198 collected / Architecture Guard 9 passed（未改动）
```

---

## 15. Gate

```
B1-6 TEST_MATRIX = DESIGN SPECIFICATION（canonical = 38）
DESIGN DECISION FREEZE = PASS（D-1 = B · D-2 = B · D-3 = D · D-4 = A · DC-1 = A · T-1 = DEFERRED）
canonical 受设计层裁定影响 = 0（仍为 38）
本阶段新增/修改测试 = 0
0010 = ABSENT
IMPLEMENTATION = BLOCKED
```
