# AUTHORIZATION / ACL / POLICY — ACCEPTANCE MATRIX

| 字段 | 内容 |
|---|---|
| **阶段** | `STAGE 2 — AUTHORIZATION / ACL / POLICY PREP` |
| **日期** | 2026-09-23 |
| **基线** | HEAD `eb6d4cb…` · TAG `UAP-V0.1.7-GOVERNANCE-GATE` · Alembic head `0011_p09_agent_tool_permission` |
| **配套** | [`AUTHORIZATION_PREP_REPORT.md`](./AUTHORIZATION_PREP_REPORT.md) |
| **性质** | **本矩阵为未来实施阶段的验收判据，不构成当前验收结论** |

## 状态图例

| 标记 | 含义 |
|---|---|
| `ASSET` | 既有冻结资产**已具备**该能力（附 0011 实测证据）；实施阶段只需**沿用**而非新建 |
| `PENDING` | 尚无实现，须由实施阶段交付 |
| `BLOCKED-OQ` | 被 §18 的 OQ 阻塞，OQ 裁定前不可实施 |
| `BLOCKED-P10` | 被 P10（`events`/`audit_logs`）阻塞 |

> ⚠ **任何行都不得在 OQ 裁定前标记为 PASS。** 本阶段 `IMPLEMENTATION = NOT AUTHORIZED`。

---

## 1. ARCH — 架构放置与分层

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| ARCH-01 | 授权**契约**位于 `core/`，**不**承载持久化 | `core/permission` `core/policy` `core/resource` 已存在；G-1/G-2 硬门 | `core` 无 sqlalchemy/psycopg/services 依赖 | AST 守卫 `G-1` `G-2` | 0 命中 | **ASSET** |
| ARCH-02 | 授权**实现**位于 `services/`，且为唯一持久化承载层 | `D-PLAT-03`；`services/` **尚不存在** | 实现落 `services/authorization/` | 目录存在 + `git ls-files services` | 包存在且含实现 | `BLOCKED-OQ`(A16) |
| ARCH-03 | `core ↛ domains` 不倒置 | `DEPENDENCY_RULES.md` §7；守卫 `test_core_never_imports_domains` | 0 命中 | AST 守卫 | 0 命中 | **ASSET** |
| ARCH-04 | `agent ↛ infrastructure` / `apps` / `services` 不倒置 | G-3 硬门（含 `services`） | 0 命中 | AST 守卫 `G-3` | 0 命中 | **ASSET** |
| ARCH-05 | 不新建第三个授权契约模块（避免概念分裂） | `core/permission` + `core/policy` 已双契约 | 复用而非新增 | 人工 + 目录审计 | 无新增 core 契约包 | `BLOCKED-OQ`(A16) |
| ARCH-06 | `domains` 经约定契约消费授权，不自建框架 | `D-PLAT-06` / `06.a`；domains 仅 `manifest.py` | 0 越界依赖 | AST 守卫 `G-4` | 0 命中 | **ASSET** |

## 2. AUTH — 授权模型本体

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| AUTH-01 | 三层职责不重叠：RBAC=基线 / ACL=实例 / Policy=条件 | §6.1 职责表；`core/permission` 与 `core/policy` Owns 描述**已重叠** | 明确单一归属，无重复求值路径 | 契约审计 + 代码路径审计 | 每个决策只经一条求值链 | `BLOCKED-OQ`(A01) |
| AUTH-02 | 决策**确定性** | 未实现 | 同输入恒同输出 | 重复求值测试 | 100 次一致 | `PENDING` |
| AUTH-03 | 决策**顺序无关** | 未实现 | 规则顺序不改变结果 | 排列组合测试 | 全排列一致 | `PENDING` |
| AUTH-04 | 决策**可审计** | `core/audit` 契约存在，字段不足；`audit_logs` 不存在 | 每次决策可追溯 | 审计字段断言 | 字段齐备 | `BLOCKED-P10` |
| AUTH-05 | `Subject` 可表达 user / agent / role | `acl_subject_types` 白名单已含三者；`Subject` 仅 `identity_id` | 契约可表达三类主体 | 契约单元测试 | 三类均可构造并求值 | `BLOCKED-OQ`(A02/A18) |
| AUTH-06 | Action 有统一词汇表 | `Action(name, resource_type)` 无枚举；DB `action` 为自由 text | 词表冻结且可校验 | 契约 + DB 断言 | 枚举一致 | `BLOCKED-OQ`(A05) |
| AUTH-07 | 无"不同代码路径不同结果" | 未实现 | 单一求值入口 | 入口唯一性审计 | 仅 1 个 public 求值函数 | `PENDING` |
| AUTH-08 | Agent 不得绕过 Authorization | `agent/tools` 契约明示工具是唯一出口 | 无旁路 | AST + 运行时守卫 | 0 旁路 | `PENDING` |
| AUTH-09 | Tool 不得绕过 Policy | `Tool.invoke` **不**携带授权结果（现状缺口） | 工具无法在无决策下执行 | 契约审计 | 执行前强制决策参数 | `BLOCKED-OQ`(A09) |

## 3. TENANT — 租户隔离

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| TENANT-01 | 任何授权决策携带 tenant scope | `resources.tenant_id` NN；`TenantContext` 契约 | 缺 tenant ⇒ DENY | 契约测试 | 拒绝 | `PENDING` |
| TENANT-02 | 跨租户访问不可通过 ACL 提升 | `acl_subject_types` 白名单；`STEP1B_ACL_STRATEGY` §4 | 跨租户 ACL 无效 | 跨租户注入测试 | DENY | `PENDING` |
| TENANT-03 | role 仅在 `role.tenant_id = resource.tenant_id`（或 platform role）时生效 | `STEP1B_ACL_STRATEGY` §4 明文 | 错配无效 | 集成测试 | DENY | `PENDING` |
| TENANT-04 | `require_same_tenant()` 语义被沿用 | `core/tenant/interfaces.py` 已实现该函数 | 不一致即抛错 | 单元测试 | 抛 `PermissionError` | **ASSET** |
| TENANT-05 | DB 层 tenant/space 一致性由 trigger 强制 | `tg_resources_tenant_space_consistency` · `tg_agents_tenant_space_consistency` | 非法组合被拒 | DB trigger 测试 | RAISE | **ASSET** |
| TENANT-06 | formal 库全程未被触碰 | 生产 `uap` = 0 表 | 0 变更 | `information_schema` 计数 | = 0 | **ASSET** |

## 4. SCOPE — 作用域

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| SCOPE-01 | scope 层级明确（PLATFORM→TENANT→SPACE→RESOURCE?） | `ck_roles_scope` 3 值 + `tg_roles_scope_shape` + 3 部分唯一索引 | 层级冻结且互斥 | DB 约束 + 契约测试 | 形状非法即拒 | **ASSET**（3 层）/ `BLOCKED-OQ`(A06)（4/5 层） |
| SCOPE-02 | `SELF` 作用域定义（§12 要求） | 现有模型**无** SELF | 明确定义或显式排除 | 契约审计 | 有明确裁定 | `BLOCKED-OQ`(A06) |
| SCOPE-03 | 角色三作用域互斥由 DB 强制 | `uq_roles_platform` / `uq_roles_tenant` / `uq_roles_space` 实测 | 重复角色被拒 | DB 唯一性测试 | 违反即拒 | **ASSET** |
| SCOPE-04 | resource scope 过滤（space 有值时须相等） | `core/resource.is_in_scope()` 已实现 | 越界为 False | 单元测试 | 越界 False | **ASSET** |
| SCOPE-05 | 资源继承（`inherited`）可用 | `resource_permissions.inherited` 存在，**但无 parent 资源** | 继承语义可判定 | 契约 + DB 审计 | 明确裁定 | `BLOCKED-OQ`(A04/A08) |

## 5. AGENT — Agent 作为主体

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| AGENT-01 | Agent 可被表达为授权主体 | `acl_subject_types` CHECK 白名单含 `agent`；`agent_permissions` 表存在 | 契约可表达 | 契约测试 | 可求值 | `BLOCKED-OQ`(A02) |
| AGENT-02 | Agent 权限**不越过** actor 边界 | §14 原则；`tool_executions` 双列已备；**无强制** | 交集语义 | 越权注入测试 | DENY | `BLOCKED-OQ`(A03) |
| AGENT-03 | Agent 独立权限可表达 | `agent_permissions(permission_id/tool_id, effect, conditions)` 为**授权权威面**；`resource_scope` 为 **opaque**（`D-AUTH-23`，**非**权威面） | 可表达 | DB + 契约审计 | 三选一非空（`ck_agent_permissions_scope_target`） | **ASSET** |
| AGENT-04 | Agent 风险上限受约束 | `agents.max_risk_level` 四档 CHECK | 超限动作被拒 | 集成测试 | DENY | `PENDING` |
| AGENT-05 | Agent 禁用/归档后授权立即失效 | `agents.status(draft/active/disabled/archived)`；`agent_versions.status(...revoked)` | 失效 | 状态机测试 | DENY | `PENDING` |
| AGENT-06 | Delegation 关系可审计 | `tool_executions.actor_id` + `agent_id`；**`AuditEvent` 无 delegator** | delegator 可追溯 | 审计字段断言 | 字段齐备 | `BLOCKED-P10` |
| AGENT-07 | Agent 版本标识类型一致 | `AgentDescriptor.version: str` vs `agent_versions.version integer` | 类型对齐 | 契约审计 | 一致 | `BLOCKED-OQ`(A19) |
| AGENT-RESOURCE-SCOPE-01 | 运行时 `.py` 对 `agent_permissions.resource_scope` 的 **code 级引用 = 0**（AST 判定；docstring 声明不计） | AST 守卫实测 0 | 0 引用 | `tests/architecture/test_agent_resource_scope_opaque.py`（豁免：migration 源 · integration test · 说明性 docstring） | 运行时命中 = 0 | **PASSED** |
| AGENT-RESOURCE-SCOPE-02 | `resource_scope` **不构成**授权权威 | `D-AUTH-23`（`FROZEN`）· `0011` 源自述「不解释、不构成授权判定」 | 服务不读取、不推导 `PLATFORM`/`TENANT`/`SPACE` | 契约审计 + 服务调用路径检查 | 0 条推导路径 | `PENDING` |
| AGENT-RESOURCE-SCOPE-03 | **P09 schema 未变**（`resource_scope` 保持 opaque） | `0011` sha256 `cdaf8383630335db…`；列集 / 约束集 / 索引集与基线**逐项相等** | 零变更 | migration 目录审计 + `information_schema` 逐项比对 | 逐项相等 | **ASSET** |
| AGENT-RESOURCE-SCOPE-04 | 空串 / 空白 / 任意 opaque 取值**不产生 `ALLOW`** | **`ND-A`** = 不追加 `<> ''` ⇒ `''` 与 `'   '` 结构合法；字段不参与授权 | 结果由其**他**权威来源决定 | 求值注入测试 | 无 `ALLOW` | `PENDING` |

> **`AGENT-RESOURCE-SCOPE-01…04` 的完整定义见** `AUTHORIZATION_IMPLEMENTATION_TEST_MATRIX.md` **§5.1**。
> 该系列**不含任何 schema 动作** —— 0 DDL / 0 DML / 0 migration。

## 6. TOOL — 工具授权

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| TOOL-01 | 工具声明所需权限（结构化） | `tool_permissions` 仅指向 `permission_id`，**无 resource/action/scope** | 结构化四元组 | 契约 + schema 审计 | 可静态验证 | `BLOCKED-OQ`(A09) |
| TOOL-02 | 工具是 agent 到 service 的**唯一**通道 | `agent/tools` 契约 docstring | 无旁路 | AST 守卫 | 0 旁路 | **ASSET**（契约）/ `PENDING`（强制） |
| TOOL-03 | 工具执行前强制授权决策 | `Tool.invoke(params, context)` **无决策参数** | 决策前置 | 契约审计 | 参数强制 | `BLOCKED-OQ`(A09) |
| TOOL-04 | 版本级白名单可校验 | `agent_versions.allowed_tools`(jsonb) | 白名单外拒执行 | 集成测试 | DENY | `PENDING` |
| TOOL-05 | 执行记录含 agent + actor 归属 | `tool_executions.agent_id` + `actor_id` 实测 | 双归属 | DB 断言 | 两列可选且可填 | **ASSET** |
| TOOL-06 | 拒绝已进入执行生命周期 | `ck_tool_executions_status` 含 `denied` | `denied` 为终态 | DB CHECK | 枚举含 denied | **ASSET** |
| TOOL-07 | **Tool 侧**与 **Agent 侧**授权路径**相互独立、互不替代** | `tool_permissions`（Tool 侧结构，0008）vs `agent_permissions.resource_scope`（Agent 侧 P09 opaque，0011） | 两条独立路径，各自可验证 | 契约审计 + schema 审计 | 无交叉推导 | `BLOCKED-OQ`(A09) |

> **`TOOL-07` 已于 2026-09-23 拆分**（原行把 Tool 侧与 Agent 侧混为一条）：
> **Tool 侧** → 保留为 `TOOL-07`（本行，与 `SC-2` / `D-AUTH-09` 对应）；
> **Agent 侧** → 迁至 §5 `AGENT-RESOURCE-SCOPE-01…04`（依据 **`D-AUTH-23`**，`resource_scope` = Legacy Opaque）。
> 原始措辞「`resource_scope` 自由 text 被治理」**不再适用** —— 该字段**不要求**被治理为结构化，**只需**保持 opaque 且不被当作授权权威。

## 7. POLICY — 策略

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| POLICY-01 | Policy 归属单一（不与 `core.permission` 重叠） | 两模块 Owns 描述重叠 | 单一归属 | 契约审计 | 无重复求值 | `BLOCKED-OQ`(A01) |
| POLICY-02 | 策略**只能收紧**，不能放宽静态授予 | §19/§21 要求；`combine()` any-deny-wins 已成文 | 不可放大 | 策略注入测试 | 无法放大 | `PENDING` |
| POLICY-03 | `conditions` 从 storage-only 升级为可解析（若采用 Option C） | `R2-D-15` 明示当前 **storage-only** | 解析确定性 | 策略求值测试 | 确定性 | `BLOCKED-OQ`(A01) |
| POLICY-04 | 策略版本可追溯 | §22 要求 `policy_version`；现无 | 版本入决策与审计 | 契约审计 | 字段存在 | `BLOCKED-OQ`(A14) |
| POLICY-05 | `combine()` 语义与 `R2-D-14` 合并为单一算法 | `core/policy.combine()` any-deny-wins；`R2-D-14` DENY>ALLOW | 单一算法 | 契约审计 + 测试 | 单一入口 | `BLOCKED-OQ`(A07) |

## 8. RISK — 风险

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| RISK-01 | 风险值域**统一**（四档 vs float 冲突解决） | DB 3 表四档 CHECK vs `RiskPolicy.score()->float[0,1]` | 单一值域 | 契约 + DB 审计 | 一致 | `BLOCKED-OQ`(A10) |
| RISK-02 | 四档枚举完整 | `ck_tools_risk_level` / `ck_agents_max_risk_level` 实测 `LOW/MEDIUM/HIGH/CRITICAL` | 四档 | DB CHECK | 一致 | **ASSET**（DB）/ `PENDING`（契约） |
| RISK-03 | 风险参与决策（非仅存储） | `tool_executions.risk_level` 已落库；无求值 | 风险影响决策 | 集成测试 | 高风险被拦 | `PENDING` |
| RISK-04 | Agent 风险上限与工具风险交叉校验 | `agents.max_risk_level` + `tools.risk_level` | 超限拒绝 | 集成测试 | DENY | `PENDING` |

## 9. APPROVAL — 人工审批边界

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| APPROVAL-01 | 审批需求可表达（静态 + 动态） | `tools.approval_required`（静态 bool）已落库；无动态 | 静态下限 + 策略加严 | 契约审计 | 两者共存且不冲突 | `BLOCKED-OQ`(A11) |
| APPROVAL-02 | 决策结果含 `REQUIRES_APPROVAL` | `Decision(allowed: bool)` **无三值** | 三值结果 | 契约测试 | 三值可表达 | `BLOCKED-OQ`(A14) |
| APPROVAL-03 | 执行生命周期有"待审批"态 | `tool_executions.status` 无 `awaiting_approval` | 状态可表达 | DB CHECK | 枚举含待审批 | `BLOCKED-OQ`(A11) |
| APPROVAL-04 | §19 五类高敏动作有明确边界 | `Delete`/`Export`/`External Send`/`Financial`/`Permission Change`/`Cross-Space` | 每类有档位 | 设计审计 | 六类全覆盖 | `BLOCKED-OQ`(A11) |
| APPROVAL-05 | 审批系统**本阶段不实现** | §18 明令 | 0 实现 | 代码审计 | 0 新增代码 | **ASSET**（遵守） |

## 10. CACHE — 缓存与撤销

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| CACHE-01 | 首发不产生 stale allow | 当前无任何授权缓存 | 零缓存或零 stale | 代码审计 | 0 缓存路径 | **ASSET**（现状）/ `BLOCKED-OQ`(A13) |
| CACHE-02 | 撤销后授权立即失效 | `revoked_at`/`archived_at`/`expires_at`/`status` 四个信号已落库 | 失效 | 撤销测试 | 立即 DENY | `PENDING` |
| CACHE-03 | Role 归档后 deny 行不再参与决策 | `STEP1B_ACL_STRATEGY` §5 明文 | deny 失效、allow 保留 | 集成测试 | 符合 §5 | `PENDING` |
| CACHE-04 | Agent 归档使 ACL 到期 | `STEP1B_ACL_STRATEGY` §5（`expires_at=now()`） | 到期 | 集成测试 | 到期 | `PENDING` |
| CACHE-05 | RLS（可选）不破坏隔离 | `STEP1B_ACL_STRATEGY` §4 Q1（未实施） | 连接池归还后重置 | 不适用 | 未实施 | `PENDING` |

## 11. AUDIT — 审计

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| AUDIT-01 | 授权决策与工具执行**不混为一谈** | `core/audit.AuditEvent` 与 `tool_executions` 为不同载体 | 概念分离 | 设计审计 | 分离 | **ASSET**（概念）/ `PENDING`（实现） |
| AUDIT-02 | 审计字段齐备（§23 的 14 项） | `AuditEvent` 缺 `subject`/`delegator`/`decision`/`reason`/`policy`/`risk`/`approval` | 14 项齐备 | 字段断言 | 齐备 | `BLOCKED-P10` |
| AUDIT-03 | 授权审计持久化可用 | **`audit_logs` / `events` 在 0011 不存在（P10）** | 可落库 | 表存在性 | 表存在 | `BLOCKED-P10` |
| AUDIT-04 | append-only 不可变 | `D-PLAT` 数据律「`audit_logs` 不可变」；`AuditSink.write()` 仅追加 | 无 UPDATE/DELETE | DB 权限/trigger | 不可变 | `BLOCKED-P10` |
| AUDIT-05 | ACL grant/revoke 同事务审计 | `STEP1B_ACL_STRATEGY` §6 明文 | 同事务 | 集成测试 | 原子 | `PENDING` |
| AUDIT-06 | `AuditEvent.id` 生成策略合规 | `uuid.uuid4()` vs 数据律 UUIDv7 | 明确定义 | 契约审计 | 有裁定 | `BLOCKED-OQ`(A22) |

## 12. SECURITY — 安全边界

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| SEC-01 | `Agent → Database` 路径不存在 | `agent/` 无 db import（实测 0） | 0 | AST 守卫 `G-3` | 0 | **ASSET** |
| SEC-02 | `Agent → SQL / session / engine` 不存在 | 全层扫描仅 1 处字面量误报（已核对） | 0 | AST + 人工核对 | 0 | **ASSET** |
| SEC-03 | `Tool → Permission Bypass` 无 | `Tool.invoke` 不携带决策（缺口） | 无旁路 | 契约审计 | 强制决策 | `BLOCKED-OQ`(A09) |
| SEC-04 | `API → Direct Execution` 无 | `apps/` 仅 health/meta 路由 | 0 | 路由审计 | 0 | **ASSET** |
| SEC-05 | `User Input → Privilege Escalation` 无 | `Subject` 由调用方构造（缺口） | 主体来自 trusted context | 契约审计 + 注入测试 | 不可伪造 | `PENDING` |
| SEC-06 | 授权失败统一 FAIL CLOSED | `DENY`/`default_decision()`/`combine()`/`R3-D-07`/`R5` 多重先例 | 8 类失败分支全 DENY | 失败注入矩阵 | 全 DENY | `BLOCKED-OQ`(A12) |
| SEC-07 | `HIGHLY_CONFIDENTIAL` 资源不被降级 | `ck_resources_classification`；数据律「HIGHLY_CONFIDENTIAL 禁降级」 | 不降级 | DB CHECK + 集成测试 | 拒绝降级 | **ASSET**（DB） |
| SEC-08 | ACL 变更对 CRITICAL 资源记 HIGH 风险 | `STEP1B_ACL_STRATEGY` §6 明文 | 风险标记 | 集成测试 | 标记 HIGH | `BLOCKED-P10` |
| SEC-09 | 无伪造 subject | `tg_acl_subject_exists`；`CORE_DOMAIN_MODEL` §1.3 | RAISE | DB trigger 测试 | RAISE | **ASSET** |
| SEC-10 | 注册表不可被 runtime 扩展 | `tg_acl_subject_types_protect` + 硬编码 CHECK 白名单 | 拒绝 | DB trigger 测试 | RAISE | **ASSET** |

## 13. DEPENDENCY — 依赖与前置

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| DEP-01 | 架构守卫全绿 | `tests/architecture` **14 passed**（实测） | 全绿 | pytest | 0 failed | **ASSET** |
| DEP-02 | 不要求 `core → domains` | 设计审计（§16） | 0 | AST 守卫 | 0 | **ASSET** |
| DEP-03 | 不要求 `agent → infrastructure` | 设计审计（§16） | 0 | AST 守卫 `G-3` | 0 | **ASSET** |
| DEP-04 | `services/` 包前置条件被显式登记 | `D-PLAT-01`；包**不存在** | 实施前须建包 | 目录审计 | 已登记 | **ASSET**（已登记）/ `PENDING`（建包） |
| DEP-05 | 审计持久化依赖 P10 被显式登记 | `events`/`audit_logs` 0011 不存在 | 依赖图明确 | 表存在性 | 已登记 | **ASSET**（已登记）/ `BLOCKED-P10` |
| DEP-06 | Agent Runtime 依赖图已产出 | §27 依赖图（8 项能力） | 图完整 | 报告审计 | 8/8 | **ASSET** |
| DEP-07 | Module 消费方式已定义 | §28；无 Module 实现 | 只声明 Resource/Action/Policy | 设计审计 | 无第二套框架 | `PENDING` |

## 14. MIGRATION — 迁移影响（Proposed only）

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| MIG-01 | 本阶段创建 migration 数 = 0 | `0012+` absent（实测） | 0 | 目录审计 | 0 | **ASSET** |
| MIG-02 | `0010` 未被修改 | sha256 `6d9907237f80e9da…` | 未变 | sha256 比对 | 一致 | **ASSET** |
| MIG-03 | `0011` 未被修改 | sha256 `cdaf8383630335db…` | 未变 | sha256 比对 | 一致 | **ASSET** |
| MIG-04 | 单 head / 无 branch | `alembic heads`=0011；`branches`=空 | 单一 | alembic 命令 | 通过 | **ASSET** |
| MIG-05 | 任何未来 schema 变更仅登记为 PROPOSED | §17 表 | 未创建 | 目录审计 | 0 新表 | **ASSET** |
| MIG-06 | 未擅自建表（无提前建表） | `resources.parent_id` / `policy_rules` / `approval_requests` / `resource_relations` 均不存在 | 0 | `information_schema` | 0 | **ASSET** |
| MIG-07 | P09 schema/trigger/约束未触碰 | 0011 内 P09 对象未变 | 0 变更 | DB 对象比对 | 0 | **ASSET** |

## 15. REGRESSION — 回归基线

| ID | Requirement | Evidence | Expected Result | Verification Method | Pass Condition | Cur. |
|---|---|---|---|---|---|---|
| REG-01 | 定向测试基线不下降 | 上轮基线：architecture+contract+unit = **115 passed** | ≥ 115 | pytest | 0 failed | **ASSET**（基线） |
| REG-02 | 全量回归基线不下降 | 上轮基线：**342 passed / 0 failed / 0 error** | ≥ 342 | pytest | 0 failed | **ASSET**（基线） |
| REG-03 | 架构守卫负向样例有效 | 上轮基线 **14/14**（7 负向 + 7 对照） | 14/14 | 合成树注入 | 全 PASS | **ASSET**（基线） |
| REG-04 | 工作树干净 | `git status --porcelain` = 0（本轮前）；本轮新增 2 个 PREP 文档 | 仅 PREP artifacts | `git status` | 无意外文件 | `PENDING`（复核） |
| REG-05 | 无 commit / tag / push | 本轮未执行 | 未执行 | `git log` | HEAD 未推进 | **ASSET** |
| REG-06 | 生产库未被触碰 | formal `uap` = 0 表 | 0 | `information_schema` | 0 | **ASSET** |

---

## 16. Decision ↔ Acceptance 映射（§32，2026-09-23 决议轮补入）

> 依据 `AUTHORIZATION_DECISION_RESOLUTION.md`。**当前 22 项决策全部为 `PROPOSED`（`HUMAN DECISION = PENDING`）**，
> 故本映射表目前是**待激活的映射**；Human 冻结后即为「每项 FROZEN 决策 → 至少一条验收判据」的完整凭据。

| OQ | 对应 Acceptance 行 | 映射依据 |
|---|---|---|
| A01 | AUTH-01 · POLICY-01 · POLICY-05 | 组合模式 + 职责唯一性 |
| A02 | AGENT-01 · AUTH-05 | Agent 作为主体可表达 |
| A03 | AGENT-02 · AGENT-06 | 越权边界 + delegation 审计 |
| A04 | SCOPE-05 | 资源继承可用性 |
| A05 | AUTH-06 | Action 词表可校验 |
| A06 | SCOPE-01 · SCOPE-02 · SCOPE-03 · SCOPE-04 | Scope 层级 + SELF 定性 |
| A07 | POLICY-05 · SEC-06 | 单一合并算法 + fail-closed |
| A08 | SCOPE-05 · CACHE-03 · CACHE-04 | 继承 / 归档 / 到期 |
| A09 | TOOL-01 · TOOL-03 · TOOL-07 · SEC-03 · AUTH-09 | 工具授权结构化 + 无旁路 |
| A10 | RISK-01 · RISK-02 · RISK-03 · RISK-04 | 风险值域统一 |
| A11 | APPROVAL-01 · APPROVAL-03 · APPROVAL-04 | 审批模型与状态承载 |
| A12 | SEC-06 | 失败语义统一 |
| A13 | CACHE-01 · CACHE-02 | 缓存与撤销 |
| A14 | APPROVAL-02 · AUTH-05 · POLICY-04 | Decision 契约三值 |
| A15 | AUDIT-02 · AUDIT-03 · AUDIT-05 | 审计字段与持久化 |
| A16 | ARCH-02 · ARCH-05 | 契约 / 实现落点 |
| A17 | MIG-05 · MIG-06 | schema 三档分类与零变更 |
| A18 | AUTH-05 · SEC-09 · SEC-10 | 主体词汇统一 + 防线保持 |
| A19 | AGENT-07 | 版本语义 |
| A20 | SEC-08 · CACHE-03 | ACL 改判与审计 |
| A21 | DEP-06 · DEP-07 | 依赖图与 Module 消费 |
| A22 | AUDIT-06 | 审计 id 生成 |
| — | `AGENT-RESOURCE-SCOPE-01` · `AGENT-RESOURCE-SCOPE-02` · `AGENT-RESOURCE-SCOPE-03` · `AGENT-RESOURCE-SCOPE-04` · `TOOL-07` | `resource_scope` = Legacy Opaque（`D-AUTH-23` · `GAP-11`，**非** OQ）；Tool 侧 / Agent 侧路径分离 |
| — | `SC-1` · `SC-1b` · `T-ACT-01`…`T-ACT-06` · `MIG-05` · `MIG-06` | `D-B14-08` → **SUPERSEDED** by `D-AUTH-05`（`D-AUTH-24`）；Action canonical **存储形 = 小写**（`D-AUTH-25`，NFKC + casefold 归一） |

**覆盖核对**（**实测，非估算**）：**22 / 22 OQ** 均至少映射到 1 条验收行；**另加非 OQ 决策 3 条**（`D-AUTH-23` · `GAP-11`；`D-AUTH-24` / `D-AUTH-25` · `D-B14-08` 冲突裁定）
⇒ 决策侧 **23 / 23** 有归属，**无 orphan**。
被映射的验收行**去重后 = 50 行**（占矩阵 **99** 行的 **50.5%**）；**50 个 ID 已逐一验证均真实存在于本矩阵**（无悬空引用）。
**`FROZEN` 决策数 = 22**（19 OQ + `D-AUTH-23/24/25`）· `DEFERRED` = 3 · 平台级 `SUPERSEDED` = 1（`D-B14-08` → `D-AUTH-05`）⇒ 「Every FROZEN decision → at least one criterion」**已满足**。

> **历史值对照**（`GAP-11` 轮之前）：映射 **46** 行 / 矩阵 **95** 行 = 48.4%。
> 变化 **+4** 行（`AGENT-RESOURCE-SCOPE-01…04`）· **+1** 决策（`D-AUTH-23`）。

---

## 17. DECISION FREEZE 状态（2026-09-23）

> **Human 已于 2026-09-23 逐项裁定 22 项 OQ**：**19 `FROZEN` + 3 `DEFERRED` + 0 `SUPERSEDED`**。
> 决策正文见 `PLATFORM_DECISION_LOG.md` 的 `D-AUTH-01`…`D-AUTH-25`。
> **本表把每项决策映射到可验证的验收判据（§29 要求）**；`DELIVERABLE` = 交付阶段。
>
> **追加（2026-09-23）**：**`GAP-11` 专项** —— `D-AUTH-23` = `FROZEN`（**非 OQ**，见 **§17.4**）。
> **追加（2026-09-24）**：**`D-B14-08` 冲突裁定** —— `D-AUTH-24`（supersession）与 `D-AUTH-25`（Action canonical 形 = 小写）= `FROZEN`（**非 OQ**，见 **§17.5**）。
> ⇒ `D-AUTH` 条目总数 **23**：**`FROZEN` 20 + `DEFERRED` 3**；`OQ` 口径仍为 **19 + 3 = 22**。

### 17.1 FROZEN（19）

| OQ | Decision ID | Status | Acceptance Criterion | Verification Method |
|---|---|---|---|---|
| A01 | `D-AUTH-01` | **FROZEN** | 三层职责无重复求值路径；`conditions` 归属唯一 | 契约审计 + 求值入口唯一性检查（AUTH-01 · POLICY-01 · POLICY-05） |
| A02 | `D-AUTH-02` | **FROZEN** | Agent 可作为授权主体被求值 | 契约测试（AGENT-01 · AUTH-05） |
| A04 | `D-AUTH-04` | **FROZEN** | Resource 7 项 canonical 属性齐备；owner 仅 User | schema 审计 + 契约测试（SCOPE-05） |
| A05 | `D-AUTH-05` | **FROZEN** | 12 项 Action 词表可校验；无自由字符串绕过 | DB CHECK + 契约枚举断言（AUTH-06） |
| A06 | `D-AUTH-06` | **FROZEN** | 3 层 scope 互斥；`SELF` 为 predicate 非 scope | DB 约束测试 + 谓词测试（SCOPE-01…04） |
| A07 | `D-AUTH-07` | **FROZEN** | 同输入同输出；规则顺序无关；可解释命中来源 | 重复求值 / 全排列 / 审计字段测试（POLICY-05 · SEC-06） |
| A08 | `D-AUTH-08` | **FROZEN** | 无隐式资源父级继承；explicit deny 参与计算 | 继承测试 + 越界注入（SCOPE-05 · CACHE-03 · CACHE-04） |
| A09 | `D-AUTH-09` | **FROZEN** | 工具四元组可静态校验；执行前强制携带决策 | 契约审计 + 静态校验测试（TOOL-01 · TOOL-03 · TOOL-07 · SEC-03 · AUTH-09） |
| A10 | `D-AUTH-10` | **FROZEN** | 授权判定仅用四档枚举；`score` 不对外 | 契约 + DB 值域断言（RISK-01…04） |
| A11 | `D-AUTH-11` | **FROZEN** | `approval_required` = 静态 OR 策略；审批结果≠ALLOW | 组合逻辑测试 + 语义断言（APPROVAL-01 · 03 · 04） |
| A12 | `D-AUTH-12` | **FROZEN** | 8 类失败分支一律 DENY | 失败注入矩阵（SEC-06） |
| A14 | `D-AUTH-14` | **FROZEN** | 三值可表达；`REQUIRES_APPROVAL` 不可被当作可执行 | 契约测试 + 调用方行为测试（APPROVAL-02 · AUTH-05 · POLICY-04） |
| A15 | `D-AUTH-15` | **FROZEN** | 审计字段 12 类齐备；与 Tool Execution 分离 | 字段断言 + 载体分离审计（AUDIT-02 · 03 · 05） |
| A16 | `D-AUTH-16` | **FROZEN** | core 无 I/O；agent 不经 DB/infrastructure | AST 守卫 `G-1` `G-2` `G-3`（ARCH-02 · ARCH-05） |
| A17 | `D-AUTH-17` | **FROZEN** | 本冻结 0 schema 变更；仅 2 个方向列入研究 | migration 目录审计 + 0010/0011 hash（MIG-05 · MIG-06） |
| A18 | `D-AUTH-18` | **FROZEN** | Subject Types={USER,ROLE,AGENT}；与 Provider 正交 | 词汇表断言 + 防线保持测试（AUTH-05 · SEC-09 · SEC-10） |
| A19 | `D-AUTH-19` | **FROZEN** | runtime identity = 单调整数 revision | 契约审计（AGENT-07） |
| A20 | `D-AUTH-20` | **FROZEN** | ACL 唯一键不变；改判=替换+同事务审计 | 约束定义比对 + 事务测试（SEC-08 · CACHE-03） |
| A22 | `D-AUTH-22` | **FROZEN** | Audit/Event ID = UUIDv7 | 契约断言（AUDIT-06） |
| — | `D-AUTH-24` | **FROZEN** | `D-B14-08` → **SUPERSEDED** by `D-AUTH-05`；`SC-1b` 保留；canonical 接受 / 非 canonical 拒绝 | 迁移 CHECK 实测 + `test_resource_acl_schema`（`x9.opaque` → 拒绝）+ ACL 迁移测试 |
| — | `D-AUTH-25` | **FROZEN** | Action canonical **存储形 = 小写**；归一 = NFKC → strip → casefold；存储边界精确小写 | `test_migration_vocabulary_is_the_core_vocabulary` + `test_storage_boundary_rejects_non_lowercase_spellings` + `_same_action` 单测组 |

### 17.2 DEFERRED（3）— Decision Boundary → Deferred Phase → Future Acceptance

| OQ | Decision ID | Status | Decision Boundary（**已冻结的边界**） | Deferred Phase | Future Acceptance |
|---|---|---|---|---|---|
| A03 | `D-AUTH-03` | `DEFERRED` | Agent=独立主体；User=Actor/Delegator context；执行记录须区分 Agent/Actor/Delegator；**禁止** Agent 权限自动等于 User 权限；**禁止** Agent 权威 > 委派 User 的有效权威 | **Agent Runtime**（Exit：delegation 载体经单独授权） | 越权注入测试 → DENY（AGENT-02 · AGENT-06） |
| A13 | `D-AUTH-13` | `DEFERRED` | 当前 **`No Authorization Cache`**；若未来允许，须满足 No Fail Open / Bounded TTL / Explicit Revocation Invalidation / No stale ALLOW after security-critical revoke | **Tool Runtime**（Exit：真实流量模型 + Human 授权） | 撤销后立即 DENY；无 fail-open 路径（CACHE-01 · CACHE-02） |
| A21 | `D-AUTH-21` | `DEFERRED` | Memory 与 Workflow **必须**使用同一 Canonical Authorization Model；**禁止**各自建立独立授权体系 | **Agent Runtime**（Exit：Memory/Workflow 授权动作与作用域定义并经授权） | 跨 tenant/space 记忆读写被拒（DEP-06 · DEP-07） |

### 17.3 状态语义更新（对 §1–§15 行状态列的影响）

`§1`–`§15` 行中的 `BLOCKED-OQ` 标记（**28 处**）**统一表示"曾被未裁定 OQ 阻塞"**。
**自 2026-09-23 起，22 项 OQ 已全部裁定** ⇒ 该阻塞**已解除**：
- 属 **FROZEN（19 项）** 所阻塞的行 → 阻塞解除，**转为待实施**（`PENDING`）。
- 属 **DEFERRED（3 项）** 所阻塞的行（A03 / A13 / A21 相关）→ **转为其 Deferred Phase 的前置**，见 §17.2。
- `BLOCKED-P10`（7 行）**不受本轮影响** —— P10 依赖仍然存在（`D-AUTH-15` 明确 persistence `DEFERRED TO P10`）。

> **历史测量保留**：§汇总 的 `BLOCKED-OQ = 28` 为 **2026-09-23 冻结前** 的实测值，保留作为历史证据；
> 冻结后的状态以本 §17 为准。

### 17.4 `GAP-11` 专项 —— `D-AUTH-23`（`FROZEN`）· **非 OQ**

| 项 | 内容 |
|---|---|
| Decision ID | **`D-AUTH-23`** |
| 来源 | **`GAP-11`**（Implementation Gap，**非** OQ）—— `agent_permissions.resource_scope` 为 P09 无约束自由 text |
| Status | **`FROZEN`**（2026-09-23 · Human Decision **A — Legacy Opaque**） |
| **`GAP` 状态** | **`GAP-11 = RESOLVED`** —— 由本条唯一处置；**无** schema 动作。**规范表述**：`resource_scope` = **OPAQUE TEXT** · **NOT AUTHORIZATION AUTHORITY** · `ND-A = RESOLVED` · `P09` / `0011` **unchanged** |
| 决策 | 保持 P09 原语义 **`OPAQUE TEXT`**：**不解释** · **不构成授权判定** · **不得**用于推导 `PLATFORM` / `TENANT` / `SPACE` · **不得**用于扩大 effective authorization |
| **`ND-A`** | **`RESOLVED`** = **不追加** `resource_scope <> ''` ⇒ `''` / `'   '` / 任意 opaque 值在当前 P09 结构规则下**仍然合法**（无伪语义） |
| Acceptance Criterion | 运行时引用 = 0；服务无推导路径；P09 schema 逐项相等；空 / 空白 / opaque 值**不产生 `ALLOW`** |
| Verification Method | AST 守卫 + 契约审计 + `information_schema` 比对 + 求值注入（`AGENT-RESOURCE-SCOPE-01…04`） |
| 迁移影响 | **0**（无 DDL / DML / migration；`0012_authz_enforcement` 既有规划**不变**） |
| 边界 | 任何未来规范化 / 验证 / 重新定义 ⇒ **NEW HUMAN DECISION + P09 SUPERSESSION** |
| 单列裁决 | `D-AUTH-23` **不改变** `D-AUTH-01`…`D-AUTH-22` 的任何既有语义，仅**封堵一条潜在旁路** |

---

### 17.5 `D-B14-08` 冲突裁定专项 —— `D-AUTH-24` / `D-AUTH-25`（`FROZEN`）· **非 OQ**

| 项 | 内容 |
|---|---|
| 来源 | **冲突**：`D-B14-08`（B1-4，2026-09-13 `FROZEN — A`："零新增 semantic/format contract"，`resource_permissions.action` = opaque）↔ `D-AUTH-05` + **`SC-1b`**（canonical action CHECK）。**执行级证据**：`test_resource_acl_schema` 的 `'x9.opaque'` 断言即 `D-B14-08` 的可执行编码，`SC-1b` 令其失败。 |
| Decision ID | **`D-AUTH-24`**（supersession）· **`D-AUTH-25`**（canonical 存储形） |
| Previous Decision | `D-B14-08` = `FROZEN — A`（零新增约束；opaque identifier） |
| New Decision | `D-B14-08` → **`SUPERSEDED`**，**superseded by `D-AUTH-05`**；`SC-1b` **保留**；Action canonical **存储形 = 小写** |
| Status | **`FROZEN`**（2026-09-24 · Human Decision **A + lowercase**） |
| **Supersession 关系** | **平台级 supersession = 1**（与 `D-AUTH` 命名空间内计数 0 **分开表述**） |
| Normalization | **NFKC → strip → casefold**；`_same_action` 对 stored/requested **双侧归一**；**禁止** canonical 路径 `upper()` / 大写比较 |
| Reason | `D-AUTH-05` 影响范围原文即列明 `resource_permissions.action`；`D-B14-08` 自身把词表 **defer 到 Authorization 阶段**（本阶段即该阶段）；否则 ACL 可长期存有永不匹配的 action（数据完整性 / 可审计性缺口） |
| Schema Impact | `SC-1` / `SC-1b` CHECK 取值 = **小写 canonical 形**（`0012` 已实施；0010 / 0011 / P09 **unchanged**） |
| Implementation Impact | `core/permission/vocabulary.py`（ACTIONS 小写 + casefold）· `services/authorization/permissions.py`（`_same_action` 双侧归一）· `0012` CHECK · 相关测试折叠 |
| Acceptance Impact | `ACT-01` / `ACT-02` **语义不变**；"任意 opaque 被接受"断言**移除** → canonical 接受 + 非 canonical 拒绝；存储边界新增 `READ`/`Read`/`rEaD`/`foo`/`x9.opaque` 全拒绝探针 |
| 根因（系统性） | `D-B14-08` 与 `D-AUTH-05` **分属两个决策日志且互为 0 引用** ⇒ 冻结时结构上不可发现。**已修复**：`B1-4_DECISION_LOG.md` 增补 append-only supersession 标记 |
| 边界 | 仅 `resource_permissions.action` / `permissions.action` 的词表形；**不**改变 `SUBJECT_TYPES` / `STORED_SCOPES` / `RISK_LEVELS` / `EFFECTS` 的大小写 |

---

## 汇总

> **本表数字为 2026-09-23 由命令实测**（`grep -cE` 逐分类统计，**非估算**）。
> **重算轮次**：`GAP-11` / `D-AUTH-23` 轮（本轮）⇒ 新增 §5 `AGENT-RESOURCE-SCOPE-01…04` 4 行；`TOOL-07` 拆分后**行数不变**。
> **ID 前缀映射**：§12 SECURITY 行前缀为 `SEC-` · §13 DEPENDENCY 为 `DEP-` · §14 MIGRATION 为 `MIG-` · §15 REGRESSION 为 `REG-` ·
> §5 新增系列前缀为 **`AGENT-RESOURCE-SCOPE-`**（独立于 `AGENT-` 系列，**不**与之合并计数）。
> **注意**：部分行为**混合状态**（如 `**ASSET**（3 层）/ BLOCKED-OQ(A06)`），会同时计入多列，
> 故 ASSET+PENDING+OQ+P10 之和（**106**）**大于**总行数（**99**）。

| 分类 | 行数 | ASSET | PENDING | BLOCKED-OQ | BLOCKED-P10 |
|---|---|---|---|---|---|
| ARCH | 6 | 4 | 0 | 2 | 0 |
| AUTH | 9 | 0 | 4 | 4 | 1 |
| TENANT | 6 | 3 | 3 | 0 | 0 |
| SCOPE | 5 | 3 | 0 | 3 | 0 |
| AGENT | 7 | 1 | 2 | 3 | 1 |
| **AGENT-RESOURCE-SCOPE**（新增） | **4** | **2** | **2** | **0** | **0** |
| TOOL | 7 | 3 | 2 | 3 | 0 |
| POLICY | 5 | 0 | 1 | 4 | 0 |
| RISK | 4 | 1 | 3 | 1 | 0 |
| APPROVAL | 5 | 1 | 0 | 4 | 0 |
| CACHE | 5 | 1 | 4 | 1 | 0 |
| AUDIT | 6 | 1 | 2 | 1 | 3 |
| SECURITY（`SEC-`） | 10 | 6 | 1 | 2 | 1 |
| DEPENDENCY（`DEP-`） | 7 | 6 | 2 | 0 | 1 |
| MIGRATION（`MIG-`） | 7 | 7 | 0 | 0 | 0 |
| REGRESSION（`REG-`） | 6 | 5 | 1 | 0 | 0 |
| **合计** | **99** | **44** | **27** | **28** | **7** |

> **历史值对照**（`GAP-11` 轮之前）：行数 **95** · ASSET **42** · PENDING **25** · BLOCKED-OQ **28** · BLOCKED-P10 **7**。
> 变化：行数 **+4**（`AGENT-RESOURCE-SCOPE-01…04`）· ASSET **+2**（`-01` `-03` 当前已成立）· PENDING **+2**（`-02` `-04` 待实施）·
> BLOCKED-OQ / BLOCKED-P10 **不变**。⚠ `TOOL-07` 为**改写**（非新增），故 TOOL 行数仍为 7。
>
> `ASSET` = 既有冻结资产已具备（**无需新建，只需沿用**）；
> `BLOCKED-OQ` 标记共 **28** 处（**历史测量，冻结前**），映射到 §18 的 **22 项 OQ**；
> 冻结后状态见 **§17 / §17.4**；
> `BLOCKED-P10` 共 **7** 行（审计持久化链路，**不受本轮回影响**）。

**结论**：本矩阵**不构成验收结论**。
在 22 项 OQ 全部裁定且 OQ-A15 的 P10 依赖解除之前，不得宣告 Authorization 实施完成。

---

**END OF AUTHORIZATION ACCEPTANCE MATRIX（2026-09-23）**
