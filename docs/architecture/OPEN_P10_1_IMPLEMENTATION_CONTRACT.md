# UAP — OPEN-P10-1 IMPLEMENTATION CONTRACT（Phase 1）

> ## 状态
>
> ```text
> 轮次        = OPEN-P10-1 IMPLEMENTATION PREP — Phase 1（READ-ONLY DESIGN · CONTRACT ONLY）
> 文档状态    = **DRAFT · NOT IMPLEMENTED · NOT FROZEN**
> 性质声明    = **Decision Freeze ≠ Implementation Authorization**
>               `OPEN-P10-1 DECISION = FROZEN` · `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED`
> 契约作用    = 把已 `FROZEN` 的 `D-OP101-01 … D-OP101-14` **逐项映射**为可实施要求 + 依赖 + 风险 + 验收证据
> 本轮未做    = 未 CREATE ROLE · 未 GRANT/REVOKE · 未 ALTER ROLE/OWNER · 未 CREATE|ALTER|DROP FUNCTION ·
>               未改 C2 · 未改 0007 · 未创建 0016/0017 · 未 DDL/DML · 未 seed INSERT ·
>               未改 runtime / env.py / settings / testkit / code · 未 alembic upgrade|downgrade · 未 commit/tag/push
> ```
>
> **本契约不做**：不新增设计（一切要求均可回溯到 `D-OP101-NN` 或本文件 §7 登记的既有事实）·
> 不代裁任何开放项（`OI-1` / `OI-2` / `R-*` 处置）· 不产生任何实施授权。
>
> **基线**：`OPEN_P10_1_IMPLEMENTATION_PREP_BASELINE_REPORT.md`（Phase 0）。
> 本文件所有事实引用均以 `B-<n>`（基线节）或 `C-<n>` / `T-<n>`（基线 §5 / §6）标注。

---

## 1. 契约范围与性质

```text
IN  ：D-OP101-01…14 的实施要求 · 逐项依赖 · 实施风险（R-01…R-08）· CC-7 Implementation Gate ·
      migration 顺序建议 · rollback 策略 · 一致性扫描与开放项登记
OUT ：任何 DDL/DML/角色操作/C2 改写/migration 创建/代码或配置修改 · 任何实施授权 ·
      对既有冻结决策的改写 · 对其他 architecture 文档的顺手修改（Human 明令禁止）
```

**四条恒定边界（贯穿全契约）**

```text
X-1  本契约不授权实施；进入实施须 Human 明确 `OPEN-P10-1 IMPLEMENTATION AUTHORIZATION = AUTHORIZED`
X-2  `D-P13-15` 的 `Does not authorize` 含「C2 修改」⇒ **C2 改写不得由本契约或 `D-OP101-05` 单独授权**
X-3  角色创建归 **deployment / orchestration / operations**（`D-OP101-04`）⇒ **迁移不创建角色**
X-4  `0016` / `0017` 的**创建**均未授权（`D-OP101-03`）
```

---

## 2. `D-OP101-NN` → Implementation 映射总表

| Decision | Implementation Impact | 主要落点（对象/文件） | 依赖 | 风险 | 验收组 |
|---|---|---|---|---|---|
| `D-OP101-01` | Role topology（`RM-D` 三层身份） | 集群角色 `uap_seed` / `uap_migrator` / `uap_app` | `D-OP101-02/04/07` | `R-01` `R-04` `IO-1` | `SEC-03` `TEST-01` |
| `D-OP101-02` | Migration identity privilege（`NOSUPERUSER`） | 角色属性；引导身份 | `D-OP101-04` | `R-02` `R-05` `OI-1` | `SEC-03` `SEC-04` |
| `D-OP101-03` | Revision ownership（`0016` 归本阶段；P13 = `0017`） | `migrations_alembic/versions/` | P13 实施契约（另轮） | `IO-2` `T-1…T-4` | `MIG-01` `MIG-02` |
| `D-OP101-04` | Role creation lifecycle（环境预置） | 编排 / bootstrap；**非**迁移 | `R-01` `D-OP101-11` | `R-01` `R-08` | `MIG-04` `TEST-01` |
| `D-OP101-05` | C2 predicate change boundary（`CP-F` + `CC-7`） | `enforce_acl_subject_types_protect()` 函数体 | `D-OP101-02/13` | `R-03` `OI-2` | `SEC-02` `SEC-05` `SEC-06` |
| `D-OP101-06` | readonly role strategy（DEFER） | **不**创建 `uap_readonly` | `IO-1` | `IO-1` | `MIG-04` `SEC-01` |
| `D-OP101-07` | runtime grant scope（最小集） | 每库 `GRANT` 矩阵 | `D-OP101-04/08` | `R-07` | `SEC-01` `RUN-02` `MIG-05` |
| `D-OP101-08` | DDL boundary enforcement（DB 层 + 正/负断言） | 权限面 + 测试 | `D-OP101-07` | `R-07` | `SEC-01` `TEST-02` |
| `D-OP101-09` | existing object ownership（全量转移） | 156 对象 `ALTER … OWNER` | `OI-1`（成员资格） | `R-04` `R-06` | `MIG-03` `MIG-02` |
| `D-OP101-10` | dual identity configuration | `env.py` · `alembic.ini` · `settings.py` · `.env.example` · compose | `R-02` | `R-02` | `RUN-01` `SEC-03` |
| `D-OP101-11` | test infrastructure（testkit + 双 DSN） | `tests/integration/alembic_testkit.py` 等 | `D-OP101-04` | `R-01` `R-08` | `TEST-01` `TEST-03` `TEST-04` |
| `D-OP101-12` | downgrade behavior（`REVOKE` + 保留角色） | migration `downgrade()` | `D-OP101-05/09` | `R-07` | `MIG-02` `MIG-07` |
| `D-OP101-13` | machine verification（拓扑落地 + 八项测试） | 验收判据本身 | `D-OP101-11` | `OI-2` | `GATE-01` `TEST-05` |
| `D-OP101-14` | existing guard rationale | `test_p10_event_audit_*` 两文件 | — | `R-08` | `TEST-06` |

---

## 3. 逐项映射（五项字段 · 逐条）

> 字段固定为：`Decision Source` / `Implementation Requirement` / `Dependencies` / `Risk` / `Acceptance Evidence`
> 「Implementation Requirement」为**要求的陈述**，非实施步骤；本契约**不给出** SQL / 代码。

### 3.1 `D-OP101-01` — 角色拓扑（`RM-D`）

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-01`（`FROZEN` · Human `ACCEPT OPTION D`） |
| **Implementation Requirement** | 建立三层受信身份：`uap_seed`（仅 registry seed 的受信 context）/ `uap_migrator`（DDL 与所有权承载）/ `uap_app`（runtime 身份）。角色**不得**由迁移或 runtime 创建（见 `D-OP101-04`）。 |
| **Dependencies** | `D-OP101-02`（三者均 `NOSUPERUSER`）· `D-OP101-04`（创建者）· `D-OP101-07`（GRANT 面）· 基线 `B-3.1`（当前仅 `uap`） |
| **Risk** | `R-01`（集群级生命周期）· `R-04`（所有权归属）· `IO-1`（第四角色超出 `CORE §13` 列举 ⇒ 设计文档口径差异） |
| **Acceptance Evidence** | `SEC-03`（身份分离可证）· `TEST-01`（角色夹具）· `MIG-04`（迁移零角色创建） |

### 3.2 `D-OP101-02` — Migration identity 权限等级（`NOSUPERUSER`）

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-02`（Human `ACCEPT OPTION A`） |
| **Implementation Requirement** | `uap_seed` / `uap_migrator` 必须 `NOSUPERUSER`（且不含 `CREATEDB`/`CREATEROLE`/`REPLICATION`/`BYPASSRLS` 的继承），仅持最小所需权限。**不得**以集群超级用户作为受信 migration context。 |
| **Dependencies** | `D-OP101-04`（谁创建角色 ⇒ 引导身份须具 `CREATEROLE`，见 `R-05`）· `OI-1`（所有权转移的成员资格前提） |
| **Risk** | `R-02`（与 runtime 身份耦合）· `R-05`（引导身份的"鸡生蛋"） |
| **Acceptance Evidence** | `SEC-03` · `SEC-04`（伪造面）· `TEST-03`（集群隔离） |

### 3.3 `D-OP101-03` — Revision 编号归属

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-03`（`CUSTOM DECISION` · 原文逐字见 PDL） |
| **Implementation Requirement** | `0016` 归属 `OPEN-P10-1 Database Trust Boundary Foundation`；P13 seed 不占用 `0016`，其 revision 为 `0017_p13_seed`（由**后续 P13 Implementation Contract** 正式登记）。**不得**在本阶段创建 `0016` 或 `0017`。 |
| **Dependencies** | P13 实施契约（另轮）；基线 `T-1…T-4`（17 个测试文件 / 链长断言 / heads 断言 / `HEAD_REVISION` 常量） |
| **Risk** | `IO-2`（既有 `0016_p13_seed` 设计记录需重映射登记）· `T-2` 链长断言 `== 15` 与 `T-3` heads 断言将被打破 ⇒ 属**强制同步面** |
| **Acceptance Evidence** | `MIG-01`（链正确且单 HEAD）· `MIG-02`（可逆）· `TEST-07`（测试同步面逐项对账） |

### 3.4 `D-OP101-04` — 角色创建者（环境预置）

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-04`（Human `ACCEPT OPTION C`） |
| **Implementation Requirement** | 角色由 **deployment / orchestration / operations** 预置（pre-provision）；迁移与 runtime **均不得**执行角色创建。 |
| **Dependencies** | `R-01`（生命周期/幂等）· `D-OP101-11`（testkit 预置）· 基线 `C-5`/`C-6`（`BASE_DSN`/`_ADMIN_DSN` 与 runtime 引擎） |
| **Risk** | `R-01`（集群级、跨库共享、`reset_test_database()` 不清理）· `R-08`（环境与迁移版本可能不同步） |
| **Acceptance Evidence** | `MIG-04`（迁移源码零 `CREATE ROLE`）· `TEST-01` · `TEST-03` |

### 3.5 `D-OP101-05` — C2 判据改动边界（`CP-F` + `CC-7`）

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-05`（`CUSTOM DECISION` · 原文逐字见 PDL；含 `CC7-1…CC7-6`） |
| **Implementation Requirement** | 未来对 C2 的改动**只允许**在 `INSERT` 分支引入 `current_user` ∧ `session_user` **合取**判据；`DELETE`/`UPDATE(key immutable)` 分支**逐字不变**；runtime 拒绝消息**逐字节一致**；且必须满足 `CC7-1…CC7-6`。 |
| **Dependencies** | `D-OP101-02`（受信身份须先存在）· `D-OP101-13`（八项测试）· §5 `CC-7 Implementation Gate` |
| **Risk** | `R-03`（**新先例**：跨迁移函数替换，先例前值 = 0；`D-P13-15` **不授权** C2 修改）· `OI-2`（八项测试中的 C2 项归属轮次未定） |
| **Acceptance Evidence** | `SEC-02` · `SEC-05`（拒绝消息逐字）· `SEC-06`（受信放行）· `SEC-07`（非 INSERT 语义不变） |

### 3.6 `D-OP101-06` — `uap_readonly` 策略（DEFER）

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-06`（Human `ACCEPT OPTION B`） |
| **Implementation Requirement** | 本阶段**不创建** `uap_readonly`、**不**为其建立任何 GRANT。 |
| **Dependencies** | `IO-1`（`CORE §13` 口径差异的登记） |
| **Risk** | `IO-1`（只读消费者将继续复用 runtime 凭据）；`CORE §13` 呈「子集落地」，须以分阶段声明避免误读 |
| **Acceptance Evidence** | `MIG-04`（角色集合恰为约定的受信 + runtime 身份）· `SEC-01` |

### 3.7 `D-OP101-07` — runtime GRANT 矩阵（最小集）

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-07`（Human `ACCEPT OPTION C`） |
| **Implementation Requirement** | 按 runtime **实际读写面**逐表核定最小 GRANT（表 × 动词），并在**每个数据库**重复落地（`GRANT` 不跨库）。 |
| **Dependencies** | `D-OP101-04`（角色须先存在）· `D-OP101-08` · **实施前置**：一次只读的运行时读写面盘点（`R-07`） |
| **Risk** | `R-07`（过窄 ⇒ runtime `permission denied`；过宽 ⇒ 违背最小权限；跨库重复） |
| **Acceptance Evidence** | `SEC-01`（runtime 无 DDL）· `RUN-02`（最小权限验证）· `MIG-05`（GRANT 落地） |

### 3.8 `D-OP101-08` — DDL 边界强制

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-08`（Human `ACCEPT OPTION C`） |
| **Implementation Requirement** | 「runtime 不持 DDL」须由 **DB 层强制**（GRANT 面排除），并同时具备**正向断言**与**负向探针**。 |
| **Dependencies** | `D-OP101-07` · `D-OP101-11`（夹具） |
| **Risk** | `R-07`（负向探针自身需执行 DDL 尝试 ⇒ 只能在一次性测试库执行） |
| **Acceptance Evidence** | `SEC-01` · `TEST-02`（负向权限测试） |

### 3.9 `D-OP101-09` — 既有 156 对象所有权

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-09`（Human `ACCEPT OPTION B`） |
| **Implementation Requirement** | 既有 **156** 对象的 owner **全量转移**至 `uap_migrator`（含索引 / 约束 / 分区附件 / 函数）。 |
| **Dependencies** | `OI-1`：**派生前置** —— 执行角色须为 `uap_migrator` 的成员（`uap_migrator` 为 `NOSUPERUSER`）⇒ 需先解决成员资格；与 `D-OP101-12`（保留角色、不 `DROP`）**相容** |
| **Risk** | `R-04`（改动面最大：35 表 / 108 索引 / 22 函数 + 分区附件）· `R-06`（成员资格前提） |
| **Acceptance Evidence** | `MIG-03`（ownership 正确）· `MIG-02`（可逆） |

### 3.10 `D-OP101-10` — 双身份配置

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-10`（Human `ACCEPT OPTION A`） |
| **Implementation Requirement** | 引入**独立键**承载 migration 身份，并**显式化** DSN 解析链；不得保留「一个变量同时决定迁移与运行时身份」的现状。 |
| **Dependencies** | `R-02`；基线 `C-1`（`env.py::_resolve_url()` 优先级）· `C-2`（`alembic.ini` 硬编码）· `C-3`（`settings.DATABASE_URL`）· `C-4`（`conftest` 默认值）· `C-7`（`.env.example` 无分离键） |
| **Risk** | `R-02`：若不显式化，迁移将跟随 runtime 身份 ⇒ 无 DDL ⇒ 失败，或反向迫使 runtime 提权（**直接违反** `D-P10-13`） |
| **Acceptance Evidence** | `RUN-01`（应用 DSN 分离）· `SEC-03`（迁移身份分离可证） |

### 3.11 `D-OP101-11` — 测试基建

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-11`（Human `ACCEPT OPTION A`） |
| **Implementation Requirement** | testkit 负责角色的**幂等预置**，并提供 runtime / migration **双 DSN 夹具**。 |
| **Dependencies** | `D-OP101-04`；基线 `T-6`（`reset_test_database()` = `DROP DATABASE … WITH (FORCE)` + `CREATE DATABASE`，**不触碰角色**）· `T-7`（回归基线 636 passed） |
| **Risk** | `R-01`（角色不随库重建消失 ⇒ 幂等责任在夹具）· `R-08`（本地集群角色泄漏/互相影响） |
| **Acceptance Evidence** | `TEST-01` · `TEST-03`（集群隔离）· `TEST-04`（双 DSN 夹具） |

### 3.12 `D-OP101-12` — Downgrade 语义

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-12`（Human `ACCEPT OPTION B`） |
| **Implementation Requirement** | 降级执行 `REVOKE`（回收授权）并**保留**集群角色；migration 的 `downgrade()` **不得** `DROP ROLE`；C2 须恢复为**对应授权前版本**。 |
| **Dependencies** | `D-OP101-05`（`CC7-5`）· `D-OP101-09` |
| **Risk** | `R-07`：单库迁移只能回收**本库**授权 ⇒ **跨库授权盘点**须由环境/运维承担 |
| **Acceptance Evidence** | `MIG-02`（可逆）· `MIG-07`（无 `DROP ROLE`）· `SEC-05`（C2 复原） |

### 3.13 `D-OP101-13` — 「身份隔离已成立」的机读判据

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-13`（Human `ACCEPT OPTION C`） |
| **Implementation Requirement** | 判据 = **拓扑落地** **且** **八项可证性测试全部通过**（可执行证据，非文档声明）。 |
| **Dependencies** | `D-OP101-11`（双角色夹具）· `D-OP101-05`（八项测试中的 C2 相关项） |
| **Risk** | `OI-2`：八项测试含 C2 的 ALLOW / 复原项，而 C2 改写须**独立授权**且按执行顺序属 **P13 B-1 Amendment** 之后 ⇒ 「OPEN-P10-1 完成时八项测试是否可达」须 Human 明确口径 |
| **Acceptance Evidence** | `GATE-01`（判据达成）· `TEST-05`（八项测试套件） |

### 3.14 `D-OP101-14` — 既有守卫 rationale 同步

| 字段 | 内容 |
|---|---|
| **Decision Source** | PDL `D-OP101-14`（Human `ACCEPT OPTION A`） |
| **Implementation Requirement** | **保留**既有断言谓词（语料为 `0013` 源码，file-scoped），仅**更新 rationale 文本**；改动须以集合运算证明最小（`removed ⊆ {rationale 文本}`）。 |
| **Dependencies** | 无 |
| **Risk** | `R-08`：改测试须 Human 批准（平台纪律：**不得自行改测试**） |
| **Acceptance Evidence** | `TEST-06`（rationale 更新且断言不变） |

---

## 4. 实施风险（**重点展开 R-01…R-04** + 登记 R-05…R-08）

### R-01 Role Lifecycle（**重点**）

```text
R-01.1  CREATE ROLE 的 cluster scope
        事实：PG 角色为集群级（基线 B-3.1）⇒ 在任一库创建即对 4 个库（postgres / uap / uap_b1_test / uap_test）可见。
        影响：角色不是"某库的对象"，不能随库迁移/回滚；角色的存在性是**全局副作用**。
        要求：`D-OP101-04` 把创建权交给环境引导 ⇒ 与库生命周期**解耦**（正确方向）。

R-01.2  多数据库一致性
        事实：角色存在性 = 全局；**GRANT = 每库独立**（对象级授权不跨库）。
        影响：任何依赖 GRANT 的要求（`D-OP101-07`/`08`）**必须逐库落地**；单库 migration 无法覆盖其余库。
        要求：实施时须为每个库定义"授权落地 + 授权盘点"两件事，且二者都可机读断言（`MIG-05`）。

R-01.3  reset_test_database() 行为
        事实（基线 T-6）：`alembic_testkit.py:34-40` = `DROP DATABASE IF EXISTS "uap_b1_test" WITH (FORCE)`
                              + `CREATE DATABASE "uap_b1_test"`；**不触碰角色**。
        影响：① 角色在库重建后**仍然存在** ⇒ 夹具不得假设"干净起点"；
              ② 若夹具创建角色，第二次运行必须**幂等**（PG 无 `CREATE ROLE IF NOT EXISTS`）；
              ③ 测试若删除角色，会影响**同一集群的其它库** ⇒ 禁止在夹具中 `DROP ROLE`（与 `D-OP101-12` 一致）。

R-01.4  DROP ROLE 条件
        事实：`DROP ROLE` 要求该角色**不拥有对象、不持权限**（且无依赖）。
        影响：`D-OP101-09`（156 对象归 `uap_migrator`）与 `D-OP101-12`（保留角色）**共同**决定：
              本阶段**不存在** `DROP ROLE` 路径 ⇒ 二者相容（`D-OP101-09` 的 owner 变更不会阻塞任何 `DROP`）。

R-01.5  幂等策略（**要求，非实现**）
        ⇒ 角色创建（环境引导）须幂等：已存在即跳过 / 校验属性一致后跳过；属性不一致须**显式失败**（不得静默沿用）。
        ⇒ 幂等的**责任方** = 环境引导（创建）+ testkit（预置）（`D-OP101-04` + `D-OP101-11`）。
        ⇒ 本契约**不给出**幂等实现（DDL 未授权）。
```

### R-02 Migration Identity 耦合（**重点**）

```text
现状（基线 C-1…C-7 · 逐字）：
        DATABASE_URL
             |
             +--> Alembic   （env.py:52 `os.environ.get("DATABASE_URL")`；优先级 2，**覆盖** alembic.ini:5 的硬编码）
             |
             +--> Runtime   （config/settings.py:57 `DATABASE_URL` 字段；infrastructure/database/config.py:37 构建引擎）

R-02.1  风险陈述
        runtime identity 与 migration identity **共用同一变量名** ⇒ 「谁是迁移」与「谁是运行时」在配置层**不可区分**。
        若仅把 runtime 侧改为 `uap_app`（`OQ-OP101-10` 的选项 B），则 env.py 会**跟随**该变量 ⇒
        迁移将以 `uap_app` 执行 ⇒ ① 无 DDL 权限 ⇒ 迁移失败；或 ② 为使迁移可行而给 `uap_app` 提权 ⇒
        **直接违反** `D-P10-13`「不得给应用运行时 DDL 权限」与 `D-OP101-08`。

R-02.2  配置隔离需求（`D-OP101-10` = A）
        ⇒ 引入**独立键**承载 migration 身份（键名由实施契约轮确定）；
        ⇒ 该键须被 env.py 的解析链**显式支持**，且**优先于** runtime 键；
        ⇒ `.env.example` 须以**空值**提供该键（保持既有安全基线：空值 fail-closed）。

R-02.3  解析优先级调整需求（**要求，非实现**）
        ⇒ 现行优先级顺序（attributes → `DATABASE_URL` → ini）**必须**被改为「migration 专用键 → attributes → ini」
          或等价形态，使**迁移身份不再可能被 runtime 变量覆盖**；
        ⇒ 该调整属 `env.py` 修改（**本轮禁止**），须在实施授权后执行，且须配套一条**可机读断言**
          （读取生效 URL 的**角色部分**，断言 ≠ runtime 角色）。

R-02.4  回滚风险
        ⇒ 若只改 runtime 键而漏改 env.py：**迁移静默以错误身份执行**（若该身份恰有权限则不会报错）⇒ 属**静默失效**风险，
          必须以断言防护（`SEC-03`）；
        ⇒ 回滚时须同时回退：独立键、env.py 解析链、`alembic.ini`、`.env.example`、compose、testkit 默认值，共 6 处；
          遗漏任一处即留下"身份可被覆盖"的残余 ⇒ 列入 `RUN-01`/`SEC-03` 的失败条件。
```

### R-03 C2 Change Boundary（**重点** · 见 §5 Gate）

```text
R-03.1  现状：C2 = unchanged（基线 B-3.3 逐字函数体）
        ⇒ `INSERT` 分支**无条件 RAISE**；无 `current_user` / `session_user` / `pg_has_role` 判据；
          触发器 `tgtype=31`（BEFORE INSERT/DELETE/UPDATE ROW）· `prosecfg=false` · `tgenabled=O`。

R-03.2  未来实施可能涉及：`CREATE OR REPLACE FUNCTION`（覆盖 `0007` 所建 C2）
        ⇒ 属**跨迁移函数替换**（先例前值 = 0）。

R-03.3  但 `D-P13-15` **不授权** C2 修改
        ⇒ 其 `Does not authorize` 逐字含「`C2 修改`」；
        ⇒ `D-OP101-05` 虽**批准** `CC-7`，但明文「该修改**不得由本 OQ 单独授权实施**，仍须经过独立 Implementation Authorization」。

R-03.4  必须建立的闸门 ⇒ **见 §5「CC-7 Implementation Gate」**（6 项条件 + 授权要求 + 证据要求）。

R-03.5  不得执行：本轮未执行任何 `CREATE|ALTER|DROP FUNCTION`；C2 与 `0007` 均未变更。
```

### R-04 Existing Ownership（**重点**）

```text
R-04.1  事实（基线 B-3.2）：`public` 共 **156** 对象（表 35 / 索引 108 / 函数 22 / 其余为约束与分区附件），
        owner **全部**为 `uap`（唯一 owner）；`pg_proc` 22 函数 owner 亦为 `uap`。

R-04.2  是否迁移 owner
        ⇒ `D-OP101-09` = **full ownership transition**（全量转移至 `uap_migrator`）
        ⇒ 转移面 = 156 对象，且须覆盖：表、索引、序列（0）、函数、以及**分区父/子表与已附加分区**的连带要求。

R-04.3  是否保留旧 owner
        ⇒ 裁定为**全量转移** ⇒ 目标态**不保留** `uap` 作为对象 owner（`uap` 仅作为集群引导/超级用户身份存在）；
        ⇒ 若实施中因故无法转移某类对象，**必须显式登记**，不得静默形成"混合所有权"（`D-OP101-09` 禁止项）。

R-04.4  是否未来对象策略
        ⇒ 转移后的**新建对象**须归 `uap_migrator`；由于角色创建已归环境引导（`D-OP101-04`），
          未来迁移的连接身份（`D-OP101-10`）决定新建对象的 owner ⇒ 与 `D-OP101-10` 强耦合。
        ⇒ ⚠️ 若"未来对象归 `uap_migrator`"而"历史对象仍归 `uap`"，即构成 `OQ-OP101-09` 的选项 C 形态 —— **本裁定未选该项** ⇒ 历史对象**必须**一并转移。

R-04.5  不得执行：本轮**未**执行任何 `ALTER … OWNER`（基线 `C-*` 与 §9 边界）。
```

### R-05 … R-08（登记 · 非重点展开）

```text
R-05  引导身份的"鸡生蛋"：`uap_seed`/`uap_migrator` 须为 `NOSUPERUSER`（`D-OP101-02`），
      但 `CREATE ROLE` 需要 `CREATEROLE` 或超级用户 ⇒ **引导身份**必须另行解决（`D-OP101-04` 的
      deployment/orchestration 侧），且该身份**不得**与 runtime 或迁移身份复用。⇒ 属实施契约须定义的前置。

R-06  所有权转移的成员资格前提：`ALTER … OWNER TO uap_migrator` 要求执行角色为 `uap_migrator` 成员
      （或在目标角色为超级用户时由超级用户执行）⇒ 见 `OI-1`。**派生于** `D-OP101-09 × D-OP101-02`。

R-07  授权面与跨库：GRANT 每库独立（R-01.2）；降级只能回收本库授权（`D-OP101-12`）
      ⇒ 须由环境/运维承担**跨库授权盘点**；负向 DDL 探针只能在一次性测试库执行。

R-08  环境/测试连带：`reset_test_database()` 不清理角色（T-6）；本地集群可能出现角色泄漏；
      改测试文件须 Human 批准（`D-OP101-14`）；测试同步面（`T-1`…`T-4`）在新增 revision 后**必然**被打破。
```

---

## 5. `CC-7 Implementation Gate`

> **性质**：这是**进入任何 C2 改写的唯一闸门**。`D-OP101-05` 批准了 `CC-7`（新先例），但**不构成**实施授权。

### 5.1 六项条件（逐字取自 `D-OP101-05` 的 `CUSTOM DECISION` 原文）

| 编号 | 条件（逐字） | 可验证方式（要求 · 非实现） |
|---|---|---|
| `CC7-1` | 触发器本身不被 `DISABLE` | 断言 `pg_trigger.tgenabled = 'O'`（BEFORE/AFTER 期间不变）；断言实施期无 `DISABLE TRIGGER` / `ALTER TRIGGER` 语句 |
| `CC7-2` | runtime identity 继续 DENY | 以 runtime 身份执行 registry `INSERT` ⇒ 拒绝；错误消息与 `0007` 原版**逐字节一致** |
| `CC7-3` | 仅受信 migration identity 获得 `INSERT` 例外 | 仅受信身份可写入；其余一切身份（含普通 SQL client）均 DENY |
| `CC7-4` | 原有非 `INSERT` 保护语义保持不变 | `DELETE` 分支与 `UPDATE`(key immutable) 分支文本**逐字不变**；行为探针与改前一致 |
| `CC7-5` | downgrade 后 C2 恢复为对应授权前版本 | `pg_get_functiondef` 与"授权前版本"**逐字节**比对 |
| `CC7-6` | 不得由本 OQ 单独授权实施；仍须经过独立 Implementation Authorization | 见 5.2 / 5.3 |

### 5.2 进入闸门所需（**全部**满足）

```text
G-CC7-1  `OPEN-P10-1` 的身份隔离**已成立**（`D-OP101-13` 判据：拓扑落地 + 八项测试全通过）
G-CC7-2  Human 明确 `OPEN-P10-1 IMPLEMENTATION AUTHORIZATION = AUTHORIZED`
G-CC7-3  Human **单独**确认本次实施**包含** C2 改写（`D-P13-15` 的 `Does not authorize` 含「C2 修改」
         ⇒ 该确认**不能**由实施授权**默示**推出，须显式）
G-CC7-4  跨迁移函数替换（覆盖 `0007` 所建对象）作为**新先例**已被 Human 明确批准（`D-OP101-05` 已批准 `CC-7` 本身）
G-CC7-5  本次改写的**授权前版本**已被逐字节记录（作为 `CC7-5` 的比对基线）
G-CC7-6  `OI-2`（八项测试中 C2 相关项的归属轮次）已由 Human 明确
```

### 5.3 本轮闸门状态

```text
CC-7 Implementation Gate = **CLOSED**
  G-CC7-1 = 未满足（隔离尚未实施）
  G-CC7-2 = 未满足（`OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED`）
  G-CC7-3 = 未满足（未收到 C2 改写的单独确认）
  G-CC7-4 = 已满足（`CC-7` 本身已批准）
  G-CC7-5 = 未满足（尚未有授权前版本记录）
  G-CC7-6 = 未满足（`OI-2` 待裁）
⇒ 本轮**不得**执行 `CREATE OR REPLACE FUNCTION`；C2 = unchanged（实测）
```

---

## 6. Migration 顺序建议 与 Rollback 策略（**登记 · 非实施**）

### 6.1 Migration 顺序建议

```text
SEQ-0  环境引导（**非迁移** · 属 deployment/orchestration/operations，`D-OP101-04`）：
         创建 `uap_seed` / `uap_migrator` / `uap_app`（全部 `NOSUPERUSER`，`D-OP101-02`）；幂等且属性校验；
         建立"引导身份 → `uap_migrator`"的成员关系（所有权转移的必要前提，见 `OI-1`）。
       ⚠️ 该步在**迁移之外** ⇒ 迁移必须能**断言**其已完成，否则 FAIL-CLOSED。

SEQ-1  授权落地（**每库** · 可在迁移内，`D-OP101-07`/`08`）：
         为 `uap_app` 建最小 GRANT（运行时读写面）；
         显式不授予任何 DDL（schema `CREATE` / 对象 `ALTER`/`DROP`）。
       ⚠️ `GRANT` 每库独立 ⇒ 每个库各自落地（R-01.2）。

SEQ-2  所有权转移（**每库** · 可在迁移内，`D-OP101-09`）：
         156 对象 owner → `uap_migrator`；含表 / 索引 / 函数 / 分区父与子表 / 约束；
         若任一对象无法转移 ⇒ **显式失败**（不得静默形成混合所有权）。

SEQ-3  连接身份分离（**非迁移** · 属配置面，`D-OP101-10`）：
         独立键 + `env.py` 解析链显式化 + `alembic.ini` / `.env.example` / compose 同步；
         配套"生效 URL 的角色断言"（R-02.3）。

SEQ-4  测试基建（**非迁移** · 属测试面，`D-OP101-11`）：
         角色幂等预置 + 双 DSN 夹具 + 集群隔离断言。

SEQ-5  C2 改写（**仅当 §5 Gate 全开** · `D-OP101-05`）：
         `CREATE OR REPLACE FUNCTION`，且必须满足 `CC7-1…CC7-6`。
       ⚠️ 按执行顺序（`D-P13-15`）：C2 改写属 **P13 B-1 Amendment**；是否纳入 OPEN-P10-1 由 `OI-2` 裁定。

SEQ-6  守卫 rationale 同步（`D-OP101-14`）：仅改 rationale 文本，断言谓词不变。

⇒ 顺序建议依据：`D-OP101-04`（角色先于授权）→ `D-OP101-07/08`（授权先于所有权转移，避免转移后无法自我修正）
  → `D-OP101-09`（所有权）→ `D-OP101-10`（身份）→ `D-OP101-11`（测试）→ `D-OP101-05`（C2，若开放）
  → `D-OP101-14`（文档化收尾）。
```

### 6.2 Rollback 策略（**登记**）

```text
RB-1  C2（若已改写）：`downgrade` **必须**复原"授权前版本"函数定义（逐字节）⇒ `CC7-5`。
      依据：`D-OP101-05` / `D-OP101-12`。
RB-2  授权：`REVOKE` 全部已授出权限；**不得** `DROP ROLE`（`D-OP101-12` 明令）。
RB-3  所有权：若已转移，回滚须**反向** `ALTER … OWNER`；反向转移同样受 `OI-1` 的成员资格前提约束。
      ⚠️ 因 `D-OP101-12` 保留角色，**不**触发 `DROP ROLE` 的对象所有权阻塞 ⇒ 反向转移是唯一回滚路径。
RB-4  角色：**保留**（不回滚角色存在性）；若需最终清除，须由环境/运维在**所有库**完成授权回收后再评估 —— 属环境面，非迁移面。
RB-5  配置（`D-OP101-10`）：回滚须覆盖 6 处（独立键 / env.py / alembic.ini / .env.example / compose / testkit 默认值），
      遗漏任一即留有"身份可被覆盖"的残余。
RB-6  FAIL-CLOSED：任何一步无法可靠判定「处于预期基线」时，`RAISE` 并整体回滚（与 `D-P13-12` 同源纪律）。
```

---

## 7. 一致性扫描（`docs/**/*.md` · 四分类）

### 7.1 扫描面与目标

```text
扫描面 = docs/ 下全部 .md（**123** 个文件；纯 Python 逐行扫描）
目标   = ① 三角色旧描述 ② `uap_readonly` 旧承诺 ③ `0016`/`0017` revision 描述 ④ OPEN-P10-1 旧状态
分类   = ACTIVE / FROZEN / DESIGN HISTORY / IMPLEMENTATION INPUT（并按实际来源细分为 6 类）
禁止   = 顺手修改历史文档（**本轮未修改任何被扫描到的历史文档**）
```

### 7.2 分类计数（**raw 命中 158**）

| 目标 | PDL `FROZEN` | PREP 现行材料 | `CORE` 设计目标 | 实施输入 / 历史阶段文档 | DESIGN HISTORY | 残差（`OTHER`） | 小计 |
|---|---|---|---|---|---|---|---|
| `S1` 三角色旧描述 | 9 | 13 | 1 | 8 | 3 | 0 | **34** |
| `S2` `uap_readonly` 旧承诺 | 16 | 21 | 1 | 5 | 3 | 0 | **46** |
| `S3` `0016`/`0017` revision 描述 | 18 | 15 | 0 | 15 | 0 | **2** | **50** |
| `S4` OPEN-P10-1 旧状态 | 6 | 16 | 0 | 6 | 0 | 0 | **28** |
| **合计** | **49** | **65** | **2** | **34** | **6** | **2** | **158** |

**分类语义（本 PREP 轮的裁决口径）**

```text
PDL `FROZEN`           = `PLATFORM_DECISION_LOG.md` 内的冻结决策正文（**权威**；本轮未改写）
PREP 现行材料           = `OPEN_P10_1_*.md`（本轮及前序 PREP/决策轮文档；**现行有效**，非陈旧陈述）
`CORE` 设计目标         = `CORE_DOMAIN_MODEL.md` §13（**目标态**；`RM-D` 为其扩展、`uap_readonly` 已 DEFER）
实施输入 / 历史阶段文档   = 各阶段 `*_IMPLEMENTATION_CONTRACT.md` / `*_MIGRATION_PLAN.md` / `*_SCHEMA_DESIGN.md` /
                        `*_DECISION_LOG.md` / `*_ACCEPTANCE_MATRIX.md` 等（**历史时点 / 实施输入**）
DESIGN HISTORY          = `STEP1A_*` / `STEP1B_*` / `B1-4_*` / `B1-5_*` / `B1-6_*` / `ER_MODEL.md` / `ARCHITECTURE.md`
残差 `OTHER`            = 2 行（见 `IO-2`）
```

### 7.3 分类为「需后续同步」的项（**只登记，不修改**）

| 编号 | 内容 | 命中行 | 性质 | 处置 |
|---|---|---|---|---|
| `IO-1` | 「三角色 + `uap_readonly` 只读」的旧陈述 | `CORE_DOMAIN_MODEL.md:1058`（`CORE` 设计目标）· `STEP1A_DESIGN_REPORT.md:442` · `STEP1B_B0_GATE_REPORT.md:98` · `STEP1B_SCHEMA_TEST_MATRIX.md:118`（DESIGN HISTORY） | **design-vs-decision delta**（`D-OP101-01` 引入第四角色 `uap_seed`；`D-OP101-06` 将 `uap_readonly` DEFER） | 由**实施契约轮**以**附录式现行口径声明**处理；**本轮未修改** |
| `IO-2` | `0016_p13_seed` 的旧编号引用 | `P13_DECISION_COMPLETION_EVIDENCE.md:231` · `P13_DECISION_FREEZE_RECORD.md:242`（P13 轮历史记录） | **编号重映射**（`D-OP101-03`：P13 seed = `0017_p13_seed`） | 由 **P13 实施契约轮**重登记；**本轮未修改** |

```text
⇒ 一致性扫描结论：**无 ACTIVE-vs-FROZEN / FROZEN-vs-FROZEN / SCHEMA-vs-DECISION 冲突**
   残余 = `IO-1`（4 行，分阶段口径差异）+ `IO-2`（2 行，编号重映射），**均已登记、均不阻塞本 PREP**
```

---

## 8. 开放项（**需 Human 裁定 · 本契约不代裁**）

| 编号 | 事项 | 依据 | 选项（不含推荐） | 影响 |
|---|---|---|---|---|
| `OI-1` | 所有权全量转移的**成员资格前提**如何解决：实施/引导身份是否须先成为 `uap_migrator` 成员（或以超级用户执行转移）？ | 派生：`D-OP101-09 × D-OP101-02`（基线 `R-06`） | (a) 引导身份临时具备成员资格（转移后回收）；(b) 由超级用户在受控窗口执行转移；(c) CUSTOM | 决定 `SEQ-0`/`SEQ-2` 的可实施性与 `RB-3` 的回滚路径 |
| `OI-2` | **C2 改写归属轮次**：八项可证性测试含 C2 的 ALLOW/复原项，而 C2 改写按执行顺序属 `P13 B-1 Amendment`；`OPEN-P10-1` 的完成判据（`D-OP101-13`）是否包含 C2 改写？ | `D-OP101-05`（`CC7-6`）· `D-OP101-13` · `D-P13-15` 执行顺序 | (a) `OPEN-P10-1` 内含 C2 改写（则 `D-OP101-13` 的"八项测试全通过"在 OPEN-P10-1 内可达）；(b) C2 改写留在 `P13 B-1 Amendment`，`D-OP101-13` 的判据分期满足（须 Human 明确分期内口径）；(c) CUSTOM | 直接决定 `GATE-01` 的可达性与 `CC-7 Gate` 的 `G-CC7-1`/`G-CC7-6` |
| `OI-3` | 独立键的**键名**与 `.env.example` 的空值语义 | `D-OP101-10`（"新增独立键"，未指定名） | (a) `MIGRATION_DATABASE_URL`；(b) `DATABASE_URL_MIGRATION`；(c) CUSTOM | 决定 `RUN-01` 的断言目标 |

---

## 9. 本轮边界与自证偏差

```text
本轮变更（全部新增 `.md`，位于 `docs/architecture/`）：
  OPEN_P10_1_IMPLEMENTATION_PREP_BASELINE_REPORT.md · OPEN_P10_1_IMPLEMENTATION_CONTRACT.md（本文件）·
  OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md
非文档变更 = 0
```

**自证偏差（逐条 · 如实披露）**

```text
① 未执行任何 DDL/DML/角色操作/函数改写/migration 创建；`alembic heads` 为只读命令；
   数据库侧仅执行 `SELECT` 类查询（`pg_roles` / `pg_class` / `pg_proc` / `pg_trigger` / `pg_auth_members` 等）。
② 基线 §4.1 登记的**命名差异**：Human 指令引用的 `OPEN_P10_1_DECISION_RECORD.md` 实为
   `OPEN_P10_1_HUMAN_DECISION_RECORD.md` ⇒ 以实际文件为准，**未重命名、未新建同义文件**。
③ `OI-1` / `OI-2` / `OI-3` 为**本契约发现的开放项**（非新设计），**本文件不代裁**，
   其中 `OI-2` 若按严格读法可能使 `D-OP101-13` 的判据在 `OPEN-P10-1` 内**不可达** ⇒ 已显式提请。
④ 一致性扫描为**纯文本机械扫描**（四分类 + 6 类细分）；`IO-1`/`IO-2` 逐行裁决后剩余 6 行，
   均**未修改**（Human 明令：禁止顺手修改历史文档）。
⑤ `R-*` 与 `SEQ-*` / `RB-*` 均为**风险与顺序登记**，不构成实施步骤；本契约**不含**任何 SQL / 代码。
```

---

**END OF OPEN-P10-1 IMPLEMENTATION CONTRACT（Phase 1 · 2026-09-27 · **DRAFT · NOT IMPLEMENTED · NOT FROZEN** · Gate = `CC-7 Implementation Gate = CLOSED` · `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED`）**
