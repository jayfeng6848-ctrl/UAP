# P16 RUNTIME PRIVILEGE MATRIX

## 0. 目的与规则

```text
目的 = 在实现 migration 前冻结 uap_runtime 的 P16 权限面，并证明 unexpected allowed = 0
principal = uap_runtime（唯一；禁止新建 role · 禁止借用 uap_migrator / uap_bootstrap）
禁止 = GRANT ALL · 任何 DELETE · 任何 ALTER/DDL · CREATE ROLE · SET ROLE migrator
验证 = 每项必须有 reason；未列出的组合必须为 0（见 §3 验证方法）
```

## 1. 现状（P16 之前 · 实测）

```text
uap_runtime 现有 = 29 表 · 51 项（SELECT / INSERT / UPDATE 组合）
  · 已含：events(+分区) INSERT/SELECT/UPDATE · audit_logs(+分区) INSERT/SELECT ·
          users/identities/devices/credentials/resources/memberships/sessions INSERT 或 UPDATE ·
          agents/agent_versions/agent_permissions/tools SELECT（P09 面）
  · 未含：ai_providers · ai_models · ai_routes · ai_policies · ai_request_logs ·
          tool_versions · tool_permissions · tool_executions · agent_runs（表尚不存在）
```

## 2. P16 目标矩阵（新增项标注 ★）

| Table | SELECT | INSERT | UPDATE | DELETE | Reason | Principal |
|---|---|---|---|---|---|---|
| agents | 是（已有） | 否 | 否 | 否 | 读取 agent 定义与状态（D02/D03） | uap_runtime |
| agent_versions | 是（已有） | 否 | 否 | 否 | 解析 published version（§27） | uap_runtime |
| agent_permissions | 是（已有） | 否 | 否 | 否 | Agent 侧授权输入（D05/D06） | uap_runtime |
| tools | 是（已有） | 否 | 否 | 否 | 读取 tool 定义（D06） | uap_runtime |
| tool_versions ★ | 是 | 否 | 否 | 否 | input/output schema · handler_ref（registry key）· timeout | uap_runtime |
| tool_permissions ★ | 是 | 否 | 否 | 否 | tool 授权判定输入（D06） | uap_runtime |
| ai_providers ★ | 是 | 否 | 否 | 否 | privacy_tier / max_classification / enabled 判定（D04） | uap_runtime |
| ai_models ★ | 是 | 否 | 否 | 否 | capability / context / pricing / is_private（D04） | uap_runtime |
| ai_routes ★ | 是 | 否 | 否 | 否 | route 解析（tenant/space 覆盖）（D04） | uap_runtime |
| ai_policies ★ | 是 | 否 | 否 | 否 | policy 过滤（classification / privacy / budget / latency）（D04） | uap_runtime |
| ai_request_logs ★ | 否（写后不读） | 是 | 否 | 否 | 记录 provider/model/usage/cost/latency/status（§23） | uap_runtime |
| tool_executions ★ | 是（自身台账） | 是 | 是 | 否 | 执行台账（status/attempts/duration/error） | uap_runtime |
| agent_runs ★（新表） | 是 | 是 | 是 | 否 | Agent Run 台账（D02/D12） | uap_runtime |
| events（含分区） | 是（已有） | 是（已有） | 是（已有） | 否 | P15 兼容（本阶段不激活生产事件） | uap_runtime |
| audit_logs（含分区） | 是（已有） | 是（已有） | 否 | 否 | 审计写入（append-only） | uap_runtime |
| 其他既有表 | 保持现状（不变更） | — | — | — | 不在 P16 scope | uap_runtime |

```text
新增项合计 = 10 张表（tool_versions · tool_permissions · ai_providers · ai_models · ai_routes ·
                       ai_policies · ai_request_logs · tool_executions · agent_runs · agent_runs）
实际新增 = 9 张既有表 + 1 张新表（agent_runs）
```

## 3. 验证方法（必须在迁移与验收时执行）

```text
1. information_schema.role_table_grants WHERE grantee='uap_runtime'
   → 与本文矩阵逐行比对；未列出的 (table, privilege) 组合必须为 0
2. SELECT count(*) FROM information_schema.role_table_grants
   WHERE grantee='uap_runtime' AND privilege_type='DELETE' → 必须为 0
3. has_table_privilege('uap_runtime', <table>, 'DELETE') 对上述表 → 全部 false
4. has_table_privilege('uap_runtime', 'agent_runs', 'ALTER') 等 DDL 权限 → false
5. pg_has_role('uap_runtime','uap_migrator','MEMBER') → false（不得借权）
6. 负路径测试：SET ROLE uap_migrator / CREATE ROLE / ALTER TABLE / DELETE FROM agent_runs
   → 全部必须被拒绝（见 P16 安全测试集）
unexpected allowed = 0
```

## 4. 明确不授予（即便实现需要）

```text
DELETE ai_request_logs / agent_runs / tool_executions（历史台账不可删）
UPDATE agents / agent_versions / tools / tool_versions / ai_* 配置表
INSERT/UPDATE tenants / spaces / memberships / roles / permissions / resource_permissions
ALTER / CREATE / DROP（任何 DDL）
CREATE ROLE / SET ROLE / GRANT 权限
ai_providers.secret_ref 的读取实现（凭据不经 DB 解析路径；secret 只经 env → resolver → adapter）
```

**END OF P16 RUNTIME PRIVILEGE MATRIX**
