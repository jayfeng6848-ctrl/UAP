# P09_MIGRATION_PLAN

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE（迁移 identity 与顺序规则 FROZEN）**
**DESIGN**: **NOT STARTED** · **0011**: **ABSENT（本阶段不得创建）**
**权威记录**: `P09_DECISION_LOG.md`（`D-P09-09` / `D-P09-11` / `D-P09-01`）

> 本文档只冻结**迁移的身份与顺序规则**。具体 DDL 语句、对象命名表、列级细节属 **P09 DESIGN** 交付物。
> **本阶段不得创建 `0011`，不得执行任何 migration。**

---

## 1. Revision Identity（FROZEN，`D-P09-09`）

| 项 | 值 |
|---|---|
| revision | **`0011_p09_agent_tool_permission`** |
| filename | **`0011_p09_agent_tool_permission.py`** |
| `filename == revision` | 是（沿用 0001–0009 的 1:1 约定） |
| 长度 | **30** ≤ 32（`alembic_version.version_num = varchar(32)`） |
| 格式 | `<4位序号>_<snake_case 语义>`（`MIGRATION_IMPLEMENTATION_CONTRACT §7:83`） |
| `down_revision` | `0010_b1_6_ai_gateway`（当前唯一 head） |
| 单头约束 | 必须保持 single head（`§7:85`） |
| append-only | 已发布 revision 永不改写（`§7:86`） |
| **当前状态** | **ABSENT —— 本阶段不得创建** |

---

## 2. 迁移内容范围（FROZEN 边界）

```
包含（P09 范围，见 P09_SCOPE.md §2）:
  · agents · agent_versions · agent_permissions · tool_executions（4 表）
  · 上述表的 PK / FK（16 条，含 9 条新冻结的 ON DELETE）/
    **CK 合计 8 条**（agents 2 · agent_versions 1 · agent_permissions 2 [D-P09-05] ·
    tool_executions 3 [D-P09-13]）/ NN / NULL / DEFAULT
  · **索引 8 个**（`D-P09-15`；4 个 UQ 形 + 4 个查询形），含：
      uq_agents_key · ix_agents_tenant_status · uq_agent_versions · ix_ap_agent ·
      uq_agent_perm · uq_tool_exec_idem（UNIQUE INDEX · D-P09-04）·
      ix_texec_tenant_created · ix_texec_status
  · agents tenant/space consistency trigger（D-P09-12）
  · tg_version_immutable（agent_versions；与 tool_versions 共用名 D-B15-03 = A）
  · updated_at trigger（按平台既有 set_updated_at() 模式）
  · deferred FK fk_agents_current_version（尾部补）

不包含（明确禁止）:
  ✗ 任何分区 DDL（D-P09-01 = B：tool_executions 不分区）
  ✗ G/H/I/J（D-P09-06 = A）
  ✗ events / audit_logs（P10）
  ✗ 任何 seed / INSERT（SD:193）
  ✗ ai_request_logs 的任何变更（D-P09-10）
  ✗ 保留期自动清理 job / scheduler / pg_partman 集成（U-1 未冻结）
  ✗ 对 0001–0010 的任何修改
```

---

## 3. Upgrade 顺序（FROZEN 依据）

```
[1] agents                       —— **不含** current_version_id 的 FK 约束（列存在）
[2] agent_versions               —— agent_id → agents 正常声明（CASCADE）
[3] agent_permissions            —— agent_id / version_id / permission_id / tool_id + 2 条 CHECK（D-P09-05）
[4] tool_executions              —— **不分区**；tenant_id NOT NULL；PK = id；**3 条 CHECK**（D-P09-13）
[5] 索引                          —— **8 个对象**（D-P09-15）：uq_agents_key · ix_agents_tenant_status ·
                                    uq_agent_versions · ix_ap_agent · uq_agent_perm ·
                                    uq_tool_exec_idem（UNIQUE INDEX，部分谓词）·
                                    ix_texec_tenant_created · ix_texec_status
                                    声明形式：`uq_agent_versions` 用 `sa.UniqueConstraint`；
                                    其余 3 个 UQ 形用 `CREATE UNIQUE INDEX`（部分/表达式唯一只能是 index）；
                                    4 个查询形用 `CREATE INDEX`（0008:178 / 0010:296 先例）
[6] function                      —— `enforce_agents_tenant_space_consistency()` ·
                                    `enforce_agent_versions_immutable()`（**先于 trigger 创建**）
                                    复用 `set_updated_at()`（0003）· `uap_uuid_v7()`（0002），**不重建**
[7] trigger                       —— `tg_agents_set_updated_at`（BEFORE UPDATE ON agents）·
                                    `tg_version_immutable`（BEFORE UPDATE OR DELETE ON agent_versions）·
                                    `tg_agents_tenant_space_consistency`（BEFORE INSERT OR UPDATE ON agents）
                                    形态先例：0003:47-55 · 0007:232-236 · 0008:204-211
[8] deferred FK（**最后**）          —— `ALTER TABLE agents ADD CONSTRAINT fk_agents_current_version
                                    FOREIGN KEY (current_version_id) REFERENCES agent_versions(id)
                                    ON DELETE SET NULL`（`SD §4.1:132-134` 逐字）
                                    **不加 `DEFERRABLE`**：三步顺序（两表均已存在后才 ADD）已消除对 deferral 的需求，
                                    且 `D-P09-11` 明令「不得修改其升级侧既有定义」；
                                    若 Human 要求 `DEFERRABLE` ⇒ `ND-B`（见 `P09_SCHEMA_DESIGN.md` §2B.9）
多表 DDL 若需要，按平台既有 `op.execute` 显式 DDL 模式（P09 = **不分区**，无子分区对象 —— `D-P09-01` = B）
对象命名表（FK 16 · CK 8 · 索引 8 · trigger 3 · function 2）= `P09_SCHEMA_DESIGN.md` §2B.2
列类型 / DEFAULT 矩阵（54 列）= `P09_SCHEMA_DESIGN.md` §2B.1（时间列一律 `_TS` = `postgresql.TIMESTAMP(timezone=True, precision=3)`）
```
> 依据：`STEP1B_SCHEMA_DEPENDENCY.md §4.1:124-134`（deferred FK 三步）· `:170`（P09 交付链）·
> `D-P09-01`（无分区步骤）· `D-P09-12`（新增 consistency trigger）。

---

## 4. Downgrade 顺序（FROZEN，`D-P09-11` = A：0005 同构）

```
[1] DROP TRIGGER   tg_agents_tenant_space_consistency ON agents ·
                   tg_version_immutable ON agent_versions ·
                   tg_agents_set_updated_at ON agents
[2] DROP FUNCTION  enforce_agents_tenant_space_consistency() · enforce_agent_versions_immutable()
                   （**不 DROP** set_updated_at / uap_uuid_v7 —— 先例 0007:266 / 0008:225）
[3] DROP CONSTRAINT fk_agents_current_version     ← **优先解除 deferred 约束**（D-P09-11）
[4] DROP INDEX     **7 个**显式索引（4 查询形 + 3 个 UQ 形索引：`uq_agents_key` · `uq_agent_perm` ·
                   `uq_tool_exec_idem`；`uq_agent_versions` = **UNIQUE CONSTRAINT**，随表移除 — 0008:196 先例）
[5] DROP TABLE     tool_executions               ← 逆依赖序：先删叶子（P09 内无 incoming FK）
[6] DROP TABLE     agent_permissions              ← 引用 agents + agent_versions
[7] DROP TABLE     agent_versions                 ← 引用 agents（F6 CASCADE）
[8] DROP TABLE     agents                         ← 最后（其 current_version_id 约束已于 [3] 解除）
> 严格逆序、无遗留 orphan object；不得改写 0001–0010（append-only）。
```
> 先例：`0005_b1_3_authorization.py` — upgrade `ADD CONSTRAINT`（`:431-436`）·
> downgrade 先 `DROP CONSTRAINT IF EXISTS`（`:519-520`）再 `DROP TABLE roles`（`:37`）。

---

## 5. 验证清单（DESIGN / IMPLEMENTATION 轮执行；本阶段不执行）

```
□ revision / filename / down_revision 与 §1 逐字一致
□ 唯一 head = 0011_p09_agent_tool_permission
□ 4 表存在；tool_executions **relkind='r'**（非分区）
□ tool_executions PK = id；tenant_id NOT NULL
□ 16 条 FK 的 ON DELETE 逐条匹配（9 条新冻结 + 7 条既有）
□ tool_executions 的 FK 中 CASCADE = 0
□ **索引对象 = 8**（D-P09-15）· **不额外补 FK 列索引**
□ **UQ 计数：`pg_constraint` = 1（uq_agent_versions）· `pg_indexes` = 3**（D-P09-16）
□ uq_tool_exec_idem 存在于 pg_indexes 且不在 contype='u'
□ agent_permissions 2 条 CHECK 语义精确、未合并
□ **tool_executions 3 条 CHECK 齐备且未合并**（D-P09-13）
□ **agent_versions：published 行 UPDATE / DELETE 均被拒；无状态迁移豁免**（D-P09-14）
□ agents consistency trigger 生效且无授权语义
□ agent_versions 发布后不可变（tg_version_immutable）
□ deferred FK 存在（confdeltype='n'）；downgrade 顺序正确
□ **列类型矩阵一致**（54 列；类型分布 uuid 20 / text 16 / timestamptz(3) 9 / jsonb 6 / integer 3）——
  见 `P09_SCHEMA_DESIGN.md` §2B.1
□ **9 个时间列全部为 `timestamptz(3)`**（不得使用 `sa.DateTime`；平台 guard 覆盖）
□ **CK 8 / FK 16 / 索引 8 / trigger 3 / function 2 名称逐字一致**（`P09_SCHEMA_DESIGN.md` §2B.2）
□ **deferred FK 存在**（`confdeltype='n'`）；**无 `DEFERRABLE`**（除非 `ND-B` 另有裁定）
□ 零 seed；无 INSERT
□ G/H/I/J 不存在；events/audit_logs 不存在
□ 0010 与 0001–0009 未被修改（sha256 对照）
```

---

## 6. Production Guard（承 PLATFORM 铁律）

```
· formal `uap` 库全程保持 0 业务表（迁移验证仅在一次性库执行）
· 不得对正式 `uap` 执行 upgrade
· 不得在 DB 中留下测试残留
```

---

## 7. 本阶段**未**冻结（NOT FROZEN）

```
· 每条 DDL 的具体 SQL 文字（**对象命名表已 DESIGN RESOLVED** = `P09_SCHEMA_DESIGN.md` §2B.2）
· 全部 CHECK 的约束名 → **DESIGN RESOLVED**（§2B.5 · 8 个名称）
· `agents` consistency trigger 名称 / 函数名 → **DESIGN RESOLVED**（§2B.3）
· `tg_version_immutable` 的函数名 → **DESIGN RESOLVED**（§2B.4）
· 列级逐项定义表（类型 / NULL / DEFAULT）与时间列清单 → **DESIGN RESOLVED**（§2B.1）
· 升级 / 降级步骤的最终编号形式 → 本文档 §3 / §4 已定
· 仍需 Human Decision：`ND-A`（`resource_scope <> ''`）· `ND-B`（`DEFERRABLE`）
```

---

## 8. Gate

```
P09 revision identity = FROZEN（0011_p09_agent_tool_permission）
P09 迁移内容范围 = FROZEN（4 表 · 16 FK · 8 CK · 8 索引 · 3 trigger · 2 function · 1 deferred FK · 0 seed）
P09 upgrade/downgrade 顺序规则 = FROZEN（§3 / §4）· 顺序细节 = DESIGN RESOLVED
0011 = ABSENT（本阶段未创建）
MIGRATION = NO · DDL = NO · DML = NO
P09 DESIGN = WRITE COMPLETE · IMPLEMENTATION = NOT STARTED
HUMAN DECISION REQUIRED = ND-A · ND-B（不阻断其余设计）
```
