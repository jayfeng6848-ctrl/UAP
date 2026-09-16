# STEP 1-B / B0 — Index Strategy

Status: **DESIGN PREPARATION — 不创建任何表**
来源：STEP 1-A 冻结设计 `CORE_DOMAIN_MODEL.md` §12 + ER_MODEL
原则：**只为已知查询模式建索引**；每个非 PK 索引必须说明用途与查询模式；不为"以后可能用"建。

> 部分唯一索引（UNIQUE 语义）在 CONSTRAINT_MATRIX 列出，本文档不重复；本文档只覆盖 **非唯一查询索引 + 唯一索引的落点说明**。

---

## 1. 索引清单（逐表）

### users

| 索引 | 类型 | 服务查询 | 说明 |
|---|---|---|---|
| `ix_users_status` | btree (status) | 后台任务按状态扫描（锁定清理等） | 低频；若确认无后台批扫可去掉 → 标注 P3 候选 |

### identities

| 索引 | 类型 | 服务查询 |
|---|---|---|
| （唯一索引已覆盖登录解析） | — | `(provider,issuer,subject)` UQ 即查询索引；不再额外建 |

### credentials

| 索引 | 类型 | 服务查询 |
|---|---|---|
| 部分唯一 `(identity_id) WHERE type='password' AND revoked_at IS NULL` | UQ | 当前有效密码唯一 |

### devices

| 索引 | 类型 | 服务查询 |
|---|---|---|
| `ix_devices_user_status ON (user_id, status)` | btree | "我的设备列表 / 撤销某用户全部设备" |

### sessions

| 索引 | 类型 | 服务查询 |
|---|---|---|
| `uq_sessions_token`（token_hash） | UQ | 认证查 session（主查询） |
| `uq_sessions_refresh` 部分 | UQ | refresh 轮换 |
| `ix_sessions_user_status ON (user_id, status)` | btree | 会话列表 / 批量撤销 |
| `ix_sessions_expires_active ON (expires_at) WHERE status='active'` | 部分 btree | TTL 清理 job |

### tenants

| 索引 | 类型 | 服务查询 |
|---|---|---|
| `ix_tenants_status` | btree | 后台任务（归档/清理扫描） | 低频 → P3 候选

### spaces

| 索引 | 类型 | 服务查询 |
|---|---|---|
| 部分 UQ `(tenant_id, lower(key)) WHERE deleted_at IS NULL` | UQ | 空间查找 |
| `ix_spaces_tenant_status ON (tenant_id, status)` | btree | 租户空间列表 / 归档扫描 |

### tenant_memberships

| 索引 | 类型 | 服务查询 |
|---|---|---|
| UQ `(tenant_id, user_id)` | UQ | 成员唯一 + "用户加入的租户"（user_id 打头时需 `(user_id)` 辅助？→ 见下） |
| `ix_tm_user ON (user_id)` | btree | **"我属于哪些租户"（切租户列表）** —— 由 UQ 以 tenant_id 打头，无法服务 user 开头查询，故需此单列索引 |

### memberships

| 索引 | 类型 | 服务查询 |
|---|---|---|
| 部分 UQ `(space_id, user_id) WHERE removed_at IS NULL` | UQ | 成员唯一 + 空间成员列表 |
| `ix_memberships_tenant_user ON (tenant_id, user_id)` | btree | "我在该租户的哪些空间" |

### roles

| 索引 | 类型 | 服务查询 |
|---|---|---|
| 三条部分唯一（platform/tenant/space） | UQ | 角色 key 查找；已覆盖 scope 查询无需额外索引 |

### role_permissions

| 索引 | 类型 | 服务查询 |
|---|---|---|
| PK `(role_id, permission_id, effect)` | PK | 按角色取权限（主查询）；不需要 permission_id 反查则免建反向索引 |
| `ix_rp_permission ON (permission_id)` | btree | 权限被哪些角色使用（审计/变更影响分析）→ 若低频可 P3 |

### resources（重点：租户过滤 + 列表）

| 索引 | 类型 | 服务查询 |
|---|---|---|
| 部分 UQ `(tenant_id, resource_type, natural_key)` | UQ | natural_key 幂等查找 |
| `ix_res_tenant_space_type_status ON (tenant_id, space_id, resource_type, status)` | btree | **资源列表主查询（tenant→space→type→status 前缀过滤）** |
| `ix_res_tenant_owner ON (tenant_id, owner_id)` | btree | "我创建的资源" |
| `ix_res_tenant_type_created ON (tenant_id, resource_type, created_at DESC)` | btree | 时间序列表/分页 |
| `ix_res_tenant_deleted ON (tenant_id, deleted_at) WHERE deleted_at IS NOT NULL` | 部分 btree | retention purge 扫描（软删超期行）→ 若 purge 走 job 需此索引 |

### resource_permissions

| 索引 | 类型 | 服务查询 |
|---|---|---|
| UQ `(resource_id, subject_type_id, subject_id, action)` | UQ | **按资源取 ACL（主查询）** |
| `ix_rp_subject ON (subject_type_id, subject_id)` | btree | "某主体有哪些授权"（审计/撤销时用） |

### agents

| 索引 | 类型 | 服务查询 |
|---|---|---|
| 部分 UQ `(tenant_id, lower(key)) WHERE archived_at IS NULL` | UQ | Agent 查找 |
| `ix_agents_tenant_status ON (tenant_id, status)` | btree | Agent 列表/调度扫描 |

### agent_versions / agent_permissions

| 索引 | 类型 | 服务查询 |
|---|---|---|
| UQ `(agent_id, version)` | UQ | 版本定位 |
| `ix_ap_agent ON (agent_id)` | btree | Agent 权限清单（若 UQ 顺序不同则必须；见约束矩阵 UQ） |

### tools

| 索引 | 类型 | 服务查询 |
|---|---|---|
| 平台 + 租户两条部分 UQ | UQ | 工具查找 |

### tool_versions / tool_permissions / tool_executions

| 索引 | 类型 | 服务查询 |
|---|---|---|
| UQ `(tool_id, version)` | UQ | 版本定位 |
| `ix_texec_idem ON (tool_id, idempotency_key) WHERE idempotency_key IS NOT NULL` | 部分 UQ | **幂等锚点** |
| `ix_texec_tenant_created ON (tenant_id, created_at DESC)` | btree | 执行历史列表 |
| `ix_texec_status ON (status, started_at) WHERE status='running'` | 部分 btree | 超时重扫（running 超时判定）→ 若实现重试 job 需要 |

### ai_providers / ai_models / ai_routes

| 索引 | 类型 | 服务查询 |
|---|---|---|
| UQ `(key)` | UQ | 厂商查找 |
| UQ `(provider_id, model_key)` | UQ | 模型定位 |
| UQ `(COALESCE(tenant_id), COALESCE(space_id), capability, priority)` | UQ | 路由匹配（租户/平台最具体优先） |
| `ix_aimodels_capability ON (capability) WHERE enabled` | 部分 btree | 按 capability 枚举可用模型 → 若路由缓存充分可免（P3） |

### ai_policies

| 索引 | 类型 | 服务查询 |
|---|---|---|
| UQ `(tenant, space, name)` | UQ | 策略查找 |

### ai_request_logs（分区表）

| 索引 | 类型 | 服务查询 |
|---|---|---|
| `ix_airl_tenant_occurred ON (tenant_id, occurred_at DESC)` | btree | 成本/用量查询 |

### events（分区表，outbox 轮询是热点）

| 索引 | 类型 | 服务查询 |
|---|---|---|
| `ix_events_dispatch ON (status, next_attempt_at) WHERE status IN ('pending','claimed')` | 部分 btree | **outbox 轮询（claim 扫描）** —— claim 用 `FOR UPDATE SKIP LOCKED`，此索引加速候选行定位 |
| `ix_events_tenant_type_time ON (tenant_id, event_type, occurred_at DESC)` | btree | 事件查询（排障/回放） |

> 分区表索引建在父表自动下推；避免在 `payload` jsonb 上建 GIN（无查询需求）。

### audit_logs（分区表）

| 索引 | 类型 | 服务查询 |
|---|---|---|
| `ix_audit_tenant_time ON (tenant_id, occurred_at DESC)` | btree | 租户审计页 |
| `ix_audit_actor_time ON (actor_id, occurred_at DESC)` | btree | 用户行为轨迹 |
| `ix_audit_resource ON (resource_type, resource_id, occurred_at DESC)` | btree | 资源历史 |
| `ix_audit_correlation ON (correlation_id)` | btree | 链路追踪 |
| `ix_audit_risk ON (risk_level, occurred_at) WHERE risk_level IN ('HIGH','CRITICAL')` | 部分 btree | 安全告警扫描 |

---

## 2. 冗余与反模式排查

| 检查 | 结论 |
|---|---|
| 低基数列单列索引（status/classification/scope/risk_level） | **不建**：选择性差 |
| 每列都建 | **不建**：只建上表所列 |
| jsonb GIN | **不建**：无 jsonb 过滤查询需求；需要时单独立项 |
| `tenant_id` 打头重复 | 多索引共享同一前缀（如 resources 三索引均 tenant 打头）——可接受：列顺序不同，服务不同查询；不合并（无法用单一复合索引服务三类查询） |
| 外键列自动索引 | PG **不会**自动为 FK 建索引。需要按 FK 反查的表：`ix_rp_permission`、`ix_rp_subject`、`ix_ap_agent`、`ix_texec_*`、`ix_tm_user`。FK 仅在删除时做 R 检查（无索引会导致父表 DELETE 时子表全扫）→ **凡 FK 目标为"会被删除的父行"且子表无合适索引者必须补** |

## 3. FK 反查强制清单（父表删除性能）

父表 DELETE（或 RESTRICT 检查）会扫子表 FK 列；下列 FK 列若无常驻索引需补（防全表扫）：

| 子表 FK 列 | 已有索引? | 动作 |
|---|---|---|
| `identities.user_id` | 无（UQ 是 provider 打头） | **补 `ix_identities_user ON (user_id)`** |
| `credentials.user_id` / `identity_id` | 部分 UQ 打头 identity_id（password 唯一）覆盖不了全 user | **补 `ix_credentials_user ON (user_id)`** |
| `devices.user_id` | `(user_id, fingerprint)` UQ 打头 user_id | 已覆盖（复合可服务前缀） |
| `sessions.user_id` / `identity_id` / `device_id` | `ix_sessions_user_status` 打头 user_id；其余两列无 | **补 `ix_sessions_identity ON (identity_id)`、`ix_sessions_device ON (device_id)`**（撤销级联时性能） |
| `tenant_memberships.tenant_id/user_id/role_id` | UQ 打头 tenant_id；`ix_tm_user`；role_id 无 | **补 `ix_tm_role ON (role_id)`**（role 删除 RESTRICT 检查） |
| `memberships.tenant_id/space_id/user_id/role_id` | UQ 打头 space_id（部分）；`ix_memberships_tenant_user`；role_id 无 | **补 `ix_memberships_role ON (role_id)`** |
| `roles.tenant_id/space_id` | 部分 UQ 打头 | tenant/space purge 时低风险（roles 少）→ P3 |
| `role_permissions.role_id/permission_id` | PK 打头 role_id | `ix_rp_permission` 已补 |
| `resources.tenant_id/space_id/owner_id` | 复合索引打头 tenant/space/owner 均覆盖 | 通过 |
| `resource_permissions.resource_id/subject_type_id/granted_by` | UQ 打头 resource_id | `ix_rp_subject` 已补；subject_type_id FK 目标（acl 表）几乎不删 → 免 |
| `agents.owner_id` | 少 | P3 |

> 上表"动作"列的补充索引进入 P12；RESTRICT FK 的父表删除性能是 B1 测试项（`tests/integration/test_fk_scan_no_seq`）。

---

## 4. 索引命名规范

- 唯一：`uq_<table>_<cols>`
- 查询：`ix_<table>_<cols>`（列序同索引定义）
- 部分：名内含 `WHERE` 语义注释；DDL 里必须写明谓词
- 复合列序 = 等值在前、范围在后（如 `(tenant_id, space_id, resource_type, status)`）

---

## 5. 汇总决策

- **必建（查询/约束语义）**：见 §1 各表（无 P3 标注者）
- **P3 候选（确认后建）**：`ix_users_status`、`ix_tenants_status`、`ix_rp_permission`、roles FK 反查、agents.owner_id、`ix_aimodels_capability`
- **不建**：低基数列单列、jsonb GIN、无查询支撑的组合
- 季度用 `pg_stat_user_indexes` 清理零扫描索引（列入运维手册）
