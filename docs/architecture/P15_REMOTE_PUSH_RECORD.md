# P15 REMOTE PUSH RECORD

## 0. 文档性质

```text
类型 = POST-RELEASE FAILURE EVIDENCE
轮次 = P15 REMOTE PUSH GATE（2026-09-28）
结论 = remote push 技术上成功 · fresh clone 验证失败 · P15 release = BLOCKED
```

> 本文件**不是**成功 Release 记录。
> 它记录的是 `0.1.11` 推送成功但验证失败的事实。
> 本文件不得回写进 `dc44c99`；`dc44c99` 与其 tag 为不可变历史。

---

## 1. Remote Push 实测结果

```text
Remote URL              = https://github.com/jayfeng6848-ctrl/UAP.git
Remote main pre-push    = 15feebadeecd6f7d90e81569c3e869bc20cb18c5   (P14)
Remote main post-push   = dc44c9939d7708b68e5b461a7ccb6684588d1106   (P15)
Push 方式               = fast-forward（15feeba..dc44c99）
Force push              = 0
远端 tag                = UAP-V0.1.11-P15-EVENT-CONSUMER（annotated）
远端 tag object         = bc312cd95ef65c5d4fa9a302a0832915107e5fac
远端 peeled target      = dc44c9939d7708b68e5b461a7ccb6684588d1106
P14 tag                 = b9d356065bad6c5a42796790c832998ffedb2175 → 15feebad（未变）
```

推送动作本身完全符合 PUSH GATE §14 / §15：
只推 `main` 与唯一获授权的 annotated tag，未使用 `--tags` / `--follow-tags`。

---

## 2. Fresh Clone 验证：FAIL

```text
fresh clone HEAD        = dc44c9939d7708b68e5b461a7ccb6684588d1106   ✓
fresh clone tag target  = dc44c99                                    ✓
Alembic heads           = 0017_p13_seed（单 head）                    ✓
upgrade / downgrade / re-upgrade（隔离 verification DB）               ✓
P15 smoke（4 文件 allowlist）
  = 52 passed / 0 failed / 1 collection error                        ✗
```

失败原文：

```text
tests/integration/test_p15_claim.py:27
  from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn
E   ModuleNotFoundError: No module named 'tests.integration.runtime_testkit'
52 tests collected, 1 error
```

即：**committed 的 P15 Batch 2 测试在 clean clone 中无法被收集**。

---

## 3. 根因

```text
tests/integration/runtime_testkit.py
  状态 = untracked（从未提交）
  .gitignore = 未忽略
  P15 payload = 未包含
  依赖者 = 已提交的 9 个测试模块 + wave2_testkit.py
```

同一 clean-tree 复核还发现第二个同类缺口：

```text
tests/architecture/test_p10_event_audit_boundary.py
  状态 = untracked
  作用 = Wave 1 explicit allowlist 中的架构边界守卫
```

详见 `docs/architecture/P15_CLEAN_CLONE_DEPENDENCY_AUDIT.md`。

---

## 4. 影响面

```text
P15 smoke（4 文件）        → collection FAIL
Wave 1 regression（17 文件）→ collection FAIL（缺 test_p10_event_audit_boundary.py）
Wave 2 regression（9 文件） → collection FAIL（8 errors · runtime_testkit）
```

因此 `0.1.11` 不满足 fresh-clone 可复现性，FRESH-CLONE PRINCIPLE 不成立。

注意：

```text
P15 功能代码本身未失败
失败的是 Release Artifact Completeness
```

---

## 5. 正式裁决

```text
UAP-V0.1.11-P15-EVENT-CONSUMER
  = PUBLISHED BUT RELEASE-BLOCKED

Classification
  = FAILED RELEASE CANDIDATE
  = CLEAN-CLONE COMPLETENESS FAILURE

F-RP-04 = OPEN / BLOCKING
```

---

## 6. 不可变约束

```text
commit dc44c9939d7708b68e5b461a7ccb6684588d1106 = IMMUTABLE
tag object bc312cd95ef65c5d4fa9a302a0832915107e5fac = IMMUTABLE
tag UAP-V0.1.11-P15-EVENT-CONSUMER = 不删除 / 不移动 / 不重建
force push / amend / rebase / reset = 禁止
```

---

## 7. 后续

```text
补救方向 = V0.1.12 corrective release（新 commit + 新 annotated tag）
本文件的 0.1.12 结果不在此处回填；
0.1.12 推送完成后由独立的 post-push record 记录。
```

**END OF P15 REMOTE PUSH RECORD（post-release failure evidence · 2026-09-28）**
