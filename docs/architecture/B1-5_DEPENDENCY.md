# B1-5 — Dependency Analysis（PREP）

Status: **PREP / DESIGN — 不创建任何对象**
配套：`B1-5_SCOPE.md` · `B1-5_SCHEMA_DESIGN.md` · `STEP1B_SCHEMA_DEPENDENCY.md`

> 本文件不构成冻结。边界冲突一律登记 `B1-5_DECISION_LOG.md`，**不在 PREP 阶段为"让数字一致"而修改 schema 设计**。

---

## 1. 全局阶段链（已交付 → B1-5）

```
B1-0 (0001,0002 基建)  ─→  B1-1 (0003 identity)
                              │
                              ▼
                          B1-2 (0004 tenant/space + membership 骨架)
                              │
                              ▼
                          B1-3 (0005 authorization, 0006 bootstrap state)
                              │
                              ▼
                          B1-4 (0007 resource/ACL)   ← 已封存
                              │
                              ▼
                       ★ B1-5 (P07 Tool)  ← 本阶段
```

**B1-5 与父基线的 git 关系**：
```
B1-4 Commit = e9766fbe8b13294d8a6cdfbff640f14d8e57a68f
B1-4 Tag    = UAP-V0.1.4-B1-4-RESOURCE-ACL
HEAD        = e9766fb（B1-5 起点）
```

---

## 2. B1-5 内部对象依赖（拓扑）

```
tenants (P03, 已存在)
   │  〔仅当 D-B15-02 裁定加 FK〕
   ▼
tools  ◀── ROOT（除 tenant 外无入边）
   │
   ├──────────────▶ tool_versions      (tool_id → tools.id, CASCADE)
   │                     │
   └──────────────▶ tool_permissions   (tool_id → tools.id, CASCADE)
                         │  version_id NULL → tool_versions.id, CASCADE
                         │
permissions (P04, 已存在)
   └──────────────▶ tool_permissions   (permission_id → permissions.id, CASCADE)
```

**创建顺序（唯一合法拓扑序）**：
```
1. tools
2. tool_versions          （依赖 tools）
3. tool_permissions       （依赖 tools + tool_versions + permissions）
4. function enforce_tool_versions_immutable()
5. triggers（tools.set_updated_at, tool_versions.immutable）
```

---

## 3. FK 清单（预计 5 条）

| # | FK | 目标 | 删除规则 | 依据 | 状态 |
|---|---|---|---|---|---|
| 1 | `tools.tenant_id` | `tenants.id` | **RESTRICT** | 历史冲突见 C-1；**D-B15-02 = FROZEN — A**（2026-09-14）：`tenant_id NULL → tenants.id ON DELETE RESTRICT`；B0 四处已同步 | ✅ **FROZEN** |
| 2 | `tool_versions.tool_id` | `tools.id` | **CASCADE**（NN） | `CONSTRAINT_MATRIX:230` · `CORE:11.1` 白名单"版本快照" | ✅ 冻结 |
| 3 | `tool_permissions.tool_id` | `tools.id` | **CASCADE**（NN） | `CONSTRAINT_MATRIX:240` · `CORE:11.1` 白名单"配置行" | ✅ 冻结 |
| 4 | `tool_permissions.version_id` | `tool_versions.id` | **CASCADE**（NULL 允许） | `CONSTRAINT_MATRIX:240` | ✅ 冻结 |
| 5 | `tool_permissions.permission_id` | `permissions.id` | **CASCADE**（NN） | `CONSTRAINT_MATRIX:240` | ✅ 冻结 |

> `tool_executions` 的 4 条 FK（含 `agent_id → agents.id`）**不在 B1-5**（属 P09）。

---

## 4. Forward Dependency 检查

| 检查项 | 结果 |
|---|---|
| 引用 `agents` / `agent_versions` / `agent_permissions` | **0** ✅ |
| 引用 `ai_providers` / `ai_models` / `ai_routes` / `ai_policies` / `ai_request_logs` | **0** ✅ |
| 引用 `events` / `audit_logs` | **0** ✅ |
| 引用 `tool_executions` | **0** ✅（该表属 P09） |
| 引用不存在的表 | **0** ✅ |
| 需要"先建表后补 FK"绕道 | **不需要** ✅ |

**结论：B1-5 无前向依赖（no forward dependency）。**

---

## 5. 循环 FK 检查

```
tools → tool_versions → tool_permissions → tools   ?
```
`tool_permissions.tool_id → tools.id` 与 `tools → tool_versions` 均为**单向出边**；`tool_permissions → tool_versions` 亦单向。

**结论：B1-5 三表构成有向无环图（DAG），无循环 FK，无需 `DEFERRABLE`。** ✅

> 对照：P09 的 `agents ↔ agent_versions` 是真循环（`SCHEMA_DEPENDENCY` §4.1），B1-5 **不涉及**。

---

## 6. 既有对象复用（不重建）

| 对象 | 来源 | B1-5 动作 |
|---|---|---|
| `uap_uuid_v7()` | `0003` / P00 | **复用**（PK 默认值），**不重建** |
| `set_updated_at()` | `0003` / P00 | **复用**（`tools` 的 `updated_at`），**不重建** |
| `permissions.id` | `0005` / P04 | **只读引用**（FK 目标） |
| `tenants.id` | `0004` / P03 | **只读引用**（仅当 D-B15-02 加 FK） |

---

## 7. 对下游 phase 的契约（只记录，不实现）

| 下游 | 依赖 B1-5 的什么 | phase |
|---|---|---|
| `agent_permissions.tool_id → tools.id` | `tools` 表存在 | P09 |
| `tool_executions.tool_id/tool_version_id` | `tools` / `tool_versions` 存在（RESTRICT） | P09 |
| Agent 调用链 `Agent → Policy → Tool → Service → DB` | `tools` / `tool_versions` / `tool_permissions` 就位 | P09+ |

> 这些是**下游对 B1-5 的依赖**，**不是** B1-5 对下游的依赖 ⇒ 不构成 forward dependency。

---

## 8. Core / Domain 依赖检查

| 检查 | 结果 |
|---|---|
| `core/*` → `domains/*` | **0** ✅ |
| `core/*` 引入 `agent` / `intelligence` / `apps` | **0** ✅ |
| B1-5 计划对象触及 Domain 表 | **0** ✅ |
| B1-5 计划中含行业词（restaurant/company/family/…） | **0** ✅ |
| `Space.kind` 被写成 core 常量 | **不适用**（Tool 域不读 kind） |

---

## 9. 边界冲突登记（域内不一致）

| # | 冲突 | 位置 A | 位置 B | 处置 |
|---|---|---|---|---|
| **C-1** | `tools.tenant_id` 是否 FK | *（历史引述，未篡改）* `SCHEMA_DEPENDENCY:51` FK 列 = `—` + 「无实际 FK 强制」；`CONSTRAINT_MATRIX` tools 段**无 FK 行** | *（历史引述）* `ER_MODEL:276` `tenant_id FK`（唯一支持来源） | ✅ **已解决 — D-B15-02 = FROZEN — A**：采用 FK + RESTRICT；**B0 四处当前有效口径已同步** |
| **C-2** | immutable trigger 命名 | `TRIGGER_INVENTORY:164` 逐表命名 `tg_agent_versions_immutable` / `tg_tool_versions_immutable`（**原文引述，未修改 B0**） | `SCHEMA_DEPENDENCY:240` 统一名 **`tg_version_immutable`** | ✅ **已解决 — D-B15-03 = FROZEN**：B1-5 采用 `tg_version_immutable`；**残留项**：`TRIGGER_INVENTORY:164` 的逐表命名需同步修订（**B0 文档，属另案，本轮未改**） |
| **C-3** | `tool_versions.status` 取值域 | *（历史引述，未篡改）* 未定义（`CONSTRAINT_MATRIX` / `CORE` 该表**均无 CK**；全库 12 处 `status IN (...)` 先例不含本表） | `STEP1A_DESIGN_REPORT:67` 仅说"published 后不可变" | ✅ **已解决 — D-B15-04 = FROZEN — A**：**`status CHECK = 0`**；仅 `published` 为 immutable 语义锚点 |

> 以上均为**文档层冲突**，**不修改任何冻结文档**，仅报告。

---

## 10. 校验汇总

```
FK 总数                = 5
FK 删除规则            = RESTRICT 1（`tools.tenant_id`）· CASCADE 4 · 待裁定 0
循环 FK                = 0
Forward dependency     = 0
Core→Domain            = 0
计划外对象             = 0
```
