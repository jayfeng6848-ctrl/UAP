# B1-6 Migration Plan

**Stage**: B1-6（= P08 AI Gateway）· **Status**: DESIGN —— **本轮不创建任何 migration**
**输入**: `B1-6_DECISION_LOG.md`（D-B16-01 ～ D-B16-11 FROZEN）· `B1-6_SCHEMA_DESIGN.md` · `B1-6_DEPENDENCY.md`
**边界**: 本轮 `0010 = ABSENT`；**DESIGN Gate 结束后仍必须 `0010 = ABSENT`**。

---

## 1. Revision 元信息（规划）

| 项 | 值 |
|---|---|
| **预计 revision id** | **`0010`**（编号由 `0009_timestamp_precision.py:35` 指定：「因 0009 被本 correction 专用，**P08 后续 migration 编号顺延至 0010**」） |
| `down_revision` | **`0009_timestamp_precision`** |
| 文件名 / 命名约定 | `0010_<slug>.py`（**filename == revision**，沿用 0001–0009 的 1:1 约定） |
| **长度硬约束** | revision id **≤ 32 字符**（`alembic_version.version_num` = `varchar(32)`；`env.py` 用默认 `version_table`，未覆盖列类型） |
| 档 | `migrations_alembic/versions/0010_*.py` |
| 性质 | **新业务 phase 的 migration**（P08）—— 与 0009 的 corrective 性质不同 |
| **创建状态** | **本轮 NOT CREATED** |

> **命名前例**：`0009_platform_timestamp_precision`（33 字符）曾被 PostgreSQL 拒绝
> （`value too long for type character varying(32)`）⇒ 改为 `0009_timestamp_precision`（24 字符）。
> 0010 的 slug 必须在实施前核算长度。

---

## 2. 前置条件（Preconditions）

```
✅ 0001–0009 已全部应用且链完整（唯一 head = 0009_timestamp_precision）
✅ 前置表存在：tenants（0004）· spaces（0004）· users（0003）
✅ 前置函数存在：set_updated_at()（0003）· uap_uuid_v7()（0002）
✅ 平台时间精度已校正为 timestamptz(3)（0009）
✅ 无同名对象残留（ai_providers / ai_models / ai_routes / ai_policies / ai_request_logs 均为新表）
✅ 实施前须经独立的 Implementation Gate 显式授权（本轮不授权）
```

**不得修改**：`0001`–`0009` 任何一行 · `alembic/env.py` · `alembic.ini` · `script.py.mako`。

---

## 3. upgrade 顺序（规划，8 步）

```
──────────────────────────────────────────────────────────────────
 STEP 1   create_table  ai_providers
          · 15 列 · PK(id) · uq_ai_providers_key（UNIQUE CONSTRAINT）
          · ck_ai_providers_privacy_tier / _max_classification / _health_status
          · 无 FK（ROOT）· 无 tenant_id

 STEP 2   create_table  ai_models
          · 15 列 · PK(id)
          · FK fk_ai_models_provider → ai_providers.id ON DELETE CASCADE
          · uq_ai_models (provider_id, model_key)（UNIQUE CONSTRAINT）
          · ck_ai_models_max_classification / _context_window

 STEP 3   create_table  ai_routes
          · 10 列 · PK(id)
          · FK fk_ai_routes_primary_model → ai_models.id   RESTRICT
          · FK fk_ai_routes_tenant        → tenants.id     RESTRICT   ← D-B16-02
          · FK fk_ai_routes_space         → spaces.id      RESTRICT   ← D-B16-02
          · ck_ai_routes_capability / _priority

 STEP 4   create_table  ai_policies
          · 16 列 · PK(id)
          · FK fk_ai_policies_tenant → tenants.id  RESTRICT          ← D-B16-02
          · FK fk_ai_policies_space  → spaces.id   RESTRICT          ← D-B16-02
          · ck_ai_policies_no_unguarded_fallback（铁律 5）
          （STEP 3 与 STEP 4 可并行 —— SCHEMA_DEPENDENCY:212）

 STEP 5   create_table  ai_request_logs（PARENT, PARTITION BY RANGE (occurred_at)）
          · 17 列 · PK (id, occurred_at)  —— 分区键进 PK
          · FK fk_ai_request_logs_provider → ai_providers.id  RESTRICT   ← D-B16-03
          · FK fk_ai_request_logs_model    → ai_models.id     RESTRICT   ← D-B16-03
          · **无 status CHECK**（D-B16-04）· **无 updated_at** · **无 trigger**
          · **agent_id / actor_id / tenant_id / space_id 无 FK**（D-B16-03）

 STEP 6   CREATE TABLE ai_request_logs_<YYYYMM>  PARTITION OF ai_request_logs
          FOR VALUES FROM ('<月初 UTC>') TO ('<次月初 UTC>')             ← D-B16-05
          · 子分区继承 PK；当月子分区 = 1 个
          · 命名约定 = SCHEMA_DESIGN §9 DC-1（**DC-1 = A FROZEN**：ai_request_logs_<YYYYMM>，UTC 月边界）

 STEP 7   CREATE INDEX / CREATE UNIQUE INDEX
          · CREATE UNIQUE INDEX uq_ai_routes  ON ai_routes
              (COALESCE(tenant_id,'0…'), COALESCE(space_id,'0…'), capability, priority)
          · CREATE UNIQUE INDEX uq_ai_policies ON ai_policies
              (COALESCE(tenant_id,'0…'), COALESCE(space_id,'0…'), lower(name))
          · CREATE INDEX ix_airl_tenant_occurred ON ai_request_logs (tenant_id, occurred_at DESC)
              —— 建在**父表**，PG 自动下推至子分区（INDEX_STRATEGY:160）
          · （uq_ai_providers_key / uq_ai_models 由 STEP 1/2 的 UNIQUE CONSTRAINT 隐式建立）

 STEP 8   CREATE TRIGGER ×4（复用 set_updated_at()，**不重建函数**）
          · tg_ai_providers_set_updated_at  BEFORE UPDATE ON ai_providers
          · tg_ai_models_set_updated_at     BEFORE UPDATE ON ai_models
          · tg_ai_routes_set_updated_at     BEFORE UPDATE ON ai_routes
          · tg_ai_policies_set_updated_at   BEFORE UPDATE ON ai_policies
          （ai_request_logs 无 updated_at ⇒ **无 trigger**）
──────────────────────────────────────────────────────────────────
 SEED = 0（无任何 INSERT）
```

**实现形态约定**（沿用 `STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md:98`）

```
· 声明式表对象优先（op.create_table）
· 复杂对象（分区 DDL、trigger）用 op.execute + 显式注释
· 禁止在一个 revision 内混 schema 与 seed 数据
· 每条 FK/CK/UQ 显式命名（fk_<table>_<target> / ck_<table>_<field> / uq_<table>）
· 关键列附注释标明所依据的 Human Decision（如 `# D-B16-02 = A（FROZEN）`）—— 沿用 0008 的做法
```

---

## 4. 分区创建（详细）

```
父表   : ai_request_logs
方式   : PARTITION BY RANGE (occurred_at)
键边界 : 一律 UTC 月边界（CORE:921）
P08 建 : 当月子分区 1 个（D-B16-05 = FROZEN — A）
命名   : ai_request_logs_<YYYYMM>（UTC calendar month）← **DC-1 = A FROZEN**
PK     : 子分区继承 (id, occurred_at)
索引   : 父表索引自动下推（不额外建本地索引）
FK     : 声明在父表，自动下推
保留   : 90 天后按分区删除（CORE:358/963）—— **执行机制不在本阶段**
维护   : **手工运维（D-3 = D FROZEN）** —— 0010 不预建未来月份、不建自动清理、不引入 job /
         scheduler / pg_partman / CREATE EXTENSION，亦不修改 Docker / compose / worker runtime
```

**PG 兼容性**（环境实测 = PostgreSQL 16.15）

```
✅ PK 含分区键 —— 满足 PG 对分区表 PK 的强制要求
✅ 从分区表到普通表的 FK —— PG 支持（声明在父表）
✅ 父表索引下推 —— PG 支持
⚠️ 本表**无 UQ** ⇒ 不涉及"分区表唯一索引必须包含分区键"的约束
```

---

## 5. downgrade 顺序（严格逆序，无 orphan）

```
 1) DROP TRIGGER ×4（tg_ai_*_set_updated_at）
 2) DROP INDEX  uq_ai_routes · uq_ai_policies · ix_airl_tenant_occurred
 3) DROP TABLE  ai_request_logs_<YYYYMM>       ← **先 DROP 子分区**（SCHEMA_DEPENDENCY:270）
 4) DROP TABLE  ai_request_logs                ← 再 DROP 父表
 5) DROP TABLE  ai_policies
 6) DROP TABLE  ai_routes
 7) DROP TABLE  ai_models
 8) DROP TABLE  ai_providers
───────────────────────────────────────────────
 不 DROP：set_updated_at() · uap_uuid_v7()（既有函数，属前置阶段）
 不触碰：tenants / spaces / users / 既有 27 trigger / 既有对象
 不回滚：audit_logs / events（P10，不存在）· 无审计类数据被 downgrade 删除
```

**幂等与可逆性要求**

```
· downgrade 后 B1-6 相关对象残留 = 0（表 / trigger / index / 函数实例）
· set_updated_at() 实例数仍为 1（未被误重建）
· uap_uuid_v7() 完好
· B1-5 及更早对象完好（tools 三表 / resources 三表 / platform_state …）
· roundtrip: upgrade → downgrade → upgrade 三次对象集逐项一致
```

---

## 6. Migration Verification（实施轮须完成）

| 项 | 内容 |
|---|---|
| **A. Fresh upgrade** | `0001 → 0010` 成功；head = `0010` |
| **B. Catalog 全量核对** | 5 表 · 73 列 · PK 5 · **FK 8（1 CASCADE + 7 RESTRICT）** · UQ CONSTRAINT 2 · UQ INDEX 2 · CK 8 · trigger 4 · 函数新增 0 · 非 PK 索引 5 |
| **C. 分区核对** | 父表 `relkind='p'`；当月子分区存在且 PK 继承；索引下推可见 |
| **D. Downgrade** | `0010 → 0009`；B1-6 对象残留 = 0；既有对象完好 |
| **E. Re-upgrade** | `0009 → 0010`；对象集与首次逐项一致 |
| **F. Seed 核对** | 5 表 `count(*) = 0` |
| **G. Guard** | Architecture Guard 9 passed · Core→Domain = 0 · 平台精度 guard PG1–PG7 覆盖新表 |
| **H. 回归** | 全量回归不低于既有基线（B1-6 实施轮新增 38 canonical 项） |
| **I. Production Guard** | **`formal uap` 全程保持 0 tables**；所有验证仅在 disposable 库执行 |
| **J. 负向验证** | 非法 CK 值被拒 · RESTRICT 删除被拒 · status 任意值可写入（S5 豁免）· 无 agent_id FK |

---

## 7. 运维顺序要求（N-3 处置结论）

**问题**：`ai_request_logs` 带 FK RESTRICT ⇒ 删除 `ai_providers` / `ai_models` 前须先清 request log。

**结论：可在不改变 D-B16-03 的前提下通过 operational ordering 处理 ⇒ 无需 schema 变更。**

```
purge(ai_provider) 顺序：
  1) 清理引用该 provider / 其 models 的 ai_request_logs
     · 路径 a：经**手工分区维护 / 清理**移除整分区
       （**D-3 = D FROZEN ⇒ 无自动维护机制**；DROP 分区不触发 FK 检查 —— 整分区移除引用行）
     · 路径 b：显式 DELETE（受分区裁剪加速）
  2) 解除 ai_routes 对相应 models 的引用
  3) 删除 ai_models（F2 / F8 引用已解除；F1 关系随 provider 处理）
  4) 删除 ai_providers（F1 CASCADE 此时可完成）
```

**未改变项**：全部 `ON DELETE` 保持 D-B16-02 / D-B16-03 冻结值；未新增 trigger；未新增 FK；未改变 PK。

**D-3 = D FROZEN 同步**：分区自动维护机制**不属于** B1-6 migration implementation；
未来月份分区的创建与 90 天保留清理为 P08 的**人工运维职责**（见 `B1-6_DECISION_LOG.md` §9.5）。

**关联登记**：`CORE:985` 的「模型目录随 provider purge 清理」在 F8 RESTRICT 存在时不能一步到位 ——
该表述与冻结事实的措辞差异登记为 **DESIGN OBSERVATION（N-1）**，见 `B1-6_SECURITY_REVIEW.md` §4。

---

## 8. 迁移护栏（Production Guard）

```
· 不得对正式 `uap` 执行 upgrade（formal uap 必须保持 0 tables）
· 不得 `alembic upgrade head` 于正式库
· 所有验证使用 disposable 库（如 uap_b1_test）；完成后复位
· 不得修改 0001–0009 / env.py / alembic.ini / script.py.mako
· 不得在同一 revision 内混入 seed 数据
· downgrade 仅限"上一版本 + 数据无损已验证"；生产回滚以备份恢复优先
```

---

## 9. 影响面预判

| 项 | 影响 |
|---|---|
| 新增对象 | 5 表（含 1 分区父 + 1 子分区）· 8 FK · 2 UQ CONSTRAINT · 2 UQ INDEX · 8 CK · 1 btree 索引 · 4 trigger |
| 既有对象 | **0 变更**（无 ALTER，无 DROP；仅复用 `set_updated_at()`） |
| 既有测试 | **须连带同步**：5 个 FORBIDDEN/FUTURE 集合 · 20 处 head 断言 · smoke 表清单（见 `B1-6_TEST_MATRIX.md` §8 AG3 / §9 AM5） |
| 正式库 | **0 影响**（不在正式库执行） |
| 业务代码 | **0 变更** |
| 分区维护 | **手工运维（D-3 = D FROZEN）**；0010 只建父表 + 当月子分区，不含预建/清理/扩展 |

---

## 10. 本轮禁止事项（重申）

```
× 创建 0010 migration
× 修改任何 migration（0001–0009）
× 修改 alembic env.py / alembic.ini / script.py.mako
× 执行 migration（upgrade / downgrade）
× DDL / DML / 修改数据库
× 创建 formal uap tables
× 修改 B0 文档
× 修改 B1-6_DECISION_LOG.md
× 修改测试 / 新增测试代码
× 修改业务代码 / Core / Domain
× commit / tag
```

---

## 11. Gate

```
B1-6 MIGRATION_PLAN = DESIGN（0010 未创建）
DESIGN DECISION FREEZE = PASS（D-1 = B · D-2 = B · D-3 = D · D-4 = A · DC-1 = A · T-1 = DEFERRED）
0010 = ABSENT
migration head = 0009_timestamp_precision（未变）
DATABASE = UNTOUCHED（DDL = 0 · DML = 0）
IMPLEMENTATION = BLOCKED
```
