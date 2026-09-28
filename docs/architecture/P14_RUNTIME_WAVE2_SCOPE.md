# UAP — P14 RUNTIME WAVE 2 SCOPE

> ## 状态
>
> ```text
> 状态      = **HUMAN DECISION REQUIRED**
> 性质      = 范围候选（**未授权 · 未实现**）
> 依据      = Wave 1 FINAL ACCEPTANCE REPORT（WAVE 1 ACCEPTED）·
>             P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT / SCOPE / DEPENDENCY_MAP /
>             ACCEPTANCE_MATRIX · SEC-P14-01…14（PDL 附录 O）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · 0018+ = 0
> 本轮未做   = runtime code = 0 · DDL / DML = 0 · migration = 0 · role / grant / revoke = 0
> ```

---

# 0. 本文件不假定任何节点必然进入 Wave 2

```text
候选核心链（**候选**，非既定）：

    Identity
        ↓
    Device
        ↓
    Session
        ↓
    Authorization Context
        ↓
    API Adaptation

每一个节点**是否进入 Wave 2** 必须由 Human Decision 明确（见 §4 与
P14_RUNTIME_WAVE2_HUMAN_DECISION_SHEET.md）。不得依目录名自动扩大范围。
```

---

# 1. 现有资产实况（§三 只读勘察结论 · 禁止假设为空白）

```text
分层现状（**Domain 契约齐备 · 实现层空白**）：

  core/*（Domain 契约 · 已冻结 · 只作被消费对象）
    identity / device / session / auth / membership / permission / tenant / space /
    resource / audit / event / policy  —— 均含 interfaces.py
    ⇒ Identity / Device / Session 的**契约**已存在（非空白）

  services/
    authorization/（12 文件 · Stage 2 唯一授权权威 · 只读不写 · 不缓存）
    ⇒ **不存在** identity / device / session service 包（实现层空白）

  apps/api/
    main.py（FastAPI factory · lifespan 未接 RuntimeApplication）· routes/{health,meta}
    ⇒ **不存在** identity / device / session 端点；API 层为 transport-only 现状

  apps/frontend/（Vite + React 前端 · 非 Python runtime 面）
  apps/worker/main.py（generic background scheduler · FILE_INVENTORY 列为 OUT OF SCOPE）

  domains/（business / company / entertainment / family 的 manifest · 业务域）
    ⇒ 不属 P14 · 不得在 Wave 2 消费

  infrastructure/
    database/{config,principal,runtime,persistence,session,health,migration} ·
    runtime/{errors,retry,lifecycle} · logging/{structured,redaction} ·
    monitoring/metrics · cache|queue|storage/interfaces（仅接口）
    ⇒ Wave 1 已验收基础层（冻结输入）

  schema（migration 0017 · 已存在对象）
    users · identities · credentials · devices · sessions · tenants · spaces ·
    memberships · tenant_memberships · roles · permissions · role_permissions ·
    resources · resource_permissions · events(+分区) · audit_logs(+分区) ·
    platform_state · platform_memberships · agents / agent_versions /
    agent_permissions / tools / acl_subject_types · alembic_version
    ⇒ Identity / Device / Session 的**存储面**已存在（非空白）
```

```text
⇒ Wave 2 的实质 = 在既有 Domain 契约与既有 schema 之上**实现 adapter / service / use-case**，
  而不是新建模型。由此产生 §5 的 CONTRACT DIVERGENCE（必须先裁决）。
```

---

# 2. Candidate Core

```text
C-1 Identity
  in-scope 候选 = identity 建立 / 状态推进 / 唯一性判定 / 凭据关联 / 停用撤销
  依赖      = Wave 1 Foundation（uap_runtime 连接 · transaction · repository）
              + 既有 schema：users · identities · credentials
  现状      = core/identity + core/auth 契约存在；无 service 实现
  未决      = ID-W2-01…05 + VOC-W2-01…04（见 §5）

C-2 Device
  in-scope 候选 = enrollment / binding / revoke / replacement
  依赖      = C-1 + 既有 schema：devices（+ sessions 级联语义）
  现状      = core/device 契约存在；无 service 实现
  未决      = DV-W2-01…05

C-3 Session
  in-scope 候选 = creation / lifecycle / revoke / timeout / concurrency
  依赖      = C-1 + C-2 + 既有 schema：sessions
  现状      = core/session 契约存在；无 service 实现
  未决      = SS-W2-01…05

  ⚠ Identity / Device / Session 均为**候选**；是否全部进入 Wave 2 由 Human 裁定
    （SCOPE-W2-01，见 Decision Sheet Batch 0）。
```

---

# 3. Candidate Adaptation

```text
A-1 API boundary（transport / adaptation only）
  in-scope 候选 = authentication adapter · 请求→authenticated context 转换 ·
                  error mapping · 既有 FastAPI 装配（lifespan 接线）
  依赖      = C-1…C-3（若任一未实现，则 API 无业务可暴露）
  现状      = apps/api 仅有 health / meta；lifespan 未接 RuntimeApplication（Wave 1 已登记事实）
  未决      = API-W2-01…04 + SC-W2-01（API 是否同轮）
  ⇒ API **不得**获得 business authority；不得 handler → direct DB（RUNTIME-G-05）
```

---

# 4. Supporting Capability

```text
S-1 authorization context propagation
      把 authenticated subject 映射进既有 Stage 2 Authorization（**不新建引擎**）
      未决 = AUTH-W2-01…03
S-2 authentication context propagation
      最小上下文（不得把整行 record / credential 对象塞入 context）
      未决 = CTX-W2-01…04
S-3 observability context（correlation / request context · 复用既有 logging）
      未决 = SEC-W2-04（observability 面）+ CTX-W2-03
S-4 error mapping（复用 Wave 1 Error Taxonomy 的 8 类 · 不新建映射体系）
      未决 = API-W2-04
S-5 tenant / space context（认证成功 ≠ tenant/space 授权）
      未决 = CTX-W2-02 + SEC-W2-03
```

---

# 5. ⚠ CONTRACT DIVERGENCE（本轮只读勘察发现 · 必须先裁决）

```text
分类      = `WAVE2 CONTRACT DIVERGENCE — DOMAIN vs SCHEMA VOCABULARY`
性质      = **决策前置项**（非 Wave 1 缺陷；Wave 1 未触碰 identity/device/session）
依据      = 只读比对 core/*/interfaces.py 与 migration 0017 实测 schema
处置      = 已登记为 VOC-W2-01…04（Decision Sheet Batch 0）· **不得自行选择**
```

| # | 维度 | Domain 契约（core/） | 实测 schema（0017） | 差异性质 |
|---|---|---|---|---|
| D-1 | 聚合根 | identity 中心：`Device.identity_id`、`Session(identity_id, device_id)`；**无 User 契约** | user 中心：`devices.user_id`、`sessions.user_id + identity_id`、`identities.user_id` | **真实分歧**（聚合根不同） |
| D-2 | credential type | `CREDENTIAL_TYPES = (password, token, api_key, device)` | `credentials.type ∈ (password, api_key, recovery_code, device_cert, otp)` | **真实分歧**（枚举不同） |
| D-3 | device status | `DEVICE_STATUS = (pending, active, revoked)` | `devices.status ∈ (pending, active, untrusted, revoked, lost)` | 子集/超集（契约无法表达 2 态） |
| D-4 | identity 状态 | `Identity.status` 默认 `"active"`（**无枚举**） | `identities.status ∈ (active, unverified, suspended, revoked)` | **真实分歧**（契约无枚举） |
| D-5 | identity 类别 | `IDENTITY_KINDS = (user, service, device_subject)` | `identities.provider ∈ (local, oidc, saml, device, service)` | 轴不同（kind vs provider）需显式映射 |
| D-6 | user 状态 | **无 User 契约** | `users.status ∈ (pending, active, suspended, locked, deleted)` | 契约缺失 |
| D-7 | credential algorithm | **未在契约表达** | `credentials.algorithm ∈ (argon2id, scrypt, sha256_hmac)`（NOT NULL） | 契约缺失（SEC-08 已定 Argon2id 语义） |
| D-8 | session 状态 | `SESSION_STATUS = (active, expired, revoked)` | `sessions.status ∈ (active, expired, revoked)` | **一致** ✅ |
| D-9 | permission effect | `EFFECTS = (ALLOW, DENY, REQUIRES_APPROVAL)` | `role_permissions.effect ∈ (allow, deny)` | **真实分歧**（存储无法表达 REQUIRES_APPROVAL） |

```text
重要更正（防生成第二套状态机）：
  指令 §六 举例的 `pending → verified → credential/device verified → active` **不是**
  当前 Domain 契约或 schema 中的状态名。现行权威只有：
    DB identities.status = (active, unverified, suspended, revoked)
    DB users.status      = (pending, active, suspended, locked, deleted)
  ⇒ Wave 2 必须**采用其中一套**（或经 Human 裁决建立显式映射），
     **禁止**新造第三套状态名。
```

```text
live 复核已完成（见 P14_RUNTIME_WAVE2_SCHEMA_DEPENDENCY_REGISTER.md §3），补充事实：
  · `memberships` / `tenant_memberships`.status = (invited, active, suspended, removed)
    ⇒ **与 Domain `MEMBERSHIP_STATUS` 完全一致**（无分歧）
  · `users` 唯一性已存在：UNIQUE(lower(email)) / UNIQUE(lower(username))
    **WHERE deleted_at IS NULL** ⇒ **全局**（无 tenant 维度）· 大小写不敏感 · 软删除后释放
    ⇒ 任何 tenant-scoped 唯一性方案都会与既有 DB 行为冲突（见 ID-W2-03）
  · `devices` 唯一性 = UNIQUE(**user_id**, fingerprint) ⇒ per-user 唯一；
    **未禁止**跨用户复用同一 fingerprint
  · `sessions.device_id` **可空**且无唯一约束 ⇒ "必须绑定已验证设备"与并发策略
    只能由应用层表达（DB 无法约束）
  · `role_permissions.effect` 仅 (allow, deny) ⇒ 见 D-9

⇒ 上述复核**未产生**新的 schema dependency；§1 结论不变
⇒ 复核**新增** 1 项词表分歧（D-9），已并入本表
```
```

---

# 6. Explicitly Excluded（Wave 2 明确排除）

```text
EX-1  Bootstrap CLI                    （RTA-09 = OPTION B · OUT OF SCOPE）
EX-2  P15                              （FORBIDDEN）
EX-3  Schema support objects           （RTA-10 = B · SEPARATE DECISION）
EX-4  new migration（0018+）           （FORBIDDEN）
EX-5  new role                         （需独立 Security Decision）
EX-6  new grants / revoke              （需独立 Security Decision · 不得自动 GRANT）
EX-7  authorization model redesign      （Stage 2 为唯一权威 · 不得重写）
EX-8  permission vocabulary redesign    （`SUBJECT_TYPES/ACTIONS/STORED_SCOPES/EFFECTS` 冻结）
EX-9  C2 modification                   （SEC-12 · 冻结）
EX-10 CC-7 modification                 （SEC-12 · 冻结）
EX-11 P13 seed modification             （冻结）
EX-12 domains/** 业务域实现             （不属 P14）
EX-13 agent/** runtime 实现             （不属 P14 · 见 FILE_INVENTORY OUT OF SCOPE）
EX-14 apps/worker 后台调度实现          （FILE_INVENTORY 明确不自动纳入）
EX-15 Wave 1 已验收基础行为的改写        （须登记 FOUNDATION REGRESSION RISK）
```

---

# 7. 与 Wave 1 的关系（Foundation 冻结输入）

```text
Wave 2 **只消费**以下 Wave 1 ACCEPTED 资产（FINAL ACCEPTANCE REPORT §28 Evidence Freeze）：
  Runtime Bootstrap · uap_runtime Connection · Connection Pool · Transaction Boundary ·
  Persistence Adapter · Lifecycle · Health Infrastructure · Observability ·
  Error Taxonomy · Authorization Integration Boundary · Security DB Boundary

如需改变其中任何一项：
  登记 `FOUNDATION REGRESSION RISK` / `WAVE1 FOUNDATION CHANGE REQUIRED`
  → 停止该方向实现 → 单独影响评估与授权
```

---

# 8. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 8 份 · 见 Wave 2 文档集）
Runtime code = 0 · DB 写操作 = 0 · DDL / DML = 0 · migration = 0 ·
role / grant / revoke = 0 · commit / tag / push = 0
Wave 2 Implementation = NOT STARTED · Wave 2 Authorization = REQUIRED
```

**END OF P14 RUNTIME WAVE 2 SCOPE（2026-09-28 · HUMAN DECISION REQUIRED · 含 CONTRACT DIVERGENCE D-1…D-8 · 未实现 · HARD STOP ACTIVE）**
