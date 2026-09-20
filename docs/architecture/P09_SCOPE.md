# P09_SCOPE

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE（SCOPE FROZEN）**
**DESIGN**: **NOT STARTED** · **0011**: **ABSENT** · **IMPLEMENTATION**: NOT STARTED
**权威记录**: `P09_DECISION_LOG.md`

> 本文档只记录**已被 Human 冻结**的范围决策（`D-P09-06` / `D-P09-07` / `D-P09-08` + `D-P09-01` 的范围含义）。
> 范围之外的任何扩张均**未被授权**。

---

## 1. 阶段定位

| 项 | 依据 |
|---|---|
| P09 = Agent（含执行日志） | `STEP1B_SCHEMA_DEPENDENCY.md:170` |
| P09 表清单 | `agents` · `agent_versions` · `agent_permissions` · `tool_executions`（`SD:213`） |
| 拓扑位置 | `… P07 tool → P08 AI → P09 agent(+tool_executions+补 FK) → P10 …`（`STEP1B_B0_GATE_REPORT.md:45`） |
| 阶段性质 | **SCHEMA ONLY**（`D-P09-07` = FROZEN — A） |

---

## 2. IN SCOPE（**FROZEN**）

1. 4 张表：`agents` · `agent_versions` · `agent_permissions` · `tool_executions`
2. 上述表自身的 **PK / FK / UQ / CK / NN / NULL / DEFAULT**
3. **1 个新增对象**：`agents` 的 tenant/space **consistency trigger**（`D-P09-12` = A）
4. 索引：**8 个对象 —— 清单与命名 FROZEN（`D-P09-15` = ND-03）**；权威 = `STEP1B_INDEX_STRATEGY`
   （`CORE §12` 为不完整摘要，**不回改**）；**不额外补 FK 列索引**（FK 反查补索引归 P12）
   · 逐项清单见 `P09_SCHEMA_DESIGN.md` §2.7 / `P09_DECISION_LOG.md` §2A（`D-P09-15`）—— 本文件不重复展开
5. trigger：`tg_version_immutable`（`agent_versions`，与 `tool_versions` 共用名 → `D-B15-03 = A`）·
   `updated_at` trigger（按平台既有 `set_updated_at()` 模式）
6. **deferred FK**：`fk_agents_current_version`（`D-P09-11`）
7. revision identity：`0011_p09_agent_tool_permission`（`D-P09-09`，**只冻结 identity**）

---

## 3. OUT OF SCOPE（**FROZEN**）

| 项 | 依据 |
|---|---|
| `G/H/I/J` 四件 ACL cross-table trigger | `D-P09-06` = A · `TRIGGER_INVENTORY:200-203` · `SD:241` |
| `agent/` 代码层（runtime / registry / tools / memory / workflow） | `D-P09-07` = A |
| Agent Runtime · Agent Registry Runtime · Tool Runtime · Memory Runtime · Workflow Runtime | `D-P09-07` = A |
| HTTP API / Socket / Worker / Scheduler / Celery / 分区自动化 | `D-P09-07` = A（SCHEMA ONLY） |
| `events` / `audit_logs` | `SD:171`（P10） |
| `acl_subject_types` 的 `agent` 行 seed | `SEED_STRATEGY:111-117`（P13）· `D-B14-01 = A` |
| 任何 seed（P09 全域） | `SD:193`「P00–P10 均无 seed 需求；P13 才有 seed」 |
| AI Provider / AI Route runtime | `D-P09-07` = A |
| `tool_executions` 分区结构 | `D-P09-01` = B（**不分区**） |
| 90 天保留的**自动执行机制**（scheduler / job / extension） | `D-P09-01` 边界 + `U-1`：**`DESIGN DEFERRED`** —— retention policy/eligibility 已收敛（§2B.7），executor = **人工运维**（`D-3 = D` 先例），不属 P09 |
| `013` / P13 相关任何实现 | 阶段顺序（`SD:174`） |

---

## 4. DEFERRED

见 `P09_DECISION_LOG.md` §4（`G/H/I/J` → P09 后 / P11 · `events`/`audit_logs` → P10 · Audit 写入 → P10 ·
`agent` subject seed → P13 · `ai_request_logs.agent_id` FK → 新决策 · Agent Runtime → 未排期 ·
分区维护自动化 → 未来 operational 阶段）。

---

## 5. 阶段边界关系（事实陈述，非新决策）

```
P08（B1-6，已交付）──▶ P09（本阶段）──▶ P10（Event / Audit）
                │                      │
                │ agents.default_route_id → ai_routes.id（SET NULL）—— P09 引用 P08，方向正确
                │ ai_request_logs.agent_id = NO FK（D-P09-10）—— 无 P08 → P09 结构依赖
                └ G/H/I/J = 「P09 后」（D-P09-06）
```

---

## 6. 可追溯性（Traceability）

| OQ | 决策 | 本文件承载位置 |
|---|---|---|
| OQ-01 | `D-P09-01` | §3（不分区列入 OUT OF SCOPE 的分区结构） |
| OQ-06 | `D-P09-06` | §3 第 1 行 |
| OQ-07 | `D-P09-07` | §1（性质）+ §3（代码层 / 运行时全列） |
| OQ-08 | `D-P09-08` | `P09_DECISION_LOG.md` §1 / §6（9 份文档模式） |
| 其余 | `D-P09-02`～`D-P09-05` · `D-P09-09`～`D-P09-12` | 见对应载体文档 |
| ND-01 | `D-P09-13` | `P09_SCHEMA_DESIGN.md` §2.8 · `P09_MIGRATION_PLAN.md` §2/§3 |
| ND-02 | `D-P09-14` | `P09_SCHEMA_DESIGN.md` §2.6 · `P09_SECURITY_REVIEW.md` §3 |
| ND-03 | `D-P09-15` | 本文件 §2 第 4 项 · `P09_SCHEMA_DESIGN.md` §2.7 |
| ND-04 | `D-P09-16` | `P09_SCHEMA_DESIGN.md` §2.9 · `P09_TEST_MATRIX.md` T-23 |
| ND-05 | `D-P09-17` | `P09_DECISION_LOG.md` §4A · `P09_DEPENDENCY.md` §6 |
| ND-06 | `D-P09-18` | `P09_DECISION_LOG.md` §2A（补注清单） |

---

## 7. Gate

```
P09 SCOPE = FROZEN（IN / OUT / DEFERRED 如上；含 ND 轮 D-P09-15 与 DESIGN WRITE 轮的范围收敛）
P09 DESIGN = WRITE COMPLETE · IMPLEMENTATION = NOT STARTED · 0011 = ABSENT
未授权扩张 = 0    ·    未实现对象 = 0
IN SCOPE 设计交付 = 4 表 · 54 列 · 16 FK · 8 CK · 8 索引（1 CONSTRAINT + 3 INDEX + 4 非唯一）·
                    3 trigger · 2 function · 1 deferred FK · 0 seed（P09_SCHEMA_DESIGN.md §2B.8）
HUMAN DECISION REQUIRED = ND-A · ND-B（不阻断）
DESIGN DEFERRED = retention 自动化执行器
```
