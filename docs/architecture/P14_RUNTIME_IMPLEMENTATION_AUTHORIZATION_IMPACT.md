# UAP — P14 RUNTIME IMPLEMENTATION AUTHORIZATION IMPACT

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CLOSURE + RUNTIME IMPLEMENTATION AUTHORIZATION PREPARATION（§二十二）
> 性质      = 授权后影响说明（**条件性**：以 RTA-01…RTA-10 获批为前提；当前未获批）
> 基线      = Security DB Boundary = ACCEPTED · HEAD c420403d… · migration 0017_p13_seed
> 本轮未做   = 未修改任何文件 · 未产生任何实现
> ```

---

# 1. 授权后允许变化的代码面

```text
（依 RTA-01 / RTA-05 / RTA-06 / RTA-07 / RTA-08 获批后）

允许新增/修改：
  · apps/api/**             —— 应用装配、路由（新增 identity/device/session/authorization 端点）
  · services/**             —— use-case 编排、事务边界、persistence 协调（含 authorization 扩展）
  · infrastructure/database/session.py · config.py
                            —— 连接边界与连接配置（身份切换为 uap_runtime）
  · infrastructure/database/health.py
                            —— readiness 探针（既有决策语义不变）
  · infrastructure/logging/** · infrastructure/monitoring/**
                            —— observability（含脱敏）
  · tests/**（对应新增）      —— 单元 / 契约 / 架构 / 定向安全探针
  · config/settings.py      —— **仅** runtime DSN 指向 uap_runtime 的配置调整
                               （该文件当前含 BATCH-B 修改，须在不破坏其既有语义前提下变更）

条件性：
  · RTA-09 = A ⇒ 可新增 Bootstrap CLI 代码（**独立于 Runtime API**）
  · RTA-10 = B ⇒ 需先另立 Schema Decision，且 0018+ 仍 FORBIDDEN 直至该 Decision 授权
```

---

# 2. 授权后允许读取的 DB 对象（uap_runtime 已实施面）

```text
SELECT（26 项 · 已授权）：
  users · identities · credentials · devices · sessions · tenants · spaces ·
  tenant_memberships · memberships · roles · permissions · role_permissions ·
  acl_subject_types · resource_permissions · events(+events_202609) · resources ·
  audit_logs(+audit_logs_202609) · platform_state · platform_memberships ·
  agents · agent_versions · agent_permissions · tools · alembic_version
⇒ 读面已就位，Runtime 可直接读取；但**授权判定读取必须经集中式 authorization 路径**（SEC-10）
```

---

# 3. 授权后已由 `uap_runtime` 授权的 DB 操作（写面）

```text
INSERT（12 项 · 已授权）：
  users · identities · credentials · devices · sessions · tenant_memberships ·
  memberships · events(+events_202609) · resources · audit_logs(+audit_logs_202609)

UPDATE（10 项 · 已授权）：
  users · identities · credentials · devices · sessions · tenant_memberships ·
  memberships · events(+events_202609) · resources

DELETE（3 项 · 已授权，仅此三处）：
  sessions · tenant_memberships · memberships

⇒ 以上即 Runtime 实现层可用的**全部**写能力；超出即为越权（DB 层会拒绝）
```

---

# 4. 仍然 DENY 的数据库操作（实现层不得尝试绕过）

```text
· resource_permissions 的 INSERT / UPDATE / DELETE（SEC-09 · 防 self-escalation）
· credentials 的 DELETE（SEC-08 · no physical delete）
· tenants / spaces 的任何写（SEC-05 · SELECT ONLY）
· platform_state / platform_memberships 的写（SEC-13 · bootstrap-owned）
· roles / permissions / role_permissions / acl_subject_types 的任何写（platform / migration 受控）
· audit_logs 的 UPDATE / DELETE（tg_audit_immutable）
· events / resources 的 DELETE（SEC-07）
· 任何 DDL（CREATE / ALTER / DROP / CREATE SCHEMA）· 任何 CREATE ROLE · 任何 GRANT / REVOKE
· SET ROLE 到 uap_migrator / uap_bootstrap / uap_app
（以上均已由 54 次负向探针实测拒绝 · 0 意外放行）
```

---

# 5. 仍需 dedicated path 的 Bootstrap 能力

```text
· platform_memberships INSERT（首行）
· platform_state UPDATE（uninitialized → initialized）
· audit_logs INSERT（action = 'platform.admin.bootstrap'）
⇒ 仅 `uap_bootstrap`（一次性本地 CLI 路径）可执行；**normal Runtime 不得执行**（RUNTIME-SEC-03/08）
⇒ 若 RTA-09 = B（独立），则这些能力在 Runtime 轮内保持"已授权但未使用"状态
```

---

# 6. 禁止触碰的文件 / 资产

```text
· migrations_alembic/versions/0001–0017（尤其 0016 / 0017）
· 任何 0018+ migration（本路线内一律禁止）
· migrations_alembic/env.py（P0 修复语义冻结）
· config/build_info.py（D-PLAT-15 v2 构建期只读工件）
· core/*/interfaces.py 的**契约语义**（仅可作为被消费对象）
· domains/**（业务域）· agent/**（agent runtime）
· apps/worker/main.py（generic scheduler · 不自动纳入）
· infrastructure/database/migration.py（migration engine）
· scripts/**（OI-G-4 范围）
· PDL / Contract / Scope / Dependency / Acceptance 的**冻结正文**
· Security DB Boundary 资产：uap_runtime / uap_bootstrap / 其 grants / C2 / CC-7 /
  pg_default_acl / ownership 拓扑
```

---

# 7. 实现层不得修改的既有 Security Boundary

```text
INV-1  uap_runtime 的 51 项授权（不得新增 / 不得减少；新增需求须重开 Security Decision）
INV-2  uap_bootstrap 的 6 项授权（同上）
INV-3  uap_app 的 5 项授权与 CREATE=false（不得变更）
INV-4  uap_migrator 的 migration-only 边界（不得变更）
INV-5  pg_default_acl = 0（不得引入 default ACL）
INV-6  178 对象 ownership 拓扑（全 uap_migrator · 不得变更）
INV-7  C2 / CC-7（不得变更）
INV-8  P13 seed（3 / 12 / 12 · 不得变更）
⇒ 任一项被实施层修改 ⇒ 触发 §三十一 的 BLOCKED 条件
```

---

# 8. 授权后的验收义务（预告）

```text
Runtime 实现完成后须重新执行：
  · ACCEPTANCE_MATRIX 的 PLANNED 项（34 项）逐项验证
  · Security regression（PRV-1…PRV-8 重新实测 · 确认边界未被实现层改动）
  · 架构守卫（tests/architecture）保持通过
  · 负向探针重跑（确认实现未引入新的越权路径）
  · P14 Security DB Boundary 的 10 条不变量（RUNTIME-SEC-01…10）逐条证据
```

---

# 9. 本轮工程变更

```text
未修改任何文件 · 未产生任何实现 · DDL / DML / migration / runtime code = 0
new role / grant / revoke = 0 · commit = 0 · tag = 0 · push = 0
P14 RUNTIME IMPLEMENTATION = NOT AUTHORIZED · HARD STOP = ACTIVE
```

---

**END OF P14 RUNTIME IMPLEMENTATION AUTHORIZATION IMPACT（2026-09-27 · 条件性影响说明 · 未获批 · 未产生实施）**
