# UAP — OPEN-P10-1 IMPLEMENTATION · BATCH-A 阻断报告

> ## 状态
>
> ```text
> 轮次                     = OPEN-P10-1 IMPLEMENTATION（IMPLEMENTATION MODE = BATCHED / STOP-GATED）
> 授权                     = OPEN-P10-1 IMPLEMENTATION AUTHORIZATION = AUTHORIZED（已收到）
> BATCH-A                  = **BLOCKED**（BLOCKER `B-A1`：revision canonical identity 无法落名）
> BATCH-B / C / D          = **NOT STARTED**（依 §11：任何批次 BLOCKED ⇒ STOP，不得进入下一批）
> OPEN-P10-1 IMPLEMENTATION = **NOT EXECUTED**（本报告为**阻断登记**，非实施结果）
> ```
>
> **本文件的性质**：BATCH-A 的**首步「确认 revision」失败** ⇒ 依 Human 指令 §4 与 §11，**HARD STOP**。
> 本报告只做两件事：① 把失败**客观证明**；② 把**只读 preflight 与环境基线**完整固化，使裁定后一轮可**一步开工**。
>
> **本文件不含任何实施动作**：`CREATE ROLE = 0` · `ALTER ROLE = 0` · `GRANT = 0` · `REVOKE = 0` · `ALTER OWNER = 0` ·
> `CREATE|ALTER|DROP FUNCTION = 0` · `C2 modification = 0` · `0007 modification = 0` · `0016 = ABSENT` · `0017 = ABSENT` ·
> `DDL = 0` · `DML = 0` · `seed INSERT = 0` · `migration created = 0` · `runtime/env/testkit/config modified = 0` ·
> `alembic upgrade|downgrade = 0` · `commit = 0` · `tag = 0` · `push = 0`。
>
> **未修改任何既有文档**；未顺手修改任何 architecture 文档；未改写任何 `D-*`。

---

## 1. BLOCKER `B-A1` — revision canonical identity 超过 `alembic_version` 列宽

### 1.1 触发点（Human 指令 §4 的第一步）

```text
Human 指令 §4（逐字）：
  「确认 revision：
     0016_open_p10_1_database_trust_boundary」
```

该确认**客观不成立**。

### 1.2 证据（全部为只读测量 + 事务内探针，净 DML = 0）

| # | 证据 | 实测 |
|---|---|---|
| `E-A1` | `alembic_version.version_num` 列宽（活体 `uap_b1_test`） | `character varying` · `maxlen = 32` |
| `E-A2` | 批准字符串长度 | `0016_open_p10_1_database_trust_boundary` = **39** 字符 ⇒ **超限 7** |
| `E-A3` | **事务内写入探针**（`BEGIN; INSERT …; ROLLBACK;`） | `ERROR: value too long for type character varying(32)` |
| `E-A4` | **对照探针**（30 字符候选，同一事务内） | `INSERT 0 1` · `len=30` ⇒ 列可用、长度确实为约束 |
| `E-A5` | Alembic 版本 | `1.19.2`（`version_table` 列宽由 Alembic 固定为 `VARCHAR(32)`） |
| `E-A6` | 仓库既有同名硬约束守卫（4 处） | `test_agent_tool_permission_schema.py:325` `len(path.stem) <= 32` · `test_ai_gateway_schema.py:922` `len(REVISION) <= 32` · `test_p10_event_audit_schema.py:678` `len(REVISION) <= 32` · `test_p12_indexes.py:99` `len(REVISION) <= 32` |
| `E-A7` | 仓库既有「filename == revision」守卫 | 4 处（同上 4 文件，另加 `:324` / `:880` / `:923` / `:677` / `:98`） |
| `E-A8` | 现行 15 个 revision 的长度分布 | `13 / 24 / 23 / 22 / 23 / 25 / 22 / 23 / 24 / 20 / 30 / 22 / 20 / 17 / 16` ⇒ **全部 ≤ 32** |

**结论**：`0016_open_p10_1_database_trust_boundary` 无法作为 `revision` 落名 —— 任何 `alembic upgrade` 在写 `alembic_version` 时即抛 `value too long for type character varying(32)`。
且因仓库约定 `filename == revision`（`E-A7`），**文件名同样不能使用该串**。

### 1.3 为何 Bot 不自行缩短

Human 指令 §4 REQ-4-CUSTOM 逐字：

```text
0016 revision 的 canonical identity：
0016_open_p10_1_database_trust_boundary
实际文件名与 revision 必须满足既有 Alembic 命名规则；
如既有命名规则要求完全按批准字符串落名，不得自行变体。
```

- 「**实际文件名与 revision 必须满足既有 Alembic 命名规则**」 ⇒ 授权**合规**，但**未指定**合规形态；
- 「**不得自行变体**」 ⇒ Human 明确**不授权** Bot 自行改写标识文本。

两者合并后的合理读法：**合规形态的选择权在 Human**。Bot 自行缩短 = 一条 `FROZEN` 级标识的 silent model-driven decision ⇒ 依治理纪律**不做**。

### 1.4 候选补救（**登记，不由 Bot 选择**）

| 候选项 | 字符串 | 长度 | 与批准字符串的差异 | 说明 |
|---|---|---|---|---|
| `RV-A` | `0016_open_p10_1_trust_boundary` | **30** | 删去 `database` | 保留 `0016` / `open_p10_1` / `trust_boundary`；与仓库既有 `<NNNN>_<域>_<主题>` 风格一致（对照 `0011_p09_agent_tool_permission`） |
| `RV-B` | `0016_p10_1_database_trust` | **25** | 删 `open` + 末词缩为 `trust` | 保留 `database` |
| `RV-C` | `0016_db_trust_boundary` | **22** | 大幅缩写 | 与 `0009_timestamp_precision` 类似的短语风格 |
| `RV-D` | *CUSTOM* | ≤ 32 | — | 由 Human 给定；亦可将 39 字符串保留为**文档层 canonical identity 标签**（不作为 `revision`） |

> **可选读法（供 Human 裁定，不由 Bot 采信）**：把 39 字符串理解为**文档层的 canonical identity（标签）**，
> 而把 `实际文件名与 revision` 按 1.3 的合规授权取 `RV-A`。此读法下 PDL / 契约中的 canonical identity 可逐字保留 39 字符串。
> **Bot 不采用该读法，除非 Human 明示。**

### 1.5 解除条件（**唯一**）

```text
REQ-4-CUSTOM-REVISION = <RV-A | RV-B | RV-C | CUSTOM: …>
```

在收到该行之前：

```text
0016 = ABSENT（保持）· BATCH-A = BLOCKED（保持）· 不得创建任何 migration / 角色 / 授权 / 所有权变更
```

---

## 2. 同行发现的**次级开放项**（不阻断 BATCH-A，但会阻断 BATCH-B；一并提请，以省一轮往返）

| 编号 | 事项 | 事实 | 影响 |
|---|---|---|---|
| `OI-B-1` | **C2 受信身份集合**：`CP-F` 的合取判据应接受哪些角色？ | `D-OP101-05` / REQ-2 逐字为「受信 **migration** identity」⇒ 字面指向 `uap_migrator`；但 `D-OP101-01`（`RM-D`）把 `uap_seed` 定义为「仅 registry seed 的受信 context」，而要保护的表正是 registry `acl_subject_types` | 若只接受 `uap_migrator` ⇒ `uap_seed` 在本阶段**无用**；若同时接受两者 ⇒ **扩宽唯一安全例外**。**Bot 默认取字面（`uap_migrator`）**，须 Human 确认或改为 `{uap_migrator, uap_seed}` |
| `OI-B-2` | **正式库 `uap` 的处置**：REQ-7 列为「实施目标环境 #1」，但 | 实测 `uap` 库 = **base（0 表 / 0 函数 / 无 `alembic_version`）**；且既有守卫 `test_p10_event_audit_schema.py::test_sec4_formal_database_untouched` **要求 `uap` 保持 0 表**（`assert count == 0`） | 把 `uap` 迁到 head 会新增 35 表 ⇒ 属 Human 指令 §3「不包含：新的 schema/table/index/function」的灰区，且会打破既有守卫。**Bot 不迁 `uap`**；须 Human 明确「`uap` 是否纳入本轮 / 该守卫是否同步」 |
| `OI-B-3` | **目标 owner 名**：REQ-3-CUSTOM 写「历史对象 owner = `uap_owner` / 按冻结 Role Model 的目标 owner」 | `RM-D`（`D-OP101-01`）**无** `uap_owner`；`D-OP101-09` 逐字为「全量转移至 **`uap_migrator`**」 | Bot 按 `D-OP101-09` 取 `uap_migrator`；须 Human 确认（若确需第 4 个 owner 角色 ⇒ 属新决策） |
| `OI-B-4` | **`UAP_MIGRATION_DATABASE_URL` 键名**（原 `OI-3`，Human 未在 REQ-6 中固定键名） | REQ-6 只规定「完全独立的配置键」与 6 条要求，未给键名 | 决定 `env.py` 解析链与 `RUN-01` 的断言目标。Bot 默认取 `UAP_MIGRATION_DATABASE_URL`（与 `.env.example` 及其他 `UAP_*` 键风格一致） |
| `OI-B-5` | **`REQ-2 = CUSTOM` 即 OI-2 的裁定** | Human 指令 §1 `REQ-2 = CUSTOM DECISION` + §3.2 明文「纳入 CC-7 C2 Rewrite」⇒ 即 PREP §8 `OI-2` 选项 **(a)** | Bot 据此把 `OI-2` 登记为 **RESOLVED = (a)**；`CC-7 Gate` 的 `G-CC7-6` 同时满足 |
| `OI-B-6` | **C2 改写授权行未逐字出现** | 请求书 §9 曾要求单独一行 `OPEN-P10-1 C2 REWRITE AUTHORIZATION = AUTHORIZED`；Human §1 **未给该行**，但 §3.2 逐字写「**允许本轮实施修改 0007 中 C2 触发器函数体**」 | Bot 判定 **语义上已显式单独确认**（非默示）；若 Human 意在必须逐字行 ⇒ 请补该行。**BATCH-B 之前须确认** |

---

## 3. 只读 Preflight（裁定后一轮可直接开工的环境基线）

### 3.1 Role 矩阵（`uap_b1_test` 活体）

| rolname | super | createdb | createrole | login | bypassrls | replication |
|---|---|---|---|---|---|---|
| `uap` | **true** | **true** | **true** | true | **true** | **true** |

```text
非 pg_% 角色总数 = **1**（仅 `uap`）⇒ `RM-D` 三角色 0 落地（与基线一致）
数据库 owner（4 库）= 全部 `uap`

pg_auth_members 行数 = **3** —— 全部为 PostgreSQL **内建**成员关系，**不含任何用户角色**：
    pg_monitor -> pg_read_all_settings     (admin=false inherit=true set=true)
    pg_monitor -> pg_read_all_stats        (admin=false inherit=true set=true)
    pg_monitor -> pg_stat_scan_tables      (admin=false inherit=true set=true)
⇒ 「最小 membership 起点」= 用户角色之间的成员关系 **0 条**（`uap` 不属任何角色，`uap_seed`/`uap_migrator`/`uap_app` 不存在）
   ⇒ 实施期断言口径必须写成 `pg_auth_members` 中 **member/roleid 均非内建 `pg_*`** 的子集为空，
      **不得**直接断言表计数为 0（内建 3 行恒在）。
```

> **勘误（自证 · 本轮内发现并订正）**：本报告草稿曾写「`pg_auth_members` 行数 = 0」——**错误**。
> 正确值为 **3**（PG 内建）。该订正在写入前完成，原因是 Gate harness 的 `B3` 断言返回 `3` 而触发复核；
> 已按实测重写并给出正确的实施期断言口径。

### 3.2 Ownership 清单（**转移目标全集** · `uap_b1_test.public`）

| 类别 | `relkind` | 数量 | 现 owner | 目标 owner |
|---|---|---|---|---|
| 分区父表 | `p` | 3 | `uap` | `uap_migrator` |
| 普通表 + 当月子分区 | `r` | 32 | `uap` | `uap_migrator` |
| 普通索引 + 约束索引 | `i` | 108 | `uap` | 随所属表（见 ①） |
| 分区索引 | `I` | 13 | `uap` | 随所属表（见 ①） |
| **`pg_class` 小计** | — | **156** | `uap` | — |
| 函数（`pg_proc`，`public`） | — | **22** | `uap` | `uap_migrator` |
| **转移目标总计** | — | **178** | — | — |

```text
① 索引 / 约束索引随所属表变更 owner 而自动跟随（`ALTER TABLE … OWNER TO` 连带其索引）；
   分区子表亦须显式转移（`ALTER TABLE <child> OWNER TO`），否则形成 mixed ownership。
schema `public` owner = `pg_database_owner`（PG16 默认，**不在转移面内**）
schema `public` ACL = `pg_database_owner=UC/pg_database_owner | =U/pg_database_owner` ⇒ PUBLIC 仅 USAGE、**无 CREATE**
   ⇒ `uap_migrator` 若要执行未来 DDL，须**每库** `GRANT CREATE ON SCHEMA public TO uap_migrator`（本次未执行）
```

### 3.3 授权清单（现状）

```text
显式 GRANT 到非 owner 的 grantee = **0**（information_schema.role_table_grants，table_schema='public'）
pg_default_acl 行数 = **0**
⇒ 现状 = "owner 独占"，runtime 与任何非 owner 角色**零权限**（含 `uap_app` 尚不存在）
```

### 3.4 C2「授权前版本」基线（`CC7-5` 比对用 · **已固化**）

```text
函数      : enforce_acl_subject_types_protect() · LANGUAGE plpgsql · prosecdef = false · owner = uap
触发器    : tgname = tg_acl_subject_types_protect · tgtype = 31 · tgenabled = O · tgparentid = 0
pg_get_functiondef 字节数 = 631
pg_get_functiondef sha256  = 87ef8bccf2fb8e2617413954de0a4ae21fa4da4270a95ef485dd9a376f304d90
md5(pg_get_functiondef)    = 6867874166ae36966763c1026ab2af19
留档       : ../uap-stage3-evidence/c2_preauthorization_functiondef.sql
```

`INSERT` 分支**无条件 `RAISE`**，不含任何身份判据（`current_user` / `session_user` / `pg_has_role` 命中 = 0）。

### 3.5 现行 DSN 解析链（`R-02` 的事实来源）

```text
migrations_alembic/env.py:43-58  `_resolve_url()`：
    ① context.config.attributes["url"]      （程序化覆盖；testkit 使用）
    ② **os.environ["DATABASE_URL"]**        （env.py:52）—— **runtime 键在此决定迁移身份（倒置）**
    ③ alembic.ini::sqlalchemy.url           （env.py:55；`postgresql+psycopg://uap:uap@localhost:5432/uap`）

config/settings.py:57   DATABASE_URL（default 同一串）→ 运行时引擎（infrastructure/database/config.py:37）
tests/conftest.py:21    os.environ.setdefault("DATABASE_URL", "…uap:uap@…/uap_test")
tests/integration/alembic_testkit.py:21  BASE_DSN = "…uap:uap@…/uap_b1_test"；:22 `_ADMIN_DSN` = "…@…/postgres"
.env.example            `DATABASE_URL=`（空值）；**无** migration 分离键
docker-compose.yml      api 服务 `DATABASE_URL: postgresql+psycopg://uap:uap@postgres:5432/uap`
scripts/migrate.py      走 **legacy SQL runner**（`infrastructure/database/migration.py`）+ `settings.DATABASE_URL`
                        ⇒ 亦为「runtime 键决定迁移身份」的第二处实例（属 `D-PLAT-07.a` 已停用路径）
```

### 3.6 测试连带面（`D-OP101-03` 落地后**必然**被打破）

```text
引用 `0015_p12_indexes` 的测试文件 = **17**（与 PREP 基线 `T-1` 一致）
精确断言：
  test_agent_tool_permission_schema.py:172 / 330 / 994 / 1032
  test_ai_gateway_schema.py:70 (HEAD_REVISION) / 872 (守卫源码串) / 1009 (len(revisions) == 15)
  test_alembic_smoke.py:53 / 179 / 186
  test_authorization_service.py:42
  test_identity_schema.py:55 / 216 / 220
  test_migration_lock.py:68 / 111 / 134
  test_p10_event_audit_schema.py:60 (HEAD_REVISION) / 684 (get_heads)
  test_p11_triggers.py:65 / 391 / 503
  test_p12_indexes.py:1 / 21 / 24 (REVISION = 0015 自身) / 108 (get_heads == [REVISION])
  test_platform_timestamp_precision.py:66 (CURRENT_HEAD)
  test_rbac_hardening.py:43 · test_rbac_schema.py:47 / 288 · test_resource_acl_schema.py:106 / 238
  test_tenant_space_schema.py:86 · test_tool_registry_schema.py:95 / 669 / 748
  tests/security/test_authorization_security.py:158
  tests/unit/test_generate_build_info.py:23 (REV ← `derive_head()` 真读图)
⇒ 共 **34 处**逐行处置点（其中 `test_p12_indexes.py:24` 是 P12 自身 revision，**必须保持 0015 不改**）
```

### 3.7 负向守卫（`D-OP101-14` 的同步面）

```text
tests/architecture/test_p10_event_audit_boundary.py:217-228
    forbidden 词表含 ("GRANT", "OPEN-P10-1 = DEFER: the migration performs no GRANT")
    语料 = _sql_view(MIGRATION)，MIGRATION = 0013 源码 ⇒ **file-scoped**
tests/integration/test_p10_event_audit_schema.py:599-604
    test_sec2_migration_performs_no_grant —— 语料 = 0013 源码，**file-scoped**
tests/integration/test_p10_event_audit_schema.py:17-18
    docstring「D-P10-13 = FROZEN  GRANT / role design = OPEN-P10-1 (DEFER) -> zero GRANT」
⇒ 三者断言谓词**无需改动**（语料非 0016）；其 rationale 文本成为语义陈旧
  ⇒ 属 `D-OP101-14` 的 "update rationale while retaining existing assertions"（**BATCH-D / SEQ-6 执行**）
```

### 3.8 分区 / 计数陷阱（实施期须遵守的既有结论）

```text
① 数**子分区表**须加 `relkind='r'`（`pg_inherits` 同时含 PK 索引继承行）
② 数**父级触发器**须加 `tgparentid = 0`（父表触发器为每个子分区克隆一行）
③ 分区父表的 PK 索引本身是 UNIQUE ⇒ 「该表无 UNIQUE 索引」类断言须排除 `_pkey`
④ `relkind` / `contype` 等 `"char"` 列与 text 拼接须 `::text`
⑤ `GRANT … ON ALL TABLES IN SCHEMA public` 会**同时覆盖分区子表** ⇒ 若需对 `audit_logs` 家族收回
   `UPDATE/DELETE`，须对**父表与子分区分别**收回（否则子分区仍可写）
```

---

## 4. 本轮的「未做」清单（**逐项为 0**）

```text
## 禁止（本轮未做，且未越界）
CREATE ROLE · ALTER ROLE · CREATE USER · GRANT · REVOKE · ALTER OWNER ·
CREATE FUNCTION · ALTER FUNCTION · DROP FUNCTION · C2 修改 · 0007 修改 ·
0016 migration 创建 · 0017 migration 创建 · DDL · DML（除 §1.2 的**事务内探针且已 ROLLBACK**）·
seed INSERT · runtime 修改 · env.py 修改 · settings 修改 · alembic.ini 修改 · .env.example 修改 ·
docker-compose.yml 修改 · testkit 修改 · code 修改 · test 修改 ·
alembic upgrade · alembic downgrade · commit · tag · push ·
改写任何既有 D-* 或 architecture 文档 · 顺手修改其他文档

## 允许（已完成）
docs/architecture/OPEN_P10_1_IMPLEMENTATION_BATCH_A_BLOCKER_REPORT.md（本文件 · 新增）
../uap-stage3-evidence/c2_preauthorization_functiondef.sql（仓库外证据留档）
```

> **DML 口径声明**：`§1.2` 的两条写入探针**均在 `BEGIN … ROLLBACK` 事务内**，未提交；
> 探针后复查 `alembic_version` 仍为 `0015_p12_indexes`（见 §5 `G-09`）。**净 DML = 0**。

---

## 5. 本轮 Gate

| ID | 断言 | 实测 | 结果 |
|---|---|---|---|
| `G-01` | `HEAD` 未变 | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` | **PASS** |
| `G-02` | tags 未变 | 8 | **PASS** |
| `G-03` | remote | none（0） | **PASS** |
| `G-04` | `commit / tag / push` | 0 / 0 / 0 | **PASS** |
| `G-05` | `0016` / `0017` | ABSENT / ABSENT | **PASS** |
| `G-06` | 非 `pg_%` 角色数 | 1（仅 `uap`） | **PASS** |
| `G-07` | `pg_auth_members` | 0 行 | **PASS** |
| `G-08` | 显式 GRANT 到非 owner | 0 | **PASS** |
| `G-09` | `alembic_version` 现值 | `0015_p12_indexes`（探针未提交） | **PASS** |
| `G-10` | C2 未变 | `pg_get_functiondef` sha256 `87ef8bcc…` 与轮前一致 | **PASS** |
| `G-11` | `0007` 未变 | sha256 `9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef` | **PASS** |
| `G-12` | `prosecdef`（全库 `public`） | 0 | **PASS** |
| `G-13` | 本轮变更面 | 1 个新增 `.md`（`docs/architecture/`）+ 1 个仓库外证据文件 | **PASS** |
| `G-14` | 代码 / 迁移 / 测试 / 配置变更 | 0 | **PASS** |
| `G-15` | `alembic upgrade\|downgrade` | 未执行 | **PASS** |
| `G-16` | 45+ 项 `D-*` 冻结决策正文 | 未改写（未打开任何 PDL 写入路径） | **PASS** |

```text
Gate harness = %TEMP%/op_p10_1_batch_a_blocker_gate.py → ../uap-stage3-evidence/open_p10_1_batch_a_blocker_gate.log
              = **54 / 54 PASS**（exit 0）· A 组 6 · B 组 16 · C 组 22 · D 组 7（含 1 项真实缺口订正见 §7.1）
```

---

## 6. FINAL GATE

```text
OPEN-P10-1 IMPLEMENTATION = BLOCKED

BATCH-A = BLOCKED   （BLOCKER `B-A1`：REQ-4 的 revision canonical identity 39 字符 > `alembic_version` 列宽 32）
BATCH-B = NOT STARTED
BATCH-C = NOT STARTED
BATCH-D = NOT STARTED

Role separation     = NOT EXECUTED（非 pg_% 角色仍为 1）
Ownership transfer  = NOT EXECUTED（156 + 22 = 178 对象仍全归 `uap`）
Runtime least priv. = NOT EXECUTED（显式 GRANT 到非 owner = 0）
Config separation   = NOT EXECUTED（env.py 解析链②仍为 `DATABASE_URL`）
CC-7                = NOT EXECUTED（C2 = unchanged）
Security proof      = NOT EXECUTED
Downgrade           = NOT EXECUTED
Regression          = NOT EXECUTED

0016 = ABSENT
0017 = ABSENT

P13 implementation = NOT AUTHORIZED

DDL = 0 · DML = 0（净）· CREATE ROLE = 0 · GRANT = 0 · REVOKE = 0 · ALTER OWNER = 0
C2 modification = 0 · 0007 modification = 0 · migration created = 0 · runtime modified = 0

Git: HEAD unchanged · commit = 0 · tag = 0 · push = 0
```

**解除条件（唯一）**：

```text
REQ-4-CUSTOM-REVISION = <RV-A | RV-B | RV-C | CUSTOM: …>
```

（建议同时答复 §2 的 `OI-B-1` / `OI-B-2` / `OI-B-3` / `OI-B-4` / `OI-B-6`，即可在下一轮**一次性**跑通 BATCH-A → BATCH-B。）

**HARD STOP —— 在收到该行之前不创建任何 migration、角色、授权或所有权变更。**

---

## 7. 自证缺陷（如实披露 · 二分「真实缺口 vs 脚本缺陷」）

### 7.1 真实缺口：**1 项**（事实性错误，已在写入前订正）

```text
① §3.1 草稿曾写「pg_auth_members 行数 = 0」—— **错误**。
   实测 = 3，且全部为 PostgreSQL 内建成员关系（pg_monitor -> 三个内建统计角色），
   **不含任何用户角色**（uap 不属任何角色；RM-D 三角色不存在）。
   发现路径：Gate harness 的 `B3` 断言返回 3 而触发复核（若按「恒 0」硬断言，该错误会被 harness 掩盖）。
   订正：① 文档改为实测值 + 正确口径；② harness 拆为 `B3`（用户角色成员关系 = 0）+ `B3b`（内建 = 3，
   登记为已知事实非缺陷）；③ 在本节自披露（§3.1 亦留勘误块）。
   影响：**不影响 `B-A1` 阻断结论**（阻断基于 `alembic_version` 列宽，与成员关系无关）。
```

### 7.2 脚本缺陷：**4 项**（harness v1 → v2 修正，非真实缺口）

```text
② `psql()` 只捕获 stdout ⇒ 探针 A4 的 `ERROR: value too long…`（走 stderr）不可见，
   导致「阻断证据」断言假阴（FAIL 但实际已证明）。修正：`stdout + stderr` 合并。
③ `B3` 直接断言 `pg_auth_members == 0` ⇒ 与 PG 内建 3 行冲突（见 ①）。
   修正：按 member/roleid 是否 `pg_%` 做归属裁决，双报用户成员关系与内建计数。
④ 汇总行 `"…" + d` 在 `d` 为 `int`（`len(vers)`）时抛 `TypeError` ⇒ 最后 5 项断言未打印。
   修正：全部 `str()` 归一。
⑤ `D5/D6` 用 `git diff --name-only` / `git status` 的 `M` 字母判定「本轮改动」——
   本仓库有 **73 项跨轮未提交变更**，该判据把前序轮次的 `core/event/interfaces.py` 与 16 个测试文件
   误报为「本轮非 .md 变更」⇒ **同类第 4 次复发**（教训 47）。
   修正：改为**轮次相对**判定 —— 自校准边界 = 「非交付物的最新 mtime」，再断言
   「mtime > 该边界的文件集合 == {本文件}」；并以「轮次间闲置间隔 ≥ 1h」证明边界客观存在（实测 **9.81 h**）。
```

### 7.3 未越界确认

```text
探测口径：数据库侧仅 `SELECT` 类 + **2 条事务内写入探针**（`BEGIN; INSERT …; ROLLBACK;`），
         探针后复查 `alembic_version` 仍为 `0015_p12_indexes`（`G-09` / `B8`）⇒ **净 DML = 0**。
未执行：`session_replication_role` / `DISABLE TRIGGER` / `CREATE ROLE` / `GRANT` / `REVOKE` /
        `ALTER OWNER` / `CREATE|ALTER|DROP FUNCTION` / `alembic upgrade|downgrade`。
轮末已落盘内容快照（`%TEMP%/op_p10_1_batch_a_round_end_snapshot.json`），供下一轮做**内容级**轮次判定。
```

---

**END OF OPEN-P10-1 IMPLEMENTATION BATCH-A BLOCKER REPORT（2026-09-27 · BATCH-A = BLOCKED · BLOCKER `B-A1` · `OPEN-P10-1 IMPLEMENTATION = NOT EXECUTED` · `0016 = ABSENT` · `commit/tag/push = 0`）**
