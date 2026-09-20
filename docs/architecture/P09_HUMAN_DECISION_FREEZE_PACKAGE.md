# P09_HUMAN_DECISION_FREEZE_PACKAGE

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE — 已完成**
**DESIGN**: **NOT STARTED** · **0011**: **ABSENT** · **IMPLEMENTATION**: NOT STARTED
**Freeze date**: 2026-09-17（OQ 轮 · `D-P09-01`～`D-P09-12`）· 2026-09-17（**ND 轮 · `D-P09-13`～`D-P09-18`**）
**权威记录**: `P09_DECISION_LOG.md`（本文档为其证据包）

> 本文档承载 `D-P09-01` … `D-P09-18` 的**决策证据**（问题 / 权威来源 / 冲突 / 后果）。
> 它**不**重新解释 Human Decisions，**不**引入新方案，**不**解决 `U-1` / `U-2` / `U-3` / `NU-07` / `NU-08` / `NU-09`。

---

## 1. 冻结范围与前置

| 项 | 值 |
|---|---|
| 阶段 | P09（`STEP1B_SCHEMA_DEPENDENCY.md:170/:213` = Agent 域 4 表 + 顺序链） |
| 决策数 | **18** = OQ 轮 **12**（`D-P09-01`～`D-P09-12`，对应 `OQ-01`～`OQ-12`）+ ND 轮 **6**（`D-P09-13`～`D-P09-18`，对应 `ND-01`～`ND-06`） |
| 冻结来源 | `P09 HUMAN DECISION FREEZE PREP REPORT`（OQ 轮）· `P09 HUMAN DECISION FREEZE PREP REPORT — ND-01～ND-06`（ND 轮）→ Human 逐项裁定 |
| 前置解锁 | **B-1**（创建 P09 承载文档）· **B-2**（历史文档最小修订）— 均于 2026-09-17 授权；**ND-06** = 第二轮最小补注授权（2026-09-17） |
| 本轮写入 | OQ 轮：9 份 P09 文档（新建）+ 6 组历史文档最小修订（B-2 范围）；ND 轮：P09 文档 8 份同步 + 历史文档 2 份补注（CM ×3 / CORE ×1，ND-06 范围） |
| 本轮未做 | 未创建 `0011` · 未执行 migration / DDL / DML · 未修改 `0001`–`0010` · 未修改 B1-6 implementation / 测试 · 未修改 `agent/` · 未实现任何 runtime / API / worker · 未 commit · 未 tag |

---

## 2. 决策证据包（12 项）

### D-P09-01 — `tool_executions` 不分区

```
问题（OQ-01）: tool_executions 在 P09 是否建为分区表？
权威来源     : CORE:358「90 天后按分区删除（详见 §13）」· CORE:960「hard delete（分区，90 天）」
               CM:256「分区 90 天 hard delete」· STEP1A:69「分区，90 天 hard delete」
               STEP1A:384（hard delete(分区) 组）
               反证：SD:265 §9 分区表清单 = 仅 events / audit_logs / ai_request_logs
               约束：PK 三源一致 = id（CORE:353 / CM:250 / STEP1A:69）
冲突         : 5 处「分区」表述 vs §9 清单缺列；若分区则分区键必须进 PK（与 PK=id 冲突）
裁决         : B —— 不分区
结构后果     : PK = id 保持不变；不新增分区对象；升级无分区 DDL；降级无子分区 DROP
保留后果     : 90 天 hard delete（**执行机制 U-1 未冻结**）
未授权事项   : 不得借修订之机扩展 retention 执行机制
```

### D-P09-02 — `tool_executions.tenant_id` = NOT NULL

```
问题（OQ-02）: tenant_id 是否 NOT NULL？
权威来源     : CORE:354（FK 行仅写 tenant_id，无 NULL 标记）· ER:298（uuid tenant_id FK，无 nullable 注记）
               CM:251（FK 行未列 tenant_id）· CM:255（tenant_id?（设计为 NN 若按租户隔离））
               SD:54（依赖列含 tenants，FK 列未列）
冲突         : CORE/ER 无标记（可读作 NN）vs CM 显式 ?（未定）
裁决         : A —— NOT NULL
FK 后果      : tool_executions.tenant_id → tenants.id ON DELETE RESTRICT（见 D-P09-03 F12）
安全后果     : 每条执行记录必属某租户（范围过滤全覆盖）
未授权事项   : 不得扩展新的租户模型
```

### D-P09-03 — 9 条 FK 的 ON DELETE

```
问题（OQ-03）: §11.1 默认规则（凡不在白名单者一律 RESTRICT）不能机械适用（B1-5 已实现白色单外 CASCADE）；
               9 条 FK 的删除规则无来源明写
裁决         : F1/F2/F3/F12 = RESTRICT · F7/F15/F16 = SET NULL · F10/F11 = CASCADE
既有不变     : F4/F5 = SET NULL · F6/F8/F9 = CASCADE · F13/F14 = RESTRICT
关键语义     : tool_executions 的 5 条 FK 中 CASCADE = 0 ⇒ Agent / User 删除不级联清除历史 execution
登记（不阻断）: F3 = RESTRICT 与先例 spaces.owner_id / resources.owner_id（SET NULL）方向相反 —— 仅登记
```

### D-P09-04 — 幂等唯一性对象 = `uq_tool_exec_idem`（UNIQUE INDEX）

```
问题（OQ-04）: (tool_id, idempotency_key) 部分唯一性的名与形式？
权威来源     : CM:252（uq_tool_exec_idem）· INDEX_STRATEGY:128（ix_texec_idem）· INDEX_STRATEGY:7（自述不重复）
               D-B15-06 = A（区分 constraint-form / index-form；表达式不计入 UNIQUE CONSTRAINT）
冲突         : 同一对象两名；INDEX_STRATEGY 自相矛盾
裁决         : A —— 名 = uq_tool_exec_idem；类型 = UNIQUE INDEX；谓词 = idempotency_key IS NOT NULL；按 UNIQUE INDEX 计
边界         : 不得伪装为 UNIQUE CONSTRAINT；不得同时保留两个实际对象
```

### D-P09-05 — `agent_permissions` = 2 条 CHECK

```
问题（OQ-05）: CK 计为 1 条还是 2 条？
权威来源     : CORE:314（仅「至少一列非 NULL」）vs CM:293（「至少一列非 NULL」+ effect IN ('allow','deny')）
               ER:265-274 无 CK 行 · STEP1A:65 未提 CK
裁决         : B —— 2 条 CHECK
CHECK-1      : permission_id IS NOT NULL OR tool_id IS NOT NULL OR resource_scope IS NOT NULL
CHECK-2      : effect IN ('allow', 'deny')
边界         : 不得合并；canonical = 2 CHECK constraints
未冻结       : 两条 CHECK 的正式名称 → 命名待 P09 DESIGN 确定（U-3）
```

### D-P09-06 — G/H/I/J 不属于 P09

```
问题（OQ-06）: 4 件 ACL cross-table trigger 是否属 P09？
权威来源     : TRIGGER_INVENTORY:200-203（最早 phase 列 = P09 后 ×4）· :124/:136/:147/:158（dependency）
               :214 · SD:237-239 · SD:241（该列语义 = 「trigger 最早可挂的 phase」）· SD:176③
               B1-4_DECISION_LOG:28/:50（D-B14-02 = A）· B1-4_DEPENDENCY:71-82（H/I dependency 不含 agents，已如实记载）
冲突         : 「P09 后」字面（严格晚于 P09）vs B1-4 旁注「实际按 P11 集中」（旁注非独立冻结条款）
裁决         : A —— 不属于 P09 implementation；保持「P09 后」
边界         : 不得移入 P09 / P10；不得创建 P11 migration；不得创建 trigger / function
```

### D-P09-07 — P09 = SCHEMA ONLY

```
问题（OQ-07）: P09 是否触及 agent/ 代码层？
权威来源     : agent/ 11 tracked 文件（72ade9f = UAP-V0.1.0-INIT；全部 Protocol / frozen dataclass；
               顶层 import 实测 = __future__ / dataclasses / typing）
               ARCHITECTURE:13 / :51-58 · DEPENDENCY_RULES §4 · tests/architecture/test_dependency_rules.py:123-131
               STEP1A:560（「明确不在 STEP 1-B：具体 Agent / Tool 实现」）
裁决         : A —— SCHEMA ONLY
边界         : 不修改 agent/ runtime / registry / tools / memory / workflow；STEP 0 骨架保持原样；
               不实现 Agent Runtime · Agent Registry Runtime · Tool Runtime · Memory Runtime · Workflow Runtime
```

### D-P09-08 — 9 份文档模式

```
问题（OQ-08）: P09 文档集？
权威来源     : B1-5_* = 9 份 · B1-6_* = 9 份（D-B16-09 = A）· B1-4_* = 12 份（两种模式并存）
裁决         : P09 沿用 B1-5 / B1-6 的 9-document mode（固定 9 份）
边界         : 不恢复 12 份模式；不创造第 10–12 份
执行结果     : 本阶段创建 9 份（见 P09_DECISION_LOG.md §6）
```

### D-P09-09 — revision 冻结

```
问题（OQ-09）: 0011 的 revision id？
权威来源     : MIGRATION_IMPLEMENTATION_CONTRACT §7:83/:85/:86 · B1-6_MIGRATION_PLAN:15/:16 · 0009:35
裁决         : revision = 0011_p09_agent_tool_permission
               filename = 0011_p09_agent_tool_permission.py（filename == revision）
               ≤ 32 字符（实测 30）· single head · append-only
边界（强制） : 只冻结 identity；不得创建该文件；不得执行 migration
```

### D-P09-10 — `ai_request_logs.agent_id` 维持 NO FK

```
问题（OQ-10）: P09 是否为其增加 FK？
权威来源     : B1-6_DECISION_LOG §D-B16-03（FROZEN — A：FK 列 = provider_id + model_id，均 RESTRICT；
               agent_id / actor_id / tenant_id / space_id = NO FK；边界「不得形成 P08 → P09 forward FK dependency」）
               B1-6_DEPENDENCY:179（若未来要加，属新决策，须显式授权）
               tests/integration/test_ai_gateway_schema.py:455-470（AF5 断言，B1-6 canonical 38 之一）
裁决         : 维持 NO FK
边界         : 禁止通过 P09 顺手增加 agent_id → agents.id；未来增加须作为新的 Human Decision；本阶段不启动新决策
```

### D-P09-11 — deferred FK downgrade 采用 0005 同构

```
问题（OQ-11）: fk_agents_current_version 的 downgrade 顺序？
权威来源（升级侧，Frozen）: SD §4.1:124-134（三步；约束名 fk_agents_current_version；ON DELETE SET NULL）
                            SD:136「Phase 08」已由 D-B16-08 = C 判为陈旧引用，正式归属 P09
权威来源（降级侧，先例）  : 0005_b1_3_authorization.py — upgrade ADD CONSTRAINT（:431-436）；
                            downgrade 先 DROP CONSTRAINT IF EXISTS（:519-520）再 DROP TABLE roles（:37）
裁决         : A —— 0005 同构
Upgrade      : agents → agent_versions → ADD fk_agents_current_version
Downgrade    : DROP fk_agents_current_version → DROP agent_versions → DROP agents
边界         : 该 FK 必须保持 ON DELETE SET NULL；不得修改升级侧既有定义
```

### D-P09-12 — `agents` tenant/space consistency trigger（structural only）

```
问题（OQ-12）: 是否为 agents 建立 tenant/space 一致性约束？
权威来源     : CM:169 / :171（resources 同形 + tg_resources_tenant_space_consistency）
               TRIGGER_INVENTORY:86-93（F2 定义）· B1-4_DECISION_LOG:152/:213（D-B14-10 = A-1 · P06）
               CM:267（agents FK 行）
冲突         : resources 与 agents 同形，但 agents 此前无对应 trigger（先例 ≠ 冻结要求）
裁决         : A —— 增加该 trigger
冻结语义     : space_id IS NULL → 允许；space_id IS NOT NULL → 必须 agents.tenant_id = spaces.tenant_id
边界（强制） : 只负责 STRUCTURAL INTEGRITY；绝对不得解释 ALLOW / DENY / 权限继承 / 角色 / 资源授权 / ACL decision
未冻结       : trigger 正式名称（U-2）
```

---

## 2A. ND 轮决策证据包（`D-P09-13` ～ `D-P09-18`）

### D-P09-13 — `tool_executions` = 3 条 CHECK

```
问题（ND-01）: CK 计为 1 条（CORE:357）还是 3 条（CM:253）？
权威来源     : CORE:357（1）vs CM:253（3）· ER:296-306 无 CK 行 · STEP1A:69 无 CK
实作先例     : 0007 = 6 CK（= CM 6）· 0008 = 5 CK（= CM 5）· 0010 = 8 CK（= CM 8）
               —— 六次实施全部采用 CM 超集；ck_tools_timeout（0008:115）为同类数值域 CK 先例；
               OQ-05（CORE 1 vs CM 2）已裁为 CM 超集
裁决         : 3 条 —— status IN (...) + attempts >= 1 + duration_ms >= 0
语义         : duration_ms IS NULL 行通过；attempts 为 NN ⇒ attempts >= 1 为有效域收紧
未冻结       : 3 条 CHECK 的约束名（U-3 同族）
连带         : CORE:357 已按 D-P09-18 补注
```

### D-P09-14 — `agent_versions` published 状态迁移 = 沿用 0008 同构

```
问题（ND-02）: 是否允许 published → deprecated / revoked？
权威来源     : CORE:303 · CORE:957（§13 保留策略：immutable，只能 deprecate/revoke）· CM:284
               TRIGGER_INVENTORY:164/:204（K 共用名 · 表建时）· 0008 实作（OLD.status='published' 一律 RAISE）
               B1-5_SCHEMA_DESIGN:127（「deprecate/revoke 走应用层状态迁移（后续阶段）」）· TDF6（后续）
裁决         : A —— OLD.status='published' ⇒ UPDATE = RAISE · DELETE = RAISE ·
               不允许 published → deprecated · 不允许 published → revoked
归属         : deprecate / revoke 属后续应用层治理阶段
层级澄清     : CORE:303 = trigger 不变式；CORE:957 = §13 保留策略分类 ⇒ 二者层级不同，非实质矛盾
边界         : 不得修改 0008；不得设状态迁移豁免（否则与共用 trigger 名语义分叉）
```

### D-P09-15 — P09 索引权威与 8 个对象

```
问题（ND-03）: 索引清单以何为准？是否补 FK 列索引？
权威来源     : CORE §12:1022-1026（P09 仅 4 行，无 agent_permissions 行）
               vs INDEX_STRATEGY:103-131（逐表 + 用途 + §4 命名规范 + §5 三分汇总）· :202（FK 反查补索引 → P12）
决定性先例   : 0010 实作 5 个非 PK 索引对象；CORE §12 仅列 2 条 ⇒ 实作采用 INDEX_STRATEGY 超集
裁决         : INDEX_STRATEGY = 权威；交付 8 个 —— uq_agents_key · ix_agents_tenant_status ·
               uq_agent_versions · ix_ap_agent · uq_agent_perm · uq_tool_exec_idem ·
               ix_texec_tenant_created · ix_texec_status
不补         : 不额外补 FK 列索引（agents.owner_id = P3；FK 反查补索引归 P12）
子项         : ix_texec_status 纳入本次交付
CORE §12     : 不回改；由 P09 文档明确权威归属
```

### D-P09-16 — UQ 计数口径

```
问题（ND-04）: UQ 如何计数？
权威来源     : D-B15-06 = A（1 CONSTRAINT + 3 INDEX；表达式唯一不计入 UNIQUE CONSTRAINT；
               以 pg_constraint / pg_indexes 实测为准）· PG 规则（部分/表达式唯一只能是 index）
裁决         : UNIQUE CONSTRAINT = 1（uq_agent_versions）· UNIQUE INDEX = 3
               （uq_agents_key · uq_agent_perm · uq_tool_exec_idem）
要求         : canonical 统计必须区分 pg_constraint 与 pg_indexes
未冻结       : canonical 总计数与编号空间
```

### D-P09-17 — `0008` 措辞漂移处置

```
问题（ND-05）: 0008:36-37「不实施 G/H/I/J（…）—— 仍属 P09」与 D-P09-06 = A 字面矛盾
权威来源     : TRIGGER_INVENTORY:200-203 · SCHEMA_DEPENDENCY:237-241 · D-B14-02 = A · D-P09-06 = A
               MIGRATION_IMPLEMENTATION_CONTRACT §7:86（已发布 revision 永不改写）
裁决         : A —— 不修改 0008（亦不改任何已发布 migration）；在 P09 文档登记漂移
权威解释     : TRIGGER_INVENTORY + D-P09-06 = A ⇒ G/H/I/J 属于 P09 后
处置同构     : 与 D-B16-08 = C（B1-6 陈旧引用，由 B1-6_DEPENDENCY §5.1 加注）同构
物理后果     : docstring 注释 ⇒ 无 DDL / 结构后果
```

### D-P09-18 — ND-06 最小文字补注包（已执行）

```
问题（ND-06）: 是否授权 CM / CORE 最小文字补注？
授权范围（4 处，已完成）:
  ① CM agent_versions NULL 列表补 published_by
  ② CM agent_permissions 增加 NN / NULL 列表
  ③ CM 该表 UQ 行补名 uq_agent_perm
  ④ CORE tool_executions CK 补 attempts >= 1 / duration_ms >= 0
约束         : 保持既有语义、不新增设计；不修改已发布 migration；不修改代码和测试
执行结果     : 4/4 完成（单位置唯一命中替换；内容由既有 CORE 定义派生）
```

---

## 3. NOT FROZEN（随包登记，不得自行决定）

| ID | 事项 | 状态 |
|---|---|---|
| `U-1` | `tool_executions` 90 天 hard delete 的执行机制 | **NOT FROZEN** → 待 P09 DESIGN |
| `U-2` | `agents` consistency trigger 的正式名称 | **NOT FROZEN** → 待 P09 DESIGN |
| `U-3` | 全部 8 个 CHECK 的正式名称 | **DESIGN RESOLVED**（`P09_SCHEMA_DESIGN.md` §2B.5）—— 非 Human Decision |
| `NU-07` | `tg_version_immutable` 的 trigger **函数名**（`agent_versions` 侧） | **DESIGN RESOLVED** = `enforce_agent_versions_immutable()`（§2B.4；**不修改 `0008`**） |
| `NU-08` | 列类型 / DEFAULT 逐项 · P09 时间列清单 | **DESIGN RESOLVED**（§2B.1 · 54 列 / 9 个时间列） |
| `NU-09` | `agent_permissions` CK-1 的空串 / NULL 边界 | **DESIGN RESOLVED**（§2B.6）· 可选收紧 ⇒ `ND-A` **HUMAN DECISION REQUIRED** |
| — | canonical **总计数**与编号空间（分类口径已由 `D-P09-16` 冻结） | **NOT FROZEN**（规格计数见 §2B.8） |
| `ND-B` | `fk_agents_current_version` 是否 `DEFERRABLE` | **HUMAN DECISION REQUIRED** |
| `NU-C` | retention 自动化执行器 | **DESIGN DEFERRED** |

---

## 4. DEFERRED

`G/H/I/J`（P09 后 / 实际 P11）· `events` / `audit_logs`（P10）· Audit 写入（P10）·
`acl_subject_types` 的 `agent` 行 seed（P13）· `ai_request_logs.agent_id` 加 FK（新决策，未排期）·
Agent Runtime / 具体实现（未排期）· 分区维护自动化（未来 operational / runtime 阶段）。

---

## 5. 冻结后不变量（本阶段只读核验，全部 PASS）

```
P08 不回改（0010 sha256 6d9907237f80e9da）        P08 → P09 forward FK = 0
P09 → Core = 0 · Core → Domain = 0                agent → database = 0 · agent → infrastructure = 0
P09 零 seed                                       P09 无 runtime / API / worker / scheduler
G/H/I/J 未实现（0）                               P10 / P13 未提前实现（0）
```

---

## 6. Gate

```
P09 HUMAN DECISION FREEZE = COMPLETE
DECISIONS = 18/18 FROZEN（OQ 轮 12 + ND 轮 6）· 新增决策号 = 0（DESIGN WRITE 未新增）
DESIGN RESOLVED = 6（U-1 策略与资格 · U-2 · U-3 · NU-07 · NU-08 · NU-09）→ P09_SCHEMA_DESIGN.md §2B
HUMAN DECISION REQUIRED = ND-A · ND-B      DESIGN DEFERRED = NU-C      NOT FROZEN = canonical 总计数
P09 DESIGN = WRITE COMPLETE · P09 IMPLEMENTATION = NOT STARTED · 0011 = ABSENT
MIGRATION = NO · DDL = NO · DML = NO · COMMIT = NO · TAG = NO
未修改 = 0001–0010 · 任何已发布 migration · 任何测试 · 任何代码
```
