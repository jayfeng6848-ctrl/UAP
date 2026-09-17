# B1-6 Schema Design

**Stage**: B1-6（= P08 AI Gateway）· **Status**: DESIGN —— **只设计，不创建任何数据库对象**
**输入**: `B1-6_DECISION_LOG.md`（D-B16-01 ～ D-B16-11 FROZEN）· B0 同步后权威口径（`ER_MODEL` · `CORE_DOMAIN_MODEL` · `STEP1B_SCHEMA_DEPENDENCY` · `STEP1B_CONSTRAINT_MATRIX` · `STEP1B_INDEX_STRATEGY` · `STEP1B_TRIGGER_INVENTORY` · `STEP1B_SEED_STRATEGY`）
**边界**: 本阶段 `0010 = ABSENT`；不执行 DDL/DML。

> **列定义来源**：字段集合取自 `CORE_DOMAIN_MODEL:364-414`（§1.5）与 `STEP1B_CONSTRAINT_MATRIX:298-352`（§6）。
> **不得凭空补充 schema** —— 本文件不新增任何冻结文档未列出的列。

---

## 1. 域总览

```
ai_providers        平台级 ROOT（无 tenant_id）          15 列
ai_models           模型目录（provider 技术子实体）        15 列
ai_routes           capability → model 路由 / fallback     10 列
ai_policies         分级 / 准入 / fallback / 预算 / 延迟    16 列
ai_request_logs     成本 / 可观测（分区表）                 17 列
                                                       ─────
                                                       73 列
```

**命名与类型风格**：沿用 B1-1 ～ B1-5 既有风格
`id` = `postgresql.UUID(as_uuid=True)` + `server_default uap_uuid_v7()`；
时间列 = `sa.DateTime(timezone=True)`（平台铁律 `timestamptz(3)`，由 0009 + 平台 guard 强制）；
`text` = `sa.Text()` · `int` = `sa.Integer()` · `bool` = `sa.Boolean()` · `jsonb` = `postgresql.JSONB()` · `numeric` = `sa.Numeric()`

---

## 2. `ai_providers`

| 项 | 内容 |
|---|---|
| **purpose** | 厂商/网关连接的**数据化**描述。厂商名是数据行，不是 Core 逻辑分支（架构铁律 3） |
| **tenant 维度** | **无 `tenant_id`** —— **D-B16-11 = FROZEN — A**（平台级 ROOT） |

### 2.1 列定义（15）

| 列 | 类型 | NULL | 默认 | 说明 |
|---|---|---|---|---|
| `id` | uuid | **NN** | `uap_uuid_v7()` | PK |
| `key` | text | **NN** | — | 逻辑键（数据非代码） |
| `display_name` | text | NULL | — | |
| `adapter` | text | **NN** | — | **适配器注册键 —— opaque 文本引用**（D-B16-06 = FROZEN — A） |
| `base_url` | text | NULL | — | |
| `enabled` | bool | **NN** | — | |
| `health_status` | text | **NN** | — | |
| `health_checked_at` | timestamptz(3) | NULL | — | |
| `privacy_tier` | text | **NN** | — | |
| `max_classification` | text | **NN** | — | |
| `capabilities` | jsonb | NULL | — | |
| `config` | jsonb | NULL | — | **不含密钥** |
| `secret_ref` | text | NULL | — | 指向密钥管理，**只存引用，绝不存明文** |
| `created_at` | timestamptz(3) | **NN** | `now()` | |
| `updated_at` | timestamptz(3) | **NN** | `now()` | trigger 维护 |

### 2.2 约束

| 类别 | 内容 |
|---|---|
| PK | `id` |
| **FK** | **无**（ROOT） |
| UQ | `uq_ai_providers_key ON (key)` —— **UNIQUE CONSTRAINT**（纯列，无表达式） |
| CK ×3 | `ck_ai_providers_privacy_tier`：`privacy_tier IN ('public','vetted','private','self_hosted')`<br>`ck_ai_providers_max_classification`：`max_classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')`<br>`ck_ai_providers_health_status`：`health_status IN ('unknown','healthy','degraded','down')` |
| NN | id, key, adapter, privacy_tier, max_classification, enabled, health_status, created_at, updated_at |
| NULL | display_name, base_url, capabilities, config, secret_ref, health_checked_at |
| **不建立** | `key` 无 regex/format CK（沿用 opaque 键处理惯例）· **无 tenant_id 列** |

### 2.3 索引 / trigger / seed

```
索引    : uq_ai_providers_key（由 UNIQUE CONSTRAINT 隐式建立）
trigger : tg_ai_providers_set_updated_at  —— BEFORE UPDATE，purpose = NEW.updated_at = now()
          （复用既有 set_updated_at()，不重建函数）
seed    : 0
```

---

## 3. `ai_models`

| 项 | 内容 |
|---|---|
| **purpose** | 模型能力、成本、合规上限的目录 |

### 3.1 列定义（15）

| 列 | 类型 | NULL | 默认 | 说明 |
|---|---|---|---|---|
| `id` | uuid | **NN** | `uap_uuid_v7()` | PK |
| `provider_id` | uuid | **NN** | — | → `ai_providers.id` |
| `model_key` | text | **NN** | — | |
| `display_name` | text | NULL | — | |
| `capabilities` | jsonb | NULL | — | |
| `context_window` | int | **NN** | — | |
| `max_output_tokens` | int | NULL | — | |
| `input_price_per_1k` | numeric | NULL | — | |
| `output_price_per_1k` | numeric | NULL | — | |
| `max_classification` | text | **NN** | — | |
| `is_private` | bool | **NN** | — | |
| `latency_p95_ms` | int | NULL | — | |
| `enabled` | bool | **NN** | — | |
| `created_at` | timestamptz(3) | **NN** | `now()` | |
| `updated_at` | timestamptz(3) | **NN** | `now()` | trigger 维护 |

### 3.2 约束

| 类别 | 内容 |
|---|---|
| PK | `id` |
| FK ×1 | `fk_ai_models_provider`：`provider_id → ai_providers.id` **ON DELETE CASCADE**（NN） |
| UQ | `uq_ai_models ON (provider_id, model_key)` —— **UNIQUE CONSTRAINT** |
| CK ×2 | `ck_ai_models_max_classification`：`max_classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')`<br>`ck_ai_models_context_window`：`context_window > 0` |
| NN | id, provider_id, model_key, context_window, max_classification, is_private, enabled, created_at, updated_at |
| NULL | display_name, capabilities, max_output_tokens, input_price_per_1k, output_price_per_1k, latency_p95_ms |

**CASCADE 依据**：`CORE_DOMAIN_MODEL §11.1` 白名单「技术子实体 `ai_providers → ai_models`」（模型目录随 provider purge 清理）。

### 3.3 索引 / trigger / seed

```
索引    : uq_ai_models（隐式）
          ix_aimodels_capability —— **不建立**（**D-2 = B FROZEN**）；其 B0 定义引用了 ai_models 上
          不存在的列（该表只有 `capabilities jsonb`）⇒ 登记为 **T-1 = DEFERRED**（见 §9.2 / §9.3）
trigger : tg_ai_models_set_updated_at —— BEFORE UPDATE（复用 set_updated_at()）
seed    : 0
```

---

## 4. `ai_routes`

| 项 | 内容 |
|---|---|
| **purpose** | capability → model 的路由与 fallback 链 |

### 4.1 列定义（10）

| 列 | 类型 | NULL | 默认 | 说明 |
|---|---|---|---|---|
| `id` | uuid | **NN** | `uap_uuid_v7()` | PK |
| `tenant_id` | uuid | NULL | — | **NULL = 平台默认** |
| `space_id` | uuid | NULL | — | |
| `capability` | text | **NN** | — | |
| `priority` | int | **NN** | — | |
| `primary_model_id` | uuid | **NN** | — | → `ai_models.id` |
| `fallback_chain` | jsonb | NULL | — | `[{model_id, when: {...}}]` |
| `enabled` | bool | **NN** | — | |
| `created_at` | timestamptz(3) | **NN** | `now()` | |
| `updated_at` | timestamptz(3) | **NN** | `now()` | trigger 维护 |

### 4.2 约束

| 类别 | 内容 |
|---|---|
| PK | `id` |
| FK ×3 | `fk_ai_routes_primary_model`：`primary_model_id → ai_models.id` **RESTRICT**（NN）<br>`fk_ai_routes_tenant`：`tenant_id → tenants.id` **RESTRICT** ← **D-B16-02 = FROZEN — A**<br>`fk_ai_routes_space`：`space_id → spaces.id` **RESTRICT** ← **D-B16-02 = FROZEN — A** |
| UQ | `uq_ai_routes ON (COALESCE(tenant_id,'0…'), COALESCE(space_id,'0…'), capability, priority)`<br>—— **含 `COALESCE(...)` 表达式 ⇒ 只能实现为 UNIQUE INDEX，不能是 UNIQUE CONSTRAINT**（D-B16-07 口径） |
| CK ×2 | `ck_ai_routes_capability`：`capability IN ('chat','embeddings','rerank','vision','audio_asr','audio_tts','moderation')`<br>`ck_ai_routes_priority`：`priority >= 0` |
| NN | id, capability, priority, primary_model_id, enabled, created_at, updated_at |
| NULL | tenant_id（NULL = 平台默认）、space_id、fallback_chain |
| **不建立** | 无 tenant/space 一致性 trigger（`TRIGGER_INVENTORY` 仅 `tg_resources_tenant_space_consistency` 一条，挂 resources）· **不得扩大** tenant/space FK 范围 |

### 4.3 索引 / trigger / seed

```
索引    : uq_ai_routes（唯一索引，表达式）
trigger : tg_ai_routes_set_updated_at —— BEFORE UPDATE（复用 set_updated_at()）
seed    : 0
```

---

## 5. `ai_policies`

| 项 | 内容 |
|---|---|
| **purpose** | 数据分级 → 供应商准入 / fallback / 预算 / 延迟约束 |

### 5.1 列定义（16）

| 列 | 类型 | NULL | 默认 | 说明 |
|---|---|---|---|---|
| `id` | uuid | **NN** | `uap_uuid_v7()` | PK |
| `tenant_id` | uuid | NULL | — | |
| `space_id` | uuid | NULL | — | |
| `name` | text | **NN** | — | |
| `max_classification` | text | **NN** | — | |
| `allowed_privacy_tiers` | jsonb | NULL | — | |
| `denied_providers` | jsonb | NULL | — | |
| `require_private` | bool | **NN** | — | |
| `allow_fallback` | bool | **NN** | — | |
| `fallback_preserves_classification` | bool | **NN** | `true` | |
| `budget_daily_usd` | numeric | NULL | — | |
| `latency_budget_ms` | int | NULL | — | |
| `redaction_profile` | text | NULL | — | |
| `enabled` | bool | **NN** | — | |
| `created_at` | timestamptz(3) | **NN** | `now()` | |
| `updated_at` | timestamptz(3) | **NN** | `now()` | trigger 维护 |

### 5.2 约束

| 类别 | 内容 |
|---|---|
| PK | `id` |
| FK ×2 | `fk_ai_policies_tenant`：`tenant_id → tenants.id` **RESTRICT** ← **D-B16-02 = FROZEN — A**<br>`fk_ai_policies_space`：`space_id → spaces.id` **RESTRICT** ← **D-B16-02 = FROZEN — A** |
| UQ | `uq_ai_policies ON (COALESCE(tenant_id,'0…'), COALESCE(space_id,'0…'), lower(name))`<br>—— **含表达式 ⇒ UNIQUE INDEX**（D-B16-07 口径） |
| CK ×1（必做） | `ck_ai_policies_no_unguarded_fallback`：**`allow_fallback = false OR fallback_preserves_classification = true`**<br>（= 数据架构铁律 5「`HIGHLY_CONFIDENTIAL` 禁止因厂商故障降级到公共模型」的 **DB 层落地**） |
| CK ×2（B0「建议」；**不实现**） | `budget_daily_usd >= 0` · `latency_budget_ms >= 0` —— **D-1 = B FROZEN ⇒ 本阶段不新增该两条 CHECK**（见 §9.2） |
| NN | id, name, max_classification, require_private, allow_fallback, fallback_preserves_classification, enabled, created_at, updated_at |
| NULL | tenant_id, space_id, allowed_privacy_tiers, denied_providers, budget_daily_usd, latency_budget_ms, redaction_profile |

### 5.3 索引 / trigger / seed

```
索引    : uq_ai_policies（唯一索引，表达式）
trigger : tg_ai_policies_set_updated_at —— BEFORE UPDATE（复用 set_updated_at()）
seed    : 0
```

---

## 6. `ai_request_logs`（分区表）

| 项 | 内容 |
|---|---|
| **purpose** | 成本 / 配额 / 可观测（**不是审计**，**不存 prompt 原文**） |

### 6.1 列定义（17）

| 列 | 类型 | NULL | 默认 | 说明 |
|---|---|---|---|---|
| `id` | uuid | **NN** | `uap_uuid_v7()` | **PK 组成部分** |
| `occurred_at` | timestamptz(3) | **NN** | `now()` | **分区键 + PK 组成部分** |
| `tenant_id` | uuid | NULL | — | **无 FK**（D-B16-03） |
| `space_id` | uuid | NULL | — | **无 FK**（D-B16-03） |
| `actor_id` | uuid | NULL | — | **无 FK**（D-B16-03） |
| `agent_id` | uuid | NULL | — | **无 FK**（D-B16-03，**不得新增**） |
| `provider_id` | uuid | NULL | — | → `ai_providers.id` |
| `model_id` | uuid | NULL | — | → `ai_models.id` |
| `capability` | text | **NN** | — | |
| `classification` | text | **NN** | — | |
| `prompt_tokens` | int | NULL | — | 命名以 `CORE` 细分为准（**D-4 = A FROZEN**） |
| `completion_tokens` | int | NULL | — | 同上（**D-4 = A FROZEN**） |
| `cost_usd` | numeric | NULL | — | |
| `latency_ms` | int | NULL | — | |
| `status` | text | **NN** | — | **CHECK = 0**（D-B16-04） |
| `error_code` | text | NULL | — | |
| `correlation_id` | text | NULL | — | |

### 6.2 约束

| 类别 | 内容 |
|---|---|
| PK | **`(id, occurred_at)`** —— 复合；**分区键必须进 PK**（`CORE:412` · `UUID_STRATEGY:111`） |
| FK ×2 | `fk_ai_request_logs_provider`：`provider_id → ai_providers.id` **RESTRICT**<br>`fk_ai_request_logs_model`：`model_id → ai_models.id` **RESTRICT**<br>（均 NULL 允许 ⇒ 可写 NULL 而不触发引用检查） |
| **FK 明确不建立** | `agent_id` · `actor_id` · `tenant_id` · `space_id` —— **D-B16-03 = FROZEN — A** |
| UQ | **0** |
| **CK** | **0** —— `status` **不建立取值域 CHECK**（**D-B16-04 = FROZEN — A**）<br>**Canonical Test Matrix 中 S5 对该列的 CHECK 检查 = EXEMPT / NOT APPLICABLE** |
| NN | id, capability, classification, status, occurred_at |
| NULL | tenant_id, space_id, actor_id, agent_id, provider_id, model_id, prompt_tokens, completion_tokens, cost_usd, latency_ms, error_code, correlation_id |

### 6.3 分区（D-B16-05 = FROZEN — A）

```
分区方式     : PARTITION BY RANGE (occurred_at)
分区键边界   : 一律 UTC 月边界（CORE:921）
P08 建       : 父表 + 当月子分区（SCHEMA_DEPENDENCY:267）
子分区 PK    : 继承父表 PK (id, occurred_at)
子分区命名   : ai_request_logs_<YYYYMM>（UTC calendar month）← **DC-1 = A FROZEN**
保留策略     : 90 天后按分区删除（CORE:358/963）
downgrade    : 先 DROP 子分区，再 DROP 父表（SCHEMA_DEPENDENCY:270）
维护机制     : **手工运维（D-3 = D FROZEN）** —— 0010 不预建未来月份、不建自动清理、不引入
               job / scheduler / pg_partman / CREATE EXTENSION，亦不改 Docker / compose / worker runtime
```

**PK 与分区键兼容性**：`(id, occurred_at)` 含分区键 `occurred_at` ⇒ 满足 PG 对分区表 PK 的强制要求。
**FK 与分区兼容性**：PG 16.15 支持**从分区表到普通表**的 FK；FK 声明在父表并自动下推至子分区。

### 6.4 索引 / trigger / seed

```
索引    : ix_airl_tenant_occurred ON (tenant_id, occurred_at DESC)   ← INDEX_STRATEGY:151
          建在父表（PG 自动下推到子分区）
trigger : 0 —— 本表**无 updated_at** ⇒ 无 set_updated_at trigger
          （TRIGGER_INVENTORY 条目 A 的表清单不含 ai_request_logs）
seed    : 0
```

---

## 7. 对象计数（预计）

| 类别 | 数量 | 明细 |
|---|---|---|
| 表 | **5** | `ai_providers` · `ai_models` · `ai_routes` · `ai_policies` · `ai_request_logs` |
| 列 | **73** | 15 + 15 + 10 + 16 + 17 |
| PK | **5** | 4 个单列 `id` + 1 个复合 `(id, occurred_at)` |
| **FK** | **8** | CASCADE **1**（F1）· RESTRICT **7**（F2–F8）—— 逐条见 `B1-6_DEPENDENCY.md` §3 |
| **UQ（constraint 形式）** | **2** | `uq_ai_providers_key` · `uq_ai_models` —— **D-B16-07 = FROZEN — A** |
| **UQ（index 形式）** | **2** | `uq_ai_routes`（表达式）· `uq_ai_policies`（表达式）—— 表达式唯一**不计入** constraint |
| CK（必做） | **8** | ai_providers 3 · ai_models 2 · ai_routes 2 · ai_policies 1 · ai_request_logs **0** |
| CK（B0「建议」；**不实现**） | **0** | `budget_daily_usd >= 0` · `latency_budget_ms >= 0` —— **D-1 = B FROZEN ⇒ 不新增**（见 §9.2） |
| **status CK** | **0** | D-B16-04 = FROZEN — A |
| Trigger | **4** | `tg_ai_providers_set_updated_at` · `tg_ai_models_set_updated_at` · `tg_ai_routes_set_updated_at` · `tg_ai_policies_set_updated_at` |
| Function（新增） | **0** | 复用 `set_updated_at()` |
| 分区 | **父表 1 + 当月子分区 1** | D-B16-05 = FROZEN — A |
| 非 PK 索引 | **5** | `uq_ai_providers_key`（隐式）· `uq_ai_models`（隐式）· `uq_ai_routes` · `uq_ai_policies` · `ix_airl_tenant_occurred`<br>（`ix_aimodels_capability` **不建立** —— **D-2 = B FROZEN**，见 §9.3） |
| Seed | **0** | P00–P10 均无 seed；P13 才有 seed |

> **索引计数口径**：`uq_ai_providers_key` / `uq_ai_models` 以 `UniqueConstraint` 实现时，PG 自动建同名索引 ⇒
> "非 PK 索引" 含其隐式索引（与 B1-5 的 `uq_tool_versions` 同类）。**精确口径待实施时按 `pg_indexes` 实测确认**
> （B1-4 曾出现 `CK ×5/×6` 摘要漂移；D-B15-06 已建立"显式标注口径"的做法）。

---

## 8. 明确不设计的对象（防范围蔓延）

| 对象 | 归属 | 依据 |
|---|---|---|
| `agents` / `agent_versions` / `agent_permissions` / `tool_executions` | P09 | `SCHEMA_DEPENDENCY:170` |
| `events` / `audit_logs` | P10 | `SCHEMA_DEPENDENCY:171` |
| `resource_relations` | P2 可选 | `CORE` §11.1 |
| `fk_agents_current_version`（deferred FK） | **P09** | `:170`；**`:136` 的「Phase 08」为陈旧引用**（D-B16-08 = C，见 `B1-6_DEPENDENCY.md` §5.1） |
| `agents.default_route_id → ai_routes` | P09（P09 侧建立） | `:143` |
| G / H / I / J ACL trigger | P09 后 | `TRIGGER_INVENTORY` |
| `ai_request_logs.agent_id` FK | **不建**（且不得新增） | D-B16-03 = FROZEN — A |
| adapter registry / 解析 / 加载 | 不在本阶段 | D-B16-06 = FROZEN — A |
| 分区维护 job / pg_partman | **本阶段不做**（**D-3 = D FROZEN** ⇒ 手工运维） | `STEP1A_DESIGN_REPORT:511 R2` · §9.4 |
| 任何 API / Socket / service 实现 | 0 | `B1-6_API_DESIGN.md` |
| RLS / policy / authorization evaluator | 0 | 架构边界 |
| 任何 seed 行 | 0 | §11 |

---

## 9. 设计约定与未裁定项

### 9.1 设计约定（B0 未规定；**DC-1 已由 Human 裁定**，见 §9.5）

| ID | 内容 | 说明 |
|---|---|---|
| **DC-1** | 分区子表命名 = **`ai_request_logs_<YYYYMM>`**（UTC calendar month） | **✅ DC-1 = A FROZEN（2026-09-16）** —— 命名成为既定契约；downgrade 必须按该命名删除对应 child partition；后续手工创建月份分区沿用同规则 |
| **DC-2** | P08 只建 **1 个**子分区（当月） | 直接来自 `SCHEMA_DEPENDENCY:267`「+ 当月子分区」 |
| **DC-3** | `numeric` 列不限定精度（`sa.Numeric()`） | B0 未规定 `numeric(p,s)`；本阶段不引入精度约束 |
| **DC-4** | 子分区继承父表 PK，不额外建本地索引 | 来自 `INDEX_STRATEGY:160`「分区表索引建在父表自动下推」 |

### 9.2 设计层裁定（Design Decision Freeze，2026-09-16）—— 权威记录见 `B1-6_DECISION_LOG.md` §9

| ID | 内容 | 裁定 | 状态 |
|---|---|---|---|
| **D-1** | `ai_policies` 的 `budget_daily_usd >= 0` / `latency_budget_ms >= 0`（B0 标注「（建议）」） | **不实现** | ✅ **FROZEN — B** |
| **D-2** | `ix_aimodels_capability`（`INDEX_STRATEGY:139` 标注 P3 可免） | **不建立 / 延后** | ✅ **FROZEN — B** |
| **D-3** | 分区维护机制（预建/清理 job · pg_partman） | **手工运维** | ✅ **FROZEN — D** |
| **D-4** | `ai_request_logs` 字段命名 | `prompt_tokens` + `completion_tokens`（= 本设计现状） | ✅ **FROZEN — A** |
| **DC-1** | 分区子表命名 | `ai_request_logs_<YYYYMM>` | ✅ **FROZEN — A** |

**裁定后本设计的结构事实（未变）**：列 **73** · 必做 CK **8** · status CK **0** · 非 PK 索引 **5** · trigger **4** · seed **0**。

#### 9.3 T-1（DEFERRED / FUTURE DESIGN CLARIFICATION）

```
STEP1B_INDEX_STRATEGY.md 定义 : ix_aimodels_capability ON (capability) WHERE enabled
事实                          : ai_models 不存在 capability 列，仅存在 capabilities jsonb
处置（D-2 = B 同时登记）      : 不创建该索引 · 不修改 B0 · 不擅自决定目标列 · 不宣布该索引作废

### 9.3 与既有 schema 的风格一致性

```
✅ id = UUID + uap_uuid_v7() 兜底（同 0003–0008）
✅ 时间列 = timestamptz(3)（0009 校正后口径 + 平台 guard PG1–PG7 覆盖）
✅ 状态字段 = text + CHECK，不用 PG enum（CONSTRAINT_MATRIX:7）
✅ updated_at 由 trigger 维护，应用层不依赖（CORE:920）
✅ 命名：fk_<table>_<target> · uq_<table> · ck_<table>_<field> · tg_<table>_set_updated_at
✅ 业务实体 RESTRICT / 技术子实体 CASCADE（CORE §11.1）
✅ 未新增任何函数（复用 set_updated_at()）
```

---

## 10. Gate

```
B1-6 SCHEMA_DESIGN = DESIGN（未创建任何数据库对象）
DESIGN DECISION FREEZE = PASS
  D-1 = B · D-2 = B · D-3 = D · D-4 = A · DC-1 = A · T-1 = DEFERRED
0010 = ABSENT
DDL = 0 · DML = 0
列 = 73 · FK = 8（1 CASCADE + 7 RESTRICT）· UQ = 2 constraint + 2 index
必做 CK = 8 · status CK = 0 · 非 PK 索引 = 5 · trigger = 4 · function 新增 = 0 · seed = 0
```
