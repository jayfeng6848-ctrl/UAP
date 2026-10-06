# OPEN-P10-1 BATCH-C EXECUTION AUTHORIZATION REQUEST

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次      = OPEN-P10-1 BATCH-C IMPLEMENTATION AUTHORIZATION PREP（STRICT READ-ONLY）
> 文件性质  = **REQUEST**（请求 · 未授权 · 未实施）
> 目标      = 把 BATCH-C（Trust Boundary / 0016 + CC-7）的开工授权摆到 Human 面前；不自行开工
> as-of 锚点 = HEAD 034ee97c… · 分支 main · tags 8 · remote none · 单头 0015_p12_indexes（15 文件）
>             PDL sha256 a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56
>             0007 sha256 9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef
>             C2 md5 6867874166ae36966763c1026ab2af19 · 触发器 31|O|0
>             roles 4 · ownership 178 / 残留 0 · uap_app 授权 5 · 正式库 uap 0 表
>             0016 / 0017 = ABSENT / ABSENT · BATCH-B FINAL = PASS（67/67）
> 有效期    = 基线若变须**重新签发**
> Gate      = batch_c_authz_request_gate.log（见 §6.4 的实测计数）
> 自证缺陷  = 真实缺口 **0** · harness 口径缺陷 **2 类 / 3 项**（见 §6.4）
> ```

---

## §1 状态声明

### §1.1 三条不得混淆

```text
① 本请求 ≠ 授权                       —— 在 §6 答复行被提供之前，BATCH-C = NOT STARTED。
② 授权 ≠ 实施完成                     —— 获授权只解除开工门槛；每步仍须按 §6 Stop Gate 留证。
③ 实施授权 ≠ 解除 C2 专项边界         —— CC-7 的改写仍受 CC7-1…6 六项条件 + D-P13-11（禁 bypass）
                                         + D-P13-15（Does not authorize 含「C2 修改」的授权路径已由
                                         OI-B-6 = B 的语义授权承载）共同约束。
```

### §1.2 当前权威状态（as-of §0 锚点）

```text
OPEN-P10-1 DECISION FREEZE     = FROZEN（D-OP101-01…14 全 FROZEN · 载体 sha 未变）
OPEN-P10-1 REVISION RESOLUTION = PASS（实际 revision = 0016_open_p10_1_trust_boundary · 30 字符）
BATCH-A                        = PASSED（角色/所有权/授权边界已落地）
BATCH-B                        = FINAL SECURITY VERIFICATION = PASS（双 DSN 分离 + env.py 角色断言）
BATCH-C                        = **NOT STARTED**（本请求对象）
BATCH-D                        = NOT AUTHORIZED
CC-7 Implementation Gate       = **6 / 6 条件满足**（详见 §3.3）—— 仅剩开工授权
OI-G-3                         = **实测仍成立**（uap_migrator 无 schema CREATE —— 本轮两探针复测）
```

### §1.3 已消费的决策与登记项（Decision consumption = 14/14 + 5 OI）

| 项 | 状态 | 本轮处置 |
|---|---|---|
| `D-OP101-01…14` | 全 `FROZEN`（14/14 · 载体 sha `a83fde5c…` 未变） | 按冻结语义消费，**不重新解释** |
| `REVISION RESOLUTION RECORD` | sha `dbee2d89…` 未变 | revision = `0016_open_p10_1_trust_boundary`（30 字符）沿用 |
| `BATCH-B DECISION RECORD` | sha `002e2509…` 未变 | 双 DSN 语义（`UAP_MIGRATION_DATABASE_URL` / `DATABASE_URL`）沿用 |
| **`OI-BB-5`** | resolved / unchanged | 无 CI carrier；本批不新建（§2.3 重申） |
| **`OI-BB-11`** | registered / unchanged | `attributes["url"]` = 程序化 override carrier；FAIL-CLOSED = 「migration 键与 attributes 均缺失」；如需"仅认 env 键"须改范围外测试，另行授权 |
| **`OI-BB-13`** | registered / unchanged | `set_main_option` 对含 `%` 的 URL 触发 configparser 插值错误 —— **对 0016 的实现形态是实际约束**（CC-7 函数体字符串不得含未转义 `%`，或须规避该路径），已计入 `CC-7 MODEL` 的裁定上下文 |
| **`OI-BB-14`** | registered / unchanged | `env.py` 不可导入 ⇒ BATCH-C 测试基建不得 import 它；测试方式候选 A/B/C 见 Block |
| **`OI-G-3`** | **实测仍成立**（本轮两探针复测） | `uap_migrator` 无 schema `CREATE` ⇒ 0016 的**必要前置**（FD-C-1 强化） |

---

## §2 执行范围（IN / OUT）

### §2.1 IN —— BATCH-C 授权覆盖

```text
Trust Boundary evaluation        —— 0016 迁移的信任边界语义落成（CC-7 C2 函数体改写）
CC-7 implementation preparation  —— 0016 迁移文件创建（含 CC-7 改写 + downgrade 复原）
required schema privilege transition —— OI-G-3 的 schema CREATE 授权过渡（方式由 §3 候选裁定）
test-infrastructure preparation  —— CF-C-4 裁定后的测试载体变更（CF-BB-S1 = B 已把 testkit/conftest
                                    归入 BATCH-C 的授权轨迹）
```

### §2.2 OUT —— 明确不在本批

```text
runtime behavior 变更 · AI gateway · ACL 逻辑 · business logic · 业务逻辑
P13 seed / 0017（即便 0016 落地后 registry 仍保持 0 行）
roles 的创建/删除/属性变更（uap_seed/uap_migrator/uap_app 三角色的**属性**不变）
uap_app 的 5 项授权边界（D-OP101-07 冻结的最小集 —— 本批**不**增删）
ownership 变更（BATCH-A 已 178/178 完成；0016 的改写不改变 owner）
C2 触发器状态变更（DISABLE/ENABLE —— CC7-2 明令触发器始终 ENABLED）
正式库 uap 的任何操作（uap = EXCLUDED）· commit · tag · push · BATCH-D
```

### §2.3 本请求不授权的面

```text
除「被授权去执行 §2.1」以外的任何变更，本请求均不授权，即使被答复为 AUTHORIZED 亦不含：
0017 创建 · P13 seed INSERT · uap_app 权限扩 · C2 触发器状态变更 · SECURITY DEFINER ·
session_replication_role · DISABLE TRIGGER · GUC/application_name/session flag 作信任判据 ·
新建 CI/CD 载体（OI-BB-5 冻结）· 正式库 uap 变更 · commit/tag/push
```

### §2.4 冲突登记册（CF-C · 与 Human Decision Block 一一对应 · 不自动解决）

| 编号 | 冲突/待裁事项 | 本轮实测 | 状态 |
|---|---|---|---|
| **`CF-C-1`** | Trust Boundary 需要的 schema CREATE 授权 vs BATCH-A 冻结的「uap_app grants = 5」 | 实测**无冲突**（授权对象是 uap_migrator；uap_app 5 项边界不动）——但属**新增授权面**，须 Human 批准 | 待裁 |
| **`CF-C-2`** | migration 执行能力 vs `uap_migrator` 的 NOSUPERUSER 等限制 | 实测**无冲突**（CREATE + 既有 ownership + USAGE 已覆盖 0016 全部 DDL；无需放宽 NOSUPERUSER） | 待裁 |
| **`CF-C-3`** | ownership transition vs ownership residual = 0 | 实测**无冲突**（0016 改写不改变 owner；178/178 已终态） | 待裁 |
| **`CF-C-4`** | integration test 执行 vs `reset_test_database()`（19 文件）摧毁 BATCH-A ownership | **真实张力**：BATCH-C 是测试基建批次，测试必须能跑，但 reset 摧毁 ownership state ⇒ 需 Human 选机制 | 待裁 |
| **`CF-C-5`** | **授权持久性**：CREATE 授权持久保留 vs 窗口期 + downgrade 回收（对齐 `D-OP101-12`） | 新发现 · 需 Human 裁定 | 待裁 |
| **`CF-C-6`** | **0016 内容边界**：仅含 CC-7 改写，还是另含 trust-boundary 对象？ | 新发现 · 需 Human 裁定 | 待裁 |
| **`CF-C-7`** | **时序**：registry 正/负探针以 CC-7 落地为前提；P13 seed 仍被序列阻塞 | 一致性确认项 | 待裁 |

---

## §3 候选结构（**仅列 · 不选择**）

### §3.1 三个候选结构

| 候选 | 结构语义 | 差异点 |
|---|---|---|
| **`CC-C-S1` 部署身份先行** | 部署/运维身份（`uap`）在 0016 执行**之前**，以显式、可审计的一次性步骤执行 `GRANT CREATE ON SCHEMA public TO uap_migrator`（记入 WHO/WHAT 台账）；0016 仅含 CC-7 改写 | 授权动作在批次序列**之外**（out-of-band ops action） |
| **`CC-C-S2` Runbook 步骤 0** | 同一授权动作，但被**形式化为 BATCH-C 脚本序列的显式 Step-0**（幂等 · 产出证据 · 失败即 STOP），随后执行 0016 | 授权动作**内嵌**于批次序列，可复跑 |
| **`CC-C-S3` 窗口期授权 + 降级回收** | 同 S1/S2 之授权，但**对齐 `D-OP101-12`**：在 BATCH-C 的 downgrade 中显式 `REVOKE CREATE ON SCHEMA public FROM uap_migrator`，使该权限只存在于迁移窗口内 | 权限**不**持久；后续批次需重新授权 |

> **约束（来自本轮实测 FD-C-1，见 §3.2）**：无论选哪个候选，「`GRANT CREATE ON SCHEMA public TO uap_migrator`」都是 0016 的**必要前置** —— 不能由 0016 自授（授权者必须持有 grant 权利，而执行者是 `uap_migrator` 本身；且 `SECURITY DEFINER` 被 CC7 明令禁止）。

### §3.2 决定性实测发现 **FD-C-1**（本轮新增 · 修正既有假设）

```text
命题：替换【自己拥有的】既有函数，是否需要 schema CREATE？
方法：事务内探针（BEGIN → SET ROLE uap_migrator → DDL → ROLLBACK ⇒ 净变更 0）
实测①  CREATE OR REPLACE FUNCTION public.uap_uuid_v7()（自有函数） ⇒ ERROR: permission denied for schema public
实测②  CREATE FUNCTION public.__probe_new_fn()（新函数）          ⇒ ERROR: permission denied for schema public
对照   探针后 total=178 · residue=0 · C2 md5 68678741…（未变）
结论   PostgreSQL 中 CREATE OR REPLACE 一个**自有**函数**仍要求** schema CREATE
       ⇒ OI-G-3 的授权对 0016（CC-7 改写）**确为必要前置**（此前 BATCH-A 报告按"创建新对象"推断，
          本轮以"替换自有函数"实测证实 —— 结论一致但证据更强）
影响   FD-C-1 使 CF-C-1 从"可选优化"变为"必要前置"，并进入 §3 三个候选结构的共同约束
```

### §3.3 CC-7 Implementation Gate（契约 §5 条件 · 本轮实测状态）

| 条件 | 内容 | 本轮实测 |
|---|---|---|
| `G-CC7-1` | 身份隔离已成立（拓扑落地 + 判据测试） | ✅ **满足**（BATCH-A 拓扑 + BATCH-B BB-S01…S08 全 PASS） |
| `G-CC7-2` | Human 明确 OPEN-P10-1 IMPLEMENTATION AUTHORIZATION = AUTHORIZED | ✅ **满足**（已收到并执行至 BATCH-B FINAL） |
| `G-CC7-3` | Human 单独确认包含 C2 改写 | ✅ **满足**（`REQ-2 = CUSTOM` + `OI-B-5 = CONFIRM` + `OI-B-6 = B` 语义授权） |
| `G-CC7-4` | 跨迁移函数替换作为新先例已被批准 | ✅ **满足**（`D-OP101-05` 批准 `CC-7`；本轮复测**全仓跨迁移替换先例仍 = 0** —— 0014 的 4 处 `CREATE OR REPLACE` 均为其**自建**函数，不构成先例） |
| `G-CC7-5` | 授权前版本已逐字节记录 | ✅ **满足**（C2 md5 `68678741…` + `c2_preauthorization_functiondef.sql` 留档） |
| `G-CC7-6` | OI-2（C2 相关测试归属轮次）已明确 | ✅ **满足**（`OI-2 = RESOLVED(a)`，CC-7 归 OPEN-P10-1） |

```text
⇒ CC-7 Implementation Gate = **6 / 6 满足** —— 唯一未决项 = 本请求的开工授权
   （先例复核为本轮增量取证：0014 的 4 处 CREATE OR REPLACE 均为其自建函数的首建，非跨迁移替换）
```

---

## §4 Validation Matrix（before / transition / after / rollback proof）

| 编号 | 项 | Before（现状） | Expected transition | After（期望终态） | Rollback proof |
|---|---|---|---|---|---|
| `V-C-1` | schema CREATE（uap_migrator） | `CREATE=false`（实测） | 按 §3 候选授予权限 | `CREATE=true`（S1/S2 持久 或 S3 窗口期） | S3：downgrade 内 `REVOKE` 后复测 `CREATE=false` |
| `V-C-2` | C2 函数体 | 逐字 = `c2_preauthorization_functiondef.sql`（md5 `68678741…`） | CC-7：INSERT 分支加入 `uap_migrator` 信任判据；其余分支逐字不变 | 函数 md5 **改变**；但 DELETE/UPDATE 分支与错误消息**逐字不变**；触发器仍 `31|O|0` + ENABLED | 0016 downgrade 将函数体复原 ⇒ md5 回到 `68678741…` |
| `V-C-3` | C2 拒绝语义 | runtime INSERT = DENY（无条件） | runtime/伪造身份仍 DENY；`uap_migrator` INSERT = **ALLOW**（受信例外） | 正/负探针矩阵通过（CC7 语义判别法：受信 context 的放行**不**等于绕过） | downgrade 后 runtime 与 migration INSERT 均 DENY（回到基线） |
| `V-C-4` | uap_app 边界 | 5 项直接授权 | **零变更** | 5 项直接授权（逐字相同） | 不适用（无变更即无需回滚） |
| `V-C-5` | ownership | 178/178 → uap_migrator | 0016 改写不改变 owner | 仍 178/178 → uap_migrator（残留 0） | 不适用 |
| `V-C-6` | revision 链 | `0015_p12_indexes`（单头） | + `0016_open_p10_1_trust_boundary` | 16 文件 · 单头 `0016…` · down_revision = `0015_p12_indexes` | `alembic downgrade 0015_p12_indexes` ⇒ 回到 15 文件语义（0016 文件按仓库纪律保留于链上，downgrade 使 DB 回到 0015 状态） |
| `V-C-7` | registry 行数 | `acl_subject_types` = 0 行 | **0 行**（0016 不 seed；P13 才 seed） | 0 行 | 不适用 |

---

## §5 Risk / Rollback

| 编号 | 风险 | 后果 | 回滚证据要求 |
|---|---|---|---|
| **`R-C-1` 角色特权回滚** | `GRANT CREATE` 扩大了 uap_migrator 的可创建面 | 窗口外仍可创建新对象（S1/S2）或窗口内失控 | S3：downgrade `REVOKE` 后的 `has_schema_privilege` 复测记录；S1/S2：显式登记"持久授权"的知情接受 |
| **`R-C-2` ownership 回滚** | 0016 若意外产生新对象（应无） | 混合 ownership | 前后 `pg_class`/`pg_proc` owner 分布比对（残留必须 = 0） |
| **`R-C-3` migration downgrade** | 0016 downgrade 须把 C2 复原到授权前语义 | 残留弱化 | downgrade 后 C2 md5 == `68678741…`（逐字节）+ 触发器 `31|O|0` |
| **`R-C-4` failed migration recovery** | 0016 中途失败（DDL 事务性 ⇒ 自动回滚） | 半改写状态 | alembic 事务性保证 + 失败后 `alembic_version` 复测（应仍 `0015_p12_indexes`）+ C2 md5 复测 |
| **`R-C-5` CC7 条件违背** | 改写意外弱化非 INSERT 分支 | 安全语义损失 | 改写前后函数体**分段比对**：DELETE/UPDATE 分支与错误消息逐字不变（仅 INSERT 分支变化） |
| **`R-C-6` 测试自毁** | integration 套件 reset 摧毁 BATCH-A ownership | 需重建 178 对象所有权 | 由 `CF-C-4` 裁定的机制承担（re-apply / 独立库 / 延后），并留证 |

---

## §6 Stop Gate

### §6.1 停止规则

```text
出现以下任一情况 ⇒ 立即 STOP：
  · new conflict（冻结决策 / 实施契约 / 实际 DB 状态之间的新矛盾）
  · scope expansion（需要触及授权清单之外的文件/对象）
  · role boundary ambiguity（角色边界语义不清）
  · ownership ambiguity（所有权语义不清）
⇒ 不得自动消解、不得顺手修复、不得进入 BATCH-D、不得自行修改冻结 Decision
```

### §6.2 完成判定（勾选表）

| 判定 | 状态 |
|---|---|
| `C-1` 0016 文件创建且 `filename == revision == 0016_open_p10_1_trust_boundary`（30 字符） | ☐ |
| `C-2` upgrade：`0015 → 0016` 单头成立 | ☐ |
| `C-3` CC-7 改写落地且 **仅** INSERT 分支变化 | ☐ |
| `C-4` 正/负探针矩阵（runtime DENY · 伪造 DENY · `uap_migrator` ALLOW · 触发器 ENABLED） | ☐ |
| `C-5` downgrade：C2 md5 回到 `68678741…` + 角色保留（`D-OP101-12`） | ☐ |
| `C-6` re-upgrade：结果与首升一致（对象哈希比对） | ☐ |
| `C-7` ownership 残留 = 0 · uap_app 5 项授权逐字不变 | ☐ |
| `C-8` 证据清单（逐文件 bytes/sha256） | ☐ |

### §6.3 暂停点

```text
C-1…C-8 全 PASS ⇒ BATCH-C = PASSED ⇒ 立即停止
等 Human 的 BATCH-D 授权（终验/回归），不得自动进入
```

### §6.4 自证缺陷（如实披露）

```text
真实缺口 = **0**（本轮无任何实施动作）

harness 口径缺陷 = **2 类 / 3 项**（详见 gate 日志）：
  ① 探针 md5 查询的 `pg_proc p` 与 `pg_namespace` join 使 `oid` 歧义 ⇒ 一次查询报错（改用无 join 查询复测）；
  ② 裸子串断言被「错误消息里的合法自引用」击穿（教训 68/74 同类）⇒ 改为否定式感知/作用域限定断言。
本轮**没有**为迁就结果修改任何受保护源码/测试载体。
```

---

**END OF OPEN-P10-1 BATCH-C EXECUTION AUTHORIZATION REQUEST（2026-09-27 · REQUEST · 未授权 · 未实施 · `BATCH-C = NOT STARTED`）**
