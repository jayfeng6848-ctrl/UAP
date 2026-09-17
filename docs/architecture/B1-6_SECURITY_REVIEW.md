# B1-6 Security Review

**Stage**: B1-6（= P08 AI Gateway）· **Status**: DESIGN —— 只审计设计，**未创建任何数据库对象**
**输入**: `B1-6_DECISION_LOG.md`（D-B16-01 ～ D-B16-11 FROZEN）· `B1-6_SCHEMA_DESIGN.md` · B0 同步后口径
**边界**: 不引入任何运行时授权/执行逻辑；不改 B0；不改代码/测试。

---

## 1. 审计矩阵

| # | 审计项 | 判定 | 说明 |
|---|---|---|---|
| **S1** | **Tenant isolation** | **PASS** | `ai_routes.tenant_id` / `ai_policies.tenant_id` → `tenants.id` **RESTRICT**（D-B16-02 = A）⇒ 租户级行无法指向不存在的租户；租户被引用时不可删。**不启用 RLS** ⇒ 行级隔离依赖应用/授权层（与 B1-4 / B1-5 同口径） |
| **S2** | **Space isolation** | **PASS** | `ai_routes.space_id` / `ai_policies.space_id` → `spaces.id` **RESTRICT**（D-B16-02 = A）。**无** tenant↔space 一致性 trigger（`TRIGGER_INVENTORY` 仅 `tg_resources_tenant_space_consistency`）⇒ **跨表一致性不在 DB 层强制**，与 B1-4 的 resources 处理不同，属既有 B0 口径（`SCHEMA_DEPENDENCY:74/75` 未要求该 trigger） |
| **S3** | **Platform-level ROOT（无 tenant_id）** | **PASS** | `ai_providers` 无 `tenant_id` 列（D-B16-11 = A）· 无 FK ⇒ 平台全局注册表，不存在跨租户写入口径歧义。**性质说明**：这是与 `tools`（`tenant_id NULL = 平台内置`）**不同的** platform-level 表达（"无列" vs "列可 NULL"）；两者并存，见 `B1-6_DEPENDENCY.md` §9 |
| **S4** | **`ai_request_logs` 跨 tenant 数据边界** | **WARN（已知取舍）** | `tenant_id` / `space_id` **无 FK**（D-B16-03 = A）⇒ 可写入不可解析的 tenant/space 值；无 DB 级租户一致性保证。**这是 Human 明确选择的边界**（以便日志不阻塞租户 purge）；隔离由应用层 + 未来授权层承担。**登记为已接受风险（Accepted Risk）** |
| **S5** | **RESTRICT 删除语义** | **PASS** | 7 条 RESTRICT（F2–F8）符合 `CORE §11.1`「业务数据实体一律 RESTRICT」；CASCADE 仅 1 条（`ai_providers → ai_models`），且在 `§11.1` 白名单内（技术子实体） |
| **S6** | **provider / model 删除对 request log 的 RESTRICT 影响** | **PASS（附运维顺序要求）** | 见 §3（N-3 处置）。结论：**可在不改 D-B16-03 的前提下通过 operational ordering / 分区 drop 处理** ⇒ **非 BLOCKING** |
| **S7** | **Privilege escalation** | **PASS** | 本阶段无角色/权限/授权求值；无 `GRANT`/`DENY` 语义；无 `SECURITY DEFINER` 函数；无 RLS bypass 面 |
| **S8** | **`adapter` 不得形成代码执行入口** | **PASS** | `adapter` = **纯 `text` 列**：无 CK、无 UQ、无 FK、无 trigger 读取、无 server_default（D-B16-06 = A）。P08 **不引入**解析/加载/注册/动态导入/运行时发现。**边界声明**：DB 中的 `adapter` 值**不触发任何代码路径** |
| **S9** | **secret 明文设计** | **PASS** | `ai_providers.secret_ref` = `text NULL`，**只存引用**；`config jsonb NULL` 明确「**不含密钥**」（`CONSTRAINT_MATRIX:309`）。**无任何列存储 API Key / token 明文**（对齐 `CORE:1047`） |
| **S10** | **不引入 P09 权限模型** | **PASS** | 无 `agent_permissions` / `tool_permissions` 类比对象；无 `resource_permissions` 绑定；不新增任何主体类型（`acl_subject_types` 不动） |
| **S11** | **Zero seed** | **PASS** | 5 表 seed = 0（`STEP1B_SEED_STRATEGY` 中 `ai_` 0 命中 · D-B16-11 = A）。⇒ **不产生任何默认 provider / 默认路由 / 默认策略**，不存在"出厂预置可被误用"的面 |
| **S12** | **RLS** | **PASS（= 0）** | 不启用 RLS（与 B1-4 / B1-5 同口径）。**登记**：P08 的行级隔离因此完全依赖应用/授权层 |
| **S13** | **Authorization evaluator / ABAC** | **PASS（= 0）** | 本阶段无授权求值；`fallback_chain` / `allowed_privacy_tiers` / `denied_providers` 均为 **jsonb 存储**，**不做求值**（与 B1-5 `conditions` storage-only 同口径） |
| **S14** | **未来授权层交互契约** | **WARN（未冻结）** | 未来授权层如何消费 `ai_policies`（分级/准入/预算）尚未冻结；本阶段只保证"存得住、不解释" |
| **S15** | **分区特有面** | **PASS** | `ai_request_logs` 父表 + 当月子分区（D-B16-05 = A）；PK 含分区键 ⇒ 无跨分区唯一性歧义（本表无 UQ）。**不存 prompt 原文**（`CORE:408`）⇒ 日志内容本身不含对话文本 |
| **S16** | **敏感数据落库面** | **PASS（设计层）** | 5 表中**无**邮箱/电话/身份证等 PII 列；`ai_request_logs.correlation_id` 为不透明关联 id；`error_code` 为错误分类码。**脱敏由应用层承担**（本阶段不设计脱敏实现） |

```
BLOCKER = 0 · RISK = 0 · WARN = 3（S4 / S14 · + §2 的触发面未启用）· PASS = 13
```

### 1.1 边界声明（强制）

```
本阶段仅强制"结构性不变式"：
  · 引用完整性（FK）
  · 取值域（CK）
  · 唯一性（UQ constr / UQ index）
  · updated_at 维护（4 个 BEFORE UPDATE trigger）
  · 分区归属（RANGE(occurred_at)）

本阶段【不】承担：
  · authorization evaluation / role resolution / deny resolution
  · 租户或空间的隐式隔离（无 RLS）
  · AI 分级降级的运行时执行（仅 DB 层 CK 封死非法组合）
  · 密钥管理与解析
  · 任何 AI 运行时行为
```

---

## 2. 与 B1-4 / B1-5 安全结论的一致性

| 结论 | B1-4 | B1-5 | B1-6 | 一致 |
|---|---|---|---|---|
| 不启用 RLS | ✅ | ✅ | ✅ | ✅ |
| 不实现授权求值 | ✅ | ✅ | ✅ | ✅ |
| jsonb 配置列 storage-only | ✅ | ✅（`conditions`） | ✅（`fallback_chain` / `allowed_privacy_tiers` / `denied_providers` / `capabilities` / `config`） | ✅ |
| DENY > ALLOW 留给授权层 | ✅ | ✅ | ✅（无 DENY 概念引入） | ✅ |
| 零 seed | ✅ | ✅ | ✅ | ✅ |
| 业务实体 RESTRICT | ✅ | ✅（`tools.tenant_id`） | ✅（7 条） | ✅ |
| 无明文密钥列 | ✅ | — | ✅（`secret_ref` 仅引用） | ✅ |

**B1-4 / B1-5 的安全结论全部延续未变。**

---

## 3. N-3 处置（provider/model 删除与日志 RESTRICT 的运维语义）

**问题原文**（`B1-6_DEPENDENCY.md` §9 N-3）：`ai_request_logs` 带 FK RESTRICT ⇒ 删除 `ai_providers` / `ai_models` 前须先清 request log；与 `CORE:963`（90 天分区 hard delete）、`CORE:985`（模型目录随 provider purge 清理）的运维顺序需明确。

**结论：可在不改变 D-B16-03 的前提下通过 operational ordering 处理 ⇒ NON-BLOCKING。**

**推演依据（纯 schema 事实）**

```
引用链：
  ai_request_logs.provider_id → ai_providers.id   RESTRICT   (F7)
  ai_request_logs.model_id    → ai_models.id      RESTRICT   (F8)
  ai_models.provider_id       → ai_providers.id   CASCADE    (F1)
  ai_routes.primary_model_id  → ai_models.id      RESTRICT   (F2)

⇒ 删除 ai_providers 会触发 F1 的 CASCADE（尝试删其所有 ai_models）
⇒ 但这些 ai_models 被 F8（logs）与 F2（routes）RESTRICT 引用 ⇒ **CASCADE 将被拒绝**
⇒ 因此 provider/model 的删除必须先解除 F2 / F7 / F8 的引用
```

**运维顺序规则（本设计结论 —— 无需任何 schema 变更）**

```
purge(ai_provider) 步骤：
  1) 清理/删除引用该 provider 或其 models 的 ai_request_logs
     —— 路径 a：经**手工分区维护 / 清理**移除整分区（DROP 分区不触发 FK 检查）
        （**D-3 = D FROZEN ⇒ P08 无自动维护机制**；自动化延后至未来 operational/runtime 阶段）
     —— 路径 b：显式 DELETE（受分区裁剪加速）
  2) 解除 ai_routes 对相应 models 的引用（删除/改写 ai_routes 行）
  3) 删除 ai_models（F2 / F8 引用已解除）
  4) 删除 ai_providers（F1 CASCADE 此时可完成）
```

**未改变项**：`ON DELETE` 全部保持 D-B16-03 / D-B16-02 冻结值；未新增 trigger；未新增 FK。
**未解决项（登记，非阻塞）**：`CORE §11.1:985` 的表述「模型目录随 provider purge 清理」在 F8 RESTRICT 存在时**不能一步到位**——该表述与冻结事实的措辞差异见 §4 的 N-1。

---

## 4. N-1 处置（`CORE:985` 类别标签与 RESTRICT 的语义问题）

**性质判定**：**DESIGN OBSERVATION / DEFERRED ISSUE**（**不在本 Gate 修改 CORE**）

```
位置   : CORE_DOMAIN_MODEL.md:985
原文   : | 技术子实体 | `ai_providers → ai_models`、`ai_models → ai_request_logs`(若建 FK) | 模型目录随 provider purge 清理 |
问题   : ① 该行位于 CASCADE 白名单节（"技术子实体"类别其余条目均 CASCADE 族），
          但 D-B16-03 = A 冻结 ai_models → ai_request_logs 为 **RESTRICT**；
        ② 该行的条件式「(若建 FK)」已被 D-B16-03 = A 消解为"FK 已建 + RESTRICT"，
          该处已在 AUTH-02 授权范围内同步（标注「FK 已建，ON DELETE RESTRICT」）；
        ③ 但**类别标签「技术子实体」未修改** —— 改标签超出 AUTH-02
          「仅根据 D-B16-02 / D-B16-03 结果修正 FK 事实」的范围。
```

**本阶段处置**：**仅登记**。不修改 `CORE_DOMAIN_MODEL.md`。不影响 P08 可实现性。

**关联**：`STEP1B_CONSTRAINT_MATRIX:343-352` 的 `ai_request_logs` 段 FK 行已由 AUTH-02 落为 RESTRICT（一致）；
`SCHEMA_DEPENDENCY:76` 的「FK 尽量保持 NULL 宽松」取向已被同批同步替换为确定 RESTRICT 事实（一致）。

---

## 5. 其他登记项

| # | 内容 | 类别 |
|---|---|---|
| **O-1** | `ai_request_logs` 字段命名差异：`CONSTRAINT_MATRIX:348` 写 `tokens`；`CORE:412` 写 `prompt_tokens` + `completion_tokens`。本设计采用 CORE 细分命名 | DESIGN OBSERVATION（不改 B0） |
| **O-3** | `CORE:985` 未记录 `ai_request_logs.provider_id → ai_providers`（D-B16-03 新增的 F7）。补记录超出 AUTH-02 范围 | DEFERRED |
| **O-4** | `ai_request_logs` 的 `tenant_id` / `space_id` 无 FK ⇒ **无 DB 级租户隔离**（S4 的 Accepted Risk） | Accepted Risk（Human 已裁定） |
| **O-5** | 分区子表命名 `ai_request_logs_<YYYYMM>`（UTC calendar month） | **DC-1 = A FROZEN（2026-09-16）** |
| **O-6** | `ai_policies` 的 2 条「建议」CK | **D-1 = B FROZEN ⇒ 不实现**（DB 层允许负值，属已裁定取舍） |

---

## 6. 结论

```
B1-6 SECURITY REVIEW = DESIGN REVIEWED
BLOCKER = 0 · RISK = 0
WARN = 3（S4 跨租户日志无 FK · S14 未来授权层契约未冻结 · 一致性 trigger 未启用）
PASS = 13

关键边界（强制）：
  不启用 RLS · 不实现授权求值 · jsonb 列 storage-only
  adapter = 纯文本（不构成代码执行入口）
  secret_ref = 仅引用（无明文）
  零 seed · 无 P09 权限模型

N-1 = DESIGN OBSERVATION / DEFERRED ISSUE（未改 CORE）
N-3 = 已给出 operational ordering 结论（NON-BLOCKING，未改 D-B16-03）；D-3 = D FROZEN 后分区维护为人工职责
T-1 = DEFERRED / FUTURE DESIGN CLARIFICATION（INDEX_STRATEGY 的 ix_aimodels_capability 引用不存在列）
DESIGN DECISION FREEZE = PASS（D-1 = B · D-2 = B · D-3 = D · D-4 = A · DC-1 = A）
```
