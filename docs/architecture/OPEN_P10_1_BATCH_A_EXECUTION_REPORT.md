# UAP — OPEN-P10-1 BATCH-A EXECUTION REPORT

> ## 状态
>
> ```text
> 轮次          = OPEN-P10-1 BATCH-A EXECUTION（IMPLEMENTATION MODE = BATCHED / STOP-GATED）
> 授权          = BATCH-A START = AUTHORIZED（CF-BA-1 = NEW · CF-BA-2 = B）
>
> BATCH-A                     = **PASSED**
> Role topology               = **PASS**
> Role membership             = **PASS**
> Ownership transfer          = **PASS**
> Grant boundary              = **PASS**
> Security verification       = **PASS**
>
> BATCH-B / C / D             = **NOT AUTHORIZED / NOT STARTED**
> OPEN-P10-1 IMPLEMENTATION    = BATCH-A 完成；BATCH-B 起未开始
> 数据库范围                    = `uap_b1_test` only（正式库 `uap` = **EXCLUDED**，保持 0 表）
> 执行身份                      = `uap`（deployment / orchestration / operations authority · `D-OP101-04`）
> ```
>
> **本批未做**：`0016` migration 创建 · `alembic upgrade|downgrade` · C2 修改（`CREATE OR REPLACE FUNCTION` /
> `ALTER FUNCTION` / `DISABLE TRIGGER` / trigger state change / `session_replication_role`）· `0007` 修改 ·
> `env.py` / `settings.py` / `alembic.ini` / `.env.example` / `docker-compose.yml` 修改 · `tests/**` 修改 ·
> runtime 连接切换 · 正式库 `uap` 的任何变更 · `commit` / `tag` / `push`。

---

## §1 as-of baseline（开工前实测 · 与本批所有锚点比对）

| 维度 | 值 |
|---|---|
| `HEAD` / `branch` | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` / `main` |
| tags / remote | 8 / none |
| migration heads | `0015_p12_indexes`（单头）· 15 个迁移文件 · `0016` / `0017` = ABSENT |
| 活体 `alembic_version` | `0015_p12_indexes` |
| 非 `pg_%` 角色 | 1（仅 `uap`）· `RM-D` 三角色不存在 |
| `pg_auth_members` | 3 行（**全为 PG 内建**）· 用户成员关系 **0** |
| ownership | 156 `pg_class`（`p`3/`r`32/`i`108/`I`13）+ 22 `pg_proc` = **178**，全归 `uap` |
| explicit grants 到非 owner | 0 · `pg_default_acl` = 0 行 |
| `public` ACL | `pg_database_owner=UC | =U`（owner + PUBLIC USAGE） |
| 正式库 `uap` | 0 表 · 无 `alembic_version` |
| 安全锚点 | `0007` sha256 `9e0105b9…` · C2 `md5` `6867874166ae36966763c1026ab2af19` · PDL sha256 `a83fde5c…` |
| 额外实测 | 无 enum / domain 类型；22 个函数 `proacl` 全为 NULL（⇒ PUBLIC 默认 `EXECUTE`）；0 序列 |

**开工前置结论**：无 drift；另发现 **19 个测试文件调用 `reset_test_database()`** ⇒ 本批**不得运行测试套件**
（会重建 `uap_b1_test` 从而抹掉 A-3 的所有权转移结果）⇒ 本批验证**全部为只读查询 + 会话探针**。

---

## §2 逐步执行结果（A-1 … A-5）

### A-1 CREATE / VERIFY ROLES — **PASS**

```text
执行        : 单个幂等 DO 块，创建 uap_seed / uap_migrator / uap_app
授权对象      : LOGIN · NOSUPERUSER · NOCREATEDB · NOCREATEROLE · NOREPLICATION · NOBYPASSRLS
失败关闭      : 已存在但属性不符 ⇒ RAISE EXCEPTION（不静默沿用）
结果        : 3 created（`A1-CREATED` × 3）
幂等证明      : 复跑 ⇒ `A1b-NOOP` × 3（无创建、无错误）
```

| rolname | super | createdb | createrole | replication | bypassrls | login |
|---|---|---|---|---|---|---|
| `uap` | true | true | true | true | true | true |
| `uap_app` | **false** | **false** | **false** | **false** | **false** | true |
| `uap_migrator` | **false** | **false** | **false** | **false** | **false** | true |
| `uap_seed` | **false** | **false** | **false** | **false** | **false** | true |

```text
非 pg_% 角色 = 4（uap + RM-D 三角色）⇒ CF-BA-2 = B 落地
口令          = 本地 dev 约定（角色名），**必须在任何非 dev 环境替换**（见 §6 OI-G-4）
执行者        = current_user = session_user = uap · current_database = uap_b1_test
```

### A-2 ROLE MEMBERSHIP — **PASS**

```text
设计        : 最小 membership = **空集**（`uap_migrator` 直接拥有对象 ⇒ 无需成员关系；
              执行者 `uap` 为超级用户 ⇒ 可完成 ALTER OWNER 而无需成员资格）
执行        : 失败关闭守卫（非空即 RAISE）+ 7 组禁止关系显式否定断言
结果        : `A2-VERIFIED minimal membership = EMPTY SET (0 user-role rows)`
              `A2-VERIFIED no forbidden membership among 7 checked pairs`
```

### A-3 OWNERSHIP TRANSFER — **PASS**

```text
目标        : 178 对象 owner 全量转移 `uap` → `uap_migrator`（`D-OP101-09`）
顺序        : ① 表（p 3 + r 32 = 35，含分区父与子表）② 残留索引 ③ 函数（22）④ 零残留断言
结果        : tables transferred = 35 · residual indexes transferred = **0**（121 个索引随表自动跟随）
              functions transferred = 22
              A3.4 residue: pg_class=0, pg_proc=0, pg_type=0
台账        : 逐对象 `WHO_EXECUTED / KIND / SUBTYPE / OBJECT / OLD_OWNER / NEW_OWNER / WHY_REQUIRED / STATUS`
              178 行 · TRANSFERRED=178 · ALREADY-TARGET=0 · UNEXPECTED=0
              unique OLD_OWNER = {uap} · unique NEW_OWNER = {uap_migrator}
自动跟随（未单列，但已核验零残留）: 121 索引（`i`108 + `I`13）· 35 复合行类型（`typtype=c`）· 35 数组类型（`typtype=b`）
```

```text
WHO EXECUTED = uap（deployment/orchestration/operations authority, `D-OP101-04`）
WHY REQUIRED = `D-OP101-09` full ownership transition to `uap_migrator`
RESULT       = **178 / 178**，**无 mixed ownership**
```

### A-4 RUNTIME GRANT BOUNDARY — **PASS**

```text
授予面（**确定性最小集**）:
  ① GRANT USAGE ON SCHEMA public TO uap_app          （**CREATE 明确不授**，`D-OP101-08`）
  ② GRANT SELECT ON TABLE public.alembic_version     （runtime **当日唯一实际读面** = readiness 模式状态探针）
  ③ GRANT INSERT, SELECT ON TABLE public.audit_logs  （父表 + 当期分区各一行）
      依据逐字：`CORE §13`「审计不可变 | `audit_logs` 仅授予 `INSERT, SELECT`」；
               `D-OP101-07` 决策文本「含 `audit_logs` 的写读动词组合」
结果: 直接授权 **恰好 5 行**，逐行如下：
```

| grantee | object | privilege |
|---|---|---|
| `uap_app` | `public.alembic_version` | `SELECT` |
| `uap_app` | `public.audit_logs` | `INSERT` |
| `uap_app` | `public.audit_logs` | `SELECT` |
| `uap_app` | `public.audit_logs_202609` | `INSERT` |
| `uap_app` | `public.audit_logs_202609` | `SELECT` |

```text
负向断言（12 项全部成立）: 无 schema CREATE · 无 audit_logs UPDATE/DELETE/TRUNCATE ·
  无 users SELECT/INSERT · 无 events/roles/permissions SELECT ·
  非 uap_migrator 成员 · 非 pg_database_owner 成员
交叉核验: `pg_default_acl` = 0 行 · `relacl` 仅出现于上述 3 个关系 · 零 stray grantee
        `uap_app` db-CONNECT = true · db-CREATE = **false**
未做    : **未在本批切换应用连接**（runtime config = BATCH-B）；`uap_app` 当前无功能载荷
```

### A-5 READ-ONLY VERIFICATION — **PASS**

```text
V-1  角色拓扑与属性            PASS  3/3 全部 NOSUPERUSER + LOGIN，无 CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS
V-2  trust-context 分离        PASS  uap_app 既非 migration trust context 亦非 owner trust context
V-3  runtime 无 migration 成员  PASS  用户成员关系行 = 0
V-4  pg_default_acl            PASS  0 行
V-5  pg_class ownership        PASS  156/156 归 uap_migrator · 混合 = 0
V-6  pg_proc ownership         PASS  22/22 归 uap_migrator · 混合 = 0
V-7  pg_type ownership         PASS  复合/数组类型全部随表（0 例外）
V-8  授权面                    PASS  uap_app 直接授权 = 5 · uap_migrator 显式授权 = 0 · uap_seed 授权 = 0
V-9  未触碰边界                PASS  C2 md5 + trigger `31|O|0` 未变 · `prosecdef` = 0 · `alembic_version` = 0015_p12_indexes
```

**会话级身份证明（15 / 15 PASS）**

| 探针 | 结果 |
|---|---|
| `uap_seed` / `uap_migrator` / `uap_app` 各自 `current_user = session_user` | ✅ 三条身份均可登录且互异 |
| `uap_app` → `SET ROLE uap_migrator` | ✅ **`permission denied to set role`** |
| `uap_app` → `SET ROLE uap_seed` | ✅ `permission denied` |
| `uap_app` → `SET ROLE pg_database_owner`（schema owner） | ✅ `permission denied` |
| `uap_app` → `SET SESSION AUTHORIZATION uap_migrator` | ✅ `permission denied to set session authorization` |
| `uap_app` → `CREATE TABLE`（**DDL 负向探针**） | ✅ `permission denied for schema public` |
| `uap_app` → `SELECT users` / `SELECT roles` | ✅ `permission denied for table` |
| `uap_app` → `SELECT audit_logs`（正向） | ✅ 允许（0 行） |
| `uap_app` → `SELECT alembic_version`（正向） | ✅ 允许（`0015_p12_indexes`） |
| `uap_migrator` → `SELECT users`（正向） | ✅ 允许 |
| `uap_seed` → `SELECT users` | ✅ `permission denied` |
| 失败探针残留 | ✅ `batch_a_probe` 表数 = **0** · `public` 对象仍 **156** · 函数仍 **22** |

**边界核验**

| 项 | 实测 |
|---|---|
| `HEAD` / tags / remote | `034ee97c…`（未动）· 8 · none |
| `0007` sha256 / PDL sha256 | `9e0105b9…` / `a83fde5c…`（均未变） |
| `0016` / `0017` / heads | ABSENT / ABSENT / `0015_p12_indexes`（单头） |
| 正式库 `uap` | 非系统表 **0** · 无 `alembic_version` · `public` 对象 **0** ⇒ **EXCLUDED 严格遵守** |
| 集群级角色可见性 | 4 个库（`uap` / `uap_b1_test` / `uap_test` / `postgres`）均可见 `uap_app,uap_migrator,uap_seed` ⇒ **预期行为** |
| `GRANT`/所有权是否扩散 | `uap` / `uap_test` / `postgres` 中对三新角色的授权 = **0** ⇒ **未扩散** |

---

## §3 五张矩阵

**① Role matrix**

| role | super | createdb | createrole | replication | bypassrls | login | 目标职责 |
|---|---|---|---|---|---|---|---|
| `uap_seed` | F | F | F | F | F | T | 受信 seed / registry bootstrap context（本阶段**零权限**） |
| `uap_migrator` | F | F | F | F | F | T | migration identity · 178 对象 owner |
| `uap_app` | F | F | F | F | F | T | runtime application identity · 5 项直接授权 |

**② Membership matrix**

| member → role | 结果 |
|---|---|
| `uap_app` → `uap_migrator` / `uap_seed` / `uap` / `pg_database_owner` | **全部 false** |
| `uap_migrator` → `uap_app` · `uap_seed` → `uap_app` | **false** |
| 用户角色成员关系总行数 | **0**（PG 内建 3 行不计入） |

**③ Ownership inventory**

| 类 | 数量 | owner | 混合 |
|---|---|---|---|
| `pg_class`（`p`3 + `r`32 + `i`108 + `I`13） | 156 | `uap_migrator` | 0 |
| `pg_proc` | 22 | `uap_migrator` | 0 |
| `pg_type`（`c`35 + `b`35） | 70 | `uap_migrator`（随表） | 0 |
| **显式转移目标** | **178** | — | **0** |

**④ Grant matrix（`uap_app` 直接授权）**

| 对象 | 动词 | 依据 |
|---|---|---|
| `SCHEMA public` | `USAGE`（无 `CREATE`） | 引用对象之必要；`D-OP101-08` |
| `alembic_version` | `SELECT` | readiness 探针读面 |
| `audit_logs` / `audit_logs_202609` | `INSERT`, `SELECT` | `CORE §13` · `D-OP101-07` |
| 其余 34 张表 | **无** | 逐表矩阵需 runtime 实际读写面（不存在）⇒ `OI-G-1` |

**⑤ Identity proof matrix**

| 命题 | 证据 | 结论 |
|---|---|---|
| `uap_migrator` = NOSUPERUSER | `pg_roles` + A-1 | ✅ |
| `uap_app` = NOSUPERUSER | `pg_roles` + A-1 | ✅ |
| `uap_seed` = 非超级用户 | `pg_roles` + A-1 | ✅ |
| `uap_app` ≠ migration trust context | `pg_auth_members` = ∅ + `SET ROLE` 被拒 | ✅ |
| `uap_app` ≠ owner trust context | 非 `pg_database_owner` 成员 + `SET ROLE` 被拒 | ✅ |
| runtime 无 migration membership | `pg_auth_members` 用户行 = 0 | ✅ |
| migration role 无不必要的 runtime privilege | 显式授权 = 0（owner 隐含行已排除） | ✅ |
| runtime 无 DDL | `has_schema_privilege(CREATE)` = false + DDL 探针被拒 | ✅ |

---

## §4 Mandatory Security Verification（对照 Human 清单逐条）

```text
☑ uap_migrator = NOSUPERUSER                         → A-1 + V-1
☑ uap_app      = NOSUPERUSER                         → A-1 + V-1
☑ uap_seed     = 非超级用户                           → A-1 + V-1
☑ uap_app ≠ migration trust context                  → V-2 + `SET ROLE uap_migrator` 被拒
☑ uap_app ≠ owner trust context                      → V-2 + `SET ROLE pg_database_owner` 被拒
☑ runtime 无 migration membership                     → V-3（用户行 = 0）
☑ migration role 无不必要的 runtime privilege         → V-8（显式授权 = 0）
☑ 核验 pg_auth_members                                → V-2/V-3
☑ 核验 pg_roles                                       → V-1
☑ 核验 pg_default_acl                                 → V-4（0 行）
☑ 核验 pg_class ownership                             → V-5（156/156）
☑ 核验 pg_proc ownership                              → V-6（22/22）
☑ 核验 information_schema.role_table_grants           → V-8（5 行，精确集合）
```

---

## §5 未越界确认（逐项为 0）

```text
0016 migration 创建 = 0            alembic upgrade = 0            alembic downgrade = 0
CREATE OR REPLACE FUNCTION = 0     ALTER FUNCTION = 0            DISABLE TRIGGER = 0
trigger state change = 0           session_replication_role = 0   C2 modification = 0
0007 modification = 0              env.py = 0 · settings.py = 0 · alembic.ini = 0
.env.example = 0 · docker-compose.yml = 0                          tests/** 修改 = 0
runtime cutover = 0                final regression = 0           正式库 uap 变更 = 0
BATCH-B / C / D 任何动作 = 0        commit = 0 · tag = 0 · push = 0
```

> **注**：本批**未**修改任何仓库文件（唯一新增为 `docs/architecture/` 下本报告）；
> 证据全部落盘于**仓库外**目录 `../uap-stage3-evidence/batch_a/`（见 §8 manifest）。
> 另：`ALTER DEFAULT PRIVILEGES` **未使用**（不在授权动词清单内）⇒ 见 `OI-G-2`。

---

## §6 待决项（**登记 · 非冲突 · 不阻断 BATCH-A 判定**）

```text
为遵守「发现冻结决策 / 实施契约 / 实际 DB 状态之间出现新冲突 ⇒ HARD STOP」这一指令，
下列各项均已逐条比对，结论：**均非「冲突」**，而是 BATCH-A 之后自然出现的**前置与边界登记**。
```

| 编号 | 事项 | 依据与判定 |
|---|---|---|
| `OI-G-1` | **runtime 逐表 DML 矩阵不可核定**：除 `audit_logs`（冻结设计明示）与 `alembic_version`（当日读面）外，其余 34 张表的动词组合需要「runtime 实际读写面」，而 runtime 业务实现尚不存在 ⇒ **未授权任何 DML**（不得以扩权替代最小集） | `D-OP101-07`；**非冲突**（该决策要求"最小集"，在面不存在时最小集 = 已授部分） |
| `OI-G-2` | **未来分区不继承授权**：`audit_logs` 家族按分区逐月新增，而 `GRANT` 只落在"当前存在"的关系上；本批**未使用** `ALTER DEFAULT PRIVILEGES`（不在授权动词清单内）⇒ 后续月份分区**不会**自动获得 `uap_app` 的 `INSERT/SELECT`。修复机制（default privileges / 分区创建时补授）**需新决策** | `D-OP101-07`；**非冲突**（属机制选择） |
| `OI-G-3` | **`uap_migrator` 不具 schema `CREATE`**：实测 `uap_migrator` → `CREATE TABLE` 被拒（`permission denied for schema public`）。⇒ BATCH-C 创建 `0016` 前**必须先补齐** `GRANT CREATE ON SCHEMA public TO uap_migrator`（或等价） | `D-OP101-02` 的「仅持 seed / DDL 所需的最小权限」是**上限约束**（least privilege），**不**要求此刻即持有全部 DDL 权限 ⇒ **非冲突**，属 **BATCH-C 前置**。⚠️ 若 Human 采「下限」读法（即认为该决策要求此刻必须授予），请明示 —— 那将是 BATCH-A 的**范围增补**，须另行授权 |
| `OI-G-4` | **角色口令为本地 dev 约定**（等于角色名，与既有 `uap:uap` 同性质）：**必须在任何非 dev 环境替换**，且不得写入日志 | 安全基线；**非冲突** |
| `OI-G-5` | **`uap_seed` 零权限**：按 `CF-BA-2 = B` 已建立该角色，但按 `OI-B-1 = A` 其**不进入** C2 受信集合 ⇒ 本阶段**无任何授权、无 C2 权限**。其 registry-seed 权限面属未来决策 | `D-OP101-01` + `OI-B-1 = A`；**非冲突**（`uap_seed` 的存在性与授权面是两件事） |
| `OI-G-6` | **PUBLIC 默认 `EXECUTE`**：22 个函数的 `proacl` 全为 NULL ⇒ PUBLIC（含 `uap_app`）对全部函数具 `EXECUTE`。本批**未回收**（回收会改变既有默认语义，且 `uap_uuid_v7()` 作为列默认值被引用） | **非冲突**，属**已登记残余面** |
| `OI-G-7` | **所有权转移是"当前库状态"属性**：`reset_test_database()` 会 `DROP/CREATE DATABASE`，新库对象 owner 取决于**建对象的角色** ⇒ 该转移结果**不随库重建而保留**；测试期行为属 BATCH-C/D 面 | `R-01.3`；**非冲突** |
| `OI-G-8` | **集群级可见性**：三个新角色在 `uap` / `uap_test` / `postgres` 中同样可见（PG 集群语义）；但**未授予任何权限、未改任何所有权**（实测 = 0） | Human 已明示为预期行为；**非冲突** |

```text
⇒ 本批**未触发 HARD STOP**：无任何「冻结决策 vs 实现契约 vs 实际 DB 状态」的实质性矛盾。
⇒ 上述 8 项均**未自行处置**，留待 Human 裁定；BATCH-A 的判定不依赖它们。
```

---

## §7 自证缺陷（如实披露 · 真实缺口 **0** · 脚本缺陷 **7 项**）

```text
真实缺口 = 0（所有步骤的最终 DB 效果与设计完全一致；失败处均为脚本层并已失败关闭，无部分生效的残留）
```

| # | 缺陷 | 类型 | 处置 |
|---|---|---|---|
| ① | `RAISE NOTICE` 裸用于 SQL 层（须在 `DO` 块内）⇒ A-4 首次执行**中途中止**（`GRANT USAGE` 已生效，其后未执行） | 脚本 | 改为 DO 块包裹；A-4 幂等重跑补齐 |
| ② | `string_agg(DISTINCT x, ', ' ORDER BY 1)` 在 PG 中非法（DISTINCT 聚合的 ORDER BY 表达式须在参数表内）⇒ A-4.4 中止 | 脚本 | 改为子查询 + 外层 `string_agg` |
| ③ | A-4.4 期望常数写错（写 6，实为 **5**）⇒ 假 FAIL。7 项直接授权的算术：1 + 2 + 2 = 5 | 脚本 | 修正为 5 |
| ④ | `text \|\| "char"`（`c.relkind`）类型歧义 ⇒ A-5 中止（**既有教训 25 复发**） | 脚本 | 改 `c.relkind::text` |
| ⑤ | **裁定点**：`information_schema.role_table_grants` **会为对象 owner 合成行**（35 表 × 4 DML = **140** 行）⇒ 「`uap_migrator` 持有 140 项 runtime DML 授权」为**假阳**。这些是**所有权隐含权限**，非授权 | 脚本 + 判定口径 | 改为**排除 owner** 后判定（显式授权 = 0），另加 `relacl` 与 `aclexplode` 两条独立交叉核验 |
| ⑥ | 「`public` 内 `relacl` 全为 NULL」断言错误 —— `GRANT` 本身**会**创建 `relacl`（实测 3 个关系带 ACL，内容恰为 A-4 的授权）；且显式授权查询漏了 `table_schema='public'` 过滤（误计 191 行系统 schema 的 PUBLIC 授权） | 脚本 | 改为「除 3 个 A-4 目标外无 `relacl`」+「无 stray grantee」+「`public` 内显式非 owner 授权 = 5」 |
| ⑦ | 会话探针脚本把 psql **SQL 错误的退出码**写成 3（实为 **1**；3 用于 `-f` 脚本错误）⇒ 7 项假 FAIL（**12 项语义结果当时即全部正确**） | 脚本 | 期望值改为 1；重跑 15/15 PASS |

```text
另：A-4 首次中止后**未静默继续** —— 立即以幂等方式完整重跑并留下两次执行日志；
    最终授权集合经三条独立核验（information_schema / relacl / aclexplode）一致。
    本批**未在失败状态下推进任何后续步骤**。
```

---

## §8 Evidence manifest

落盘位置：`../uap-stage3-evidence/batch_a/`（**仓库外**）

| 文件 | bytes | sha256（前 16） |
|---|---|---|
| `MANIFEST.txt` | 2089 | `f3e5829821d524e7` |
| `A1_executor_identity.log` | 182 | `2196dd82bd5a4e5e` |
| `A1_create_roles.log` | 96 | `692c40473ebd3dd9` |
| `A1_post_verify.log` | 671 | `d3441874a6884af9` |
| `A1b_idempotency.log` | 277 | `4c67efcc76816a3a` |
| `A2_membership.log` | 567 | `8b2da833b2d8b74c` |
| `A3_ledger_pre.tsv` | 8017 | `b322b901bb196d5a` |
| `A3_transfer.log` | 320 | `ad7020069ea5716f` |
| `A3_ledger_post.tsv` | 8082 | `1cabecd828511128` |
| `A3_who_what_old_new_why.tsv` | 27913 | `12d66a65b0f5f310` |
| `A4_runtime_grant_boundary.sql` | 4948 | `1fad0d3f62395ab8` |
| `A4_grants.log` | 1772 | `cd6a6cb9b809ed14` |
| `A5_readonly_verification.sql` | 10108 | `cf2942833a5f2a30` |
| `A5_verification.log` | 3240 | `d04e46c375fb3ba8` |
| `A5_session_probes.log` | 2026 | `521efae1e3f88e7c` |
| `A5_boundaries.log` | 1147 | `d1a94131b379656a` |
| `GATE_batch_a.log`（独立复算 · 69/69 PASS） | 3660 | `ef26453661a0b82b` |

**独立复算 Gate**：`GATE_batch_a.log` —— 对上述全部结果**从零重新推导**（69 项断言，一次通过）：

```text
A 组 角色拓扑 2 · B 组 成员关系 6 · C 组 所有权 5 · D 组 授权边界 7
E 组 安全面 8 · F 组 边界 11 · G 组 报告 17 · H 组 轮次范围 3
⇒ checks=69 passed=69 failed=0（exit 0）
该 Gate **不重置数据库**（19 个测试文件会 reset，故本批禁止跑测试套件）
```

**可复现工件**：`A4_runtime_grant_boundary.sql`（幂等 · 失败关闭）与 `A5_readonly_verification.sql`（纯只读 · 失败关闭）
可作为本批结果的**独立复算**入口。

---

## §9 FINAL GATE

```text
BATCH-A = **PASSED**

Role topology         = **PASS**
Role membership       = **PASS**
Ownership transfer    = **PASS**
Grant boundary        = **PASS**
Security verification = **PASS**

A-1 CREATE/VERIFY ROLES  = PASS（3 created · 幂等复跑 3/3 NOOP）
A-2 ROLE MEMBERSHIP      = PASS（membership = 空集 · 7 组禁止关系否定断言成立）
A-3 OWNERSHIP TRANSFER   = PASS（178/178 · 无混合所有权 · 零残留）
A-4 RUNTIME GRANT BOUNDARY = PASS（5 项直接授权 · 12 项负向断言 · 0 stray grantee）
A-5 READ-ONLY VERIFICATION = PASS（V-1…V-9 + 会话探针 15/15 + 边界核验）

数据库范围 = uap_b1_test only（正式库 uap 保持 0 表 · EXCLUDED 严格遵守）
0016 = ABSENT · 0017 = ABSENT · alembic heads = 0015_p12_indexes（单头）
C2 = UNCHANGED（md5 + trigger 31|O|0）· 0007 = UNCHANGED · PDL = UNCHANGED
runtime cutover = NOT PERFORMED · config separation = NOT PERFORMED（BATCH-B）

待决项 = OI-G-1 … OI-G-8（登记 · 非冲突 · 不阻断本判定）
自证缺陷 = 真实缺口 0 · 脚本缺陷 7（全部失败关闭并已修复/重跑）

BATCH-B = NOT AUTHORIZED
BATCH-C = NOT AUTHORIZED
BATCH-D = NOT AUTHORIZED
commit = 0 · tag = 0 · push = 0

⇒ **STOP POINT —— A-1…A-5 完成，立即停止。**
   等待 Human 的 BATCH-B 授权（config separation）或其他指令；不得自动进入下一批。
```

---

**END OF OPEN-P10-1 BATCH-A EXECUTION REPORT（2026-09-27 · `BATCH-A = PASSED` · `0016 = ABSENT` · `commit/tag/push = 0`）**
