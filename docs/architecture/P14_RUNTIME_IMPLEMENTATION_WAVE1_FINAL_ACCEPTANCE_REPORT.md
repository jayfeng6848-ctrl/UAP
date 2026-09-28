# UAP — P14 RUNTIME IMPLEMENTATION WAVE 1 FINAL ACCEPTANCE REPORT

> ## 状态
>
> ```text
> 轮次      = P14 RUNTIME IMPLEMENTATION WAVE 1 — FINAL ACCEPTANCE + EVIDENCE FREEZE
> 性质      = 只读最终验收（无新实现 · 无 schema 变更 · 无 Git 写入操作）
> 基线      = HEAD c420403d5469241e8b03855428ebce435d539c9e · branch main · tags 9 · remote 0
> 结果      = WAVE 1 ACCEPTED（Runtime Wave 1 = IMPLEMENTED + VERIFIED + ACCEPTED）
> 边界      = P14 Overall Acceptance = **NOT YET**（Identity / Device / Session / API 未实施）
> ```

---

# 1. Scope

```text
本次最终验收**只覆盖** Wave 1 已授权且已实际实现的基础层：

  Application Runtime Bootstrap          Runtime Configuration
  uap_runtime DB Connection              Principal Verification
  Connection Pool                        Transaction Boundary
  Persistence Adapter                    Domain Boundary
  Authorization Integration Boundary     Lifecycle / Shutdown
  Health Infrastructure                  Observability
  Error Taxonomy                         Wave 1 Tests
  Security Regression

明确排除（不得提前标 PASS）：
  Identity Business / Device Business / Session Business / API Endpoint /
  Bootstrap CLI / New Schema Object / Migration 0018+ / Privilege Expansion / P15
```

---

# 2. Authorization Reference

```text
Human Authorization（pasted instruction「P14 — RUNTIME IMPLEMENTATION WAVE 1」）
  → P14_RUNTIME_IMPLEMENTATION_AUTHORIZATION_SHEET.md（AUTHORIZATION RESOLVED）
  → P14_RUNTIME_IMPLEMENTATION_AUTHORIZATION_CLOSURE_REPORT.md（AUTHORIZATION CLOSED）

RTA Resolution（本轮实测复核）
  RTA-01 … RTA-08 = AUTHORIZED（Runtime process / API boundary / service / repository /
                     centralized authorization integration / identity-device-session workflow /
                     operational health / observability / tests）
  RTA-09          = OPTION B ⇒ Bootstrap CLI = OUT OF SCOPE（独立授权）
  RTA-10          = OPTION B ⇒ 不得隐式创建 schema support object（须独立 Schema Decision）
  ID 完整性        = 10/10 · 无重复 · 无重编号 · 无第二套 RTA ID

Scope 约束（本轮遵守）
  实现严格限于 P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md 与 FILE_INVENTORY 列明的
  IN SCOPE 面；OUT OF SCOPE 与 SEPARATE AUTHORIZATION 面一律未触碰（见 §17）
```

---

# 3. Security Boundary Dependency

```text
上游（本 Wave 消费、不修改）
  P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md   （逐操作行列 · REQUIRED / NOT REQUIRED）
  P14_SECURITY_IMPLEMENTATION_REPORT.md §6/§12  （51 + 6 exact row-grants · nspacl · default ACL）
  P14_SECURITY_ACCEPTANCE_REPORT.md             （Security Acceptance PASS）
  P14_SECURITY_IMPLEMENTATION_CLOSURE_REPORT.md （冻结资产定义）

DB 层冻结值（本轮实测复核 · uap_b1_test）
  uap_runtime = 51 · uap_bootstrap = 6 · uap_app = 5 · uap_seed = 0 · uap_migrator = 245
  pg_default_acl = 0 · user-defined memberships = 0 · ownership residual = 0
  schema CREATE（全部非 uap 角色）= false · USAGE = true
  public nspacl = {pg_database_owner=UC, =U, uap_app=U, uap_runtime=U, uap_bootstrap=U}

⇒ Runtime 实现**只消费**已冻结授权面，未新增任何 GRANT / REVOKE（见 §25）
```

---

# 4. Incident Reference

```text
文档 = P14_RUNTIME_IMPLEMENTATION_WAVE1_INCIDENT_REPORT.md（**独立保留 · 未删除 · 未改写**）
性质 = CF-C-4 TEST EXECUTION SCOPE VIOLATION（Agent 以目录级 pytest 参数触达禁跑文件）
事实 = tests/security/test_authorization_security.py 的 reset_test_database() 在断言之前
       DROP/CREATE uap_b1_test ⇒ SECURITY EVIDENCE FREEZE 库内基线丢失
保留 = 该事故的事实、根因与影响**不得**因后续恢复而从记录中移除
```

---

# 5. Recovery Reference

```text
文档 = P14_RUNTIME_IMPLEMENTATION_WAVE1_INCIDENT_RECOVERY_REPORT.md
授权 = HD-P14-REC-01（RESTORE uap_b1_test · TARGET = uap_b1_test ONLY）
恢复 = 0017 migration chain（identity = uap_migrator · CF-C-5=B 窗口）+ 冻结授权面精确重放
结果 = uap_b1_test RESTORED · 与事故前基线 28 项键 **0 diff** · 正式库 uap UNCHANGED
治理 = HD-P14-REC-02 → OI-G-9（REGISTER ONLY）· HD-P14-REC-03 → 新载体双归属
```

---

# 6. Final Test Manifest

```text
载体 = P14_RUNTIME_WAVE1_TEST_EXECUTION_MANIFEST.md（EXPLICIT ALLOWLIST · 逐文件）
本轮执行（全部使用**显式文件路径**；未使用任何目录级参数）

  1 Runtime Architecture      tests/architecture/*.py（3 文件）              = 28 passed
  2 Runtime Contract          tests/contract/*.py（2 文件）                  = 23 passed
  3 Runtime Unit              tests/unit/test_runtime_*.py（3 文件）          = 20 passed
  4 Runtime Integration      tests/integration/test_runtime_db_wave1.py     = 13 passed
  5 Security allowed         tests/integration/test_runtime_security_regression_wave1.py
                             + tests/security/test_no_secrets.py            = 46 passed
  6 P14 acceptance subset    tests/unit/{test_project_boot,test_config,test_logging,
                             test_build_info,test_migration_runner,
                             test_migration_state_probe}.py                 = 81 passed

  合计 = 211 passed · 0 failed · 0 skipped · 0 error
```

---

# 7. Application Bootstrap Evidence

```text
实现 = infrastructure/runtime/lifecycle.py:RuntimeApplication.start()
链条 = configuration load → validate → dependency construction（DB 边界 + pool）
       → principal assertion → ready（LifecycleState.STARTED）

证据
  单元 = tests/unit/test_runtime_lifecycle_boundary.py（11 用例：start / double-start /
         stop-before-start / start-after-stop / dependency failure / disposal error / registry）
  活体 = tests/integration/test_runtime_db_wave1.py::test_application_lifecycle_against_live_database
         （真实 DB：state=STARTED · principal=uap_runtime · health=(True,None) · stop() → STOPPED）

API 接线边界（§二十三）
  apps/api lifespan = **NOT WIRED**（本轮未接入 · 事实保留 · 属后续 API Wave）
  ⇒ 本项验收口径 = "Runtime infrastructure implemented"，
     **不**等同于 "API application wiring done"
```

---

# 8. DB Connection Evidence

```text
实现 = infrastructure/database/runtime.py:RuntimeDatabase（唯一 application-level DB 边界）
       engine/pool 构造复用 infrastructure/database/session.py:build_engine
身份 = RuntimeDatabase.from_config(..., require_role="uap_runtime") → start()

证据（活体 · 13 passed）
  连接建立                      test_runtime_connects_as_uap_runtime
  DSN 角色解析                  test_dsn_role_is_read_from_the_url
  loopback（DB 读）             test_approved_reads
  health（未启动 / 已启动）      test_health_is_false_before_start · 主用例
  池释放（幂等）                 test_dispose_is_idempotent_and_releases_the_pool

禁止项复核
  无 DATABASE_URL 之外的第二 runtime 连接来源 · 未使用 uap_migrator / uap_bootstrap /
  uap_app / uap_seed / superuser 作为 runtime 身份（§10）
```

---

# 9. Principal Evidence

```text
断言 = infrastructure/database/principal.py:assert_connection_principal()
       SELECT current_user, session_user 正向断言（不依赖 config 字符串）

证据
  活体  current_user = session_user = **uap_runtime**（test_runtime_connects_as_uap_runtime）
  活体  require_role 不匹配 ⇒ PrincipalAssertionError + 池不存活
        （test_principal_assertion_is_enforced_not_merely_configured）
  角色属性（实测 · §13）
        uap_runtime   : LOGIN=on · NOSUPERUSER · NOCREATEDB · NOCREATEROLE ·
                        NOINHERIT(rolinherit=false) · NOREPLICATION · NOBYPASSRLS
        uap_bootstrap : 同上
  其他           memberships = 0 · ownership residual = 0 ·
                 function EXECUTE(runtime/bootstrap) = 0/0 · schema CREATE = false
```

---

# 10. Transaction Evidence

```text
实现 = RuntimeDatabase.transaction()（service/use-case 拥有事务所有权）

Commit 证明（独立、可回溯）
  test_transaction_commit_is_durable
    BEGIN（transaction ctx）→ SELECT pg_current_xact_id() → 退出 → COMMIT
    → **另一事务**读 pg_xact_status(xid) = **'committed'**

Rollback 证明（独立）
  test_transaction_rollback_is_observed
    BEGIN → 取 xid → 强制失败 → ROLLBACK → pg_xact_status(xid) = **'aborted'**
  test_rollback_leaves_no_residue
    BEGIN → INSERT users（approved）→ 异常 → ROLLBACK → users 计数仍 **0**（无残留）
  test_rolled_back_session_does_not_poison_the_pool
    失败事务后池内连接可复用（DC-22）· health 仍 (True, None)

边界复核（§十二）
  Service/use-case 拥有事务 ✅ · Repository 无 self-commit ✅（persistence.py 无 .commit）·
  Handler 不 commit ✅（apps/ 全量扫描无 execute/commit）· 异常 → rollback 且**不吞异常** ✅ ·
  无 nested hidden transaction（transaction() 单层，session 每次 close）✅ ·
  连接正确归还（finally: session.close() + pool 复用验证）✅
```

---

# 11. Persistence Evidence

```text
实现 = infrastructure/database/persistence.py:Repository（持 session · 不建 engine · 不 commit）

证据
  test_rolled_back_session_does_not_poison_the_pool  ⇒ 失败后连接可复用
  test_rollback_leaves_no_residue                    ⇒ 持久化边界不产生半写
  结构性扫描                                          ⇒ persistence.py 内 create_engine = 0、
                                                       sessionmaker = 0、commit = 0（§22）

边界 = Service → Repository（契约）→ SQLAlchemy session（由 transaction 边界提供）→ uap_runtime
       Service → raw SQL = 0（无 handler/service 直接 SQL 路径）
```

---

# 12. Security Regression Evidence

```text
载体 = tests/integration/test_runtime_security_regression_wave1.py（24 用例 · 全部 PASS）
身份 = uap_runtime（env 注入 UAP_RUNTIME_TEST_DSN · 缺省 SKIP · **不回退**其他身份）
手法 = 每个探针都在事务内执行并**强制回滚**（探针永不提交）
判据 = 拒绝必须是 SQLSTATE 42501（InsufficientPrivilege），而非语法/类型错误

DENY 面（实测被拒）
  SET ROLE uap_migrator / uap_bootstrap / uap_seed / uap_app     → 42501
  CREATE ROLE（含 SUPERUSER 变体）· CREATE SCHEMA ·
  CREATE TABLE / VIEW / MATERIALIZED VIEW / SEQUENCE / TYPE / INDEX / FUNCTION / TRIGGER → 42501
  ALTER TABLE ADD COLUMN / OWNER TO · ALTER SCHEMA OWNER · ALTER ROLE（CREATEDB / SUPERUSER）·
  COMMENT ON · DROP TABLE / SCHEMA / ROLE ·                                     → 42501
  resource_permissions（I/U/D）· platform_memberships（I/U/D）· platform_state（I/U/D）·
  tenants（I/U/D）· spaces（I/U/D）· credentials DELETE · audit_logs/events DELETE → 42501
  权限篡改尝试（GRANT / REVOKE / ALTER DEFAULT PRIVILEGES）→ **inert**：
    执行后 relacl 与 pg_default_acl 指纹不变 · uap_seed 未获得 users SELECT

ALLOW 面（实测与 Matrix 一致）
  runtime SELECT 26 · INSERT 12 · UPDATE 10 · DELETE 3 = **51**
  credentials 允许 INSERT/UPDATE 但**无 DELETE**（SEC-08 无物理删除）
  DELETE 面恰为 {sessions, memberships, tenant_memberships}

指纹 = test_runtime_grant_fingerprint_is_exact（51 项 · default_acl 0 · memberships 0 ·
       function EXECUTE 0 · schema CREATE/USAGE = false/true）
```

---

# 13. Architecture Evidence

```text
证据 = tests/architecture（3 文件 · 28 passed）+ tests/contract（2 文件 · 23 passed）

Core → Domain = 0                       ✅（架构守卫通过）
handler → SQL = 0                       ✅（apps/ 全量扫描：text( / execute( / session_scope /
                                          create_engine / commit( = 0）
Repository create_engine = 0             ✅
Repository self-commit = 0               ✅
runtime code GRANT/REVOKE/CREATE ROLE/
ALTER ROLE/migration execution = 0        ✅（基础设施文件全量扫描为空）

依赖方向
  lifecycle → database.runtime → persistence → uap_runtime → PostgreSQL
  （infrastructure/runtime/__init__ 刻意不 re-export，避免与 database 成环）
```

---

# 14. Error Taxonomy Evidence

```text
实现 = infrastructure/runtime/errors.py（8 类 + NEVER_RETRY_CATEGORIES + classify/is_retryable）

8 类（实测分类集合）
  configuration · connection · persistence · transaction ·
  authorization · authentication · security_boundary（含 PrincipalAssertion）· unexpected

证据
  tests/unit/test_runtime_error_taxonomy.py（6 用例）
    · 8 类互异 · PrincipalAssertion ∈ SecurityBoundary · 安全类**永不重试** ·
      临时类可重试 · 未知异常 → unexpected 且**不泄露 message**
  tests/unit/test_runtime_retry_boundary.py（4 用例）
    · bounded（max_attempts 命中即停）· 退避可注入 · **authorization 失败仅调用 1 次** ·
      max_attempts ≥ 1
  work/failclosed_revalidation.py（独立复核 · 10/10 OK）

禁止项
  未把所有异常归一为 RuntimeError（分类可区分 security 与 transient）✅
  credential / authorization / security failure 不重试 ✅
  constraint violation 不无限重试（不在可重试分类内，且 retry 有上限）✅
```

---

# 15. Observability Evidence

```text
实现 = 复用 infrastructure/logging/{structured,redaction}.py 与 monitoring/metrics.py
       lifecycle 记录结构化事件：uap.runtime.startup / uap.runtime.shutdown
       runtime.py:describe() 走 DatabaseConfig.safe_url()（口令恒为 ***）
       runtime.py:_safe_db_error() 对 password= / 连接串做遮蔽

证据
  test_describe_never_leaks_the_credential（活体）
    · principal 正常暴露（身份非机密）
    · 渲染结果不含 ":uap_runtime@" 与 ":uap_runtime:"（无口令）
    · safe_url 含 ":***@"
    · **原始 DSN 不出现在 describe() 输出中**
  tests/security/test_no_secrets.py（22 项 · 全仓扫描 · PASS）

红线（不得出现）：password · token · credential · secret · full DSN ·
credential hash · raw sensitive payload ⇒ 实测未出现
```

---

# 16. Acceptance Mapping Final State

```text
文档 = P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md（§14 Wave1 更新 + §15 恢复后更新）

状态口径（六态）：VERIFIED / IMPLEMENTED / PLANNED / BLOCKED / OUT OF SCOPE / SEPARATE DECISION

本轮状态（只按真实证据）
  VERIFIED    = Runtime 连接 · Principal · Pool · Transaction（commit/rollback）·
                Persistence 边界 · Lifecycle 活体 · Observability 脱敏 · 安全回归 ·
                PRV-1 / PRV-4 / PRV-8 · Runtime Unit / Integration
  IMPLEMENTED = OPS-1 HTTP 面（health/ready 合同测试通过；runtime readiness 参数化门留待 API Wave）·
                Authorization Integration Boundary（结构性）
  PLANNED     = Identity / Device / Session / Authorization runtime 业务编排 / 审计写入语义 等
  BLOCKED     = OPS-3 / AUD-3 / AUDX-2（bootstrap CLI · RTA-09 = B）
  OUT OF SCOPE= Bootstrap CLI · P15
  SEPARATE    = 任何 schema support object（RTA-10 = B）

⇒ planned **未**因"有相关代码"被改写为 PASS；Identity / Device / Session / API 的 acceptance
   **未**因 Wave 1 通过而提前置 PASS
```

---

# 17. Scope Containment

```text
越界扫描（§二十一）—— 结论：**无越界**

  identity business workflow        = 0（Wave 1 文件无 enroll / onboarding 语义）
  device business workflow          = 0
  session business workflow         = 0
  API endpoint                      = 0（apps/ 未新增路由；lifespan 未接线）
  Bootstrap CLI                     = 0（scripts/ 未新增；运行时无 bootstrap 凭据路径）
  schema support object             = 0（见 §18）
  migration                         = 0（0018+ 不存在；migrations_alembic/** 未修改）
  authorization model rewrite       = 0（services/authorization 未被改动）

Wave 1 触碰的文件（相对 Wave 1 起始 dirty 基线）
  created : infrastructure/runtime/{__init__,errors,retry,lifecycle}.py
            infrastructure/database/{principal,runtime,persistence}.py
            tests/unit/test_runtime_{error_taxonomy,retry_boundary,lifecycle_boundary}.py
            tests/integration/{runtime_testkit,test_runtime_db_wave1,
                               test_runtime_security_regression_wave1}.py
            docs/architecture/P14_RUNTIME_WAVE1_{TEST_EXECUTION_MANIFEST,
                                                BATCHD_OI_REGISTRATION}.md
            docs/architecture/P14_RUNTIME_IMPLEMENTATION_WAVE1_{REPORT,INCIDENT_REPORT,
                                                               INCIDENT_RECOVERY_REPORT,
                                                               FINAL_ACCEPTANCE_REPORT}.md
  modified: infrastructure/database/__init__.py（仅追加导出）
            infrastructure/runtime/lifecycle.py（删除未使用的 re-export 导入）
            infrastructure/database/runtime.py（D-W1-1 fail-closed 修复：补入缺失 import）
            tests/integration/test_runtime_db_wave1.py（D-W1-2 测试载荷修复）
            docs/architecture/P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md（§14/§15 追加）
  core/ · services/ · apps/ · domains/ · agent/ · migrations_alembic/ = **未触碰**
  （工作树中的 core/event/interfaces.py 等为 Wave 1 **之前**既存的历史 dirty，非本轮改动）
```

---

# 18. Schema Boundary

```text
SCHEMA MUTATION SCAN（Wave 1 Runtime implementation 引入的**新**对象）

  Tables / Views / Functions / Triggers / Indexes / Sequences / Types / Schemas = 0
  Migrations（0018+）                                                          = 0

证据（口径 = 与事故前冻结基线逐项比对，而非"看起来没变"）
  pg_class(public, r/p/i/I) = 156（基线 156）→ 新增 0
  pg_proc(public)           =  22（基线  22）→ 新增 0
  pg_trigger total          = 272（基线 272）· parent triggers = 39（基线 39）→ 新增 0
  alembic_version           = 0017_p13_seed · 0018+ 文件 = 0
  default_acl               = 0（未使用 ALTER DEFAULT PRIVILEGES）

既有 P13 对象**不计入** Wave 1；任何新 support object = SEPARATE DECISION REQUIRED（RTA-10 = B）
⇒ 本轮未出现 SCHEMA DEPENDENCY DISCOVERED 情形
```

---

# 19. Git Integrity

```text
HEAD            = c420403d5469241e8b03855428ebce435d539c9e（未变）
branch          = main（未变）
tags            = 9 条（未变 · UAP-V0.1.9-P13-SEED 仍指向 c420403d）
remote          = 0
staged          = 0（**未 stage 任何历史 dirty 文件**）
pre-final-acceptance dirty  = 168
post-final-acceptance dirty = 168 + 本报告（1 个新增文档）

禁止项：COMMIT = 0 · TAG = 0 · PUSH = 0
```

---

# 20. DB Integrity

```text
Formal DB uap
  prestate == poststate = **True**（pg_class 0 · pg_proc 0 · default_acl 0 ·
  memberships 0 · grants 仅 uap 隐式 1463 · roles 6）
  ⇒ Formal DB impact = 0 · Formal Security Evidence Freeze = **INTACT**
  （RTA 授权范围 = uap_b1_test ONLY；恢复轮对 `uap` 只做 SELECT）

Test DB uap_b1_test（RESTORED）
  alembic = 0017_p13_seed · 0018+ = 0
  P13 baseline intact      : acl_subject_types = {user, role, agent} ·
                             permissions = canonical 12 ·
                             role_permissions = platform_admin × 12（effect = allow）
  C2 intact                : public.enforce_acl_subject_types_protect() ·
                             md5 = 185e95be8bc4304edbcd3f4d5cda1eff
  CC-7 intact              : tg_acl_subject_types_protect 存在且 tgenabled = O ·
                             受信分支（current_user ∧ session_user = uap_migrator）存在
  Security Matrix exact    : 51 / 6 / 5 / 0 / 245 · default_acl 0 · membership 0 ·
                             ownership residual 0 · nspacl 精确一致
  意外数据残留              : users 0 · audit_logs 0（全部测试写入均在事务内回滚）
  与事故前冻结基线对账      : 28 项键 **0 diff**
```

---

# 21. Final Wave 1 Disposition

```text
WAVE 1 ACCEPTED

含义（严格限定，依 §三十六）
  P14 Runtime Wave 1 = IMPLEMENTED + VERIFIED + ACCEPTED
  ≠ P14 Runtime = COMPLETE
  ≠ P14 Overall Acceptance（Identity / Device / Session / API 仍未实施）

本轮唯一允许得出的结论边界
  运行时基础层（Bootstrap / Connection / Principal / Pool / Transaction / Persistence /
  Lifecycle / Health / Observability / Error Taxonomy / Authorization Integration Boundary）
  已实现、已由单元 + 集成 + 安全证据覆盖并予以接受。

Evidence Freeze（§二十八）
  冻结对象：Runtime Bootstrap · DB Connection · uap_runtime usage · Persistence Adapter ·
           Transaction Boundary · Lifecycle · Health Infrastructure · Observability ·
           Error Taxonomy · Authorization Integration Boundary · Wave 1 Test Evidence
  后续 Wave 若必须改变其中任何一项（DB connection behavior / transaction semantics /
  repository contract / lifecycle / authorization integration），必须登记
  `FOUNDATION REGRESSION RISK`，不得静默覆盖 Wave 1。

Wave 2
  P14 WAVE 2 IMPLEMENTATION = NOT AUTHORIZED（可准备 Scope / Dependency Lock /
  Acceptance Mapping / Human Authorization Sheet，但不得开始业务代码）
  Bootstrap CLI = OUT OF SCOPE（RTA-09 = OPTION B）· P15 = FORBIDDEN
```

**END OF P14 RUNTIME IMPLEMENTATION WAVE 1 FINAL ACCEPTANCE REPORT（2026-09-28 · WAVE 1 ACCEPTED · P14 Overall = NOT YET · 未 commit/tag/push · HARD STOP ACTIVE）**
