# B1-4 PREP — Gate Report · **Revision R1**

Status: **B1-4 PREP = 设计修订完成，等待人工审查** · **B1-4 IMPLEMENTATION = BLOCKED（未进入）**
本轮性质：**纯设计修订** —— 未建表 · 未创建 0007 · 未执行 DDL/DML · 未改 0001–0006 · 未改 `env.py` · 未改代码/测试 · 未 commit/tag

---

## 1. R1 的核心更正（本轮最重要结论）

| 项 | 上一轮 | **R1 更正（以冻结原文为准）** |
|---|---|---|
| `acl_subject_types` seed | 推荐"B1-4 只 seed `user`/`role`" | **B1-4 不 seed 任何行** —— 三行属 **P13**（`STEP1B_SCHEMA_DEPENDENCY.md:193`） |
| ACL trigger G/H/I/J | 推荐"B1-4 建 G(user/role)/H/I，J 延 P09" | **B1-4 实施 0 个** —— 四个 trigger「最早可挂」冻结为 **P09 后**（`TRIGGER_INVENTORY.md:163-166`；`SCHEMA_DEPENDENCY.md:235-237`） |
| 安全性论证 | "存在 P06→P09 未验证主体窗口" | **风险不成立**：B1-4 不 seed ⇒ 注册表为空 ⇒ `subject_type_id` FK 不可满足 ⇒ ACL 行**物理不可写入** ⇒ 无伪造主体、无未注册主体 |
| 文档计数 | "10 份"与"8 份"并存（表述不一致） | **Planned = 9（用户清单）+ 1（DECISION_LOG ADR）= 10 · Existing = 10 · Missing = 0 · Unexpected = 0**（已实测） |
| untracked 计数 | 52 | **53**（上一轮 52 是 GATE 报告落盘前的瞬时快照；本轮实测清单：43 文档 + `alembic.ini` + `migrations_alembic/` + 8 测试文件） |

---

## 2. Q1 / Q2 原文级回答（用户第一节要求）

**Q1：B0 的"G/H/I/J 排 P09 之后"意味着 = A（全部必须等 P09 后）**

| 出处 | 行 | 原文 |
|---|---|---|
| `STEP1B_TRIGGER_INVENTORY.md` §1 G | 89 | `dependency \| resource_permissions + acl_subject_types + users + roles + agents → **最早 P09 后**（agents 表存在）` |
| 同上 §1 H | 101 | `dependency \| resource_permissions + acl_subject_types（P09 后）` |
| 同上 §1 I | 112 | `dependency \| resource_permissions + acl_subject_types（P09 后）` |
| 同上 §1 J | 123 | `dependency \| resource_permissions（P09 后）` |
| 同上 §2 汇总表 | 163–166 | `最早 phase` 列 = **P09 后**（G/H/I/J 四项） |
| 同上 §3 | 177 | "G/H/I/J 依赖 agents/resource_permissions 等，**均在 P09 后建**" |
| `STEP1B_SCHEMA_DEPENDENCY.md` §7 | 235 | `tg_acl_subject_exists` → **P09 之后（依赖 agents 表）** |
| 同上 §7 | 236 | `tg_acl_user_hard_delete` → 依赖 `users + resource_permissions` → **P09 后** |
| 同上 §7 | 237 | `tg_acl_role_delete_block` → 依赖 `roles + resource_permissions` → **P09 后** |
| 同上 §7 语义 | 241 | 该列 = "trigger **最早**可挂的 phase" |

**Q2（原文不精确之处，如实报告，未自行修正）**：H/I 的 `dependency` 字段**不含 `agents`**；其"P09 后"是**显式阶段冻结**，而非依赖推导结果。`TRIGGER_INVENTORY.md:177` 用"依赖 agents"概括四项，对 H/I 理由不充分。**是否提前实施属冻结文档修订事项**，须人工批准（D-B14-02 备选 B），本 PREP 不自行裁定。

---

## 3. 冻结事实核实结果（对应最终输出格式）

| 项 | 核实结论 |
|---|---|
| **G/H/I/J** | **最早可挂 = P09 后（全部四项）**；B1-4 实施 **0 个** —— 双文档一致（`TRIGGER_INVENTORY:89/101/112/123/163-166/177`；`SCHEMA_DEPENDENCY:235-237/241`） |
| **Subject Types** | CK 白名单 = `('user','role','agent')`（**无 group**，`CORE:248`）；初始 **三行** seed 属 **P13**（`SEED_STRATEGY:14/111-116`）；**B1-4 不 seed**；治理 = **平台受控注册表**（`CORE:244/249` + `ACL_STRATEGY:124-126`），运行时无写入口 |
| **Resource Tenant/Space Integrity** | `tenant_id` **NN + RESTRICT**；`space_id` **NULL 允许 + RESTRICT**；`space_id NULL` 语义 = "平台级资源或未定空间"（`CONSTRAINT_MATRIX:173`）；**冻结文档未定义** `resources` 的归属一致性约束（对比 `memberships` 在 `:155`/`CORE:162,477` 明确定义了） ⇒ **已冻结 D-B14-10 = A-1（2026-09-13）**：B1-4 引入 `tg_resources_tenant_space_consistency`（P06；structural integrity only） |
| **granted_by** | 语义 = **actor attribution（执行授权动作的人）**，**非** ACL owner（依据 `ACL_STRATEGY:115` 将其列入 audit 的 actor 组）；`ON DELETE` 原文未写 ⇒ **已冻结 D-B14-09 = A：`ON DELETE SET NULL`（2026-09-13）** |
| **action** | 冻结仅要求 **NN**（`CONSTRAINT_MATRIX` 的 `action` 仅在 NN 行），**无格式/取值约束**；action 与 permission **词表未冻结**（`SEED_STRATEGY` §4「seed 示例，B1 定稿」；`B0_GATE_REPORT`「字典清单待人工定稿」）⇒ **已冻结 D-B14-08 = A（2026-09-13）：零新增 semantic/format contract**，`action` = **opaque identifier** |

---

## 4. 本轮修订的文档（10 份，全部为 PREP 设计文档）

| 文档 | R1 变更 |
|---|---|
| `B1-4_SCOPE.md` | IN 清单移除 seed 与提前 trigger；新增 R1 修订说明与能力影响告知；§3 OPEN 列表更正为 4 项（**R4：已被冻结取代 ⇒ OPEN = 0**） |
| `B1-4_DEPENDENCY.md` | §3 重写为原文级结论（Q1 回答 + 引用行号）；新增 §3.1 "ACL 是否存在未验证主体风险 → 不存在" |
| `B1-4_SCHEMA_DESIGN.md` | §3.2/§3.3/§4.2/§4.3/§7 全部按 R1 更正（seed 移除、trigger 归零、差异表重排） |
| `B1-4_DESIGN.md` | §5 grant 前置条件；§6 冻结一致性表更新；**新增 §8 `acl_subject_types` 治理模型** |
| `B1-4_SECURITY_REVIEW.md` | 访问矩阵（注册表运行时无写路径）；§8 缺口表重写（S1 撤回 → S1' 能力空窗、新增 S7 治理） |
| `B1-4_API_DESIGN.md` | 未变更（结论仍为 0 接口） |
| `B1-4_TEST_MATRIX.md`（**变更历史；R4 后现行版本为 R4**） | §4 重写（B1-4 仅 A0 系列可执行；A1–A11 移入 P13 后）；§9 优先级更新；**R2：统一计数口径（§0）· 三分标注（【B1-4】/【后续】/【待裁定】）· `resource_permissions` 行级测试全部标注为【后续】· 新增 §5 R-ISOLATION-01…05（含 UPDATE 路径）· 新增 §8 决策依赖测试（ACT / GB / TC / REG 系列）· §11 声明未写测试代码** |
| `B1-4_MIGRATION_PLAN.md` | upgrade 步骤移除 seed、trigger 减为 1（+2 可选）〔**R4：两项均已冻结 ⇒ 最终 3 个**〕；downgrade 同步；4 处 seed 表述更正 |
| `B1-4_DECISION_LOG.md` | **全量重写**（原文级引用、2 项撤回声明、治理模型、语义裁定、P3 边界） |
| `B1-4_PREP_GATE_REPORT.md` | 本文件（R1 格式） |

**未修改任何其他文件**：`0001–0006` / `env.py` / 全部代码 / 全部测试 / B1-3 文档 / `ver.py` 等一律未触碰。

---

## 5. P3 边界：逐项 `KEEP DEFERRED`（未修复、未扩 scope）

| 项 | 判定 | 是否已违反 B1-4 安全边界 |
|---|---|---|
| P3-1 `STEP1B_B1_3_SCHEMA_REVIEW.md:191` 旧 R4 表述 | **KEEP DEFERRED** | **否** |
| P3-2 `STEP1B_SEED_STRATEGY.md:152` 漂移 | **KEEP DEFERRED** | **否** |
| P3-3 production migration mechanical guard | **KEEP DEFERRED**（登记为实施前必须复核项） | **否**（既有控制缺口）；实施时**禁止**裸 `alembic upgrade head` |
| P3-4 `audit_logs`（P10） | **KEEP DEFERRED** | **否**（B1-4 期 ACL 不可写 ⇒ 无待审计变更） |
| P3-5 `deactivate` workflow | **KEEP DEFERRED** | **否** |

---

## 6. 只读一致性扫描（本轮实测）

| 检查 | 结果 |
|---|---|
| Core → Domain = 0 | ✅（B1-4 文档中行业词汇仅出现在**否定性表述/扫描准则**中） |
| migration `create_table` | **14 = 14 existing business tables**（`0003:5 + 0004:4 + 0005:4 + 0006:1`；0006 含 `platform_state`）—— **无 B1-4 三表** ⇒ B1-4 完成后为 **17 business tables + `alembic_version` = 18 physical tables** |
| `0007` | **不存在** ✅ |
| Alembic head | `['0006_b1_3_bootstrap_state']`（单头） |
| 正式 `uap` 库 | **0 表** |
| pytest | **128 passed, 1 warning** |
| Architecture Guard | **9 passed** |
| 残留"上一轮被撤回推荐" | **0** ✅ |
| Git | HEAD `72ade9f` 未变 · 2 tags 未变 · **staged 空** · tracked 仅 2 行（pyproject/requirements，B1-0 遗留）· untracked **53** · **未 commit / 未 tag** |

---

## 7. OPEN DECISION 状态（每项：事实依据 / 问题 / 候选 / 推荐 / 理由 / 是否违反冻结 / 是否需 Human Decision）

| ID | 事实依据 | 推荐 | 是否违反冻结 | 需 Human Decision | Status |
|---|---|---|---|---|---|
| **D-B14-01** `agent` seed 时机 | `SCHEMA_DEPENDENCY:193`（P00–P10 无 seed）· `:174` P13 = Seed · `SEED_STRATEGY:14/111-116` | **B1-4 不 seed**（三行属 P13） | 否（= 冻结原文） | **否** | **RESOLVED BY FROZEN TEXT** |
| **D-B14-02** G/H/I/J phase | `TRIGGER_INVENTORY:89/101/112/123/163-166/177` · `SCHEMA_DEPENDENCY:235-237/241` | **B1-4 实施 0 个** | 否（= 冻结原文） | **否**（提前需另案批准并修订冻结文档） | **RESOLVED BY FROZEN TEXT** |
| **D-B14-08** `action` 结构 vs 词表 | `CONSTRAINT_MATRIX`（`action` 仅 NN，CK 仅有 `effect`）· `SEED_STRATEGY` §4 · `B0_GATE_REPORT`（字典待定稿） | **A：零新增 semantic/format contract**；`action` = opaque identifier；**不迁移**未来 `permissions` seed dictionary | A 否 | **已裁定（2026-09-13）** | **FROZEN — A** |
| **D-B14-09** `granted_by` 语义+删除 | `CORE` · `ACL_STRATEGY` §2/§6 · `CONSTRAINT_MATRIX` §3 | 语义 = **actor attribution**；删除 = **`ON DELETE SET NULL`** | 补齐未明示项（非改写） | **已裁定（2026-09-13）** | **FROZEN — A** |
| **D-B14-10** Resource 归属一致性 | `CONSTRAINT_MATRIX:169/173` · 对比 `CORE:162,477` + `:155` | **A-1（2026-09-13 Human Decision）：B1-4 引入 `tg_resources_tenant_space_consistency`（P06 / B1-4）；B0 三份冻结文档已同步修订（TRIGGER_INVENTORY 条目 F2 · DEPENDENCY §7 · CONSTRAINT_MATRIX §3）；G/H/I/J 保持 P09 后** | 属新增（**已批准**） | 否 | **FROZEN — A-1** |
| **D-B14-12** 注册表治理（新增） | `CORE:244/249` · `ACL_STRATEGY` §1/§7 · `CORE:248` | **platform-controlled registry + `tg_acl_subject_types_protect`**；whitelist 保持 user/role/agent | 属**新增**；**不**与 G/H/I/J 相位冲突（C2 = P06） | **已裁定（2026-09-13）** | **FROZEN — A** |
| D-B14-03/04/05/06/07 | 见 DECISION_LOG | 维持 FROZEN / defer | 否 | 否 | FROZEN |
| D-B14-11 | 见 §5 | 全部 KEEP DEFERRED | 否 | 否 | FROZEN |

**仍需人工裁定 = 0 项** —— **D-B14-08 = FROZEN — A** · **D-B14-09 = FROZEN — A** · **D-B14-10 = FROZEN — A-1** · **D-B14-12 = FROZEN — A**（均 2026-09-13）；**O-1 = FROZEN — A**（canonical total = 84）· **O-2 = FROZEN**；**O-5 = CLOSED**；D-B14-01 / 02 由冻结原文解决。**不再存在 OPEN 决策。**

---

## 8. 最终 Gate 输出

```text
==================================================
UAP STEP 1-B / B1-4 PREP REVISION R1
==================================================

Implementation: BLOCKED

P0: 0
P1: 0（原 D-B14-01 / D-B14-02 两项 P1 已由冻结原文解决，降为 RESOLVED）
P2: 0 —— D-B14-08 / 09 / 10 / 12 均已于 2026-09-13 由 Human Decision 冻结（A / A / A-1 / A）
P3: 5（B1-3 遗留 P3-1…P3-5，全部 KEEP DEFERRED）

Frozen Facts Verified:
- G/H/I/J = 最早可挂「P09 后」（全部四项，双文档一致：TRIGGER_INVENTORY:89/101/112/123/163-166/177、
  SCHEMA_DEPENDENCY:235-237/241）⇒ B1-4 实施 0 个
- Subject Types = CK 白名单 ('user','role','agent')（无 group）；三行 seed 属 P13；
  B1-4 不 seed；治理 = 平台受控注册表（运行时无写入口）
- Resource Tenant/Space Integrity = tenant_id NN+RESTRICT、space_id NULL+RESTRICT；
  归属一致性约束「B0 未定义」⇒ **已冻结 D-B14-10 = A-1（2026-09-13）**：B1-4 引入 `tg_resources_tenant_space_consistency`（P06；structural integrity only）
- granted_by = actor attribution（非 owner）；ON DELETE 原文未写 ⇒ **已冻结 D-B14-09 = A：`ON DELETE SET NULL`（2026-09-13）**
- action = 冻结仅 NN；词表未冻结 ⇒ B1-4 不得发明（默认零新增）

Open Decisions:
- D-B14-01 = RESOLVED BY FROZEN TEXT（B1-4 无 seed；三行属 P13）
- D-B14-02 = RESOLVED BY FROZEN TEXT（B1-4 实施 0 个 ACL trigger）
- D-B14-08 = FROZEN — A（零新增 semantic/format contract；`action` = opaque identifier）
- D-B14-09 = FROZEN — A（语义 = actor attribution；`ON DELETE SET NULL`）
- D-B14-10 = FROZEN — A-1（B1-4 引入 `tg_resources_tenant_space_consistency`，P06；structural integrity only）
- D-B14-12 = FROZEN — A（platform-controlled registry + `tg_acl_subject_types_protect`；whitelist 不变）

Documents:
Planned = 9（用户清单）+ 1（B1-4_DECISION_LOG.md，ADR）
Existing = 10
Missing = 0
Unexpected = 0
（第 10 份用途：承载 13 项决策的原文级依据、撤回声明与裁定材料；用户指令要求「同时更新/新增对应 ADR」）

Database:
formal uap = 0 tables
B1-4 tables = 0
0007 = absent

Migration:
head = 0006_b1_3_bootstrap_state
create_table 合计 = 14 = 14 existing business tables（0003:5 / 0004:4 / 0005:4 / 0006:1）
（B1-4 完成后目标口径：17 business tables + alembic_version = 18 physical tables）

Tests:
existing regression unchanged
128 passed
Architecture Guard 9 passed

Git:
HEAD unchanged (72ade9f)
no commit
no tag
staged = empty
tracked changes = 2 行（pyproject/requirements，B1-0 遗留）
untracked = 53

Final:

B1-4 PREP = READY FOR HUMAN REVIEW
（说明：原 P1 级争议已由冻结原文解决；剩余 4 项 P2 为「新增约束/语义补齐」，
  不阻塞 PREP 完成，但实施前须裁定）

B1-4 IMPLEMENTATION = BLOCKED
==================================================
```

---

## 9. Test Matrix R2 修订记录（本轮追加）

| 修订项 | 内容 |
|---|---|
| **计数口径统一** | 全文统一为 §0 表达式：`14 existing + 3 B1-4 = 17 business tables` `+ alembic_version = 18 physical tables`；S1 / SEC2 / M1 / M3 / M10 口径一致（M3 downgrade 后回到 14 + alembic_version = 15 physical） |
| **三分标注**（**R2-era 描述；R4 已被 O-2 = FROZEN 取代为 `Current Status` + `Post-Approval Level` 双字段**） | 每条测试标注 `【B1-4】` / `【后续】` / `【待裁定】`；`resource_permissions` 行级测试（F4–F6、C10、A1–A11、ACT-02、GB-01）**全部**标注为【后续】（B1-4 期该表不可写入） |
| **D-B14-08** | 仅保留 **ACT-01（`action IS NULL` → 拒绝，B1-4 可执行，NN 先于 FK 检查）** 与 **ACT-02（重复 UQ → 拒绝，【后续】）**；**明令禁止**任何 `read`/`write`/`create`/`update`/`delete`/`resource.read`/`resource.write` 词表测试（附冻结原文依据） |
| **D-B14-09** | 明确 `granted_by` = **actor attribution（非 owner）**；**GB-00（语义/结构断言，【B1-4】）**、**GB-01（SET NULL，【后续】—— 需先有 ACL 行，P13 后）**、**GB-02（`owner_id` SET NULL，【B1-4】）** 三条分列，**明令不得合并** |
| **D-B14-10**（**R3 已被 A-1 取代**：TC-01…04 与 R-ISOLATION-01…05 现为【B1-4】；TC-00 转为历史项）| 新增 **TC-00 = KEEP OPEN DECISION（不标 PASS）**；TC-01…TC-04 为批准后的条件测试；新增 **R-ISOLATION-01…05**，**同时覆盖 INSERT 与 UPDATE**；并声明 trigger 仅做 **structural integrity**、不做 authorization evaluation |
| **优先级重核** | P0/P1/P2/P3 按统一判定原则重列，**未人为升降级**；I4/TC-00 保留为 KNOWN OPEN DECISION |

---

## 10. 停止声明

- 未创建任何表、**未创建 0007**、未执行 DDL/DML
- 未修改 `0001–0006`、`env.py`、任何代码或测试、任何 B1-3 文档
- 未 commit、未 tag、未进入 Implementation
- **推荐方案未被当作冻结决定**：D-B14-01/02 采用**冻结原文**（非推荐）；D-B14-08/09/10/12 在裁定前均标注 **OPEN / PROPOSED**，现已由 2026-09-13 Human Decision 正式冻结（A / A / A-1 / A）
