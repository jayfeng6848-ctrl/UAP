# B1-5 — API / Boundary Design（PREP）

Status: **PREP / DESIGN**
阶段：**B1-5 = P07 Tool 域（schema-only）**

---

## 1. 结论先行

```
HTTP API   = 0
Socket.IO  = 0
CRUD       = 0
CLI        = 0（除既有 migration 工具链）
```

**B1-5 = schema 阶段，不新增任何路由、不新增任何 Socket.IO event、不新增任何 Service 层入口。**

---

## 2. 理由

1. **无授权判定则无写入口**：Tool 注册/版本发布/权限绑定的写接口必须建立在**已实现的 Authorization Layer** 之上（谁能注册平台级 Tool？谁能发布租户私有 Tool 版本？谁能绑定 `tool_permissions`？）。该层属后续阶段。此时开接口 ⇒ 产生"没有授权判定的写入口"，直接违反 default-deny。
2. **与 B1-4 同构先例**：`B1-4_API_DESIGN:4,18` 已确立"数据层阶段不开接口"的判例，B1-5 无理由偏离。
3. **调用链尚未就位**：`Agent → Policy → Tool → Service → DB` 的 Policy 与 Agent 分别属后续阶段（P08/P09+）；此时暴露 `tools` 的运行时调用面没有意义。

---

## 3. 后续阶段的接口契约（冻结输入，**非本阶段实现**）

以下仅为**下游阶段的输入契约**，B1-5 **不实现**：

| 能力 | 依赖 | 归属 |
|---|---|---|
| Tool 注册 / disable | `tools` + Authorization Layer | 后续 |
| Tool 版本发布 / deprecate | `tool_versions` + 不变性 trigger 状态迁移 | 后续 |
| Tool 权限绑定 / 解绑 | `tool_permissions` + Authorization Layer | 后续 |
| Tool 调用执行 + 幂等 | `tool_executions`（**P09**） | P09+ |
| 审计写入 | `audit_logs`（**P10**） | P10 |

---

## 4. 与后续阶段的依赖

| 阶段 | 依赖点 |
|---|---|
| P08 AI Gateway | 无直接耦合 |
| P09 Agent | `agent_permissions.tool_id → tools.id`；`tool_executions.tool_id/tool_version_id` |
| P10 Event / Audit | Tool 高危操作（发布/绑权/disable）需审计 |
| 授权阶段 | `tool_permissions` 作为"调用 Tool 所需权限"的输入（本阶段 storage-only） |

---

## 5. 边界声明

- 本阶段**不**定义任何 Tool 的 REST/Socket 契约（不预置 OpenAPI、不预置事件名）。
- 本阶段**不**引入 `handler_ref` 的解析/加载机制（`handler_ref` 仅为文本引用列，**不得**在 B1-5 内引入代码路径或插件加载）。
- 本阶段**不**引入 Plugin / Dynamic registration API。
