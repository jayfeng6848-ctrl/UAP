# P09_TEST_MATRIX

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE（测试义务已冻结；计数未冻结）**
**DESIGN**: **NOT STARTED** · **0011**: **ABSENT** · **IMPLEMENTATION**: NOT STARTED
**权威记录**: `P09_DECISION_LOG.md`

> **重要**：canonical test matrix 的**计数与编号空间属 P09 DESIGN 交付物，本阶段 NOT FROZEN**。
> 本阶段只登记**由 12 项冻结决策直接派生**的测试义务。

---

## 1. 本阶段测试状态

```
canonical 计数              = NOT FROZEN（→ P09 DESIGN）
编号空间                    = NOT FROZEN（→ P09 DESIGN）
**分类计数口径**            = **FROZEN**（`D-P09-16`：`pg_constraint` / `pg_indexes` 必须区分；
                              UNIQUE CONSTRAINT 1 · UNIQUE INDEX 3）
测试义务                    = 内容 FROZEN（T-01 ～ T-26）+ DESIGN RESOLVED 新增（T-27 ～ T-37）
测试文件                    = 未创建（本阶段禁止 test implementation）
现有测试                    = 未修改
Architecture Guard          = 9 passed（只读复跑，未修改任何测试）
```

---

## 2. 由冻结决策派生的测试义务（**内容冻结，计数未冻结**）

| # | 义务 | 派生自 | 断言要点 |
|---|---|---|---|
| T-01 | `tool_executions` **不是**分区表 | `D-P09-01` = B | `relkind = 'r'`；无 `pg_partitioned_table` 记录；无子分区 |
| T-02 | `tool_executions` PK = `id` | `D-P09-01` = B | `pg_constraint contype='p'` 列 = `{id}` |
| T-03 | `tool_executions.tenant_id` NOT NULL | `D-P09-02` = A | `attnotnull = true` |
| T-04 | FK `tool_executions.tenant_id → tenants.id` = RESTRICT | `D-P09-02`/`03` F12 | `confdeltype = 'r'` |
| T-05 | 9 条 FK 的 `ON DELETE` 精确匹配 | `D-P09-03` | F1/F2/F3/F12 = `r`；F7/F15/F16 = `n`(SET NULL)；F10/F11 = `c` |
| T-06 | 既有 7 条 FK 的 `ON DELETE` 未被改变 | `D-P09-03` | F4/F5 = `n`；F6/F8/F9 = `c`；F13/F14 = `r` |
| T-07 | `tool_executions` 的 FK 中 CASCADE = 0 | `D-P09-03` 语义 | 5 条 FK 的 `confdeltype` 集合 ⊆ {`r`,`n`} |
| T-08 | 幂等唯一性对象为 **UNIQUE INDEX** 且名为 `uq_tool_exec_idem` | `D-P09-04` = A | 存在于 `pg_indexes`；**不**出现于 `pg_constraint contype='u'` |
| T-09 | `agent_permissions` 有 **2** 条 CHECK，且语义精确 | `D-P09-05` = B | ① 三列全 NULL 被拒；② `effect` 非 allow/deny 被拒；**不得**合并 |
| T-10 | `agents` tenant/space consistency trigger 生效 | `D-P09-12` = A | `space_id IS NULL` 放行；`space_id NOT NULL` 且 `tenant_id` ≠ space 所属租户 ⇒ 拒绝 |
| T-11 | 该 trigger **不做**授权解释 | `D-P09-12` 边界 | 无 allow/deny/角色/permission 相关分支（源码与 catalog 双查） |
| T-12 | `G/H/I/J` **不存在** | `D-P09-06` = A | 4 个 trigger 函数名零命中（沿用既有 `P09_ACL_TRIGGERS` 断言口径） |
| T-13 | `agent_versions` 发布后不可变 | 既有（`CORE:303`）+ `D-P09-07` | `tg_version_immutable` 生效；UPDATE/DELETE 被拒 |
| T-14 | deferred FK 可补且降级顺序正确 | `D-P09-11` = A | upgrade 后 `fk_agents_current_version` 存在（`confdeltype='n'`）；downgrade 先 DROP 约束再 DROP 表 |
| T-15 | 零 seed | `SD:193` | 4 表 `count(*) = 0`；migration 内 `INSERT` = 0 |
| T-16 | `ai_request_logs` 无新增 FK | `D-P09-10` | 其 FK 列集合仍 = `{provider_id, model_id}`（AF5 口径） |
| T-17 | P08 → P09 forward FK = 0 | `D-P09-10` | 0010 内无指向 `agents*` 的 FK |
| T-18 | `agent/` 不触达数据库 | `D-P09-07` + `DEPENDENCY_RULES §4` | 既有 Guard 断言（9 passed）持续生效 |
| T-19 | revision identity 精确 | `D-P09-09` | `0011_p09_agent_tool_permission`；`filename == revision`；≤32；单头；append-only |
| T-20 | 4 表存在性与命名 | `SD:170/:213` | `agents` / `agent_versions` / `agent_permissions` / `tool_executions` 齐备 |
| T-21 | **索引对象 = 8**（清单与命名） | `D-P09-15`（ND-03） | 8 个索引名逐个存在于 `pg_indexes`；无第 9 个 P09 索引对象（逐项清单见 `P09_SCHEMA_DESIGN.md` §2.7）。**两种统计口径必须区分，不得混为一谈**：<br>① **设计层索引对象 = 8** = **7 个显式创建**的索引对象（`uq_agents_key` · `ix_agents_tenant_status` · `ix_ap_agent` · `uq_agent_perm` · `uq_tool_exec_idem` · `ix_texec_tenant_created` · `ix_texec_status`）+ **1 个 UNIQUE CONSTRAINT 的 backing index**（`uq_agent_versions`，随 `sa.UniqueConstraint` 建立）<br>② **`pg_indexes` 实测行数 = 12** = 7 显式 + 1 CONSTRAINT backing + **4 个 PRIMARY KEY index**（`agents_pkey` · `agent_versions_pkey` · `agent_permissions_pkey` · `tool_executions_pkey`） |
| T-22 | **不额外补 FK 列索引** | `D-P09-15` | P09 表上不存在为 `agents.owner_id` 等 FK 列单独建立的索引 |
| T-23 | **UQ 分类计数 = CONSTRAINT 1 / INDEX 3** | `D-P09-16`（ND-04） | `pg_constraint(contype='u')` = {`uq_agent_versions`}；`pg_indexes` 中 unique 形 = {`uq_agents_key`,`uq_agent_perm`,`uq_tool_exec_idem`} |
| T-24 | **`tool_executions` 3 条 CHECK 且未合并** | `D-P09-13`（ND-01） | `status` 非法值被拒 · `attempts = 0` 被拒 · `duration_ms = -1` 被拒 · `duration_ms IS NULL` 通过 |
| T-25 | **`agent_versions` 无状态迁移豁免** | `D-P09-14`（ND-02） | published → deprecated 被拒；published → revoked 被拒；UPDATE / DELETE 均 RAISE |
| T-26 | **`0008` 未被修改**（措辞漂移仅登记） | `D-P09-17`（ND-05） | `0008_b1_5_tool_registry.py` sha256 = `8b29cc23a93e2058`（未变）；G/H/I/J 零命中 |

**DESIGN WRITE 轮新增义务（T-27 ～ T-37）—— 新增理由：§2B 的设计收敛产出（列类型 / DEFAULT / 对象命名 /
retention contract / 顺序细节）在冻结轮并不存在，必须由测试固定，否则实现期会重新分叉；
T-36 / T-37 为 DESIGN FIX ROUND-1 依 REVIEW 发现 F-5 补入（部分谓词与表达式唯一归一语义）。**
**编号口径**：T-27+ 属**同一编号空间**的延续（不改变 canonical 计数规则；canonical 总数仍 NOT FROZEN）。

| # | 义务 | 派生自 | 断言要点 |
|---|---|---|---|
| T-27 | **列类型矩阵一致（54 列）** | `P09_SCHEMA_DESIGN.md` §2B.1（`NU-08`） | 4 表列数 = 15/12/9/18；类型分布 uuid 20 · text 16 · timestamptz(3) 9 · jsonb 6 · integer 3 |
| T-28 | **9 个时间列全为 `timestamptz(3)`** | §2B.1（平台铁律 CORE:923） | `datetime_precision = 3`；库内无 `timestamp(6)` / `timestamp without time zone` |
| T-29 | **DEFAULT 矩阵一致** | §2B.1 | `id` → `uap_uuid_v7()`；`created_at`/`updated_at` → `now()`；**其余列无默认** |
| T-30 | **对象命名逐字一致** | §2B.2 / §2B.5（`U-3` · `NU-07`） | CK 8 名 · FK 16 名 · 索引 8 名 · trigger 3 名 · function 2 名，与文档逐字相符 |
| T-31 | **retention 锚列存在且无 executor 对象** | §2B.7（`U-1`） | `tool_executions.created_at` NN；`ix_texec_tenant_created` 存在；**无** job/scheduler 表列/extension/分区对象 |
| T-32 | **deferred FK 无 `DEFERRABLE`** | §2B.9 `ND-B` 默认（FROZEN 定义） | `pg_constraint.condeferrable = false`（若 Human 裁定 `ND-B` 为真，本项随之调整） |
| T-33 | **downgrade 零残留** | §4（`D-P09-11`） | downgrade 后 4 表 + 2 function + 3 trigger + 8 索引全部消失；`fk_agents_current_version` 先被解除 |
| T-34 | **禁列扫描** | §2B.1（CORE:272） | 4 表中不存在 secret / dsn / password / token / credential 语义列名（CI 扫描口径） |
| T-35 | **一致性 trigger 与 FK 的职责边界** | §2B.3（`U-2` §5.4） | trigger 的「space 不存在」RAISE 与 `fk_agents_space` 并存；**移除 trigger 后 FK 仍拒绝非法 space_id**（证明 trigger 不替代 FK） |
| T-36 | **`uq_agents_key` 部分谓词语义（`archived_at IS NULL`）** | `D-P09-15` / `CM:268` / `INDEX_STRATEGY:107` | 同一 `(tenant_id, lower(key))` 在 `archived_at IS NULL` 时唯一；行归档（`archived_at` 置值）后该键**可被重新使用**（部分索引释放）；未归档行之间仍互斥 |
| T-37 | **`uq_agent_perm` 的 COALESCE 唯一归一语义** | `D-P09-15` / `CORE:313` / `CM:292` | 唯一性表达式 = `uq_agent_perm ON (agent_id, COALESCE(version_id, nil), COALESCE(permission_id, nil), COALESCE(tool_id, nil), COALESCE(resource_scope, ''))`；在该表达式下：<br>① `resource_scope = NULL` 与 `resource_scope = ''` **等价**（经 `COALESCE` 归一到同一值 ⇒ 互为重复、产生冲突）；<br>② `resource_scope = '   '`（空白串）**与 `''` 不等价**（`COALESCE` 不改变非 NULL 值 ⇒ 为独立占位，可与其他 `'   '` 行冲突）；<br>③ 显式 nil-uuid 占位与 `NULL` 同样**等价**；<br>④ 退化行（三目标列皆 NULL）由 CK-4 拒绝。<br>**不做** trim / normalize，**不新增** NOT NULL 或 CHECK（`ND-A` = FROZEN AS NO-TIGHTENING） |

---

## 3. 实施轮必然连带修改（**登记；计数未冻结**）

```
· 6 个既有测试文件的 FORBIDDEN / FUTURE / P09_ACL_TRIGGERS 集合（含 agents / agent_versions /
  agent_permissions / tool_executions 的禁止项）—— 实施 0011 后必须同步
· head 断言面：测试源码中 0010_b1_6_ai_gateway 共 24 处 / 10 文件（+ 平台 guard 常量）
· 平台 guard（`test_platform_timestamp_precision.py`）的 P09 覆盖范围 —— **精确目标值（FIX ROUND-1 复核得出）**：

  | 常量 / 断言 | 现值（@P08） | **P09 目标值** |
  |---|---|---|
  | `BUSINESS_TABLES` | 26 | **30**（25 业务 + 4 P09 + 1 当月子分区） |
  | `PHYSICAL_TABLES` | 27 | **31**（+ `alembic_version`） |
  | `PLATFORM_TABLES` | 20 + 5 = 25 | **29**（20 + P08 5 + P09 4） |
  | `PLATFORM_PAIRS` | 72 + 10 = 82 | **91**（+ 9 P09 时间列） |
  | `CURRENT_HEAD` | `0010_b1_6_ai_gateway` | **`0011_p09_agent_tool_permission`** |
  | PG6 `set_updated_at` trigger | 18 | **19**（仅 `agents`；另 3 表无 `updated_at`） |
  | PG6 总 trigger | 31 | **34**（+ 3） |
  | PG6 `now()` 默认 | 43 | **48**（+ 5：agents ×2 · agent_versions ×1 · agent_permissions ×1 · tool_executions ×1） |
  | PG3 覆盖集合 | 20 表/72 列 ∪ P08 5 表/10 列 | **∪ P09 4 表 / 9 列**（沿用 `P08_TIMESTAMP_COLUMNS` 先例，新增 `P09_TIMESTAMP_COLUMNS`） |

  **P09 四表的 9 个 timestamp columns（PG3 静态清单）**
  ```
  agents            : archived_at · created_at · updated_at
  agent_versions    : published_at · created_at
  agent_permissions : created_at
  tool_executions   : started_at · finished_at · created_at
  ⇒ 4 表 / 9 列，全部 timestamptz(3)
  ```
→ 上述均属 P09 DESIGN / IMPLEMENTATION 交付物，本阶段**未修改任何测试**
```

---

## 4. 本阶段**未**冻结（NOT FROZEN）

```
· canonical 总计数与编号空间（分类口径已由 D-P09-16 冻结；T-27+ 为同空间延续）
· 测试文件命名与用例编号
· 每个义务对应的断言写法与夹具策略
· 参数化/集合型断言的最终形态
· `ND-A`（resource_scope <> ''）与 `ND-B`（DEFERRABLE）相关断言 —— 须待 Human 裁定后方可写死
  （T-32 暂按 FROZEN 定义断言 `condeferrable = false`）
```

---

## 5. Gate

```
P09 测试义务 = FROZEN（T-01 ～ T-26）+ DESIGN RESOLVED（T-27 ～ T-37）⇒ 设计层合计 37 项
P09 canonical 计数 = NOT FROZEN（分类计数口径 = FROZEN · D-P09-16）
本阶段：测试文件创建 = 0 · 测试修改 = 0 · Guard = 9 passed
P09 DESIGN = WRITE COMPLETE · 0011 = ABSENT
```
