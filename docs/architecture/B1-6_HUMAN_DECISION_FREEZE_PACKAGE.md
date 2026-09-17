# B1-6 Human Decision Freeze Package

**Stage**: B1-6（= P08 AI Gateway）· **Status**: **HUMAN DECISION FREEZE — FROZEN（2026-09-16）**
**本文件性质**：**已完成 Freeze 的权威决策输入载体**。DESIGN 阶段的一切结论均以此为唯一决策来源。
**约束**: **不得重新打开已 FROZEN 的 D-B16-01 ～ D-B16-11；不得重新回收已确定参数；不得以新设计解释覆盖已冻结的 Human Decision。**

---

## 1. Baseline

```
HEAD           = 964ea2c47f1b561a1dca5abed45ca4bc89d9f5e7
branch         = main
migration      = 0001 → 0002 → 0003 → 0004 → 0005 → 0006 → 0007 → 0008 → 0009
head migration = 0009_timestamp_precision（唯一 head）
0010           = ABSENT
formal uap     = 0 tables
Architecture Guard = 9 passed · Core → Domain = 0
```

---

## 2. B1-6 ↔ P08 Evidence

```
Literal        : `B1-6` / `B1.6` / `B16` / `b1_6` 全库命中 = 0（无预定义名称）
Phase evidence : STEP1B_SCHEMA_DEPENDENCY.md:169   P08 = AI Gateway（5 表链）
                 STEP1B_B0_GATE_REPORT.md:45       P07 tool → P08 AI → P09 agent
                 B1-4_SCOPE.md:42                  Tool / AI / Agent 域 | P07 / P08 / P09
                 0009_timestamp_precision.py:35    「P08 后续 migration 编号顺延至 0010」
Repository     : P01–P07 全部已建（migration 0001–0009 · 20 张业务表无缺）
Ambiguity      : `B1-x → P-x` 映射非 1:1（B1-1=P01+P02 · B1-2=P03+P05 · B1-3=P04）
```

**D-B16-01 = FROZEN — A** 已由 Human 确认 `B1-6 = P08 AI Gateway`；
**约束**：不得据此改变历史 B0 文档中已有的 phase 定义。

---

## 3. Human Decisions（汇总）

```
D-B16-01 = FROZEN — A      B1-6 = P08 AI Gateway
D-B16-02 = FROZEN — A      ai_routes / ai_policies 的 tenant_id / space_id → FK + RESTRICT
D-B16-03 = FROZEN — A      ai_request_logs.provider_id / model_id → FK + RESTRICT（不含 agent_id）
D-B16-04 = FROZEN — A      ai_request_logs.status 零新增校验；S5 明确豁免
D-B16-05 = FROZEN — A      ai_request_logs：P08 建父表 + 当月子分区
D-B16-06 = FROZEN — A      adapter 仅文本引用；不引入解析/加载/注册/运行时机制
D-B16-07 = FROZEN — A      UNIQUE CONSTRAINT = 2 · UNIQUE INDEX = 2
D-B16-08 = FROZEN — C      不回改 B0 :136；说明义务由 B1-6 文档承载
D-B16-09 = FROZEN — A      沿用 B1-5 的 9 份文档模式
D-B16-10 = FROZEN — A      独立编号空间 Canonical Test Matrix（须登记 S5 EXEMPT）
D-B16-11 = FROZEN — A      ai_providers 平台级 ROOT / 无 tenant_id / 零 seed

OPEN = 0        BLOCKING = 0
```

---

## 4. Decision Evidence（冻结依据）

### 4.1 D-B16-02（四来源冲突 → 裁定 A）

| 来源 | 原文（冻结前） | 取向 |
|---|---|---|
| `SCHEMA_DEPENDENCY:74/75` | 「tenant/space NULL **无 FK**」· FK 列「—（无强 FK）」 | 不支持 FK |
| `CONSTRAINT_MATRIX:327 / :333-341` | ai_routes FK 行仅 `primary_model_id`；ai_policies 段**无 FK 行** | 未列 |
| `CORE_DOMAIN_MODEL:391 / :402` | FK 行**无 → 目标、无删除规则** | 表述不完整 |
| `ER_MODEL:352-353 / :361-362` | `uuid tenant_id FK` / `uuid space_id FK` | **支持 FK（唯一）** |

**Human Decision = A**：四列均加 FK + `ON DELETE RESTRICT`，**四列均保持 nullable**。
**B0 同步（AUTH-02 授权，已执行）**：`SCHEMA_DEPENDENCY:74/75` · `CONSTRAINT_MATRIX:327 / :338（新增 FK 行）` · `CORE:391 / :402`。

### 4.2 D-B16-03（三来源冲突 → 裁定 A）

| 来源 | 原文（冻结前） | 取向 |
|---|---|---|
| `SCHEMA_DEPENDENCY:76` | 「分区表；FK 尽量保持 NULL 宽松或**仅 provider/model**」 | 条件式 |
| `CONSTRAINT_MATRIX:343-352` | **FK 行 = 0** | 未列 |
| `CORE_DOMAIN_MODEL:407-412` | **FK 行 = 0** | 未列 |
| `ER_MODEL:375-376` | `uuid provider_id FK` / `uuid model_id FK` | **支持 FK** |
| `CORE §11.1:985` | 「`ai_models → ai_request_logs`（**若建 FK**）」 | 条件式 |

**Human Decision = A**：`provider_id` + `model_id` 加 FK + 两列均 `ON DELETE RESTRICT`；
**`agent_id` / `actor_id` / `tenant_id` / `space_id` 明确无 FK**（⇒ 不构成 P08 → P09 前向依赖）。
**B0 同步（AUTH-02）**：`SCHEMA_DEPENDENCY:76` · `CONSTRAINT_MATRIX:348（新增 FK 行）` · `CORE:985`。

### 4.3 D-B16-04（Human wording —— 逐字权威）

> `ai_request_logs.status` 在 B1-6 中不新增取值域 CHECK。不凭空定义或冻结新的 status vocabulary。
> 沿用 D-B15-04 的边界口径：本阶段仅保留 status 字段，不建立新的 status CHECK 约束。
> Canonical Test Matrix 中，S5 对 `ai_request_logs.status` 的 CHECK 检查不适用/予以明确豁免。

**对照先例**：`tool_versions.status` = 0 CK（D-B15-04 = A）· `agent_versions.status` = 4 值 CK · `tool_executions.status` = 5 值 CK。
**本决策不引入任何 status 词表。**

### 4.4 D-B16-05

`SCHEMA_DEPENDENCY:267`（父表 + **当月子分区**）· `:270`（downgrade 先 DROP 子分区）·
`:169`（P08 行未提分区）vs `:171`（P10 行显式「分区父表 + 初始子分区」）·
`CORE:412/414/921` · `STEP1B_SCHEMA_TEST_MATRIX:112 M8` · `STEP1A_DESIGN_REPORT:511 R2`（按月分区需预建）。
**Human Decision = A**：P08 建父表 + 当月子分区。

### 4.5 D-B16-06

`CORE:370/709`（适配器注册键，指向 `intelligence/providers` 已注册适配器）· `ER_MODEL:332` · `CONSTRAINT_MATRIX:307`（NN，无 CK/UQ/FK）。
代码侧：`intelligence/providers/interfaces.py` 的 `ProviderRegistry` **类已存在实现体**，**全库 0 处调用**。
**Precedent**：**D-B15-09 = FROZEN — A**（`handler_ref` 仅文本引用）。
**Human Decision = A**：`adapter` 仅文本引用；P08 不引入解析/加载/注册/运行时机制。

### 4.6 D-B16-07

`ai_routes` / `ai_policies` 的 UQ 均含 `COALESCE(...)` 表达式 ⇒ 不可为 UNIQUE CONSTRAINT。
**Precedent**：**D-B15-06 = FROZEN — A**（`UNIQUE CONSTRAINT = 1` · `UNIQUE INDEX = 3`；表达式唯一不计入 constraint）。
**Human Decision = A**：沿用同口径 ⇒ `UNIQUE CONSTRAINT = 2` · `UNIQUE INDEX = 2`。

### 4.7 D-B16-08（裁定 C）

```
Exact stale statement : STEP1B_SCHEMA_DEPENDENCY.md:136
                        「…该约束加入 **Phase 08** 尾部。」
                        （语境：§4.1 agents ↔ agent_versions 真循环的 deferred FK 解法）
正确归属              : P09 —— :170（P09 行「补 agents.current_version_id FK」）
                        · B0_GATE_REPORT:45 · B1-4_DEPENDENCY:132 · B1-5_SCOPE:42
全库唯一性            : `Phase [0-9]{1,2}` 匹配 = 仅此 1 处
物理事实              : P08 时 `agents` 不存在 ⇒ 照 :136 字面执行 ALTER TABLE agents 不可执行
Human Decision = C    : **不回改 B0**
```

**B1-6 侧加注义务（本文件即履行）**：
> **`STEP1B_SCHEMA_DEPENDENCY.md:136` 的「Phase 08」属于陈旧引用；
> `agents.current_version_id` deferred FK 的正式归属为 P09。**

### 4.8 D-B16-09 / D-B16-10 / D-B16-11

```
D-B16-09 : B1-4 文档集 12 份（全 tracked）vs B1-5 文档集 9 份（全 untracked）—— 两模式并存
           ⇒ Human 选 A：沿用 B1-5 的 9 份模式
D-B16-10 : P08 canonical matrix 原不存在（STEP1B_SCHEMA_TEST_MATRIX 10 类中无 P08 章节）
           先例：B1-4 = 84（O-1 = FROZEN — A）· B1-5 = 39（D-B15-07 = FROZEN — A）
           ⇒ Human 选 A：独立编号空间
D-B16-11 : SCHEMA_DEPENDENCY:72/95/103 · B0_GATE_REPORT:42 五来源一致为 ROOT 且无 tenant_id
           SEED_STRATEGY 0 命中 · intelligence/ 无 tenant 提及
           ⇒ Human 选 A：平台级 ROOT / 无 tenant_id / 零 seed
```

---

## 5. Frozen Facts

```
tables           = 5
columns          = 73（15 + 15 + 10 + 16 + 17）
PK               = 5（4 单列 + 1 复合 (id, occurred_at)）
FK               = 8（CASCADE 1 · RESTRICT 7）—— 逐条见 B1-6_DEPENDENCY.md §3
UNIQUE CONSTRAINT= 2（uq_ai_providers_key · uq_ai_models）
UNIQUE INDEX     = 2（uq_ai_routes · uq_ai_policies，均为 COALESCE 表达式）
CK（必做）        = 8（ai_providers 3 · ai_models 2 · ai_routes 2 · ai_policies 1 · ai_request_logs 0）
status CHECK     = 0（D-B16-04）
trigger          = 4（tg_ai_{providers,models,routes,policies}_set_updated_at）
function 新增     = 0（复用 set_updated_at()）
partition        = 父表 1 + 当月子分区 1
非 PK 索引        = 5（含 2 个由 UNIQUE CONSTRAINT 隐式建立）
seed             = 0
P08 → P09 forward FK = 0
```

---

## 6. Open Decisions

```
无 —— D-B16-01 ～ D-B16-11 全部 FROZEN（10 × A + 1 × C）。
```

**下列设计层事项已由 Human 于 2026-09-16 正式裁定**（权威记录见 `B1-6_DECISION_LOG.md` §9）：

| ID | 内容 | 位置 |
|---|---|---|
| **D-1** | `ai_policies` 两条「建议」CHECK 是否实现 | **B — FROZEN：不实现**（必做 CK 保持 8；参考 `users.failed_attempts` 同型先例未在 0003 落地） | `B1-6_SCHEMA_DESIGN.md` §9.2 · `B1-6_DECISION_LOG.md` §9.2 |
| **D-2** | `ix_aimodels_capability` 是否建 | **B — FROZEN：不建立 / 延后**（非 PK 索引保持 5；不新增 AX2 断言） | 同上 §9.3 |
| **T-1** | `INDEX_STRATEGY` 的该索引定义引用 `ai_models` 上不存在的列 | **DEFERRED / FUTURE DESIGN CLARIFICATION**（不改 B0、不决定目标列、不宣布作废） | `B1-6_DECISION_LOG.md` §9.4 / §10 |
| **D-3** | 分区维护机制（预建/清理 job · pg_partman） | **D — FROZEN：手工运维**（0010 不含预建/清理/job/scheduler/pg_partman/扩展） | 同上 §9.5 |
| **D-4** | `ai_request_logs` 字段命名 | **A — FROZEN：`prompt_tokens` + `completion_tokens`**（= 设计现状；列数保持 73） | 同上 §9.6 |
| **DC-1** | 分区子表命名 | **A — FROZEN：`ai_request_logs_<YYYYMM>`**（UTC calendar month） | 同上 §9.7 |

---

## 7. Implementation Blockers

```
B-1  🔴 未获 Implementation Gate 显式授权（本轮为 DESIGN Gate）
B-2  ✅ 已解除 —— 设计层 5 项（D-1 ～ D-4 · DC-1）已由 Human 于 2026-09-16 裁定（见 §6）；T-1 登记为 DEFERRED
B-3  ⚠️ 实施轮连带修改（既有测试）：5 个 FORBIDDEN/FUTURE 集合 + 20 处 head 断言 + smoke 表清单
B-4  ✅ 已裁定 —— **D-3 = D FROZEN（手工运维）**：未来月份分区创建与 90 天保留清理为人工职责；自动化延后
B-5  ⚠️ N-1（CORE:985 类别标签）与 O-3（CORE:985 未记录 F7）—— 已登记，**不阻塞 P08 可实现性**
B-6  ⚠️ 既有：P3-3 生产迁移机械护栏（KEEP DEFERRED）
```

**结论**：设计层**无 BLOCKING**；解除需 §6 的 5 项确认 + Implementation Gate 授权。

---

## 8. Scope Boundary

```
IN SCOPE   : ai_providers · ai_models · ai_routes · ai_policies · ai_request_logs
             + PK 5 · FK 8 · UQ 4 · CK 8 · trigger 4 · 分区（父+当月）· 索引 · 零 seed

OUT OF SCOPE: tool_executions · agents / agent_versions / agent_permissions（P09）
              events / audit_logs（P10）· G/H/I/J（P09 后）· resource_relations（P2）
              P11 跨表 trigger · P12 纯查询索引 · P13 seed
              Authorization Layer / 授权求值 / ABAC / RLS · HTTP API / Socket

DEFERRED   : adapter runtime · provider SDK loading · secret storage 实现
             agent integration · tool execution · 路由/fallback/policy 执行引擎
             分区维护机制
```

---

## 9. Security Boundary

```
不启用 RLS（= 0）· 不实现授权求值 · 不引入 ABAC
jsonb 列（capabilities / config / fallback_chain / allowed_privacy_tiers / denied_providers）storage-only
adapter = 纯文本（不构成代码执行入口）· secret_ref = 仅引用（无明文）
零 seed · 不引入 P09 权限模型
RESTRICT 7 条 · CASCADE 1 条（§11.1 白名单内）
```
详见 `B1-6_SECURITY_REVIEW.md`（BLOCKER = 0 · RISK = 0 · WARN = 3 · PASS = 13）。

---

## 10. Test Matrix Accounting

```
Canonical Total = 38 = 基础九类 37 + decision-derived 1
  AS 6 · AF 5 · AC 8 · AX 2 · AT 2 · AP 3 · AE 1 · AG 4 · AM 6 · AD 1
Registration（后续阶段）= 5 行（RF1–RF5）—— 不计入
S5 对 ai_request_logs.status = EXEMPT / NOT APPLICABLE   ← D-B16-04 = FROZEN — A
Implementation tests written = 0（本阶段）
```

---

## 11. Migration Boundary

```
0010 = ABSENT（本轮未创建）
预期 revision = 0010 · down_revision = 0009_timestamp_precision · 长度 ≤ 32 字符
upgrade 8 步 · downgrade 严格逆序（先子分区后父表）· seed = 0
```
详见 `B1-6_MIGRATION_PLAN.md`。

---

## 12. Production Safety

```
formal uap = 0 tables（未被触碰）
DDL = 0 · DML = 0 · migration executed = NO
0001–0009 未修改 · env.py / alembic.ini / script.py.mako 未修改
```

---

## 13. Gate

```
D-B16-01 … D-B16-11 = ALL FROZEN（10 × A + 1 × C）
D-1 = B FROZEN · D-2 = B FROZEN · T-1 = DEFERRED · D-3 = D FROZEN · D-4 = A FROZEN · DC-1 = A FROZEN
OPEN = 0 · BLOCKING = 0

B1-6 HUMAN DECISION FREEZE  = FROZEN
B1-6 DESIGN DECISION FREEZE = PASS
B1-6 DESIGN                 = COMPLETE
0010 = ABSENT
DATABASE = UNTOUCHED
B0 = PROTECTED（本轮未修改任何 B0 文档）
IMPLEMENTATION = BLOCKED
NEXT GATE = B1-6 Implementation Authorization（须显式授权）
```
