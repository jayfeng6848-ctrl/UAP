# UAP — P14 RUNTIME IMPLEMENTATION WAVE 1 REPORT

> ## 状态
>
> ```text
> 轮次      = P14 RUNTIME IMPLEMENTATION WAVE 1（Human Authorization 已下发）
> 性质      = 实施 + 只读验证（未 commit / 未 tag / 未 push）
> 基线      = HEAD c420403d…（branch main · tag UAP-V0.1.9-P13-SEED · remote 0）
> 冻结资产   = env.py · 0016 · 0017 · PDL · C2 · CC-7 · P13 seed · roles · grants
> 结果      = 实现完成 · 单元/架构/契约证据 PASS · 集成与安全回归 BLOCKED（见 §7 事故）
> ```

---

# 1. 本轮输入（以仓库实际文件为准）

```text
已读取（实际存在）：
  P14_RUNTIME_IMPLEMENTATION_GUARDRAILS.md
  P14_RUNTIME_IMPLEMENTATION_AUTHORIZATION_SHEET.md
  P14_RUNTIME_IMPLEMENTATION_AUTHORIZATION_CLOSURE_REPORT.md
  P14_RUNTIME_IMPLEMENTATION_FILE_INVENTORY.md
  P14_RUNTIME_IMPLEMENTATION_DEPENDENCY_LOCK.md
  P14_RUNTIME_DB_CONNECTION_IMPLEMENTATION_CONTRACT.md
  P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md
  P14_RUNTIME_IMPLEMENTATION_AUTHORIZATION_IMPACT.md
  P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md · P14_RUNTIME_SLICE_SCOPE.md
  P14_RUNTIME_SLICE_DEPENDENCY_MAP.md · P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md
  P14_SECURITY_IMPLEMENTATION_CLOSURE_REPORT.md · P14_SECURITY_ACCEPTANCE_REPORT.md
  P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md · P14_RUNTIME_CONNECTION_SECURITY_NOTE.md

指令中按名称列出但仓库不存在的文件（按"不要凭名称创造第二份"处理）：
  P14_RUNTIME_RUNTIME?（不存在）· 其余以仓库实际文件为准
```

---

# 2. Wave 1 Baseline（实施前实测 · SECURITY EVIDENCE FREEZE）

```text
Git     HEAD      = c420403d5469241e8b03855428ebce435d539c9e
        branch    = main · tags = 9 · remote = 0 · staged = 0
        dirty     = 152（WAVE-1 PRE-CHANGE DIRTY BASELINE，已存盘，未被 stage）

DB（uap_b1_test，实测，与 handoff 逐项一致）
        roles                 = 6（uap / uap_app / uap_bootstrap / uap_migrator / uap_runtime / uap_seed）
        user memberships      = 0
        default_acl           = 0
        grants                = runtime 51 · bootstrap 6 · app 5 · seed 0 · migrator 245
        schema CREATE         = 全部 false（uap 除外）· USAGE = true
        pg_class(public)      = 156 · pg_proc(public) = 22
        ownership residual    = 0
        C2 md5                = 185e95be8bc4304edbcd3f4d5cda1eff
        registry/permissions/role_permissions = 3 / 12 / 12
        users / audit_logs    = 0 / 0
        alembic_version       = 0017_p13_seed · migration 文件 0018+ = 0
        受保护文件 sha256     = env.py 577f0d0e… · 0016 10284d98… · 0017 1251f0b1… · PDL 4775a686…

口径说明（防口径漂移）：grant 计数以 information_schema.role_table_grants 为主口径；
  aclexplode(relacl) 为副口径（runtime=51 两者一致；migrator 245 vs 182 属口径差异，
  非状态漂移 —— 已用 work/grant_probe.py 复算确认）。
```

---

# 3. Wave 1 实现清单（分层）

```text
新增 · Runtime 层
  infrastructure/runtime/__init__.py        18 行  刻意不 re-export（避免与 database 成环）
  infrastructure/runtime/errors.py         111 行  8 类错误 taxonomy + NEVER_RETRY + classify/is_retryable
  infrastructure/runtime/retry.py           50 行  retry_idempotent（bounded + 退避 + 非可重试直抛）
  infrastructure/runtime/lifecycle.py      177 行  RuntimeApplication（start/stop/health/registry）

新增 · Persistence / DB 边界
  infrastructure/database/principal.py      63 行  role_from_url + assert_connection_principal（fail-closed）
  infrastructure/database/runtime.py       178 行  RuntimeDatabase（engine/pool · transaction · health · dispose）
  infrastructure/database/persistence.py    60 行  Repository 基类（持 session · 不 commit）

修改 · 既有文件（仅增补导出）
  infrastructure/database/__init__.py            追加导出 Repository / PrincipalAssertionError /
                                                 assert_connection_principal / role_from_url / RuntimeDatabase

新增 · 单元测试
  tests/unit/test_runtime_error_taxonomy.py
  tests/unit/test_runtime_retry_boundary.py
  tests/unit/test_runtime_lifecycle_boundary.py

新增 · 集成 / 安全回归测试与测试基建
  tests/integration/runtime_testkit.py                        runtime 身份解析（env 注入 · fail-closed）
  tests/integration/test_runtime_db_wave1.py                  §8–§18 只读 / 事务 / 池 / 生命周期
  tests/integration/test_runtime_security_regression_wave1.py §15 / §26 负向探针
```

```text
分层依赖方向（无反向依赖）：
  apps/api            （本轮未接线，见 §6-B）
      ↓
  infrastructure/runtime/lifecycle.py        （进程生命周期）
      ↓
  infrastructure/database/runtime.py         （唯一 application-level DB 边界）
      ↓
  infrastructure/database/persistence.py     （Repository 契约；无 self-commit）
      ↓
  uap_runtime  →  PostgreSQL
```

---

# 4. 逐层验收（Wave 1 目标链）

```text
Application Bootstrap
  · RuntimeApplication.start()：config load → validate → DB construct → principal assert → ready
  · 任一环节失败 = 启动失败（无 startup anyway / 无 degraded security mode / 无静默继续）
  证据：tests/unit/test_runtime_lifecycle_boundary.py（11 用例）· lifecycle.py:start

Runtime Configuration Boundary
  · 复用 config/settings.Settings + DatabaseConfig（未新增 env key，保持 DATABASE_URL 单键）
  · 配置面不含 GRANT / role creation / migration / bootstrap authority / privilege escalation
  证据：DatabaseConfig 字段清单（url/pool/echo/timeout）· validate() fail-fast

uap_runtime Connection
  · RuntimeDatabase.from_config(..., require_role="uap_runtime") → start()
  · 不存在 uap_migrator / uap_bootstrap / uap_app / uap_seed 的 runtime fallback（仅 DATABASE_URL）
  证据：代码路径 + runtime_testkit 身份断言（§17 禁止替换身份）

Principal Verification
  · SELECT current_user, session_user 正向断言；require_role 不匹配 → PrincipalAssertionError（fail-closed）
  · 断言失败时 engine 立即 dispose（池不存活）
  证据：principal.py · runtime.py:start · 单元用例 test_principal_assertion…（集成待恢复）

Connection Pool
  · 单一 engine（复用 build_engine）：pool_size=5 · max_overflow=10 · pool_pre_ping=True
  · statement_timeout 可配置 · dispose() 幂等
  证据：session.py:build_engine · runtime.py:dispose

Transaction Boundary
  · transaction() 上下文：成功 → session.commit()；异常 → session.rollback() 后原样抛出；finally close
  · Repository 不持有事务所有权；handler 不启用事务（API 面未接线）
  证据：runtime.py:transaction · persistence.py:Repository

Retry Boundary
  · retry_idempotent：bounded（max_attempts）+ 指数退避 + 注入式 sleep
  · NEVER_RETRY_CATEGORIES = configuration / transaction / authorization / authentication /
    security_boundary ⇒ 安全类失败绝不重试
  证据：errors.NEVER_RETRY_CATEGORIES · retry.py · 单元用例（authorization 失败仅调用 1 次）

Persistence Adapter
  · Repository 基类：持 session、_fetch_one/_fetch_all、错误包装为 PersistenceError
  · 无 create_engine / 无 sessionmaker / 无 commit（结构性事实）
  证据：persistence.py 全文

Domain Boundary
  · 本轮未新增 Domain 契约（Wave 1 不触碰 core/*/interfaces.py 语义）
  · Core → Domain = 0（tests/architecture 全量通过）
  证据：tests/architecture（见 §5）

Authorization Integration
  · 本轮只保留边界：未新增第二套授权引擎 / 未新增第二套权限词表 / 未绕过 services/authorization
  · 明确登记：Runtime Service → Authorization Service 的 adapter 接线属后续 Wave
  证据：本轮改动文件清单中无任何授权实现变更

Lifecycle / Shutdown
  · stop()：停新工作 → 释放服务 → dispose 池 → flush observability → 终态 STOPPED
  · 不吞 shutdown 错误（disposal 异常 → TransactionError 上报，状态仍落 STOPPED）
  证据：生命周期单元用例（stop / double-start / stop-before-start / disposal error）

Health Infrastructure
  · 区分 process alive 与 database ready：health() 返回 (ok, safe_message)
  · 未启动 → (False, "runtime database not started")；探针失败 → (False, 脱敏信息)
  · HTTP 面（/health, /ready）沿用既有 apps/api/routes/health.py，本轮未改
  证据：runtime.py:health · 单元用例

Observability
  · 复用既有 infrastructure/logging（structured + redaction）与 monitoring/metrics
  · 启动/关停/连接结果以结构化事件记录（uap.runtime.startup / uap.runtime.shutdown）
  · redaction：describe() 使用 DatabaseConfig.safe_url()，口令恒为 ***；异常文本经 _safe_db_error 脱敏
  证据：runtime.py:describe / _safe_db_error · 单测 test_describe_never_leaks_the_credential（集成待恢复）

Error Taxonomy
  · 8 类（Configuration / Connection / Persistence / Transaction / Authorization /
    Authentication / SecurityBoundary(+PrincipalAssertion) / UnexpectedInternal）
  · 不存在"所有异常归一化为 RuntimeError('something went wrong')"
  · 异常文本不含 secret（_safe_db_error 对 password= 与连接串做遮蔽）
  证据：errors.py · _safe_db_error · 单元用例
```

---

# 5. 测试与证据

```text
已执行（离线，无 DB 副作用）
  $ python -m pytest -q tests/unit/test_runtime_error_taxonomy.py \
        tests/unit/test_runtime_retry_boundary.py \
        tests/unit/test_runtime_lifecycle_boundary.py tests/architecture tests/contract
  → 71 passed · 1 warning（starlette anyio alias DeprecationWarning，与本轮无关）

已执行（含 DB 副作用的路径 —— 见 §7 事故）
  同一次更宽的运行包含 tests/security/test_authorization_security.py
  → 275 passed · 26 errors（errors 全属该文件 setup 失败）→ 该文件触发 uap_b1_test 重建

未取得有效证据（BLOCKED）
  tests/integration/test_runtime_db_wave1.py                 （uap_b1_test 已空）
  tests/integration/test_runtime_security_regression_wave1.py（uap_b1_test 已空）

未执行（依 CF-C-4 / OI-BB-14 纪律）
  · 未执行任何会 reset_test_database() 的文件（但本轮误执行 1 个，见 §7）
  · 未执行 alembic upgrade / downgrade（一次都没有）
  · 未 import migrations_alembic/env.py 做单元测试

测试用例新增统计
  单元：11（lifecycle）+ 6（taxonomy）+ 4（retry）
  集成：12（db wave1）· 安全回归：24（含 parametrize 展开）
  集成/安全回归的执行受 §7 阻塞，用例本体已冻结待运行
```

---

# 6. 关键设计决定（需 Human 知悉）

```text
A. require_role 采用可配置而非硬编码
   默认 = "uap_runtime"（生产 / 集成显式传入）；测试可传 None。
   理由：既有 tests/unit/test_project_boot.py::test_application_starts 使用 conftest 的
        DATABASE_URL（uap 超级用户 DSN）且不连真库；硬编码将破坏既有 BATCH-B 验收链。

B. apps/api/main.py 的 lifespan 本轮未接线
   依据 §十九（具体 API surface 可以留给后续 API Wave）。
   后果：Python 侧 API 进程尚未经由 RuntimeApplication 启动；本项在 Wave 1 报告内显式登记为
        边界（不是遗漏）。Health 面仍由既有 apps/api/routes/health.py 提供。

C. 未新增任何 env key
   runtime 仍只用 DATABASE_URL（D-OP101-10 双键冻结）；migration 仍只用 UAP_MIGRATION_DATABASE_URL。
   测试侧新增测试专用键 UAP_RUNTIME_TEST_DSN（不参与应用配置、不构成 fallback 链）。

D. Runtime credential 不入库（DC-7 / §17）
   集成 / 安全测试的 runtime DSN 不写入仓库（源码 / 模板 / fixture 均不含明文），
   由操作者经 UAP_RUNTIME_TEST_DSN 注入；缺省时 SKIP 而不回退到 DATABASE_URL 或其它身份。

E. 未创建任何 schema support object（RTA-10 = B）
   本轮全部实现均基于既有 0017 schema；无表 / 视图 / 函数 / 触发器 / 索引 / 序列 / 类型 / schema 新建。
```

---

# 7. 事故（Incident）

```text
分类      = CF-C-4 违规执行（Agent 误将含 reset_test_database() 的安全测试纳入运行范围）
文件      = tests/security/test_authorization_security.py（19 个 CF-C-4 文件之一）
触发命令   = python -m pytest -q tests/unit tests/architecture tests/security tests/contract
             --ignore=tests/unit/test_generate_build_info.py
直接原因   = 该文件 fixture 断言陈旧：assert current_revision() == "0015_p12_indexes"，
            而现行 head = 0017_p13_seed ⇒ setup 失败 ⇒ 26 errors
实际影响   = uap_b1_test 被 DROP/CREATE 重建；SECURITY EVIDENCE FREEZE 的库内基线丢失
             · pg_class(public) 156 → 0 · pg_proc 22 → 0 · C2 函数不存在
             · alembic_version 表不存在 · grants 仅余 uap（超用户隐式）
             · public nspacl 丢失 uap_app / uap_runtime / uap_bootstrap 的 USAGE
未受影响   = 角色本体（6 个，属性与口令未变）· uap（正式库，0 表）· uap_test · 全部仓库文件
             · env.py / 0016 / 0017 / PDL sha256 未变 · Git HEAD / tags 未变
修复       = 未执行任何修复（修复需 alembic upgrade + 重放 Security DB Boundary，
            二者均超出本轮授权，且属 §二十六 冻结面）
详细登记   = docs/architecture/P14_RUNTIME_IMPLEMENTATION_WAVE1_INCIDENT_REPORT.md
```

---

# 8. Wave 1 Change Boundary（§28）

```text
modified files
  infrastructure/database/__init__.py          （仅追加导出）
  infrastructure/runtime/lifecycle.py          （删除未使用的 build_engine re-export 导入）

created files
  infrastructure/runtime/{__init__,errors,retry,lifecycle}.py
  infrastructure/database/{principal,runtime,persistence}.py
  tests/unit/test_runtime_error_taxonomy.py
  tests/unit/test_runtime_retry_boundary.py
  tests/unit/test_runtime_lifecycle_boundary.py
  tests/integration/runtime_testkit.py
  tests/integration/test_runtime_db_wave1.py
  tests/integration/test_runtime_security_regression_wave1.py
  docs/architecture/P14_RUNTIME_IMPLEMENTATION_WAVE1_REPORT.md
  docs/architecture/P14_RUNTIME_IMPLEMENTATION_WAVE1_INCIDENT_REPORT.md

tests added
  单元 21 用例（taxonomy 6 · retry 4 · lifecycle 11）· 集成 12 + 安全回归 24（待运行）

unrelated dirty files
  Wave 1 起始 dirty = 152（历史遗留 · 未触碰 · 未 stage）
  Wave 1 结束 dirty = 165（= 152 + 本轮 13 条新增路径）
  （另修改 1 个既存非 git 文件：docs/architecture/P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md，
    该文件本就不在 git 索引内，故不计入 dirty 增量）

frozen files untouched
  migrations_alembic/**（含 env.py / 0016 / 0017）· docs/architecture/PLATFORM_DECISION_LOG.md
  C2 / CC-7 实现 · P13 seed · roles · grants · default ACL · 既有冻结 Decision / Contract 正文

forbidden actions
  commit = 0 · tag = 0 · push = 0 · P15 = 0
```

---

# 9. 本轮工程变更计数

```text
新增文件（仓库）           = 15（runtime 4 · database 3 · tests 6 · docs 2）
修改既存文件（仓库）        = 2（infrastructure/database/__init__.py ·
                              docs/architecture/P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md）
DDL（运行时代码发起）       = 0
DML（运行时代码发起）       = 0
migration（0018+）         = 0
新 role / GRANT / REVOKE   = 0 / 0 / 0
ALTER OWNER / ownership    = 0
commit / tag / push        = 0 / 0 / 0

数据库层副作用（事故）       = 1 次 DROP / CREATE DATABASE uap_b1_test（由测试文件触发，非运行时代码）
```

---

# 10. 结论

```text
Runtime 实现（Bootstrap / Configuration / Connection / Principal / Pool / Transaction /
Retry / Persistence / Lifecycle / Health / Observability / Error Taxonomy）  = IMPLEMENTED（有单元证据）
Authorization Integration Boundary（仅边界，不重写 Stage 2）                   = IMPLEMENTED（结构性）
API 接线 / Identity / Device / Session                                        = NOT STARTED（后续 Wave）
Bootstrap CLI                                                                 = OUT OF SCOPE（RTA-09=B）

集成证据 / 安全回归证据                                                        = BLOCKED（§7 事故）
Security Evidence Freeze（库内基线）                                           = DESTROYED（待 Human 裁决）
```

**END OF P14 RUNTIME IMPLEMENTATION WAVE 1 REPORT（2026-09-28 · 实现完成 · 证据部分 BLOCKED · 未 commit / tag / push · HARD STOP ACTIVE）**

---

# 11. 附录 — 事故恢复后状态更新（2026-09-28 · append-only）

> 本附录**不修改**上文任何历史段落；事故记录（§7）与本文档的时点结论全部保留。

```text
触发      = HD-P14-REC-01（AUTHORIZED — RESTORE uap_b1_test · ONLY）
恢复结果   = uap_b1_test RESTORED（28 项指纹与事故前基线 0 diff）· 正式库 uap UNCHANGED
活体证据   = 重新取得（见 INCIDENT RECOVERY REPORT §9/§10/§14）

§5 状态更新（原：集成/安全回归 BLOCKED）
  tests/integration/test_runtime_db_wave1.py                  → 13 passed
  tests/integration/test_runtime_security_regression_wave1.py → 全部 PASS（安全回归 46 passed 组合内）
  ⇒ 上文 §5「未取得有效证据（BLOCKED）」在恢复后**已解除**；详细对账见 ACCEPTANCE MAPPING §15

§9 计数更新（恢复轮新增）
  实现缺陷修复       = 2（D-W1-1 fail-closed NameError · D-W1-2 测试载荷）
  新增/修改代码文件   = 2（infrastructure/database/runtime.py ·
                        tests/integration/test_runtime_db_wave1.py；均为 Wave 1 范围内）
  新增治理文档       = 4（TEST_EXECUTION_MANIFEST · BATCHD_OI_REGISTRATION ·
                        INCIDENT_RECOVERY_REPORT · ACCEPTANCE MAPPING §15 更新）
  commit / tag / push = 0 / 0 / 0

§10 结论更新
  集成证据 / 安全回归证据  = PASS（已重新取得）
  正式 Security Evidence Freeze = INTACT · Test Evidence Baseline = RESTORED
  P14 Runtime Wave 1        = READY FOR FINAL ACCEPTANCE
```

**END OF WAVE 1 REPORT ADDENDUM（2026-09-28 · 恢复完成 · 证据重取得 · HARD STOP ACTIVE）**
