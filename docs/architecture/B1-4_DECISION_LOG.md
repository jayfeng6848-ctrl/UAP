# B1-4 — Decision Log（ADR）· **Revision R1**

Status: **PREP R1 — 仅修订设计结论，未实施任何项**
R1 变更性质：**撤回上一轮 2 项"推荐"**（D-B14-01 / D-B14-02），改以**冻结原文**为准；补齐治理模型、`granted_by` 语义、`action` 语义边界、Resource 归属一致性四类裁定材料。
格式：`事实依据 / Problem / Options / Recommended / Reason / 是否违反冻结 / 是否需要 Human Decision / Status`

---

## D-B14-01 — `acl_subject_types` 在 B1-4 是否 seed `user`/`role`/`agent`

| 项 | 内容 |
|---|---|
| **事实依据（原文）** | ① `STEP1B_SCHEMA_DEPENDENCY.md:193`：**"P00-P10 均无 seed 需求；P13 才有 seed。所有 trigger（P11）必须先于 P13 seed。"**<br>② `STEP1B_SCHEMA_DEPENDENCY.md:174`：P13 = Seed / built-in data<br>③ `STEP1B_SCHEMA_DEPENDENCY.md:219,249`：所有 trigger 必须在 seed（P13）之前<br>④ `STEP1B_SEED_STRATEGY.md:14`：seed 顺序 `[1] acl_subject_types (user/role/agent)`（**属 P13 的 seed 清单**）<br>⑤ `STEP1B_SEED_STRATEGY.md:111-116`：初始 seed 三行 `user`/`role`/`agent`；不注册 `group` |
| **Problem** | 上一轮我把"B1-4 是否注册 `agent`"当作 open question，并推荐"B1-4 只 seed user/role，`agent` 随 P09"。该推荐**在冻结事实下不成立**：P06（= B1-4）**根本不属于 seed phase**。 |
| **Options** | **A（=冻结原文）**：B1-4 **不 seed 任何 `acl_subject_types` 行**；三行 `user`/`role`/`agent` 统一在 **P13** 播种（届时 ACL 校验 trigger 已在 P11 就位）。<br>B（上一轮我的推荐）：B1-4 seed `user`/`role`，`agent` 延 P09 —— **自创**，无冻结依据。<br>C（B0 字面三行在 B1-4 seed）：**违反** P00–P10 无 seed 的冻结条款。 |
| **Recommended** | **A** —— 直接采用冻结原文，**无需新增裁定** |
| **Reason** | 冻结事实已自洽解决争议：seed 在 P13 ⇒ **seed 永远晚于 trigger** ⇒ 不存在"已注册但未校验"的窗口。且 P06→P13 期间 `acl_subject_types` 为空表，`resource_permissions.subject_type_id` 的 FK **无法满足** ⇒ ACL 行**物理不可写入** ⇒ 既不产生伪造主体，也不产生未注册主体。 |
| **是否违反冻结** | 否（A 就是冻结原文）；B/C 均**违反**冻结 |
| **是否需要 Human Decision** | **否**（上一轮"推荐 B"已撤回并标注） |
| **Status** | **RESOLVED BY FROZEN TEXT**（B1-4 无 seed） |

> **撤回声明**：上一轮 `B1-4_DECISION_LOG.md` 的 D-B14-01「推荐 A：B1-4 只 seed user/role」**作废**（前提不成立）。

---

## D-B14-02 — G/H/I/J 的 phase 归属（B1-4 是否实施其中任何一个）

### Q1 回答：B0 的"G/H/I/J 排 P09 之后"= **A（全部必须等 P09 后）**

**原文级证据（两处独立、互不依赖）**

| 出处 | 行 | 原文 |
|---|---|---|
| `STEP1B_TRIGGER_INVENTORY.md` §1 G | 89 | `dependency \| resource_permissions + acl_subject_types + users + roles + agents → **最早 P09 后**（agents 表存在）` |
| 同上 §1 H | 101 | `dependency \| resource_permissions + acl_subject_types（P09 后）` |
| 同上 §1 I | 112 | `dependency \| resource_permissions + acl_subject_types（P09 后）` |
| 同上 §1 J | 123 | `dependency \| resource_permissions（P09 后）` |
| 同上 §2 汇总表 | 163–166 | `最早 phase` 列：G/H/I/J **全部 = `P09 后`** |
| 同上 §3 一致性检查 | 177 | "**不引用不存在表**：G/H/I/J 依赖 agents/resource_permissions 等，**均在 P09 后建**" |
| `STEP1B_SCHEMA_DEPENDENCY.md` §7 | 235 | `tg_acl_subject_exists` … 依赖 `resource_permissions + acl_subject_types + users/roles/agents` → **P09 之后（依赖 agents 表）** |
| 同上 §7 | 236 | `tg_acl_user_hard_delete` → 依赖 `users + resource_permissions` → **P09 后** |
| 同上 §7 | 237 | `tg_acl_role_delete_block` → 依赖 `roles + resource_permissions` → **P09 后** |
| 同上 §7 语义说明 | 241 | "上表是 trigger **最早**可挂的 phase … P11 的 trigger DDL 也必须按上表顺序排列" |

**原文内部的不精确之处（如实报告）**：H/I 的 `dependency` 清单**不含 `agents`**，其"P09 后"是**显式阶段冻结**而非由依赖列机械推导；§3 的合并理由句（行 177）以"依赖 agents"概括 G/H/I/J，对 H/I 而言理由不充分。

| 项 | 内容 |
|---|---|
| **Problem** | 上一轮我提出"B1-4 建 G(user/role 分支)/H/I，J 与 agent 分支延 P09"，实质是把**字面 B**（依赖已足即可提前）当作设计依据，与两处冻结原文的"最早可挂 = P09 后"**冲突**。 |
| **Options** | **A（=冻结原文）**：B1-4 **不实施 G/H/I/J 任何一个**；四个 trigger 的最早 phase 均为 P09 后（实际按 P11 集中)，并在 P13 seed 之前就位。<br>B（上一轮我的推荐）：B1-4 提前实施 G(user/role)/H/I —— 需**修订** `TRIGGER_INVENTORY` 与 `SCHEMA_DEPENDENCY` 的 phase 列 ⇒ **属冻结文档修订**，需显式人工批准。<br>C：四个 trigger 全部在 B1-4 实施 —— 引用不存在的 `agents`，违反"trigger 不得引用未建表"，**不可行**。 |
| **Recommended** | **A** —— 直接采用冻结原文，B1-4 **零 ACL trigger** |
| **Reason** | ①A 无需任何裁定即可实施，且不产生阶段边界漂移；②提前（B）虽在依赖上可行，但会让"P09 后"这一冻结列失去约束力，属**静默扩权**；③A 的安全性经论证充分：B1-4→P13 期间 `acl_subject_types` 为空 ⇒ `subject_type_id` FK 不可满足 ⇒ `resource_permissions` **不可写入任何行** ⇒ 不存在未验证主体，也不存在"Authorization Layer 不知道如何验证"的主体（见 D-B14-12）。 |
| **是否违反冻结** | 否（A 就是冻结原文）；B 会**违反并需修订**冻结文档 |
| **是否需要 Human Decision** | **否**（采用 A）；**仅当**人工希望在 B1-4 提前获得 ACL 完整性时才需裁定 B，且必须同时批准修订两处冻结文档 |
| **Status** | **RESOLVED BY FROZEN TEXT**（B1-4 实施 0 个 ACL trigger） |

> **撤回声明**：上一轮「推荐 A：B1-4 建 3 个 trigger」**作废**（与冻结原文冲突）。
> **能力影响（如实告知）**：按 A 实施后，`resources` 从 B1-4 起可用，但 **ACL 能力（`resource_permissions` 写入）要到 P13 seed 之后才真正可用** —— 这是冻结设计的既定顺序，非缺陷。

---

## D-B14-03 — 域扩展表接入机制

| 项 | 内容 |
|---|---|
| 事实依据 | CORE 架构铁律：`domains/* → core/*` 单向；`resources` 为 registry，域表以 1:1 共享主键挂接（CORE §1.3 注、ER_MODEL `domain_extension` 块） |
| Recommended | 域表由 **Domain 模块**负责，Core migration 永不出现域表 |
| 是否违反冻结 | 否（承袭） · **Human Decision：否** |
| Status | **FROZEN（承袭架构铁律）** |

## D-B14-04 — `resource_relations` 不建

| 项 | 内容 |
|---|---|
| 事实依据 | `STEP1B_CONSTRAINT_MATRIX.md:200-207`「P2 可选，B1 不建」；`CORE_DOMAIN_MODEL.md:268-276` 同；B0 Q3 |
| Recommended | 不建（defer） · **Human Decision：否** |
| Status | **FROZEN（B0 Q3）** |

## D-B14-05 — RLS 不启用

| 项 | 内容 |
|---|---|
| 事实依据 | R5-D-04 / B0 Q1（OPEN）；`CORE_DOMAIN_MODEL.md` Q1 |
| Recommended | 不 enable、不建 policy、不改 PG 配置 · **Human Decision：否**（保持 OPEN） |
| Status | **FROZEN（承袭 R5-D-04）** |

## D-B14-06 — `classification` 只升不降由应用层保证

| 项 | 内容 |
|---|---|
| 事实依据 | B0 `STEP1B_SCHEMA_TEST_MATRIX.md` R6「classification 只升不降（应用层）→ DENY + audit」 |
| Recommended | 应用层规则；B1-4 DB 只保证取值域（CK） · **Human Decision：否** |
| Status | **FROZEN（B0 R6）** |

## D-B14-07 — ACL 变更审计（依赖 `audit_logs`）

| 项 | 内容 |
|---|---|
| 事实依据 | `STEP1B_ACL_STRATEGY.md:115` 要求 grant/revoke 同事务写 `audit_logs`；`audit_logs` 属 P10（`SCHEMA_DEPENDENCY.md:169`）⇒ **B1-4 时不存在** |
| Recommended | **defer 到 P10**；契约保留；B1-4 不实现审计写入 · **Human Decision：否** |
| Status | **FROZEN-defer**（与 B1-3 P3-4 同类） |
| 安全含义 | 在 `acl_subject_types` 为空、ACL 不可写的现状下（D-B14-01/02 结论），B1-4 期间**不存在可被审计的 ACL 变更** ⇒ 无实际暴露 |

---

## D-B14-08 — `resource_permissions.action`：结构校验 vs 授权词表

| 项 | 内容 |
|---|---|
| **事实依据** | ① `STEP1B_CONSTRAINT_MATRIX.md:196`：`action` 仅要求 **NN**，**无任何格式或取值约束**<br>② `STEP1B_CONSTRAINT_MATRIX.md:120`（`permissions`）：`resource_type` 标注"原文档标注 NULL 时 action 语义全局；建议 NN 或 NULL 择一，**以 Entity Catalog 为准**" ⇒ 语义仍有未决<br>③ `STEP1B_SEED_STRATEGY.md:90` 标题："初始 permissions 字典（**seed 示例，B1 定稿**）"；`STEP1B_B0_GATE_REPORT.md:125`："**seed permissions 字典清单待人工定稿**" |
| **Problem** | `action` 词表（如 `read`/`write`/`resource.read`）**未冻结**；上一轮我提示"与 `permissions.key` 同族格式"存在把**结构校验**误升为**词表冻结**的风险。 |
| **Options** | **A（推荐）**：B1-4 保持冻结现状（`action` 仅 NN），**不加** CK；词表与对齐规则 defer 到 Permission Dictionary / Authorization 阶段。<br>B：仅加**结构**格式 CK（如 `^[a-z][a-z0-9_.]{1,63}$`），**不定义任何取值语义** —— 属新增约束，需批准。<br>C：B1-4 定义 action 词表（`read`/`write`/…）—— **越界**，明确禁止。 |
| **Recommended** | **A**（保守、零新增）；若人工希望收紧输入面则选 **B**（**仍不得**定义语义取值） |
| **Reason** | 区分 **Structural validation**（格式/非空）与 **Authorization vocabulary**（取值语义）；后者未冻结，B1-4 无权限发明。 |
| **是否违反冻结** | A 否；B 属新增约束（需批准）；C 违反 |
| **是否需要 Human Decision** | **是（仅当采纳 B）** |
| **Status** | **FROZEN — A（2026-09-13 Human Decision）** |
| **冻结内容（2026-09-13）** | 保留 `NOT NULL` + 已冻结的结构性唯一性 `UQ(resource_id, subject_type_id, subject_id, action)`；**不新增** action semantic vocabulary / enum / whitelist / CHECK vocabulary / namespace 语义；**不迁移**未来 `permissions` 表 seed dictionary；`action` = **当前未冻结语义的非空 opaque action identifier**。**A = 零新增 semantic/format contract**（**不加** regex CHECK、**不加** 命名空间 CHECK、**不加** semantic format contract）。**`ACT-03` 条件未成立** |

> **撤回声明**：上一轮 D-B14-08 的表述"与 `permissions.key` **同族** CK（推荐 A）"已被本项取代 —— 推荐改为 **默认 A（不加 CK）**，B 仅作可选收紧。

---

## D-B14-09 — `granted_by` 的语义与删除行为

| 项 | 内容 |
|---|---|
| **事实依据** | ① `CORE_DOMAIN_MODEL.md:258`：字段定义 `granted_by NULL → users.id`（**无语义说明、无 ON DELETE**）<br>② `STEP1B_ACL_STRATEGY.md:44`：DDL `granted_by uuid REFERENCES users(id)`（**未写 ON DELETE**）<br>③ `STEP1B_CONSTRAINT_MATRIX.md:192`：`granted_by NULL → users.id`（同）<br>④ `STEP1B_ACL_STRATEGY.md:115`：将其列在 **audit 的 actor 组**："写入/删除必须同事务写 `audit_logs`：**actor**、resource、subject、action、effect、`granted_by`" |
| **Problem** | `granted_by` 究竟是 **ACL owner** 还是 **actor attribution（执行授权动作的人）**；删除行为完全未冻结。 |
| **裁定（语义）** | **B = Actor attribution / 执行授权操作的人**（依据 ④ 的 actor 分组语境；ACL 的"归属"由 `resources.owner_id` 承担，`resource_permissions` 本身无 owner 概念） —— **不得**当作 permission owner。 |
| **Options（删除行为）** | **A**：`ON DELETE SET NULL`（推荐）；B：`RESTRICT`；C：`CASCADE`。 |
| **Recommended** | **A（PROPOSED）**：用户最终 purge 后 ACL 不被删除，历史 attribution 变为 NULL；完整操作历史由 **`audit_logs`** 承接（**B1-4 不实现 `audit_logs`**，见 D-B14-07）。 |
| **Reason** | B 会让历史授予者阻碍用户清理；C 属静默数据丢失（违反 P2-03 精神）；A 与 `resources.owner_id` 的既有 SET NULL 先例一致。 |
| **是否违反冻结** | ON DELETE 属**冻结未明示** ⇒ A 是**补齐**而非改写；语义裁定 B 属**解释**冻结（不新增能力） |
| **是否需要 Human Decision** | **是**（A/B/C + 语义确认） |
| **Status** | **FROZEN — A（2026-09-13 Human Decision）** |
| **冻结内容（2026-09-13）** | `resource_permissions.granted_by` **`ON DELETE SET NULL`**；语义保持 = **actor attribution**（`resources.owner_id` = **ownership**）。理由：删除 actor **不**级联删除 ACL；保留 ACL 生命周期；actor attribution 在主体删除后允许为空；**不因 user hard delete 而意外删除 `resource_permissions`**；与 `owner_id` 语义保持独立。**`F3` / `GB-02`（owner_id）与 `GB-01`（granted_by）三条分别存在，禁止合并**；**不得**因 SET NULL 而修改 `owner_id` 的既有删除策略 |

---

## D-B14-10 — `resources.tenant_id` / `space_id` 归属一致性

| 项 | 内容 |
|---|---|
| **事实依据** | ① `STEP1B_CONSTRAINT_MATRIX.md:169`：`tenant_id → tenants.id **R**（NN）`；`space_id NULL → spaces.id **R**`；`owner_id NULL → users.id **SN**`<br>② `STEP1B_CONSTRAINT_MATRIX.md:173`：NULL 列含"`space_id`（**平台级资源或未定空间**）"<br>③ `CORE_DOMAIN_MODEL.md:162` + `:477`：**`memberships`** 的冗余 `tenant_id` 由 trigger 保证 `= spaces.tenant_id`（B1-2 已实现 `tg_membership_tenant_consistency`）<br>④ **`resources` 在冻结文档中没有任何归属一致性约束/trigger**（逐项核对 CONSTRAINTS §3 与 TRIGGER_INVENTORY G–J） |
| **Problem** | 非法组合可成立：`resources.tenant_id = Tenant-A` 而 `resources.space_id = Space-B`（`Space-B.tenant_id = Tenant-B`）⇒ 通过冗余字段绕过租户隔离。 |
| **语义裁定（原文支撑）** | · `tenant_id` **始终 NOT NULL**（= 无"无租户资源"）<br>· `space_id IS NULL` = **平台级资源或未定空间**（原文用词，二者未区分 —— 记录为措辞模糊，不自行细分）<br>· 资源**不允许跨 Tenant**（`tenant_id` 为唯一归属）<br>· 资源**不允许跨 Space**（`space_id` 单值）；**不允许跨 Space 层级**<br>· 若 `space_id` 非空，则 `spaces.tenant_id` **必须** `= resources.tenant_id` |
| **Options** | **A**：新增 B1-4 内 trigger `tg_resources_tenant_space_consistency`（BEFORE INSERT/UPDATE，仅结构完整性；不改 B1-2）<br>**B**：DB 原生复合 FK —— `resources (space_id, tenant_id) → spaces (id, tenant_id)`，**需给 `spaces` 增加 `UNIQUE (id, tenant_id)`** ⇒ **修改 B1-2 已冻结表结构**，需批准<br>**C（=冻结现状）**：仅应用层保证，DB 无强制 |
| **Recommended** | **A**（若人工要求 DB 强制）或 **C**（若坚持零新增）—— 见下 |
| **Reason** | 冻结文档**未**为 resources 定义该约束（对比 memberships 明确定义了）⇒ 选 A/B 都属**新增约束**，必须由人工决定；B 虽最"DB-native"，但触碰 B1-2 冻结结构，代价最高。<br>**trigger 职责声明**：仅做 **structural integrity**（拒绝非法组合）；**绝不**承担 authorization evaluation（授权仍由 Authorization Layer 决定）。 |
| **是否违反冻结** | A/B 属**新增**（需批准）；C = 现状（无违反，但存在隔离绕过风险） |
| **Human Decision（2026-09-13）** | **A-1 —— 批准在 B1-4 引入 `tg_resources_tenant_space_consistency`**（BEFORE INSERT OR UPDATE；`space_id IS NULL` 放行；非空时要求 `resources.tenant_id = spaces.tenant_id`）。<br>**已先修订 B0 冻结文档**：`STEP1B_TRIGGER_INVENTORY.md`（新增条目 **F2**，earliest phase = **P06 / B1-4**）· `STEP1B_SCHEMA_DEPENDENCY.md` §7（相位表新增该行 = P06）· `STEP1B_CONSTRAINT_MATRIX.md` §3（`resources` 增 TRIGGER 行）。<br>**G/H/I/J 的「P09 后」未改动、既有相位未重排。** |
| **边界（强制）** | trigger **只承担 structural integrity**，**不承担 authorization evaluation**；不引入 RLS；不引入 Domain/Agent/Tool/AI/Event/Audit 依赖 |
| **Status** | **FROZEN — A-1**（2026-09-13 Human Decision） |

---

## D-B14-12 — `acl_subject_types` 治理模型（新增，R1 必需项）

| 项 | 内容 |
|---|---|
| **事实依据** | ① `CORE_DOMAIN_MODEL.md:244`：定义为"**受控的注册机制**。新增 subject type 必须先在此注册，否则 ACL 写入触发 trigger 拒绝"<br>② `CORE_DOMAIN_MODEL.md:249`：扩展流程 = "**插一行注册 + 写 trigger 验证**"（即注册与 trigger 扩展**成对**）<br>③ `STEP1B_ACL_STRATEGY.md:124-126`：未来 `group` 路径 = `CREATE groups` → `INSERT acl_subject_types` → 扩展 trigger → 加测试（**migration 驱动**）<br>④ `CORE_DOMAIN_MODEL.md:248`：CK 白名单仅 `('user','role','agent')` |
| **Problem** | 若任何模块可自由 INSERT，将产生"**Authorization Layer 不知道如何验证**"的主体类型 ⇒ 授权不确定性（用户第八条明列的风险）。 |
| **治理结论（设计，非实施）** | `acl_subject_types` = **平台受控 Subject Type Registry**（**不是**自由业务注册表）：<br>· **INSERT**：**仅经 migration**（伴随 trigger 校验分支 + 测试），**不提供运行时写入口**<br>· **UPDATE**：仅允许 `description`；`key` 不可变（避免绕过 CK 白名单语义）<br>· **DELETE**：**禁止物理删除**；退役走 `archived_at`（部分唯一索引随之释放）<br>· **Domain / Plugin 自行注册**：**不允许**（无路径；且 CK 白名单已阻断新 key 的运行时插入）<br>· **未实现主体类型不得产生有效 ACL**：由"注册表为空 ⇒ FK 不可满足 ⇒ `resource_permissions` 不可写入"保证（D-B14-01/02 结论成立的直接推论） |
| **Options** | **A（推荐）**：以上治理 + 在 B1-4 加 `tg_acl_subject_types_protect`（BEFORE INSERT/UPDATE/DELETE：拒绝运行时 INSERT；`key` 不可变；禁 DELETE）<br>**B**：仅靠 CK 白名单（现状）+ 文档约定，不建 trigger<br>**C**：定义 Plugin 注册 API —— **本阶段明确不做**（超出 B1-4 scope） |
| **Recommended** | **A**（**已于 2026-09-13 由 Human Decision 采纳 = FROZEN — A**） |
| **Reason** | 与 B1-3 已确立的同类先例一致（`tg_roles_is_system_protect` 对系统角色的"运行时不可写"策略，R2-D-05）；且该 trigger 只依赖 `acl_subject_types` 自身 ⇒ **可在 B1-4 建立，不违反 G/H/I/J 的 P09 约束**。 |
| **是否违反冻结** | 属**新增约束**（需批准）；**不**与 G/H/I/J 相位冲突（不同表、无 agents 依赖） |
| **是否需要 Human Decision** | **是** |
| **Status** | **FROZEN — A（2026-09-13 Human Decision）** |
| **冻结内容（2026-09-13）** | `acl_subject_types` = **platform-controlled registry**；whitelist 保持 **`user` / `role` / `agent`**（**不得**新增 `group` 或任何未冻结 subject type，**不得**修改 whitelist，**不得**提前 seed）；采用 **platform-controlled registry + protection mechanism**（`tg_acl_subject_types_protect`，BEFORE INSERT/UPDATE/DELETE）。**registry 不允许** Domain runtime / Plugin runtime / 普通业务代码 / 未来 API 自由注册。**边界：遵循既有 B0/B1-4 架构边界，不得演变为 Domain authorization** |

---

## D-B14-13 — B1-4 的 seed 与 trigger 交付清单（R1 重新裁定）

| 项 | 内容 |
|---|---|
| **事实依据** | `SCHEMA_DEPENDENCY.md:193`（P00–P10 无 seed）· `:219/:249`（trigger 先于 P13 seed）· `TRIGGER_INVENTORY.md:163-166`（G/H/I/J 最早 P09 后） |
| **裁定** | **B1-4（P06）交付：**<br>· 3 张表 + 全部 PK/FK/UQ/CK/NN/DEFAULT + 8 个索引<br>· trigger **3 个**：`tg_resources_set_updated_at`（复用 B1-1 `set_updated_at()`）+ `tg_resources_tenant_space_consistency`（D-B14-10 = A-1，**structural integrity only**）+ `tg_acl_subject_types_protect`（D-B14-12 = A，**registry governance only**）<br>· **已批准**：`tg_resources_tenant_space_consistency`（2026-09-13 D-B14-10 A-1）· `tg_acl_subject_types_protect`（2026-09-13 D-B14-12 A）—— 二者均仅依赖 B1-4 自身对象，无 forward 依赖，B0 冻结文档已同步<br>· **不交付**：G/H/I/J 全部（P09 后）· 任何 seed 行（P13） |
| **Status** | **FROZEN（3 表 + 3 trigger；0 seed；0 个 G/H/I/J）** |
| 是否需要 Human Decision | 否（清单已由 D-B14-10 A-1 / D-B14-12 A 完全确定） |

---

## D-B14-11 — B1-3 遗留 P3：逐项 `KEEP DEFERRED`

| 遗留项 | R1 判定 | 是否已违反 B1-4 安全边界 |
|---|---|---|
| **P3-1** `STEP1B_B1_3_SCHEMA_REVIEW.md:191` R4 表述未标注 R5 取代（该文件无 R5 段） | **KEEP DEFERRED** | **否**（纯展示；未改动任何 schema/trigger/授权语义） |
| **P3-2** `STEP1B_SEED_STRATEGY.md:152` 同类漂移 | **KEEP DEFERRED** | **否**（R5 段在 :156 已正确取代） |
| **P3-3** production migration mechanical guard（`alembic.ini` 默认 URL = 正式库；`env.py` 无 opt-in 拒绝） | **KEEP DEFERRED** —— 但**登记为实施前必须复核的控制项** | **否**（属既有控制缺口；但 B1-4 新增 0007 后影响面+1。实施阶段**禁止**执行裸 `alembic upgrade head`，必须以显式 URL/attributes 指向 disposable 库） |
| **P3-4** `audit_logs`（P10） | **KEEP DEFERRED** | **否**（结合 D-B14-01/02：B1-4 期间 ACL 不可写入 ⇒ 无待审计变更） |
| **P3-5** `deactivate(user)` service workflow | **KEEP DEFERRED** | **否**（与资源/ACL 无交集） |

**本轮未修改任何 P3 涉及文件**（0001–0006 / env.py / B1-3 实现与文档均未触碰）。

---

## 汇总（Revision R1）

| ID | 主题 | Status | Human Decision |
|---|---|---|---|
| D-B14-01 | `acl_subject_types` seed 时机 | **RESOLVED BY FROZEN TEXT**（B1-4 无 seed；三行在 P13） | 否（上一轮推荐已撤回） |
| D-B14-02 | G/H/I/J phase 归属 | **RESOLVED BY FROZEN TEXT**（B1-4 实施 0 个 ACL trigger） | 否（采用冻结；提前需另案批准+修订冻结文档） |
| D-B14-03 | 域扩展表接入 | FROZEN（Domain 层） | 否 |
| D-B14-04 | `resource_relations` | FROZEN（不建） | 否 |
| D-B14-05 | RLS | FROZEN（不启用） | 否 |
| D-B14-06 | classification 只升不降 | FROZEN（应用层） | 否 |
| D-B14-07 | ACL 审计 → P10 | FROZEN-defer | 否 |
| D-B14-08 | `action` 结构 vs 词表 | **FROZEN — A（2026-09-13）：零新增 semantic/format contract；`action` = opaque identifier；B0 文档已同步** | 已裁定 |
| D-B14-09 | `granted_by` 语义 + 删除行为 | **FROZEN — A（2026-09-13）：`ON DELETE SET NULL`；语义=actor attribution；B0 文档已同步** | 已裁定 |
| D-B14-10 | Resource 归属一致性 | **FROZEN — A-1（2026-09-13）：B1-4 引入 `tg_resources_tenant_space_consistency`（P06）；B0 三份文档已同步修订；G/H/I/J 保持 P09 后** | 已裁定 |
| D-B14-12 | `acl_subject_types` 治理模型（新增） | **FROZEN — A（2026-09-13）：platform-controlled registry + `tg_acl_subject_types_protect`；whitelist 保持 user/role/agent；B0 文档已同步** | 已裁定 |
| D-B14-13 | B1-4 交付清单（重新裁定） | **FROZEN**（3 表 + 3 trigger + 0 seed） | 已裁定 |
| D-B14-11 | B1-3 P3 边界 | 全部 **KEEP DEFERRED** | 否 |

**仍需人工裁定的 OPEN = 0 项** —— **D-B14-08 = FROZEN — A** · **D-B14-09 = FROZEN — A** · **D-B14-10 = FROZEN — A-1** · **D-B14-12 = FROZEN — A**（均 2026-09-13 Human Decision）；D-B14-01 / 02 已由冻结原文解决；**不再存在 OPEN 决策**。
