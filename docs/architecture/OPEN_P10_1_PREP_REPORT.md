# UAP — OPEN-P10-1 PREP REPORT（Database Trust Boundary Design）

> ## 状态
>
> ```text
> 轮次        = OPEN-P10-1 PREP（STRICT READ-ONLY · 设计阶段）
> 文档状态    = **DRAFT · NOT FROZEN**
> 目的        = 把 `OPEN-P10-1`（显式 DEFERRED 开放项）立项为**可冻结的数据库信任边界设计**
> Gate 结果   = **PREP = READY FOR HUMAN DECISION（OQ-OP101-01…14 待裁）**
> 本轮未做    = 未 CREATE ROLE · 未 GRANT/REVOKE · 未新增/改动 migration · 未创建 0016+ ·
>               未改 0007 / C2 · 未改 code / test / config · 未改 .env / alembic.ini · 未 commit/tag/push
> dependent   = `P13 B-1 Amendment`（挂起）· `P13 IMPLEMENTATION = NOT AUTHORIZED`
> ```
>
> **立项依据（Human 裁定 · 逐字）**
>
> ```text
> 执行顺序 = OPEN-P10-1 Database Trust Boundary Foundation → P13 B-1 Amendment → P13 Implementation
> 目标     = 建立数据库角色分离：至少区分 migration trust context / runtime application context
>            runtime   : registry INSERT = DENY
>            migration : controlled registry seed = ALLOW
> ```
>
> **本文件不做**：不选择机制族（`M-2`/`M-6` + 载体 `M-4` 的选择属 Human 决策）· 不代裁任何 `OQ-OP101-NN` ·
> 不改写任何既有 `D-*` 决策正文 · 不产生任何实施授权（Charter §6）。

**权威来源（本轮原样读取）**：`P13_B1_HUMAN_DECISION_AMENDMENT.md`（§3 `B-1`…`B-7` · §4 `M-1`…`M-7` · §6 · §7 `A-1`…`A-5`）·
`P13_B1_HUMAN_DECISION_FINAL_DIRECTION.md` · `PLATFORM_DECISION_LOG.md`（`D-P10-13` · `D-P11-08` · `D-P13-01…15` + 附录 J/K）·
`CORE_DOMAIN_MODEL.md` §13 · `MIGRATION_STRATEGY.md` §8/§9 · `P13_IMPLEMENTATION_CONTRACT.md` §3 · `STEP1B_SEED_STRATEGY.md`。

---

## 1. Scope 与 OUT 面（**冻结证据逐条引用 · 不自创范围**）

### 1.1 IN（本阶段设计面）

| # | 设计面 | 冻结证据 |
|---|---|---|
| `S-1` | **身份可区分**：migration context 与 runtime context 至少由**不同数据库角色**承载 | Human 裁定 §4（本阶段目标）· Amendment `B-1`（同角色 ⇒ 无边界） |
| `S-2` | **runtime 不可伪造**：runtime 角色不得能取得 migration 权限 | Human 裁定 §5「runtime 可获得 migration 权限」= 禁止 · Amendment `M-2` C 行 |
| `S-3` | **最小权限**：runtime 不持 DDL；受信角色仅持 seed 所需最小权限 | `D-P10-13` 禁止项「不得给应用运行时 DDL 权限」· `CORE` §13 |
| `S-4` | **C2 判据不可伪造**：受信信号只可为服务端身份（role），不得为 GUC / `application_name` / 会话变量 / 临时标志 | Human 裁定 §2 + §5 · Amendment `M-1`（不满足准则） |
| `S-5` | **registry 目标**：runtime registry INSERT = DENY；受信 context 的 controlled registry seed = ALLOW | Human 裁定 §4 · `D-P13-03`（核心目标）· `D-P13-04` |
| `S-6` | **降级完整**：C2 复原 + 角色/GRANT 回收，不留持久例外主体 | Amendment `A-3` · §7 准则「downgrade 后 C2 完整」 |
| `S-7` | **可证性**：八项测试证据链（runtime DENY 逐字一致 · 伪造被拒 · 受信 ALLOW · 复原） | Amendment `A-5` · §7 测试矩阵 |

### 1.2 OUT（本阶段**不**设计 · 需另开 scope）

```text
OUT-1  业务授权模型（RBAC/ABAC/ACL 语义）        —— 属 D-AUTH-*，已冻结，不改
OUT-2  RLS / 行级安全                             —— D-P10-15 明文禁止（无 RLS）
OUT-3  AI Provider / Tool 权限面                  —— 属 P08 / P09 / AI Gateway
OUT-4  P13 seed 的对象集合与顺序                  —— 属 D-P13-01…14，已冻结，不改
OUT-5  C2 函数体的具体改写文本                    —— 属 P13 B-1 Amendment（本阶段**前置**，非本阶段交付）
OUT-6  runtime 应用架构（服务/API/worker 分层）    —— 属 D-PLAT-* / D-AGENT-*
OUT-7  生产备份 / PITR 运维策略                    —— 属 MIGRATION_STRATEGY §10
OUT-8  `uap_readonly` 的完整只读 GRANT 矩阵        —— 本阶段**仅登记为 OQ**（OQ-OP101-06）
```

### 1.3 与既有冻结的关系（**不 supersede 任何决策**）

| 冻结项 | 本阶段关系 |
|---|---|
| `D-PLAT-09`（路线 A：`P10→P11→P12→P13→Runtime`） | **未 supersede · 未改写**；本阶段是 Human 裁定的**前置闸门**，属路线 A 的细化 |
| `D-P10-13` / `OPEN-P10-1` | **本阶段即该 OPEN 项的实现前置设计**；其「禁止不得给应用运行时 DDL 权限」为本阶段硬约束 |
| `D-P11-08`（`SECURITY INVOKER` canonical · 禁 `DEFINER`） | **保持**；本阶段设计**不得**引入 `SECURITY DEFINER` |
| `D-P13-03`（migration-controlled path） | **核心目标保持**；其"受信 path"的**主体定义**待本阶段冻结后形式化 |
| `D-P13-11`（禁 DISABLE / 临时关闭 / 绕过 C2） | **保持**；`CP-1`/`CP-2` 与其一致 |
| `D-P13-15`（B-1 Amendment） | **前置即本阶段**；其 Purpose 的「前提是数据库身份隔离已经成立」由本阶段产出 |

---

## 2. Baseline（只读校验 · 轮次起始）

```text
HEAD              = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e（branch main）
tags              = 8 · remote = none（从未 push）
alembic 单头      = 0015_p12_indexes（`alembic heads` 实测）
versions/         = 15 个 · `001[6-9]*` = **0** ⇒ 0016+ = ABSENT
迁移 sha256        = 0010 6d9907237f80e9da · 0011 cdaf8383630335db · 0012 5ecd1ef30b403fb4
                    0013 da1bdffd4ddd2202 · 0014 3be9c8c092869c8d · 0015 94b0d22800c8971e
PDL sha256（轮前） = b7ff037829a7ef19520cd4dc7937244d80581cff6f11e09bb81541061e8a636f（3061 行 · 219441 bytes）
命名空间（轮前）   = D-PLAT 17 · D-AUTH 25 · D-AGENT 16 · D-P10 18 · D-P11 14 · D-P12 15 · D-P13 14 · supersession = 1
```

**库清点（实测）**

| 库 | public 表（`r`+`p`） | `alembic_version` |
|---|---|---|
| `postgres` | —（仅系统） | — |
| `uap`（formal） | **0** | 表不存在 |
| `uap_b1_test` | **35** | `0015_p12_indexes` |
| `uap_test` | 2 | 表不存在 |

⇒ **schema 级实测基于 `uap_b1_test`（@0015，唯一处于正式链头的库）**。`uap`（formal）为 0 表，与本阶段无关。

---

## 3. Existing Substrate（既有底座 · 实测）

### 3.1 角色与所有权（`OPEN-P10-1` 的**核心缺口**）

```text
E-1  非 `pg_%` 角色 = **仅 `uap`**（1 个）⇒ CORE §13 的三角色模型 **0 落地**
E-2  `uap` 属性：rolsuper = t · rolcreatedb = t · rolcreaterole = t · rolbypassrls = t · rolcanlogin = t
E-3  `public` schema 全部 156 个对象（表/索引/序列/函数）**owner = uap**（唯一 owner）
E-4  `pg_proc`：22 个函数 · owner 全为 `uap` · `prosecdef = 0`（无 SECURITY DEFINER）· `proconfig` 为空（0 个设定 search_path）
E-5  `public` schema：owner = `pg_database_owner`（PG16 默认）· ACL = `pg_database_owner=UC | =U`
     ⇒ **PUBLIC 仅有 USAGE，无 CREATE**（PG16 默认行为，未被人为改动）
E-6  数据库 ACL = `NULL`（默认）⇒ 无数据库级显式授权
E-7  显式 `GRANT` 到非 owner 主体 = **0**（`information_schema.role_table_grants` grantee ∉ {uap, PUBLIC} = NONE）
```

**⇒ 与 `D-P10-13` 的登记完全一致**：角色体系**尚未在任何 migration 中落地**（`CREATE ROLE` / `GRANT` / `REVOKE` 可执行语句 = 0，见 §4.3）。

### 3.2 对象规模（GRANT 矩阵的基数）

```text
表（parent + leaf） = 35     序列 = 0     索引 = 108
触发器（父级 tgparentid=0）= 39     触发器行（含子分区克隆）= 40      子分区表 = 3
函数 = 22     非 public schema = 0（**仅 `public`**）
```

> **`39` 与 `D-P13-11` 的「39 triggers」逐字一致** ⇒ 分区触发器克隆（40 − 39 = 1，`audit_logs` 增强行）**不计入**父级计数。

### 3.3 连接与凭据面（**信任边界缺口的直接成因**）

```text
E-8  `alembic.ini:5`              sqlalchemy.url = postgresql+psycopg://uap:uap@localhost:5432/uap   （**硬编码**）
E-9  `config/settings.py:57`      DATABASE_URL   = postgresql+psycopg://uap:uap@localhost:5432/uap   （默认值）
E-10 `tests/integration/alembic_testkit.py:21`   BASE_DSN = …//uap:uap@localhost:5432/<test db>
E-11 `docker-compose.yml:7-9`     POSTGRES_USER = uap · POSTGRES_PASSWORD = uap · POSTGRES_DB = uap
E-12 `.env.example`               `DATABASE_URL=`（**空**）· **无** migration/runtime 分离键
E-13 运行时连接工厂                `infrastructure/database/{config.py:37, session.py:29}` 单一 `settings.DATABASE_URL`
```

⇒ **`E-8`…`E-13` 共同证明**：仓库中**只有一条数据库身份**，且该身份为集群超级用户。任何"上下文判据"在库内**不可强制执行**。

### 3.4 客户端自述信号的可伪造性（**实测探针 · 复验**）

```text
E-14 probe 1（未设置）      →  current_setting('uap.probe_ctx', true) = NULL
E-15 probe 2（同会话 set）  →  set_config('uap.probe_ctx','x', true) 后读回 'x'   ⇒ **无权限门槛**
E-16 probe 3（新会话）      →  读回 NULL                                          ⇒ 事务级可复原，但**不提供信任**
```

---

## 4. 实测清单（**先测量再写入** · 可复现）

### 4.1 对象 / 角色计数（`uap_b1_test` @0015）

| 指标 | 实测值 | 取数谓词（摘要） |
|---|---|---|
| 非 `pg_%` 角色 | `1`（`uap`） | `pg_roles where rolname not like 'pg\_%'` |
| `public` 对象总数 | `156` | `pg_class relnamespace=public`（`r,p,S,i,v`） |
| 对象 owner 种类 | `1`（`uap`） | `group by pg_get_userbyid(relowner)` |
| 表（`r`+`p`） | `35` | `relkind in ('r','p')` |
| 子分区表 | `3` | `pg_inherits` + `relkind='r'`（**排除 PK 索引继承行**） |
| 索引 | `108` | `relkind='i'` |
| 父级触发器 | `39` | `pg_trigger where not tgisinternal and tgparentid=0` |
| 触发器行（含克隆） | `40` | `pg_trigger where not tgisinternal` |
| 函数 | `22` | `pg_proc` in `public` |
| `prosecdef = true` | `0` | 同上 |
| 显式 GRANT 到非 owner | `0` | `information_schema.role_table_grants` |

### 4.2 迁移内 GRANT / 角色语句（**raw / adjudicated 双报**）

```text
raw 命中（`CREATE ROLE|CREATE USER|GRANT |REVOKE |SET ROLE|ALTER DEFAULT PRIVILEGES|session_replication_role`，
         扫 `migrations_alembic/versions/*.py`）= **13 行**
adjudicated（逐行裁决）：
  可执行语句 = **0**
  非可执行（注释 / docstring / 中文说明）= **13**（示例：0013:28「本 revision **零 GRANT**」· 0013:267「# [9] GRANT = 0」·
  0005:32「re-grant = UPDATE 本行」等）
⇒ 与 `D-P10-13` 的实测登记一致（既有 12 个 migration 中 `GRANT` = 0）。
```

### 4.3 阶段/编号面

```text
`alembic heads` = `0015_p12_indexes`（单头）· chain length = 15
测试中引用 `0015_p12_indexes` 的文件 = **17 个**
其中**链长硬断言**：`tests/integration/test_ai_gateway_schema.py:1009` → `assert len(revisions) == 15`
其中 **heads 硬断言**：`test_ai_gateway_schema.py:1007` · `test_agent_tool_permission_schema.py:330` · `test_p12_indexes.py:108`
其中 `HEAD_REVISION` 常量：`test_ai_gateway_schema.py:70` · `test_p10_event_audit_schema.py:60`
```

### 4.4 既有负向守卫（`TEST vs DECISION` 风险的落点）

```text
G-1  `tests/architecture/test_p10_event_audit_boundary.py:225`
     ("GRANT", "OPEN-P10-1 = DEFER: the migration performs no GRANT")  —— 语料 = **0013 迁移源码**（file-scoped）
G-2  `tests/integration/test_p10_event_audit_schema.py:599-604`
     `test_sec2_migration_performs_no_grant` —— 语料 = **0013 迁移源码**（file-scoped）
G-3  `tests/integration/test_p10_event_audit_schema.py:18`（docstring）「D-P10-13 = FROZEN  GRANT / role design = OPEN-P10-1 (DEFER)」
⇒ **判定**：`G-1`/`G-2` 的**断言谓词**不改写（二者只扫 0013 源码，新增 migration 文件**不在其语料内**）；
   但其 **rationale 文本**（"OPEN-P10-1 = DEFER"）在角色体系落地后将变为**语义陈旧** ⇒ 属 `TEST vs DECISION` 登记项
   （`OQ-OP101-14`），**不得由 Bot 自行改测试**（skill 教训 16）。
```

---

## 5. 信任边界模型（**设计面 · 不选机制**）

### 5.1 身份分离契约（`OPER` 级 · 目标态）

```text
IC-1  存在**至少两个**数据库角色：`R_mig`（migration trust context）与 `R_app`（runtime application context）
IC-2  `R_app` **不是** `R_mig` 的成员（直接或间接）⇒ `SET ROLE R_mig` 在 runtime 凭据下**失败**
IC-3  `R_mig` 与 `R_app` 的凭据**不同**，且由不同配置键承载（不得共用同一 DSN）
IC-4  `R_app` 不持 DDL（`CREATE` on schema / 任何 `ALTER`/`DROP` 对象权限）
IC-5  C2 的放行判据**只**可为服务端身份（`current_user` / `session_user` / `pg_has_role`），
      且**不得**可为：GUC · `application_name` · 会话自定义参数 · 临时标志（Human 明令）
IC-6  `R_app` 路径的 registry INSERT 判定结果 = **与 0007 原版逐字相同的拒绝**（Amendment §9 判别法）
IC-7  downgrade 后：C2 定义 = 0007 原文本（逐字节）· `R_mig` / `R_app` 及其 GRANT **无残留**
```

### 5.2 机制族（**既有分析结论 · 非本轮新选择**）

```text
`P13_B1_HUMAN_DECISION_AMENDMENT.md` §4/§6 已确立：
  · `M-2`（角色判据）与 `M-6`（受信路径）是**唯一可满足全部 §7 准则**的机制族；
  · `M-4`（C2 函数改写）是**必需载体** —— 因 C2 对 INSERT **无条件 RAISE**，
    任何"允许受信 context"都**必然**改写 C2；**改写≠绕过**，安全性由所承载信号决定；
  · `M-1`（GUC）· `M-3`（DEFINER）· `M-5`（状态控制）· `M-7`（新对象）**均不满足**。
⇒ 本阶段**不重新选择机制族**；本阶段的任务是**把该机制族落地所需的前置条件形式化**。
```

### 5.3 目标态不变量（**供 acceptance 逐项断言**）

| 编号 | 不变量 | 可证伪判据 |
|---|---|---|
| `INV-01` | runtime 角色 ≠ migration 角色 | `current_user` 在两路径不同 |
| `INV-02` | runtime 无法成为 migration 角色 | `SET ROLE R_mig` 失败（`OQ-OP101-02` 前置） |
| `INV-03` | runtime registry INSERT = DENY | 错误消息 = 0007 原版逐字 |
| `INV-04` | 受信 context registry seed = ALLOW | 仅目标行写入，其余写入仍被拒 |
| `INV-05` | runtime 不持 DDL | `has_schema_privilege(R_app,'public','CREATE') = false` 等逐项 |
| `INV-06` | 判据不可伪造 | 以 `R_app` 伪造 GUC / `application_name` / `SET ROLE` 后仍 DENY |
| `INV-07` | downgrade 后 C2 逐字节复原 | `pg_get_functiondef` 比对 0007 原文本 |
| `INV-08` | downgrade 无残留受信主体 | `pg_roles` 无 `R_mig`；`pg_class.relacl` / `role_table_grants` 无其授权 |

---

## 6. 角色模型设计面（**四个候选 · 均未选择**）

> **说明**：以下为**设计空间枚举**，用于 Human 裁定（`OQ-OP101-01`）。
> **本文件不推荐、不排序为结论、不代选**；`Recommended Direction` 见 `OPEN_P10_1_DECISION_RESOLUTION.md`（且**标注 `≠ Human Decision`**）。

| 编号 | 形态 | 与 `CORE` §13 的关系 | 主要代价 | 主要风险 |
|---|---|---|---|---|
| `RM-A` | 原样落地三角色：`uap_migrator`(DDL，仅迁移窗口) / `uap_app`(DML) / `uap_readonly` | **完全一致** | 需完整 GRANT 矩阵（35 表 × 动词）+ 156 对象所有权问题 | 面最大；须先解决所有权归属（`OQ-OP101-09`） |
| `RM-B` | 两角色最小切片：`uap_migrator` + `uap_app`（`uap_readonly` DEFER） | 一致（子集） | GRANT 矩阵仍需覆盖 runtime 全部 DML 面 | `uap_readonly` 留待后续，验收范围需显式限定 |
| `RM-C` | 保留 `uap`（集群超级用户）为 **migration identity**；新增单一 `uap_app`（NOSUPERUSER + 最小 DML）为 **runtime identity** | **部分**（`uap` ≠ `uap_migrator`） | 改动最小：无需所有权迁移；`alembic.ini` 不变 | `R_mig` 仍为超级用户 ⇒ 不满足"最小权限"精神；受信主体 = 超级用户（`OQ-OP101-02`） |
| `RM-D` | 三层：`uap_seed`（**仅** `acl_subject_types` INSERT，用于 registry）/ `uap_migrator`（DDL）/ `uap_app`（DML） | **超出** §13（新增角色） | 需新决策承认第四角色 | 角色数增加 ⇒ 治理面扩大；`D-P13-15` 的"受信 migration context"需与之对齐 |

**角色是 cluster 级对象（关键约束 · 实测）**

```text
K-1  PG 角色为**集群级**，不是 database 级 ⇒ 同一 cluster 的 `uap` / `uap_b1_test` / `uap_test` **共享**角色集合
K-2  `CREATE ROLE` 需 `CREATEROLE` 或超级用户 ⇒ 当前迁移角色 `uap` **具备**（`rolcreaterole = t`）
K-3  `DROP ROLE` 要求该角色**不拥有对象、不持有权限**（否则报错）⇒ 降级须先 `REVOKE` / `REASSIGN`
K-4  测试基建 `reset_test_database()`（DROP/CREATE DATABASE）**不会**移除 cluster 级角色 ⇒ 幂等责任在角色创建方
⇒ 角色创建位置（迁移内 vs 独立 bootstrap）**属 Human 决策**（`OQ-OP101-04` / `OQ-OP101-03`）
```

---

## 7. C2 判据面（**改造受约束面 · 不写函数文本**）

```text
C2 事实（复验）：`acl_subject_types` BEFORE INSERT/DELETE/UPDATE（row）
  · `TG_OP='INSERT'` → **无条件 RAISE**（无豁免分支 / 无 GUC 判据 / 无角色白名单）
  · 函数属性：`prosecdef = false` · `proconfig` 空 · owner = `uap` · 0007 创建
⇒ 结论（沿用 Amendment）：**C2 必须被改写**才能放行任何受信写入（`M-4` 载体），无第二条路径。
```

**判据候选（设计面 · 未选择）**

| 编号 | 判据 | 伪造面 | 备注 |
|---|---|---|---|
| `CP-A` | `IF current_user = ANY (ARRAY['uap_migrator']) AND TG_OP='INSERT' THEN RETURN NEW;` —— 字面角色白名单 | 依赖角色非成员（`IC-2`） | 判据与角色名耦合 ⇒ 改名须同步 |
| `CP-B` | `IF pg_has_role(current_user,'uap_migrator','MEMBER') AND TG_OP='INSERT' THEN RETURN NEW;` | 同上；`pg_has_role` 已含成员链 | 语义更显式（改名影响同 A） |
| `CP-C` | 不加判据，改由**权限层**阻断 runtime（撤 `INSERT` 权限） | **不成立**：C2 无条件 RAISE ⇒ 权限层**无法放行**任何人 | **仅登记为已排除项** |

**改造硬约束（无论选 `CP-A` 或 `CP-B`）**

```text
CC-1  DELETE / UPDATE(key 不可变) 分支**逐字不变**
CC-2  runtime 路径的拒绝消息**逐字节一致**（Amendment §9 判别法）
CC-3  不得引入 `SECURITY DEFINER`（`D-P11-08`）
CC-4  不得使用 GUC / 会话变量 / `session_replication_role` / `application_name`（Human 明令 + `CP-2`/`CP-4`）
CC-5  函数体不得新增表读取（避免 `search_path` 依赖与递归 —— P10 先例纪律）
CC-6  downgrade 须复原 0007 原函数文本（逐字节）
CC-7  以 `CREATE OR REPLACE FUNCTION` 覆盖 0007 对象 ⇒ **跨迁移函数替换**（**先例 = 0**，Amendment `B-5`）⇒ 新先例，须 Human 明确批准
```

---

## 8. 迁移 / 恢复面（**设计记录 · 本轮不建文件**）

```text
MIG-1  角色创建与 GRANT 的**归属**：迁移内 vs 独立 bootstrap 脚本（`scripts/`）⇒ **OQ-OP101-04**
MIG-2  revision 编号：若需独占 revision ⇒ 与 P13 seed 的 `0016` 预留冲突 ⇒ **OQ-OP101-03**
       （`D-PLAT-09` 阶段序的派生必然结果；**具体编号须 Human 裁定，Bot 不预占**）
MIG-3  迁移连接串：`alembic.ini:5` 为**硬编码** ⇒ 若 migration identity 变更，须一并处理（**OQ-OP101-10**）
MIG-4  downgrade 语义：`REVOKE` → `REASSIGN`/`DROP ROLE` → C2 复原；**须 FAIL-CLOSED**（与 `D-P13-12` 同源纪律）
MIG-5  迁移确定性：不得使用 `CREATE ROLE ... IF NOT EXISTS` 之外的隐式分支（PG 无 `IF NOT EXISTS` ⇒ 须 `DO $$ ... $$` 幂等块）
       ⇒ 与 `D-P13-10`（幂等 = 既有 precedent，冲突即显式失败）的一致性须评估
MIG-6  分区/对象不变：本阶段**不新增表 / 列 / 索引 / 触发器**（除 C2 函数替换外，属 P13 B-1 Amendment 面）
MIG-7  迁移链完整性：`0010–0015` sha256 **不得变化**（历史不可改写）
```

---

## 9. 连接 / 凭据 / 环境面（**设计面 · 未选择**）

| 编号 | 面 | 现状（实测） | 设计问题（未裁） |
|---|---|---|---|
| `EN-1` | 运行时 DSN 键 | `config/settings.py:57` `DATABASE_URL`（默认 = 超级用户 `uap`） | runtime 是否改用 `R_app` 凭据？键名与默认值如何？ |
| `EN-2` | 迁移 DSN 键 | `alembic.ini:5` 硬编码 `uap` | 是否新增独立键（如 `MIGRATION_DATABASE_URL`）？硬编码是否改为 env 注入？ |
| `EN-3` | 凭据模板 | `.env.example` 仅 `DATABASE_URL=`（空）· **无**分离键 | 是否新增第二凭据键？空值语义（fail-closed）如何定义？ |
| `EN-4` | 容器编排 | `docker-compose.yml` `POSTGRES_USER=uap`（容器超级用户） | 是否在 compose 中预置 `R_app` / `R_mig`？还是交由迁移/bootstrap 创建？ |
| `EN-5` | `build_info` / `/ready` | `EXPECTED_ALEMBIC_REVISION`（构建期工件，运行时不可覆盖） | 角色变更是否影响 `/ready` 语义？（初步：否，登记待验） |
| `EN-6` | 敏感面纪律 | `.env` 不入库 · 日志双重脱敏（既有安全基线） | 新凭据须遵守同一纪律（不得写入文档/日志/示例） |

---

## 10. 连带同步面（**实施轮的强制同步清单 · 本轮仅登记**）

```text
T-1  迁移链与 revision 常量：`0015_p12_indexes` 引用面 = **17 个测试文件**
     · 链长硬断言 `test_ai_gateway_schema.py:1009 assert len(revisions) == 15`
     · `heads` 硬断言 `test_ai_gateway_schema.py:1007` / `test_agent_tool_permission_schema.py:330` / `test_p12_indexes.py:108`
     · `HEAD_REVISION` 常量 `test_ai_gateway_schema.py:70` / `test_p10_event_audit_schema.py:60`
     · `test_p10_event_audit_schema.py:60` 已含"head 随链推进"注释（该套件策略为跟随 head）
T-2  负向守卫 rationale：`test_p10_event_audit_boundary.py:225` · `test_p10_event_audit_schema.py:599-604`/`:18`
     （`G-1`/`G-2`/`G-3`）⇒ **断言谓词不改**；rationale 文本须显式对账（`OQ-OP101-14`）
T-3  测试基建：`tests/integration/alembic_testkit.py`（`BASE_DSN` / `_ADMIN_DSN` / `reset_test_database()`）
     ⇒ 多角色下如何提供 runtime vs migration 凭据、cluster 级角色的幂等与清理（`OQ-OP101-11`）
T-4  配置面：`config/settings.py` · `alembic.ini` · `env.example` · `docker-compose.yml`
T-5  文档面（**只在实施轮同步 · 本轮不改**）：`CORE_DOMAIN_MODEL.md` §13 的"尚未实现"表述 ·
     `MIGRATION_STRATEGY.md` §9 执行账号表述 · `P10_IMPLEMENTATION_*` 中 `OPEN-P10-1 = DEFER` 的历史陈述
T-6  守卫面：若引入"角色/GRANT 存在"的正向断言，须同时保留"未偷偷形成权限体系"的历史时点表述（附录式声明现行口径）
```

---

## 11. 依赖四类分离

| 类别 | 内容 | 状态 |
|---|---|---|
| **design 依赖** | `IC-1`…`IC-7` 身份分离契约 · `INV-01`…`INV-08` 不变量 · 角色模型（`RM-A`…`RM-D`）· C2 判据（`CP-A`/`CP-B`） | **待 Human 裁定**（`OQ-OP101-01/02/05/06`） |
| **schema 依赖** | 本阶段**不新增**表/列/索引/触发器；唯一对象级变更为 **C2 函数替换**（属 P13 B-1 Amendment 实施面） | 设计记录（`CC-7` 新先例待批） |
| **implementation 依赖** | 角色创建/GRANT 的归属与位置 · revision 编号 · 迁移连接串 · downgrade 序列 · 幂等形态 | **BLOCKED**（待 design 裁定） |
| **runtime 依赖** | runtime 凭据注入 · `DATABASE_URL` 语义变更 · 服务启动后的权限断言 | **BLOCKED**（待 `OPEN-P10-1` 冻结后随 Runtime 阶段） |

---

## 12. OQ 清单（`OQ-OP101-01`…`OQ-OP101-14` · **全部待 Human 裁定**）

| 编号 | 问题（一句话） | 关键依据 | 关联 |
|---|---|---|---|
| `OQ-OP101-01` | 角色拓扑采用 `RM-A` / `RM-B` / `RM-C` / `RM-D`？ | `CORE` §13 · `D-P10-13` · §6 | `INV-01` |
| `OQ-OP101-02` | migration identity **是否必须非超级用户**（最小权限），或接受超级用户为受信 context？ | Human §5「runtime 可获得 migration 权限 = 不得」· §6 `RM-C` | `INV-02` |
| `OQ-OP101-03` | 本阶段是否独占一个 Alembic revision？若是，编号归属与 P13 seed（原预留 `0016`）的顺延关系如何？ | `D-PLAT-09` · Human §3 执行顺序 · §8 `MIG-2` | `T-1` |
| `OQ-OP101-04` | 角色由**迁移**创建，还是由**独立 bootstrap 脚本 / 运维**创建（迁移仅断言存在并 FAIL-CLOSED）？ | `K-2`/`K-4` · `MIGRATION_STRATEGY` §9 | `MIG-1` |
| `OQ-OP101-05` | C2 放行判据采用 `CP-A`（字面白名单）或 `CP-B`（`pg_has_role`）？（`CP-C` 已排除） | Human §5 · `D-P11-08` · §7 `CC-1`…`CC-7` | `INV-03/04/06` |
| `OQ-OP101-06` | 本阶段是否同时落地 `CORE` §13 的 `uap_readonly`，或 DEFER？ | `CORE` §13 · `OUT-8` | `RM-A`/`RM-B` |
| `OQ-OP101-07` | runtime 角色的 GRANT 矩阵范围（哪些表 / 哪些动词）如何界定？含 `audit_logs`/`events` 的 INSERT 吗？ | `D-P10-13` · `CORE` §13「audit_logs 仅 INSERT, SELECT」 | `INV-05` |
| `OQ-OP101-08` | 「runtime 不持 DDL」是否由 **DB 层强制**（GRANT 面排除）并加正向断言？ | `D-P10-13` 禁止项 | `INV-05` |
| `OQ-OP101-09` | 既有 **156 个对象**的所有权保持 `uap`，还是迁移至 `R_mig`？ | `E-3` · §6 | `RM-A`/`RM-B` 可行性 |
| `OQ-OP101-10` | 配置/环境面如何承载双身份（`EN-1`…`EN-4`）：新增键名、`alembic.ini` 硬编码处理、compose 预置？ | `E-8`…`E-13` | `T-4` |
| `OQ-OP101-11` | 测试基建如何处理多角色与 **cluster 级角色**的幂等/清理（`reset_test_database()` 不清理角色）？ | `K-1`/`K-4` · `T-3` | `T-1`/`T-2` |
| `OQ-OP101-12` | downgrade 语义：`REVOKE`/`REASSIGN`/`DROP ROLE` 的序列、FAIL-CLOSED 边界、跨库副作用如何界定？ | `K-3` · `D-P13-12` 同源纪律 | `INV-07/08` |
| `OQ-OP101-13` | 「数据库身份隔离已经成立」的**机读判据**是什么（`D-P13-15` 的前置证明形式）？ | `D-P13-15` Purpose | `INV-02`/`INV-08` |
| `OQ-OP101-14` | 既有守卫 rationale（`G-1`/`G-2`/`G-3`）如何同步？属 `TEST vs DECISION` 冲突，须 Human 裁定处置口径 | skill 教训 16 · §4.4 | `T-2` |

> **`Recommended Direction` 与裁定请求单见 `OPEN_P10_1_DECISION_RESOLUTION.md`**（其中每条均标注 `≠ Human Decision`）。

---

## 13. Gate 结论

| 检查项 | 结果 |
|---|---|
| Scope 与 OUT 面（冻结证据逐条引用） | ✅ §1（`S-1`…`S-7` / `OUT-1`…`OUT-8`） |
| Baseline 只读校验（HEAD / tags / remote / 单头 / sha / 命名空间） | ✅ §2 |
| Existing Substrate 实测 | ✅ §3（`E-1`…`E-16`） |
| 实测清单（角色 / 对象 / GRANT / 负向守卫 / 编号面） | ✅ §4 |
| 信任边界模型（身份分离契约 + 不变量） | ✅ §5（`IC-1`…`IC-7` / `INV-01`…`INV-08`） |
| 角色模型设计面（4 候选 · **均未选择**） | ✅ §6（`RM-A`…`RM-D` + cluster 级约束 `K-1`…`K-4`） |
| C2 判据面（3 候选 · 含已排除项） | ✅ §7（`CP-A`/`CP-B`/`CP-C` + `CC-1`…`CC-7`） |
| 迁移 / 恢复面 | ✅ §8（`MIG-1`…`MIG-7`） |
| 连接 / 凭据 / 环境面 | ✅ §9（`EN-1`…`EN-6`） |
| 连带同步面 | ✅ §10（`T-1`…`T-6`） |
| 依赖四类分离 | ✅ §11 |
| OQ 清单（14 项 · 全部待裁） | ✅ §12 |
| **未实施**：`CREATE ROLE` = 0 · `GRANT`/`REVOKE` = 0 · migration 新增/改动 = 0 · `0016+` = ABSENT | ✅ §0/§11 |
| **未改写**：`0007` / C2 / 任何 `D-*` 决策正文 / `0010–0015` sha256 | ✅ §2 |

```text
OPEN-P10-1 PREP = **READY FOR HUMAN DECISION**
（设计面齐备；`OQ-OP101-01…14` 全部待裁；**不得**进入实现）
前置依赖  = 无（本阶段为前置闸门本身）
下游依赖  = P13 B-1 Amendment（挂起）→ P13 Implementation（NOT AUTHORIZED）
```

---

**END OF OPEN-P10-1 PREP REPORT（2026-09-26 · Gate = `READY FOR HUMAN DECISION` · **DRAFT · NOT FROZEN** · 未实施任何 DDL/DML/DDL-role）**
