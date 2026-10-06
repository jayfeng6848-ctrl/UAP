# OPEN-P10-1 BATCH-C · DECISION RECORD

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次                    = BATCH-C HUMAN DECISION SUBMISSION GATE（REGISTRATION）
> 提交载体                = 消息通道（优先级 B · P-6 适用：Block §3 保持空白时点快照，由本 Record 登记）
> DECISION STATUS         = SUBMITTED · VALID · REGISTERED
> 必填                    = 8/8 VALID
> 补充                    = 3/3 REGISTERED（CF-C-5/6/7 全部裁定 · 无遗留开放冲突）
> BATCH-C IMPLEMENTATION  = AUTHORIZED BUT NOT STARTED
> 下一轮                  = BATCH-C IMPLEMENTATION PRE-FLIGHT（0016 创建前单独 Gate · 不得跳过）
> 0016 / 0017             = ABSENT / ABSENT（本 Record 不创建任何迁移）
> BATCH-D                 = NOT AUTHORIZED
> ```

---

## §1 Human Raw Values（逐字保留 · 未作改写）

```text
BATCH-C START AUTHORIZATION = AUTHORIZED
CF-C-1 = 仅批准向 uap_migrator 授予 0016 所需的 schema CREATE 能力
CF-C-2 = 保持 migration identity 为 NOSUPERUSER
CF-C-3 = 保持现有 ownership，不发生 ownership transition
CF-C-4 = 延后至 BATCH-D 处理 integration / reset_test_database 冲突
CC-7 MODEL = Trusted Migration Identity Model
MIGRATION ROLE POLICY = uap_migrator-only
OWNERSHIP POLICY = Preserve Existing Ownership
CF-C-5 = Windowed Privilege + Post-Migration Revocation
CF-C-6 = 0016 Scope Strictly Limited to CC-7
CF-C-7 = CC-7 落地并验证后，才允许进入 registry / seed 后续流程
```

Human 附带约束声明（全文并入本 Record，与逐字取值同效力）：

```text
0016 MUST NOT:
- create P13 seed data
- create Agent data
- modify runtime configuration
- grant uap_app migration privileges
- introduce SECURITY DEFINER
- use application_name/GUC as trust boundary
- change ownership topology
- change BATCH-A grants
- bypass C2

OI-G-3 = 必须处理，不得标记为"无需处理"
FD-C-1 = 已实测成立
OI-BB-14 = env.py 不可直接 import
CF-C-4 = 本批不以 reset_test_database() 跑 integration suite
```

CC-7 语义模型（Human 逐字）：

```text
CC-7 采用：
current_user = 'uap_migrator'
AND
session_user = 'uap_migrator'
作为唯一受信 migration execution condition。

要求：
- 仅真实 uap_migrator execution context 被允许进入 CC-7 trusted path
- 保留既有 role assertion
- 不使用 GUC/application_name/session flag 作为信任依据
- 不使用 SECURITY DEFINER 绕过权限边界
- 不扩大到 uap_app
- 不允许 runtime identity 获得 trusted migration capability
```

CF-C-5 流程（Human 逐字）：

```text
deployment/orchestration
        ↓ grant to uap_migrator
0016 execution
        ↓ post-migration verification
revoke extra CREATE capability
        ↓ retain uap_migrator
```

总体意图（Human 逐字）：**两条边界不得合并** —— runtime `uap_app → DATABASE_URL → runtime only`；migration `uap_migrator → UAP_MIGRATION_DATABASE_URL → migration only`。

---

## §2 Parse Result（P-1 归一 + 矩阵映射登记）

> 映射性质声明：下列"矩阵映射"列为**登记推导**（registration derivation），依据 = Human 语义与 Block §2 候选文本**逐字/精确对应**，非推断补全；Human 语义与候选文本存在差异之处以 **Human raw 为准**，映射列仅作机读索引。

| # | 槽位 | P-1 归一 | 矩阵映射 | 对应依据（Block §2 候选文本） |
|---|---|---|---|---|
| 1 | `BATCH-C START AUTHORIZATION` | `AUTHORIZED` | **AUTHORIZED**（P-2 词表内） | §2.1 主开关 |
| 2 | `CF-C-1` | 仅批准向 uap_migrator 授予 0016 所需 schema CREATE | **A**（+5 项约束子句） | 候选 A = "授权对象是 uap_migrator，不触碰 uap_app 的 5 项边界 + 授权予以批准" —— 语义精确对应；Human 附加约束（不授 uap_app / 不 SUPERUSER / 不绕过 / 不改 5 grants）为**收紧**，非扩展 |
| 3 | `CF-C-2` | 保持 NOSUPERUSER（+ NOCREATEDB/NOCREATEROLE/NOREPLICATION/NOBYPASSRLS） | **A** | 候选 A = "足够（…NOSUPERUSER 无需放宽）"；"最小必要 privilege provision" = Human 明示路径 |
| 4 | `CF-C-3` | 保持现有 ownership，无 transition | **A** | 候选 A = "0016 改写不改变 owner；178/178 已终态" |
| 5 | `CF-C-4` | 延后至 BATCH-D | **C** | 候选 C = "integration 测试延后至 BATCH-D" —— **逐字对应** |
| 6 | `CC-7 MODEL` | Trusted Migration Identity Model | **CUSTOM**（P-4 满足：附完整自由文本） | 候选 A/B 为**实现形态**（内联字符串 vs `sql/` 受版本控制文件）；Human 给出的是**信任模型**（= 已冻结 `CP-F`：`current_user ∧ session_user` 合取）+ 六项要求，**未指定 A/B 形态** ⇒ 登记 `OI-DC-1`（§5） |
| 7 | `MIGRATION ROLE POLICY` | uap_migrator-only（current_user = session_user = uap_migrator） | **A** | 候选 A = "uap_migrator（经 UAP_MIGRATION_DATABASE_URL；与 OI-B-1=A 一致）"；禁 uap_app/postgres/superuser/SET ROLE = 与 A 语境一致 |
| 8 | `OWNERSHIP POLICY` | Preserve Existing Ownership | **A** | 候选 A = "维持 uap_migrator（OI-B-3=CONFIRM 的延续）"；"不引入 uap_owner" 与 RM-D 角色集一致 |
| 9 | `CF-C-5` | Windowed Privilege + Post-Migration Revocation | **B** | 候选 B = "窗口期（BATCH-C downgrade 内 REVOKE）"；Human 显式声明"与 D-OP101-12 = downgrade REVOKE + retain role 治理方向一致" |
| 10 | `CF-C-6` | 0016 Scope Strictly Limited to CC-7 | **A** | 候选 A = "仅 CC-7 改写（无新对象创建）" |
| 11 | `CF-C-7` | CC-7 落地并验证后才进入 registry/seed | **CONFIRM** | 候选 CONFIRM；P13 seed 仍被 D-PLAT-09 序列阻塞 |

**解析规则核对**：`P-1` ✓（逐字保留）· `P-2` ✓（AUTHORIZED ∈ 词表）· `P-3` ✓（映射后全部在允许值内；CUSTOM 附完整文本）· `P-4` ✓ · `P-5` 不适用（无空槽）· **`P-6` 适用**（消息通道 ⇒ Block 保持空白时点快照，本 Record 登记）· `P-7` ✓（`CF-C-1 = A`、`CF-C-2 = A`，均非 B，无附加解决路径要求）。

---

## §3 Completeness & Validation Result

```text
Completeness   = 8/8 required + 3/3 supplementary ⇒ COMPLETE
Value check    = 无空白 · 无 TBD/保持开放/见上文/采用建议/未决定 · 无多值冲突 · 无候选外新语义
                 （CC-7 MODEL 为 CUSTOM 自由文本，P-4 允许；其内含的信任条件 = 已冻结 CP-F，非新语义）
Conflict check = PASS（§4）
P-7            = PASS
⇒ DECISION STATUS = SUBMITTED · VALID · REGISTERED
```

## §4 Conflict Validation（逐项）

| # | 冲突面 | 裁定结果 | 与冻结决策关系 |
|---|---|---|---|
| 1 | schema CREATE vs BATCH-A `uap_app = 5 grants` 边界 | Human 明示：授权对象仅 `uap_migrator`，不触碰 `uap_app` 5 项边界 | 与 `OI-G-3` 现状（`uap_migrator` CREATE=false）的**改变方式 = 窗口期**（CF-C-5=B）；BATCH-A 冻结边界不受影响 |
| 2 | CF-C-5=B 窗口期 vs `D-OP101-12`（Downgrade = REVOKE and retain role） | Human 显式对齐：revoke extra CREATE、**retain `uap_migrator` 角色**、禁 `DROP ROLE` | **一致** · supersession = 0 |
| 3 | CC-7 信任条件 vs `D-OP101-04`（C2 = CP-F） | Human 采用 `current_user ∧ session_user = uap_migrator` | **与 CP-F 一致**（受信身份 = `uap_migrator`，与 `OI-B-1 = A` 一致） |
| 4 | CC-7 禁令 vs C2 永久原则 | Human 明示：无 SECURITY DEFINER / 无 GUC / 无 application_name / 无 SET ROLE workaround / runtime identity 不得获得 trusted capability | **全部一致**；`CC7-1…6` 六条件继续约束实施 |
| 5 | CF-C-6=A vs 0016/0017 归属（`D-OP101-13`） | 0016 = Trust Boundary 仅 CC-7；0017 = P13 seed 保持 | **一致** · 无归属变更 |
| 6 | CF-C-4=C vs BATCH-C Gate 验证方式 | BATCH-C 采用**独立安全验证 + 最小探针**（CLI/subprocess/DB 探针）；**不跑 integration suite / 不 reset / 不重放 ownership** | 与 `OI-BB-14`（env.py 不可 import ⇒ 只能 CLI/probe）**自洽**；19 文件 reset 冲突遗留至 BATCH-D（登记为 BATCH-D 范围，非遗漏） |
| 7 | 窗口期 GRANT 的执行身份 | Human 明示："migration privilege 由部署/编排身份在执行窗口前准备，migration 执行本身仍由 uap_migrator 完成" | 与 `D-OP101-03`（Role Creation = deployment/orchestration pre-provision）方向一致；**runbook 细节未指定** ⇒ `OI-DC-2`（§5） |
| 8 | migration/runtime 双键边界 | Human 明示两条边界不得合并 | 与 BATCH-B 冻结语义（`UAP_MIGRATION_DATABASE_URL` ↔ `settings.DATABASE_URL` 双向禁 fallback）**一致** |

## §5 OI Consumption（开放项处置台账）

| OI | 状态 | 处置 |
|---|---|---|
| `OI-G-3`（uap_migrator 无 schema CREATE） | **RESOLVED（by CF-C-1=A + CF-C-5=B）** | 窗口期授予 → 0016 执行 → 验证后 REVOKE；Record 明令不得记为"无需处理" |
| `FD-C-1` | **CONFIRMED**（Human 引用为既定事实） | schema CREATE 必要性成立，无争议 |
| `OI-BB-14`（env.py 不可直接 import） | **CARRIED（约束生效）** | 测试设计仅允许 CLI/subprocess 探针 / 独立 helper / DB 集成探针 |
| `OI-BB-11/13`（attributes["url"] 保留 / % 插值） | CARRIED | 实施时继续遵守 |
| `OI-G-1 / OI-G-2`（逐表 DML 矩阵 / 分区授权继承） | CARRIED | 非本批范围 |
| **`OI-DC-1`（新）**：CC-7 MODEL 的**实现形态**（A = 迁移文件内联字符串常量 / B = `migrations_alembic/sql/` 受版本控制文件） | **OPEN ⇒ PRE-FLIGHT 必答** | Human 裁定的是信任模型（= CP-F），A/B 形态未指定；PRE-FLIGHT 契约须提出形态并经 Human 确认后方可创建 0016 |
| **`OI-DC-2`（新）**：窗口期 GRANT/REVOKE 的 **runbook**（执行身份的具体形态、执行窗口边界、验证点、失败回滚） | **OPEN ⇒ PRE-FLIGHT 必答** | Human 已定方向（deployment/orchestration 准备 + uap_migrator 执行 + post-verification revoke）；细节由 PRE-FLIGHT 契约提出 |
| `CC-7 Gate`（此前 4/6） | **⇒ PRE-FLIGHT 重估** | 本裁定满足其前置依赖（CREATE 能力来源 + C2 改写归属确认）；六条件在 PRE-FLIGHT 逐一重估并留证据 |

## §6 CF-C-1…7 Status（总表）

```text
CF-C-1 = RESOLVED（A + 约束：仅 uap_migrator · 不触 uap_app 5 grants · 无 SUPERUSER · 无绕过角色）
CF-C-2 = RESOLVED（A：NOSUPERUSER 等 5 项属性保持 · 最小必要 privilege provision）
CF-C-3 = RESOLVED（A：无 ownership transition · 不转移 178 对象 · 不新建 owner role · 不重放 BATCH-A）
CF-C-4 = RESOLVED（C：延后 BATCH-D · 本批禁 reset/重放/临时破坏 ownership · 采用独立最小探针）
CF-C-5 = RESOLVED（B：Windowed Privilege + Post-Migration Revocation · retain role · 对齐 D-OP101-12）
CF-C-6 = RESOLVED（A：0016 仅 CC-7 · 禁 P13 seed/agents/ACL/registry/runtime logic · 0017 归属不变）
CF-C-7 = RESOLVED（CONFIRM：CC-7 落地并验证 ⇒ STOP/PASS ⇒ 之后才进入 registry/seed 后续流程）
```

## §7 Scope Derivation（由裁定导出 · 非复制旧名单）

### §7.1 IN（BATCH-C 实施允许面）

| # | 对象 | 依据 |
|---|---|---|
| 1 | 新建 `migrations_alembic/versions/0016_open_p10_1_trust_boundary.py`（30 字符 · `down_revision = 0015_p12_indexes` · filename==revision） | CF-C-6=A + `D-OP101-13` 归属 + RV-A 裁定 |
| 2 | CC-7 函数改写（替换涉及 C2 信任判据的自有函数；trust 条件 = `current_user ∧ session_user = uap_migrator`；保留既有 role assertion） | CC-7 MODEL（CUSTOM）+ MIGRATION ROLE POLICY=A |
| 3 | 窗口期 privilege provision：deployment/orchestration 身份在执行窗口前 GRANT `CREATE ON SCHEMA public TO uap_migrator`；post-migration verification 后 REVOKE；`uap_migrator` 角色保留 | CF-C-1=A + CF-C-5=B + D-OP101-12 |
| 4 | 独立安全验证与最小探针（CLI/subprocess/DB 探针；正向 + 负向；不 import env.py；不跑 integration suite；不 reset 库） | CF-C-4=C + OI-BB-14 |
| 5 | BATCH-C 证据留档（仓库外 `uap-stage3-evidence/`） | 序列惯例 |

### §7.2 OUT（禁止面 · 由裁定逐条导出）

```text
- P13 seed / 0017 / registry data / agents / agent_versions / agent_permissions / tool_executions / ACL & permission seed（CF-C-6=A · CF-C-7）
- runtime configuration 修改（env.py / settings.py / alembic.ini 的运行时面）（0016 MUST NOT）
- uap_app 授权变更 —— 保持恰 5 项（CF-C-1 约束 · 0016 MUST NOT "grant uap_app migration privileges"）
- ownership topology 变更 / 新 owner role / BATCH-A grants 变更（CF-C-3 · OWNERSHIP POLICY · 0016 MUST NOT）
- SECURITY DEFINER / GUC / application_name / session flag 信任判据 / SET ROLE workaround（CC-7 要求 · 0016 MUST NOT）
- integration suite 执行 / reset_test_database() / ownership 重放（CF-C-4=C）
- Contract / Matrix implementation sync（本批不动 · 另行授权，沿用 BATCH-B 先例）
- commit / tag / push（REQ-8 = NOT AUTHORIZED 维持 · 各自独立授权）
```

## §8 Implementation Authorization State

```text
BATCH-C IMPLEMENTATION  = AUTHORIZED BUT NOT STARTED
授权来源                = 本 Record（Human 消息通道提交 · 2026-09-27）
但本授权 ≠ 开工          = 下一轮必须先完成 BATCH-C IMPLEMENTATION PRE-FLIGHT（0016 创建前单独 Gate），
                          含：OI-DC-1（CC-7 实现形态 A/B）与 OI-DC-2（窗口期 runbook）裁定/确认 +
                          CC-7 Gate 六条件重估 + 0016 契约确认；PRE-FLIGHT 通过前 0016 = ABSENT。
0016 / 0017             = ABSENT / ABSENT
DDL / DML / ROLE / GRANT / OWNER / C2 = 0（本 Record 轮未执行任何实施动作）
COMMIT / TAG / PUSH     = 0（未授权）
BATCH-D                 = NOT AUTHORIZED
```

## §9 Registration Chain（可追溯）

```text
Request   = OPEN_P10_1_BATCH_C_EXECUTION_AUTHORIZATION_REQUEST.md（§1…§6 · Gate 86/86）
Block     = OPEN_P10_1_BATCH_C_HUMAN_DECISION_BLOCK.md（§3 保持空白时点快照 · P-6 · 新增 §6 输入登记）
Review    = OPEN_P10_1_BATCH_C_DECISION_REVIEW_REPORT.md（第一~三轮 · BLOCKED 历史 · §8.4 三硬约束已全部被本裁定处置）
Record    = 本文件（唯一现行决策权威 · 后续轮次以其为解析基准）
Gate log  = ../uap-stage3-evidence/batch_c_decision_register_gate.log（harness 独立复算）
```

**END OF OPEN-P10-1 BATCH-C DECISION RECORD（2026-09-27 · `DECISION STATUS = REGISTERED` · `BATCH-C IMPLEMENTATION = AUTHORIZED BUT NOT STARTED` · `0016 = ABSENT` · 下一轮 = `BATCH-C IMPLEMENTATION PRE-FLIGHT`）**
