# UAP — P14 RUNTIME IMPLEMENTATION PREFLIGHT

> ## 状态
>
> ```text
> 轮次      = P14 RUNTIME IMPLEMENTATION PREFLIGHT（Phase 16 + 17 + 18）
> 状态      = 预检报告（只读分析）；**本轮不实施任何 runtime code**
> 依据      = P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md（FROZEN · PDL 附录 N）
>             + P14 PRIVILEGE / SECURITY GATE REPORT（DECISION READY）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · 0018+ = 0
> 本轮未做   = 未创建 Python 文件 · 未修改 services / apps / agent / database layer ·
>             未创建 API / CLI implementation / worker / scheduler · 未 commit/tag/push
> ```

---

# 1. Implementation can begin for（可先行实施面）

以下面**不依赖特权数据库访问**，其行为由已冻结的 Contract 决定，故可在取得
`P14 IMPLEMENTATION AUTHORIZATION` 后先行实施：

```text
IMPL-1  runtime modules
        依据：Contract §1（runtime execution layer）· §9（single-host baseline + container-friendly）
        内容：进程/服务宿主、生命周期、依赖装配、优雅关闭

IMPL-2  API boundaries
        依据：Contract §1 + §7 SC-1（apps/api = transport / adaptation · handler 不直接 SQL）
        内容：传输与适配层、契约面、错误语义骨架（错误分类见 §10 FR-2）

IMPL-3  service orchestration
        依据：Contract §7 SC-2（services = use-case orchestration + transaction boundary +
              persistence coordination）· SC-3（domains 不依赖具体 services）
        内容：use-case 编排骨架、事务边界、持久化协调接口（不含实际 DB 写入路径）

IMPL-4  authorization middleware
        依据：Contract §6（AC-1/AC-2/AC-3/AC-4/AC-5）
        内容：centralized precheck + service/use-case enforcement 的中间件骨架；
              default deny / deny precedence / ABAC / FAIL CLOSED 语义
              （判定所需的数据读取路径在写路径之外单独评估 —— 见 §2）

IMPL-5  identity workflow
        依据：Contract §3（IC-1…IC-6）
        内容：staged onboarding 的状态机与流程编排（pending → identity verification →
              credential/device verification → activation/session）
              **不含**实际主体/凭据落库（见 §2）

IMPL-6  bootstrap CLI structure
        依据：Contract §8（BR-1…BR-7）
        内容：CLI 骨架、显式调用、一次性语义、state lock 前置检查、无网络暴露
              **不含**特权写入执行（见 §2）

IMPL-7  observability layer
        依据：Contract §11（OB-1…OB-6）
        内容：request ID / correlation ID 贯通、结构化日志、metrics 接入、trace hooks、
              secret 与敏感 payload 过滤、operational logs 与 audit logs 分离
```

---

# 2. Must wait for Privilege Security Gate（须等待特权决定的面）

```text
WAIT-1  database-backed onboarding
        原因：需要 users / identities / credentials / devices / sessions 的写权限，
              而 uap_app 对上述表**零权限**（实测）；新增授权属独立 Gate
        依赖：Security Decision（principal 模型 + 最小集确认 + 授权执行轮）

WAIT-2  database-backed membership mutation
        原因：memberships 类对象的写权限未定，且 P13 留白未裁（UNKNOWN ⇒ DENY）
        依赖：Security Decision（含 UNKNOWN 项裁定）

WAIT-3  privileged bootstrap
        原因：platform_memberships / platform_state 的写权限不在 uap_app；
              bootstrap 执行身份与凭据来源**未裁**（Security Gate §10 的两个 UNKNOWN）
        依赖：Security Decision（bootstrap 身份与凭据）

WAIT-4  authorization 的**数据读取**路径（判定所需 SELECT）
        说明：middleware 骨架（IMPL-4）可先行；但其读取 roles / permissions /
              role_permissions / acl_subject_types / resource_permissions 的权限同样缺失
        依赖：Security Decision（读侧最小集）
```

```text
⇒ 分界原则：**结构可先行，特权写入/读取须等待 Security Gate。**
   不得以"先写死占位实现"的方式绕过 —— 任何依赖新授权的代码路径在授权前不得落地。
```

---

# 3. 实施序列建议（分析 · 非授权）

```text
Step A（无特权）  IMPL-1 / IMPL-2 / IMPL-7 骨架
Step B（无特权）  IMPL-3 服务编排骨架 + IMPL-4 授权中间件骨架（不含读取路径）
Step C（无特权）  IMPL-5 身份流程状态机 + IMPL-6 CLI 结构（不含落库）
Step D（需授权）  Security Decision 完成 → 授权执行轮 → WAIT-1…4 的落库/读取路径
Step E（需授权）  bootstrap 特权路径（operator CLI 执行身份确定后）
Step F          验收矩阵逐项执行（ACCEPTANCE_MATRIX 51 条目；当前全部 PENDING）
```

---

# 4. Phase 17 — 本轮不实施（HARD RULE 复述）

```text
即使已明确代码结构，本轮**不得**：
  × create Python files（runtime / API / CLI / worker / scheduler）
  × modify existing services
  × modify apps
  × modify agent
  × modify database layer
  × create migration（0018+）
  × 执行 GRANT / REVOKE / CREATE ROLE

原因：Runtime implementation 必须以
      **frozen Contract + Privilege Gate** 为输入；
      当前 Privilege Gate 仍为 DECISION READY（未 SECURITY APPROVED）。
```

```text
实测确认（本轮）：services/ 下新增文件 = 0 · apps/agent/core/infrastructure 修改 = 0
                  （git status 中相关 M 项均为既往脏集，sha 未变）
```

---

# 5. Phase 18 — Cross-Phase Regression（只读）

```text
P09（agent/tool permission 结构）   : 未变（agents 族 0 行 · 表结构未改）
Authorization（0005/0007/0012）     : 未变（roles 1 行 platform_admin · 词表未改）
P10（0013 events/audit_logs）        : 未变（events 0 · audit_logs 0）
P11（0014 triggers）                 : 未变（父级 39 · 全部启用）
P12（0015 indexes）                  : 未变（pg_class 156）
P13（0016/0017）                     : 未变（0016 sha 10284d98… · 0017 sha 1251f0b1…）
CC-7（C2 受信边界）                  : 未变（C2 md5 185e95be8bc4304edbcd3f4d5cda1eff）
P14（附录 M/N + Contract + 4 文档）    : 本轮仅新增 3 份分析文档；FROZEN 决策未改

边界不变量
  Core → Domain            = 0（tests/architecture = 28 passed）
  Runtime → Schema ownership = 0（0018+ = 0 · pg_class / pg_proc 未变）
  Runtime → Migration authority = 0（未使用 uap_migrator 身份）
  Runtime → uap_migrator    = 0（无角色成员关系 · 无凭据复用）
  Future leakage           = 0（无 P15+ · 无 0018+）
```

---

# 6. Preflight 结论

```text
Implementation Preflight = READY
  · 可先行实施面已界定（7 项）
  · 须等待面已界定（4 项）· 依赖 Security Gate
  · 实施序列建议已给出（Step A–F · 分析性质，非授权）
  · 本轮未实施任何代码（Phase 17 遵守）
  · 跨阶段回归无异常（Phase 18 全绿）

但：**P14 IMPLEMENTATION = NOT AUTHORIZED**（保持）；
    且 WAIT-1…4 在 Security Decision 之前不可启动。
```

---

# 7. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · schema = unchanged
新增文档 = 本文件（+ 同轮 2 份）· commit = 0 · tag = 0 · push = 0
```

---

**END OF P14 RUNTIME IMPLEMENTATION PREFLIGHT（2026-09-27 · Implementation Preflight = READY · 可先行 7 项 / 须等待 4 项 · `P14 IMPLEMENTATION = NOT AUTHORIZED`）**
