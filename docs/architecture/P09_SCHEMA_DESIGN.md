# P09_SCHEMA_DESIGN

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE + DESIGN RESOLVED**
**DESIGN**: **P09 DESIGN WRITE = COMPLETE**（§2B 承载六项 DESIGN UNKNOWN 的收敛结果）
**0011**: **ABSENT** · **IMPLEMENTATION**: NOT STARTED · **权威记录**: `P09_DECISION_LOG.md`
**冻结轮次**: OQ 轮（`D-P09-01`～`D-P09-12`）+ ND 轮（`D-P09-13`～`D-P09-18`，2026-09-17）
**设计轮次**: DESIGN WRITE（2026-09-17，收敛 `U-1` / `U-2` / `U-3` / `NU-07` / `NU-08` / `NU-09`）

> **`DESIGN RESOLVED` ≠ `HUMAN DECISION FROZEN`**：§2B 未新增任何 `D-P09-*` 决策号；
> 仍需 Human 决定的两项见 §2B.9（`ND-A` / `ND-B`）。

> 本文档只记录**已冻结**的结构事实（承接 `D-P09-01` / `02` / `04` / `05` / `12`）。
> 凡标注 **NOT FROZEN** 者，本阶段**不得**推定、补齐或计数。

---

## 1. 表清单（FROZEN）

| # | 表 | purpose | 来源 |
|---|---|---|---|
| 1 | `agents` | 执行实体（**不是模型**）：编排工具、策略与模型路由 | `CORE:286` |
| 2 | `agent_versions` | Agent 定义的不可变快照（发布后不可改） | `CORE:297` |
| 3 | `agent_permissions` | Agent 能碰什么（权限、工具、资源范围）—— 白名单 | `CORE:309` |
| 4 | `tool_executions` | 执行记录 + 幂等锚点 + 重试依据 | `CORE:352` |

---

## 2. 决策层结构事实（FROZEN）

### 2.1 `tool_executions` 形态（`D-P09-01` = B）

```
分区       : **不分区**（无 PARTITION BY；无子分区对象）
PK         : `id`（保持不变）
保留       : 90 天 hard delete
执行机制   : NOT FROZEN（U-1）—— 本阶段不定义、不实现、不扩展
```

### 2.2 `tool_executions.tenant_id`（`D-P09-02` = A）

```
NOT NULL   : **是**
FK         : tenant_id → tenants.id ON DELETE RESTRICT（F12）
```

### 2.3 幂等唯一性对象（`D-P09-04` = A）

```
对象名     : **uq_tool_exec_idem**
对象类型   : **UNIQUE INDEX**
谓词       : idempotency_key IS NOT NULL（部分唯一）
计数口径   : 按 **UNIQUE INDEX** 计（不得计为 UNIQUE CONSTRAINT）
列         : (tool_id, idempotency_key)
```

### 2.4 `agent_permissions` CHECK（`D-P09-05` = B）

```
CHECK 数   : **2**（不得合并）

CHECK-1 : permission_id IS NOT NULL OR tool_id IS NOT NULL OR resource_scope IS NOT NULL
CHECK-2 : effect IN ('allow', 'deny')

约束名     : NOT FROZEN（U-3 —— 命名待 P09 DESIGN 确定）
canonical  : 2 CHECK constraints（口径已冻结；具体名称待 DESIGN）
```

### 2.5 `agents` tenant/space 一致性（`D-P09-12` = A）

```
新增对象   : tenant/space consistency trigger（挂 agents）
触发时机   : BEFORE INSERT OR UPDATE（沿用 F2 先例形态 —— 最终时机细节属 DESIGN 交付物）
语义       : space_id IS NULL           → 允许
             space_id IS NOT NULL       → 必须 agents.tenant_id = spaces.tenant_id
边界       : **STRUCTURAL INTEGRITY ONLY**
             绝对不得解释 ALLOW / DENY / 权限继承 / 角色 / 资源授权 / ACL decision
             授权解释仍属 Authorization Layer（R-D-14 精神不变）
对象名     : NOT FROZEN（U-2 —— 待 P09 DESIGN 确定）
```

### 2.6 版本不可变性（既有冻结，P09 承接）

```
agent_versions.status = 'published' 后禁止 UPDATE / DELETE
实现       : trigger `tg_version_immutable`（**与 tool_versions 共用同一名** —— D-B15-03 = A）
双保险     : trigger + 撤掉 UPDATE 权限（CORE:303）
语义边界   : **不允许** published → deprecated · **不允许** published → revoked（`D-P09-14` = ND-02）
             deprecate / revoke 属**后续应用层治理阶段**（P09 不实现）
实现同构   : 沿用 `0008` 同构语义；**不得修改 `0008`**、不得设状态迁移豁免
函数名     : **NOT FROZEN**（`NU-07` —— trigger 名共用已冻结，函数名未冻结）
```

### 2.7 索引清单与权威归属（`D-P09-15` = ND-03）

```
权威       : **`STEP1B_INDEX_STRATEGY`** = P09 最终索引清单权威
             （`CORE §12` 为其**不完整摘要** —— 先例：0010 实作 5 条 vs CORE §12 仅 2 条；**CORE §12 不回改**）
交付对象   : **8 个** 非 PK 索引对象
  ① uq_agents_key             部分唯一（UNIQUE INDEX 形式）
  ② ix_agents_tenant_status   btree
  ③ uq_agent_versions         唯一（UNIQUE CONSTRAINT 形式）
  ④ ix_ap_agent               btree
  ⑤ uq_agent_perm             表达式唯一（UNIQUE INDEX 形式）
  ⑥ uq_tool_exec_idem         部分唯一（UNIQUE INDEX 形式 · D-P09-04）
  ⑦ ix_texec_tenant_created   btree
  ⑧ ix_texec_status           部分 btree（**纳入本次 P09 交付**）
权威行号   : `INDEX_STRATEGY §1:107-108`（agents）· `:114-115`（agent_versions / agent_permissions）·
             `:129-131`（tool_executions）· 命名规范 `§4:208-209` · 三分汇总 `§5:217-219`
清单指针   : 本节为本清单的**唯一展开处**；`P09_SCOPE.md` / `P09_DEPENDENCY.md` / `P09_TEST_MATRIX.md`
             以指针引用，不重复展开
不补       : **不额外补 FK 列索引**（`INDEX_STRATEGY §3`：`agents.owner_id` = P3；
             FK 反查补索引进入 **P12**，`INDEX_STRATEGY:202`）
```

### 2.8 `tool_executions` CHECK 数（`D-P09-13` = ND-01）

```
CHECK 数   : **3**（采用 `CM:253` 超集；`CORE:357` 为摘要遗漏）
  ① status IN ('running','succeeded','failed','denied','timeout')
  ② attempts >= 1
  ③ duration_ms >= 0
P09 CK 合计: **8**（agents 2 · agent_versions 1 · agent_permissions 2 [§2.4] · tool_executions 3 [本节]）
语义       : `duration_ms IS NULL` 行**通过**（NULL 语义）；`attempts` 为 NN ⇒ ② 为有效域收紧
约束名     : **NOT FROZEN**（与 `U-3` 同族）
```

### 2.9 UQ 计数口径（`D-P09-16` = ND-04）

```
UNIQUE CONSTRAINT = **1**  → uq_agent_versions
UNIQUE INDEX      = **3**  → uq_agents_key · uq_agent_perm · uq_tool_exec_idem
计数要求   : canonical 统计**必须区分** `pg_constraint` 与 `pg_indexes`
（与 D-B15-06 完全同构；部分唯一 `WHERE` 与表达式唯一 `COALESCE` 只能是 index 形式）
```

---

## 2B. DESIGN WRITE 收敛（2026-09-17 · **DESIGN RESOLVED，非 Human Decision**）

> 本节收敛 `U-1` / `U-2` / `U-3` / `NU-07` / `NU-08` / `NU-09` 六项 DESIGN UNKNOWN。
> **`DESIGN RESOLVED` ≠ `HUMAN DECISION FROZEN`**：本节内容由「冻结决策 + 历史先例 + 显式架构规则」
> 唯一确定，**未新增任何 `D-P09-*` 决策号**；若与既有冻结决策冲突，以冻结决策为准。

### 2B.1 列类型 / DEFAULT 矩阵（`NU-08`）

**类型先例（实现必守）**
```
时间列 : `postgresql.TIMESTAMP(timezone=True, precision=3)`（0010:86 `_TS`；0001–0008 的 `sa.DateTime` 已由 0009 纠正）
         ⇒ **P09 四表一律直接用 `_TS` 形式**，不得使用 `sa.DateTime`
UUID   : `postgresql.UUID(as_uuid=True)`，PK/`id` 加 `server_default=sa.text("uap_uuid_v7()")`（0008:89-90 · 0010:127-128）
JSONB  : `postgresql.JSONB()`
文本   : `sa.Text()`（平台无 `varchar(n)` 先例）· 整型 : `sa.Integer()`
DEFAULT: 仅 `id → uap_uuid_v7()` · `created_at/updated_at → now()`（0010 另有 boolean 默认 true 的个案）
         其余列**无 DEFAULT**（NN 列必须由写入方提供；0008 `input_schema`/`output_schema` 为 NN jsonb 无默认的先例）
```

**`agents`（15 列）**

| column | type | null | default | 语义 | 来源 |
|---|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK | CORE:287 · CM:266/270 |
| `tenant_id` | uuid | NN | — | FK F1 → tenants R | CM:267/270 |
| `space_id` | uuid | NULL | — | FK F2 → spaces R | CM:267/271 |
| `owner_id` | uuid | NN | — | FK F3 → users R | CM:267/270 |
| `key` | text | NN | — | 租户内 opaque 标识 | CORE:289 · D-B15-05 先例 |
| `name` | text | NN | — | 展示名 | CORE:289 |
| `description` | text | NULL | — | 描述 | CM:271 |
| `status` | text | NN | — | CK-1（4 值域） | CORE:291 |
| `max_risk_level` | text | NN | — | CK-2（4 值域） | CORE:291 |
| `current_version_id` | uuid | NULL | — | FK F5（**deferred**）→ agent_versions SN | CORE:288 |
| `default_route_id` | uuid | NULL | — | FK F4 → ai_routes SN | CORE:289 |
| `config` | jsonb | NN | — | 配置（**禁 DSN / 凭据**） | CM:270/272 |
| `archived_at` | timestamptz(3) | NULL | — | 归档时间（部分唯一索引谓词） | CM:271 |
| `created_at` | timestamptz(3) | NN | `now()` | — | 平台惯例 |
| `updated_at` | timestamptz(3) | NN | `now()` | trigger 维护（CORE:920） | CM:270 |

**`agent_versions`（12 列）**

| column | type | null | default | 语义 | 来源 |
|---|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK | CORE:298 |
| `agent_id` | uuid | NN | — | FK F6 → agents C | CM:279/282 |
| `version` | integer | NN | — | 版本序号（UQ 组成） | CORE:300 |
| `definition` | jsonb | NN | — | 定义快照 | CM:282 |
| `input_schema` | jsonb | NULL | — | 输入契约 | CM:283 |
| `output_schema` | jsonb | NULL | — | 输出契约 | CM:283 |
| `allowed_tools` | jsonb | NN | — | 允许工具清单（快照） | CM:282 |
| `checksum` | text | NN | — | 内容校验和 | CM:282 |
| `status` | text | NN | — | CK-3（4 值域） | CORE:302 |
| `published_by` | uuid | NULL | — | FK F7 → users SN | CM:279/283 |
| `published_at` | timestamptz(3) | NULL | — | 发布时间 | CM:283 |
| `created_at` | timestamptz(3) | NN | `now()` | — | CM:282 |

**`agent_permissions`（9 列）**

| column | type | null | default | 语义 | 来源 |
|---|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK | CORE:310 |
| `agent_id` | uuid | NN | — | FK F8 → agents C | CM:291 |
| `version_id` | uuid | NULL | — | FK F9 → agent_versions C | CM:291 |
| `permission_id` | uuid | NULL | — | FK F10 → permissions C | CM:291 |
| `tool_id` | uuid | NULL | — | FK F11 → tools C | CM:291 |
| `resource_scope` | text | NULL | — | 范围限定（text，**不解释**） | CORE:312 |
| `effect` | text | NN | — | CK-5（allow/deny） | CM:291 · CORE:312 |
| `conditions` | jsonb | NULL | — | **storage-only**（R-D-15） | CORE:312 |
| `created_at` | timestamptz(3) | NN | `now()` | — | CM:291 |

**`tool_executions`（18 列）**

| column | type | null | default | 语义 | 来源 |
|---|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK | CORE:353 |
| `tenant_id` | uuid | NN | — | FK F12 → tenants R | CM:251/254 |
| `tool_id` | uuid | NN | — | FK F13 → tools R | CM:251/254 |
| `tool_version_id` | uuid | NN | — | FK F14 → tool_versions R | CM:251/254 |
| `agent_id` | uuid | NULL | — | FK F15 → agents SN | CM:251/255 |
| `actor_id` | uuid | NULL | — | FK F16 → users SN | CM:251/255 |
| `idempotency_key` | text | NULL | — | 幂等键（部分唯一） | CM:252/255 |
| `status` | text | NN | — | CK-6（5 值域） | CORE:357 |
| `input_digest` | text | NN | — | 输入摘要（非明文载荷） | CM:254 |
| `output_digest` | text | NULL | — | 输出摘要 | CM:255 |
| `risk_level` | text | NULL | — | 运行时风险等级（**无 CK**，避免新增词表） | CM:255 |
| `attempts` | integer | NN | — | 尝试次数（CK-7） | CM:253/254 |
| `started_at` | timestamptz(3) | NN | — | 执行开始（应用提供） | CM:254 |
| `finished_at` | timestamptz(3) | NULL | — | 执行结束 | CM:255 |
| `duration_ms` | integer | NULL | — | 耗时（CK-8） | CM:253/255 |
| `error_code` | text | NULL | — | 错误码（opaque） | CM:255 |
| `correlation_id` | text | NN | — | 链路追踪（先例：0010:275 `Text`） | CM:254 |
| `created_at` | timestamptz(3) | NN | `now()` | 记录创建（**retention 锚**，见 §2B.7） | CM:254 |

**列级汇总**：列数 **54**（15 + 12 + 9 + 18）· 类型分布 = uuid **20** · text **16** · timestamptz(3) **9** · jsonb **6** · integer **3**。
**时间列清单（9 列，全部 `_TS`）**：`agents.archived_at` / `created_at` / `updated_at` ·
`agent_versions.published_at` / `created_at` · `agent_permissions.created_at` ·
`tool_executions.started_at` / `finished_at` / `created_at`。
**禁列确认**：无 secret / DSN / credentials / access token / authorization policy blob 列
（`config` / `definition` / `allowed_tools` / `conditions` 仅为 opaque 数据载体，CORE:272 的 CI 扫描义务在 P09 延续）。

### 2B.2 对象命名表（全量 · `DESIGN RESOLVED`）

```
PK（4，隐式）        : agents_pkey · agent_versions_pkey · agent_permissions_pkey · tool_executions_pkey

FK（16）             : fk_agents_tenant · fk_agents_space · fk_agents_owner ·
                       fk_agents_current_version（**名已冻结** SD §4.1）· fk_agents_default_route ·
                       fk_agent_versions_agent · fk_agent_versions_published_by ·
                       fk_agent_permissions_agent · fk_agent_permissions_version ·
                       fk_agent_permissions_permission · fk_agent_permissions_tool ·
                       fk_tool_executions_tenant · fk_tool_executions_tool ·
                       fk_tool_executions_tool_version · fk_tool_executions_agent · fk_tool_executions_actor
                       命名先例：fk_<table>_<target>（0007:129-134 · 0008:111/145/165-171 · 0010:180/205-215）

CK（8）              : ck_agents_status · ck_agents_max_risk_level · ck_agent_versions_status ·
                       ck_agent_permissions_scope_target · ck_agent_permissions_effect ·
                       ck_tool_executions_status · ck_tool_executions_attempts ·
                       ck_tool_executions_duration                      （见 §2B.5）
                       命名先例：ck_<table>_<semantic>（ck_tools_timeout · ck_tools_risk_level ·
                       ck_tools_idempotency · ck_tools_audit_policy · ck_resource_permissions_effect ·
                       ck_credentials_secret …）

UQ / 索引（8）        : uq_agents_key（部分唯一 INDEX）· ix_agents_tenant_status ·
                       uq_agent_versions（UNIQUE **CONSTRAINT**）· ix_ap_agent ·
                       uq_agent_perm（表达式唯一 INDEX）· uq_tool_exec_idem（部分唯一 INDEX）·
                       ix_texec_tenant_created · ix_texec_status          （`D-P09-04` / `D-P09-15` / `D-P09-16`）

Trigger（3）          : tg_agents_set_updated_at（BEFORE UPDATE）· tg_version_immutable
                       （BEFORE UPDATE OR DELETE ON agent_versions）· tg_agents_tenant_space_consistency
                       （BEFORE INSERT OR UPDATE）                         （见 §2B.3 / §2B.4）

Function（新增 2 / 复用 2）: enforce_agents_tenant_space_consistency() ·
                       enforce_agent_versions_immutable() ·
                       复用 set_updated_at()（0003）· 复用 uap_uuid_v7()（0002）
                       属性先例：`LANGUAGE plpgsql`，**无 SECURITY DEFINER**、不设显式 owner
                       （0002:28-29 `VOLATILE PARALLEL SAFE` 仅 UUID 生成函数需要）

碰撞检查（本轮实测）  : 上述名称在 migrations 中**命中 0**；例外两项均属预期 ——
                       `tg_version_immutable`（3 处 = 0008 实作 + 文档引用，**共用名已冻结** D-B15-03）·
                       `fk_agents_current_version`（1 处 = 文档引用，**名已冻结**）
```

### 2B.3 `U-2` — `agents` tenant/space consistency（实现设计）

```
trigger   : `tg_agents_tenant_space_consistency`
function  : `enforce_agents_tenant_space_consistency()` RETURNS trigger · LANGUAGE plpgsql
timing    : **BEFORE INSERT OR UPDATE** FOR EACH ROW        （形态先例：0007:232-236 F2）
语义（唯一三分支）
  · `NEW.space_id IS NULL`                     → RETURN NEW（放行）
  · `NEW.space_id IS NOT NULL` 且 space 存在     → 要求 `NEW.tenant_id = spaces.tenant_id`
  · `NEW.space_id IS NOT NULL` 且 tenant 不匹配  → RAISE EXCEPTION（回滚）
space 不存在 : 与 F2 同构 —— SELECT 得 NULL 时 RAISE（'agents.space_id % does not exist'）。
               **职责边界**：引用完整性由 FK `fk_agents_space`（F2）承担；trigger 的存在性分支仅为
               「避免 NULL 比较歧义 + 报错路径统一」，**不替代 FK**，也不改变 FK 语义。
UPDATE 检查范围: 无条件校验 `NEW`（不引入「仅当 space_id/tenant_id 变化时校验」分支）——
               与 F2 同构；`NEW.tenant_id` 任意字段变更后都重新满足不变量。
只做结构完整性: 不写其他表 · 不做级联 · 不写审计 · **不做授权判定**
禁止          : ALLOW / DENY / 权限继承 / 角色 / 资源授权 / ACL decision（授权解释属 Authorization Layer，R-D-14）
错误信息风格   : 与 F2 同构，含表名、列值与原因（如 'cross-tenant agent denied'）
函数属性      : 无 SECURITY DEFINER；无额外 volatility 声明
其它函数      : 另需 `tg_agents_set_updated_at`（BEFORE UPDATE，复用 `set_updated_at()`，TRIGGER_INVENTORY:19 已列 agents）
触发器时序    : `agents` 上两个 BEFORE 触发器（`tg_agents_set_updated_at` / `tg_agents_tenant_space_consistency`）
                **无相互字段依赖**（前者只写 `NEW.updated_at`；后者只读 `NEW.tenant_id` / `NEW.space_id`）；
                PostgreSQL 在**同一 timing/event** 下按 **trigger name 顺序**执行 ⇒ 行为确定、无需干预；
                **不得引入人为排序机制**（无 `FOLLOWS` / `PRECEDES`；不合并函数；不为排序而改名）
```

### 2B.4 `NU-07` — published 版本不可变性（实现设计）

```
trigger   : `tg_version_immutable`（**共用名已冻结** D-B15-03；挂 agent_versions）
function  : `enforce_agent_versions_immutable()` RETURNS trigger · LANGUAGE plpgsql（**独立函数**）
timing    : **BEFORE UPDATE OR DELETE** FOR EACH ROW
语义
  · DELETE：`OLD.status = 'published'` → RAISE（回滚）；否则 RETURN OLD
  · UPDATE：`OLD.status = 'published'` → RAISE（回滚）；否则 RETURN NEW
不允许（`D-P09-14`）: published → deprecated · published → revoked  ← DB 层不可达
归属      : deprecate / revoke 属**后续应用层治理阶段**（P09 = SCHEMA ONLY）
为什么不复用 0008 的函数: `enforce_tool_versions_immutable()` 的 RAISE 消息硬编码表名 `tool_versions`，
               且 **`0008` 不得修改**（append-only）。故 P09 新建独立函数、消息硬编码 `agent_versions`；
               两函数语义**同构**（满足共用 trigger 名的语义一致性要求）。
函数属性  : 无 SECURITY DEFINER；`BEFORE` 行级触发返回 OLD/NEW 的写法沿用 0008:207-211 先例
双保险    : CORE:303「撤掉 UPDATE 权限」属**未来运维/权限配置**，P09 不实现（无对象交付）
```

### 2B.5 `U-3` — 8 个 CHECK 的语义与名称

| # | 表 | 名称 | 语义（冻结文本） | 依据 |
|---|---|---|---|---|
| CK-1 | `agents` | `ck_agents_status` | `status IN ('draft','active','disabled','archived')` | CORE:291 · CM:269 |
| CK-2 | `agents` | `ck_agents_max_risk_level` | `max_risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` | CORE:291 · CM:269 |
| CK-3 | `agent_versions` | `ck_agent_versions_status` | `status IN ('draft','published','deprecated','revoked')` | CORE:302 · CM:281 |
| CK-4 | `agent_permissions` | `ck_agent_permissions_scope_target` | `permission_id IS NOT NULL OR tool_id IS NOT NULL OR resource_scope IS NOT NULL` | `D-P09-05` CHECK-1 |
| CK-5 | `agent_permissions` | `ck_agent_permissions_effect` | `effect IN ('allow','deny')` | `D-P09-05` CHECK-2 |
| CK-6 | `tool_executions` | `ck_tool_executions_status` | `status IN ('running','succeeded','failed','denied','timeout')` | `D-P09-13` ① |
| CK-7 | `tool_executions` | `ck_tool_executions_attempts` | `attempts >= 1` | `D-P09-13` ② |
| CK-8 | `tool_executions` | `ck_tool_executions_duration` | `duration_ms >= 0` | `D-P09-13` ③ |

```
命名合规 : `ck_<table>_<semantic>`（0007/0008/0010 先例统一）；**不含 authorization 语义词**
          （`scope_target` 仅描述「三个目标列至少一列非空」这一结构事实，不表示权限判定）
唯一性   : 8 名称在 migrations 中命中 0（无碰撞）；与 PG 63 字节标识符上限距离充足
一致性   : migration / test / docs 三处必须逐字一致（测试义务 T-29）
```

### 2B.6 `NU-09` — CK-1 的结构边界

```
判定规则（全部依据 PostgreSQL 语义，不引入 trim / normalize）
  · `resource_scope IS NULL`      → **不计为 target**（NULL 比较结果为 NULL ⇒ 该 disjunct 不成立）
  · `resource_scope = ''`         → `IS NOT NULL` 为 TRUE ⇒ **计为 target**（CK-1 满足）
  · `resource_scope = '   '`      → 同上 ⇒ **计为 target**（不做 btrim / trim）
  · `permission_id` / `tool_id`   → uuid，判定同 `IS NOT NULL`
  · `conditions`                  → **不参与 CK-1**（不把 JSON 解释为权限 target；保持 storage-only）
最小结构语义: 「三列中至少一列非 NULL」= 声明该行**指向某个对象**；不表达任何 allow/deny 含义。
先例与边界（如实登记）
  · 全库**无** trim / btrim / 空串归一先例；
  · 但存在**空串拒绝**先例：`ck_credentials_secret` = `secret_hash <> ''`（0003:155）。
  · ⇒ 是否对 `resource_scope` 追加 `<> ''` 属**可选收紧**，会改变 `D-P09-05` 已冻结的 CHECK-1 文本，
    **不在本轮自行决定** → 列为 `HUMAN DECISION REQUIRED`（见 §2B.10）。
```

### 2B.7 `U-1` — 90 天 retention contract

```
Policy（策略，FROZEN 来源）      : `tool_executions` = **hard delete，90 天**（D-P09-01 · CORE:960/:965 · CM:256 · STEP1A:384）
Eligibility（资格，本轮收敛）    : **`created_at < now() - interval '90 days'`**
  选择依据（三源，非直觉）
    ① `created_at` 是平台统一保留锚 —— 0003 起所有表 `created_at` 均 NN + `server_default now()`；
    ② P09 内**唯一**支持时间范围扫描的索引 = `ix_texec_tenant_created (tenant_id, created_at DESC)`
       （INDEX_STRATEGY:130「执行历史列表」）；`started_at` **无**范围索引
       （`ix_texec_status` 是 `WHERE status='running'` 的部分索引，服务超时重扫而非保留清理）；
    ③ `started_at` 语义为「执行开始」（重试/排队场景可晚于记录创建），不适合作「记录年龄」判据。
Executor（执行机制，**不属 P09**）: **不实现** —— P09 = SCHEMA ONLY（D-P09-07）
    · **不引入**：scheduler · worker · cron（pg_cron 等）· background job · extension（pg_partman 等）
      · 分区 · runtime service · 任何新函数 / 新对象
    · 先例：B1-6 `D-3 = D`（FROZEN）—— 分区维护与保留清理 = **人工运维**，
      "Automation is deferred to a future operational/runtime phase."
    · ⇒ P09 交付物仅：**列 + 索引**（使清理语句可高效执行），执行本身为运维职责。
FK 影响分析（hard delete `tool_executions` 行）
    被删除方（子表行）自身不触发任何 FK 动作：无表引用 `tool_executions`（P09 内 0 个 incoming FK）
    · `tenant_id` / `tool_id` / `tool_version_id` = RESTRICT ⇒ **限制的是父侧删除**（删租户/工具前须先清执行记录），
      不影响执行记录的自身删除；
    · `agent_id` / `actor_id` = SET NULL ⇒ 父侧（agent/user）删除时**保留**执行行并置空归属，
      ⇒ 历史执行记录**不会**被级联清除（`D-P09-03` 语义后果，已在 `P09_DEPENDENCY.md §3` 登记）；
    · **不得**新增任何 CASCADE。
结论: `Retention Policy` / `Retention Eligibility` = **DESIGN RESOLVED**；
      `Retention Executor` = **DESIGN DEFERRED**（人工运维；若要求自动化执行器 ⇒ 新 Human Decision）。
```

### 2B.8 Canonical P09 Schema（设计收敛后）

```
Tables            = 4      （agents · agent_versions · agent_permissions · tool_executions）
Columns           = 54     （15 / 12 / 9 / 18）
FK                = 16     CASCADE = 5 · RESTRICT = 6 · SET NULL = 5
CK                = 8      （agents 2 · agent_versions 1 · agent_permissions 2 · tool_executions 3）
Unique Constraint = 1      （uq_agent_versions）
Unique Index      = 3      （uq_agents_key · uq_agent_perm · uq_tool_exec_idem）
Non-unique Index  = 4      （ix_agents_tenant_status · ix_ap_agent · ix_texec_tenant_created · ix_texec_status）
Total Index Obj   = 8      （+ PK 4，隐式）
Trigger           = 3      （tg_agents_set_updated_at · tg_version_immutable · tg_agents_tenant_space_consistency）
Function（新增）   = 2      （enforce_agents_tenant_space_consistency · enforce_agent_versions_immutable）
Deferred FK       = 1      （fk_agents_current_version · ON DELETE SET NULL）
Seed              = 0      （SD:193：P00–P10 无 seed）
P08 → P09 FK      = 0      （D-P09-10）
Partition         = 0      （D-P09-01 = B）
Runtime / API / Worker / Scheduler = 0        Authorization Evaluator = 0
```

### 2B.9 仍需 Human Decision（**不得自行冻结**）

| ID | 问题 | 证据 | 影响 | 状态 |
|---|---|---|---|---|
| **ND-A**（承接 `NU-09`） | 是否对 `resource_scope` 追加 `<> ''`（拒绝空串）？ | 冻结文本 = `D-P09-05` CHECK-1；空串拒绝先例 = `ck_credentials_secret`（0003:155）；全库无 trim 先例 | 若收紧 ⇒ 修改冻结 CHECK-1 文本 + CK 语义变更 + 测试断言 | **HUMAN DECISION REQUIRED** |
| **ND-B**（§11 请求文本） | `fk_agents_current_version` 是否带 **DEFERRABLE**？ | 冻结定义 `SD §4.1:132-134` = `… ON DELETE SET NULL;`（**无** DEFERRABLE）；`D-P09-11` 明令「不得修改其升级侧既有定义」；3 步顺序（最后 ADD）已消除对 deferral 的需求 | 若加 DEFERRABLE ⇒ 修改冻结约束定义（可能与 `D-P09-11` 冲突） | **HUMAN DECISION REQUIRED** |
| **NU-C**（登记） | 自动化 retention 执行器（scheduler / job）是否立项 | `D-3 = D`（手工运维）先例 | 引入 runtime 阶段与对象 | **DESIGN DEFERRED**（非本轮阻断） |
| **NU-D**（登记） | `agents.space_id` 指向**不存在 space** 时的报错来源（trigger 先 RAISE vs 仅靠 FK） | F2 先例（0007:60-63）在 trigger 内 RAISE | 报错文本差异，无结构影响 | DESIGN RESOLVED（沿用 F2 同构），登记备查 |

---

## 3. 各表既有定义（承接 B0，未在本次冻结中改动）

以下仅**引用**既有权威来源，**不是**本次新决策：
`agents`（`CORE:282-291` / `CM:262-272`）· `agent_versions`（`CORE:293-303` / `CM:274-284`）·
`agent_permissions`（`CORE:305-314` / `CM:286-294`）· `tool_executions`（`CORE:348-358` / `CM:246-256`）。

**本次对既有文档的最小修订**（B-2 授权，仅涉及已冻结决策）：
```
CORE:314   CK 行补 `effect IN ('allow','deny')`（反映 D-P09-05 = 2 条 CHECK）
CORE:358   保留行「分区」→ 不分区（D-P09-01）
CORE:960   保留策略「（分区，90 天）」→「（不分区，90 天）」（D-P09-01）
CORE:288/:299/:311/:354   9 条 FK 的 ON DELETE 补注（D-P09-03）
CM:251    补 tenant_id → tenants.id R（NN）；F15/F16 补 SN
CM:254/255  tenant_id 移出 NULL 列表、补入 NN 列表（D-P09-02）
CM:256     「分区 90 天 hard delete」→「不分区，90 天 hard delete」（D-P09-01）
CM:267    F1/F2/F3 补 R · CM:279 published_by 补 SN · CM:291 permission_id/tool_id 补 C
CM:270    NN 列表补 owner_id（CM 内部缺口修复 · D-P09-03 F3）
INDEX_STRATEGY:128  ix_texec_idem → uq_tool_exec_idem（标注 UNIQUE INDEX）
STEP1A:69/:384      「分区」→「不分区」（仅 tool_executions）
```

---

## 4. NOT FROZEN（本阶段不得推定）

| 项 | 状态 |
|---|---|
| 列级逐项清单（类型 / NULL / DEFAULT） | **DESIGN RESOLVED**（§2B.1 · 54 列全量） |
| **索引清单与 8 个索引对象命名** | **FROZEN**（`D-P09-15`） |
| **UQ 计数口径（CONSTRAINT 1 / INDEX 3）** | **FROZEN**（`D-P09-16`） |
| **`tool_executions` CHECK 数（3）** | **FROZEN**（`D-P09-13`） |
| 全部 **CHECK 的约束名** + 全部 FK / trigger / function 名 | **DESIGN RESOLVED**（§2B.2 / §2B.5） |
| `agents` consistency trigger 的名称与时机细节（`U-2`） | **DESIGN RESOLVED**（§2B.3） |
| `tg_version_immutable` 的 trigger 函数名（`NU-07`） | **DESIGN RESOLVED**（§2B.4） |
| 90 天保留的执行机制（`U-1`） | **DESIGN RESOLVED（policy + eligibility）** · executor = **DESIGN DEFERRED**（§2B.7） |
| P09 **时间列清单**与列类型（`NU-08`） | **DESIGN RESOLVED**（§2B.1 · 9 列） |
| `agent_permissions` CK-1 的空串 / NULL 边界（`NU-09`） | **DESIGN RESOLVED**（§2B.6）· 可选收紧 ⇒ `ND-A` **HUMAN DECISION REQUIRED** |
| `fk_agents_current_version` 是否 `DEFERRABLE`（`ND-B`） | **HUMAN DECISION REQUIRED**（§2B.9） |
| canonical **总计数**与编号空间 | **NOT FROZEN** → P09 TEST_MATRIX §2（§2B.8 已给出规格计数，编号空间待冻结） |
| seed | **FROZEN = 0**（`SD:193`：P00–P10 均无 seed） |

---

## 5. 不设计 / 不实现（FROZEN 边界）

```
✗ 分区结构（D-P09-01 = B）
✗ G/H/I/J trigger（D-P09-06 = A）
✗ agent/ 代码与任何 Runtime（D-P09-07 = A）
✗ API / Worker / Scheduler / Celery / 分区自动化（D-P09-07 = A）
✗ events / audit_logs（P10）· 任何 seed（P13）
✗ ai_request_logs 的任何 FK 变更（D-P09-10）
✗ 0011 migration 文件（D-P09-09 只冻结 identity）
```

---

## 6. Gate

```
P09 SCHEMA（决策层） = FROZEN（本文档 §2，含 ND 轮 D-P09-13～D-P09-16）
P09 SCHEMA DESIGN（交付物） = **COMPLETE**（本文档 §2B · DESIGN RESOLVED）
P09 DESIGN = **WRITE COMPLETE** · IMPLEMENTATION = NOT STARTED · 0011 = ABSENT
DB 对象变更 = 0 · DDL = 0 · DML = 0
NOT FROZEN（不得自行冻结）= canonical 总计数与编号空间
HUMAN DECISION REQUIRED（不阻断其他设计） = ND-A（resource_scope <> '' 可选收紧）· ND-B（DEFERRABLE）
DESIGN DEFERRED = retention 自动化执行器（人工运维先例 D-3 = D）
```
