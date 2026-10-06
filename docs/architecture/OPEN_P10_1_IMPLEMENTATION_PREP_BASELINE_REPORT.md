# UAP — OPEN-P10-1 IMPLEMENTATION PREP BASELINE REPORT（Phase 0）

> ## 状态
>
> ```text
> 轮次        = OPEN-P10-1 IMPLEMENTATION PREP — Phase 0（STRICT READ-ONLY BASELINE）
> 文档状态    = **BASELINE · READ-ONLY · NOT FROZEN**
> 性质声明    = **Decision Freeze ≠ Implementation Authorization**
>               `OPEN-P10-1 DECISION = FROZEN` · `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED`
> 本轮未做    = 未 CREATE ROLE · 未 GRANT/REVOKE · 未 ALTER ROLE/OWNER · 未 CREATE|ALTER|DROP FUNCTION ·
>               未改 C2 · 未改 0007 · 未创建 0016/0017 · 未 DDL/DML · 未 seed INSERT ·
>               未改 runtime / env.py / settings / testkit / code · 未 alembic upgrade|downgrade · 未 commit/tag/push
> ```
>
> **本文件只做一件事**：把「即将被实施的对象」的**当前事实**钉住，供 `OPEN_P10_1_IMPLEMENTATION_CONTRACT.md` 与
> `OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` 引用。**不含任何实施、不含任何设计选择。**

---

## 1. Git Baseline

| 项 | 实测值 |
|---|---|
| `HEAD` | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` |
| branch | `main` |
| tags | **8**（全部 annotated **unsigned**；仓库无 GPG ⇒ `git tag --verify` 恒 `no signature found`，**非缺陷**） |
| remote | **none**（`git remote -v` = 0 行；从未 push） |
| dirty state | `git status --porcelain` = **69** 条（全部为**前序轮次已授权但未提交**的交付物；**本轮未新增/回退任何条目**） |

**dirty 集构成（只读分类 · 供 scope 判定复用）**

```text
已跟踪且 modified（M）  ： docs/architecture/*.md（8 个）· docs/{api,security}/README.md ·
                          core/event/interfaces.py · tests/**（16 个 .py）
未跟踪（??）            ： docs/architecture/ 下的各阶段 PREP/CONTRACT/MATRIX/DECISION_* 文档 ·
                          migrations_alembic/versions/001[3-5]*.py · tests/{architecture,integration}/test_p1*_*.py
```

> **注**：`migrations_alembic/versions/001[3-5]*.py` 属 **P10/P11/P12 实施轮的已授权交付物**（`??` 未跟踪），
> **不属**「迁移被修改」。`0007_b1_4_resource_acl.py` **不在** dirty 集中 ⇒ **未修改**。

---

## 2. Migration Baseline

| 项 | 实测值 |
|---|---|
| 单 HEAD | `alembic heads` = **`0015_p12_indexes`**（**1 行** ⇒ 单 HEAD） |
| revision 文件数 | **15**（`0001` … `0015`） |
| `0016` 是否存在 | **ABSENT**（`versions/0016*` = 0） |
| `0017` 是否存在 | **ABSENT**（`versions/0017*` = 0） |
| `0018+` | **ABSENT** |
| 链长 | **15**（`0001_baseline` → `0015_p12_indexes`） |

**关键迁移指纹**

```text
0007_b1_4_resource_acl.py   sha256 = 9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef   （未修改）
0010_b1_6_ai_gateway.py     sha256 前16 = 6d9907237f80e9da
0011_p09_agent_tool_permission.py      = cdaf8383630335db
0012_authz_enforcement.py              = 5ecd1ef30b403fb4
0013_p10_event_audit.py                = da1bdffd4ddd2202
0014_p11_triggers.py                   = 3be9c8c092869c8d
0015_p12_indexes.py                    = 94b0d22800c8971e
```

**revision 归属（依 `D-OP101-03` 冻结文本 · 仅登记，不创建）**

```text
0016 → 归属 OPEN-P10-1 Database Trust Boundary Foundation
0017 → P13 seed（由后续 P13 Implementation Contract 正式登记为 `0017_p13_seed`）
⇒ 两者的**创建**均**未被授权**（本 PREP 轮亦不创建）
```

---

## 3. Database Baseline（**只读** · `uap_b1_test` @0015）

> `uap_b1_test` 为**唯一处于正式链头**的库；`uap`（formal）实测 0 表；`uap_test` 为 `tests/conftest.py` 默认库。
> 本轮**只执行 `SELECT` 类查询**（无 `INSERT`/`UPDATE`/`DELETE`）。

### 3.1 Roles

| 项 | 实测值 |
|---|---|
| 非 `pg_%` 角色 | **1**（仅 `uap`）⇒ `CORE §13` 三角色 / `RM-D` 四角色 **均未落地** |
| `uap` 属性 | `rolsuper=t` · `rolinherit=t` · `rolcreaterole=t` · `rolcreatedb=t` · `rolcanlogin=t` · `rolreplication=t` · `rolbypassrls=t` · `rolconnlimit=-1` · `rolvaliduntil=NULL` |
| `pg_auth_members` | **3 行，全部为 PG 内建**（`pg_monitor` ← `pg_read_all_settings` / `pg_read_all_stats` / `pg_stat_scan_tables`）⇒ **不涉及 `uap`** |
| 集群级特性 | 角色为 **cluster-scoped** ⇒ 同一 cluster 的 `postgres` / `uap` / `uap_b1_test` / `uap_test` **共享角色集合** |

### 3.2 Schema / Ownership

| 项 | 实测值 |
|---|---|
| `public` 对象总数 | **156**（表 / 索引 / 函数 / 视图） |
| owner 分布 | **`uap` × 156**（唯一 owner） |
| 表（`r`+`p`） | **35**（含 **3** 个子分区表） |
| 索引 | **108** · 序列 **0** · 视图 **0** |
| 函数 | **22**（owner 全为 `uap` · `prosecdef = 0` · `proconfig` 全空） |
| 父级触发器（`tgparentid=0`） | **39** · 触发器行（含子分区克隆）**40** |
| `public` schema | owner = `pg_database_owner`（PG16 默认）· ACL = `pg_database_owner=UC | =U` ⇒ **PUBLIC 仅 `USAGE`、无 `CREATE`** |
| 数据库 ACL | `NULL`（默认）⇒ 无库级显式授权 |
| 显式 `GRANT` 到非 owner | **0** · `pg_default_acl` = **0 行** |
| 4 库 owner | 全为 `uap` |

### 3.3 C2 当前函数状态（**逐字** · `pg_get_functiondef`）

```text
触发器 : tgname = tg_acl_subject_types_protect · tgtype = 31 · tgenabled = O · tgparentid = 0
函数   : enforce_acl_subject_types_protect() · LANGUAGE plpgsql · prosecdef = false · owner = uap · proconfig 空

BEGIN
  IF TG_OP = 'INSERT' THEN
    RAISE EXCEPTION
      'acl_subject_types is a platform-controlled registry: runtime INSERT denied '
      '(registry rows are migration-controlled)';
  ELSIF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION
      'acl_subject_types rows cannot be deleted (retire via archived_at)';
  ELSE  -- UPDATE
    IF NEW.key IS DISTINCT FROM OLD.key THEN
      RAISE EXCEPTION 'acl_subject_types.key is immutable (registry governance)';
    END IF;
    RETURN NEW;
  END IF;
END;

⇒ INSERT 分支**无条件 RAISE**（无任何身份判据：不含 current_user / session_user / pg_has_role）
⇒ 拒绝消息由**两条相邻字符串字面量**隐式拼接（逐字文本见上，中间恰一个空格）
```

### 3.4 `0007` 当前状态

```text
migrations_alembic/versions/0007_b1_4_resource_acl.py
  sha256 = 9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef
  未修改（不在 git dirty 集中）· C2 由该迁移创建（D-B14-12 = A）
```

### 3.5 `@0015` 种子现状

```text
acl_subject_types = 0 · permissions = 0 · roles = 1（platform_admin）· role_permissions = 0
users = 0 · tenants = 0 · platform_state = 1
```

---

## 4. Decision Baseline

### 4.1 决策载体（读取结果）

| 文件 | 状态 | 指纹 / 计数 |
|---|---|---|
| `PLATFORM_DECISION_LOG.md` | **已写入并冻结** | sha256 = `a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56` · 3633 行 · END 行 **16** |
| `OPEN_P10_1_DECISION_RESOLUTION.md` | 请求单（保持 `PENDING` 时点快照，**未被回填**） | sha256 = `2854fe9d18e77da2a338592539677f0d25da562d206c258694ec513d5580afa3` · 647 行 |
| `OPEN_P10_1_HUMAN_DECISION_RECORD.md` | 收据与登记（`DECISION RECEIPT · REGISTERED`） | 9 节 |

> **命名说明（如实披露）**：Human 指令引用的 `OPEN_P10_1_DECISION_RECORD.md` 在仓库中实际名为
> **`OPEN_P10_1_HUMAN_DECISION_RECORD.md`**（本 PREP 轮以**实际存在**的文件为准并登记该差异，不重命名、不新建同义文件）。

### 4.2 `D-OP101-01` … `D-OP101-14` 存在性校验

| ID | 标题（PDL 行号） | 存在 |
|---|---|---|
| `D-OP101-01` | 角色拓扑（`RM-D`）（L2847） | ✅ |
| `D-OP101-02` | migration identity 的权限等级（L2859） | ✅ |
| `D-OP101-03` | revision 编号归属（L2871） | ✅ |
| `D-OP101-04` | 角色创建者（L2893） | ✅ |
| `D-OP101-05` | C2 判据形态（L2905） | ✅ |
| `D-OP101-06` | 是否同时落地 `uap_readonly`（L2949） | ✅ |
| `D-OP101-07` | runtime GRANT 矩阵范围（L2961） | ✅ |
| `D-OP101-08` | 「runtime 不持 DDL」是否由 DB 层强制（L2973） | ✅ |
| `D-OP101-09` | 既有 156 对象的所有权（L2985） | ✅ |
| `D-OP101-10` | 配置 / 环境面承载双身份（L2997） | ✅ |
| `D-OP101-11` | 测试基建与集群级角色（L3009） | ✅ |
| `D-OP101-12` | downgrade 语义（L3021） | ✅ |
| `D-OP101-13` | 「身份隔离已成立」的机读判据（L3033） | ✅ |
| `D-OP101-14` | 既有守卫 rationale 的同步口径（L3045） | ✅ |

```text
`^# D-OP101-\d{2} —` 命中 = **14** ⇒ **14 / 14 全部存在**（顺序 01 → 14）
命名空间现行计数：D-PLAT 17 · D-AUTH 25 · D-AGENT 16 · D-P10 18 · D-P11 14 · D-P12 15 · D-P13 15 · **D-OP101 14**
supersession 注册行 = 1（未变）
```

### 4.3 冻结摘要（**只读转录 · 不再解释**）

```text
Role Model = RM-D（uap_seed / uap_migrator / uap_app）
Migration Identity = NOSUPERUSER
Role Creation = deployment / orchestration / operations pre-provision
C2 = CP-F（CUSTOM：current_user ∧ session_user 合取）· CC-7 批准（CC7-1…6）
uap_readonly = DEFER
Runtime GRANT = minimum required set
DDL restriction = DB enforced + positive assertion + negative probe
Existing 156 object ownership = full ownership transition
Dual identity configuration = independent migration/runtime keys + explicit resolution chain
Test infrastructure = testkit role provisioning + dual DSN fixtures
Downgrade = REVOKE and retain cluster role（migration 不得 DROP ROLE）
Isolation acceptance criterion = topology landed + complete eight-test proof
Guard rationale = update rationale while retaining existing assertions
```

---

## 5. 配置 / 身份耦合基线（R-02 的事实来源 · **只读**）

```text
C-1  migrations_alembic/env.py:43-57  `_resolve_url()` 优先级（逐字顺序）：
       1. config.attributes["url"]（程序化覆盖；testkit 使用）
       2. **`DATABASE_URL` 环境变量**（env.py:52 `os.environ.get("DATABASE_URL")`）
       3. alembic.ini 的 `sqlalchemy.url`（env.py:55）
     env.py:109 / :123 均以 `_resolve_url()` 作为连接 URL
C-2  alembic.ini:3 注释（逐字）：「Runtime URL is resolved in env.py: 1) explicit `-x url=` 2) DATABASE_URL env」
     alembic.ini:5  `sqlalchemy.url = postgresql+psycopg://uap:uap@localhost:5432/uap`（**硬编码**）
C-3  config/settings.py:57  `DATABASE_URL: str = Field(default="postgresql+psycopg://uap:uap@localhost:5432/uap")`
     ⇒ **runtime 与 migration 读取同一个变量名**
C-4  tests/conftest.py:21  `os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://uap:uap@localhost:5432/uap_test")`
     ⇒ 测试进程默认使**迁移与 runtime 同时**指向 `uap` 角色 + `uap_test` 库
C-5  tests/integration/alembic_testkit.py:21  `BASE_DSN` = `…//uap:uap@localhost:5432/uap_b1_test`
     `:22` `_ADMIN_DSN` = `…//uap:uap@localhost:5432/postgres`（**同角色**）
C-6  infrastructure/database/config.py:37 / session.py:29 —— runtime 单一引擎以 `settings.DATABASE_URL` 构建
C-7  .env.example —— `DATABASE_URL=`（**空值**）；**无** migration / runtime 分离键

⇒ **耦合事实**：当前 **一个环境变量同时决定迁移身份与运行时身份**，且 env 会**覆盖** `alembic.ini` 的硬编码值。
   任何角色分离若不同时处理 `C-1` 的解析链，迁移将跟随 runtime 身份（反之亦然）。
```

---

## 6. 测试连带基线（**只读**）

```text
T-1  引用 `0015_p12_indexes` 的测试文件 = **17 个**（任何新 revision 落地后须逐项对账）
T-2  链长硬断言：`tests/integration/test_ai_gateway_schema.py:1009` → `assert len(revisions) == 15`
T-3  heads 硬断言：`test_agent_tool_permission_schema.py:330` → `get_heads() == ["0015_p12_indexes"]`
                    `test_p10_event_audit_schema.py:684` → `get_heads() == [HEAD_REVISION]`（该套件策略 = 跟随 head）
                    `test_p12_indexes.py:108` → `get_heads() == [REVISION]`
T-4  `HEAD_REVISION` 常量：`test_ai_gateway_schema.py:70` · `test_p10_event_audit_schema.py:60`
T-5  负向守卫（`TEST vs DECISION` 面 · 对应 `D-OP101-14`）：
       `tests/architecture/test_p10_event_audit_boundary.py:225`（语料 = 0013 源码 · file-scoped）
       `tests/integration/test_p10_event_audit_schema.py:599-604` `test_sec2_migration_performs_no_grant`（语料 = 0013 源码）
       `tests/integration/test_p10_event_audit_schema.py:18`（docstring rationale）
T-6  测试基建（对应 `D-OP101-11`）：`alembic_testkit.py:34-40`
       `reset_test_database()` = `DROP DATABASE IF EXISTS "uap_b1_test" WITH (FORCE)` + `CREATE DATABASE "uap_b1_test"`
       ⇒ **不触碰角色**（集群级角色在重建库后仍然存在）
T-7  全量回归历史基线：**636 passed / 0 failed / 6 skipped**（542 → 596 → 623 → 636；本 PREP 轮**未执行**回归）
```

---

## 7. 本轮边界与自证偏差

```text
本轮变更（全部新增 `.md`，位于 `docs/architecture/`）：
  OPEN_P10_1_IMPLEMENTATION_PREP_BASELINE_REPORT.md（本文件）
  OPEN_P10_1_IMPLEMENTATION_CONTRACT.md
  OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md
非文档变更 = 0（migration = 0 · code = 0 · test = 0 · config = 0 · runtime = 0）
```

**自证偏差（逐条 · 如实披露）**

```text
① 数据库取数全部为 `SELECT` 类只读查询（`pg_roles` / `pg_class` / `pg_proc` / `pg_trigger` / `pg_auth_members` /
   `pg_namespace` / `information_schema`）；**未执行**任何 INSERT/UPDATE/DELETE（DML = 0）。
② 未执行 `CREATE ROLE` / `GRANT` / `REVOKE` / `ALTER ROLE` / `ALTER OWNER` / `CREATE|ALTER|DROP FUNCTION`；
   未执行 `alembic upgrade` / `alembic downgrade`（`alembic heads` 为只读命令）。
③ `uap`（formal）库实测 0 表 ⇒ schema 级实测在 `uap_b1_test` 完成；`uap_test` 仅 2 表。
④ `alembic current` 未执行（需连接库且非本 PREP 必需）⇒ 以 `alembic heads` + 各库 `alembic_version` 实测代替。
⑤ 命名差异（§4.1）：Human 引用的 `OPEN_P10_1_DECISION_RECORD.md` 实为 `OPEN_P10_1_HUMAN_DECISION_RECORD.md`
   —— 以实际文件为准，**未重命名、未新建同义文件**。
```

---

**END OF OPEN-P10-1 IMPLEMENTATION PREP BASELINE REPORT（Phase 0 · 2026-09-27 · **READ-ONLY · NOT FROZEN** · `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED`）**
