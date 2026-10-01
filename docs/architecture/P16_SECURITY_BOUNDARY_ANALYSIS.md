# P16 SECURITY BOUNDARY ANALYSIS

## 0. 性质

```text
ANALYSIS ONLY（NOT FROZEN）
范围 = Actor / Authorization / Credential / Runtime Principal / Tenant-Space / Audit 边界
原则 = 只报告证据与缺口；任何语义选择均登记为 Human Decision Item
```

---

## 1. Actor / Identity 分层（实测）

| 实体 | 载体 | 是否 ACL subject | 证据 |
|---|---|---|---|
| User | users · identities · sessions | **YES**（subject_type = USER） | `core/permission/vocabulary.SUBJECT_TYPES` |
| Role | roles · role_permissions | **YES**（ROLE） | 同上 |
| Agent | agents · agent_versions | **YES**（AGENT · D-AUTH-02） | 同上 · P09 四表 |
| Worker（P15 consumer） | 进程 + worker_id（TEXT） | **NO**（D-P15/O-3） | `events.worker_id` 为 text；无 subject |
| DB service principal | uap_app / uap_runtime / uap_migrator / uap_seed / uap_bootstrap | **NO**（不是 ACL subject） | P14 privilege matrix · grants 实测 |
| Service Principal（应用内部） | 无独立实体 | 不存在 | 全仓无 service principal 表/主体 |
| AI Provider | ai_providers（行） | **NO**（不是 subject） | 表为平台级配置 ROOT |
| Tool | tools · tool_versions | **NO**（不是 subject） | 授权对象是 tool + permission |
| Event / Audit | events / audit_logs（行） | **NO**（载体） | P10 契约 |

```text
必须保持的不等式（P15 继承）
  Actor Identity ≠ Agent Identity ≠ Worker Identity ≠ DB Service Principal
  Worker = execution mechanism（不是 ACL subject）
  禁止新增：system_agent / ai_worker / runtime_agent / service_agent / worker_subject /
            service_subject / consumer_subject / system_subject
  ⇒ 若 P16 认为必须新增 system/service subject ⇒ STOP · 独立 Human Decision
```

## 2. Authorization 路径审计

```text
已存在（实测）
  12 canonical actions（read…admin）· SUBJECT_TYPES = USER/ROLE/AGENT · STORED_SCOPES = PLATFORM/TENANT/SPACE
  DENY > ALLOW · FAIL CLOSED · 无授权缓存（D-AUTH-13）· approval ≠ ALLOW（D-AUTH-11/14）
  四档 risk 与 permission/decision 分离（D-AUTH-10）
  Tool 是 agent 唯一的受控出口（D-AUTH-09）
  ToolGate.authorize() 已实现：tool 必须存在且 enabled；grant；scope；approval 组合判定；异常 fail-closed
  三审计分离（D-AUTH-15）：authorization audit ≠ tool execution audit ≠ agent run audit
```

```text
链路（提案映射）
  Agent → Tool            ：agent_versions.allowed_tools（JSONB）
  Tool → Permission       ：tool_permissions.permission_id（FK → permissions）
  Permission → Actor      ：role_permissions / agent_permissions / resource_permissions
  Actor → Authorization   ：services/authorization/service.py（Decision）
  Authorization → Allow/Deny ：DENY>ALLOW · 默认 DENY（无 grant）
```

### 2.1 八个必答问题

| # | 问题 | 现状证据 | 结论 |
|---|---|---|---|
| 1 | Agent permission 是否已足够？ | agent_permissions 表（effect/conditions/resource_scope）存在；解析逻辑未实现 | **证据不足** → Human Decision |
| 2 | 是否需要 tool-level permission？ | tool_permissions 表存在；ToolGate 已按 tool 判定 | 结构已具备；绑定规则待裁决 |
| 3 | 是否需要 resource-scope？ | `agent_permissions.resource_scope` 为 **Legacy Opaque**（D-AUTH-23） | **需裁决**（是否启用为强约束） |
| 4 | Agent 是否继承 User 权限？ | 无继承规则实现；D-AUTH-06 定义 scope 与显式向下继承 | **需冻结** |
| 5 | Agent 是否拥有独立权限？ | D-AUTH-02（Agent 独立主体）+ agent_permissions | 是（主体独立）；边界需冻结 |
| 6 | Worker 执行时如何保留 originating actor？ | P15 冻结：actor provenance = 事件 originating actor | 已冻结；P16 需沿用 |
| 7 | 后台执行如何避免权限提升？ | 禁止借用 platform_admin / uap_bootstrap / uap_migrator（P15 O-3） | 已冻结；P16 需沿用 |
| 8 | Tool 能否代表 actor 修改 tenant-scoped state？ | 无 tool 执行实现；无 actor→tool 写路径 | **需冻结**（P16-D06） |

## 3. Credential / Secret Boundary（强制重点）

```text
现状（实测）
  · ai_providers.secret_ref : TEXT 列（可空）· 全仓 0 处代码引用 ⇒ 无解析器、无注入路径
  · .env.example : OPENAI_API_KEY= / ANTHROPIC_API_KEY= / DEEPSEEK_API_KEY=（空值占位）
  · config/settings.py : 仅 SECRET_KEY（应用签名）+ AI_DEFAULT_PROVIDER/MODEL/TIMEOUT；无 provider key 字段
  · credentials 表 : 属 Identity 面（uap_runtime 有 INSERT/SELECT/UPDATE）——不是 AI provider 凭据
  · intelligence/providers : FORBIDDEN_DIRECT_IMPORTS（禁止直接 import vendor SDK）
  · ai_request_logs 设计定位 = 成本/配额/可观测（表注释：不存 prompt 原文 · 非审计）
  · ai_policies.redaction_profile : 存在字段（无实现）
  · AuthenticatedContext.LOG_SAFE_FIELDS : 明确白名单（不含任何凭据）
```

### 3.1 Credential Data Flow（当下链路不存在；以下为未来实现的必须约束）

| 关注点 | 现状 | 风险 | 需要的决定 |
|---|---|---|---|
| 谁存 secret | 无实现（secret_ref 未解析；env 占位） | — | P16-D07 |
| 谁读取 secret | 不存在读取者 | 若由 agent/tool 读取 ⇒ 泄漏面扩大 | P16-D07 |
| 谁可触发使用 | 目前无人可触发 | 需明确仅 provider adapter 边界内 | P16-D07 |
| Agent 是否能看到 secret | 现状 N/A | 必须 **NO** | P16-D07 |
| Tool 是否能看到 secret | 现状 N/A | 必须 **NO** | P16-D07 |
| Worker 是否能看到 secret | 现状 N/A（P15 worker 不涉及） | 必须 **NO** | P16-D07 |
| Audit 是否可能泄漏 | 无 AI 审计落地 | 必须脱敏 + 白名单 | P16-D07 / D05 |
| Exception 是否可能泄漏 | 无实现 | 必须脱敏（禁止回显 key/URL 凭据） | P16-D07 |
| AI prompt 是否可能泄漏 | 无实现 | prompt 不得承载 secret；request log 不存原文 | P16-D07 / D05 |

```text
禁止进入的位置（建议硬约束）：DB 明文 · request log · application log · audit log ·
event payload · tool result · AI prompt · AI response
结论：凭据边界 = P16 SECURITY DECISION / BLOCKER CANDIDATE（F-P16-05）
```

## 4. Runtime Principal Boundary（P14 继承）

```text
既有 principal（FROZEN 面）
  uap_app · uap_runtime · uap_bootstrap · uap_migrator · uap_seed（+ 超管 uap）
  P14 规则：runtime DSN 必须指向 uap_runtime 且 current_user == session_user == uap_runtime
           （infrastructure/database/principal.assert_connection_principal）
  禁止把 uap_migrator / uap_bootstrap 用于正常 runtime
```

### 4.1 现状能力 vs P16 需求（实测 grant）

| 面 | uap_runtime 现状 | P16 需要 | 判定 |
|---|---|---|---|
| ai_providers | 无 grant | 读（routing 需要） | **New grant required** |
| ai_models | 无 grant | 读 | **New grant required** |
| ai_routes | 无 grant | 读（含 tenant/space 覆盖） | **New grant required** |
| ai_policies | 无 grant | 读 | **New grant required** |
| ai_request_logs | 无 grant | INSERT（成本/可观测） | **New grant required** |
| agents / agent_versions / agent_permissions | SELECT | 读（+ 可能写 run 状态） | 部分足够 |
| tools | SELECT | 读 | 足够 |
| tool_versions / tool_permissions | 无 grant | 读（input/output schema · handler_ref · effect） | **New grant required** |
| tool_executions | 无 grant | INSERT/UPDATE（执行台账） | **New grant required** |
| events | INSERT/SELECT/UPDATE（含分区） | 生产事件 | 足够（若 D08 批准） |
| audit_logs | INSERT/SELECT（含分区） | 审计写入 | 足够 |
| users/identities/devices/sessions/credentials | INSERT/SELECT/UPDATE | 身份路径 | 足够 |

```text
结论：P16 必然产生新的 grant（至少 6 张表）。
选项：①扩展 uap_runtime 的 grant（改动 P14 面 ⇒ 高风险）②新增专用 principal（如 uap_agent）
     ③由既有 uap_runtime 承担并接受面扩大
⇒ 任一选项均需 Human Decision（P16-D11 / P16-D12）；禁止 BOT 自行创建 principal 或 grant
```

### 4.2 各环节 principal 建议（提案，非冻结）

| 环节 | 建议承担者（PROPOSAL） | 说明 |
|---|---|---|
| AI request ingress | uap_app（API 面） | 与现有 API 一致 |
| Agent execution | uap_runtime（现有 runtime 边界） | 需新增 ai_*/tool_* 读权限 |
| Tool execution | uap_runtime | 需 tool_versions/tool_executions 权限 |
| Event production | uap_runtime | events INSERT 已有 |
| Outbox consumer | uap_runtime（P15 worker） | 已就绪 |
| Audit write | uap_runtime / uap_app | audit_logs INSERT 均已有 |

## 5. Tenant / Space Scope 分类（实测 schema）

| 对象 | tenant_id | space_id | 语义分类 | 证据 |
|---|---|---|---|---|
| ai_providers | 无该列 | 无 | **platform-scoped ROOT** | 0010 · D-B16-11 |
| ai_models | 无 | 无 | **platform-scoped** | 0010 |
| ai_routes | NULLable | NULLable | tenant / space / platform 覆盖 | 0010 |
| ai_policies | NULLable | NULLable | tenant / space / platform 覆盖 | 0010 |
| ai_request_logs | NULLable | NULLable | tenant-scoped 或 platform | 0010 |
| agents | **NOT NULL** | NULLable | tenant-scoped（无 platform agent 语义） | 0011 |
| agent_versions | 经 agent_id | — | 继承 agent | 0011 |
| agent_permissions | 经 agent_id | — | 继承 agent | 0011 |
| tool_executions | **NOT NULL** | 无该列 | tenant-scoped | 0011 |
| tools | NULLable | 无 | 平台工具或 tenant 工具 | 0008 |
| tool_versions / tool_permissions | 经 tool_id | — | 继承 tool | 0008 |
| events | NULLable | NULLable | NULL = **platform-scoped**（P15 冻结） | 0013 · PDL 附录 U |
| audit_logs | NULLable | NULLable | 同上 | 0013 |
| credentials / devices / sessions | 经 user/identity | — | tenant via membership | 0002–0005 |

```text
必须保持：tenant_id = NULL ⇒ platform-scoped
           ≠ unknown tenant · ≠ tenant impersonation · ≠ authorization bypass
冲突登记：agents.tenant_id NOT NULL 与 events.tenant_id NULLable 语义不同 ⇒
          平台级 agent 是否存在 = Human Decision（P16-D10）
```

## 6. Security Blockers / Decision Items

```text
BLOCKER CANDIDATES
  B-1 运行时 principal 对 ai_*/tool_* 无任何 grant（F-P16-02）→ P16-D11 / D12
  B-2 Tool 执行边界不存在且可能触及 tenant-scoped 写（F-P16-04）→ P16-D06
  B-3 凭据解析路径不存在，且不得进入 log/audit/event/prompt（F-P16-05）→ P16-D07

已冻结、不得改动（P16 必须原样继承）
  Actor provenance · 禁止 principal 借用 · subject vocabulary（USER/ROLE/AGENT）·
  12 canonical actions · DENY>ALLOW · 无授权缓存 · approval ≠ ALLOW ·
  UUIDv7 canonical event identity · tenant_id = str | None（NULL = platform-scoped）·
  P15 consumer 语义（claim/lease/retry/recovery/幂等）
```

**END OF P16 SECURITY BOUNDARY ANALYSIS（ANALYSIS ONLY）**
