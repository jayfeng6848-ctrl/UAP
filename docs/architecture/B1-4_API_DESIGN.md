# B1-4 — API / Socket Design（PREP ONLY）

Status: **DESIGN — 本阶段不实现任何接口**
结论先行：**B1-4 = schema 阶段，不新增任何 HTTP 路由、不新增任何 Socket.IO event。**

---

## 1. 本阶段接口交付结论

| 项 | 结论 |
|---|---|
| HTTP 路由新增 | **0** |
| Socket.IO event 新增（emit / on） | **0 / 0** |
| 认证/授权中间件改动 | **0** |
| 前端改动 | **0** |
| 应用服务实现 | **0**（仅冻结契约，见 `B1-4_DESIGN.md` §5） |

**理由**：B1-4 交付数据层（表 + 约束 + trigger）。接口必须建立在**已实现的 Authorization Layer** 之上，而该层属后续阶段；在此阶段引入接口会导致"没有授权判定的写入口"，直接违反 default-deny 与"AI 只提 Intent"原则。

---

## 2. 后续阶段接口契约（冻结输入，非本阶段实现）

> 以下为**实现阶段**必须遵守的契约；本阶段只做设计冻结，不落地。

### 2.1 HTTP（受保护资源操作）

| 方法 · 路径（建议） | 语义 | 认证 | 授权 | 幂等 |
|---|---|---|---|---|
| `GET /v1/resources` | 列表（强制 tenant/space 过滤） | ✅ 必需 | 能力 + 范围过滤 | 天然幂等 |
| `GET /v1/resources/{id}` | 详情 | ✅ | ACL/permission | 天然幂等 |
| `POST /v1/resources` | 创建 | ✅ | `resource.create`（字典未定稿 → 默认 DENY） | 支持 `Idempotency-Key` |
| `PATCH /v1/resources/{id}` | 修改（label/metadata/classification） | ✅ | 能力 + 分类门控 | 幂等（PATCH 语义） |
| `POST /v1/resources/{id}/archive` | 归档 | ✅ | 能力 | 幂等（重复归档无副作用） |
| `DELETE /v1/resources/{id}` | 软删 | ✅ | 能力 | 幂等（已删 → 204） |
| `POST /v1/resources/{id}/permissions` | grant（allow/deny） | ✅ | **授权层放行 + 高危分类升级** | UPSERT（UQ 冲突 → UPDATE） |
| `DELETE /v1/resources/{id}/permissions/{perm_id}` | revoke | ✅ | 同上 | 幂等（不存在 → 204） |
| `POST /v1/admin/purge`（运维通道） | 受控 purge | ✅ 强认证 | 平台级 + 备份校验 | 幂等（按批次 token） |

**统一约定**

| 项 | 规则 |
|---|---|
| 认证 | 所有写操作**第一行强制认证检查**（等价 `@require_auth`）；无认证 → 401 |
| 授权 | 认证后必经授权层；**默认 DENY**；失败 → 403（不泄漏对象是否存在） |
| 错误体 | `{ "error": { "code": "...", "message": "...", "request_id": "..." } }`；**不得**回显 ACL 细节或 `conditions` 原文 |
| 超时 | 请求处理超时 5s（默认）；purge 走异步任务 |
| 重试 | 客户端仅对 幂等方法 + `Idempotency-Key` 重试；服务端不得自行重试写操作 |
| 幂等 | `POST /permissions` = UPSERT；`DELETE` = 目标态；创建类用 `Idempotency-Key` |
| 审计 | 高危操作（grant/revoke/purge/分类变更）必须写审计（**`audit_logs` 落地于 P10**） |
| 分页 | 列表强制游标分页（`created_at` 序，配合 `ix_res_tenant_type_created`） |

### 2.2 Socket.IO

本阶段 **0 event**。实现阶段若需要实时通知，必须遵守：

```
每个 event 必须具备完整 emit/on 对应关系：
  server emit  "resource.permission.changed"  → client on  "resource.permission.changed"
  client emit  "resource.subscribe"           → server on  "resource.subscribe"
```
| 要求 | 规则 |
|---|---|
| 命名 | `resource.<noun>.<verb>`（小写点分） |
| 订阅过滤 | 服务端按 `tenant_id`/`space_id` + membership 过滤房间；**不得**按客户端自称租户入房 |
| 鉴权 | 连接握手即认证；每次 subscribe 再校验 membership/ACL |
| 载荷 | **不得**携带 ACL 明细、`conditions` 原文、跨租户对象 id |
| 超时/重试 | ack 超时 5s；重连后以**增量拉取**（`GET /v1/resources?since=`）为准，Socket 不作唯一真相源 |
| 幂等 | 事件携带 `event_id` + `version`，客户端按 id 去重 |
| 授权边界 | Socket 只能**通知**，不能成为授权判定通道 |

> **AI 约束**：任何 Socket/HTTP 路径都不得让模型输出参与授权判定；AI 仅提 Intent，授权由 Application Authorization Layer 执行。

---

## 3. 与后续阶段的依赖

| 实现阶段 | 前置 |
|---|---|
| 资源 CRUD 接口 | Authorization Layer（能力判定）+ permission 字典定稿 |
| ACL grant/revoke 接口 | 同上 + `audit_logs`（P10）就绪 |
| 实时通知 | 上述 + Socket 基础设施改造（独立阶段） |
| purge 运维通道 | 备份/PITR 流程（MIGRATION_CONTRACT §12）+ 运维审批 |
