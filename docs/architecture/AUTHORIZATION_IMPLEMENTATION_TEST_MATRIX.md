# AUTHORIZATION / ACL / POLICY — IMPLEMENTATION TEST MATRIX

| 字段 | 内容 |
|---|---|
| **阶段** | `STAGE 2 — IMPLEMENTATION CONTRACT PREP` |
| **性质** | `TEST MATRIX`（**未编写任何测试代码**） |
| **日期** | 2026-09-23 |
| **基线** | HEAD `eb6d4cb…` · Alembic head `0011_p09_agent_tool_permission` |
| **配套** | [`AUTHORIZATION_IMPLEMENTATION_CONTRACT.md`](./AUTHORIZATION_IMPLEMENTATION_CONTRACT.md) · [`AUTHORIZATION_SCHEMA_IMPACT.md`](./AUTHORIZATION_SCHEMA_IMPACT.md) |
| **决策 registry** | `D-AUTH` total **23** = `FROZEN` **20** + `DEFERRED` **3** + `SUPERSEDED` **0**（`OQ` 22 = 19 + 3；+ 非 OQ `D-AUTH-23` / `GAP-11`） |
| **实施授权** | **NOT AUTHORIZED** |
| **决策 registry** | `D-AUTH` total **25** = `FROZEN` **22** + `DEFERRED` **3** + `SUPERSEDED` **0**（含 `D-AUTH-24`：`D-B14-08` → SUPERSEDED by `D-AUTH-05`；`D-AUTH-25`：Action canonical 形 = 小写） |

> **本矩阵定义"实施阶段必须写哪些测试"**，不包含测试实现。
> 现有基线（上轮实测）：`tests/architecture` **14 passed** · 全量回归 **342 passed / 0 failed / 0 error** ·
> 负向样例 **14/14**。实施后**必须不下降**。

---

## 0. 命名对齐（合同 ID ↔ 本矩阵 ID）

`AUTHORIZATION_IMPLEMENTATION_CONTRACT.md` §3 的 Traceability 使用了**简写** Test ID；本矩阵为**权威展开**：

| 合同简写 | 本矩阵权威 ID |
|---|---|
| `T-COMBO` | `T-COMB-01`…`T-COMB-09` |
| `T-AGENT-01` / `T-AGENT-02` | `T-SUBJ-03` / `T-SUBJ-05`（Agent/Boundary 并入 SUBJ 系列） |
| `T-ARCH-04` | `T-ARCH-04`（一致） |
| 其余 | 与本矩阵同名 |

---

## 1. 测试分类（§29）

| 类别 | 目录 | 数量（计划） | 说明 |
|---|---|---|---|
| Unit | `tests/unit/` | 22 | 纯值对象 / 枚举 / 合并算法 |
| Contract | `tests/contract/` | 8 | Decision / Context / Request 契约形状 |
| Integration | `tests/integration/` | 12 | 经真实 PG 的 RBAC/ACL/Policy 求值 |
| Architecture | `tests/architecture/` | 5 | 分层与越界守卫 |
| Security | `tests/security/` | 12 | §30 矩阵 |
| Migration | `tests/integration/` | 5 | 4.1/4.2 计划的 upgrade/downgrade |
| Regression | 全量 | 1 | 基线不下降 |
| **`GAP-11` 专项（`D-AUTH-23`）** | `tests/architecture/` + `tests/security/` | **4** | `AGENT-RESOURCE-SCOPE-01…04`（见 §5.1） |
| **合计** | — | **69** | 65 + `GAP-11` 专项 4 |

---

## 2. UNIT（22）

| ID | 目标 | 断言 | 依据 |
|---|---|---|---|
| T-SUBJ-01 | `SubjectType` 枚举 | 仅 `USER`/`ROLE`/`AGENT`；无其它值可构造 | `D-AUTH-18` |
| T-SUBJ-02 | 词汇正交 | `SubjectType` 与 `IDENTITY_KINDS`/`providers` **不共用枚举** | `D-AUTH-18` |
| T-SUBJ-03 | Agent 可作主体 | `SubjectRef(AGENT, …)` 可构造并通过校验 | `D-AUTH-02` |
| T-SUBJ-04 | 主体不可伪造 | 缺 `subject_type` 或缺 `subject_id` ⇒ 拒绝 | `D-AUTH-12` |
| T-SUBJ-05 | base delegation context | `actor_id` / `delegator_id` / agent 三者**可区分**且可传递 | `D-AUTH-03` |
| T-SUBJ-06 | Agent 不自动继承 User | 构造 Agent 主体时**不**注入 owner 的 role_keys | `D-AUTH-03` |
| T-RES-01 | `ResourceRef` 必填校验 | `type`/`id` 缺一即 `ValueError` | `D-AUTH-04` |
| T-RES-02 | owner 仅 USER | owner 字段只接受 user 型标识 | `D-AUTH-04` |
| T-RES-03 | 无 parent | `ResourceRef` **无** `parent_id` 字段 | `D-AUTH-04`/`D-AUTH-08` |
| T-RES-04 | classification 四档 | 仅 `PUBLIC/INTERNAL/CONFIDENTIAL/HIGHLY_CONFIDENTIAL` | DB CHECK |
| T-ACT-01 | 12 项 canonical | 集合恰好为 12 项且与 `D-AUTH-05` 完全一致 | `D-AUTH-05` |
| T-ACT-02 | 大小写归一 | `read`/`Read`/`READ` 归一为**小写** `read`（`D-AUTH-25`） | `D-AUTH-05` · `25` |
| T-ACT-03 | NFKC 归一 | 同形字符变体被归一后比较 | `D-AUTH-05` |
| T-ACT-04 | 非 canonical 拒绝 | `"delete_all"` ⇒ 校验失败 | `D-AUTH-05` |
| T-ACT-05 | 无第二套词表 | 不存在并行的 action 枚举 | `D-AUTH-05` |
| T-SCOPE-01 | 3 层 stored scope | 仅 `PLATFORM`/`TENANT`/`SPACE` | `D-AUTH-06` |
| T-SCOPE-02 | `SELF` 非 scope | `SELF` 出现在 predicate 而非 scope 枚举 | `D-AUTH-06` |
| T-SCOPE-03 | `RESOURCE` 非 scope | 同上 | `D-AUTH-06` |
| T-SCOPE-04 | `is_in_scope` 语义 | tenant 不等 ⇒ False；space 有值不等 ⇒ False | 既有契约 |
| T-SCOPE-05 | 作用域只收紧 | 子作用域**不能**扩大父作用域授权 | `D-AUTH-08` |
| T-INHERIT-01 | Explicit & Downward | 继承仅 `PLATFORM→TENANT→SPACE→Resource Context` | `D-AUTH-08` |
| T-INHERIT-02 | 无隐式 parent 继承 | 构造"资源层级"不产生任何授权继承 | `D-AUTH-08` |
| T-INHERIT-03 | explicit deny 参与计算 | 任一层 deny 进入最终合并 | `D-AUTH-08` |
| T-DEC-01 | 三值枚举 | 恰好 `ALLOW`/`DENY`/`REQUIRES_APPROVAL` | `D-AUTH-14` |
| T-DEC-02 | `REQUIRES_APPROVAL` 非执行许可 | `allowed` 派生属性 = False | `D-AUTH-14` |
| T-DEC-03 | Decision 字段齐备 | subject/delegator/action/resource/scope/context/effect/reason/policy_version | §22 · `D-AUTH-14` |
| T-DEC-04 | 向后兼容 | `allowed` 为派生只读属性 | 契约 |
| T-DEC-05 | reason 分类 | `EXPLICIT_DENIAL` 与 `INTERNAL_FAILURE` 可分辨 | `D-AUTH-12` |
| T-RISK-01 | 四档枚举 | 仅 `LOW/MEDIUM/HIGH/CRITICAL` | `D-AUTH-10` |
| T-RISK-02 | score 为内部信号 | `score()` **不**出现在对外契约面 | `D-AUTH-10` |
| T-RISK-03 | Risk ≠ Permission | 类型不可互换 | `D-AUTH-10` |
| T-RISK-04 | Risk ≠ Decision | 类型不可互换 | `D-AUTH-10` |
| T-VER-01 | 单调整数 revision | 版本比较按 int，非字符串 | `D-AUTH-19` |
| T-VER-02 | 不可变引用 | 版本以 `agent_versions.id` 引用 | `D-AUTH-19` |
| T-VER-03 | display 不参与判定 | 字符串版本不进入授权逻辑 | `D-AUTH-19` |
| T-CACHE-01 | 零缓存依赖 | `AuthorizationService` 无 cache 参数/依赖 | `D-AUTH-13` |

> 计数：SUBJ 6 + RES 4 + ACT 5 + SCOPE 5 + INHERIT 3 + DEC 5 + RISK 4 + VER 3 + CACHE 1 = **36**（unit 计划 22，其余归入 contract/integration；实施轮按实际文件归属调整）。

## 3. CONTRACT（8）

| ID | 目标 | 断言 |
|---|---|---|
| T-CT-01 | `AuthorizationRequest` 形状 | 四字段齐备且不可变 |
| T-CT-02 | `AuthorizationContext` 形状 | tenant/space/request_id/actor/delegator/environment |
| T-CT-03 | `AuthorizationService` 为 Protocol | 可被 `isinstance` 运行时检查；无实现绑定 |
| T-CT-04 | `Decision` 不可变 | `frozen=True` |
| T-CT-05 | `Authorizer` 单入口 | 公开求值入口**唯一** |
| T-CT-06 | 无 I/O 契约 | `core/*` 契约模块不 import DB/驱动 |
| T-CT-07 | `ToolContext` 携带决策 | 扩展后必须含决策参数 |
| T-CT-08 | `AuditEvent` 字段齐备 | 12 类字段（`D-AUTH-15`） |

## 4. INTEGRATION（12）

| ID | 目标 | 断言 | 依据 |
|---|---|---|---|
| T-INT-01 | RBAC 基线求值 | 角色授予 → allow | `D-AUTH-01` |
| T-INT-02 | ACL 资源求值 | 资源 ACL → allow | `D-AUTH-01` |
| T-INT-03 | Policy 条件求值 | 条件满足 → allow | `D-AUTH-01` |
| T-INT-04 | ACL deny 覆盖 RBAC allow | 结果 **DENY** | `D-AUTH-07` |
| T-INT-05 | 多角色任一 deny | 结果 **DENY** | **继承 `R2-D-14`** |
| T-INT-06 | 无任何 allow | **DEFAULT DENY** | `D-AUTH-12` |
| T-INT-07 | ACL 改判 = 行替换 | UPDATE 后唯一行，允许无并存 | `D-AUTH-20` |
| T-INT-08 | ACL 改判同事务审计 | 审计与改判同事务（原子） | `D-AUTH-20` |
| T-INT-09 | `expires_at` 过期 | 过期行不参与判定 | `D-AUTH-12` |
| T-INT-10 | 角色归档 | deny 行失效、allow 行保留（可追溯） | `D-AUTH-08` |
| T-INT-11 | tenant 边界 | 跨 tenant ⇒ DENY | `D-AUTH-06` |
| T-INT-12 | Agent 声明-实际一致性 | `tool_permissions` 四元组与实际访问一致 | `D-AUTH-09` |

## 5. ARCHITECTURE（§31，5）

| ID | 断言 | 现状基线 |
|---|---|---|
| T-ARCH-01 | `core → domains` = 0 | ✅ 既有守卫 |
| T-ARCH-02 | `agent → {Database, Infrastructure, services, apps}` = 0 | ✅ 既有守卫（G-3） |
| T-ARCH-03 | `core → {sqlalchemy, psycopg, services}` = 0 | ✅ 既有守卫（G-1/G-2） |
| T-ARCH-04 | 授权实现落 `services/`，契约落 `core/`，**无循环依赖** | 待实施 |
| T-ARCH-05 | 未新增第二套授权契约包 | 待实施 |

### 5.1 `GAP-11` 专项测试（**`D-AUTH-23`** · `agent_permissions.resource_scope` = Legacy Opaque）

> 目的：**防止未来 Runtime 把 P09 的 opaque 字段偷渡为授权权威**。
> 依据 **`D-AUTH-23`（`FROZEN`）**；契约落点 `AUTHORIZATION_IMPLEMENTATION_CONTRACT.md` **§19.1**。
> **状态**：**`GAP-11 = RESOLVED`**（2026-09-23 · Human Decision A — Legacy Opaque）。
> **语义**：`agent_permissions.resource_scope` = **OPAQUE TEXT** — **NOT AUTHORIZATION AUTHORITY**（不构成授权权威）；
> `ND-A = RESOLVED`（**不追加** `<> ''`）· `P09` / `0011` **unchanged**。
> **NONE 会触碰 P09 schema** —— 本组测试**不含**任何 DDL / DML / migration。

| ID | 断言 | 目录 | 依据 | 现状 |
|---|---|---|---|---|
| `AGENT-RESOURCE-SCOPE-01` | 运行时 `.py` 对 `agent_permissions.resource_scope` 的 **code 级引用 == 0**（**AST 判定**：仅统计 string literal / identifier / attribute / keyword；**docstring 说明性提及 = 声明而非引用**，不计） | `tests/architecture/test_agent_resource_scope_opaque.py` | `D-AUTH-23` §6 | **✅ 当前已成立**（AST 守卫实测 0；豁免面：0011 迁移源 · P09 集成测试 · `repository.py` 模块 docstring 对禁令自身的声明） |
| `AGENT-RESOURCE-SCOPE-02` | `resource_scope` **不是** canonical authorization authority：`AuthorizationService` 路径**不读取**该字段，且**不**由其推导 `PLATFORM` / `TENANT` / `SPACE` | `tests/architecture/test_agent_resource_scope_opaque.py` | `D-AUTH-23` §1/§5 | **✅ 当前已成立**（agent grant 查询仅选 `permission_id` / `tool_id` / `effect`） |
| `AGENT-RESOURCE-SCOPE-03` | P09 schema **未变**：`0011` sha256 = `cdaf8383630335db…`；`agent_permissions` 列集 / 约束集 / 索引集与 0011 基线**逐项相等** | `tests/integration/` | `D-AUTH-23` §2 | **✅ 当前已成立**（0011 未变） |
| `AGENT-RESOURCE-SCOPE-04` | `''` / `'   '` / 任意 opaque 取值在授权求值中**均不产生 `ALLOW`**（`resource_scope` 既不禁也不授 ⇒ 结果只由其**他**权威来源决定） | `tests/security/test_authorization_security.py`（3 测：不授 / 不改真实 allow / 不软化真实 deny） | `D-AUTH-23` §1/§7 · `D-AUTH-12` | **✅ 当前已成立**（求值器已实施；与 ACL e2e 不同，本组不依赖 `acl_subject_types` seed） |

**豁免面（允许的引用，`AGENT-RESOURCE-SCOPE-01` 不计入违规）**：

```text
migrations_alembic/versions/0011_p09_agent_tool_permission.py   （migration source）
tests/integration/test_agent_tool_permission_schema.py          （P09 integration test）
docs/architecture/**                                            （design / contract）
docs/**                                                         （documentation）
```


## 6. SECURITY（§30，12）

| ID | 场景 | 期望 | 依据 |
|---|---|---|---|
| T-SEC-01 | User A → Tenant B 资源 | **DENY** | `D-AUTH-06` |
| T-SEC-02 | Agent → 未授权资源 | **DENY** | `D-AUTH-02` |
| T-SEC-03 | Role allow + ACL deny | **DENY** | `D-AUTH-07` |
| T-SEC-04 | Policy deny + RBAC allow | **DENY** | `D-AUTH-07` |
| T-SEC-05 | Authorization service 不可用 | **DENY** | `D-AUTH-12` |
| T-SEC-06 | Expired grant | **DENY** | `D-AUTH-12` |
| T-SEC-07 | Revoked grant | **DENY** | `D-AUTH-12` |
| T-SEC-08 | Tool 直连 DB 尝试 | **FORBIDDEN**（静态守卫 + 运行时） | `D-AUTH-09` |
| T-SEC-09 | Agent 直连 infrastructure | **FORBIDDEN** | `D-AUTH-16` |
| T-SEC-10 | Agent 权限超越委派 User | **DENY** | `D-AUTH-03` |
| T-SEC-11 | 伪造 subject | **RAISE / DENY** | `D-AUTH-18`（沿用 `enforce_acl_subject_exists`） |
| T-SEC-12 | Action 拼写变体绕过 | **DENY** | `D-AUTH-05` |

## 7. MIGRATION（5）

| ID | 断言 |
|---|---|
| T-MIG-01 | `0012_authz_enforcement` 的 `revision` 长度 ≤ 32 且 `filename == revision` |
| T-MIG-02 | `down_revision == "0011_p09_agent_tool_permission"`；升级后 **单头** |
| T-MIG-03 | `upgrade` 后 3 条 CHECK + 3 个新列存在；`downgrade` 后完全还原 |
| T-MIG-04 | `0001`–`0011` 文件 sha256 **未变**（`0010`=`6d9907237f80e9da…` · `0011`=`cdaf8383630335db…`） |
| T-MIG-05 | 预检：存量 action 越界值 = 0（否则 migration 主动 RAISE） |

## 8. REGRESSION（1）

| ID | 断言 |
|---|---|
| T-REG-01 | 全量回归 **≥ 342 passed / 0 failed / 0 error**（上轮实测基线）· 架构守卫 **≥ 14 passed** · 负向样例 **14/14** |

---

## 9. §35 Acceptance Traceability（22 OQ + `GAP-11` 专项 1 = **23** 条，无 orphan）

| D-AUTH | Test IDs | Acceptance |
|---|---|---|
| 01 | T-COMB-01…09 · T-INT-01…03 | AUTH-01 · POLICY-01 |
| 02 | T-SUBJ-03 · T-INT-12 | AGENT-01 |
| 03 | T-SUBJ-05/06 · T-SEC-10 | AGENT-02 |
| 04 | T-RES-01…04 | SCOPE-05 |
| 05 | T-ACT-01…05 · T-SEC-12 | AUTH-06 |
| 06 | T-SCOPE-01…05 · T-SEC-01 | SCOPE-01…04 |
| 07 | T-COMB-01…09 · T-INT-04/05 | POLICY-05 · SEC-06 |
| 08 | T-INHERIT-01…03 · T-INT-10 | SCOPE-05 |
| 09 | T-TOOL-01…06 · T-SEC-08 | TOOL-01 · 03 · 07 |
| 10 | T-RISK-01…04 | RISK-01…04 |
| 11 | T-APPR-01…04 | APPROVAL-01 · 03 · 04 |
| 12 | T-FAIL-01…10 · T-SEC-05/06/07 | SEC-06 |
| 13 | T-CACHE-01 | CACHE-01 |
| 14 | T-DEC-01…05 | APPROVAL-02 |
| 15 | T-AUDIT-01…06 · T-CT-08 | AUDIT-02 · 03 |
| 16 | T-ARCH-01…05 · T-SEC-09 | ARCH-02 · 05 |
| 17 | T-MIG-01…05 | MIG-05 · 06 |
| 18 | T-SUBJ-01/02 · T-SEC-11 | AUTH-05 · SEC-09 · SEC-10 |
| 19 | T-VER-01…03 | AGENT-07 |
| 20 | T-INT-07/08 · T-ACL-01…05 | SEC-08 · CACHE-03 |
| 21 | （DEFERRED）T-DEP-01（占位，Agent Runtime 阶段定义） | DEP-06 · 07 |
| 22 | T-AUDIT-05 | AUDIT-06 |
| `23`（`GAP-11`） | `AGENT-RESOURCE-SCOPE-01…04` | `AGENT-RESOURCE-SCOPE-01…04` |

**结果：22 / 22 OQ 有 Test 归属；另加 `D-AUTH-23`（`GAP-11` 专项，**非** OQ）1 条 ⇒ 合计 **23**，无 orphan。**
（`D-AUTH-23` 的 `D` 列标 `23`(`GAP-11`) 以区别于 `OQ-A01…A22` 序列。）

### 9.1 待补齐的 Test ID（实施轮定义）

以下 ID 在合同与本矩阵中被引用，但**内容在实施轮定义**（本阶段只登记归属，不写测试）：

`T-COMB-01…09`（合并算法与 truth table 逐行）· `T-APPR-01…04` · `T-TOOL-01…06` ·
`T-FAIL-01…10` · `T-AUDIT-01…06` · `T-ACL-01…05` · `T-DEP-01`

---

## 10. §30 逐项对照（用户指定的 9 个场景 → 本矩阵 ID）

| 用户指定场景 | 本矩阵 ID | 期望 |
|---|---|---|
| User A → Tenant B | T-SEC-01 | DENY |
| Agent A → unauthorized resource | T-SEC-02 | DENY |
| Role allow + ACL deny | T-SEC-03 | DENY |
| Policy deny + RBAC allow | T-SEC-04 | DENY |
| Authorization failure | T-SEC-05 | DENY |
| Expired grant | T-SEC-06 | DENY |
| Revoked grant | T-SEC-07 | DENY |
| Tool direct DB attempt | T-SEC-08 | FORBIDDEN |
| Agent direct infrastructure | T-SEC-09 | FORBIDDEN |

**覆盖：9 / 9**（另新增 T-SEC-10/11/12）。

---

**END OF AUTHORIZATION IMPLEMENTATION TEST MATRIX（2026-09-23）**
