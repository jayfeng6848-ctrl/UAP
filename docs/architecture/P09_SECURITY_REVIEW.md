# P09_SECURITY_REVIEW

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE（安全边界 FROZEN）**
**DESIGN**: **NOT STARTED** · **0011**: **ABSENT** · **IMPLEMENTATION**: NOT STARTED
**权威记录**: `P09_DECISION_LOG.md`

> 本文档只登记**由本次冻结决策直接决定**的安全边界，**不新增**任何安全设计。

---

## 1. 审计范围与结论

| # | 检查项 | 结论 | 冻结依据 |
|---|---|---|---|
| S1 | `agents` tenant/space 归属一致性 | **DB 层将有一致性约束**（structural only） | `D-P09-12` = A |
| S2 | trigger 是否承担授权解释 | **否 —— 明确禁止** | `D-P09-12` 边界 + R-D-14（FROZEN SECURITY INVARIANT：不在 trigger 做授权解释） |
| S3 | 历史执行记录是否会被级联清除 | **否** —— `tool_executions` 的 FK 中 CASCADE = 0 | `D-P09-03`（F12/F13/F14 R · F15/F16 SN） |
| S4 | 租户删除是否被静默绕过 | **否** —— `agents.tenant_id` / `tool_executions.tenant_id` = RESTRICT；后者为 **NOT NULL** | `D-P09-02` · `D-P09-03`（F1/F12） |
| S5 | 归属人（`owner_id`）删除语义 | **RESTRICT**（owner 被引用时不可删） | `D-P09-03`（F3） |
| S6 | 归属人（attribution）可保留性 | `agent_versions.published_by` / `tool_executions.actor_id` = **SET NULL**（记录保留、attribution 置空） | `D-P09-03`（F7/F16） |
| S7 | Agent 是否可获得 DB 直连能力 | **否** —— `agent/` 不得 import sqlalchemy / psycopg / infrastructure | `DEPENDENCY_RULES §4` · `D-P09-07` |
| S8 | P09 是否引入权限运行时 | **否** —— SCHEMA ONLY；`agent_permissions` 仅作**数据表达**（白名单） | `D-P09-07` · `CORE:309` |
| S9 | 是否引入 P09 权限模型（运行时） | **否** | `D-P09-07` |
| S10 | seed 是否带入任何主体/权限行 | **否** —— P09 零 seed；`acl_subject_types` 的 `agent` 行属 **P13** | `SD:193` · `SEED_STRATEGY:111-117`（`D-B14-01 = A`） |
| S11 | 是否新增 RLS | **否**（本次冻结未授权任何 RLS） | 范围（`P09_SCOPE.md §3`） |
| S12 | 是否新增 G/H/I/J ACL 判定 | **否** —— P09 后 | `D-P09-06` = A |
| S13 | 是否引入外部 Provider / SDK 访问 | **否** —— SCHEMA ONLY；P09 不触 provider runtime | `D-P09-07` |
| S14 | `ai_request_logs` 是否新增结构依赖 | **否** —— `agent_id`/`actor_id`/`tenant_id`/`space_id` 维持 NO FK | `D-P09-10` |
| S15 | 是否可能因 P09 迫使 B1-6 变更 | **否**（本阶段只读核验：无 cross-phase conflict） | B1-6 Protection Check |
| S16 | `agents.config jsonb` 是否允许凭据 | **否** —— B0 已规定禁止 DSN / 凭据（CI 扫描项），P09 不改变 | `CORE:272`（`CM` 同） |

---

## 2. 关键安全边界的精确表述（FROZEN）

### 2.1 一致性 trigger 的边界（`D-P09-12`）

```
允许的能力 : 校验 space_id 非空时 agents.tenant_id = (SELECT tenant_id FROM spaces WHERE id = NEW.space_id)
禁止的能力 : 解释 ALLOW / DENY · 权限继承 · 角色 · 资源授权 · ACL decision
             （授权解释仍属 Authorization Layer —— 与 R-D-14 / D-B14-10 表述一致）
```
> 与 `tg_resources_tenant_space_consistency` 的先例表述一致：**structural integrity only**。

### 2.2 历史记录保护（`D-P09-03`）

```
tool_executions 的 5 条 FK：F12 RESTRICT · F13 RESTRICT · F14 RESTRICT · F15 SET NULL · F16 SET NULL
⇒ CASCADE = 0 ⇒ 删除 Agent 或 User **不会**清除其历史执行记录
```

### 2.3 Agent 的执行边界（既有铁律，P09 不改变）

```
Agent ─▶ Policy ─▶ Tool ─▶ Service ─▶ Database
agent/** 不得 import sqlalchemy / psycopg / psycopg2 / infrastructure / apps
（由 tests/architecture/test_dependency_rules.py 强制）
```

### 2.4 零 seed 与主体注册（FROZEN）

```
P09 表在交付后 rows = 0（P00–P10 无 seed）
acl_subject_types 的 'agent' 行属 P13 ⇒ P09 期间不得注册新 subject type
```

---

## 3. 已登记（不阻断 / 未授权处理）

| 项 | 内容 | 状态 |
|---|---|---|
| R-1 | `agents.owner_id` = RESTRICT 与既有先例（`spaces.owner_id` / `resources.owner_id` = SET NULL）方向相反 | **仅登记**（Human 已裁定；不代表先例被推翻） |
| R-2 | `agents.space_id` 的一致性由新增 trigger 保证（此前 DB 层无校验） | 由 `D-P09-12` 关闭 |
| R-3 | 未冻结项 `U-1` / `U-2` / `U-3` 不含安全语义 | 待 DESIGN（不引入安全设计） |
| R-4 | `resource_permissions` 的 `subject_type='agent'` 分支（`tg_acl_subject_exists`） | P09 后（`D-P09-06`） |
| R-5 | `tool_executions` 追加 2 条**数值域** CK（`attempts >= 1` · `duration_ms >= 0`）—— 纯域校验，**不含授权语义** | `D-P09-13`（ND-01）；登记，不引入安全设计 |
| R-6 | `agent_versions` 的 published 行**无状态迁移豁免** ⇒ deprecate / revoke 在 DB 层不可达（属后续应用层治理阶段） | `D-P09-14`（ND-02）；登记的**已知语义**，非缺陷 |
| R-7 | `0008_b1_5_tool_registry.py:36-37` 的措辞漂移（「仍属 P09」）**未修改**（append-only）；已在 P09 文档登记 | `D-P09-17`（ND-05）· `P09_DECISION_LOG.md` §4A |
| R-8 | 未冻结项 `NU-07` / `NU-08` / `NU-09` 不含安全语义 | 待 DESIGN |

---

## 3A. DESIGN WRITE 安全复核（2026-09-17 · 十项）

| # | 检查 | 结论 | 依据 |
|---|---|---|---|
| D-1 | retention hard delete 是否造成越权 | **否** —— 仅删除 `tool_executions` 自身行；本表**无 incoming FK**；父侧删除由 RESTRICT 保护；删除动作属运维通道，**不含授权判定** | §2B.7 · `D-P09-01` |
| D-2 | `SET NULL` 是否符合 attribution 语义 | **是** —— `agent_id` / `actor_id` = SET NULL：保留历史记录、归属置空（与 `D-B14-09 = A` 的 actor attribution 语义一致） | `D-P09-03` F15/F16 · `P09_DEPENDENCY.md §3` |
| D-3 | `RESTRICT` 是否保护 tenant / tool / tool_version | **是** —— F12/F13/F14 = RESTRICT ⇒ 存在执行记录时父行不可删（含 `tenant_id` **NOT NULL**） | `D-P09-02` / `D-P09-03` |
| D-4 | published immutable 是否避免绕过治理 | **是** —— `BEFORE UPDATE OR DELETE` 双拒、**无豁免**；deprecate/revoke 属后续应用层治理 | `D-P09-14` · §2B.4 |
| D-5 | agents tenant/space consistency 是否仅结构完整性 | **是** —— 三分支（NULL 放行 / 匹配放行 / 不匹配 RAISE），**无授权分支**；不写他表、不写审计、不级联 | `D-P09-12` · §2B.3 · R-D-14 |
| D-6 | `agent_permissions` 是否避免形成 runtime authorization evaluator | **是** —— 无 evaluator / 无 RLS / 无 role-deny 解析；P09 仅交付**数据表达**（白名单） | `D-P09-07` · `CORE:309` |
| D-7 | `conditions` 是否被解释为执行逻辑 | **否** —— storage-only（只存不解释） | `R-D-15` / `R2-D-15` · §2B.1 |
| D-8 | `config` / `definition` / `allowed_tools` 是否含秘密字段风险 | **低** —— 均为 opaque 数据载体，**无** secret / DSN / token 列；`agents.config` 禁 DSN/凭据的 CI 扫描义务延续 | `CORE:272` · T-34 |
| D-9 | 是否错误引入 audit / event | **否** —— `events` / `audit_logs` 属 **P10**（P09 交付 0 个对象） | `SD:171` · `D-B14-07` |
| D-10 | 是否错误引入 ACL `G/H/I/J` | **否** —— 保持「P09 后」；P09 不创建 trigger / function | `D-P09-06` |

**新登记（不阻断）**

| 项 | 内容 | 状态 |
|---|---|---|
| R-9 | CK-1 对 `resource_scope = ''` / `'   '` **视为非 NULL ⇒ 满足**（不做 trim/normalize）；若需拒绝空串须追加 `<> ''`（先例 `ck_credentials_secret`，0003:155）⇒ 改动冻结 CHECK 文本 | **HUMAN DECISION REQUIRED（`ND-A`）** |
| R-10 | `fk_agents_current_version` 默认**不带 `DEFERRABLE`**（依冻结定义）；若要求 deferrable ⇒ 改动冻结约束定义 | **HUMAN DECISION REQUIRED（`ND-B`）** |
| R-11 | retention **executor** 未实现（人工运维；自动化属未来 operational 阶段） | `DESIGN DEFERRED` |
| R-12 | 一致性 trigger 的存在性 RAISE 与 `fk_agents_space` 并存（职责边界见 §2B.3；测试义务 T-35） | DESIGN RESOLVED（登记备查） |

---

## 4. Gate

```
BLOCKER = 0 · RISK = 0（R-1 / R-5 ～ R-12 均为登记项，非风险）
P09 DESIGN = WRITE COMPLETE · IMPLEMENTATION = NOT STARTED · 0011 = ABSENT
未引入新安全设计 = 确认 · 未引入 RLS = 确认 · 零 seed = 确认
ND 轮新增 CK（D-P09-13）为**域校验**，无授权语义 = 确认
DESIGN WRITE 十项安全复核（D-1 ～ D-10）全部 PASS = 确认
HUMAN DECISION REQUIRED = ND-A（空串收紧）· ND-B（DEFERRABLE）—— 均无安全边界影响
```
