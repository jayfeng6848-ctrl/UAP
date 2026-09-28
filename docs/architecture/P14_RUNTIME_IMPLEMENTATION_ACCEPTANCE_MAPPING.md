# UAP — P14 RUNTIME IMPLEMENTATION ACCEPTANCE MAPPING

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CLOSURE + RUNTIME IMPLEMENTATION AUTHORIZATION PREPARATION（§二十）
> 性质      = 验收映射（设计）；**未实现者一律不标 PASS**
> 状态口径   = PLANNED（实施期验证）／BLOCKED（依赖未授权）／PASS **仅**用于已实测项
> 当前实测 PASS 项 = 仅 Security DB Boundary 相关（已实施）；Runtime 实现项全部 PLANNED
> 依据      = P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX（§2 27 + §5 22 + §7 2 = 51 条目）
> ```

---

# 1. 映射格式

```text
Item | Requirement | Implementation Component | Test | Security dependency | Expected Evidence
```

---

# 2. Runtime 启动 / 运行面

```text
OPS-1  liveness / readiness 语义
  Comp  = apps/api/main.py · infrastructure/database/health.py
  Test  = 启动服务 + 依赖正常/异常两类场景
  SecDep= uap_runtime 连接（DC-1/5/29）
  Evi   = /health 200（依赖异常时仍 liveness 正常）；/ready 503（DB 异常）；探针 2000 ms
  Status= PLANNED

OPS-2  期望 revision 来自构建期只读工件
  Comp  = config/build_info.py（**OUT OF SCOPE · 只读**）+ readiness 组件
  Test  = 校验运行时不可覆盖 + 缺失/无效 ⇒ error
  SecDep= 无（D-PLAT-15 v2 冻结）
  Evi   = 工件 sha + 负向探针（尝试覆盖失败）
  Status= PLANNED（组件已存在，验证待实施轮执行）

ABC-1/2/3/4  架构边界与硬门
  Comp  = 全仓分层（apps/agent/services/core/infrastructure/domains）
  Test  = tests/architecture 全量 + G-1…G-4/G-6/G-7 正负样例
  SecDep= 无
  Evi   = pytest 退出码 + 用例数 + 负向样例结果
  Status= PASS（当前 28 passed · 实施前后均须保持）
```

---

# 3. Identity / Device / Session 面

```text
IDF-1 / IDL-1  首个可登录主体建立路径可用且受控
  Comp  = services/identity（新增）· apps/api 路由（新增）· repository 适配
  Test  = 按裁定路径完成 staged onboarding（pending → verification → activation）
  SecDep= uap_runtime users/identities INSERT/UPDATE（已授权）
  Evi   = 事务内创建成功 + 计数 +1；未授权路径拒绝
  Status= PLANNED（依赖 RTA-03 授权）

IDF-2 / IDL-2 / IDL-3 / SEC-4  凭据生命周期与 secret 边界
  Comp  = services/identity 凭据子模块（新增）· core/identity 契约
  Test  = issue / rotate / revoke / expire；检索明文与日志
  SecDep= credentials S/I/U（已授权）· **无 DELETE**（已实施）
  Evi   = hash 不可逆证明 + 库/日志/审计检索 = 0 明文 + 轮换前后认证尝试
  Status= PLANNED（依赖 RTA-03）

IDF-3 / IDL-6  设备绑定与多设备语义
  Comp  = services/device（新增）
  Test  = enrollment（显式 challenge）· 1 Device:1 User · 1 User:N Device · revoke
  SecDep= devices S/I/U（已授权）· sessions S/I/U/D（已授权）
  Evi   = 绑定/冲突/撤销三类场景结果 + 同事务撤销 active sessions 证据
  Status= PLANNED（依赖 RTA-04）

SS-1/2（session lifecycle）
  Comp  = services/session（新增）
  Test  = activation 建会话 · 失效 · device revoke 同步撤销
  SecDep= sessions S/I/U/D（已授权 · 唯一含 DELETE 的对象之一）
  Evi   = 会话建立/失效记录 + 原子性证据（同事务）
  Status= PLANNED（依赖 RTA-04）

AUDX-5（审计不含敏感材料）
  Comp  = services/authorization/audit.py · infrastructure/logging/redaction.py
  Test  = metadata 抽样检索（无 secret / hash / token）
  SecDep= audit_logs I（已授权）
  Evi   = 抽样结果 0 敏感项
  Status= PLANNED
```

---

# 4. Authorization 面

```text
AUT-1/2/3（default deny / deny precedence / FAIL CLOSED）
  Comp  = services/authorization/（policy.py · permissions.py · service.py）
  Test  = 三类判定：无绑定拒绝 / allow+deny 拒绝 / 依赖不可用拒绝
  SecDep= roles/permissions/role_permissions SELECT（已授权 · 无写）
  Evi   = 三类场景判定结果 + 负向样例
  Status= PLANNED（依赖 RTA-05）

AUT-4（判定位置符合裁定）
  Comp  = authorization service 调用链
  Test  = 调用链检查（handler 不判定 + service 强制点存在）
  SecDep= 读侧最小集（已授权）
  Evi   = 调用链证据 + 越层判定不存在证明
  Status= PLANNED（依赖 RTA-05）

SEC-5/SEC-6（审计语义 / 权限面）
  Comp  = authorization + audit 路径
  Test  = 审计事件条数与语义；授权面计数
  SecDep= audit_logs I · 授权面已冻结
  Evi   = 事件对照 + grants 计数不变
  Status= SEC-6 相关：**PASS**（当前 grants 5/51/6/0/245 已实测）；
          SEC-5 审计写入语义：PLANNED
```

---

# 5. Service / Persistence 面

```text
（Repository/Service 边界）
  Comp  = services/**（orchestration）· infrastructure/database/session.py（connection）·
          repository 适配
  Test  = 分层检查 + transaction boundary 测试（service 持有事务；repository 不提交）
  SecDep= uap_runtime 连接（DC-1/16/17/18）
  Evi   = 事务边界证据（service 开/提/回）+ repository 无 commit 调用
  Status= PLANNED（依赖 RTA-06）

（Service orchestration 正确性）
  Comp  = services/** use-case
  Test  = 各 use-case 正常 / 失败 / 部分失败路径
  SecDep= 依 use-case 对应授权（已实施）
  Evi   = use-case 级测试结果
  Status= PLANNED
```

---

# 6. Fail-Closed / 错误语义

```text
FAL-1 / FAL-2 / FLM-1…FLM-5
  Comp  = service 层错误分类 + connection 层 FAIL CLOSED（DC-29…DC-35）
  Test  = 依赖不可用 / 超时 / 部分失败 / 幂等 / 错误不含敏感信息
  SecDep= 无新增授权需求
  Evi   = 五类场景行为记录 + 幂等计数对照
  Status= PLANNED（依赖 RTA-07）

FLM-2（超时语义）
  Comp  = readiness + connection 超时配置
  Test  = 阈值与行为对照（readiness 侧沿用 2000 ms）
  SecDep= 无
  Evi   = 超时行为证据
  Status= PLANNED
```

---

# 7. Persistence / 连接面

```text
PRV-1（runtime 授权面与清单精确一致）
  Comp  = 无（属 DB 层）
  Test  = role_table_grants / nspacl 对照
  SecDep= Security DB Boundary
  Evi   = 51 + 6 计数与逐项集合
  Status= **PASS**（本轮实测）

PRV-2/3/4/5/7/8（DDL 禁止 / 身份分离 / default ACL / ownership / precondition / 未用 migrator）
  Comp  = 无（属 DB 层）
  Test  = 负向探针 + catalog 断言
  SecDep= Security DB Boundary
  Evi   = 54 次探针结果 + catalog 快照
  Status= **PASS**（本轮实测）
```

---

# 8. Observability 面

```text
OPS-4（部署与可观测最小集）
  Comp  = infrastructure/logging/structured.py · redaction.py · monitoring/metrics.py
  Test  = request/correlation ID 贯通 · 结构化日志字段 · 指标端点 · 脱敏断言
  SecDep= 无新增授权
  Evi   = 日志抽样（无 secret）+ 指标输出 + ID 贯通证据
  Status= PLANNED（依赖 RTA-08）

AUD-1/AUD-2/AUD-3（审计行为）
  Comp  = audit 路径
  Test  = 事件条数 / 不可变性 / actor 语义
  SecDep= audit_logs I（S 亦已授权）· tg_audit_immutable
  Evi   = 事件对照 + UPDATE/DELETE 拒绝探针
  Status= AUD-2 **PASS**（不可变性当前实测）；AUD-1/AUD-3 PLANNED
```

---

# 9. Bootstrap 边界

```text
OPS-3 / AUD-3 / AUDX-2（bootstrap 可执行且不可重开）
  Comp  = Bootstrap CLI（**NOT STARTED**）· uap_bootstrap 连接路径
  Test  = 一次性 bootstrap 全流程 + 二次调用拒绝
  SecDep= uap_bootstrap platform_state S/U · platform_memberships S/I · audit_logs I（已授权）
  Evi   = 初次成功 + 二次拒绝 + audit 行
  Status= **BLOCKED**（依赖 RTA-09：Bootstrap CLI 是否与 Runtime 同轮）
  DB 层现状：权限已就位（catalog 断言 5/5 PASS）；CLI 未实现

（bootstrap 权限边界）
  Status= **PASS**（uap_bootstrap 独立 + broad CRUD/migration/resource_permissions 全 DENIED）
```

---

# 10. Multi-Device 语义

```text
IDF-3 / IDL-6 / DV-1…DV-5
  Comp  = services/device + services/session
  Test  = 1:1 归属约束 · 多设备并存 · 设备撤销连带会话撤销（同事务）
  SecDep= devices S/I/U · sessions S/I/U/D（已授权）
  Evi   = 三类场景 + 原子性证据
  Status= PLANNED（依赖 RTA-04）
```

---

# 11. Security Boundary 相关（已实施部分）

```text
SEC-2 / IDL-5（C2/CC-7 未放宽 · 身份与授权词汇分离）
  SecDep= C2 md5 185e95be…（实测未变）· acl_subject_types = 3 行 {user,role,agent}
  Status= **PASS**
```

---

# 12. 映射汇总

```text
条目总数（矩阵）= 51
本轮映射覆盖 = 51 / 51（无遗漏条目）

状态分布：
  PASS（已实测 · 属 Security DB Boundary 或既有基线） = PRV-1…PRV-8（8）+ ABC-1..4（4）+
        SEC-2 / SEC-6 / IDL-5 / AUD-2 等 ≈ 16 项
  PLANNED（待 Runtime 实施后验证）                      ≈ 34 项
  BLOCKED（依赖 RTA-09）                                = 1 项（OPS-3 bootstrap CLI 路径）

⇒ 未把任何未实现内容标成 PASS（依 §二十 要求）
P14 RUNTIME IMPLEMENTATION = NOT AUTHORIZED
```

---

# 13. 本轮工程变更

```text
未修改任何文件 · DDL / DML / migration / runtime code = 0
新增文档 = 本文件（+ 同轮 6 份）· commit = 0 · tag = 0 · push = 0
```

---

**END OF P14 RUNTIME IMPLEMENTATION ACCEPTANCE MAPPING（2026-09-27 · 51/51 条目映射 · PLANNED 34 · PASS 16 · BLOCKED 1 · 未提前标 PASS）**

---

# 14. WAVE 1 更新（2026-09-28 · append-only · 仅按**已有证据**改状态）

> ```text
> 原则（依 §二十四）：只有在**有测试证据**的条目标 IMPLEMENTED / VERIFIED。
> 未取得证据者保持 PLANNED / BLOCKED，不因"代码已写完"而标 PASS。
> ```

## 14.1 状态变更（有证据）

```text
条目（本文件 §2–§8 对应项）              Wave 1 状态      证据
-------------------------------------------------------------------------------------------
配置校验 / DB 配置解析                    VERIFIED        tests/unit/test_runtime_lifecycle_boundary.py::
                                                          test_start_requires_valid_configuration
事务上下文（边界语义 · 单元层）             IMPLEMENTED     infrastructure/database/runtime.py:transaction
                                                          + lifecycle 单元用例（commit/rollback 路径由
                                                          集成用例覆盖，见 14.3 BLOCKED）
Repository 边界（无 self-commit）         IMPLEMENTED     infrastructure/database/persistence.py
错误分类（security vs transient）          VERIFIED        tests/unit/test_runtime_error_taxonomy.py（6 用例）
有界重试 / 安全失败不重试                  VERIFIED        tests/unit/test_runtime_retry_boundary.py（4 用例）
关停生命周期（不吞 disposal 错误）          VERIFIED        tests/unit/test_runtime_lifecycle_boundary.py::
                                                          test_shutdown_disposal_error_is_not_swallowed
ABC-1…4 架构边界（Core→Domain = 0）        PASS（保持）    tests/architecture 全量 + tests/contract
                                                          （本轮 71 passed 运行内含）
```

## 14.2 结构性 IMPLEMENTED（代码存在 · 证据属后续 Wave）

```text
Application Bootstrap（RuntimeApplication）           IMPLEMENTED（未接线 apps/api lifespan，见 Wave1 §6-B）
uap_runtime 连接 / Principal 断言 / 连接池             IMPLEMENTED（活体证据见 14.3）
Health Infrastructure（liveness vs readiness 分离）    IMPLEMENTED（HTTP 面沿用既有 routes/health.py）
Observability（结构化 + 脱敏复用）                      IMPLEMENTED（describe()/safe_url/_safe_db_error）
Authorization Integration Boundary（仅 adapter 边界）   IMPLEMENTED（未重写 Stage 2 · 未新增词表）
```

## 14.3 BLOCKED（本文件 §2–§11 中依赖活体库的条目）

```text
OPS-1 liveness / readiness 活体             BLOCKED（无可用基线库）
FDV / SEC / PRV 活体复算                    BLOCKED（uap_b1_test 被重建为空库 —— 见事故报告）
集成测试（tests/integration/test_runtime_db_wave1.py）                 BLOCKED（未执行 · 无有效证据）
安全回归（tests/integration/test_runtime_security_regression_wave1.py） BLOCKED（未执行 · 无有效证据）

⇒ 上述条目不标 PASS，亦不因本轮实现而改状态。
```

## 14.4 Wave 1 结论

```text
Wave 1 映射更新 = 8 项状态前移（全部有单元 / 静态证据）+ 1 项结构性标注 + 依赖活体库条目 BLOCKED
未提前标 PASS = 成立
事故          = docs/architecture/P14_RUNTIME_IMPLEMENTATION_WAVE1_INCIDENT_REPORT.md
工程变更       = 见 P14_RUNTIME_IMPLEMENTATION_WAVE1_REPORT.md §8/§9（commit / tag / push = 0）
```

---

# 15. WAVE 1 事故恢复后更新（2026-09-28 · append-only · 仅按**重取得的活体证据**改状态）

> ```text
> 依据 = HD-P14-REC-01（RESTORE uap_b1_test）· 恢复证据 = INCIDENT RECOVERY REPORT §9/§10/§14
> 原则 = code exists ≠ integration verified；unit pass ≠ DB integration pass；
>        DB integration pass ≠ security acceptance pass（三者独立）
> ```

## 15.1 依赖活体库的条目（§14.3 BLOCKED → 本轮状态）

```text
条目                                        §14.3 状态   本 轮 状 态        证据
--------------------------------------------------------------------------------------------
Runtime 连接 / Principal 断言                BLOCKED     VERIFIED        test_runtime_db_wave1.py
                                                                            （current_user = session_user
                                                                             = uap_runtime · 正向断言）
Connection Pool（初始化 / 释放 / 幂等）        BLOCKED     VERIFIED        test_dispose_is_idempotent_and_releases_the_pool
Transaction Boundary（commit 持久性）         BLOCKED     VERIFIED        test_transaction_commit_is_durable
                                                                            （pg_xact_status = 'committed'）
Transaction Boundary（rollback 观察）          BLOCKED     VERIFIED        test_transaction_rollback_is_observed
                                                                            （pg_xact_status = 'aborted'）
Rollback 无残留 / 池不复用污染                 BLOCKED     VERIFIED        test_rollback_leaves_no_residue ·
                                                                            test_rolled_back_session_does_not_poison_the_pool
Application Lifecycle（活体启动/关停）          BLOCKED     VERIFIED        test_application_lifecycle_against_live_database
Observability（凭据不泄露）                    BLOCKED     VERIFIED        test_describe_never_leaks_the_credential
安全回归（DENY 面逐项）                        BLOCKED     VERIFIED        test_runtime_security_regression_wave1.py
                                                                            （24 用例 · 全部 42501）
PRV-1（runtime 授权指纹 51）                   PASS→BLOCKED VERIFIED        test_runtime_grant_fingerprint_is_exact
PRV-4（default ACL）                          PASS→BLOCKED VERIFIED        同上（pg_default_acl = 0）
PRV-8（未用 migrator / 无 membership）          PASS→BLOCKED VERIFIED        同上 + 成员关系双向 False
FLM 面（fail-closed 主断言）                   PLANNED     VERIFIED        test_principal_assertion_is_enforced_not_merely_configured
OPS-1 liveness / readiness（HTTP 面）          BLOCKED     IMPLEMENTED     contract/test_health_contract.py（23 passed）
                                                                            （runtime readiness 参数化门仍留待 API Wave）
```

## 15.2 仍未完成（保持 PLANNED / BLOCKED · 不因本轮恢复而前移）

```text
IDF-1/2/3 · IDL-1…6 · SS-1/2 · DV-1…5 · AUT-1…4 · AUDX-5 · AUD-1/AUD-3
  ⇒ Identity / Device / Session / Authorization runtime 业务编排 = NOT STARTED（后续 Wave）
OPS-3 / AUD-3 / AUDX-2（bootstrap CLI）= BLOCKED（RTA-09 = B · OUT OF SCOPE）
```

## 15.3 本轮证据计数

```text
显式 allowlist 执行（逐文件参数 · 未执行任何 DENY 文件）
  1 Architecture 28 · 2 Contract 23 · 3 Runtime Unit 20 ·
  4 Runtime Integration 13 · 5 Security allowed 46 · 6 Acceptance subset 81
  合计 = 211 passed · 0 failed

恢复后指纹对账（uap_b1_test vs 事故前基线）= 28 项键 0 diff
正式库 uap = UNCHANGED（prestate == poststate）
本轮实现缺陷修复 = 2（D-W1-1 fail-closed NameError · D-W1-2 测试载荷）
```

## 15.4 Wave 1 结论

```text
P14 Runtime Implementation Wave 1 = READY FOR FINAL ACCEPTANCE
（此前 BLOCKED 的两项证据面 —— Runtime 集成与安全回归 —— 均已重新取得且 PASS）

Formal Security Evidence Freeze = INTACT
Test Evidence Baseline           = RESTORED
OI-G-1                           = CLOSED（保持 · 依 §二十七 不自动重开）
事故证据                          = 独立保留（INCIDENT REPORT + RECOVERY REPORT 双文档）
commit / tag / push              = 0
```

**END OF P14 RUNTIME IMPLEMENTATION ACCEPTANCE MAPPING §15（2026-09-28 · 活体证据重取得 · 211 passed · 未提前标 PASS · HARD STOP ACTIVE）**

---

# 16. WAVE 1 FINAL ACCEPTANCE 收口（2026-09-28 · append-only）

> 依据 = `P14_RUNTIME_IMPLEMENTATION_WAVE1_FINAL_ACCEPTANCE_REPORT.md`（本轮 Final Acceptance）

```text
§15.4 状态更新
  P14 Runtime Implementation Wave 1 = READY FOR FINAL ACCEPTANCE
                                   → **WAVE 1 ACCEPTED**
                                   （IMPLEMENTED + VERIFIED + ACCEPTED）

最终证据（本轮实跑 · 显式 allowlist · 无目录级参数）
  Architecture 28 · Contract 23 · Runtime Unit 20 · Runtime Integration 13 ·
  Security allowed 46 · Acceptance subset 81  ⇒ 合计 211 passed · 0 failed
  §十九 fail-closed 复核 = 10/10 OK（独立脚本）

本轮不再前移的条目（保持原状态）
  PLANNED      = Identity / Device / Session / Authorization runtime 业务编排 / 审计写入语义
  BLOCKED      = OPS-3 / AUD-3 / AUDX-2（bootstrap CLI · RTA-09 = B）
  OUT OF SCOPE = Bootstrap CLI · P15
  SEPARATE     = 任何 schema support object（RTA-10 = B）

边界
  Wave 1 Verified ≠ Whole P14 Verified：
  Identity / Device / Session / API 的 acceptance **未**置 PASS；
  P14 Overall Acceptance = **NOT YET**

Git / DB
  commit / tag / push = 0 · staged = 0
  Formal DB uap = prestate == poststate（INTACT）
  Test DB uap_b1_test = RESTORED（28 项键 0 diff）
```

**END OF P14 RUNTIME IMPLEMENTATION ACCEPTANCE MAPPING §16（2026-09-28 · WAVE 1 ACCEPTED · P14 Overall = NOT YET · HARD STOP ACTIVE）**

---

# 17. WAVE 2 ACCEPTANCE PREPARATION（2026-09-28 · append-only · **全部未标 PASS**）

> ```text
> 依据 = P14_RUNTIME_WAVE2_HUMAN_DECISION_SHEET.md（36 项）· WAVE2_SCOPE / DEPENDENCY_MAP /
>        AUTHENTICATED_CONTEXT_CONTRACT / DB_OPERATION_MATRIX / SCHEMA_DEPENDENCY_REGISTER /
>        DECISION_IMPACT_ANALYSIS / DECISION_DEPENDENCY_LOCK / IMPLEMENTATION_AUTHORIZATION_SHEET
> 口径 = 本 §17 只登记**验收准备**，不得把任何 Wave 2 项写成 PASS
> ```

## 17.1 状态分配（六态 · 无 PASS）

```text
HUMAN DECISION REQUIRED（36 项 · 决定未裁决 ⇒ 验收口径无法确定）
  SCOPE-W2-01 · VOC-W2-01…04
  ID-W2-01…05 · DV-W2-01…05 · SS-W2-01…05
  CTX-W2-01…04 · AUTH-W2-01…03 · API-W2-01…04 · SEC-W2-01…05

PLANNED（已准备验收维度 · 待实现）
  Acceptance 维度（依 §二十五 设计清单）：
    Identity : 未认证创建 / 重复身份 / 已撤销凭据 / 已过期凭据 / 无效凭据
    Device   : 错误用户 / 复用设备 / 已撤销设备 / 过期 challenge / 重放 challenge
    Session  : 无效 / 过期 / 已撤销会话 / 错误 device-user 绑定 / 已撤销身份
    Authz    : 未授权 tenant / space / resource · default deny · deny precedence
  证据分层（沿用 Wave 1 口径）：static ≠ live · unit ≠ integration · integration ≠ security ·
    implemented ≠ verified · Wave 2 verified ≠ P14 verified

BLOCKED
  Wave 2 的 live / integration / security 证据
    ⇒ 依赖 (a) 36 项 Human Decision 裁决、(b) W2-AUTH-01…07 授权、
       (c) 本轮 PostgreSQL 不可达导致的 5 项 VERIFICATION PENDING 完成

OUT OF SCOPE
  Bootstrap CLI（RTA-09 = OPTION B）· P15

SEPARATE DECISION
  任何 schema support object（RTA-10 = B）· 任何新 role / 新 grant
```

## 17.2 Wave 2 不得提前满足的既有条目（保持原状态）

```text
IDF-1/2/3 · IDL-1…6 · SS-1/2 · DV-1…5 · AUT-1…4 · AUDX-5 · AUD-1/AUD-3
  ⇒ 仍为 PLANNED / BLOCKED；**未**因 Wave 2 准备文档而改变状态
OPS-3 / AUD-3 / AUDX-2（bootstrap CLI）= BLOCKED（保持）
```

## 17.3 前置条件（验收能否开始）

```text
P-1 36/36 Human Decision RESOLVED（含 5 项 Root Blocker）
P-2 W2-AUTH-01…07 逐项 Human Authorization
P-3 Schema Register §3 的 5 项 VERIFICATION PENDING 完成（只读复核）
P-4 DB Operation Matrix 无未解决 SECURITY GRANT GAP
P-5 Wave 1 Foundation 未被改写（否则 FOUNDATION REGRESSION RISK 已登记）
```

## 17.4 本轮状态

```text
Wave 2 Acceptance Preparation = CREATED（本 §17 + 9 份 Wave 2 准备文档）
Wave 2 Implementation         = NOT STARTED
Wave 2 Authorization          = REQUIRED
Wave 1 Status                 = ACCEPTED（不变 · §16）
P14 Overall Acceptance        = NOT YET
```

**END OF P14 RUNTIME IMPLEMENTATION ACCEPTANCE MAPPING §17（2026-09-28 · Wave 2 验收准备 · 0 PASS · HARD STOP ACTIVE）**

---

# 18. WAVE 2 DECISION RESOLUTION（2026-09-28 · append-only · **0 PASS**）

> ```text
> 依据 = PDL 附录 P（36 项 canonical registration）·
>        P14_RUNTIME_WAVE2_HUMAN_DECISION_SHEET.md §R（Resolution Registry）·
>        P14_RUNTIME_WAVE2_DECISION_CLOSURE_REPORT.md
> 口径 = 本 §18 只允许 DECIDED / PLANNED / READY FOR AUTHORIZATION；
>        **不得**把任何 Wave 2 implementation 标为 PASS
> ```

## 18.1 决策层状态

```text
DECIDED（36 / 36）
  SCOPE-W2-01 · VOC-W2-01…04 · ID-W2-01…05 · DV-W2-01…05 · SS-W2-01…05 ·
  CTX-W2-01…04 · AUTH-W2-01…03 · API-W2-01…04 · SEC-W2-01…05
  ⇒ 全部 FROZEN（unresolved = 0 · UNKNOWN = 0）

READY FOR AUTHORIZATION
  W2-AUTH-01…07（7 项 implementation authorization items）
  ⇒ Human Authorization = **REQUIRED**（本轮未勾选任何一项）
```

## 18.2 实现层状态（**未前移**）

```text
PLANNED（实现与验收均未开始）
  Identity implementation · Device implementation · Session implementation ·
  Authenticated Context implementation · Authorization Integration implementation ·
  API Adaptation implementation · Wave 2 Security Tests implementation

BLOCKED（依赖 W2-AUTH-01…07 授权）
  Wave 2 的 live / integration / security 证据
```

## 18.3 边界输出（决策输出 · 非实现证据）

```text
Existing Grants Sufficient = YES · New Grant Required = NO · New Role Required = NO
New Schema Object Required = NO · Migration Required = NO
C2 Change Required = NO · CC-7 Change Required = NO
Schema = unchanged · Domain = 经显式 mapping 归一 · Divergence = acknowledged + resolved by boundary
```

## 18.4 本轮状态

```text
Wave 2 Decision Resolution    = FROZEN（36 / 36）
Wave 2 Implementation         = NOT STARTED
Wave 2 Authorization          = REQUIRED
Wave 1 Status                 = ACCEPTED（不变 · §16）
P14 Overall Acceptance        = NOT YET
```

**END OF P14 RUNTIME IMPLEMENTATION ACCEPTANCE MAPPING §18（2026-09-28 · Wave 2 DECIDED · 0 PASS · HARD STOP ACTIVE）**

---

# 19. WAVE 2 IMPLEMENTATION（2026-09-28 · append-only · 仅按**实测证据**推进）

> 依据 = `P14_RUNTIME_IMPLEMENTATION_WAVE2_REPORT.md` ·
>        `P14_RUNTIME_WAVE2_TEST_EXECUTION_MANIFEST.md`（68 + 211 passed）

## 19.1 状态推进（每项均有对应测试证据）

```text
条目                                   §18 状态                 本轮状态
--------------------------------------------------------------------------------------------
Identity implementation                PLANNED                 **VERIFIED**（12 security tests）
Credential integration                 PLANNED                 **VERIFIED**（Argon2id · rotate · 无明文）
Device implementation                  PLANNED                 **VERIFIED**（13 security tests）
Session implementation                 PLANNED                 **VERIFIED**（11 security tests）
Authenticated Context implementation   PLANNED                 **VERIFIED**（context 矩阵 + API 往返）
Authorization Integration              PLANNED                 **VERIFIED**（10 security tests · Stage 2 复用）
API Adaptation                         PLANNED                 **VERIFIED**（6 security tests）
Wave 2 Security Tests implementation   PLANNED                 **VERIFIED**（54 integration/security + 14 unit）

IDF-1/2/3 · IDL-1…6 · SS-1/2 · DV-1…5（§17 中的业务验收条目）
  子集（onboarding / 凭据生命周期 / 设备绑定 / 会话创建与撤销）→ **VERIFIED**
  未覆盖子集（管理员代撤销、审批流、审计导出等）→ 保持 PLANNED（不在 Wave 2 授权范围）
AUT-1…4（Stage 2 判定语义）              PLANNED                 **VERIFIED**（经 adapter 复用 · 未重写引擎）
AUDX-5 / AUD-1 / AUD-3                 PLANNED                 **PARTIAL**（Wave 2 已写身份/设备/会话事件；
                                                                 审计导出/上报不在本轮范围）
```

## 19.2 明确未前移

```text
OPS-3 / AUD-3 / AUDX-2（bootstrap CLI 路径）      = BLOCKED（RTA-09 = B · OUT OF SCOPE）
Schema Support Objects                          = SEPARATE DECISION
P15                                             = FORBIDDEN
管理员代撤销 / 审批（REQUIRES_APPROVAL）/ 审计导出   = PLANNED（未授权）
```

## 19.3 未决登记（不隐藏）

```text
D-01  Wave 1 `Repository._fetch_one/_fetch_all` 缺陷（未修复 · 由 services/reads.py 规避）
D-02  Wave 1 审计基线断言改为不变量式（已登记）
ENV-1 argon2-cffi 未写入依赖清单（环境不可复现）
FINDING-AUTHZ-1 canonical ACTIONS 不含身份/设备/会话管理动作（未扩词表）
FINDING-ENGINE-1 readiness 探针与 runtime 使用不同 engine
```

## 19.4 边界

```text
Wave 2 = IMPLEMENTED + VERIFIED（Wave 1 回归 211 passed）
P14 Overall Acceptance = **NOT YET**（待独立的 P14 OVERALL FINAL ACCEPTANCE）
Schema Mutation = 0 · Migration = 0 · Role/Grant/Revoke Mutation = 0
Security Evidence Freeze = INTACT（边界锚点全未变）
EXPECTED TEST DATA = audit_logs 926 行（append-only · 不可删除 · 已声明）
```

**END OF ACCEPTANCE MAPPING §19（2026-09-28 · Wave 2 推进 · P14 Overall = NOT YET · HARD STOP ACTIVE）**

---

# 20. P14 OVERALL FINAL RECONCILIATION（2026-09-28 · append-only · 六态收敛）

> 依据 = `P14_OVERALL_FINAL_ACCEPTANCE_REPORT.md` · `P14_OVERALL_OI_CLOSURE_MATRIX.md`

```text
VERIFIED（有实测证据）
  Wave 1：Bootstrap · Configuration · uap_runtime Connection · Principal · Pool ·
          Transaction（commit/rollback）· Persistence Adapter · Domain Boundary ·
          Lifecycle/Shutdown · Health · Observability · Error Taxonomy
  Wave 2：Identity · Credential · Device · Session · Authenticated Context ·
          Authorization Integration（Stage 2 复用）· API Adaptation · Security Tests
  证据：Wave 2 72 passed · Wave 1 frozen set 210 passed · 干净 venv 20 passed

IMPLEMENTED（结构已实现 · 证据属后续）
  Authorization Integration Boundary 的**策略面**（canonical action 覆盖范围）·
  API readiness 参数化门（沿用既有 health 契约）

ACCEPTED（已验收基线）
  Security DB Boundary（51 / 6 精确授权面）· Wave 1 Foundation · Wave 2 Runtime

DEFERRED（明确推迟 · 不计 PASS）
  D-01（Wave 1 persistence.py foundation maintenance）
  FINDING-AUTHZ-1（管理类身份/设备/会话操作 = SEPARATE HUMAN DECISION）
  `REQUIRES_APPROVAL` 语义（未来独立 Approval / Decision model）
  OI-G-4 · OI-G-9（BATCH-D maintenance）

OUT OF SCOPE
  Bootstrap CLI（RTA-09 = OPTION B）· P15 · domains/** 业务域 · apps/worker 调度

SEPARATE DECISION
  任何 schema support object（RTA-10）· 任何新 role / 新 grant

BLOCKING（未关闭）
  D-02（Wave 1 audit 基线断言 vs append-only 审计数据的环境冲突）⇒ P14 Overall BLOCKED
```

```text
状态口径检查：无 MAYBE · 无 TBD · 无 UNKNOWN；Deferred 未标为 PASS
```

**END OF ACCEPTANCE MAPPING §20（2026-09-28 · 六态收敛 · 1 blocking（D-02）· HARD STOP ACTIVE）**

---

# 21. P14 OVERALL ACCEPTANCE CLOSURE（2026-09-28 · append-only）

> 依据 = Human 裁决 OPTION B（canonical registration = PDL **附录 Q**）·
>        `P14_OVERALL_FINAL_ACCEPTANCE_REPORT.md`

```text
§20 的 blocking item 状态更新
  BLOCKING（未关闭）D-02  →  **CLOSED（Human OPTION B）**
    · Wave 1 frozen artifact 逐字节恢复并冻结（不再改动）
    · 该断言 = Wave-1-only baseline 断言；失败的成因 = append-only EXPECTED TEST DATA
      的库状态，经 Human 裁决为环境状态产物（非代码回归 / 非验收缺陷）
    · 审计不变量由独立 Wave 2 测试覆盖（test_wave2_audit_invariant.py）

最终六态分布（blocking item = 0）
  VERIFIED   ：Wave 1 foundation + Wave 2 runtime（Identity/Credential/Device/Session/
               Context/Authorization/API）+ Security Tests
  IMPLEMENTED：Authorization 策略面（canonical action 覆盖范围）· API readiness 参数化门
  ACCEPTED   ：Security DB Boundary · Wave 1 Foundation · Wave 2 Runtime
  DEFERRED   ：D-01 · FINDING-AUTHZ-1 · REQUIRES_APPROVAL 语义 · OI-G-4 · OI-G-9
  OUT OF SCOPE：Bootstrap CLI · P15 · domains/** · apps/worker
  SEPARATE   ：任何 schema support object · 任何新 role / 新 grant

P14 状态
  P14 Overall Acceptance = **PASS**
  P14 Overall Status     = **ACCEPTED**（IMPLEMENTED + VERIFIED + ACCEPTED）
  Release Preparation    = NOT STARTED（Release 需另开授权）
  COMMIT / TAG / PUSH / P15 = FORBIDDEN
```

**END OF ACCEPTANCE MAPPING §21（2026-09-28 · P14 OVERALL ACCEPTED · blocking = 0 · HARD STOP ACTIVE）**
