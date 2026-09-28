# UAP — P14 RUNTIME WAVE 2 HUMAN DECISION SHEET

> ## 元数据
>
> ```text
> Stage           = P14_RUNTIME_WAVE2
> Baseline        = HEAD c420403d… · migration 0017_p13_seed · Wave 1 = ACCEPTED
> Decision status = **HUMAN DECISION RESOLVED**（36 项 · resolved 36 · unresolved 0 · UNKNOWN 0）
>                   → 权威记录见 §R **Resolution Registry**（2026-09-28 Human Freeze）
>                   → §1–§7 的历史候选方案与未勾选 checkbox **保留为历史，未删除、未勾选**
> 本轮性质         = 决策载体（**未实现** · 未改冻结正文 · 未改 0017 schema）
> 模板规则         = 每项给出 Question / Existing Facts / Frozen Constraints / Affected /
>                    Options / Required Follow-up / Human Decision / Human Notes
>                    **不得**出现 winner / recommended / best / preferred
> ID 完整性        = 与既有 D-* / SEC-P14-* / RTA-* / OQ-* / ID-P14-* 无重复
>                    （全仓扫描 `(ID|DV|SS|CTX|API|AUTH|SEC|VOC|SCOPE)-W2-\d+` = 0 命中）
> ```

---

# R. Resolution Registry（**权威记录** · 2026-09-28 Human Freeze）

> ```text
> 本 Registry 为 36 项 Decision 的**唯一权威裁决记录**；
> PDL 附录 P 为其 canonical registration（append-only）。
> 下文 §1–§7 的 Options 与 checkbox 保留为历史候选（未勾选）。
> Basis = EXPLICIT（Human 明文条款）/ DERIVED（由明文条款推导并注明出处）/
>        REPURPOSED（Human 以同一 ID 承载了与本 Sheet 原问题不同的裁定内容 —— 已明确标注）
> ```

| Decision | Selected | Basis | 一句话 Resolution |
|---|---|---|---|
| SCOPE-W2-01 | **REPURPOSED（§三）+ DERIVED** | EXPLICIT/DERIVED | 不修改 0017；采用 Persistence Adapter / Anti-Corruption Mapping；Identity+Device+Session+API 同轮 |
| VOC-W2-01 | **C 双根显式映射** | EXPLICIT §四/§五 | Domain 保持 Identity 语义中心；persistence anchor = `users.id` |
| VOC-W2-02 | **A 以 0017 词表为准** | EXPLICIT §七 | 仅实现 `password`；其余类型保持有效但不实现；Domain enum 经 mapping |
| VOC-W2-03 | **A 采用 5 态 persistence truth** | EXPLICIT §八 | pending/active/untrusted/revoked/lost；不得二值化 |
| VOC-W2-04 | **C 两套并存 + 显式映射** | EXPLICIT §九/§十/§十一 | user 5 态 + identity 4 态；禁止新增 persisted status |
| ID-W2-01 | **A public onboarding + 约束** | DERIVED §三十一/§三十六 | onboarding 可达，但匿名 caller 无额外权限 |
| ID-W2-02 | **A** | EXPLICIT §十 | identities：unverified→active→suspended→revoked |
| ID-W2-03 | **A 全局唯一**（trim+lower / 不敏感） | EXPLICIT §一 + live 复核 | 沿用既有唯一索引；不做 tenant-scoped |
| ID-W2-04 | **C 两者必填且一致** | EXPLICIT §六 + 0017 强制 | credential 同时绑定 identity 与 user |
| ID-W2-05 | **CUSTOM revoke 传播矩阵** | EXPLICIT §二十一/§三十六 | identity→revoked + 凭据 revoke + 同事务 session revoke；device 不自动改 |
| DV-W2-01 | **B** | EXPLICIT §十三 | eligible user + challenge + verification ⇒ active |
| DV-W2-02 | **B** | EXPLICIT §十二 | per-user fingerprint 唯一（既有约束）+ 应用层补充 |
| DV-W2-03 | **A 既有 schema 载体** | EXPLICIT §十四 | 不新增 device_challenges；否则 SCHEMA DEPENDENCY → STOP |
| DV-W2-04 | **A 同事务原子** | EXPLICIT §十五 | device→revoked 且其 active sessions→revoked，atomic |
| DV-W2-05 | **A 旧设备继续有效** | DERIVED §十二/§十六/§十八 | 不 auto-kick；并发 enrollment 需幂等/单次消费 |
| SS-W2-01 | **A** | EXPLICIT §十七 | human session 必须已验证设备（use-case 强制）；schema nullable 不改 |
| SS-W2-02 | **A** | EXPLICIT §十九/§二十 | active→expired/revoked；使用 replaced_by / absolute_expires_at |
| SS-W2-03 | **CUSTOM granular 矩阵** | EXPLICIT §二十一/§三十六 | 按触发源区分 granular / account-level |
| SS-W2-04 | **B 每设备多 session** | EXPLICIT §十八 | 不加 UNIQUE(device_id)；不自动踢旧登录 |
| SS-W2-05 | **B 部署配置参数** | EXPLICIT §二十 + DERIVED §二十九 | 双上限；refresh 不得延长 absolute；每次请求校验 |
| CTX-W2-01 | **A（字段名为 authentication assurance）** | EXPLICIT §二十二 + DERIVED §二十九 | context 最小组成 7 项；assurance 由前置链派生 |
| CTX-W2-02 | **CUSTOM fail-closed 矩阵** | EXPLICIT §二十三/§二十四/§二十五 | 无 active membership ⇒ DENY；多 candidate ⇒ 显式 context |
| CTX-W2-03 | **A 白名单** | EXPLICIT §二十二/§三十六 | 9 字段白名单；禁 secret/hash |
| CTX-W2-04 | **A** | EXPLICIT §二十二 | context 只带标识；AuthorizationRequest 由 service 构造 |
| AUTH-W2-01 | **REPURPOSED（§二十六）+ §二十七/§二十八/§二十九** | EXPLICIT | effect 只消费 allow/deny；REQUIRES_APPROVAL = DEFERRED |
| AUTH-W2-02 | **A** | EXPLICIT §三十/§二十七 | 判定只在 service + Stage 2；handler 仅适配 |
| AUTH-W2-03 | **A Wave 2 写 audit（关键事件）** | DERIVED §三十六 SEC-W2-02 + §二十一 | payload 白名单；不可变语义不改 |
| API-W2-01 | **A transport/adaptation only** | EXPLICIT §三十 | 无业务编排 / 无直接 DB / 无授权决策 |
| API-W2-02 | **A（同轮）** | EXPLICIT §三十一 | 路由面限定为 onboarding/enrollment/session/context/logout |
| API-W2-03 | **A** | EXPLICIT §三十 | HTTP→adapter→context→authz→service |
| API-W2-04 | **A 显式映射** | EXPLICIT §三十二 + DERIVED（Taxonomy） | 8 类失败全部 fail-closed；禁止 anonymous fallback |
| SEC-W2-01 | **REPURPOSED（§三十六）** | EXPLICIT + DERIVED | fail-closed DENY 清单；重复创建不披露存在性 |
| SEC-W2-02 | **REPURPOSED（§三十六）** | EXPLICIT | 六面禁泄露 secret |
| SEC-W2-03 | **REPURPOSED（§三十六）** | EXPLICIT + DERIVED | replay resistance（bounded / single-use / explicit consumption） |
| SEC-W2-04 | **REPURPOSED（§三十六）** | EXPLICIT + DERIVED | revoke 传播矩阵 + 事务边界 |
| SEC-W2-05 | **REPURPOSED（§三十六）** | EXPLICIT + DERIVED | no privilege expansion（无 role/grant/C2/CC-7 变更） |

```text
合计：36 / 36 RESOLVED · 0 PENDING · 0 UNKNOWN
REPURPOSED（Human 以该 ID 承载不同裁定内容）= **7 项**：
  SCOPE-W2-01（改为 Domain/Persistence Boundary）· AUTH-W2-01（改为 effect divergence）·
  SEC-W2-01（改为 authentication fail-closed）· SEC-W2-02（改为 no credential leakage）·
  SEC-W2-03（改为 replay resistance）· SEC-W2-04（改为 revoke propagation）·
  SEC-W2-05（改为 no privilege expansion）
完整逐项说明（Selected / Basis / Rationale / Affected boundary / Implementation consequence /
Related frozen decision / Contract impact / Schema impact）见 PDL **附录 P**。
```

---

# 0.0 文件结构说明（物理顺序 vs canonical 逻辑顺序）

> ```text
> 披露（诚实性要求 §三十八）：本轮以 append 方式把若干批次写入本文件时，
> 插入锚点选择有误，导致**章节的物理顺序**与逻辑批次顺序不一致。
> 内容**完整无损**：36 个 Decision 区块各出现且仅出现一次，无删除、无重复、无改写。
> 权威裁决记录 = §R Resolution Registry（文件开头）；本说明仅为可读性索引。
> 物理顺序问题登记为纯排版缺陷（cosmetic），非治理/内容缺陷，留待 BATCH-D 机械重排。
>
> 本文件物理顺序（自上而下）：
>   §R Registry → §0 批次表 → SCOPE-W2-01 →
>   Batch 4（CTX）→ Batch 5（AUTH）→ Batch 6（API）→ Batch 7（SEC）→
>   汇总与完整性声明 → Batch 2（DV）→ Batch 3（SS）→ VOC-W2-01…04 → Batch 1（ID）
>
> canonical 逻辑顺序（阅读建议）：
>   §R → §0 → Batch 0（SCOPE-W2-01 · VOC-W2-01…04）→ Batch 1（ID）→ Batch 2（DV）→
>   Batch 3（SS）→ Batch 4（CTX）→ Batch 5（AUTH）→ Batch 6（API）→ Batch 7（SEC）
> ```

---

# 0. 决策批次

```text
Batch 0  Governance / Root Blockers      SCOPE-W2-01 · VOC-W2-01…04      （5）
Batch 1  Identity                        ID-W2-01…05                     （5）
Batch 2  Device                          DV-W2-01…05                     （5）
Batch 3  Session                         SS-W2-01…05                     （5）
Batch 4  Authenticated Context           CTX-W2-01…04                    （4）
Batch 5  Authorization Integration       AUTH-W2-01…03                   （3）
Batch 6  API Adaptation                  API-W2-01…04                    （4）
Batch 7  Security / Abuse Boundary       SEC-W2-01…05                    （5）
                                                              合计 = **36**
```

---

# Batch 0 — Governance / Root Blockers

## SCOPE-W2-01 — Wave 2 节点组成

```text
Question
  Wave 2 到底包含哪些节点？（Identity / Device / Session / API 是否同轮）

Existing Facts
  · Domain 契约（core/identity|device|session|auth）与 schema（users/identities/
    credentials/devices/sessions）**均已存在** ⇒ 三者都属"实现 adapter/service"，非新建模型
  · services/ 仅有 authorization/ ⇒ identity/device/session 实现层为空
  · apps/api 仅有 health/meta；lifespan 未接 RuntimeApplication（Wave 1 已登记事实）

Frozen Constraints
  · 不得新建 schema 对象（RTA-10 = B）· 不得新建 role / grant（SEC-14）
  · Authorization 必须复用 Stage 2（不得第二套引擎）

Affected
  Wave 2 Scope · Dependency Map · Implementation Authorization Sheet

Options
  A. Identity + Device + Session（不含 API；API 留待 Wave 3）
  B. Identity + Device + Session + API Adaptation（同轮）
  C. Identity + Device（Session 留待 Wave 3）
  D. 仅 Identity
  E. CUSTOM（请写明）

Required Follow-up（任一选项都需要）
  · 选定组合后逐项落实 ID/DV/SS/CTX/AUTH/API 决策

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D   [ ] CUSTOM

Human Notes
```

---

# Batch 4 — Authenticated Runtime Context

## CTX-W2-01 — 认证事实枚举与映射

```text
Question
  `authentication` 事实的精确枚举名及其与 identity/device/session 状态的映射？

Existing Facts
  · P14_RUNTIME_AUTHENTICATED_CONTEXT_CONTRACT §3 给出候选枚举
    （UNVERIFIED / CREDENTIAL_VERIFIED / DEVICE_VERIFIED / SESSION_VERIFIED / REVOKED|EXPIRED）
  · 现行 schema 状态名见 VOC-W2-03/04（本 Sheet Batch 0）

Frozen Constraints
  · 不得新增与冻结状态名冲突的第二套命名 · 不得携带凭据材料

Affected
  Context · Session · Authorization · API · Acceptance

Options
  A. 采用 §3 候选枚举（并给出到 DB 状态的映射表）
  B. CUSTOM（须给出精确枚举名 + 映射表）

Human Decision
  [ ] A   [ ] B

Human Notes
```

## CTX-W2-02 — Tenant / Space 缺失与冲突的 fail-closed 语义

```text
Question
  tenant / space 无法确定、多个 membership 并存、inactive membership 时的具体行为？

Existing Facts
    · core/tenant 提供 TenantContext / require_same_tenant；core/space 提供 SpaceContext
    · DB：memberships / tenant_memberships（user_id + tenant_id + role_id）· 现存行为 0 行
    · **live 复核（2026-09-28）**：`ck_memberships_status` 与 `ck_tenant_memberships_status`
      均为 (invited, active, suspended, removed) —— **与 core `MEMBERSHIP_STATUS` 完全一致**
      ⇒ 该维度**无 Domain / Schema 分歧**
    · SEC-05：tenants / spaces = SELECT ONLY（runtime 不得创建/变更）

Frozen Constraints
  · 认证成功 ≠ tenant/space 授权（§十二 明文）· fail-closed 为默认

Affected
  Context · Authorization · API · Security

Human Decision（逐行）
  tenant 无法确定      ： [ ] DENY  [ ] 允许 PLATFORM scope  [ ] CUSTOM：__________
  space 无法确定        ： [ ] DENY  [ ] 由 use-case 决定  [ ] CUSTOM：__________
  多 membership 并存    ： [ ] 必须显式选择 active  [ ] 取最早/最新  [ ] CUSTOM：__________
  inactive membership  ： [ ] DENY  [ ] 需重新激活流程  [ ] CUSTOM：__________
  跨 tenant 访问         ： [ ] DENY（require_same_tenant）  [ ] CUSTOM：__________

Human Notes
```

## CTX-W2-03 — Observability 字段白名单

```text
Question
  context 中哪些字段可以进入 correlation / structured log / metrics？

Existing Facts
  · Wave 1：describe() 脱敏 · _safe_db_error() 遮蔽 · 既有 redaction 模块
  · SEC-P14-08：secret 不得进入 audit payload / exception / 普通日志

Frozen Constraints
  · 不得让 correlation context 承载认证材料（§十五 明文）

Affected
  Observability · Security · Acceptance

Options
  A. 白名单 = {correlation_id, session_id, device_id, identity_id, tenant_id, space_id,
               subject_type, scope, decision_effect}（**不含**任何 secret/hash）
  B. 更窄白名单（须列出）
  C. CUSTOM

Human Decision
  [ ] A   [ ] B（列出：__________）   [ ] C

Human Notes
```

## CTX-W2-04 — Context 携带 authorization 输入的粒度

```text
Question
  context 携带"完整 authorization 输入集合"，还是按 use-case 提供最小子集？

Existing Facts
  · core.permission.AuthorizationRequest 需要 subject / action / resource / scope 等
  · SEC-P14-03：EXPLICIT REQUIRED-READ ALLOWLIST · UNKNOWN → DENY · 禁止未来预授权
  · 既有 SubjectResolver 负责把标识解析为 ResolvedSubject

Frozen Constraints
  · 不得预授权 / 不得缓存判定 / 不得扩大 subject 面

Affected
  Context · Authorization · Service · Acceptance

Options
  A. context 只携带标识；AuthorizationRequest 由 service/use-case 逐次构造（最小面）
  B. context 携带构造好的 AuthorizationRequest（更少重复，但面更大）
  C. CUSTOM

Human Decision
  [ ] A   [ ] B   [ ] C

Human Notes
```

---

# Batch 5 — Authorization Integration

## AUTH-W2-01 — authenticated subject → Stage 2 映射形态

```text
Question
  Identity/Device/Session 完成后，service 如何把 authenticated subject 映射进既有 Stage 2？

Existing Facts
  · services/authorization：AuthorizationService · SubjectResolver/ResolvedSubject ·
    PolicyEngine · ToolGate · AuditBoundary（只读 · 不缓存 · 不写库）
  · core.permission.Subject(identity_id, subject_type, agent_id, actor_id, delegator_id)
    · SUBJECT_TYPES = (USER, ROLE, AGENT)
  · SEC-P14-10 = HYBRID
  · ⚠ **既有分歧 D-9（非 Wave 2 引入）**：`core.permission.EFFECTS` =
    (ALLOW, DENY, REQUIRES_APPROVAL)，而存储端 `role_permissions.effect` 仅 (allow, deny)
    （live 复核 2026-09-28）
    ⇒ 若 Wave 2 需直接消费 `role_permissions.effect` ⇒ 必须先裁决 D-9；
      若 Wave 2 完全经既有 AuthorizationService ⇒ **不阻断 Wave 2**

Frozen Constraints
  · 不得第二套 authorization engine · 不得新增 subject 类型 / action / effect
  · 必须 Authentication → Context → Central Authorization → Use-case

Affected
  Authorization · Context · Service · API · Acceptance

Options
  A. service 直接构造 core.permission.Subject 并调用 AuthorizationService（无新适配层）
  B. 新增薄 adapter（context → SubjectResolver 输入），不改 Stage 2 内部
  C. CUSTOM

Human Decision
  [ ] A   [ ] B   [ ] C

Human Notes
```

## AUTH-W2-02 — 禁止的旁路与判定位置

```text
Question
  确认禁止 handler 内 authorization 判断，以及强制点的确切位置？

Frozen Constraints（已冻结 · 仅需确认适用）
  · RUNTIME-G-04（centralized precheck + service mandatory enforcement）
  · DL-2（precheck 在 use-case 之前）· RUNTIME-G-05（handler 无 SQL）
  · AUTH-W2-02 明令禁止：Authentication → handler if role == admin

Options
  A. 确认：判定只在 service 层（+ Stage 2 内部），handler 仅适配
  B. CUSTOM

Human Decision
  [ ] A   [ ] B

Human Notes
```

## AUTH-W2-03 — Stage 2 只读语义与审计边界

```text
Question
  Wave 2 是否需要在授权判定后写入 audit（audit_logs INSERT 已授权）？由谁写？

Existing Facts
  · uap_runtime 对 audit_logs 有 SELECT + INSERT（无 UPDATE/DELETE · 不可变触发器）
  · services/authorization/audit.py = AuditBoundary（既有）
  · P14_SECURITY_IMPLEMENTATION_ACCEPTANCE_MAPPING：SEC-5 审计写入语义 = PLANNED

Frozen Constraints
  · 不得修改审计不可变语义（tg_audit_immutable）
  · 不得把 secret/hash 写入 audit payload（SEC-08）

Options
  A. Wave 2 写 audit（仅身份/设备/会话关键事件），写点集中在 service 层
  B. Wave 2 不写 audit（保持 PLANNED，留待后续 Wave）
  C. CUSTOM

Human Decision
  [ ] A   [ ] B   [ ] C

Human Notes
```

---

# Batch 6 — API Adaptation

## API-W2-01 — API 定位

```text
Question
  确认 API = transport / adaptation（非 business orchestration）？

Existing Facts
  · apps/api 仅有 health / meta；lifespan 未接 RuntimeApplication（Wave 1 登记事实）
  · RUNTIME-G-05：handler 无 direct SQL

Options
  A. 确认 A：transport / adaptation only（不得含业务编排 / 不得直接 DB）
  B. CUSTOM

Human Decision
  [ ] A   [ ] B

Human Notes
```

## API-W2-02 — API 是否与 Wave 2 同轮

```text
Question
  API 是否与 Identity/Device/Session 同轮实现？

Options
  A. Yes（同轮）
  B. No（先完成 service 层，API 留待后续）
  C. CUSTOM

Affected
  Wave 2 Scope · Acceptance · Test Governance

Human Decision
  [ ] A   [ ] B   [ ] C

Human Notes
```

## API-W2-03 — 认证信息进入 service 的通路

```text
Question
  认证信息如何进入 service？（确认既定链路）

Proposed chain（既有架构）
  HTTP request → authentication adapter → authenticated context →
  authorization → service

Frozen Constraints
  · 禁止 handler → direct DB · 禁止 handler 内授权判断

Options
  A. 确认上述链路（API 侧只做 adapter）
  B. CUSTOM

Human Decision
  [ ] A   [ ] B

Human Notes
```

## API-W2-04 — 错误映射

```text
Question
  API 层如何把 Wave 1 Error Taxonomy 的 8 类映射为 HTTP 语义？

Existing Facts
  · Wave 1 taxonomy：configuration / connection / persistence / transaction /
    authorization / authentication / security_boundary / unexpected
  · 现有 health/meta 路由为唯一既有 API 面

Frozen Constraints
  · 必须与既有 Error Taxonomy 一致（不得新建第二套错误体系）
  · authentication / authorization / security_boundary 的响应**不得**泄露内部结构或凭据

Options
  A. 建立显式映射表（8 类 → HTTP 状态 + 错误码），并对 security 类统一模糊化
  B. CUSTOM（须给出映射表）

Human Decision
  [ ] A   [ ] B
  conflict（唯一性冲突）语义：__________
  validation failure 语义：__________

Human Notes
```

---

# Batch 7 — Security / Abuse Boundary

## SEC-W2-01 — 重复 identity 创建

```text
Question
  重复创建（同一 identifier）时的行为与可观测性？

Options
  A. 拒绝并返回 conflict（不泄露该 identifier 是否已存在）
  B. 拒绝并明确告知已存在
  C. CUSTOM

Human Decision
  [ ] A   [ ] B   [ ] C

Human Notes
```

## SEC-W2-02 — Onboarding abuse / replay 边界

```text
Question
  覆盖范围与限流语义？（§十四 清单）

Required coverage（清单 · 需逐项确认）
  [ ] repeated enrollment attempts
  [ ] expired challenge reuse
  [ ] replayed credential setup
  [ ] device enrollment replay
  [ ] session fixation
  [ ] revoked credential reuse
  [ ] revoked device reuse
  [ ] concurrent onboarding

原则（已冻结）：fail closed + **bounded retry**（不得无限重试）

Human Decision
  限流载体： [ ] 应用层有界计数  [ ] 既有 credentials.failed_attempts / locked_until
            [ ] CUSTOM：__________
  bounded retry 上限：__________

Human Notes
```

## SEC-W2-03 — 跨租户 / 越权访问的 fail-closed 证明要求

```text
Question
  Wave 2 验收必须证明哪些 deny 路径？（§二十五 Authorization 面）

Required（候选）
  [ ] unauthorized tenant · [ ] unauthorized space · [ ] unauthorized resource
  [ ] default deny · [ ] deny precedence

Human Decision
  [ ] 确认上述清单    [ ] CUSTOM：__________

Human Notes
```

## SEC-W2-04 — Credential / secret 边界落点

```text
Question
  逐项确认 secret 的可达面（§十五）

Required 逐项裁定
  credential hash 存放位置 ：__________（候选：仅 credentials.secret_hash）
  challenge / token 存放位置 ：__________（取决于 DV-W2-03）
  允许进入 operational log 的字段 ：__________
  允许进入 audit log 的字段     ：__________
  允许进入 request context 的字段：__________
  允许进入 exception 文本的字段  ：__________（候选：无 secret 类字段）

Human Decision
  [ ] 接受上述"禁止进入"约束（password/token/credential/secret/full DSN/hash/raw payload）
  [ ] CUSTOM

Human Notes
```

## SEC-W2-05 — Credential algorithm 与 rotation 参数

```text
Question
  Wave 2 使用哪些 algorithm？rotation / expire 的具体参数？

Existing Facts
  · DB `credentials.algorithm NOT NULL ∈ (argon2id, scrypt, sha256_hmac)`
  · SEC-08：Argon2id 语义（P14 安全裁决）
  · DB 有 rotated_at / expires_at / revoked_at / failed_attempts / locked_until

Options
  A. algorithm = argon2id（其余不授予使用路径）
  B. 多 algorithm 允许（列出集合）
  C. CUSTOM

Human Decision
  [ ] A   [ ] B（集合：__________）   [ ] C
  rotation 周期：__________   默认 expire：__________
  failed_attempts 阈值：__________   locked_until 策略：__________

Human Notes
```

---

# 汇总与完整性声明

```text
决策总数           = **36**
  Batch 0（Governance/Root）5 · Batch 1（Identity）5 · Batch 2（Device）5 ·
  Batch 3（Session）5 · Batch 4（Context）4 · Batch 5（Authorization）3 ·
  Batch 6（API）4 · Batch 7（Security）5

已填 Decision      = **36 / 36**（**§R Resolution Registry 为权威记录**；
                      §1–§7 的历史 checkbox **保持未勾选**，仅作候选留档）
Unresolved         = **0**
ID 唯一性           = 无重复 · 无与既有 D-*/SEC-P14-*/RTA-*/OQ-* 冲突（全仓扫描 0 命中）
Root Blockers       = SCOPE-W2-01 · VOC-W2-01…04（未裁决前 Identity/Device/Session
                      ⇒ **已全部裁决**（见 §R 与 PDL 附录 P）；Root Blocker 解除，
                        但 Wave 2 Implementation 仍需 W2-AUTH-01…07 单独授权
Schema 复核          = 5 项 VERIFICATION PENDING **已全部完成**（live catalog 只读）
                      （见 SCHEMA_DEPENDENCY_REGISTER §3；未产生新 schema dependency）
新增既有分歧          = **D-9**（`role_permissions.effect` 仅 allow/deny，无法表达
                      `core.permission.EFFECTS` 的 REQUIRES_APPROVAL）
                      ⇒ 已由 AUTH-W2-01 裁决为 **DEFERRED / OUT OF SCOPE**（不阻断 Wave 2）
```

```text
本 Sheet 不含任何 implementation / DDL / DML / grant / role 动作；
§1–§7 的 Options 与 checkbox 为**历史候选**（未勾选）；正式裁决见 §R。
```

**END OF P14 RUNTIME WAVE 2 HUMAN DECISION SHEET — §1–§7 历史候选部分（2026-09-28 · 36 sections intact · checkboxes 未勾选）**

> 本文件的**权威裁决记录 = §R Resolution Registry**（文件开头）；
> canonical registration = `PLATFORM_DECISION_LOG.md` **附录 P**。

---

# Batch 2 — Device

## DV-W2-01 — Enrollment authority

```text
Question
  谁可以注册 device？

Existing Facts
  · core/device.DeviceRegistry.register(identity_id, fingerprint, label)
  · DB `devices.user_id NOT NULL` + `fingerprint NOT NULL`；status default 未在契约枚举
  · uap_runtime：devices S/I/U（无 DELETE）
  · 现行仓库无 enrollment 实现

Frozen Constraints
  · 不得默认匿名 caller 可注册设备（与 ID-W2-01 同源）
  · 不得新建 device challenge 表（RTA-10）⇒ challenge 载体须由 Human 指定

Affected
  Device · Session（创建前置）· Security（replay / abuse）

Options
  A. 仅 authenticated identity 可注册自身设备
  B. authenticated identity + 显式 challenge 校验
  C. operator-assisted（运维代为登记）
  D. CUSTOM

Required Follow-up
  · DV-W2-03（challenge 载体与过期/replay 语义）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```

## DV-W2-02 — Device ownership

```text
Question
  "one device → one user / one user → many devices" 的判定，DB 约束与
  应用规则各自承担什么？

Existing Facts
  · **live 复核（2026-09-28）**：
      `devices_pkey(id)` · `uq_devices_fingerprint` = **UNIQUE (user_id, fingerprint)**
      · `ix_devices_user_status(user_id, status)` · `fk_devices_user ON DELETE CASCADE`
    ⇒ fingerprint 唯一性是 **per-user**（同一用户内唯一）；
      **未禁止**跨用户复用同一 fingerprint（无全局唯一约束）
    ⇒ device 归属列为 `user_id`（**非** identity_id）
  · `sessions.device_id FK devices ON DELETE CASCADE`（`device_id` 可空）

Frozen Constraints
  · 不得新建 index / constraint（RTA-10）
  · 若确需 DB 层约束 ⇒ **SCHEMA DEPENDENCY** → STOP

Affected
  Device · Session · Persistence · Security（跨用户指纹复用）

Options
  A. 完全依赖应用层规则（fingerprint 唯一性由 service 判定）
  B. 依赖既有 DB 约束 + 应用层补充
  C. CUSTOM

Required Follow-up
  · 「跨用户复用同一 fingerprint」是否需要禁止？若是 ⇒ 既有 DB **无法表达**
    ⇒ `SCHEMA DEPENDENCY` → STOP（独立 Schema Decision）

Human Decision
  [ ] A   [ ] B   [ ] C

Human Notes
```

## DV-W2-03 — Enrollment challenge

```text
Question
  challenge 的创建 / 过期 / 防重放 / 重试上限 / 一次性消费 / 失败处理？

Existing Facts
  · 现行 schema **无** challenge 表 / token 表（仅 credentials.secret_hash、
    sessions.token_hash / refresh_token_hash）
  · core/device 与 core/auth 契约中**无** challenge 类型

Frozen Constraints
  · 不得新建表/函数（RTA-10）⇒ challenge 载体只能是：
       (i) 既有 credentials 行（type 指定）· 或
       (ii) 有界内存/签名令牌（无持久化）· 或
       (iii) 独立 Schema Decision

Affected
  Device · Security（replay / abuse）· Persistence

Options
  A. 以 `credentials` 行承载 challenge（type 取自 VOC-W2-02 选定词表 · 一次性消费）
  B. 无状态签名 challenge（TTL + 绑定 identity/fingerprint，不落库）
  C. CUSTOM
  D. 判定必须新增 schema object ⇒ 登记 SCHEMA DEPENDENCY 并进入独立 Schema Decision

Required Follow-up
  · expiring / replay prevention / retry bound / consumed-on-success / failed attempts
    的具体参数须同时裁定（否则实现无法确定语义）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D
  TTL（秒）：__________   重试上限：__________   失败后动作： [ ] 拒绝并保留  [ ] 锁定  [ ] CUSTOM

Human Notes
```

## DV-W2-04 — Device revoke

```text
Question
  device revoke 是否 **原子** 触发 active session revoke？

Existing Facts
  · core/device："Revocation is explicit and irreversible: a revoked device can
    never authenticate again."
  · DB：`sessions.device_id FK devices ON DELETE CASCADE`（**仅 DELETE 级联，
    不覆盖 status 置 revoked**）· `devices.revoked_at` / `revoked_reason` 存在
  · uap_runtime：devices U · sessions U/D（已授权）⇒ 可在**同一事务**内完成
  · P14 既有决策（DC-19 / UC-3,UC-5）已把"device revoke + active session 撤销"
    列为需要原子性的复合动作

Frozen Constraints
  · 事务边界由 service 拥有（DC-16/19）· 不得用触发器实现（RTA-10）

Affected
  Device · Session · Transaction Boundary（复用 Wave 1）· Security

Options
  A. 原子：同一事务内置 devices.status=revoked + 其 active sessions revoke（软撤销）
  B. 原子：置 revoked + **物理 DELETE** active sessions（uap_runtime 有 DELETE）
  C. 非原子：先置 revoked，异步清理 session
  D. CUSTOM

Required Follow-up
  · SS-W2-03（各类 revoke 对 session 的影响矩阵）· ID-W2-05（identity 侧连带）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```

## DV-W2-05 — Device replacement

```text
Question
  新设备加入后旧设备是否仍有效？并发 enrollment 行为？

Existing Facts
  · P14 已冻结：`one user → many devices`（多设备并存）
  · 并发 enrollment 无既有实现；DB 无 enrollment 唯一约束

Frozen Constraints
  · 不得新建约束/索引（RTA-10）
  · 不得把"多设备并存"自动推导为"新设备替换旧设备"

Affected
  Device · Session · Security

Options
  A. 旧设备继续有效（并存；需显式 operator revoke 才失效）
  B. 新设备加入即自动 revoke 旧设备（单设备策略）
  C. 按 platform policy 区分（默认 A，特定 use-case 走 B）
  D. CUSTOM

Required Follow-up
  · 并发 enrollment 的串行化 / 幂等语义须同时裁定

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```

---

# Batch 3 — Session

## SS-W2-01 — Session creation authority

```text
Question
  session 由谁创建、依据什么前置条件？

Existing Facts
  · core/session.SessionStore.create(identity_id, device_id, ttl_seconds)
  · **live 复核（2026-09-28）**：`user_id NOT NULL` · `identity_id NOT NULL` ·
    **`device_id` 可空（nullable = YES）** · `token_hash NOT NULL` · `expires_at NOT NULL` ·
    `ck_sessions_expiry(expires_at > created_at)` · FK：device CASCADE / identity RESTRICT /
    user CASCADE
    ⇒ 「session 必须绑定已验证设备」**无法由既有 schema 表达**（DB 允许 device_id = NULL）
      ⇒ 必须由应用层保证；若要求 DB 层强制 ⇒ `SCHEMA DEPENDENCY` → STOP
  · uap_runtime：sessions S/I/U/D（唯一含 D 的身份类对象之一）

Frozen Constraints
  · Session 创建必须依赖 authenticated identity + verified device（§八 明文）
  · 不得由任意 handler 直接创建（RUNTIME-G-05）

Affected
  Session · Device · Identity · API · Security

Options
  A. service 层在 **已验证身份 + 已验证设备** 后创建（atomic）
  B. service 层在已验证身份后创建（设备可选，device_id = NULL）
  C. CUSTOM

注：选项 A 与 B 在既有 schema 下**均可实现**；差异完全落在应用层约束，DB 不作强制。

Required Follow-up
  · SS-W2-02 / SS-W2-04（并发与替换）· CTX-W2-01（认证事实枚举）

Human Decision
  [ ] A   [ ] B   [ ] C

Human Notes
```

## SS-W2-02 — Session lifecycle

```text
Question
  session 的精确状态与转移？

Existing Facts
  · core/session：`SESSION_STATUS = ("active","expired","revoked")`
  · DB：`ck_sessions_status: status ∈ (active, expired, revoked)` —— **两边一致**
  · DB 另有 revoked_at / revoked_reason / replaced_by / last_used_at /
    absolute_expires_at（**core 契约未表达**）

Frozen Constraints
  · 以冻结契约为准（此处两边一致 ⇒ 采用 active / expired / revoked）

Affected
  Session · Persistence · Acceptance

Options
  A. 严格采用 (active, expired, revoked)，并显式定义 DB 附加字段与状态的对应
  B. CUSTOM（须给出附加字段语义）

Required Follow-up
  · SS-W2-05（timeout 参数）· swapped_by / replaced_by 是否使用

Human Decision
  [ ] A   [ ] B
  replaced_by 使用： [ ] 使用  [ ] 不使用   absolute_expires_at 使用： [ ] 使用  [ ] 不使用

Human Notes
```

## SS-W2-03 — Session revocation matrix

```text
Question
  identity revoke / device revoke / credential revoke / explicit logout /
  administrator revoke 分别对 session 有什么影响？

Existing Facts
  · core/session.SessionStore：revoke(session_id) · revoke_all_for_identity(identity_id)
  · DB 无 session 级联触发器；sessions.device_id 仅 ON DELETE CASCADE
  · uap_runtime 可在同事务内 UPDATE / DELETE sessions（已授权）

Frozen Constraints
  · 不得新增触发器（RTA-10）· 事务语义由 service 拥有

Affected
  Session · Device · Identity · Security · Acceptance

Options（逐触发源分别选择）
  A. 同事务原子撤销相关 active sessions
  B. 不撤销，但认证/授权时判定失败（fail-closed 由判定承担）
  C. CUSTOM

Human Decision（逐行）
  identity revoke      ： [ ] A  [ ] B  [ ] C
  device revoke        ： [ ] A  [ ] B  [ ] C
  credential revoke    ： [ ] A  [ ] B  [ ] C
  explicit logout      ： [ ] A  [ ] B  [ ] C
  administrator revoke ： [ ] A  [ ] B  [ ] C

Human Notes
```

## SS-W2-04 — Session concurrency

```text
Question
  多设备并存时 session 并发策略？同一设备是否允许多 session？替换与 refresh 行为？

Existing Facts
  · P14 已冻结：one user → many devices（**未**裁定 one device → many sessions）
  · **live 复核（2026-09-28）**：`sessions` **无** (device_id) 唯一约束（仅 `sessions_pkey`）；
    `replaced_by` 字段存在但语义未定
    ⇒ 并发策略**只能由应用层保证**（DB 不提供约束）
  · core/session 契约未表达并发限制

Frozen Constraints
  · 不得新建约束/索引（RTA-10）⇒ 并发策略只能由应用层实现

Affected
  Session · Device · Security · Acceptance

Options
  A. 每设备一个 active session（新 session 替换旧的，`replaced_by` 记录）
  B. 每设备允许多个 active session
  C. 每用户一个 active session（跨设备互斥）
  D. CUSTOM

Required Follow-up
  · refresh 行为（refresh_token_hash 是否使用 · 是否滚动）须同时裁定

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D
  refresh： [ ] 滚动 refresh  [ ] 不滚动  [ ] 不使用 refresh token

Human Notes
```

## SS-W2-05 — Session timeout

```text
Question
  idle timeout / absolute timeout / refresh lifetime / clock / revocation 传播？

Existing Facts
  · DB 有 `expires_at NOT NULL`（ck: expires_at > created_at）、`absolute_expires_at`（可空）、
    `last_used_at`（可空）、`revoked_at`
  · core/session.SessionStore.create(..., ttl_seconds) —— **契约未冻结具体秒数**

Frozen Constraints
  · 具体参数未冻结 ⇒ 必须由 Human Decision 明确（§八 明文）
  · 不得把参数写入 schema / GUC

Affected
  Session · Security · Observability（时钟/时区）· Acceptance

Options
  A. 给出显式数值（idle / absolute / refresh TTL）
  B. 由部署配置提供（沿用既有 settings 通道）， Wave 2 只定义语义与默认值
  C. CUSTOM

Human Decision
  [ ] A   [ ] B   [ ] C
  idle timeout（秒）：__________
  absolute timeout（秒）：__________
  refresh lifetime（秒）：__________
  时钟处理： [ ] UTC only（推荐冻结语义）  [ ] CUSTOM：__________
  revocation 传播： [ ] 即时（每次请求校验）  [ ] 有界延迟：__________

Human Notes
```


## VOC-W2-01 — 聚合根（identity-centric vs user-centric）

```text
Question
  Wave 2 的 identity 聚合根是 `users` 还是 `identities`？（D-1）

Existing Facts
  · Domain 契约：`Device.identity_id`、`Session(identity_id, device_id)`；core **无 User 契约**
  · 实测 schema：`devices.user_id`（无 identity_id 列）· `sessions.user_id + identity_id`
    · `identities.user_id NOT NULL FK users` · `users.primary_identity_id`
  ⇒ 两层**聚合根不同**

Frozen Constraints
  · 不得修改既有 schema（RTA-10）· 不得重写 core 契约语义（FILE_INVENTORY：core 契约冻结）

Affected
  Identity · Device · Session · Persistence · Authenticated Context（user_id 是否必需）

Options
  A. user-centric 为准（DB 聚合根）：Wave 2 以 users 为主，identity 为其中一种身份记录
  B. identity-centric 为准：Wave 2 以 identities 为主，users 作为 profile 载体
  C. 双根显式映射：定义 canonical 映射（1 user : N identities）并在契约层显式登记
  D. CUSTOM

Required Follow-up
  · 决定 Context 是否携带 user_id（CTX-W2-04）· 决定 Device 归属语义（DV-W2-02）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```

## VOC-W2-02 — Credential type 词表

```text
Question
  Wave 2 采用哪一套 credential type 词表？（D-2）

Existing Facts
  · core/auth：`CREDENTIAL_TYPES = ("password","token","api_key","device")`
  · DB：`credentials.type ∈ (password, api_key, recovery_code, device_cert, otp)`
  ⇒ 两集合**不同**（core 有 token/device；DB 有 recovery_code/device_cert/otp）
  · DB `credentials.algorithm` NOT NULL ∈ (argon2id, scrypt, sha256_hmac)

Frozen Constraints
  · SEC-08：NO PLAINTEXT · Argon2id 语义已冻结 · 无物理删除

Affected
  Identity（凭据关联）· Session（会话凭据）· Persistence · Security Regression

Options
  A. 以 DB 词表为准（recovery_code / device_cert / otp 可表达），core 契约作映射层
  B. 以 core 词表为准（仅 4 类），DB 的额外类别 Wave 2 不使用
  C. 显式双向映射表（并登记未使用类别）
  D. CUSTOM

Required Follow-up
  · algorithm 选择策略（SEC-W2-05）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```

## VOC-W2-03 — Device status 词表

```text
Question
  Wave 2 如何处理 core 与 DB 的 device status 差异？（D-3）

Existing Facts
  · core/device：`DEVICE_STATUS = ("pending","active","revoked")`
  · DB：`devices.status ∈ (pending, active, untrusted, revoked, lost)`
  · core 声明"revocation is explicit and irreversible"

Frozen Constraints
  · 不得新造第三套状态名 · 不得改 schema

Affected
  Device · Session（device 失效连带）· Security Regression

Options
  A. 以 DB 5 态为准（untrusted / lost 需定义语义与转移）
  B. 以 core 3 态为准，DB 的 untrusted / lost 在 Wave 2 定义为不可达态
  C. 5 态为准但仅实现 3 态的转移，另 2 态登记为后续
  D. CUSTOM

Required Follow-up
  · DV-W2-04（revoke 原子性）· SS-W2-03（revoke 对 session 的影响）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```

## VOC-W2-04 — Identity / User 状态词表

```text
Question
  identity 与 user 的状态机采用哪一套？（D-4 / D-6）

Existing Facts
  · core/identity：`Identity.status` 默认 "active"（**无枚举**）
  · DB `identities.status ∈ (active, unverified, suspended, revoked)`
  · DB `users.status ∈ (pending, active, suspended, locked, deleted)`
  · 指令 §六 举例的 `pending → verified → active` **不存在于**任何现行契约或 schema

Frozen Constraints
  · 禁止生成第二套状态机（§六 明文）· 不得改 schema

Affected
  Identity · Session · Security Regression · Acceptance

Options
  A. 采用 DB `identities.status` 四态为准（unverified 承担"待验证"语义）
  B. 采用 DB `users.status` 五态为准（pending 承担"待激活"）
  C. 两套并存但显式映射（identity 状态 + user 状态各自语义）
  D. CUSTOM（须给出精确状态名集合）

Required Follow-up
  · ID-W2-02（状态机）· ID-W2-05（disable/revoke）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D（须写明状态名集合）

Human Notes
```

---

# Batch 1 — Identity

## ID-W2-01 — Identity creation authority

```text
Question
  谁可以创建 identity？

Existing Facts
  · core/identity.IdentityResolver 只有 get_by_id / resolve（**无 create**）
  · DB：uap_runtime 对 users / identities 有 INSERT（已授权）
  · 现行仓库**不存在** identity creation 的实现或路径

Frozen Constraints
  · 不得默认任何匿名 caller 具有 identity creation privilege（§六 明文）
  · SEC-05：tenants / spaces = SELECT ONLY（不得借此创建 tenant/space）

Affected
  Identity · Device（enrollment 前置）· API（onboarding 入口）· Security

Options
  A. public onboarding path（匿名可达，但受 abuse boundary 约束）
  B. operator-assisted path（需既有权威身份）
  C. existing membership authority（须已是某 tenant 的 active member）
  D. CUSTOM

Required Follow-up
  · SEC-W2-01（重复创建）· SEC-W2-02（onboarding abuse）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```

## ID-W2-02 — Identity state machine

```text
Question
  identity 的精确状态与转移是什么（以冻结契约/schema 为准）？

Existing Facts
  · 见 VOC-W2-04（现行只有 DB 两套枚举；core 未枚举）
  · core/identity 的 `Identity.kind ∈ (user, service, device_subject)`

Frozen Constraints
  · 禁止第二套状态机 · 状态名必须取自冻结契约或 schema

Affected
  Identity · Session（active 判定）· Acceptance

Options
  A. 采用 VOC-W2-04 选定集合，Wave 2 只实现该集合内的转移
  B. CUSTOM（列出 状态集合 + 允许转移表）

Required Follow-up
  · 需与 VOC-W2-04 一致（不得冲突）

Human Decision
  [ ] A   [ ] B

Human Notes
```

## ID-W2-03 — Identity uniqueness

```text
Question
  唯一性判定范围与规则？

Existing Facts
  · DB `ck_users_login`：`users` 必须至少有 email 或 username
  · **live 复核（2026-09-28）**：已存在 `uq_users_email` = UNIQUE (lower(email))
    WHERE deleted_at IS NULL；`uq_users_username` = UNIQUE (lower(username))
    WHERE deleted_at IS NULL
    ⇒ 既有唯一性为 **全局**（无 tenant 维度）· **大小写不敏感**（lower）·
      **软删除后释放**（partial index）
  · tenants/spaces 为 SELECT ONLY；跨 tenant 语义无既有实现

⚠ 与既有 DB 行为的张力
  · 选项 B/C（tenant 范围内唯一 / 混合）**与既有 DB 唯一索引冲突**：
    `users` 表无 tenant 列，且索引已全局生效 ⇒ 若要 tenant-scoped 唯一性，
    必须另行裁决（可能触发 SCHEMA DEPENDENCY → STOP）
  · 归一化与大小写敏感性**已由 DB 事实约束**（trim 未由 DB 表达 · lower 已表达）

Frozen Constraints
  · 不得新建 unique index（RTA-10）⇒ 唯一性只能依赖既有约束 + 应用层规则

Affected
  Identity · Persistence · Security（重复创建）· Acceptance

Options
  A. 全局唯一（cluster-wide：email / username）
  B. tenant 范围内唯一（需要 tenant 归属 + 应用层校验）
  C. 混合（identity identifier 全局唯一；tenant 内 username 唯一）
  D. CUSTOM

Required Follow-up
  · 归一化 / 大小写 / 重复检测细节须同时裁定（否则 Wave 2 无法实现）
  · 若需 DB 层约束 ⇒ **SCHEMA DEPENDENCY** → STOP（独立 Schema Decision）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D
  normalization： [ ] 无  [ ] trim+lower  [ ] CUSTOM：__________
  case sensitivity： [ ] 敏感  [ ] 不敏感

Human Notes
```

## ID-W2-04 — Credential association

```text
Question
  credential ↔ identity 的关联与凭据生命周期？

Existing Facts
  · DB `credentials.identity_id`（FK identities）**且** `credentials.user_id`（FK users）
  · algorithm NOT NULL ∈ (argon2id, scrypt, sha256_hmac)
  · uap_runtime：credentials S/I/U（**无 DELETE**）

Frozen Constraints
  · SEC-08：NO PLAINTEXT / Argon2id / revoke+expire（无物理删除）

Affected
  Identity · Session · Persistence · Security

Options
  A. credential 挂 identity（identity_id 必填；user_id 由 identity 派生）
  B. credential 挂 user（user_id 必填；identity_id 由 user 派生）
  C. 两者必填且需一致（应用层校验）
  D. CUSTOM

Required Follow-up
  · VOC-W2-02（type 词表）· SEC-W2-05（algorithm / rotation 参数）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```

## ID-W2-05 — Identity disable / revoke

```text
Question
  identity 停用 / 撤销的语义，以及是否强制连带 device / session 撤销？

Existing Facts
  · core/session.SessionStore 只有 `revoke_all_for_identity`（**无 device 连带**）
  · DB `sessions.identity_id FK ON DELETE RESTRICT`（不得因 identity 删除而级联）
  · DB `devices.user_id FK ON DELETE CASCADE`（user 删除会级联 device）
  · DB `identities` 有 revoked_at / status；`devices` 有 revoked_at / revoked_reason

Frozen Constraints
  · 无物理删除语义（SEC-08 仅针对 credential；identity/user 的删除语义本轮未冻结）
  · 不得新建触发器 / 函数（RTA-10）

Affected
  Identity · Device · Session · Security · Acceptance

Options
  A. soft-disable：置 status，凭据 revoke，**同事务**连带撤销 device + active sessions（atomic）
  B. soft-disable：置 status + 凭据 revoke，session 保持但认证时判定失败
  C. 分阶段：disable 与 revoke 为两个独立操作
  D. CUSTOM

Required Follow-up
  · SS-W2-03（revoke 传播）· DV-W2-04（device revoke 原子性）

Human Decision
  [ ] A   [ ] B   [ ] C   [ ] D

Human Notes
```
