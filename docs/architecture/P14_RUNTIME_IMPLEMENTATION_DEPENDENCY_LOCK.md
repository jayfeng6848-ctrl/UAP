# UAP — P14 RUNTIME IMPLEMENTATION DEPENDENCY LOCK

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CLOSURE + RUNTIME IMPLEMENTATION AUTHORIZATION PREPARATION
> 性质      = 依赖锁定 + 实施前 preflight（**仅设计**；本轮禁止写代码）
> 基线      = Security DB Boundary = ACCEPTED（uap_runtime 51 / uap_bootstrap 6 · OI-G-1 CLOSED）
> 本轮未做   = runtime code / API / service / repository / identity / device / session /
>             authorization / bootstrap CLI 实现 = 0 · DDL / DML / grant / role = 0
> ```

---

# 1. Runtime 实施依赖链（§十三）

```text
Security DB Boundary（uap_runtime · 已 ACCEPTED · 已冻结）
        ↓
Runtime DB Connection Boundary（连接使用 uap_runtime；见 §14 契约）
        ↓
Repository / Persistence Adapter（infrastructure + services 持久化协调）
        ↓
Domain / Use-case Contracts（core/* 契约 + services 用例编排）
        ↓
Authorization Precheck（SEC-10 HYBRID）
        ↓
Identity / Device / Session Workflow
        ↓
API Boundary（apps/api）
        ↓
Operational Interface（health / readiness / observability）
        ↓
Tests（单元 / 契约 / 架构 / 定向安全探针；排除 reset 类 19 文件）

（独立支链，不得成为 normal Runtime dependency）
Bootstrap CLI
        ↓
Dedicated Bootstrap Principal（uap_bootstrap）
        ↓
One-time Bootstrap
```

```text
锁定规则：
DL-1  上层不得绕过下层（如 Repository 不得绕过 Connection Boundary 直连）
DL-2  Authorization Precheck 必须位于 use-case 之前（SEC-10 centralized）
DL-3  Bootstrap CLI **不得**被 normal Runtime import / 调用 / 依赖
DL-4  任一环节不得引入 migration / 新 role / 新 grant（须独立授权）
DL-5  Security DB Boundary 已冻结（§16 of Closure Report）；实施层不得修改
```

---

# 2. Authorization Implementation Preflight（§十五 · 仅设计确认）

```text
形态（已冻结）= SEC-P14-10 HYBRID：
   Central Authorization Service / Use-case  +  Restricted Runtime DB Read

设计确认项：
  AP-1  authorization precheck 入口 = 请求进入 use-case 之前的集中式检查点
        （实现位置在 service 层之前/之内；**不得**在 handler 内自行实现）
  AP-2  service-level mandatory enforcement = use-case 为强制点（不可跳过）
  AP-3  handler 不拥有 authorization authority（handler = transport/adaptation）
  AP-4  deny precedence（deny > allow）
  AP-5  default deny（无匹配 ⇒ 拒绝）
  AP-6  ABAC 语义维持既有 P14 Decision（不新增模型）
  AP-7  authorization failure response = FAIL CLOSED（拒绝；不降级、不放行）
  AP-8  audit decision = 按既有 audit 契约记录判定结果（不写 secret）
  AP-9  **no authorization bypass path**（含内部调用 / 定时任务 / 运维接口）
  AP-10 DB RLS 不作为 P14 primary authorization model（当前 relrowsecurity 表 = 0）

数据读取面（依 uap_runtime 已实施权限）：
  roles / permissions / role_permissions / acl_subject_types / resource_permissions = **SELECT only**
  ⇒ 授权服务只读授权模型；任何写尝试在 DB 层已被拒（SEC-09 / SEC-10）
```

---

# 3. Identity / Device / Session Preflight（§十六 · 转为实现输入）

```text
Identity（SEC-01/02/03 与 OQ-P14-01）
  ID-1  流程 = pending → identity verification → credential/device verification → activation/session
  ID-2  客户端**不得**直接访问 DB（只能经 API/服务边界）
  ID-3  bootstrap 与普通 onboarding **分离**
  ID-4  identity 行与 credential 分离（credential 独立生命周期）

Device（OQ-P14-03）
  DV-1  1 Device : 1 User（单归属）
  DV-2  1 User : N Device
  DV-3  必须显式 enrollment / challenge（不得隐式绑定）
  DV-4  revoke 语义：撤销绑定
  DV-5  **active session revocation 必须同事务**（原子性要求）

Session
  SS-1  建立于 activation；随 device revoke 同步失效
  SS-2  sessions 是**唯一**被 Matrix 明确授予 DELETE 的对象之一（清理失效会话）

Credential（SEC-08 / OQ-P14-02）
  CR-1  Argon2id hash · **no plaintext**（存储 / 日志 / audit / exception 全禁）
  CR-2  rotation（UPDATE）· revoke（UPDATE）· expire（UPDATE）
  CR-3  **no physical delete**（DB 层已无 DELETE 权限）
  CR-4  不新增认证模型
```

---

# 4. Repository / Service Boundary Preflight（§十七）

```text
职责冻结：
  Handler     = transport / adaptation（**禁止** direct SQL；**禁止** direct authorization decision）
  Service     = use-case orchestration + authorization enforcement point +
                transaction boundary + persistence coordination
  Repository  = persistence access（经 Connection Boundary 使用 uap_runtime）
  Domain      = rules / contracts（**不依赖** concrete Runtime services）

边界检查（本轮只读实测）：
  Core → Domain = 0（tests/architecture 28 passed）
  Domain 不依赖 concrete Runtime services（既有契约形态；新增代码须维持）

禁止项：
  · handler direct SQL
  · handler direct authorization decision
  · service 与 domain circular dependency
  · 越层依赖（G-1…G-4 硬门在实施前后均须保持通过）
```

---

# 5. Bootstrap CLI Preflight（§十八 · 本轮**不实现**）

```text
实现输入（设计）：
  BC-1  command shape = 本地可执行命令（显式 invocation；一次初始化）
  BC-2  local-only boundary（**no public bootstrap endpoint** · OQ-P14-09）
  BC-3  operator identity = 本地运维人员（受控执行环境）
  BC-4  credential input = LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT；
        受控部署可 LOCAL SECRET FILE / CONTAINER SECRET（SEC-12）
        禁止：CLI argument 携带 secret · hard-code · shell history · 日志 / audit 暴露
  BC-5  one-time lock = platform_state 判定 + platform_memberships 无行（R4/R5）
  BC-6  transaction boundary = 单事务（插 PM → 翻转 state → audit → COMMIT）
  BC-7  success/failure result = 明确成功/失败语义；失败整体回滚
  BC-8  idempotency = 完成后路径永久关闭（第二次调用被拒）
  BC-9  bootstrap principal credential lifecycle = 一次性；完成后不得转为 runtime credential
  BC-10 **Bootstrap CLI ≠ Runtime API**（不得经网络暴露；不得被 runtime 调用）
```

---

# 6. Observability Preflight（§十九）

```text
映射（Contract §11 OB-1…OB-6 → 实现）：
  OB-1  vendor-neutral structured observability（不绑定厂商）
  OB-2  request ID / correlation ID 贯通
  OB-3  logs / metrics / trace hooks 三面
  OB-4  **no secret** · **no credential material** · **no raw sensitive payload**
  OB-5  operational log ≠ audit log（不同载体）
  OB-6  audit 事件语义沿用既有 audit_logs 契约

边界：observability 实现**不得**引入新的权限模型或新 DB 权限
       （现有 infra/logging/redaction.py 已含脱敏职责，扩展须遵循同一纪律）
```

---

# 7. 本轮工程变更

```text
未修改任何文件 · DDL / DML / migration / runtime code = 0 · new role / grant / revoke = 0
新增文档 = 本文件（+ 同轮 6 份）· commit = 0 · tag = 0 · push = 0
P14 RUNTIME IMPLEMENTATION = NOT AUTHORIZED · HARD STOP = ACTIVE
```

---

**END OF P14 RUNTIME IMPLEMENTATION DEPENDENCY LOCK（2026-09-27 · 依赖链锁定 · Authorization / Identity·Device·Session / Repository·Service / Bootstrap / Observability 五类 preflight 完成 · 静止态）**
