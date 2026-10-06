# UAP — OPEN-P10-1 BATCH-A EXECUTION AUTHORIZATION REQUEST

> ## 状态（文件抬头）
>
> ```text
> 轮次      = OPEN-P10-1 BATCH-A EXECUTION START AUTHORIZATION PREP
> 文件性质  = **REQUEST**（请求 · 未授权 · 未实施）
> 目标      = 把 BATCH-A 的**开工授权**摆到 Human 面前；**不自行开工**
> 章节范围  = **仅 §1…§6**（依指令）
>
> 本轮未做  = 无任何 mutation（`CREATE ROLE` / `GRANT` / `REVOKE` / `ALTER OWNER` / `CREATE migration` /
>             `alembic upgrade|downgrade` / `C2 修改` / runtime·config·test 修改 / `commit` / `tag` / `push` 全为 0）
> 本轮已完成 = docs/architecture/OPEN_P10_1_BATCH_A_EXECUTION_AUTHORIZATION_REQUEST.md（新增 · 本文件）
>              docs/architecture/OPEN_P10_1_BATCH_A_HUMAN_DECISION_BLOCK.md（新增 · 全部空槽）
>
> 自证缺陷  = 真实缺口 **0** · 脚本缺陷 **3 项**（Gate harness v1→v3：① markdown 加粗把 `不得继续下一 batch`
>             拆成 `**不得**继续下一 batch` ⇒ 字面断言假阴；② 零计数行 `CREATE ROLE = 0 · GRANT = 0`
>             合法**命名** DDL 动词却被判为可执行 ⇒ 假阳；③ 描述性语句中被反引号引用的动词
>             （`` `REVOKE <role> FROM <role>` ``）同被误判 ⇒ 假阳。
>             修正后判定改为「按行剥离**行内**代码跨度（`` `[^`\n]*` ``，不跨行）+ 去加粗 + 零计数排除 +
>             **要求行首**为 DDL 动词」，并**改文档措辞**（而非削弱断言）使语义可机读。）
> Gate      = 70 / 70 PASS（exit 0）
> ```

---

## §1 状态声明

```text
BATCH-A REQUEST ≠ AUTHORIZATION
    本文件是一份**请求**。它列举范围、对象、前置、风险与停止条件，
    但**不构成**任何开工许可。Human 未在 `OPEN_P10_1_BATCH_A_HUMAN_DECISION_BLOCK.md` 中
    明确填写 `BATCH-A START AUTHORIZATION = AUTHORIZED` 之前，BATCH-A **不得开始**。

AUTHORIZATION ≠ EXECUTION COMPLETE
    即使授权到位，`BATCH-A START AUTHORIZATION = AUTHORIZED` 也只表示"允许开始"，
    **不表示** BATCH-A 已完成、**不表示** 任何验收项已通过。
    完成与否只由 §6 Stop Gate 的逐项证据决定；任何一步失败即 **STOP**。

本请求 ≠ 解除 `<专项 Gate>`
    `CC-7 Implementation Gate` 的 `G-CC7-1`（隔离已成立）/ `G-CC7-2`（开工授权）
    在 BATCH-A 内**不会**因此请求而解除；C2 相关项不在 BATCH-A 范围内。

as-of 基线（本轮实测 · 用于判定请求是否过期）
    HEAD        = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e
    branch      = main · tags = 8 · remote = none · dirty = 79
    heads       = 0015_p12_indexes（单头）· alembic_version = 0015_p12_indexes
    0016 / 0017 = ABSENT / ABSENT
    PDL sha256  = a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56
    0007 sha256 = 9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef
    C2 md5(pg_get_functiondef) = 6867874166ae36966763c1026ab2af19
    ⇒ **若答复时上述任一锚点已变，本请求失效，须重新签发。**
```

---

## §2 执行范围

### §2.1 纳入（**仅此四项**）

```text
BATCH-A:
  ① Role creation
  ② Role membership
  ③ Ownership transfer
  ④ Grant boundary preparation
```

| # | 项 | 本轮请求覆盖的含义 |
|---|---|---|
| ① | **Role creation** | 预置受信角色（创建者 = deployment / orchestration / operations 身份，`D-OP101-04`）；**不由迁移、不由 runtime 创建**；幂等且属性校验 |
| ② | **Role membership** | 建立**最小** membership；并证明 runtime **无法** `SET ROLE` 到 migration / owner trust context（`INV-02`） |
| ③ | **Ownership transfer** | 既有 **178** 对象 owner 全量转移（`D-OP101-09`）；**不得**静默形成混合所有权；任一对象无法转移即 **STOP** |
| ④ | **Grant boundary preparation** | 为 runtime GRANT 边界**做准备**（逐表动词矩阵的核定口径 + 库范围的锁定）；**边界本身**（`D-OP101-07/08` 的 `GRANT` 落地）是否含在本批内 ⇒ 见 §2.3 `CF-BA-1` |

### §2.2 **不包含**（明确排除）

```text
不包含：
  · BATCH-B config separation
  · BATCH-C migration execution
  · BATCH-D validation
```

| 排除项 | 含义 |
|---|---|
| **BATCH-B config separation** | `env.py` 解析链显式化 / `alembic.ini` / `.env.example` / compose / 双 DSN 键（`UAP_MIGRATION_DATABASE_URL`）⇒ **不在本批** |
| **BATCH-C migration execution** | `0016_open_p10_1_trust_boundary` 的创建、`alembic upgrade|downgrade`、C2 函数体改写 ⇒ **不在本批** |
| **BATCH-D validation** | 全量验收 / downgrade / re-upgrade / 回归 ⇒ **不在本批** |

### §2.3 范围冲突登记（**须 Human 确认 · 不阻断本请求的签发**）

```text
`CF-BA-1` 批次构成差异
  本次指令的批次构成：
      BATCH-A = Role creation / Role membership / Ownership transfer / Grant boundary preparation
      BATCH-B = config separation · BATCH-C = migration execution · BATCH-D = validation
  更早的 `REQ-5-CUSTOM`（2026-09-27 IMPLEMENTATION AUTHORIZATION）的批次构成：
      BATCH-A = Role / ownership / grant / **configuration** foundation
      BATCH-B = C2 CC-7 rewrite · BATCH-C = Test infrastructure + security proof · BATCH-D = Full acceptance
  ⇒ 两处对 BATCH-A / BATCH-B 的**构成**不一致（尤其：`config separation` 在旧口径属 BATCH-A，在新口径属 BATCH-B；
     `C2 改写` 在旧口径属 BATCH-B，在新口径归入 BATCH-C）。
  ⇒ 处置：**以本次指令为准**（最近指令优先），并把差异**显式登记**；
     Contract / Matrix 的批次引用同步须采用**新口径**。请 Human 在 Decision Block 中确认。
```

### §2.4 本请求**不授权**的面（与 §2.1 / §2.2 互补）

```text
即使 §3 的开工授权被答复为 `AUTHORIZED`，本请求**均不授权**：
  0016 migration 创建 · `alembic upgrade|downgrade` · C2 函数体修改 · `0007` 修改 ·
  `env.py` / `alembic.ini` / `.env.example` / compose 修改（BATCH-B）·
  `tests/**` 修改（BATCH-C/D）· 正式库 `uap` 的任何迁移 · 任何库的 GRANT 落地（若 `CF-BA-2` 未定）·
  `commit` · `tag` · `push`
```

---

## §3 执行对象清单

### §3.1 角色

```text
Role: uap_migrator
```

| 属性（目标态） | 值 |
|---|---|
| `SUPERUSER` | `false`（`D-OP101-02`） |
| `CREATEDB` / `CREATEROLE` / `REPLICATION` / `BYPASSRLS` | 全 `false` |
| `LOGIN` | 承载独立 migration DSN ⇒ 需要（键名 `UAP_MIGRATION_DATABASE_URL`，`OI-B-4`） |
| 与 runtime 的关系 | **严格非成员**（`INV-01` / `INV-02`） |
| 创建者 | deployment / orchestration / operations 身份（`D-OP101-04`） |

> ```text
> `CF-BA-2` 角色集合差异（须 Human 确认）
>   `D-OP101-01`（FROZEN）冻结的拓扑 `RM-D` = **三个角色**：`uap_seed` / `uap_migrator` / `uap_app`。
>   本次 §3 仅登记 **`uap_migrator`** 一个角色。
>   ⇒ 两种读法并存，**不由 Bot 选择**：
>      (a) BATCH-A 只创建 `uap_migrator`；`uap_seed` / `uap_app` 由**后续批次**创建；
>      (b) BATCH-A 创建 `RM-D` 全部三角色，§3 只把「与所有权转移直接相关」的 `uap_migrator` 列为主对象。
>   ⇒ 影响：`uap_app` 不存在时，`D-OP101-07/08` 的 runtime `GRANT` 无受体；
>      `uap_seed` 不存在时，`D-OP101-01` 的三角色拓扑在 BATCH-A 后**尚未落地**（`D-OP101-13` 判据不可达）。
>   ⇒ 请在 Decision Block 中裁定 (a) / (b)。
> ```

### §3.2 所有权目标

```text
Ownership target: 178 objects
```

| 类别 | `relkind` | 数量 | 现 owner | 目标 owner |
|---|---|---|---|---|
| 分区父表 | `p` | 3 | `uap` | `uap_migrator` |
| 普通表 + 当月子分区 | `r` | 32 | `uap` | `uap_migrator` |
| 普通索引 + 约束索引 | `i` | 108 | `uap` | 随所属表 |
| 分区索引 | `I` | 13 | `uap` | 随所属表 |
| **`pg_class` 小计** | — | **156** | `uap` | — |
| 函数（`pg_proc`，`public`） | — | **22** | `uap` | `uap_migrator` |
| **合计** | — | **178** | — | — |

```text
目标 owner（`OI-B-3 = CONFIRM`）= `uap_migrator`
现状 owner 集合 = {`uap`}（唯一）· 混合所有权现状 = 无
schema `public` owner = `pg_database_owner`（**不在转移面内**）
```

### §3.3 数据库范围

```text
Database scope: uap_b1_test / stage verification flow
正式库 uap: EXCLUDED
```

| 库 | 归属 | BATCH-A 处置 |
|---|---|---|
| `uap_b1_test` | **stage verification flow** | ✅ 范围内的迁移/授权/所有权操作**只在此库** |
| `uap`（正式库） | **EXCLUDED**（`OI-B-2 = A`） | ❌ 不迁移；既有守卫 `test_sec4_formal_database_untouched` **保持不动**（实测 `uap` = **0 表**） |
| `postgres` / `uap_test` | 非本轮目标 | ❌ 不在范围 |

```text
⚠️ 集群级语义（`R-01.1`）：`CREATE ROLE` 是**集群级**对象 ⇒ 角色的"存在性"会天然对全部 4 个库可见，
   这与"库级排除"并不矛盾：**排除的是库内对象/授权面，不是角色存在性**。
⚠️ 集群级影响必须显式登记：`uap` 库虽排除，但 `uap_migrator` 角色**在集群层面出现**。
```

---

## §4 前置条件（`BA-P01` … `BA-P10`）

> 全部为**开工前**必须成立的条件。任一未满足 ⇒ BATCH-A **不得开始**。

### `BA-P01` — Backup evidence（**必需**）

```text
要求：
  ① `uap_b1_test` 的**结构快照**：`pg_dump --schema-only --no-owner`（或等价）导出并留存，
     用于证明「结构在 BATCH-A 前后未变（本批不改结构）」；
  ② **状态清单快照（机读）**：把下列只读查询逐项落盘为 JSON，作为**唯一可复原的基线**：
       · `pg_class.relowner` 全量（156 行）· `pg_proc.proowner` 全量（22 行）
       · `information_schema.role_table_grants`（public 内全量）· `pg_default_acl`（0 行）
       · `pg_namespace.nspacl` / `nspowner`（public）
       · `pg_roles` 非 `pg_%` 全量属性 · `pg_auth_members` 全量
       · `pg_trigger`（`tgparentid=0`）· `pg_proc.prosecdef` · `md5(pg_get_functiondef(…))`（C2）
  ③ 证据路径与 sha256 记录在 BATCH-A 执行日志中。
性质：**只读**；不产生任何 DML/DDL。
```

### `BA-P02` — Rollback evidence（**必需**）

```text
要求：`BA-P01` 的 JSON 基线必须**足以逐条逆向复原**，并在开工前给出**反向操作清单**：
  · 角色：`D-OP101-12` = **保留**集群角色（**不** `DROP ROLE`）⇒ 回滚 = `REVOKE` + 保留；
          若需彻底清除，属环境/运维面（跨库盘点后才可评估）；
  · 所有权：逐条 `ALTER … OWNER TO uap`（反向），对象集合与 `BA-P01` 的 178 行一一对应；
  · 授权：`REVOKE` 本库全部已授出权限（含 schema 级）；
  · membership：反向 `REVOKE <role> FROM <role>`（若本批建立了任何 membership）。
证明义务：回滚清单必须能回答「执行任意前缀后，如何回到 `BA-P01` 基线」。
```

### `BA-P03` — Role creation plan（**必需**）

```text
要求：
  · 创建者身份 = deployment / orchestration / operations（`D-OP101-04`）⇒ **不是** migration、**不是** runtime；
  · **幂等**：已存在则跳过；**属性不一致须显式失败**（不得静默沿用）；
  · 属性集合（目标态）逐项显式：`NOSUPERUSER` · `NOCREATEDB` · `NOCREATEROLE` · `NOREPLICATION` ·
    `NOBYPASSRLS` · `LOGIN`；
  · 口令来源 = 环境注入（**不得**硬编码真实口令入库）；`alembic.ini` / `.env.example` 的实际改动
    **属 BATCH-B（config separation）**，不在本批；
  · 禁止项：迁移内 `CREATE ROLE`（`MIG-04`）· runtime 创建角色 · legacy runner 创建角色。
```

### `BA-P04` — Role membership plan（**必需**）

```text
要求：
  · 最小 membership：本批**预期为空集**（`uap_migrator` 直接拥有对象，无需成员关系）；
    若确需建立（例如运维身份 → `uap_migrator`），须**逐条列出角色对**并给出必要性理由；
  · **强制不变式**：`uap_app`（runtime）**不得**成为 `uap_migrator` 成员；
  · 开工前须记录 `pg_auth_members` 的**用户成员关系基线**（本轮实测 = **0**；
    PG **内建** 3 行 `pg_monitor -> …` 属系统事实，**不计入用户成员关系**）；
  · 完成后须能机读断言：用户成员关系集合 == 计划集合（多一条/少一条即失败）。
```

### `BA-P05` — Ownership transfer order（**必需**）

```text
建议顺序（须在执行日志中逐条留痕）：
  ① 前置断言：当前 owner 集合 == {`uap`}；对象总数 == 178；无混合所有权；
  ② 表（`p` 3 + `r` 32 = 35）逐表 `ALTER TABLE … OWNER TO uap_migrator`
     —— 表 owner 变更会**连带**其索引 / 约束索引 / 分区附件；但**分区子表须单独转移**（否则残留旧 owner）；
  ③ 分区族处理：父表与子表**均须转移**；顺序建议 = 父表先、子表后（或反之），但**必须遍历到零残留**；
  ④ 函数（`pg_proc` 22）逐函数 `ALTER FUNCTION … OWNER TO uap_migrator`；
  ⑤ 收尾断言：**无任何对象仍归 `uap`**（`pg_class` 156 + `pg_proc` 22 全部 == `uap_migrator`）；
     若存在无法转移者 ⇒ **STOP**（不得静默形成混合所有权）。
前置派生（`OI-1` · 已由 `REQ-3-CUSTOM` 裁定为两阶段 bootstrap）：
  执行所有权转移的身份须为 `uap_migrator` 成员、或为受信运维/超级用户身份
  ⇒ **本批采用 Phase A 语义**：由受信运维身份完成转移；Phase B（迁移以 `uap_migrator` 执行）属后续批次。
```

### `BA-P06` — Verification queries（**必需**）

```text
开工前须把下列查询**冻结为验收查询集**（执行后用同一集合复核）：
  V-1 角色集合与属性：`SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolcanlogin FROM pg_roles WHERE rolname NOT LIKE 'pg\_%'`
  V-2 用户成员关系：`pg_auth_members` 中 member/roleid **均非** `pg_%` 的子集（须 == 计划集合）
  V-3 所有权分布：`pg_class.relowner` / `pg_proc.proowner` 按 owner 分组计数（期望 156 / 22 全归 `uap_migrator`）
  V-4 混合所有权检测：`… WHERE pg_get_userbyid(relowner) <> 'uap_migrator'` 计数须 == 0
  V-5 授权面：`information_schema.role_table_grants`（public）· `pg_default_acl` · `pg_namespace.nspacl`
  V-6 runtime 无 DDL：`has_schema_privilege('uap_app','public','CREATE')` == false（若 `uap_app` 在范围内）
  V-7 C2 未变：`md5(pg_get_functiondef(<C2>))` == `6867874166ae36966763c1026ab2af19`
           且 `pg_trigger.tgenabled` == `'O'` · `tgtype` == 31 · `tgparentid` == 0
  V-8 结构未变：`public` 内 `relkind` 分组计数 == p3 / r32 / i108 / I13；`pg_proc` == 22
  V-9 正式库未动：`uap` 库 `information_schema.tables`（非系统）计数 == 0
```

### `BA-P07` — Executor identity（**必需**）

```text
要求：执行身份 = 受信运维/部署身份（本沙箱 = `uap`，集群超级用户）；
      **不得**用 runtime 身份执行任何角色/授权/所有权操作；
      执行身份与 runtime 身份的分离须在日志中留证（`current_user` / `session_user` 逐命令记录）。
⚠️ 已知事实：当前 runtime 与 migration 仍共用同一 `DATABASE_URL`（`R-02` 倒置），
   其**配置面修复属 BATCH-B** ⇒ 本批执行时**必须以显式指定的连接身份**执行，不依赖配置默认值。
```

### `BA-P08` — Database scope lock（**必需**）

```text
要求：
  · 目标库**锁定为 `uap_b1_test`**；执行前 `current_database()` 断言；
  · 正式库 `uap` **EXCLUDED**：开工前与完工后各断言 `uap` 库对象数 == 0；
  · 不得在未指定目标库的情况下向其它库扩散 `GRANT`（`REQ-7-CUSTOM` 第 5 条）；
  · `CREATE ROLE` 属集群级 ⇒ 须在日志中显式声明「角色对 4 库可见」这一**天然集群效应**。
```

### `BA-P09` — Stop Gate（**必需**）

```text
任何一步失败 ⇒ **立即 STOP**：
  · 不得进入下一 batch；
  · 不得自动回滚**其它已验证批次以外**的内容；
  · 不得自行修改任何冻结 Decision；
  · 失败须以 `BATCH-A = BLOCKED` + 失败点 + 证据路径上报。
```

### `BA-P10` — Evidence ledger & un-authorised surfaces（**必需**）

```text
要求：
  · 证据日志落盘至仓库外证据目录（`../uap-stage3-evidence/`），逐项记录命令 / 输出 / 时间戳；
  · 交付物 sha256 记录；
  · **`commit` / `tag` / `push` 仍为 NOT AUTHORIZED**（`REQ-8`），本批完成后停在工作区；
  · 本批**不得**触碰：`0016` migration 创建 · `alembic upgrade|downgrade` · C2 函数体 · `0007` ·
    `env.py` / `alembic.ini` / `.env.example` / compose（属 BATCH-B）· `tests/**`（属 BATCH-C/D）。
```

---

## §5 风险接受

> 授权 BATCH-A 开工 = **知情接受**下列风险。风险编号沿用 `OPEN_P10_1_IMPLEMENTATION_CONTRACT.md` §4。

### `R-01` Role Lifecycle risk（角色生命周期）

```text
R-01.1  `CREATE ROLE` 是**集群级**对象 ⇒ 在任一库创建即对 4 个库（`postgres` / `uap` / `uap_b1_test` / `uap_test`）可见。
        角色**不是**"某库的对象"，不能随库迁移/回滚；角色存在性是**全局副作用**。
R-01.2  角色存在性 = 全局；**GRANT = 每库独立** ⇒ 任何依赖授权的验收**必须逐库落地**（本批仅 `uap_b1_test`）。
R-01.3  `reset_test_database()` = `DROP DATABASE … WITH (FORCE)` + `CREATE DATABASE`，**不触碰角色**
        ⇒ ① 夹具不得假设"干净起点"；② 创建必须**幂等**（PG 无 `CREATE ROLE IF NOT EXISTS`）；
        ③ 禁止在夹具中 `DROP ROLE`（会影响同一集群的其它库）。
R-01.4  `DROP ROLE` 要求该角色**不拥有对象、不持权限**（且无依赖）。
        本批后 `uap_migrator` **拥有 178 对象** ⇒ **不存在** `DROP ROLE` 路径（与 `D-OP101-12` 一致）。
R-01.5  幂等责任方 = 环境引导（创建）+ testkit（预置）；属性不一致须**显式失败**，不得静默沿用。
接受含义：接受"角色一旦创建即在集群内持久存在"这一后果；接受"回滚不消除角色实体"。
```

### `R-04` Existing Ownership risk（既有 178 对象所有权）

```text
R-04.1  现状：`public` 共 **156** `pg_class` 对象 + **22** 函数 = **178**，owner **全部**为 `uap`（唯一 owner）。
R-04.2  裁定 = **full ownership transition**（`D-OP101-09`）⇒ 转移面覆盖：表、分区父/子表、索引、
        约束索引、分区索引、函数。序列 = 0。
R-04.3  目标态**不保留** `uap` 作为对象 owner（`uap` 仅作为集群引导/超级用户身份存在）。
        因故无法转移者**必须显式登记**，不得静默形成"混合所有权"。
R-04.4  转移后的**新建对象**须归 `uap_migrator` ⇒ 与 `D-OP101-10`（连接身份）强耦合；
        其配置面落定属 BATCH-B。
接受含义：接受"178 个对象的所有权被整体改写"这一**面最大**的改动；接受成员资格前提须先满足。
```

### `R-X1` Ownership transfer risk（所有权转移专项风险）

```text
X-1.1  **成员资格前提**：`ALTER … OWNER TO uap_migrator` 要求执行角色为 `uap_migrator` 成员，
       而 `uap_migrator` 为 `NOSUPERUSER` ⇒ 须由受信运维/超级用户身份执行（`REQ-3-CUSTOM` Phase A）。
X-1.2  **静默部分转移**：分区子表、分区索引、约束索引最易残留旧 owner ⇒ 必须以 `V-4` 零残留断言收尾。
X-1.3  **不可逆性感知**：反向转移同样受成员资格前提约束 ⇒ 回滚虽可行，但**不能依赖** runtime 身份完成。
X-1.4  **权限面副作用**：所有权变更会改变"谁能 GRANT/REVOKE"⇒ 与原 owner 相关的既有权限语义随之改变。
接受含义：接受"最坏情形需人工介入反向转移"；接受"转移期间存在暂时的不一致窗口（单事务内闭合为佳）"。
```

### `R-X2` Role lifecycle risk（角色生命周期专项风险）

```text
X-2.1  **集群级泄漏**：本地集群可能出现角色泄漏（测试环境重建库不清理角色）⇒ 跨库互相影响。
X-2.2  **`NOSUPERUSER` 前提的"鸡生蛋"**：创建 `NOSUPERUSER` 角色需要 `CREATEROLE` 或超级用户；
       引导身份必须另行解决，且**不得**与 runtime 或迁移身份复用。
X-2.3  **属性漂移**：角色属性被外部改动而无校验时不易察觉 ⇒ 必须以 `V-1` 逐属性断言。
X-2.4  **口令面**：独立 DSN 需要口令；口令**不得**入库、不得写进日志（脱敏）。
接受含义：接受"角色生命周期由环境承担、不由迁移管理"；接受"属性漂移须靠测试发现"。
```

### 风险汇总

| 编号 | 风险 | 是否可自动回滚 | 主要缓解 |
|---|---|---|---|
| `R-01` | Role lifecycle | 部分（角色按裁定保留） | `BA-P03` 幂等 + `V-1` 属性断言 |
| `R-04` | Existing ownership（178） | 可（反向 `ALTER OWNER`） | `BA-P01` 基线 + `BA-P05` 顺序 + `V-4` 零残留 |
| `R-X1` | Ownership transfer | 可（但受成员资格前提约束） | `BA-P02` 反向清单 + `BA-P07` 执行身份 |
| `R-X2` | Role lifecycle（专项） | 部分 | `BA-P04` membership 基线 + `BA-P08` 范围锁定 |

---

## §6 Stop Gate

```text
任何一步失败 ⇒ STOP

  · **不得**继续下一 batch（BATCH-B / C / D 均不得自动开始）；
  · **不得**自动回滚"其它已验证批次以外"的内容；
  · **不得**自行修改任何冻结 Decision（含 `D-OP101-01…14` / `D-P13-15` / `D-P10-13`）；
  · 必须以 `BATCH-A = BLOCKED` + 失败点 + 证据路径**立即上报**，等待 Human 指令。

BATCH-A 完成判定（全部满足才算完成，缺一即为 BLOCKED）：
  ☐ `BA-P01` / `BA-P02` 证据齐备（backup + rollback）
  ☐ `BA-P03` 角色创建幂等且属性逐项一致
  ☐ `BA-P04` membership == 计划集合，且 runtime 非 `uap_migrator` 成员
  ☐ `BA-P05` 178 对象所有权转移完成，且 `V-4` 零残留（无混合所有权）
  ☐ `BA-P06` 验收查询集全部通过（`V-1`…`V-9`）
  ☐ `BA-P07` 执行身份留证，runtime 身份未参与任何角色/授权/所有权操作
  ☐ `BA-P08` 范围锁定生效；正式库 `uap` 仍为 0 表
  ☐ `BA-P10` 证据日志落盘；`commit` / `tag` / `push` 仍为 0
  ☐ **未**触碰 `0016` migration / `alembic upgrade|downgrade` / C2 / `0007` / config 面 / `tests/**`

暂停点（**预期**在 BATCH-A 完成后出现）：
  完成后**停在工作区**，输出 `BATCH-A = PASSED / BLOCKED` 与六张矩阵（role / membership / ownership /
  grant / DSN resolution / identity proof），然后**等待** Human 的 BATCH-B 授权。
```

**END OF OPEN-P10-1 BATCH-A EXECUTION AUTHORIZATION REQUEST（2026-09-27 · REQUEST · 未授权 · 未实施 · `BATCH-A = NOT STARTED`）**
