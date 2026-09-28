# P15 CLEAN-CLONE DEPENDENCY AUDIT

## 0. 目的与范围

轮次：P15 RELEASE CORRECTION（2026-09-28）
触发：`UAP-V0.1.11-P15-EVENT-CONSUMER` fresh clone 无法完整收集 P15 / Wave 测试（F-RP-04）。

本审计回答的唯一问题：

```text
是否存在 tracked file →（import / reference）→ untracked / ignored / excluded file
以及 tracked test → requires → working-tree-only helper
```

审计对象：仓库实际状态（不依赖记忆、不依赖旧报告）。

```text
tracked   = 441
untracked = 103
ignored   = 36
（实测来源：git ls-files / git ls-files -o --exclude-standard /
  git ls-files -o -i --exclude-standard）
```

扫描面：`tests/` · `services/` · `apps/` · `core/` · `infrastructure/` ·
`migrations_alembic/` · `scripts/` · `config/`（全部 tracked `.py` 静态解析）
+ 全部 tracked 文本文件对 untracked 路径的引用扫描。

方法（可复现 · 纯静态 · 不执行任何测试）：

```text
1. AST 解析每个 tracked .py，提取 import / from-import（含相对 import）
2. 将模块名解析为仓库内路径；判定 = tracked / UNTRACKED / IGNORED / ABSENT
3. 对全部 tracked 文本文件扫描 untracked 文件引用
4. 用 git archive HEAD 导出纯净树，做实测对照（禁跑清单仍为 0）
```

---

## 1. Import 依赖结论

### 1.1 REQUIRED · UNTRACKED（RELEASE BLOCKER）

```text
tests/integration/runtime_testkit.py
```

被以下 **已提交** 模块 import：

```text
tests/integration/test_p15_claim.py
tests/integration/test_runtime_db_wave1.py
tests/integration/test_runtime_security_regression_wave1.py
tests/integration/test_wave2_api_security.py
tests/integration/test_wave2_audit_invariant.py
tests/integration/test_wave2_authorization_security.py
tests/integration/test_wave2_device_security.py
tests/integration/test_wave2_identity_security.py
tests/integration/test_wave2_session_security.py
tests/integration/wave2_testkit.py
```

分类：`UNTRACKED` + `REQUIRED` → `TEST INFRASTRUCTURE`（非 P15 production code）。

### 1.2 REQUIRED · UNTRACKED（Wave 1 allowlist 成员）

```text
tests/architecture/test_p10_event_audit_boundary.py
```

30 个 release allowlist 文件中，**唯一**一个未跟踪文件：

```text
P15 allowlist   4 文件 → tracked 4 / untracked 0
Wave 1 allowlist 17 文件 → tracked 16 / untracked 1  ← 本文件
Wave 2 allowlist 9 文件 → tracked 9 / untracked 0
```

它同时被 tracked 文档引用：`docs/architecture/DEPENDENCY_RULES.md`（"Carrier faces"）、
`docs/architecture/P15_BATCH4_TEST_EXECUTION_MANIFEST.md`、`PLATFORM_DECISION_LOG.md`；
该测试本身也断言 `DEPENDENCY_RULES.md` 必须点名这个守卫。

分类：`UNTRACKED` + `REQUIRED` → `TEST INFRASTRUCTURE`（架构边界守卫 · 无生产语义）。

### 1.3 非阻塞发现（NOT REQUIRED）

```text
tests/integration/test_p10_event_audit_schema.py   UNTRACKED
tests/integration/test_p11_triggers.py             UNTRACKED
tests/integration/test_p12_indexes.py              UNTRACKED
```

三者均属 CF-C-4 DENY 面（executed = 0），**不在 P15 / Wave1 / Wave2 allowlist 内**，
因此不属于 release 验证必需依赖。

分类：`UNTRACKED` + `OPTIONAL`（历史 P10/P11/P12 证据）⇒ 本轮 EXCLUDE。

### 1.4 假阳性说明（审计自证）

审计初版报告 5 条 `core.permission.Decision` 依赖。逐条复核确认**均为假阳性**：

```text
形态 = from core.permission import Decision   （导入的是 name，不是 module）
实际文件 = core/permission/decision.py          → TRACKED
假阳性成因 = 审计脚本在 Windows 大小写不敏感文件系统上把
             core/permission/Decision.py 判定为“存在”
结论 = 无 tracked 生产模块依赖未跟踪模块
```

### 1.5 生产面结论

```text
tracked production modules（services/ · apps/ · core/ · infrastructure/ ·
                            migrations_alembic/ · scripts/ · config/）
  → 对 untracked / ignored 模块的依赖 = 0
```

即：本次缺口完全位于 **测试基础设施面**，不涉及生产运行路径。

---

## 2. 非 import 引用扫描

```text
参考类别                                          性质        阻塞
tracked 文档引用 untracked 历史文档                documentation   NO
（P13 / P14 / OPEN_P10_1 / handoff / AGENT_RUNTIME）
tracked migration 注释引用 untracked 历史文档      comment only   NO
（0013 / 0014 / 0015 / 0016 的注释）
core/event/interfaces.py 注释引用 P10 contract      comment only   NO
tracked 文档引用 untracked 测试文件                documentation   NO
tracked 文档引用 tests/integration/runtime_testkit.py         → 强化 REQUIRED 判定
```

其他资源面：

```text
shell 脚本 / Dockerfile / docker-compose 对 untracked 资源的引用 = 0
配置模板（.env.example / alembic.ini）对 untracked 资源的引用 = 0
ignored 文件 = 仅 __pycache__/*.pyc（36 项）⇒ 无 REQUIRED 的 ignored 依赖
config/_build_info.py（构建期生成）不存在于工作区，且测试通过 monkeypatch 模拟，非必需
```

---

## 3. 纯净树实测（git archive HEAD）

```text
导出文件数 = 441（= tracked 441）
tests/integration/runtime_testkit.py            = 不存在
tests/architecture/test_p10_event_audit_boundary.py = 不存在
```

在纯净树上按既有显式 allowlist 做收集（collect only · 未执行用例）：

```text
P15（4 文件）
  ERROR tests/integration/test_p15_claim.py
  ModuleNotFoundError: No module named 'tests.integration.runtime_testkit'
  → 52 tests collected, 1 Error

Wave 1（17 文件）
  ERROR: file or directory not found:
         tests/architecture/test_p10_event_audit_boundary.py
  → no tests collected

Wave 2（9 文件）
  ERROR tests/integration/test_wave2_session_security.py
  ERROR tests/integration/test_wave2_authorization_security.py
  ERROR tests/integration/test_wave2_api_security.py
  ERROR tests/integration/test_wave2_audit_invariant.py
  → 5 tests collected, 8 Errors
```

结论：三套 allowlist 在**已发布树**上均不可完整收集。

---

## 4. 逐项分类（§6 分类表）

| 路径 | git 状态 | release 必要性 | 分类 | 处置 |
|---|---|---|---|---|
| `tests/integration/runtime_testkit.py` | UNTRACKED | REQUIRED | TEST INFRASTRUCTURE | INCLUDE（0.1.12） |
| `tests/architecture/test_p10_event_audit_boundary.py` | UNTRACKED | REQUIRED | TEST INFRASTRUCTURE | INCLUDE（0.1.12） |
| `tests/integration/test_p10_event_audit_schema.py` | UNTRACKED | OPTIONAL（DENY 面） | HISTORICAL TEST | EXCLUDE |
| `tests/integration/test_p11_triggers.py` | UNTRACKED | OPTIONAL（DENY 面） | HISTORICAL TEST | EXCLUDE |
| `tests/integration/test_p12_indexes.py` | UNTRACKED | OPTIONAL（DENY 面） | HISTORICAL TEST | EXCLUDE |
| `docs/architecture/handoff/*`（17） | UNTRACKED | NOT REQUIRED | HANDOFF | EXCLUDE |
| `docs/architecture/**`（81 · 非 P15） | UNTRACKED | NOT REQUIRED | HISTORICAL / FUTURE SCOPE | EXCLUDE |
| `**/__pycache__/*.pyc`（36） | IGNORED | NOT REQUIRED | GENERATED | EXCLUDE |
| `config/_build_info.py` | 不存在 | NOT REQUIRED | GENERATED | EXCLUDE |

```text
uncommitted REQUIRED dependencies（修复后）= 0
```

---

## 5. 来源与时效证据（证明非事后发明）

```text
tests/integration/runtime_testkit.py
  · 被 tracked 文档 P14_RUNTIME_WAVE1_TEST_EXECUTION_MANIFEST.md 记录为
    “P14 新增 · env 注入 runtime DSN”（P14 阶段早于 P15）
  · 被 tracked 文档 P14_RUNTIME_IMPLEMENTATION_WAVE1_REPORT.md /
    P14_RUNTIME_WAVE1_BATCHD_OI_REGISTRATION.md 引用
  · 文件 mtime = 2026-09-28 00:15（P15 release commit 21:33 之前）

tests/architecture/test_p10_event_audit_boundary.py
  · 文件 mtime = 2026-09-25 23:27（P15 之前）
  · 被 tracked 文档 DEPENDENCY_RULES.md（mtime 2026-09-25 23:26）引用
  · 被 PLATFORM_DECISION_LOG.md / P15_ALLOWLIST 引用
```

两者均为**先于本次事故存在的测试基础设施**，不是为本次事故临时编写。

---

## 6. 修复

```text
0.1.12 corrective payload 新增（explicit paths only）：
  tests/integration/runtime_testkit.py               TEST INFRASTRUCTURE
  tests/architecture/test_p10_event_audit_boundary.py TEST INFRASTRUCTURE

未纳入：DENY 面测试 / handoff / 历史文档 / __pycache__ / generated
```

修复后必须满足：

```text
required untracked dependencies = 0
fresh-clone P15 collection = 0 error
fresh-clone Wave1 collection = 0 error
fresh-clone Wave2 collection = 0 error
```

**END OF P15 CLEAN-CLONE DEPENDENCY AUDIT**
