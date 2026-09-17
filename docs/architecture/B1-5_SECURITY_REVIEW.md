# B1-5 — Security Review（PREP）

Status: **PREP / AUDIT — 只读评审，不修改任何对象**
范围：`tools` / `tool_versions` / `tool_permissions`（P07 Tool 域）
配套：`B1-5_SCHEMA_DESIGN.md` · `B1-5_DEPENDENCY.md`

> **前提声明（不得弱化）**：B1-4 的 Resource ACL 只是 **object-side ACL foundation**，**不等于**已经存在 authorization evaluator。
> B1-5 同样**不实现**授权求值。任何"顺带把授权做进去"的倾向均属越界。

---

## 1. 审计矩阵

| # | 维度 | 判定 | 说明 |
|---|---|---|---|
| S1 | **Tenant isolation** | **PASS** | **D-B15-02 = FROZEN — A**：`tenant_id NULL → tenants.id RESTRICT` ⇒ 租户级 Tool 无法指向不存在的租户，删租户被阻塞；平台级 `NULL` 语义保留。**不启用 RLS** ⇒ 行级隔离仍依赖应用/授权层（与 B1-4 同口径） |
| S2 | **Space isolation** | **PASS（N/A）** | Tool 域**无 `space_id`** ⇒ 不产生跨空间泄漏面。**注意**：这意味着 Tool **不**按空间隔离，属冻结设计（`CORE` §1.4 无 space 列） |
| S3 | **Identity boundary** | **PASS** | 不引入新主体表；`tools` 无 `owner_id`，不产生新的主体引用面 |
| S4 | **Role / Permission boundary** | **PASS** | `tool_permissions.permission_id → permissions.id`（P04 已存在，FK RESTRICT/CASCADE 明确）；**B1-5 不做角色/权限判定** |
| S5 | **Resource ACL boundary** | **PASS** | B1-5 不写 `resource_permissions`；`acl_subject_types` 仍 0 rows ⇒ ACL 行物理不可写入（B1-4 冻结事实延续） |
| S6 | **Cross-tenant FK** | **PASS** | **D-B15-02 = FROZEN — A**：FK 存在 + `ON DELETE RESTRICT`；平台级 `NULL` 放行（无引用）。B0 文档（ER / CORE / DEPENDENCY / CONSTRAINT）已同步 |
| S7 | **Delete semantics** | **PASS** | `tools → tool_versions` CASCADE（版本快照）· `tools → tool_permissions` CASCADE（配置行）· `tool_permissions.version_id/permission_id` CASCADE —— 全部在 `CORE:11.1` **CASCADE 白名单**内 ✅；`tools` 本身生命周期 = **disable**（`enabled=false`），非删除 |
| S8 | **Privilege escalation** | **PASS（本阶段无判定逻辑）** | 无 grant/revoke 实现、无角色解析、无 deny 解析 ⇒ 无新增提权面。版本不可变 trigger 只锁"快照完整性" |
| S9 | **Future authorization engine interaction** | **OPEN（契约只读）** | `tool_permissions` 将成为未来 Policy/Authorization 层的输入（"调用 Tool 需要什么权限"）。本阶段**只存不解释**；`effect`(`allow`/`deny`) 语义与 `DENY > ALLOW` 组合规则**留给 Authorization Layer** |
| S10 | **RLS** | **PASS（未启用）** | 不创建 POLICY、不 `ENABLE ROW LEVEL SECURITY`（与 B1-4 一致） |
| S11 | **Sensitive data** | **WARN** | `input_schema` / `output_schema` / `retry_policy` / `conditions` 为 **JSONB 配置位**。**纪律**：不得存放凭据/密钥/token。**DB 层无强制**（属应用层约定 + 未来审计） |
| S12 | **Seed / bootstrap security** | **PASS** | B1-5 **零 seed**（`SCHEMA_DEPENDENCY:193`）⇒ 不产生"带病入库"的初始数据，也不存在 seed 绕过 trigger 的窗口 |

---

## 2. Trigger 安全边界（强制声明）

`tg_version_immutable` 的职责**仅**为：

```
status='published' 的行禁止 UPDATE / DELETE   ← 结构性不变式
```

**不承担**（明文禁止）：
- ❌ authorization evaluation
- ❌ role resolution
- ❌ deny resolution
- ❌ ABAC / conditions 解释
- ❌ 任何 Domain / 行业业务规则

与 B1-4 的边界声明同构（`tg_resources_tenant_space_consistency` = structural integrity only；`tg_acl_subject_types_protect` = registry governance only）。

---

## 3. 与 B1-4 安全结论的一致性

| B1-4 结论 | B1-5 是否改变 |
|---|---|
| 不启用 RLS | **不变** ✅ |
| 不实现 Authorization Layer | **不变** ✅ |
| `acl_subject_types` 0 rows ⇒ ACL 不可写入 | **不变**（B1-5 不 seed） ✅ |
| `conditions` = storage-only | **不变**（`tool_permissions.conditions` 同口径） ✅ |
| DENY > ALLOW 留给 Authorization Layer | **不变** ✅ |
| G/H/I/J 不实施 | **不变**（仍 P09 后） ✅ |

---

## 4. 风险汇总

| 级别 | 项 | 处置 |
|---|---|---|
| ~~**RISK**~~ | ~~S1 / S6 —— `tools.tenant_id` 的 FK 与 tenant 隔离口径未定~~ | ✅ **CLOSED** —— D-B15-02 = FROZEN — A（`→ tenants.id RESTRICT`；B0 四处已同步） |
| **WARN** | S11 —— JSONB 配置位无 DB 层敏感数据护栏 | 登记纪律；如需强制需另案（不在 B1-5） |
| **WARN** | S9 —— 未来授权层契约未冻结 | 属后续阶段，B1-5 只保证"存得住、不解释"；**D-B15-09 = FROZEN — A** 已明确 `handler_ref` 仅文本引用 |
| **WARN** | S11 关联 —— `tool_versions.status` 取值域无 CK ⇒ 不变式**仅对字面 `'published'` 生效** | ⚠️ **已裁定（D-B15-04 = FROZEN — A）**：Human 明确选择「最小约束」策略；**该风险被有意接受** |
| **PASS** | 其余 9 维度 | — |

**BLOCKER = 0**（本阶段无实现，风险均为设计层待裁定）

---

## 5. 结论

```
B1-5 SECURITY REVIEW = PREP DRAFT
BLOCKER = 0 · RISK = 0 · WARN = 2（S11 JSONB 配置位 · S9/S11 关联的 status 最小约束策略）
```

B1-5 不引入新的授权语义、不启用 RLS、不产生 seed 窗口。原唯一 RISK（`tools.tenant_id` 隔离口径）**已由 D-B15-02 = FROZEN — A 关闭**。
