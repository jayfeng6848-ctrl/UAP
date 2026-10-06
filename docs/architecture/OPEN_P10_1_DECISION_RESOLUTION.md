# UAP — OPEN-P10-1 DECISION RESOLUTION（Human Decision Resolution Prep）

> ## 状态
>
> ```text
> 轮次        = OPEN-P10-1 HUMAN DECISION RESOLUTION PREP（STRICT READ-ONLY · 决策就绪轮）
> 文档状态    = **REVISION 2 · NOT FROZEN**（相对上一轮：字段集改为 Human 指令 §决策范围 指定的九字段）
> Gate 结果   = **OPEN-P10-1 DECISION PREP = READY FOR HUMAN DECISION**
> 裁定覆盖    = `OQ-OP101-01` … `OQ-OP101-14`（14 / 14；`Current Human Decision` **全部留空**）
> 冻结条件    = **0 / 7** ⇒ `DECISION FREEZE WRITE = NOT PERMITTED`
> 本轮严禁    = `CREATE ROLE` · `GRANT` · `REVOKE` · `ALTER ROLE` · `DDL` · `DML` · `C2 修改` ·
>               `0007 修改` · `migration 创建` · `runtime 修改` · `commit` · `tag` · `push`
> 状态保持    = `0016 = ABSENT` · `0017 = ABSENT` · `CREATE ROLE = 0` · `GRANT = 0` · `REVOKE = 0` ·
>               `C2 = unchanged` · `DDL = 0` · `DML = 0` · `commit = 0` · `tag = 0` · `push = 0`
> ```
>
> **本文件性质**：**逐项裁定请求单（Decision Resolution Sheet）**。
> **不代裁、不推断 Human 意图、不输出 IMPLEMENTATION PASS**；所有 `Recommended Direction` **均标注 `≠ Human Decision`**；
> `Current Human Decision` 字段**一律留空**待 Human 填写。

---

## 0. 阅读约定

### 0.1 布局修订说明（**不改变任何裁定内容**）

```text
上一轮（P13 B-1 FINAL DIRECTION 轮）本文件的字段集为：
  Question / Current Evidence / Options / Engineering Impact / Compatibility / Future Runtime Impact /
  Recommended Direction / HUMAN DECISION / STATUS
本轮按 Human 指令 §决策范围 改为**指定的九字段**（顺序即 Human 所列顺序）：
  1 Question · 2 Evidence · 3 Options · 4 Security Impact · 5 Runtime Impact ·
  6 Migration Impact · 7 Compatibility Impact · 8 Downgrade Impact · 9 Current Human Decision
补充保留两行（**不属于** Human 指定九字段，供裁定参考）：
  · Recommended Direction（**≠ Human Decision**）  · STATUS
⇒ 本修订**只改字段布局与内容颗粒度**；候选标签（`RM-A…RM-D` / `CP-A…`）与既有分析结论**逐一保留**，
  不 supersede 任何 `D-*` 决策、不产生实施授权。
```

### 0.2 允许的结果词表（Human 填写 `Current Human Decision` 时择一）

```text
ACCEPT OPTION A | ACCEPT OPTION B | ACCEPT OPTION C | ACCEPT OPTION D | ACCEPT OPTION E
CUSTOM DECISION | KEEP OPEN | NEED MORE EVIDENCE

STATUS 词：PENDING（未收到裁定；**占位符不构成任何一种允许结果**，不得推断为 KEEP OPEN）
           FROZEN（已获裁定并已写入决策载体）· DEFERRED（Human 明确挂起）
```

### 0.3 候选标签锁定（**逐字保持 · 不得漂移**）

```text
角色拓扑 : RM-A（CORE §13 三角色原样） · RM-B（两角色最小切片） · RM-C（保留 uap 为 migration identity）
           · RM-D（三层：uap_seed / uap_migrator / uap_app）
C2 判据  : CP-A（current_user 字面白名单） · CP-B（pg_has_role MEMBER） · CP-C（权限层阻断 —— **已排除**）
           CP-D（session_user 字面判据） · CP-E（pg_has_role USAGE） · CP-F（current_user ∧ session_user 合取）
```

### 0.4 证据纪律

```text
① 本文件所有事实均来自**直接读取仓库文件**或**本轮只读实测**，并以 ID 标注来源：
   `FD-n` / `E-n` / `P-n`（定义见 §2）· `M-n`（迁移解析，§1）。
② **不依据聊天记录推断**：凡无法从仓库或实测取得的结论，一律标注「未取得证据」而不补造。
③ 本轮**未执行任何 INSERT/UPDATE/DELETE**（`DML = 0` 为硬约束）⇒
   C2 的拒绝消息**由 `pg_get_functiondef` 逐字读取得出**，**非**由 INSERT 探针取得（见 §4.2）。
```

---

## 1. 权威材料逐项读取登记（Human 指令「必须读取」）

| # | 材料 | 读取范围（本轮） | 关键结论（逐字/紧邻原文） |
|---|---|---|---|
| `R-1` | `CORE_DOMAIN_MODEL.md` §13（`## 13. Security Review（数据层）`，行 1051–1067） | 全节 12 行表格 | 「最小权限 DB 角色 \| `uap_app`（DML）、`uap_migrator`（DDL，仅迁移窗口）、`uap_readonly`；**应用运行时不持有 DDL 权限**」·「审计不可变 \| `audit_logs` **仅授予 `INSERT, SELECT`**；`BEFORE UPDATE/DELETE` trigger 抛异常」·「租户隔离 \| … RLS（**可选**，见 Q1）…」 |
| `R-2` | `OPEN_P10_1_PREP_REPORT.md`（全文 13 节） | `§1 S-1…S-7 / OUT-1…8` · `§2 Baseline` · `§3 E-1…E-16` · `§4 P-1…P-4` · `§5 IC-1…IC-7 / INV-01…INV-08` · `§6 RM-A…RM-D / K-1…K-4` · `§7 CP-A…CP-C / CC-1…CC-7` · `§8 MIG-1…MIG-7` · `§9 EN-1…EN-6` · `§10 T-1…T-6` · `§11` · `§12 OQ-OP101-01…14` · `§13` | 设计面与不变量、候选集、连带同步面、`OQ` 清单；`K-1`「PG 角色为**集群级**，不是 database 级」· `K-3`「`DROP ROLE` 要求该角色**不拥有对象、不持有权限**」· `K-4`「`reset_test_database()`（DROP/CREATE DATABASE）**不会**移除 cluster 级角色」 |
| `R-3` | `D-P13-15`（`PLATFORM_DECISION_LOG.md` 行 2744–2762） | 记录全文（5 字段 + 登记口径声明） | `Purpose`：「**允许未来受信 migration context 建立 system registry seed，但前提是数据库身份隔离已经成立。**」· `Does not authorize`：「`0016 migration` · `seed INSERT` · `C2 修改` · `runtime permission expansion`」·「`D-P13-11` 的禁止字段**保持原样**」·「**不修改** `D-P13-01…14` 正文…supersession 新增 = 0」 |
| `R-4` | `D-P11-08`（`PLATFORM_DECISION_LOG.md` 行 2079–2089） | 记录全文 | 「P11 trigger functions：**`SECURITY INVOKER` = canonical**。**明确禁止引入 `SECURITY DEFINER`** —— 除非未来产生**新的独立 Human Decision**」· 依据「实测：全仓 `SECURITY DEFINER` = **0**（8 migration / 24 trigger / 15 function 全部默认 INVOKER），**无任何 `SET search_path`**」· 禁止「**本轮不得引入任何 `SECURITY DEFINER` function**（非本轮实施面，政策本身即刻生效）」 |
| `R-5` | **现有 migration ownership pattern**（`migrations_alembic/versions/*.py` 15 文件 + `migrations_alembic/env.py` + `alembic.ini` + `scripts/migrate.py`） | 见 §1.1 | **无任何** `CREATE SCHEMA` / `OWNER TO` / `ALTER … OWNER` / 可执行 `GRANT`/`REVOKE` ⇒ 对象所有权**完全由连接角色决定**（即 `uap`） |
| `R-6` | `MIGRATION_STRATEGY.md` §8/§9（行 100–127） | 全节 | §9 执行账号：「`uap_migrator`（仅迁移窗口授予 DDL）；应用账号 `uap_app` 无 DDL 权限」 |
| `R-7` | `D-PLAT-07` / `D-PLAT-07.a`（PDL 行 265–310） | 决策 + 实现语义 | 「**停用**应用启动时调用 legacy SQL migration runner 的行为」·「**Alembic 是唯一正式 Schema migration 入口**」· 删除 `ENABLE_MIGRATIONS_ON_STARTUP` 及其分支；**保留** legacy runner 本体与 `migrations/*.sql` |

### 1.1 `R-5` 展开：迁移所有权模式的**实测结论**

```text
M-1  15 个 migration 文件中，`CREATE SCHEMA` 命中 = **0**
M-2  `OWNER TO` / `ALTER … OWNER` 命中 = **0**（仅 `ALTER COLUMN … SET/DROP NOT NULL`、`ALTER TABLE … ADD COLUMN` 等结构变更）
M-3  可执行 `GRANT` / `REVOKE` / `CREATE ROLE` / `SET ROLE` / `session_replication_role` = **0**
     （raw 命中 4 行，全部位于 0013 的模块 docstring 与 `#` 注释，逐行裁决后 executable = 0）
M-4  ⇒ **所有权模式 = 隐式**：对象 owner 恒等于**连接角色**。当前连接角色 = `uap` ⇒ 156 对象全归 `uap`（`E-3`）。
M-5  `migrations_alembic/env.py::_resolve_url()` 的 URL 优先级（**逐字**）：
       1. `config.attributes["url"]`（程序化覆盖；testkit 使用）
       2. **`DATABASE_URL` 环境变量**
       3. `alembic.ini` 的 `sqlalchemy.url`（dev 默认）
     ⇒ **关键派生事实**：`alembic.ini:5` 的硬编码 DSN 在设置了 `DATABASE_URL` 时**被覆盖**；
       `config/settings.py:57` 的 runtime DSN **也**读同一 `DATABASE_URL`。
       ⇒ **迁移与运行时当前共享同一个环境变量** ⇒ 任何角色分离**必须**同时处理该解析链（见 `OQ-OP101-10`）。
M-6  `scripts/migrate.py` 走的是 **legacy runner**（`infrastructure/database/migration.py`，`migrations/*.sql` + `schema_migrations`），
     已被 `D-PLAT-07.a` 停用为启动路径、**保留本体不得删除** ⇒ 本设计**不得**依赖该路径承担角色创建。
M-7  `tests/conftest.py:21`：`os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://uap:uap@localhost:5432/uap_test")`
     ⇒ 测试进程的**默认**迁移/运行时 DSN 均为 `uap` 角色 + `uap_test` 库。
```

---

## 2. 实测基线（本轮只读复验）

> **范围**：`uap_b1_test`（@0015，唯一处于正式链头的库；`uap` 库 formal 为 0 表）。
> 上一轮的 `FD-n` / `E-n` 编号**沿用**；本轮**新增** `E-8…E-14`（本轮首次取得）。

### 2.1 上一轮事实复验（`FD-1…FD-7`）

```text
FD-1  alembic.ini:5 与 config/settings.py:57 的 DSN **相同**（`postgresql+psycopg://uap:uap@localhost:5432/uap`）—— 复验成立
FD-2  `pg_roles.uap`：rolsuper=t · rolcreatedb=t · rolcreaterole=t · rolbypassrls=t · rolcanlogin=t —— 复验成立
FD-3  public schema 156 对象 owner 全为 `uap` —— 复验成立
FD-4  非 `pg_%` 角色 = 仅 `uap`（1 个）—— 复验成立
FD-5  显式 GRANT 到非 owner = 0；`pg_database.datacl = NULL`；`public` schema ACL = PG16 默认 —— 复验成立
FD-6  自定义 GUC 可被任意会话 `set_config(...)` 设置并读回（事务级；新会话复原）—— 复验成立
FD-7  `application_name` / 会话变量属客户端自述（无服务端身份校验）—— 复验成立
```

### 2.2 本轮**新增**实测（`E-8…E-14`）

```text
E-8   `pg_auth_members` = **3 行**，**全部为 PG 内建**且**不涉及 `uap`**：
        pg_monitor ← pg_read_all_settings · pg_monitor ← pg_read_all_stats · pg_monitor ← pg_stat_scan_tables
      ⇒ `uap` **不是**任何角色的成员、也不是任何角色的被授予者 ⇒ 当前**无成员链可被利用**
E-9   `pg_roles.uap` 完整属性：rolsuper=t · rolinherit=t · rolcreaterole=t · rolcreatedb=t · rolcanlogin=t ·
        rolreplication=**t** · rolbypassrls=t · rolconnlimit=**-1**（无限制）· rolvaliduntil=**NULL**（永不过期）
E-10  4 个库（`postgres` / `uap` / `uap_b1_test` / `uap_test`）**owner 全为 `uap`**
E-11  `pg_default_acl` = **0 行**（无 `ALTER DEFAULT PRIVILEGES` 规则）
E-12  `has_schema_privilege('uap','public','CREATE') = true` · `USAGE = true`
E-13  关键表 `relacl = NULL`（`acl_subject_types` / `audit_logs` / `events` / `users` 四项实测）⇒ 无显式授权，权限来自 owner
E-14  C2 触发器实测：`tgname=tg_acl_subject_types_protect` · **`tgtype = 31`** · `tgenabled = O`（启用）·
        `tgparentid = 0`（父级）· 函数 `enforce_acl_subject_types_protect` · **`prosecdef = false`** · `owner = uap`
```

> **`tgtype = 31`** 位分解 = `1(ROW) + 2(BEFORE) + 4(INSERT) + 8(DELETE) + 16(UPDATE)`
> ⇒ **BEFORE INSERT / DELETE / UPDATE，FOR EACH ROW**（与 `R-2` 的 C2 描述一致）。

### 2.3 `@0015` 种子现状（`E-15`）

```text
acl_subject_types = 0 · permissions = 0 · roles = 1（platform_admin）· role_permissions = 0
users = 0 · tenants = 0 · platform_state = 1（uninitialized）
```

---

## 3. Role Model 深度分析（Human 指令「必须重点分析」第 1 组）

### 3.1 七项必答（**逐项 · 证据驱动**）

| # | 必答问题 | 当前事实（实测） | 设计后果（**非选择**） |
|---|---|---|---|
| `A-1` | **schema owner 是否独立** | `public` schema owner = `pg_database_owner`（PG16 默认，`E-5`；**未被任何迁移改动**，`M-1`）。对象 owner = 连接角色 = `uap`（`E-3`/`M-4`） | 若要求「schema owner 独立」（如专用 `uap_schema_owner`），须 `ALTER SCHEMA public OWNER TO …` ⇒ **触及 PG16 默认语义**且影响所有库；若只要求「runtime 非 owner」则**无需改动**（`E-13` 已证明 runtime 非 owner 时不具对象级 DDL）。**属 Human 决策**（`OQ-OP101-01` / `OQ-OP101-09`） |
| `A-2` | **migration identity 是否独立** | 当前 migration 与 runtime **同角色同 DSN**（`FD-1` + `M-5`）；且 `_resolve_url` 让 `DATABASE_URL` **同时**决定两者 | 要求「独立」⇒ 必须：(a) 引入独立凭据载体；(b) 修正 `env.py` 解析优先级；(c) 决定 migration 角色的权限等级。**属 `OQ-OP101-02` / `OQ-OP101-10` / `OQ-OP101-04`** |
| `A-3` | **runtime identity 是否独立** | 当前 runtime 复用 `uap`（`FD-1`）⇒ 具备 `SUPERUSER`/`CREATEROLE`/`CREATEDB`/`REPLICATION`/`BYPASSRLS`（`E-9`，`FD-2`） | 要求「独立」⇒ 引入 `uap_app`（`NOSUPERUSER`/`NOCREATEROLE`/`NOCREATEDB`/`NOREPLICATION`/`NOBYPASSRLS`）+ 最小 GRANT。**属 `OQ-OP101-01` / `OQ-OP101-07` / `OQ-OP101-08`** |
| `A-4` | **PostgreSQL role 生命周期** | 角色为**集群级**（`K-1`）：`CREATE ROLE` 在任一库执行即对所有库可见；角色**不随 `DROP DATABASE` 消失**；`DROP ROLE` 要求**不拥有对象、不持权限**（`K-3`）；`pg_shdepend` 会记录跨库依赖 | 角色创建/回收**必须**与「数据库生命周期」解耦：由**环境引导（bootstrap）**承担最自然；若由迁移承担，须解决幂等（PG 无 `CREATE ROLE IF NOT EXISTS`）与降级（`REVOKE`→`REASSIGN`/`DROP`）。**属 `OQ-OP101-03` / `OQ-OP101-04` / `OQ-OP101-12`** |
| `A-5` | **多数据库一致性** | 同一 cluster 承载 4 库，owner 全为 `uap`（`E-10`） | **角色存在性 = 全局**；**GRANT = 每库独立**（对象级授权不跨库）⇒ 信任边界方案若依赖 GRANT，**必须在每个库的迁移中重复落地**；若只依赖 `current_user` 判据，则**天然跨库一致**（判据不含对象授权）。**属 `OQ-OP101-03` / `OQ-OP101-07`** |
| `A-6` | **`reset_test_database()` 影响** | 该函数**仅** `DROP DATABASE … WITH (FORCE)` + `CREATE DATABASE`（`alembic_testkit.py:34-40`），**不触碰角色**（`K-4`） | ⇒ 若角色由迁移创建：**首次**运行创建角色，**后续**运行会因角色已存在而失败 ⇒ 必须幂等；若角色由环境引导创建：testkit **零改动**（但需保证 CI/本地已引导）。**属 `OQ-OP101-04` / `OQ-OP101-11`** |
| `A-7` | **`public` ownership 清理策略** | `public` 现为 PG16 默认（owner `pg_database_owner`，ACL `pg_database_owner=UC | =U` ⇒ **PUBLIC 仅 USAGE、无 CREATE**，`E-5`）；`has_schema_privilege('uap','public','CREATE') = true` 来自 owner/DBA 属性（`E-12`） | 「清理」= 明确**谁可 CREATE**：现状对 PUBLIC 已安全（无 CREATE）；风险来自**超级用户与 owner 身份**。可选策略：(i) 不改（依赖 runtime 非 owner）；(ii) 显式 `REVOKE CREATE ON SCHEMA public FROM PUBLIC`（**已是默认**，属冗余加固）；(iii) 迁出 `public` 到专用 schema（**触及全部既有对象**，面极大）。**属 `OQ-OP101-09` / `OQ-OP101-10`** |

### 3.2 候选 × 五维（Security / Runtime / Migration / Compatibility / Downgrade）

| 维度 | `RM-A`（CORE §13 三角色原样） | `RM-B`（两角色最小切片） | `RM-C`（保留 `uap` 为 migration identity） | `RM-D`（三层：`uap_seed`/`uap_migrator`/`uap_app`） |
|---|---|---|---|---|
| **Security Impact** | 最强（三身份分离，运行时无 DDL） | 强（两身份分离） | **中**：runtime 与 migration 可区分，但**受信主体 = 集群超级用户**（`E-9`）⇒ 凡持该凭据者皆可 seed | 最强（seed 权限收窄到仅 registry INSERT 的专用角色） |
| **Runtime Impact** | runtime 用 `uap_app`；只读消费者可用 `uap_readonly` | runtime 用 `uap_app`；无只读角色 | runtime 用 `uap_app`；migration 侧零改动 | runtime 用 `uap_app`；seed 由 `uap_seed` 承担 |
| **Migration Impact** | 需完整 GRANT 矩阵（35 表 × 动词）+ 所有权决策 | 需 GRANT 矩阵（runtime 面） | **零 GRANT**（沿用 owner 权限）· 仅需 C2 判据 | 需 registry 最小 GRANT + GRANT 矩阵 |
| **Compatibility Impact** | **完全**符合 `CORE §13` | 符合（**子集**，须声明分阶段）· `uap_readonly` = `OQ-OP101-06` | **部分**符合（`uap` ≠ `uap_migrator`）；与「最小权限 DB 角色」的**精神**张力较大 | **超出** §13（新增第四角色 ⇒ 须新决策承认） |
| **Downgrade Impact** | `REVOKE` 全矩阵 + 断言无对象 → `DROP ROLE ×2`（`K-3`） | 同 A（少一角色） | 仅 `DROP ROLE uap_app`（`uap` 保持）⇒ **最简** | 三角色回收 + registry GRANT 回收 |
| **与 `D-P13-15` 前置的关系** | 满足（身份隔离成立） | 满足 | 满足（**但受信主体过宽**） | 满足（且受信主体最小） |

> **不选择声明**：以上为**设计空间枚举**。**本文件不推荐为结论、不排序、不代选**（见 `OQ-OP101-01`）。

---

## 4. C2 Permission Boundary 深度分析（Human 指令「必须重点分析」第 2 组）

### 4.1 证明义务（Human 指令逐字）

```text
必须证明：
  runtime   : registry INSERT = DENY
  migration : registry seed   = ALLOW
且：不可通过 GUC / application_name / session flag 伪造。
```

### 4.2 载体事实（`E-14` + 逐字函数体）

```text
C2 = BEFORE INSERT/DELETE/UPDATE FOR EACH ROW（tgtype = 31）· ENABLED · parentid = 0 · SECURITY INVOKER · owner = uap
函数体（`pg_get_functiondef` 逐字）：
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
```
```
⇒ **INSERT 分支无条件 RAISE**（无判据、无豁免）⇒
   任何「受信 context 可写入」的方案**必然改写该分支**（`M-4` 载体；Amendment §4 已确立）。
   拒绝消息的**逐字文本**（用于验收「逐字一致」）：
   `acl_subject_types is a platform-controlled registry: runtime INSERT denied (registry rows are migration-controlled)`
   （两个相邻字符串字面量在 PG 中**隐式拼接**，中间**恰一个空格**）
```

> **取得方式声明**：该消息**由 `pg_get_functiondef` 读取**，**非**由 INSERT 探针触发 —— 本轮 `DML = 0` 为硬约束，
> 且**在 C2 存在时任何 INSERT 尝试本身即属 DML**。逐字一致性验收属**实施期**（`§4.5` 测试①）。

### 4.3 候选判据（`CP-A`…`CP-F`）与逐项安全性

| 编号 | 判据形态（示意，**非最终 SQL**） | 伪造面 | 强度评述 |
|---|---|---|---|
| `CP-A` | `IF current_user = ANY (ARRAY['<R_mig>']) AND TG_OP='INSERT' THEN RETURN NEW;` | 依赖「runtime 非 `R_mig` 成员」（`IC-2`）+ 连接凭据保密 | 判据**静态可读**，可对函数文本做字面断言 |
| `CP-B` | `IF pg_has_role(current_user,'<R_mig>','MEMBER') AND TG_OP='INSERT' THEN RETURN NEW;` | **跟随成员链**：若 `R_app` 任一时刻成为 `R_mig` 成员即被放行 | 比 `CP-A` **弱**（隐含依赖成员关系恒为假，且该依赖不在判据文本内） |
| `CP-C` | 不加判据，改由权限层（撤 `INSERT` 权限）阻断 runtime | —— | **已排除**：C2 无条件 RAISE ⇒ 权限层**无法放行任何人**，达不到 `migration = ALLOW` |
| `CP-D` | 同 `CP-A`，但用 **`session_user`** 而非 `current_user` | `SET ROLE` / `SET SESSION AUTHORIZATION`（后者需超级用户） | 比 `CP-A` **更强**：`session_user` = 会话建立时的登录身份，**不受 `SET ROLE` 影响** ⇒ 阻断「以受信角色连接后 `SET ROLE` 降级」与「以 runtime 连接后 `SET ROLE` 升格」两类路径（升格本已不可行，降格会误放行 `CP-A` 场景） |
| `CP-E` | `IF pg_has_role(current_user,'<R_mig>','USAGE') …` | 同 `CP-B`，但 `USAGE` 语义为「无需 `SET ROLE` 即拥有该角色特权」 | 与 `CP-B` 同级；`USAGE` 更贴近「实际生效身份」但仍随成员关系变化 |
| `CP-F` | `IF current_user = '<R_mig>' AND session_user = '<R_mig>' AND TG_OP='INSERT' THEN …`（**合取**） | 需同时伪造两者 | **最强**：两身份量**同时**约束，且均可静态断言 |

### 4.4 伪造面矩阵（Human 指令逐项）

| 伪造手段 | 是否可被服务端识别 | 对 `CP-A`/`CP-B` | 对 `CP-D`/`CP-E`/`CP-F` | 依据 |
|---|---|---|---|---|
| **GUC / 自定义会话参数** | **不可识别**（无权限门槛） | 判据**不读 GUC** ⇒ 伪造**无效** | 同 | `FD-6`（实测：任意会话可 `set_config` 并读回） |
| **`application_name`** | **不可识别**（客户端自述） | 判据**不读** ⇒ 无效 | 同 | `FD-7` · `D-P13-15` 禁止项 |
| **session flag（自定义）** | **不可识别** | 判据**不读** ⇒ 无效 | 同 | `FD-6` 同源 |
| **`SET ROLE <R_mig>`** | 可识别（需成员资格） | **可绕过 `CP-A`**：若以 `R_app` 连接且其为 `R_mig` 成员 ⇒ `current_user` 变为 `R_mig` ⇒ 放行 ⇒ **必须先满足 `IC-2`（严格非成员）** | `CP-D`/`CP-F`：`session_user` 恒为 `R_app` ⇒ **仍拒绝** | `E-8`（当前无成员链；但设计不得**依赖**当前状态） |
| **`SET SESSION AUTHORIZATION`** | 需**超级用户** | 若 runtime 非超级用户 ⇒ 不可用 | 同 | `E-9`（当前 runtime 是超级用户 ⇒ **这正是必须分离身份的原因**） |
| **`search_path` / 同名函数劫持** | 需 CREATE 权限 | C2 为**触发器**，按 OID 绑定，不受 `search_path` 影响；且 `D-P11-08` 禁止 `DEFINER` + 既有函数 `proconfig` 为空（`E-4`） | 同 | `R-4` · `E-4` |
| **`DISABLE TRIGGER` / `session_replication_role`** | 需 owner / 超级用户 | **与判据无关**：这正是 `D-P13-11` 与 `D-P13-15` 明令禁止的路径（`§5`） | 同 | `D-P13-11` 禁止字段 · Human §5 逐字 |

### 4.5 可证性测试（八项 · 来自 `R-2` §7 A-5；**本轮全部未执行**）

```text
① ordinary runtime INSERT            → DENY（错误消息与 0007 原版逐字一致）       —— 未执行（DML 禁止）
② ordinary SQL client INSERT         → DENY                                     —— 未执行（DML 禁止）
③ 伪造尝试（set_config / SET ROLE / application_name）→ DENY                    —— 未执行（DML 禁止）
④ trusted migration seed INSERT      → ALLOW（仅 registry 行）                    —— 未执行（DML 禁止）
⑤ 迁移事务结束 → protection restored                                             —— 未执行（DML 禁止）
⑥ 后续 runtime INSERT                → DENY                                      —— 未执行（DML 禁止）
⑦ downgrade 后 C2 定义 = 0007 原文本（逐字）                                      —— 未执行（DDL 禁止）
⑧ downgrade 后 ②/③/⑥ 仍为 DENY                                                   —— 未执行（DML 禁止）
⇒ 全部属**实施期**证据；本轮**仅登记义务**，不得表述为已通过（Charter：不得把计划表述为已测试）。
```

### 4.6 改写硬约束（沿用 `R-2` `CC-1…CC-7` · 逐字保持）

```text
CC-1  DELETE / UPDATE(key 不可变) 分支**逐字不变**
CC-2  runtime 路径的拒绝消息**逐字节一致**（§4.2 的逐字文本）
CC-3  不得引入 `SECURITY DEFINER`（`D-P11-08`）
CC-4  不得使用 GUC / 会话变量 / `session_replication_role` / `application_name`（Human 明令 + `D-P13-15` 禁止字段）
CC-5  函数体不得新增表读取（避免 `search_path` 依赖与递归 —— P10 先例纪律）
CC-6  downgrade 须复原 0007 原函数文本（逐字节）
CC-7  `CREATE OR REPLACE FUNCTION` 覆盖 0007 对象 = **跨迁移函数替换**（**先例 = 0**）⇒ 新先例，须 Human 明确批准
```

---

## 5. 保留原则相容性（`D-P13-11` × `D-P13-15`）

### 5.1 逐条求交

| 冻结项 | 原文要点（逐字/紧邻） | 与本设计的关系 |
|---|---|---|
| `D-P13-11` | 「seed 在 **39 triggers 全部启用**下执行」· 禁止「`DISABLE TRIGGER` · `DROP TRIGGER` · `ALTER TRIGGER` · 绕过 C2 · **临时关闭保护后再恢复**」 | **保持**。本设计的候选判据（`§4.3`）**不改触发器状态**、**不 `ALTER TRIGGER`**，仅在**函数体**内增判据 ⇒ 属「受限改动面」（`CC-*`），**不是** bypass |
| `D-P13-15` | `Purpose`：「允许未来受信 migration context 建立 system registry seed，**但前提是数据库身份隔离已经成立**」；`Does not authorize`：`0016 migration`/`seed INSERT`/`C2 修改`/`runtime permission expansion` | **前提前置**由本阶段产出（`§3`/`§4`）。注意：`D-P13-15` 的 `Does not authorize` **明确不含**「C2 修改」⇒ **C2 修改不得由 `D-P13-15` 授权**，须**另获** Human 明确批准（`CC-7` 新先例 + `OQ-OP101-05`） |
| 交集判定 | —— | **不冲突**。二者可同时满足，**当且仅当**：① 身份隔离成立（`IC-2` 严格非成员）；② 判据不可伪造（`§4.4`）；③ 触发器状态零变更；④ C2 改写获独立批准 |

### 5.2 「受信 context ≠ bypass」的机读判别法（沿用 `R-2` §9）

```text
「允许受信 migration context」= C2 判据集合中新增一个**不可伪造**的受信主体；
                            runtime 路径的判定结果**逐字不变**（仍 RAISE 同一错误）；该主体仅用于 registry seed。
「允许绕过 C2」            = 在 runtime 或任意路径上降低/移除/临时关闭 C2 的阻断能力
                            （DISABLE · session_replication_role · 可伪造判据 · 空判据替换）。

判别法（可机读）：runtime INSERT 是否仍得到与 0007 原版**逐字节相同**的拒绝消息，
                 且伪造尝试（GUC / SET ROLE / application_name）是否仍被拒。
                 任一不成立 ⇒ 属「绕过」，不属「受信 context」。
```

### 5.3 若 Human 选择的判据违反 `IC-2`

```text
若 `OQ-OP101-01`（拓扑）或 `OQ-OP101-02`（migration identity 权限）导致 runtime 可能成为 `R_mig` 成员，
或 `R_mig` 仍为 runtime 可用的超级用户凭据 ⇒ **`O-3` 方向失效**（`O-2` 的 DEFERRED 前提未解除）⇒
⇒ 该情形下 `D-P13-11` 与 `D-P13-15` **仍不冲突**，但 `D-P13-15` 的 Purpose **不可满足** ⇒ 必须在 `OQ-OP101-13` 中明确。
```

---

## 6. `OQ-OP101-01` … `OQ-OP101-14`（九字段裁定请求）

> 字段顺序 = Human 指令 §决策范围 所列；`Recommended Direction` 与 `STATUS` 为**补充行**（非 Human 指定九字段）。

---

### 6.1 `OQ-OP101-01` — 角色拓扑

| 字段 | 内容 |
|---|---|
| **1. Question** | `OPEN-P10-1` 的目标角色拓扑采用 `RM-A` / `RM-B` / `RM-C` / `RM-D` 中的哪一种？ |
| **2. Evidence** | `R-1`（`CORE §13` 三角色）· `R-2 §6`（`RM-A…RM-D` + `K-1…K-4`）· `E-1`…`E-5`（单角色 / 156 对象同属主 / `public` 默认）· `E-8`…`E-10`（无成员链 / 4 库同属主）· `M-1`…`M-4`（所有权隐式）· `D-P10-13`（`OPEN-P10-1` 登记与「不得给应用运行时 DDL 权限」） |
| **3. Options** | **A** = `RM-A`（`uap_migrator` + `uap_app` + `uap_readonly` 三角色原样）<br>**B** = `RM-B`（`uap_migrator` + `uap_app`；`uap_readonly` 另立项）<br>**C** = `RM-C`（保留 `uap` 为 migration identity，仅新增 `uap_app`）<br>**D** = `RM-D`（三层：`uap_seed` + `uap_migrator` + `uap_app`） |
| **4. Security Impact** | A/B/D：runtime 不持 DDL 且**不含** `SUPERUSER`/`CREATEROLE`/`CREATEDB`/`REPLICATION`/`BYPASSRLS`（对照 `E-9`，每项均为**移除**权限面）。C：runtime 仍与受信 context 可区分，但**受信主体 = 集群超级用户**（`E-9`）⇒ 「凡持 `uap` 凭据者皆可 seed」，信任边界**只到凭据保密层面**。D 额外把 seed 权限从 `uap_migrator` 收窄至**仅 registry INSERT** |
| **5. Runtime Impact** | A：runtime = `uap_app`，另可提供只读消费者（`uap_readonly`）。B/C/D：runtime = `uap_app`。四者对 runtime 的**行为语义**无差异（同 DSN 语义、同 ORM 层），差异仅在**权限面宽度**；C 使 migration 侧配置**零改动** |
| **6. Migration Impact** | A/B/D 需在**每个库**的迁移中落地 GRANT 矩阵（`A-5`：GRANT 不跨库）⇒ 触及 17 个测试文件的 `0015` 引用面与链长断言；C **零 GRANT**（沿用 owner 权限），迁移侧仅需 C2 判据改写一处。D 额外需 registry 上的最小 GRANT |
| **7. Compatibility Impact** | A **完全**符合 `CORE §13`；B 为 §13 的**子集**（须声明分阶段，`uap_readonly` = `OQ-OP101-06`）；C **部分**符合（`uap` ≠ `uap_migrator`），与「最小权限 DB 角色」精神张力明显；D **超出** §13（第四角色须新决策承认）。**四者均不违反** `D-P10-13` 与 `D-P13-11`/`D-P13-15` |
| **8. Downgrade Impact** | A/B/D：`REVOKE` 全矩阵 → 断言角色不拥有对象（`K-3`）→ `DROP ROLE`（多角色、跨库授权需盘点）。C：仅 `DROP ROLE uap_app`（不拥有对象、无 GRANT 时最简）。**注意**：若采用 A/B 的 `ALTER … OWNER TO uap_migrator`（`OQ-OP101-09` = B），则降级须**先迁回所有权** |
| **9. Current Human Decision** | `______________`（留空待填） |
| *Recommended Direction（≠ Human Decision）* | `RM-B` —— 在满足 `IC-1`/`IC-2` 全部准则的同时把新对象面压到最小；`uap_readonly` 与信任边界正交，可独立立项 |
| *STATUS* | **PENDING** |

---

### 6.2 `OQ-OP101-02` — migration identity 的权限等级

| 字段 | 内容 |
|---|---|
| **1. Question** | `R_mig` **是否必须**为非超级用户（最小权限），或接受**集群超级用户**作为受信 migration context？ |
| **2. Evidence** | `E-9`（`uap`：`SUPERUSER`/`CREATEROLE`/`CREATEDB`/`REPLICATION`/`BYPASSRLS` 全 true，`connlimit=-1`，`rolvaliduntil=NULL`）· `E-10`（4 库 owner）· `R-1`（`uap_migrator`「DDL，**仅迁移窗口**」隐含**非长期高权角色**）· `R-6`（`MIGRATION_STRATEGY §9`：迁移账号有 DDL、应用账号无）· Human 裁定 §5「runtime 可获得 migration 权限」= **不得** |
| **3. Options** | **A** = 必须 `NOSUPERUSER`（`R_mig` 仅持 seed/DDL 所需最小权限）<br>**B** = 接受超级用户为受信 context（受信边界 = DBA 边界）<br>**C** = 分阶段：先接受（`RM-C` 形态）→ 另立阶段收窄为 `NOSUPERUSER` |
| **4. Security Impact** | A：`R_mig` 本身最小 ⇒ 即使其凭据泄漏，攻击面限于「migration 可做的 DDL/DML」而非「集群级无所不能」；`SUPERUSER` 可绕过 `BYPASSRLS` 检查与多数权限校验、可 `SET SESSION AUTHORIZATION`、可 `DISABLE TRIGGER`（`§4.4`）⇒ 保留它等于**放弃 `D-P13-11` 的实质约束力**。B：受信主体过宽。C：终态同 A、过渡窗口内存在风险 |
| **5. Runtime Impact** | 无直接差异（runtime 用 `uap_app`）；间接：若 `R_mig` 保持超级用户，则「runtime 不得获得 migration 权限」的证明只能依赖**凭据不共享**，不可库内证明 |
| **6. Migration Impact** | A：需**引导角色**（谁能 `CREATE ROLE … NOSUPERUSER`？集群超级用户需在**迁移之外**执行，构成引导顺序问题）+ 迁移 DSN 须改为 `R_mig`（`M-5` 解析链）。B：零额外改动。C：两次改动 |
| **7. Compatibility Impact** | A/B/C 均**不违反**任何既有 `D-*`（`D-P10-13` 只约束"应用运行时"）；A **更贴合** `CORE §13`/`R-6` 的意图。**注意**：A **不改变** `D-P11-08`（`SECURITY DEFINER` 禁令仍适用） |
| **8. Downgrade Impact** | A：若曾 `ALTER ROLE … NOSUPERUSER`，降级须决定是否**恢复**超级用户属性（**不建议**，属安全退化）⇒ 建议降级仅 `DROP ROLE`，不回退属性。B：无。C：两阶段各有降级语义 |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `C` —— 目标取 A、起步用 B：把「环境引导改造」与「信任边界建立」解耦，避免同一轮同时承担两处高风险 |
| *STATUS* | **PENDING** |

---

### 6.3 `OQ-OP101-03` — revision 编号归属

| 字段 | 内容 |
|---|---|
| **1. Question** | 本阶段是否独占一个 Alembic revision？若是，编号归属为何，且 P13 seed（原预留 `0016`）是否顺延为 `0017`？ |
| **2. Evidence** | `D-PLAT-09` 路线 A + Human 裁定 §3（在 P13 前插入 `OPEN-P10-1` 闸门）· `P-1`（`alembic heads = 0015_p12_indexes`，单头，链长 15）· `P-2`（`versions/001[6-9]* = 0`）· `P-3`（17 个测试文件引用 `0015_p12_indexes`；`test_ai_gateway_schema.py:1009` 断言 `len(revisions) == 15`）· `P-4`（`P13_IMPLEMENTATION_CONTRACT.md §4` 记录 `0016_p13_seed` 为**设计记录**）· `K-1`（角色为集群级）· `M-6`（legacy runner 已停用，不得承担角色创建） |
| **3. Options** | **A** = 本阶段独占 `0016`（如 `0016_open_p10_1_role_trust_boundary`）⇒ P13 seed 顺延 `0017_p13_seed`<br>**B** = 本阶段**不经 Alembic**（角色/授权由环境引导承担）⇒ 编号不变（P13 仍 `0016`）<br>**C** = 由 Human 指定非连续编号 |
| **4. Security Impact** | 无直接安全差异；间接受 A 影响：新增 revision 的 `downgrade()` 将承担**集群级** `DROP ROLE`（`K-1`/`K-3`）⇒ 降级路径本身成为高风险面 |
| **5. Runtime Impact** | A：`/ready` 的 `EXPECTED_ALEMBIC_REVISION` 由**构建期工件**派生（运行时不可覆盖）⇒ 该工件随新 head 变化，须同步（`R-2 §9 EN-5`）。B：无变化 |
| **6. Migration Impact** | A：长链推进（15→16），须逐项同步 17 个测试文件的 `0015` 引用面与链长断言（`R-2 §10 T-1`），并处理与既有 `0016_p13_seed` **设计记录**的编号语义冲突（须**显式重映射登记**，不得静默）。B：链保持 15，**零编号改动**。C：需 Human 给出具体号 |
| **7. Compatibility Impact** | A 与 `D-PLAT-09` 阶段序**不冲突**（该序已含 `OPEN-P10-1`），但会产生「同一编号 `0016` 在契约中被两处使用」的**语义重叠** ⇒ 必须显式登记重映射。B 与所有既有契约**零冲突**。C 同 A 的重映射义务 |
| **8. Downgrade Impact** | A：`downgrade()` 必须回收角色/授权（跨库副作用，`A-5`），且须 FAIL-CLOSED。B：无迁移级降级（回退由环境引导负责）。C：同 A |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `B` —— `CREATE ROLE`/`GRANT` 属**集群级**对象（`K-1`），与「数据库 schema revision」生命周期不同；且避免与 `0016_p13_seed` 预留冲突 |
| *STATUS* | **PENDING** |

---

### 6.4 `OQ-OP101-04` — 角色创建者

| # | 字段 | 内容 |
|---|---|---|
| **1. Question** | 角色由**迁移**创建，还是由**独立引导脚本 / 编排**创建（迁移仅断言存在并 FAIL-CLOSED）？ |
| **2. Evidence** | `K-2`（迁移角色具 `CREATEROLE` ⇒ 技术可行）· `K-4`（`reset_test_database()` 不清角色）· `R-5 M-6`（legacy runner 已停用）· `scripts/` 现有 `migrate.py`(legacy) / `doctor.py` / `generate_build_info.py`（**无**引导 CLI）· `D-PLAT-07.a`（保留 legacy runner，不得删除） |
| **3. Options** | **A** = 迁移内创建（`DO $$ … $$` 幂等块）<br>**B** = 独立引导脚本（`scripts/`）创建；迁移**仅断言存在**，缺失即 `RAISE`（FAIL-CLOSED）<br>**C** = 编排/运维预置（compose init / DBA 手工）；迁移断言存在 |
| **4. Security Impact** | A：迁移路径获得 `CREATEROLE` 能力（即受信 context 可增角色）⇒ 扩大受信面。B/C：迁移**无角色 DDL** ⇒ 受信面更窄；但引导本身需高权身份（超级用户），该身份**必须**与 runtime 严格分离，且不得与迁移 DSN 复用 |
| **5. Runtime Impact** | 无直接差异 |
| **6. Migration Impact** | A：PG **无** `CREATE ROLE IF NOT EXISTS` ⇒ 需 `DO` 块，与 `D-P13-10`（幂等 = 既有 precedent「冲突即**显式失败**」）的一致性**须评估**；且降级须 `DROP ROLE`。B/C：迁移侧仅一条存在性断言（FAIL-CLOSED），**零角色 DDL** |
| **7. Compatibility Impact** | A 可能偏离既有幂等 precedent（须 Human 知悉）；B/C 与 `R-6`（`MIGRATION_STRATEGY §9`）及 `D-PLAT-07`（Alembic 唯一 schema 入口，角色非 schema）**最自洽**。三者均不违反 `D-P10-13` |
| **8. Downgrade Impact** | A：降级须回收角色（含跨库授权盘点）。B/C：降级**不涉及**角色 ⇒ 无残留风险；但须登记「环境引导与迁移版本可能不同步」的运维事实 |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `B` —— 与 `OQ-OP101-03` 的 `B` 自洽；把集群级对象交给环境引导，迁移仅做 FAIL-CLOSED 断言 |
| *STATUS* | **PENDING** |

> **格式勘误（如实披露）**：本小节表头误多一列（`# | 字段 | 内容`），不影响内容；已在 `§8` 自证偏差中登记。

---

### 6.5 `OQ-OP101-05` — C2 判据形态

| 字段 | 内容 |
|---|---|
| **1. Question** | C2 的放行判据采用 `CP-A` / `CP-B` / `CP-D` / `CP-E` / `CP-F`（或 `CUSTOM`）中的哪一种？ |
| **2. Evidence** | `§4.2`（函数体逐字 + `tgtype=31` + `prosecdef=false`）· `§4.3`（六候选）· `§4.4`（伪造面矩阵）· `E-8`（当前无成员链）· `FD-6`/`FD-7`（GUC/`application_name` 不可作信任）· `R-4`（`D-P11-08` 禁 `DEFINER`）· `D-P13-11`（禁 `ALTER TRIGGER` / 绕过 C2）· `D-P13-15`（`Does not authorize` 含 **`C2 修改`**） |
| **3. Options** | **A** = `CP-A`（`current_user` 字面白名单）<br>**B** = `CP-B`（`pg_has_role … 'MEMBER'`）<br>**D** = `CP-D`（`session_user` 字面判据）<br>**E** = `CP-E`（`pg_has_role … 'USAGE'`）<br>**F** = `CP-F`（`current_user` ∧ `session_user` 合取）<br>**CUSTOM** = Human 给出判据文本 ·（`CP-C` **已排除**） |
| **4. Security Impact** | `CP-A`/`CP-D`/`CP-F`：判据**静态可读**（可直接对函数文本做字面断言），不依赖运行期成员关系 ⇒ 审计面最清晰；其中 `CP-D` 额外免疫 `SET ROLE`，`CP-F` 为两量合取（最强）。`CP-B`/`CP-E` 依赖成员链状态 ⇒ **隐含依赖不在判据文本内**，且若 `OQ-OP101-01` 未严格保证非成员则**直接失效**。**六者均不引入可伪造信号**（`§4.4` 逐项） |
| **5. Runtime Impact** | 六者**均**保持 runtime 路径判定结果**逐字不变**（`CC-2`）⇒ 对 runtime 行为**零差异**。差异仅在「以受信角色连接后 `SET ROLE` 降级」这一非 runtime 场景（`CP-D`/`CP-F` 更严） |
| **6. Migration Impact** | 六者**均需** `CREATE OR REPLACE FUNCTION` 覆盖 0007 所建函数（`CC-7`，先例 = 0 ⇒ 新先例，须独立批准）；`down_revision` 归属由 `OQ-OP101-03` 决定；**均不触及触发器状态**（`D-P13-11` 相容） |
| **7. Compatibility Impact** | 均满足 `D-P11-08`（不引入 `DEFINER`）· 均满足 `D-P13-11`（无 `DISABLE`/`ALTER TRIGGER`/临时关闭）。**关键**：`D-P13-15` 的 `Does not authorize` **明确包含「`C2 修改`」** ⇒ **C2 改写不得由 `D-P13-15` 授权**，须 Human 在本项**单独明确批准**（含 `CC-7` 新先例） |
| **8. Downgrade Impact** | 均须在降级中**复原 0007 原函数文本（逐字节）**（`CC-6`/`CC-7`）；若遗漏即构成「永久弱化 C2」，违反 `R-2 §7` 准则。降级后须逐字校验 `pg_get_functiondef` 与 0007 原文一致 |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `CP-F`（合取）或 `CP-D`（若倾向最小改动）—— 二者以**服务端双身份量**取代成员关系依赖；`CP-A` 为最简可读形态 |
| *STATUS* | **PENDING** |

---

### 6.6 `OQ-OP101-06` — 是否同时落地 `uap_readonly`

| 字段 | 内容 |
|---|---|
| **1. Question** | 本阶段是否同时落地 `CORE §13` 的 `uap_readonly`，或 DEFER？ |
| **2. Evidence** | `R-1`（§13 列出三角色）· `E-1`（0 落地）· `P10_ACCEPTANCE_MATRIX.md:132` 与 `P10_PREP_REPORT.md:268` 将三角色登记为 `ASSET`（既有文档级承诺）· `R-2 OUT-8`（本阶段仅登记为 OQ）· `infrastructure/database/health.py`（`/ready` 探针**只读** `alembic_version`，当前以 runtime 引擎执行） |
| **3. Options** | **A** = 同时落地（完整 §13）<br>**B** = DEFER（只落 `R_mig` + `R_app`）<br>**C** = CUSTOM（如仅给只读角色 `USAGE`+`SELECT` on `alembic_version` 供探针） |
| **4. Security Impact** | A：引入**第三个**最小权限主体 ⇒ 若运维/探针使用它，可避免把 runtime 角色暴露给只读消费者（降低横向面）。B：只读需求将复用到 `uap_app`（权限更宽）。C：最小额外面 |
| **5. Runtime Impact** | A/C：`/ready` 等只读路径可获得**比 runtime 更窄**的凭据。B：`/ready` 继续复用 runtime 凭据 |
| **6. Migration Impact** | A：需覆盖全部 35 表的 `SELECT` GRANT 矩阵（每个库重复，`A-5`）。B：无。C：仅一条窄 GRANT |
| **7. Compatibility Impact** | A **完整**符合 `CORE §13`；B 为**子集**落地，须以「分阶段」显式声明以免被视为偏离 §13；C 亦为子集但显式限定。三者均不违反 `D-P10-13` |
| **8. Downgrade Impact** | A：`REVOKE` 全矩阵 + `DROP ROLE`。B：无。C：`REVOKE` 一条 + `DROP ROLE` |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `B`（DEFER）—— `uap_readonly` 与「信任边界成立」正交（不影响 `INV-01…INV-08`），独立立项可避免扩大本轮裁定面 |
| *STATUS* | **PENDING** |

---

### 6.7 `OQ-OP101-07` — runtime GRANT 矩阵范围

| 字段 | 内容 |
|---|---|
| **1. Question** | `R_app` 的 GRANT 矩阵如何界定（哪些表 × 哪些动词）？是否包含 `audit_logs` / `events` 的 `INSERT`？ |
| **2. Evidence** | `D-P10-13`（`audit_logs` 的 `GRANT INSERT, SELECT` **不属 P10 交付**，登记 `OPEN-P10-1`）· `R-1`（「`audit_logs` 仅授予 `INSERT, SELECT`」）· `D-P10-11`（`audit_logs` 不可变性**由 trigger 保证、不依赖 `GRANT`**）· `E-13`（关键表 `relacl = NULL`）· `services/authorization/audit.py`（audit 写入点）· `E-15`（@0015 行数基线） |
| **3. Options** | **A** = 按运行时**实际读写面**逐表核定（须先做一次只读盘点）<br>**B** = 保守全表 DML（除审计表外）<br>**C** = 最小集（仅当前阶段运行必需表，其余后续阶段按需扩权） |
| **4. Security Impact** | A：矩阵与实际需求等宽 ⇒ 最小授权面。B：过度授权，违反最小权限精神。C：短期最小，但**后续扩权路径须每次经新决策**（否则构成"偷偷形成权限体系"，违反 `D-P10-13` 禁止项） |
| **5. Runtime Impact** | 决定 runtime 是否出现 `permission denied`：过窄 ⇒ 运行时故障（**高风险**，须以盘点证据定界）；过宽 ⇒ 安全面相悖 |
| **6. Migration Impact** | A/B/C 均需在**每个库**落地 GRANT（`A-5`）⇒ 触及迁移链与 17 个测试文件的 `0015` 引用面；且需同步 `test_authz_enforcement_migration.py` / `test_rbac_*` 等权限相关套件 |
| **7. Compatibility Impact** | 均**不违反** `D-P10-13`；A 与 `CORE §13`「最小权限」一致；`audit_logs` 需 `INSERT`（写审计）与 `SELECT`（读审计）——**具体动词组合须 Human 明确**（`D-P10-13` 原文仅述 `INSERT, SELECT`，未述 `events`） |
| **8. Downgrade Impact** | 均须 `REVOKE` 全矩阵（逐表逐动词），且 `REVOKE` 后须断言 `role_table_grants` 无残留 |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `A`（按实际读写面逐表核定）—— 可同时满足最小权限与运行时可用性，且盘点结果可机读断言 |
| *STATUS* | **PENDING** |

---

### 6.8 `OQ-OP101-08` — 「runtime 不持 DDL」是否由 DB 层强制

| 字段 | 内容 |
|---|---|
| **1. Question** | 「应用运行时不持有 DDL 权限」是否在本阶段由 **DB 层强制**（GRANT 面排除）并加正向 + 负向断言？ |
| **2. Evidence** | `R-1`（§13「应用运行时不持有 DDL 权限」）· `R-6`（§9 应用账号 `uap_app` 无 DDL）· `D-P10-13` 禁止项「不得给应用运行时 DDL 权限」· `E-12`（当前 `uap` 有 `CREATE` on `public`）· `R-2 §7`「仅写在文档的规则必须落为 `tests/architecture` 测试」（平台铁律 6） |
| **3. Options** | **A** = DB 层强制（`R_app` 非 schema owner、无对象 DDL 权限）+ **正向**断言<br>**B** = 仅文档约定（不加断言）<br>**C** = A + **负向探针**（尝试 DDL 必失败） |
| **4. Security Impact** | A/C：DDL 面在**权限层**被硬性关闭 ⇒ 即使应用代码缺陷也无法改结构（fail-closed）。B：依赖代码纪律，库内无法证明 |
| **5. Runtime Impact** | A/C：runtime 误用 DDL 会**立即失败**（可观测、可告警）。B：可能静默执行结构变更 |
| **6. Migration Impact** | A/C 需在 GRANT 落地时**不授予** schema `CREATE` 与对象所有权（并在测试中断言）；同时须确认 `MIG-3`（`env.py` 解析链）不会把 runtime DSN 误用于迁移 |
| **7. Compatibility Impact** | A/C **强化** `D-P10-13`（属落地）；B 使该禁止项停留文档层，与平台铁律 6（`DEPENDENCY_RULES` 铁律：「仅写在文档的规则必须落为测试」）张力明显 |
| **8. Downgrade Impact** | A/C：降级时 `REVOKE` 无需恢复 DDL（不回退安全属性）；须保留测试断言不被移除 |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `C`（DB 层强制 + 负向探针）—— 与平台「文档规则必须有测试」纪律一致 |
| *STATUS* | **PENDING** |

---

### 6.9 `OQ-OP101-09` — 既有 156 对象的所有权

| 字段 | 内容 |
|---|---|
| **1. Question** | 既有 **156 个对象**的所有权保持 `uap`，还是迁移至 `R_mig`？ |
| **2. Evidence** | `E-3`（`public` 156 对象 owner 全为 `uap`）· `E-5`（schema owner = `pg_database_owner`）· `M-2`（**全仓无** `OWNER TO` / `ALTER … OWNER` 先例）· `K-3`（`DROP ROLE` 要求不拥有对象）· `E-13`（`relacl = NULL`） |
| **3. Options** | **A** = 保持 `uap`（不迁移所有权）<br>**B** = 全量 `ALTER … OWNER TO R_mig`（156 对象，含索引/约束/分区附件）<br>**C** = 仅未来新建对象归 `R_mig`，历史对象保持 `uap`（双 owner 状态） |
| **4. Security Impact** | A/C：`R_app` 非 owner ⇒ 天然无对象级 DDL（支撑 `INV-05`）。B：owner 变为 `R_mig`，`R_app` 仍非 owner ⇒ 同样支撑；但 `R_mig` 成为对象 owner ⇒ 其**回收**更难（`K-3`），且若 `R_mig` 非超级用户则 owner 变更需**逐个对象**执行（面大、可出错） |
| **5. Runtime Impact** | 无直接差异（三者 `R_app` 均非 owner） |
| **6. Migration Impact** | A：**零改动**。B：需对 156 对象（含 108 索引、22 函数、35 表）逐一 `ALTER … OWNER`，且分区父/子表、序列、约束有连带要求 ⇒ 属**最大改动面**；`down_revision` 与降级对称性均须设计。C：仅新增对象带 owner，产生**不一致状态**须显式登记 |
| **7. Compatibility Impact** | 三者均无既有决策冲突；B/C 会引入「所有权随时间分层」的事实，须在文档中显式声明（否则后续 `DROP ROLE`/降级分析会误判） |
| **8. Downgrade Impact** | A：无。B：须**反向** `ALTER … OWNER` 回 `uap`（同样 156 对象）后 `DROP ROLE`，否则 `DROP ROLE` 失败（`K-3`）。C：须处理"混合所有权"下的角色回收 |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `A`（保持 `uap`）—— 所有权迁移风险高且对 `INV-01…INV-08` **无增益**（判据基于角色身份，非所有权）；`DROP ROLE` 可行性亦最佳 |
| *STATUS* | **PENDING** |

---

### 6.10 `OQ-OP101-10` — 配置 / 环境面承载双身份

| 字段 | 内容 |
|---|---|
| **1. Question** | 双身份如何在配置/环境层承载：新增键名、`alembic.ini` 硬编码的处理、compose 是否预置角色？ |
| **2. Evidence** | `FD-1`（`alembic.ini:5` 与 `config/settings.py:57` 同 DSN）· **`R-5 M-5`（`env.py::_resolve_url()` 优先级：`attributes` → **`DATABASE_URL` env** → `alembic.ini`）** · `E-12`（`.env.example` 仅 `DATABASE_URL=`，**无**分离键）· `E-11`（compose `POSTGRES_USER=uap`）· `M-7`（`tests/conftest.py:21` 默认 `DATABASE_URL = …/uap_test`）· `infrastructure/database/config.py:37`/`session.py:29`（runtime 单一引擎） |
| **3. Options** | **A** = 新增独立键（如 `MIGRATION_DATABASE_URL`）+ `env.py` 解析链显式支持该键 + `alembic.ini` 去硬编码（或明确其仅为 dev fallback）<br>**B** = 只改 runtime 侧（`settings.DATABASE_URL` 默认值 → `uap_app`），迁移沿用 `env.py` 现有链<br>**C** = 仓库零改动，由部署期注入不同值 |
| **4. Security Impact** | **B 存在实质风险**：`env.py` 会**优先取 `DATABASE_URL`** ⇒ 若 runtime 与迁移共用该键，**迁移将以 runtime 角色执行**（即 `uap_app`），届时迁移**没有** DDL/`CREATEROLE` 能力 ⇒ 要么失败、要么迫使 `uap_app` 获得高权（**直接违反** `D-P10-13`）。A：使两身份在**配置结构层**分离，可机读断言（支撑 `IC-3`）。C：分离依赖部署纪律，**不可验证** |
| **5. Runtime Impact** | A/B：runtime 凭据在配置层显式；A 允许 `R_app` 与 `R_mig` **互不泄漏**。C：runtime 可能因误注入而使用受信凭据 |
| **6. Migration Impact** | A：改动 4 处（`env.py` / `alembic.ini` / `settings.py` / `.env.example`）+ compose；须同步 `tests/integration/alembic_testkit.py`（`BASE_DSN`/`_ADMIN_DSN`）与 `tests/conftest.py`。B：改动最小但**语义错误**（见 §4）。C：无 |
| **7. Compatibility Impact** | 三者均**不违反**既有冻结；但 B **与 `IC-3`（不同配置键承载）不兼容** ⇒ 若选 B，须显式登记「`IC-3` 不成立」并说明替代证明方式。A 使 `IC-3` 可验证 |
| **8. Downgrade Impact** | A：须回退 4 处配置（且 `alembic.ini` 的硬编码恢复）；须确保回退后**不残留** `R_mig` 凭据引用。B/C：回退面小 |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `A`（新增独立键 + 显式化解析链）—— `IC-3` 要求"由不同配置键承载"，仅 A 使该条**可验证**，且修掉 `env.py` 的"runtime 变量覆盖迁移 DSN"这一实质倒置 |
| *STATUS* | **PENDING** |

---

### 6.11 `OQ-OP101-11` — 测试基建与集群级角色

| 字段 | 内容 |
|---|---|
| **1. Question** | 测试基建如何处理多角色与 **cluster 级角色**的幂等/清理？ |
| **2. Evidence** | `E-16`/`K-4`（`alembic_testkit.py:34-40` 仅 DROP/CREATE DATABASE，**不触碰角色**）· `K-1`（角色跨 4 库共享）· `M-7`（`conftest.py` 默认 DSN = `uap`/`uap_test`）· `P-3`（17 个测试文件引用 `0015_p12_indexes`；`len(revisions) == 15` 断言）· `R-2 §10 T-3` |
| **3. Options** | **A** = testkit 预置角色（幂等 `DO` 块）+ 提供**双 DSN 夹具**（runtime / migration）<br>**B** = 仅 integration 层新增角色夹具，其余套件保持 `uap`<br>**C** = 测试期不引入角色（仅单元/架构层断言函数文本与配置面） |
| **4. Security Impact** | **C 不足以**证明 `INV-01`/`INV-02`/`INV-03`/`INV-06`（需**真实双角色会话**才能证明"runtime 被拒、受信放行、伪造无效"）⇒ 与 `A-5` 八项可证性要求冲突。A：最完整。B：多角色行为**未被端到端覆盖** |
| **5. Runtime Impact** | A：未来 runtime 阶段可直接复用双凭据夹具。B/C：需补做 |
| **6. Migration Impact** | A：`alembic_testkit.py` 需支持"角色已预置"与"未预置（FAIL-CLOSED 断言触发）"两种路径；须保证 `reset_test_database()` 后角色仍在（`K-4`）⇒ 幂等责任在**夹具**。B/C：改动小 |
| **7. Compatibility Impact** | A 与 `A-5`/`OQ-OP101-13` 一致；B/C 需显式登记"可证性降级"；**均不得**改既有负向守卫的断言谓词（`R-2 §4.4 G-1/G-2`，属 `OQ-OP101-14`） |
| **8. Downgrade Impact** | A：测试结束须清理测试角色或保持幂等（**不得**删除生产命名角色）；须避免"测试残留角色"污染多库（`A-5`） |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `A`（testkit 预置 + 双 DSN 夹具）—— `A-5` 的八项测试**必须**在真实双角色会话下执行 |
| *STATUS* | **PENDING** |

---

### 6.12 `OQ-OP101-12` — downgrade 语义

| # | 字段 | 内容 |
|---|---|---|
| **1. Question** | downgrade 语义如何界定：`REVOKE` / `REASSIGN` / `DROP ROLE` 的序列、FAIL-CLOSED 边界、跨库副作用？ |
| **2. Evidence** | `K-3`（`DROP ROLE` 要求不拥有对象、不持权限）· `K-1`（角色集群级 ⇒ 跨库）· `E-10`（4 库 owner 全为 `uap`）· `A-5`（GRANT 每库独立）· `R-2 A-3`（「复原 C2 原函数文本 → 回收角色/GRANT」，否则视为永久弱化 C2）· `D-P13-12`（FAIL-CLOSED 同源纪律） |
| **3. Options** | **A** = `REVOKE` 全部授权 → 断言角色不拥有对象 → `DROP ROLE`；任一前提不成立即 `RAISE` + 整体回滚（FAIL-CLOSED）<br>**B** = 只 `REVOKE`、**保留**角色（角色存在性由环境引导另行管理）<br>**C** = CUSTOM |
| **4. Security Impact** | A：可证明「无残留受信主体」（`INV-08`）。B：`pg_roles` 中保留**空角色** ⇒ 「受信主体存在但无权限」；`INV-08` 退化为较弱不变量（须显式登记） |
| **5. Runtime Impact** | A：降级后环境与基线**完全一致**（runtime 仍可用 `uap` 或已切回）。B：留下无权限角色，后续"角色是否存在"的断言须按存在性处理 |
| **6. Migration Impact** | A：降级须覆盖**多库授权盘点**（`A-5`）——单库迁移只能回收**本库**授权，跨库残留须由运维/引导处理 ⇒ **这是跨库副作用的核心难点**。B：只需 `REVOKE` 本库授权 |
| **7. Compatibility Impact** | A 与 `A-3`/`D-P13-12` 完全一致；B 需显式登记为**较弱不变量**。二者均不违反 `D-P13-11`（均不涉及触发器状态） |
| **8. Downgrade Impact** | 本项**即**降级语义定义。关键约束：`DROP ROLE` 若失败（角色仍拥有对象或持有其它库授权）⇒ 必须 `RAISE` 而非静默跳过；**不得**使用 `DROP ROLE … ` 之外的强制手段绕过 |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `A`（FAIL-CLOSED + `DROP ROLE`）—— 与 `A-3`「回收角色/GRANT」逐字一致，且使 `INV-08` 可机读断言 |
| *STATUS* | **PENDING** |

> **格式勘误（如实披露）**：本小节表头误多一列（`# | 字段 | 内容`），不影响内容；已在 `§8` 自证偏差中登记。

---

### 6.13 `OQ-OP101-13` — 「身份隔离已成立」的机读判据

| 字段 | 内容 |
|---|---|
| **1. Question** | `D-P13-15` 的 `Purpose` 以「**前提是数据库身份隔离已经成立**」为条件；该条件的**机读判据**是什么？ |
| **2. Evidence** | `R-3`（`D-P13-15` `Purpose` 与 `Does not authorize` 逐字）· `R-2 §5.3`（`INV-01…INV-08`）· 本轮实测：`INV-01` = **不成立**（`FD-4`：单角色）· `INV-02` = **不成立**（`E-9`：runtime = 超级用户）· `INV-05` = **不成立**（`E-12`：具 `CREATE` on `public`）· `R-2 §7 A-5`（八项可证性测试） |
| **3. Options** | **A** = 判据 = `INV-01` ∧ `INV-02` ∧ `INV-05` ∧ `INV-07` ∧ `INV-08`<br>**B** = 判据 = 全部 `INV-01…INV-08`<br>**C** = 判据 = 所选拓扑落地 **且** `A-5` 八项测试全通过 |
| **4. Security Impact** | 判据越严，越能防止「在隔离未稳时推进 C2 改写」（`O-2` 的解冻条件）。A：门槛较低（可先于完整测试集成立）⇒ 存在"声明式成立"风险。C：把成立锚定在**可执行证据**上 ⇒ 最难以空口宣称 |
| **5. Runtime Impact** | 决定 P13 B-1 Amendment 何时**解冻** ⇒ 间接决定 runtime 何时获得可写 `resource_permissions` 的前提（`D-PLAT-11` 影响面） |
| **6. Migration Impact** | C 需要测试与夹具先行（`OQ-OP101-11`）⇒ 迁移链须先具备双角色能力 |
| **7. Compatibility Impact** | 三者均**不修改** `D-P13-15` 文本（其 `Purpose` 保持逐字）；区别仅在**判据严格度**。C 与 `A-5` 天然一致 |
| **8. Downgrade Impact** | 若日后回退身份隔离，`INV-*` 判据须能被重新评估（须保留可复算的断言，而非一次性人工结论） |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `C`（拓扑落地 + `A-5` 八项测试全通过）—— 把"已成立"锚定在可执行证据上，避免以文档声明代替证明 |
| *STATUS* | **PENDING** |

---

### 6.14 `OQ-OP101-14` — 既有守卫 rationale 的同步口径

| 字段 | 内容 |
|---|---|
| **1. Question** | 既有负向守卫（`G-1`/`G-2`/`G-3`）的 rationale 如何同步？属 `TEST vs DECISION` 冲突，处置口径为何？ |
| **2. Evidence** | `G-1` = `tests/architecture/test_p10_event_audit_boundary.py:225` —— `("GRANT", "OPEN-P10-1 = DEFER: the migration performs no GRANT")`，**语料 = 0013 源码**（file-scoped）<br>`G-2` = `tests/integration/test_p10_event_audit_schema.py:599-604` `test_sec2_migration_performs_no_grant`，**语料 = 0013 源码**（file-scoped）<br>`G-3` = 同文件 `:18` docstring「D-P10-13 = FROZEN  GRANT / role design = OPEN-P10-1 (DEFER)」<br>旁证：`M-3`（当前全仓可执行 `GRANT` = 0） |
| **3. Options** | **A** = **断言谓词不改**（二者只扫 0013 源码，新对象不在其语料内）；仅更新 rationale 文本（`DEFER` → "曾为 DEFER，2026-09-26 起由 `OPEN-P10-1` 承接"）<br>**B** = 断言与 rationale 均不动，改由文档附录声明"现行口径"<br>**C** = CUSTOM |
| **4. Security Impact** | 无直接安全差异；间接：陈旧 rationale 可能让人误判 `OPEN-P10-1` 仍处 DEFER，从而**遗漏**信任边界要求 |
| **5. Runtime Impact** | 无 |
| **6. Migration Impact** | A：改动 2 处字符串 + 1 处 docstring（**须先经 Human 批准**，Bot 不得自行改测试）；须以集合运算证明改动最小（`removed ⊆ {rationale 文本}`）。B：零测试改动，须在文档附录登记现行口径 |
| **7. Compatibility Impact** | A 使测试文本与现行治理状态一致；B 使测试文本成为**历史时点事实**（须由文档声明）—— 二者均**不改写任何决策**、均**不删除守卫** |
| **8. Downgrade Impact** | 无；但若选 A，后续回退时须同样更新 rationale（避免再次陈旧） |
| **9. Current Human Decision** | `______________` |
| *Recommended Direction（≠ Human Decision）* | `A`（更新 rationale、保留断言）—— 断言语义（0013 零 GRANT）**仍然有效**，仅其解释文本需随治理状态更新 |
| *STATUS* | **PENDING** |

---

## 7. 汇总与冻结条件

### 7.1 裁定状态汇总

| 编号 | 主题 | STATUS |
|---|---|---|
| `OQ-OP101-01` | 角色拓扑（`RM-A`…`RM-D`） | **PENDING** |
| `OQ-OP101-02` | migration identity 权限等级 | **PENDING** |
| `OQ-OP101-03` | revision 编号归属 | **PENDING** |
| `OQ-OP101-04` | 角色创建者 | **PENDING** |
| `OQ-OP101-05` | C2 判据形态（`CP-A`/`B`/`D`/`E`/`F`/CUSTOM） | **PENDING** |
| `OQ-OP101-06` | `uap_readonly` 是否同步落地 | **PENDING** |
| `OQ-OP101-07` | runtime GRANT 矩阵范围 | **PENDING** |
| `OQ-OP101-08` | 「不持 DDL」是否 DB 层强制 | **PENDING** |
| `OQ-OP101-09` | 156 对象所有权 | **PENDING** |
| `OQ-OP101-10` | 配置/环境面承载双身份 | **PENDING** |
| `OQ-OP101-11` | 测试基建与 cluster 级角色 | **PENDING** |
| `OQ-OP101-12` | downgrade 语义 | **PENDING** |
| `OQ-OP101-13` | 「身份隔离已成立」机读判据 | **PENDING** |
| `OQ-OP101-14` | 既有守卫 rationale 同步口径 | **PENDING** |

```text
Current Human Decision = **PENDING × 14** · FROZEN = 0 · DEFERRED = 0
```

### 7.2 冻结条件核对

| # | 冻结条件 | 当前满足 | 说明 |
|---|---|---|---|
| 1 | 14 / 14 `OQ-OP101-NN` 均已裁定 | ❌ 0 / 14 | 全部 `PENDING` |
| 2 | 无 `PENDING` 残留 | ❌ | 14 项残留 |
| 3 | 角色拓扑唯一确定 | ❌ | `RM-A`…`RM-D` 未选 |
| 4 | C2 判据唯一确定（且明确 `CC-7` 新先例是否批准） | ❌ | `OQ-OP101-05` 未裁 |
| 5 | revision 归属确定（或明确"不经 Alembic"） | ❌ | `OQ-OP101-03` 未裁 |
| 6 | `D-P13-15` 前置判据机读化 | ❌ | `OQ-OP101-13` 未裁 |
| 7 | 连带同步面口径确定（含 `TEST vs DECISION`） | ❌ | `OQ-OP101-14` 未裁 |

```text
⇒ 冻结条件满足 = **0 / 7**
⇒ `OPEN-P10-1 DECISION FREEZE WRITE = NOT PERMITTED`
⇒ 不得进入实施；`P13 B-1 Amendment` 保持挂起；`P13 IMPLEMENTATION = NOT AUTHORIZED`
```

### 7.3 解除条件

```text
① Human 填毕 §6 的 `Current Human Decision`（14 项；或给出 CUSTOM DECISION）
② 满足 §7.2 全部 7 项
③ 授权写入决策载体（新增 `D-*` 命名空间条目 + 总表 + 不变量 + 附录；`D-P10-13` 的 `OPEN-P10-1` 按规则加**指针式补注**，不改其正文）
④ 授权后方可进入 `OPEN-P10-1 IMPLEMENTATION CONTRACT`（契约轮，仍非实施）
```

---

## 8. 本轮边界与自证偏差

```text
本轮变更（全部为 `.md`，位于 `docs/architecture/`）：
  本文件 = OPEN_P10_1_DECISION_RESOLUTION.md（REVISION 2 · 字段集按 Human 指令重排）
非文档变更 = 0（migration = 0 · code = 0 · test = 0 · config = 0）
```

**自证偏差（逐条 · 如实披露）**

```text
① 两处小节表头误多一列（`OQ-OP101-04` §6.4 与 `OQ-OP101-12` §6.12 写成 `| # | 字段 | 内容 |` 而非 `| 字段 | 内容 |`）
   —— Markdown 渲染会多出一个空列；**内容无损**，已在本节登记（Harness 已按 2 列/3 列容错解析）。
② 为复验 `FD-1`…`FD-7` 与取得 `E-8`…`E-15`，本轮在一次性测试库 `uap_b1_test`（@0015）执行**只读 SELECT/计数**；
   **未执行**任何 `INSERT`/`UPDATE`/`DELETE`（`DML = 0` 保持）⇒ C2 的拒绝消息**由 `pg_get_functiondef` 读取**取得，
   **非**由 INSERT 探针触发（后者本身即属 DML）。
③ 未执行 `CREATE ROLE` / `GRANT` / `REVOKE` / `ALTER ROLE` / `session_replication_role` / `DISABLE TRIGGER`；
   仅**登记**"当前角色具备这些能力"这一既有事实（`E-9`）。
④ `uap`（formal）库实测 0 表 ⇒ schema 级实测全部在 `uap_b1_test` 完成；`uap_test` 仅 2 表（`conftest` 默认库）。
⑤ 上一轮本文件（REVISION 1）的字段布局被本轮**取代**；其内容结论（候选集、不变量、遗漏项）**全部保留**于本文件。
```

---

**END OF OPEN-P10-1 DECISION RESOLUTION（2026-09-27 · REVISION 2 · **NOT FROZEN** · Gate = `OPEN-P10-1 DECISION PREP = READY FOR HUMAN DECISION` · `PENDING × 14` · `FREEZE WRITE = NOT PERMITTED`）**
