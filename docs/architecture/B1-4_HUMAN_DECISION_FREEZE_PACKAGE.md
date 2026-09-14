# B1-4 HUMAN DECISION FREEZE PACKAGE

Status: **Freeze 材料汇编 —— 不裁定任何决策、不实施**
依据：`B1-4_TEST_MATRIX.md`（R2）· `B1-4_DECISION_LOG.md`（R1）· `B1-4_TEST MATRIX R2 FINAL CONSISTENCY AUDIT`
本轮：**未创建/修改 migration · 未创建/修改测试代码 · 未改业务代码 · 未执行 DDL/DML · 未 commit/tag**

> **核心规则（R4 更新）**：`PROPOSED` = **候选**，**不自动升级为 FROZEN**。
> **2026-09-13 Human Decision 已冻结全部候选**：`D-B14-08 = A` · `D-B14-09 = A` · `D-B14-10 = A-1` · `D-B14-12 = A` · `O-1 = A` · `O-2 = FROZEN`；**本文件不再存在 OPEN / PROPOSED 项**（历史候选保留于各 § 供审计）。
> **R4 更新（2026-09-13）**：D-B14-08 / D-B14-09 / D-B14-12 已由 Human Decision 正式冻结为 **A**；D-B14-10 = **FROZEN — A-1**；`O-1 = FROZEN — A`（canonical total = 84）· `O-2 = FROZEN`；`O-5 = CLOSED`。**本文件不再存在 OPEN 决策。**

---

## 1. Frozen Facts（冻结前置事实，已只读复核）

| # | 事实 | 复核方式与证据 | 现状 / 交付后 |
|---|---|---|---|
| 1 | **B1-4 不 seed** | `STEP1B_SCHEMA_DEPENDENCY.md:193`（"P00-P10 均无 seed 需求；P13 才有 seed"）· `:174`（P13 = Seed） | migration 内 `INSERT INTO acl_subject_types` = **0 处** ✅ |
| 2 | **B1-4 = 0 个 ACL G/H/I/J trigger** | `TRIGGER_INVENTORY.md:89/101/112/123/163-166/177` · `SCHEMA_DEPENDENCY.md:235-237/241` | migration 内 `tg_acl_subject_exists` / `tg_acl_user_hard_delete` / `tg_acl_role_delete_block` / `tg_agent_acl_expire` = **0 处** ✅ |
| 3 | **`acl_subject_types` 当前 0 rows** | 只读查询：正式库三表存在性 = **0** | **精确表述**：B1-4 未实施 ⇒ 表**尚不存在**（故无行）；B1-4 交付后仍为 **0 rows**（不 seed） |
| 4 | **`resource_permissions` 当前不能产生合法 FK 行** | 同上 + `SCHEMA_DESIGN §3.3`（注册表空 ⇒ FK 不可满足） | **精确表述**：表尚不存在；B1-4 交付后**仍不可写入**任何行（无已注册 `subject_type_id`） |
| 5 | **action vocabulary 未冻结** | `STEP1B_CONSTRAINT_MATRIX.md:196`（`action` 仅 NN）· `:120`（语义待定）· `STEP1B_SEED_STRATEGY.md:90`（"seed 示例，B1 定稿"）· `STEP1B_B0_GATE_REPORT.md:125`（"字典清单待人工定稿"） | 全文无任何 action 取值定义 |
| 6 | **`granted_by` = actor attribution，非 owner** | `STEP1B_ACL_STRATEGY.md:115`（列入 audit 的 actor 组）· `:44`（DDL 无 ON DELETE）· `CORE_DOMAIN_MODEL.md:258` | 语义已定性；**ON DELETE 未冻结** |
| 7 | **`owner_id` 与 `granted_by` 独立处理** | `CONSTRAINT_MATRIX.md:169`（`owner_id NULL → users.id SN` = 已冻结 SET NULL） | `owner_id` = ownership（已冻结）；`granted_by` = **actor attribution**（**D-B14-09 = A FROZEN**）→ 测试分列（F3 / GB-02 vs GB-01） |
| 8 | **Tenant/Space consistency 当前 OPEN** | `CONSTRAINT_MATRIX.md:169/173`（无一致性约束）· 对比 `:155` + `CORE:162/477`（`memberships` 有） | 异租户组合**当前可成立** |
| 9 | **Subject Type Registry governance 当前 OPEN** | `CORE:244/249`（"受控的注册机制"）· `ACL_STRATEGY:124-126`（migration 驱动）· `CORE:248`（CK 白名单） | 运行时写权限未冻结 |
| 10 | **B1-4 Implementation = BLOCKED** | 正式 `uap` = **0 tables** · head = `0006_b1_3_bootstrap_state` · `0007` absent | 保持 BLOCKED |

**环境复核（只读）**：Git HEAD `72ade9f`（未变）· 2 tags · staged = 0 · untracked = 53 · 未 commit/tag

---

## 2. D-B14-08 — `resource_permissions.action`

| 项 | 内容 |
|---|---|
| **CURRENT** | **FROZEN — A（2026-09-13 Human Decision）** —— 零新增 semantic/format contract；`action` = **opaque identifier**；不新增 regex/命名空间 CHECK、enum、whitelist、vocabulary；**不迁移**未来 `permissions` seed dictionary；`ACT-03` 条件未成立 |
| **事实** | 冻结仅要求 `action` **NOT NULL**；**无格式约束、无取值约束**；action 与 `permissions.key` 的**词表与对齐规则均未冻结** |
| **必须遵守（不因裁定而改变）** | ① **NULL rejection 是结构性要求**（NN，已冻结）<br>② **不得自行创建** `read` / `write` / `create` / `update` / `delete` / `resource.read` / `resource.write` 等任何 action vocabulary<br>③ **ACT-03 是否存在取决于 Human 对候选方案的裁定** |
| **候选方案** | **A（默认，零新增）**：保持冻结现状 —— `action` 仅 NN；不加任何 CK；词表与对齐规则 defer 到 Permission Dictionary / Authorization 阶段。<br>**B（可选收紧）**：追加**结构**格式 CK（如 `^[a-z][a-z0-9_.]{1,63}$`），**不定义任何取值语义** → 该方案获批后 **ACT-03 才存在**。<br>**C（越界，明确禁止）**：在 B1-4 定义 action 词表 —— 违反"词表未冻结"。 |
| **影响** | A：零 schema 变更、零风险，但输入面较宽（脏值需应用层处理）<br>B：schema 变更 1 条 CK（属**新增约束**，需批准）；ACT-03 转为可执行（仍**不校验语义**）；若后续词表与格式不符需再迁移<br>C：不可接受 |
| **测试影响** | A：仅 ACT-01（`action IS NULL` → 拒绝，【B1-4】）+ ACT-02（重复 UQ → 拒绝，【后续】）<br>B（**未采纳**）：追加 ACT-03（非法格式拒绝）—— D-B14-08 = A ⇒ **ACT-03 条件未成立、不登记** |
| **需 Human 裁定** | 选择 **A / B**（C 禁止），并确认 ACT-03 是否纳入 |

---

## 3. D-B14-09 — `resource_permissions.granted_by`

| 项 | 内容 |
|---|---|
| **CURRENT** | **FROZEN — A（2026-09-13 Human Decision）** —— `ON DELETE SET NULL`；语义 = **actor attribution**（非 ownership）；`F3` / `GB-02`（owner_id）与 `GB-01`（granted_by）**三条分列，禁止合并** |
| **事实** | ① `granted_by` = **actor attribution**（执行授权动作的人），**不是 ACL owner**（ACL 无 owner 概念）<br>② **ON DELETE 行为未冻结** —— `ACL_STRATEGY.md:44` 的 DDL 为裸 `REFERENCES users(id)`；`CONSTRAINT_MATRIX.md:192` 与 `CORE:258` 均只写 `granted_by NULL → users.id`<br>③ `owner_id` 的 **SET NULL 已经冻结**，与 `granted_by` **分开处理**（前者 = ownership，后者 = attribution） |
| **候选方案（ON DELETE）** | **A（PROPOSED）**：`SET NULL` —— 用户最终 purge 后 ACL 行**保留**，attribution 变为 NULL；完整操作历史由 `audit_logs` 承接（**B1-4 不实现 `audit_logs`**，属 P10）<br>**B**：`RESTRICT` —— 有历史授予记录的用户不可清理<br>**C**：`CASCADE` —— **不建议**（删除历史授权 = 静默数据丢失，违反 P2-03 精神） |
| **影响** | A：需 1 条 FK 行为声明（属**补齐未明示项**，不改写语义）；GB-01 成可测<br>B：用户清理路径受阻（运维摩擦）<br>C：审计/追溯信息丢失 |
| **测试影响（已登记）** | **GB-00**（语义/结构断言，【B1-4】）· **GB-01**（SET NULL 行为，`Current Status = 【后续】` / `Post-Approval Level = —`；D-B14-09 = A 已批准，但仍需先有 ACL 行）· **GB-02 / F3**（`owner_id` SET NULL，【B1-4】，**已冻结**，**禁止与 GB-01 合并**） |
| **需 Human 裁定** | ① 确认语义 = actor attribution；② 选择 **A / B / C** |

---

## 4. D-B14-10 — Resource 的 Tenant / Space 一致性

| 项 | 内容 |
|---|---|
| **CURRENT** | **FROZEN — A-1（2026-09-13 Human Decision）** —— 已裁定：在 B1-4 引入 `tg_resources_tenant_space_consistency` |
| **冻结内容** | BEFORE INSERT **OR** UPDATE；`tenant_id` NOT NULL；`space_id` nullable；`space_id IS NOT NULL` 时要求 `spaces.tenant_id = resources.tenant_id`；Tenant-A + Tenant-A Space → ALLOW；Tenant-A + Tenant-B Space → REJECT；`space_id IS NULL` → ALLOW；**覆盖 INSERT + UPDATE**；**structural integrity only（不做 authorization evaluation）**；不引入 RLS；不引入 Domain/Agent/Tool/AI/Event/Audit 依赖 |
| **冻结文档修订（已完成本轮）** | `STEP1B_TRIGGER_INVENTORY.md` 新增条目 **F2**（earliest phase = **P06 / B1-4**）· `STEP1B_SCHEMA_DEPENDENCY.md` §7 相位表新增该行 = **P06** · `STEP1B_CONSTRAINT_MATRIX.md` §3 `resources` 增 **TRIGGER** 行（标注 structural integrity only）。**G/H/I/J 的「P09 后」未改动、既有相位未重排** |
| **事实** | `resources.tenant_id` = **NOT NULL**（`CONSTRAINT_MATRIX:169`）· `resources.space_id` = **nullable**（`space_id NULL` = "平台级资源或未定空间"，`:173`）<br>**当前可能出现**：`resources.tenant_id = Tenant-A` 且 `resources.space_id ∈ Tenant-B 的 Space` ⇒ **该状态目前不应被写成 PASS**<br>冻结文档**未**为 `resources` 定义归属一致性约束（对比 `memberships` 在 `:155` / `CORE:162,477` 明确定义了 `tenant_id = spaces.tenant_id`） |
| **候选方案** | **A（PROPOSED）**：B1-4 内新增 `tg_resources_tenant_space_consistency`（BEFORE INSERT **OR** UPDATE）—— 拒绝 `resources.tenant_id ≠ spaces.tenant_id` 的组合；仅依赖 B1-4 自身对象与既有 `spaces` 表，**不违反 G/H/I/J 的 P09 相位约束**<br>**B**：DB 原生复合 FK `resources (space_id, tenant_id) → spaces (id, tenant_id)` —— 需给 **B1-2 已冻结的 `spaces` 增加 `UNIQUE (id, tenant_id)`** ⇒ **修改已冻结表结构**，代价最高<br>**C（= 当前冻结现状）**：仅应用层保证，DB 无强制 ⇒ 保留跨租户归属错配风险 |
| **结构性影响** | A：+1 trigger +1 function（downgrade 需一并移除）；`space_id IS NULL` 一律放行；`space_id` 非空时必须匹配<br>B：最"DB-native"，但触碰 B1-2 冻结结构<br>C：零变更，但隔离依赖应用层不遗漏 |
| **必须明确的职责边界** | 任何最终采用的 trigger **只承担 structural integrity**（拒绝非法归属组合）；**不承担 authorization evaluation**（授权判定仍全部在 Authorization Layer；DB 不做授权解释） |
| **测试影响（已登记）** | **TC-00 = KNOWN OPEN DECISION 已由 A-1 关闭（历史项）**；**已随 A-1 FROZEN 升为【B1-4】**：**TC-01/02/03**（INSERT 路径）+ **R-ISOLATION-01/02**（INSERT）+ **R-ISOLATION-03/04/05**（**UPDATE 路径**）+ **TC-04** ⇒ **INSERT 与 UPDATE 双路径必须同时覆盖** |
| **需 Human 裁定** | ✅ **已裁定：A-1**（2026-09-13） |

---

## 5. D-B14-12 — Subject Type Registry 治理

| 项 | 内容 |
|---|---|
| **CURRENT** | **FROZEN — A（2026-09-13 Human Decision）** —— **platform-controlled registry + protection mechanism**（`tg_acl_subject_types_protect`）；whitelist 保持 `user`/`role`/`agent`；**registry governance only，不演变为 Domain authorization**；B0 三份文档（条目 **C2** / §7 / §3）已同步 |
| **事实** | ① `acl_subject_types` = **平台受控 registry**（`CORE:244`"受控的注册机制"；`:249`"插一行注册 + 写 trigger 验证"；`ACL_STRATEGY:124-126` 的 `group` 路径为 migration 驱动）<br>② 现有 whitelist = **`user` / `role` / `agent`**（CK；**无 `group`**，P2-02）<br>③ **B1-4 不 seed**（三行属 P13）<br>④ **未冻结**：运行时写权限、是否允许 Domain / Plugin 自行注册 |
| **候选治理方式** | **A（FROZEN — 2026-09-13 Human Decision）**：**平台受控 + 机械护栏** —— B1-4 新增 `tg_acl_subject_types_protect`（BEFORE INSERT OR UPDATE OR DELETE）：拒绝运行时 INSERT、`key` 不可变、禁物理 DELETE（退役走 `archived_at`）；仅依赖本表，**不违反 G/H/I/J 相位**<br>**B（= 现状）**：仅靠 CK 白名单 + 文档约定，不建 trigger（运行时理论上仍可 INSERT 白名单内的 key 值）<br>**C（越界，本阶段不做）**：定义 Plugin / Domain 注册 API —— 超出 B1-4 scope |
| **影响** | A（**已批准**）：+1 trigger（属新增约束）；关闭"任意模块注册类型 ⇒ 授权层不知如何验证"的路径<br>B：零变更；依赖纪律与审查<br>C：不可在本阶段做 |
| **与其它决策的关系** | 与 D-B14-01/02 结论一致：注册表为空 ⇒ ACL 不可写；A 进一步把"谁能注册"从纪律变为**机制** |
| **测试影响（已登记）** | **REG-01**（运行时 INSERT 拒绝）· **REG-02**（`key` UPDATE 拒绝 / `description` 允许）· **REG-03**（DELETE 拒绝）—— 均随 **D-B14-12 = A** 升为【B1-4】 |
| **需 Human 裁定** | 选择 **A / B**（C 不在本阶段） |

---

## 6. O-1～O-4 文档决策（R4 状态更新：O-1 / O-2 已 FROZEN；O-3 / O-4 保持 P3）

| # | 问题（来自 R2 Final Audit） | 最小修订方案（候选） | 需 Human 裁定 |
|---|---|---|---|
| ~~**O-1**~~ | 原：正文无显式 canonical total | **✅ FROZEN — A（2026-09-13）：Canonical Total = 84**（71 基础七类 + 13 §8 表格行）；`ACT-03` = **conditional / non-canonical（不计入）**；`D1–D7` 不计入。已在 TEST_MATRIX §0.2 落地 | **已裁定** |
| ~~**O-2**~~ | 原：双标注违反"一测试一状态"（**R3 审计复核后实际仅 2 处**：`GB-01` / `REG-01`；`R-ISOLATION-01` 已随 A-1 单标注化） | **✅ FROZEN（2026-09-13）：采用 `Current Status` + `Post-Approval Level` 双字段模型**；`Current Status` 每条唯一，禁止同字段双 `【…】`；已批准或无需批准时 `Post-Approval Level = —`。已在 TEST_MATRIX 状态模型节落地 | **已裁定** |
| **O-3** | §5 表格行序：`I5` 排在 `R-ISOLATION-05` 之后 | 将 `I5` 行上移至 `I4` 之后（或把 R-ISOLATION 系列整体置于 I 系列之后并重排编号；**不改变任何编号含义**） | 确认（纯排版） |
| **O-4** | §10 登记项 `D1–D7`（7 行）**无三分标注** | 保持其**矩阵外登记项**地位（不参与三分状态计数）；在 §0 或 §10 增加一句显式声明："D1–D7 为后续阶段登记，不参与测试计数与三分状态统计" | 确认该定位 |

---

## 7. Implementation Blocking Conditions（实施解除条件）

| # | 阻塞条件 | 类型 | 状态 |
|---|---|---|---|
| ~~B-1~~ | ~~**D-B14-08** 未裁定~~ | 设计裁定 | ✅ **CLOSED（FROZEN — A，2026-09-13）** |
| ~~B-2~~ | ~~**D-B14-09** 未裁定~~ | 设计裁定 | ✅ **CLOSED（FROZEN — A，2026-09-13）** |
| ~~B-3~~ | ~~**D-B14-10** 未裁定~~ | 设计裁定 | ✅ **CLOSED（FROZEN — A-1，2026-09-13）** |
| ~~B-4~~ | ~~**D-B14-12** 未裁定~~ | 设计裁定 | ✅ **CLOSED（FROZEN — A，2026-09-13）** |
| ~~B-5~~ | ~~**O-1** canonical total 未确认~~ | 文档裁定 | ✅ **CLOSED（O-1 = FROZEN — A：canonical total = 84）** |
| ~~B-6~~ | ~~**O-2** 双标注形式未裁定~~ | 文档裁定 | ✅ **CLOSED（O-2 = FROZEN：双字段状态模型）** |
| B-7 | 冻结事实 1–10 不得被实施改动推翻（不 seed / 0 ACL trigger / 不实现授权求值 / 不启用 RLS / 不建 Domain·Tool·AI·Agent·Event·Audit 表） | 冻结约束 | **受约束** |
| B-8 | 生产迁移护栏（B1-3 P3-3）为纯文档；实施阶段**禁止**裸 `alembic upgrade head` | 控制项 | **KEEP DEFERRED**（实施前复核） |

> **说明**：B-1…B-4 属"新增约束 / 语义补齐"类裁定，**不阻塞 PREP 完成**；但在其关闭前 **不得进入 Implementation**。

---

## 8. 文档计数变更声明（避免计数不一致）

| 项 | 值 |
|---|---|
| 上一轮 Planned / Existing | 10 / 10（Missing 0 · Unexpected 0） |
| 本轮新增 | **+1 = `B1-4_HUMAN_DECISION_FREEZE_PACKAGE.md`**（本文件）<br>**R3 更新**：本文件与 5 份 B1-4 文档、3 份 B0 冻结文档随 D-B14-10 = A-1 同步修订（未新增文档，计数仍 11） |
| 本轮 Planned / Existing | **11 / 11** · Missing 0 · Unexpected 0 |
| 未修改文件 | 其余 10 份 B1-4 文档、B0/B1-1/B1-2/B1-3 全部文档、`0001–0006`、`env.py`、代码、测试 —— **均未改动** |

---

## 9. 状态

```
Frozen Facts                  = 12 / 12 保持（已只读复核）
D-B14-08 / 09 / 12            = FROZEN — A（2026-09-13 Human Decision；B0 文档已同步）
D-B14-10                      = FROZEN — A-1（2026-09-13 Human Decision；B0 三份文档已同步）
O-1                           = FROZEN — A（Canonical Total = 84）
O-2                           = FROZEN（Current Status + Post-Approval Level 双字段模型）
O-3 / O-4                     = P3（记录）· O-5 = CLOSED
Implementation Blocking       = B-1…B-6 全部 CLOSED（B-7 受约束 · B-8 迁移护栏 defer）

B1-4 PREP          = READY FOR HUMAN REVIEW
B1-4 IMPLEMENTATION = BLOCKED
```
