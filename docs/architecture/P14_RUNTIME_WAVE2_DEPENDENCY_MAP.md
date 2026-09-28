# UAP — P14 RUNTIME WAVE 2 DEPENDENCY MAP

> ## 状态
>
> ```text
> 状态      = **HUMAN DECISION REQUIRED**（映射为候选 · 未实现）
> 依据      = P14_RUNTIME_SLICE_DEPENDENCY_MAP.md（既有 canonical 依赖模型）·
>             P14_RUNTIME_IMPLEMENTATION_DEPENDENCY_LOCK.md（DL-1…DL-5）·
>             Wave 1 FINAL ACCEPTANCE REPORT §28 Evidence Freeze
> 铁律      = **不新建第二套 dependency model**；本文件是既有模型的 Wave 2 展开
> ```

---

# 1. 主链（候选）

```text
Wave 1 Foundation（ACCEPTED · 冻结输入）
  Runtime Bootstrap · uap_runtime Connection · Connection Pool · Transaction Boundary ·
  Persistence Adapter · Lifecycle · Health · Observability · Error Taxonomy ·
  Authorization Integration Boundary
        ↓
Identity            （identity 建立 / 状态 / 唯一性 / 凭据关联 / 停用）
        ↓
Device              （enrollment / binding / revoke / replacement）
        ↓
Session             （creation / lifecycle / revoke / timeout）
        ↓
Authenticated Runtime Context（最小上下文：identity + device + session + actor +
                               tenant + space + authorization context）
        ↓
API Adaptation      （transport / adaptation only · 不含 business authority）
```

```text
与既有 P14_RUNTIME_SLICE_DEPENDENCY_MAP 的对应关系（同一模型 · 非新模型）：
  既有三层 Schema Layer → Authorization/Data Baseline → Runtime Layer
  Wave 2 展开 Runtime Layer 的内部顺序：Identity → Device → Session → Context → API
  （既有 Dependency Lock 的 DL-1…DL-5 全部继续生效）
```

---

# 2. 存储支链

```text
Security DB Boundary（ACCEPTED · uap_runtime 51 exact grants）
        ↓
Identity / Device / Session Persistence
        ↓
  users · identities · credentials · devices · sessions（既有 schema · 0017）
        ↓
uap_runtime（唯一 runtime 身份 · 只按已冻结授权面写入）
```

```text
授权面（已冻结 · 本 Wave **只消费**）：
  users       : S, I, U            （无 DELETE）
  identities  : S, I, U            （无 DELETE）
  credentials : S, I, U            （**无 DELETE** · SEC-08 无物理删除）
  devices     : S, I, U            （无 DELETE）
  sessions    : S, I, U, **D**     （唯一可用于物理清理的身份类对象之一）
  audit_logs  : S, I               （不可变 · 无 U/D）
  events      : S, I, U            （无 DELETE）
  roles/permissions/role_permissions/acl_subject_types/platform_* : S only
  tenants / spaces : S only（SEC-05 = SELECT ONLY）
```

---

# 3. Authorization 的插入位置（不新建模型 · 明确回答 §五）

```text
问题：Authorization 位于 Authenticated Runtime Context 之前还是之后？

答案（由既有 P14 Decision 与 Stage 2 架构决定，非本轮发明）：
  · SEC-P14-10 = **HYBRID**：Central Authorization Service + Restricted Runtime DB Read
  · DL-2：Authorization Precheck 必须位于 use-case 之前（centralized）
  · RUNTIME-G-04：centralized precheck + service mandatory enforcement
  · services/authorization/ = 唯一授权权威（只读 · 不缓存 · 不写库）

因此顺序为：

    Authentication（凭据/设备/会话校验）
            ↓
    Authenticated Runtime Context（最小、已验证的 subject）
            ↓
    Central Authorization（既有 Stage 2 · AuthorizationService）
            ↓
    Use-case（service 层 · 强制点）
            ↓
    Repository → uap_runtime

即：**Authorization 在 Authenticated Context 之后、Use-case 之前**。
明确禁止（AUTH-W2-02）：
    Authentication → handler if role == admin   ✗
```

```text
Context 与 Authorization 的接口形态（候选 · 待 Human 确认 = AUTH-W2-01/03）：
  Authenticated Context 只提供 **Subject 解析输入**（identity_id / user_id / device_id /
  session_id / tenant_id / space_id 等标识），
  Subject/Grant/AuthorizationRequest 的构造仍由既有 core.permission 契约承担
  ⇒ 不新增权限词表、不新增 subject 类型（SUBJECT_TYPES 冻结 = USER/ROLE/AGENT）
```

---

# 4. 依赖方向约束（沿用既有锁 + Wave 2 增补）

```text
DL-1  上层不得绕过下层（Repository 不得绕过 Connection Boundary 直连）        ← 继续生效
DL-2  Authorization Precheck 位于 use-case 之前                              ← 继续生效
DL-3  Bootstrap CLI 不得被 normal Runtime import / 调用 / 依赖                ← 继续生效
DL-4  任何环节不得引入 migration / 新 role / 新 grant（须独立授权）            ← 继续生效
DL-5  Security DB Boundary 已冻结；实施层不得修改                             ← 继续生效

W2-DL-1  Context 不得携带 credential / secret / hash（least privilege）      ← 候选
W2-DL-2  API 不得直接依赖 Repository（必须经 service）                        ← 候选
W2-DL-3  Identity 未定则不实现 Device；Device 未定则不实现 Session           ← 候选（待 §5）
W2-DL-4  任何新权限需求 → `SECURITY GRANT GAP` → 停止 → 独立 Security Decision ← 强制
W2-DL-5  任何新 schema 需求 → `SCHEMA DEPENDENCY DISCOVERED` → 停止 → 独立 Schema Decision ← 强制
```

---

# 5. 跨层影响扫描（0 泄漏检查）

```text
Core → Domain                = 0（core 不 import domains；架构守卫继续生效）
Wave 2 → Schema ownership    = 0（不创建/不拥有 schema 对象）
Wave 2 → 未来阶段（P15）泄漏   = 0（不创建 P15 文档/分支/编号）
Wave 2 → Wave 1 基础改写      = 0（若需要 ⇒ FOUNDATION REGRESSION RISK + STOP）
Wave 2 → 第二套 authorization = 0（必须复用 services/authorization）
Wave 2 → 第二套权限词表        = 0
Wave 2 → handler direct SQL   = 0
```

---

# 6. 并行分支（若 Human 裁定某 Decision 独立）

```text
候选并行关系（**不得**制造不存在的依赖）：
  · AUTH-W2-01/03（Stage 2 映射形态）可与 Identity 实现并行准备
  · API-W2-01（transport 定位）为独立宣言，不依赖 Identity 实现
  · SEC-W2-01…05（安全回归设计）可与实现并行编写（仅设计）
  · VOC-W2-* 为 **Root Blocker**：未裁决前 Identity/Device/Session 均不得进入实现
```

---

# 7. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 8 份）
未修改任何既有 dependency 载体（P14_RUNTIME_SLICE_DEPENDENCY_MAP /
P14_RUNTIME_IMPLEMENTATION_DEPENDENCY_LOCK 均未改写）
runtime code = 0 · DB 写 = 0 · migration = 0 · commit / tag / push = 0
```

**END OF P14 RUNTIME WAVE 2 DEPENDENCY MAP（2026-09-28 · HUMAN DECISION REQUIRED · Authorization 位于 Context 之后 / Use-case 之前 · HARD STOP ACTIVE）**
