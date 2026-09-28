# UAP — P14 RUNTIME AUTHENTICATED CONTEXT CONTRACT

> ## 状态
>
> ```text
> 状态      = **DECISION PREPARATION**（设计候选 · 未实现 · 未冻结）
> 依据      = SEC-P14-06/07/10 · RUNTIME-G-04…06 · core.permission 契约（冻结）·
>             core.identity / core.device / core.session / core.auth 契约 ·
>             P14_RUNTIME_IMPLEMENTATION_DEPENDENCY_LOCK（DL-2）
> 铁律      = **least privilege**：不得把整行 DB record / credential 对象塞入 request context
> ```

---

# 1. 目的

```text
回答一个问题：请求进入 Runtime 之后，Service / use-case 到底拿到**什么最小上下文**？

设计目标
  CT-1 只携带**标识 + 已验证事实 + 授权输入**，不携带任何 secret 或其派生值
  CT-2 足以构造既有 core.permission 的 Subject / Grant / AuthorizationRequest
  CT-3 不引入第二套 subject / scope / action 词表
  CT-4 可被既有 services/authorization 直接消费（不改造 Stage 2）
  CT-5 任何缺失 / 不确定 ⇒ **FAIL CLOSED**（RUNTIME-G-06）
```

---

# 2. 上下文成员（候选 · 字段级）

```text
字段                类型/来源                              是否必需  说明
------------------------------------------------------------------------------------------------
identity_id         uuid（identities.id）                  必需      Verified identity 标识
user_id             uuid（users.id）                       条件必需   ⚠ 取决于 VOC-W2-01（聚合根）
device_id           uuid（devices.id）| None                条件必需   设备绑定会话时必需
session_id          uuid（sessions.id）| None               条件必需   已建立会话时必需
actor_type          枚举 STRING（Human 裁定候选）            必需      actor 语义（见 §18 未决项）
subject_type        ∈ core.permission.SUBJECT_TYPES          必需      冻结词表：USER / ROLE / AGENT
tenant_id           uuid | None                             条件必需   见 §4 / SEC-W2-03
space_id            uuid | None                             条件必需   见 §4 / SEC-W2-03
scope               ∈ core.permission.STORED_SCOPES          必需      冻结词表：PLATFORM / TENANT / SPACE
correlation_id      str（既有 observability 上下文）          必需      仅用于日志关联（非信任判据）
authentication      "已完成的认证事实"（枚举 · 见 §3）         必需      不含凭据材料
authorization       AuthorizationRequest 的**输入位**（非决策结果） 必需   决策仍由 Stage 2 作出
```

```text
明确**不得**出现在 context 中（§十五 credential / secret 边界）：
  · 任何 credential 明文 · secret_hash · token_hash · refresh_token_hash
  · 任何 private key / 设备公钥之外的材料
  · 完整 DB row（users/identities/credentials/devices/sessions 的整行对象）
  · 原始 DSN · 口令 · session token 原文
  · 任何"用于跳过授权"的判据（如 application_name / GUC / 角色名直判）
```

---

# 3. `authentication` 事实（枚举 · 候选）

```text
值                     含义                                        信任来源
-----------------------------------------------------------------------------------
UNVERIFIED              无凭据 / 未认证（默认拒绝路径）               —
CREDENTIAL_VERIFIED     identity 凭据校验通过（SEC-08 无物理删除语义）  credentials.secret_hash 校验
DEVICE_VERIFIED         device 绑定已激活（devices.status = active）     实测约束见 §18
SESSION_VERIFIED        会话活跃（sessions.status = active 且未过期）    实测约束见 §18
REVOKED / EXPIRED       任一环节已撤销或过期 ⇒ 拒绝                    —

组合要求（候选 CT-2）
  Session 创建必须同时具备 CREDENTIAL_VERIFIED（或等价身份校验）+ DEVICE_VERIFIED
  ⇒ 不得由任意 handler 直接创建 session（SS-W2-01）
```

```text
⚠ 上表为**候选**；具体枚举名与映射关系须经 Human 裁决（CTX-W2-01），
  不得与 init 状态名混淆（identity/device/session 的状态名以冻结 schema / 契约为准）。
```

---

# 4. Tenant / Space 关系（认证 ≠ 授权）

```text
关系式（候选）

  Authenticated User  ≠  Tenant/Space Authorized

  context 只能携带 **候选 tenant_id / space_id**（来自请求 + 成员关系解析），
  其**有效性**必须由既有 Stage 2 Authorization 判定，而不是由 context 自身断言。

  core.tenant / core.space 已提供：TenantContext / SpaceContext / require_same_tenant
  ⇒ Wave 2 复用该契约，**不新建** tenant/space 模型（SEC-05 = SELECT ONLY）

缺失与冲突语义（候选 · 待 CTX-W2-02 裁决）
  · tenant 无法确定        → DENY（不得默认 PLATFORM 或"任意 tenant"）
  · space 无法确定         → 按 use-case 决定：需要 space 的用例 DENY
  · 多 membership 并存     → 必须**显式选择** active membership，不得取"第一个"
  · inactive membership    → DENY（fail-closed）
  · 跨 tenant 访问          → DENY（require_same_tenant 语义）
```

---

# 5. 与既有 Stage 2 的接口（候选）

```text
  context ──(identity_id/user_id/device_id/session_id/tenant_id/space_id/subject_type/scope)──▶
        services.authorization.SubjectResolver  →  ResolvedSubject
        services.authorization.AuthorizationService.authorize(AuthorizationRequest) → Decision

约束
  · 不新增 subject 类型（SUBJECT_TYPES 冻结）
  · 不新增 action（ACTIONS 冻结 = canonical 12）
  · 不新增 scope（STORED_SCOPES 冻结 = PLATFORM / TENANT / SPACE）
  · 不新增 effect（EFFECTS 冻结 = ALLOW / DENY / REQUIRES_APPROVAL）
  · context **不得**携带 Decision 结果（不缓存判定 · 不预授权）
```

---

# 6. 生命周期与所有权

```text
创建者    = authentication adapter / service（**不是** handler 自行拼装）
拥有者    = service / use-case 调用栈（每请求一份 · 不可跨请求复用）
销毁      = 请求结束即失效（不得进入长期缓存 / 不得写入 observability 长期字段）
可变性    = 不可变（frozen value object）；需要变更 ⇒ 重新经过认证与授权

依赖方向
  Authentication → Context → Authorization → Use-case → Repository → uap_runtime
  （沿用 DL-2 与 RUNTIME-G-04；与 Wave 2 DEPENDENCY MAP §3 一致）
```

---

# 7. 与 Wave 1 基础层的关系

```text
复用（不改写）
  · Error Taxonomy：context 构造失败 ⇒ Configuration/Authorization/Authentication 分类，
    **不得**归一为意外错误
  · Transaction Boundary：context 的 DB 读取发生在 service 拥有的只读事务内
  · Observability：correlation_id 走既有 logging 上下文（**不含** secret）
  · Principal：仍为 uap_runtime（context 不是身份切换手段）

如 Wave 2 发现必须改变以上任一项 ⇒ `FOUNDATION REGRESSION RISK` → STOP
```

---

# 8. 未决项（须 Human 裁决）

```text
CTX-W2-01  authentication 事实枚举的**精确命名**与映射（§3）
CTX-W2-02  tenant / space 缺失·冲突的 fail-closed 语义细节（§4）
CTX-W2-03  correlation / observability 字段白名单（§7 · 与 SEC-W2-04 联动）
CTX-W2-04  context 是否携带 authorization 输入的**完整集合**或按 use-case 最小子集
（另有 VOC-W2-01 决定是否含 user_id；该 Root Decision 未决前本契约不得冻结）
```

---

# 9. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 8 份）
runtime code = 0 · 未创建任何 context / adapter 实现 · 未修改 Wave 1 基础层
commit / tag / push = 0
```

**END OF P14 RUNTIME AUTHENTICATED CONTEXT CONTRACT（2026-09-28 · DECISION PREPARATION · 未冻结 · least privilege · HARD STOP ACTIVE）**
