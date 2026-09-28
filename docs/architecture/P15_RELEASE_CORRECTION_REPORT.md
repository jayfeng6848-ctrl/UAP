# P15 RELEASE CORRECTION REPORT

## 0. 摘要

轮次：P15 RELEASE CORRECTION（2026-09-28）
Parent：`dc44c9939d7708b68e5b461a7ccb6684588d1106`（P15 0.1.11）
Correction：`0.1.12` · tag candidate `UAP-V0.1.12-P15-EVENT-CONSUMER`

```text
0.1.11 remote push        = SUCCESS
0.1.11 release validation = FAIL
0.1.11 release status     = BLOCKED（PUBLISHED BUT RELEASE-BLOCKED）
F-RP-04                   = OPEN → CLOSED（本次修复）
F-RP-05                   = OPEN（新登记 · 需独立裁决）
```

---

## 1. 事故事实（历史 · 不可改写）

```text
commit        = dc44c9939d7708b68e5b461a7ccb6684588d1106
tag           = UAP-V0.1.11-P15-EVENT-CONSUMER
tag object    = bc312cd95ef65c5d4fa9a302a0832915107e5fac
remote main   = dc44c99（fast-forward · force push = 0）
fresh clone P15 smoke = 52 passed / 1 collection error
error         = ModuleNotFoundError: tests.integration.runtime_testkit
```

```text
dc44c99 = IMMUTABLE（不 amend / 不 rebase / 不复位）
UAP-V0.1.11-P15-EVENT-CONSUMER = IMMUTABLE（不删除 / 不移动 / 不重建）
```

详见 `docs/architecture/P15_REMOTE_PUSH_RECORD.md`。

---

## 2. 根因

```text
根因 = Release Artifact Completeness 缺陷
       已提交的测试依赖只存在于工作区的文件

实例（F-RP-04）
  tests/integration/runtime_testkit.py               UNTRACKED · REQUIRED
  tests/architecture/test_p10_event_audit_boundary.py UNTRACKED · REQUIRED（Wave 1 allowlist）
```

两者均**先于**本次事故存在（P14 / P10 期产物），非事故后新建。
详见 `docs/architecture/P15_CLEAN_CLONE_DEPENDENCY_AUDIT.md`。

---

## 3. 新登记：F-RP-05

```text
ID             = F-RP-05
Classification = PRE-EXISTING VERIFICATION-VISIBILITY DEFECT
                 （release 验证依赖工作区未提交的 tracked 文件内容）
Scope          = TEST INFRASTRUCTURE / ARCHITECTURE GUARD
P15 CODE CAUSALITY = NONE
Impact         = Wave 1 clean-clone 执行不可全绿（collection 仍 PASS）
Status         = OPEN（不在本 corrective release 授权范围内修复）
```

证据（候选树实测）：

```text
tests/architecture/test_p10_event_audit_boundary.py
  clean candidate tree = 2 failed / 9 passed
  当前工作区（含未提交修改） = 11 passed
```

两个断言分别依赖**未提交**的 tracked 文件内容：

```text
test_five_carrier_faces_are_declared_in_dependency_rules
  → docs/architecture/DEPENDENCY_RULES.md §"Carrier faces"（working tree +69 行 · 未提交）

test_event_contract_uses_the_canonical_uuid7_generator
  → core/event/interfaces.py（uuid4 → new_event_id / UUIDv7 · 未提交）
```

其中 `core/event/interfaces.py` 属既有 **F-RP-02** 登记：

```text
F-RP-02 = BATCH-B/C ACCEPTED CHANGESET RESIDUAL
          含行为语义变更（UUIDv4 → UUIDv7 · tenant_id nullable）
          处置 = REGISTER / DO NOT FIX ⇒ 须独立裁决
```

因此：

> 若要 Wave 1 clean-clone **执行**全绿，必须把 `core/event/interfaces.py` 的语义变更
> 与 `DEPENDENCY_RULES.md` 的未提交修改纳入发布 —— 这超出本 corrective release 的授权范围，
> 必须由独立人工决定（授权纳入 / 授权独立修复 / 授权豁免 / 修订 Wave 1 allowlist）。

本轮不自行扩大 scope，也不修改这两个文件。

---

## 4. 修复（0.1.12 payload）

```text
TEST INFRASTRUCTURE（新增 · explicit paths only）
  tests/integration/runtime_testkit.py
  tests/architecture/test_p10_event_audit_boundary.py

RELEASE METADATA CORRECTION（修改）
  pyproject.toml       0.1.11 → 0.1.12
  config/settings.py   0.1.11 → 0.1.12
  docker-compose.yml   0.1.11 → 0.1.12

RELEASE EVIDENCE（新增）
  docs/architecture/P15_REMOTE_PUSH_RECORD.md
  docs/architecture/P15_CLEAN_CLONE_DEPENDENCY_AUDIT.md
  docs/architecture/P15_RELEASE_CORRECTION_REPORT.md
  docs/architecture/P15_V0_1_12_RELEASE_PAYLOAD_MANIFEST.md
```

未纳入（保护约束）：

```text
F-RP-02（tests/conftest.py · core/event/interfaces.py · infrastructure/database/__init__.py）
BATCH-D（scripts/generate_build_info.py · tests/unit/test_generate_build_info.py · …）
historical dirty（DEPENDENCY_RULES.md 等 13 项）
handoff 包（17）· 非 P15 历史文档（81）· __pycache__（36）
DENY 面未跟踪测试（tests/integration/test_p10_event_audit_schema.py · test_p11_triggers.py · test_p12_indexes.py）
```

---

## 5. 实测验证（候选树 = 临时 index 导出 · 非工作区）

```text
候选树导出文件数 = 445（441 + 4 new）
```

### 5.1 P15 allowlist（4 文件）

```text
65 passed / 0 failed / 0 collection error      ✓（历史 65/0 复现）
```

### 5.2 Wave 1 allowlist（17 文件）

```text
208 passed / 3 failed / 0 collection error
```

```text
差异说明（不得表述为“全绿”）：
  3 failed = 1 × D-02 历史事实（test_runtime_db_wave1::test_approved_reads）
           + 2 × F-RP-05（依赖未提交 tracked 内容 · 本轮授权外）
历史登记 = 210 passed / 1 failed（工作区条件下测得）
本轮实测 = 208 passed / 3 failed（clean tree 条件下测得）
两者差异 = 且仅为上述 2 条 F-RP-05 断言
```

### 5.3 Wave 2 allowlist（9 文件）

```text
72 passed / 0 failed / 0 collection error      ✓（历史 72 复现）
```

### 5.4 禁跑与纪律

```text
tests/unit/test_generate_build_info.py   executed = 0
tests/security/test_authorization_security.py 等 DENY 面  executed = 0
目录级 pytest / collect-only 全树 sweep   = 0
```

### 5.5 Alembic（隔离 verification DB `uap_p15_verify`）

```text
alembic heads = 0017_p13_seed（单 head）
upgrade head → downgrade base → upgrade head = PASS
0018+ = 0（revision 文件 17 个）
verification DB 已删除
```

### 5.6 版本与安全锚点

```text
pyproject.toml / config/settings.py / docker-compose.yml = 0.1.12（一致）
roles = 6 · runtime grants = 51 · routine grants = 0 · uap_app grants = 5
ownership = uap_migrator 156（rel）+ 22（proc）
pg_class = 156 · pg_proc = 22 · pg_trigger = 272
default_acl = 0 · C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff（未变）· CC-7 = INTACT
Core → Domain = 0
Production allowlist = EMPTY · Production handlers = 0
Formal DB `uap` = 0 表（prestate == poststate）
Test DB `uap_b1_test` = 0017_p13_seed · events 0（net zero）· users 0 · audit 1655 → 1898
  （test-only append-only 活动 · 不清空 · 不作为全局 0 条件）
```

---

## 6. 结论与边界

```text
F-RP-04 = CLOSED（required untracked release dependencies = 0）
F-RP-05 = OPEN（登记 · 需独立裁决 · 不阻塞本轮 corrective commit 的既定判据）

P15 functional semantics   = unchanged（未修改 kernel / claim / worker / main）
Migration                  = unchanged（0018+ = 0）
Security                   = unchanged
Production event boundary  = unchanged（EMPTY / 0）

Push                       = FORBIDDEN（须独立 P15 V0.1.12 REMOTE PUSH GATE）
P16+                       = FORBIDDEN
```

**END OF P15 RELEASE CORRECTION REPORT**
