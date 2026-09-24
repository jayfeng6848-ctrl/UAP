# AUTHORIZATION / ACL / POLICY — IMPLEMENTATION GATE REPORT

| 字段 | 内容 |
|---|---|
| **阶段** | `STAGE 2 — IMPLEMENTATION CONTRACT PREP`（终局报告） |
| **日期** | 2026-09-23 |
| **基线 HEAD** | `eb6d4cba71d4b69dc3604d860b9ab37ee8661cd6` |
| **基线 TAG** | `UAP-V0.1.7-GOVERNANCE-GATE`（→ 同一 commit） |
| **Alembic head** | `0011_p09_agent_tool_permission`（单头 · branches none · 0012+ absent） |
| **权威** | `D-AUTH-01`…`D-AUTH-25`（`PLATFORM_DECISION_LOG.md`） |

---

## 1. Frozen Decisions

```text
FROZEN   = 20   DEFERRED = 3   SUPERSEDED = 0
（22 OQ：19 FROZEN + 3 DEFERRED；另加非 OQ 的 D-AUTH-23（GAP-11 专项）与 **D-AUTH-24/25**（D-B14-08 冲突裁定）⇒ FROZEN 22；**平台级 supersession = 1**（`D-B14-08`））
```

| 状态 | ID |
|---|---|
| **FROZEN（19 OQ）** | `D-AUTH-01` `02` `04` `05` `06` `07` `08` `09` `10` `11` `12` `14` `15` `16` `17` `18` `19` `20` `22` |
| **FROZEN（`GAP-11` 专项，非 OQ）** | **`D-AUTH-23`** — `agent_permissions.resource_scope` = Legacy Opaque（`ND-A` = 不追加 `<> ''`） |
| **DEFERRED（3）** | `D-AUTH-03` → Agent Runtime · `D-AUTH-13` → Tool Runtime · `D-AUTH-21` → Agent Runtime |

**继承且未改动**：`R2-D-14`（DENY > ALLOW）· `R2-D-15`（scope-neutral）· `R4`/`PMB-1`（`effective_platform_admin`）·
ACL 主体白名单 `user | role | agent` · P09 schema。

---

## 2. Contract（摘要 → 详见 `AUTHORIZATION_IMPLEMENTATION_CONTRACT.md`）

| 域 | 冻结要点 |
|---|---|
| **Subject** | `SubjectType = USER | ROLE | AGENT`；**Authorization Subject ⊥ Identity Provider**；Agent 为独立主体；base delegation context（`actor`/`delegator`/`agent` 可区分）；**Agent 不得超越委派 User** |
| **Resource** | 7 项 canonical（type/id/tenant/space/classification/owner/lifecycle）；**owner 仅 USER**；**无 parent** |
| **Action** | 12 项 canonical；**存储形 = 小写**（NFKC → strip → casefold 归一，`D-AUTH-25`）；必须校验；**无第二套词表** |
| **Scope** | stored = `PLATFORM/TENANT/SPACE`；predicate = `RESOURCE/SELF`；Explicit & Downward |
| **RBAC** | baseline grant；`role_permissions` PK 含 effect ⇒ allow+deny 并存 |
| **ACL** | resource-specific；`UNIQUE` **不变**；改判 = 行替换 + 同事务审计；跨层 deny 优先 |
| **Policy** | contextual/conditional；**只能收紧**；`conditions` 归属 `core/policy`；`policy_version` 入决策与审计 |
| **Decision** | 单一算法：任一 deny ⇒ DENY · policy 失败 ⇒ DENY · 审批需求 ⇒ REQUIRES_APPROVAL · 否则任一 allow ⇒ ALLOW · 否则 DENY；**deterministic / order-independent / auditable** |
| **Risk** | 四档 canonical；`Risk ≠ Permission ≠ Decision`；`score` 仅内部信号 |
| **Approval** | `静态 OR 策略`（**永不做 AND**）；**审批 ≠ Permission**；**审批结果 ≠ ALLOW** |
| **Tool** | controlled execution boundary；结构化四元组；**不得直连 DB / 不得旁路** |
| **Failure** | 8 类分支全 **FAIL CLOSED**；区分 `EXPLICIT_DENIAL` vs `INTERNAL_FAILURE` |
| **Audit** | 授权审计 **≠** 工具执行审计；12 类字段；persistence → **P10** |

**Decision Truth Table**：14 行（见合同 §13.2），覆盖 RBAC/ACL/Policy × allow/deny/缺失/失败/不可用/过期/撤销/审批。

---

## 3. Component Boundaries

```text
Core            = pure contracts / value objects / pure rules        （无 I/O）
Application     = authorization decision orchestration               （services/authorization/）
Infrastructure  = persistence / adapters / external integration
```

| 组件 | 落点 | 处理 |
|---|---|---|
| `SubjectResolver` · `ResourceResolver` · `ActionResolver` · `ScopeEvaluator` | `core/` | REUSE（+EXTEND Subject/Action） |
| `PermissionResolver` · `PolicyEvaluator` · `DecisionCombiner` | `core/` 契约 + `services/` 实现 | REUSE + EXTEND |
| `AuthorizationService` | `services/authorization/` | **NEW**（`services/` 包尚不存在） |
| `AuditBoundary` | `core/audit` 契约 | EXTEND |
| `ToolGate` | `agent/tools` | EXTEND |
| `ApprovalGate` | 契约 only | NEW（persistence → Tool Runtime） |

**不新增第三个 core 契约包**（延续 `D-AUTH-16`）。

---

## 4. Dependency Graph

```text
apps/api ──▶ services/authorization ──▶ infrastructure/database ──▶ PostgreSQL
                    │                            ▲
                    │                            │ adapter（services 内定义接口）
                    ▼
              core/{permission,policy,resource,audit,identity}      （pure contracts）

agent/* ──▶ Authorization Contract + Policy Contract + Tool Contract
              ✗ agent ↛ Database    ✗ agent ↛ Infrastructure    ✗ agent ↛ services
core/*  ──▶ （无出边到 DB / services / domains）
```

**循环依赖检查**：`core` 只被依赖、不依赖上层 ⇒ **无环**；`services → core`（允许）· `services → domains`（`D-PLAT-03.a` 允许）·
**不新增** `core → services` / `agent → services` 反向边。

---

## 5. Schema Change Set

| ID | 对象 | 类别 | 依据 | P09 影响 |
|---|---|---|---|---|
| `SC-1` | `permissions.action` | MODIFY（+CHECK） | `D-AUTH-05` | 无（表属 0005） |
| `SC-1b` | `resource_permissions.action` | MODIFY（+CHECK） | `D-AUTH-05` | 无（表属 0007） |
| `SC-2` | `tool_permissions` | ADD COLUMNS（`resource_type`/`action`/`scope`+CHECK） | `D-AUTH-09` | 无（表属 **0008**，**非 P09**） |
| `SC-3` | Module 扩展 action registry | **PROPOSED ONLY** | `D-AUTH-05` | 无 |

**NO CHANGE（8 张指定表中的 6 张 + P09 四表）**：
`resource_permissions`（唯一键按 `D-AUTH-20` 不变）· `tools` · `roles` · `role_permissions` · `resources` ·
`agent_permissions`（P09 保护）· `agents` · `agent_versions` · `tool_executions`。

**明确不采用**：`resources.parent_id` · `resource_relations` · ACL unique-key redesign。

---

## 6. Migration Plan

```text
migration count = 1
filename == revision = 0012_authz_enforcement      （22 字符 ≤ 32 上限 ✓）
down_revision = 0011_p09_agent_tool_permission
内容 = SC-1 + SC-1b（CHECK） + SC-2（3 可空列 + 1 CHECK）
状态 = PLANNED · NOT CREATED（MIGRATION NOT AUTHORIZED）
```

| 约束 | 满足 |
|---|---|
| Append-only | ✅ |
| Single-head | ✅ |
| 历史 migration 零改写 | ✅（0001–0011 逐字节不动） |
| 完全可逆 | ✅（纯附加；无数据迁移/丢失） |
| 不采用默认名 `0012_authorization.py` | ✅ |

### 6.1 Rollback Plan

| 场景 | 动作 |
|---|---|
| migration 执行失败 | Alembic 单事务回滚；DB 保持 0011 |
| 已升级需回退 | `alembic downgrade 0011_p09_agent_tool_permission`（完全可逆） |
| **应用回滚（F-1）** | **严格 `/ready` 相等 + 镜像绑定 revision ⇒ 应用回滚 ≠ 仅回滚镜像**（见 `DEPLOYMENT_AND_RECOVERY.md` **F-1**） |
| 部署链 | `backup → verify → migration → rollout → /ready`（`D-PLAT-08` 注记） |

---

## 7. Test Matrix（详见 `AUTHORIZATION_IMPLEMENTATION_TEST_MATRIX.md`）

| 类别 | 计划数 | 关键内容 |
|---|---|---|
| Unit | 22（+14 归入 contract/integration） | 枚举 / 归一化 / 值对象 |
| Contract | 8 | Request/Context/Decision 形状；无 I/O |
| Integration | 12 | RBAC/ACL/Policy 真实 PG 求值；ACL 改判；过期/归档 |
| Architecture | 5 | 分层边界 + 无循环 |
| Security | 12 | §30 全部场景 |
| Migration | 5 | 0012 结构 / 可逆 / 历史零改写 |
| Regression | 1 | **≥ 342 passed / 0 failed / 0 error** · guards **≥ 14** · 负向 **14/14** |

### 7.1 Security Matrix（§30，用户指定 9 项 100% 覆盖）

| 场景 | 期望 | ID |
|---|---|---|
| User A → Tenant B | DENY | T-SEC-01 |
| Agent → unauthorized resource | DENY | T-SEC-02 |
| Role allow + ACL deny | DENY | T-SEC-03 |
| Policy deny + RBAC allow | DENY | T-SEC-04 |
| Authorization failure | DENY | T-SEC-05 |
| Expired grant | DENY | T-SEC-06 |
| Revoked grant | DENY | T-SEC-07 |
| Tool direct DB | FORBIDDEN | T-SEC-08 |
| Agent direct infrastructure | FORBIDDEN | T-SEC-09 |

（另新增 T-SEC-10 Agent 越权 / T-SEC-11 伪造 subject / T-SEC-12 action 变体）

---

## 8. Implementation Order（§32，**本轮不执行**）

```text
1  Authorization primitives      6  Decision combination
2  Subject resolution            7  Authorization service
3  Resource resolution           8  Tool integration
4  Permission resolution         9  Audit boundary
5  Policy evaluation            10  Security tests
                                11  Migration verification
                                12  Full regression
```

**前置第 0 步（隐含必需）**：建立 `services/` 包（`D-PLAT-01`；`GAP-12`）。

---

## 9. Acceptance Criteria

| 项 | 判据 |
|---|---|
| Traceability | **22 / 22 OQ 无 orphan** + **`D-AUTH-23`（`GAP-11` 专项）1 条** ⇒ 共 **23**（`D-AUTH` → Contract → Component → Test → Acceptance） |
| 架构边界 | `core ↛ {domains, services, sqlalchemy, psycopg}` = 0 · `agent ↛ {DB, infrastructure, services, apps}` = 0 |
| 无环 | 依赖图无循环 |
| 安全矩阵 | 12 / 12 通过（§30 九项 + 三项新增） |
| 合规 | `DENY > ALLOW` · `DEFAULT DENY` · `FAIL CLOSED` · 三值语义 · `REQUIRES_APPROVAL` 非执行许可 · **`resource_scope` 不构成授权权威（`D-AUTH-23`）** |
| Migration | 单头 · append-only · 历史零改写 · 完全可逆 |
| P09 | 四表 + 0011 **零变更**（含 `D-AUTH-23` 后仍为零变更） |
| 回归 | **≥ 342 passed / 0 failed / 0 error**；守卫 ≥ 14；负向 14/14 |
| 文档同步 | 受影响的架构 / 安全 / API 文档同步 |

---

## 10. Forbidden Scope（本轮与本轮之后均需遵守）

```text
本轮（CONTRACT PREP）已完成且不得越界：
  0 migration · 0 DDL · 0 DML · 0 代码 · 0 测试实现 · 0 数据库变更 · 未 commit / tag / push

实施阶段（未授权）：
  0012 创建 · DDL · DML · Runtime 实现 · Service 实现 · API 实现 · Cache 实现 ·
  Audit persistence · Approval persistence · P09 修改 · 冻结决策改写 · 新增第三契约包 ·
  第二套授权体系（Memory/Workflow 自定义）· 循环依赖
```

---

## 11. IMPLEMENTATION GAPS（记录，未修补）

| # | Gap | 处置 |
|---|---|---|
| GAP-1 | `RiskPolicy.score()` float vs 四档 | score 降为内部信号；映射表**未冻结**（待定项） |
| GAP-2 | `core/permission.Subject` 缺 subject_type/agent/tenant | 实施期 EXTEND |
| GAP-3 | `PolicyContext` 单 `actor_id` | 实施期 EXTEND（完整 delegation → Agent Runtime） |
| GAP-4 | `Decision.allowed: bool` | 实施期 EXTEND 为 `effect` |
| GAP-5 | `core/membership` 契约 vs DB 三表语义不一致 | 契约扩展 + `services/` 适配；**不改 DB** |
| GAP-6 | `AgentDescriptor.version: str` vs int | 实施期对齐（`D-AUTH-19`） |
| GAP-7 | `AuditEvent` 缺 7 字段 + uuid4 | 实施期 EXTEND；persistence → P10 |
| GAP-8 | `agent/memory` / `agent/workflow` 零授权参数 | **`D-AUTH-21` DEFERRED → Agent Runtime** |
| GAP-9 | `IDENTITY_KINDS` vs `acl_subject_types` 词汇 | 契约层分离；**不改** `acl_subject_types` |
| GAP-10 | action 无枚举 | **`SC-1`/`SC-1b`** |
| GAP-11 | `agent_permissions.resource_scope` 自由 text（**P09 表**） | ✅ **RESOLVED** —— **`D-AUTH-23`（`FROZEN`，2026-09-23）**：**OPAQUE TEXT** · **NOT AUTHORIZATION AUTHORITY**（不构成授权判定）· `ND-A = RESOLVED`（**不追加** `<> ''`）· **P09 / 0011 零变更** · 禁令见 Contract **§19.1** · 验收 `AGENT-RESOURCE-SCOPE-01…04` |
| GAP-12 | `services/` 包不存在 | 实施期**第 0 步** |
| GAP-13 | `tool_permissions` 无结构化列 | **`SC-2`** |

---

## 12. 门判定

```text
D-AUTH 22/22 OQ mapped        = PASS（+ D-AUTH-23 专项 1 ⇒ 23/23）
Contract complete             = PASS
Schema impact complete        = PASS
Migration plan complete       = PASS
P09 protected                 = PASS
Security model preserved      = PASS
Architecture boundaries preserved = PASS
Test matrix complete          = PASS
Acceptance matrix complete    = PASS
No unresolved implementation ambiguity = PASS
No hidden scope               = PASS
No implementation performed   = PASS
GAP-11 resolved（D-AUTH-23）  = PASS
```

```text
IMPLEMENTATION CONTRACT = PASSED
IMPLEMENTATION          = NOT AUTHORIZED
MIGRATION               = NOT AUTHORIZED
COMMIT / TAG / PUSH     = NOT AUTHORIZED
```

**放行条件**：需 Human 另行签发 **`IMPLEMENTATION AUTHORIZATION`**。
`IMPLEMENTATION CONTRACT = PASSED` **不等于** `IMPLEMENTATION AUTHORIZED`。

---

**END OF AUTHORIZATION IMPLEMENTATION GATE REPORT（2026-09-23）**
**END OF AUTHORIZATION IMPLEMENTATION GATE REPORT（`GAP-11` 专项 · `D-AUTH-23` 同步：`GAP-11 = RESOLVED`；`D-AUTH` 共 23 条 = 20 `FROZEN` + 3 `DEFERRED`，2026-09-23）**
