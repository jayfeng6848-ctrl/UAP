# P15 WAVE 1 BASELINE CLOSURE

## 0. 目的

固定 Wave 1 的权威验收基线，并记录 F-RP-05 的关闭证据。

```text
Authority = HD-FRP-FOUNDATION-01（FROZEN）· PLATFORM_DECISION_LOG.md 附录 U
状态      = F-RP-05 = CLOSED
```

---

## 1. 基线声明（FROZEN）

```text
EXPECTED VERIFICATION BASELINE = COMMITTED CLEAN-CLONE TREE

不再接受 working-tree development baseline 作为 Release Verification 依据。
```

```text
Wave 1 allowlist = 17（NO REDUCTION · NO TEST SUPPRESSION · 未删 / 未 skip / 未 xfail / 未改断言）
allowlist 权威     = docs/architecture/P14_RUNTIME_WAVE1_TEST_EXECUTION_MANIFEST.md
                     （P14 commit 15feebad 进入 git · P15_BATCH4 manifest §5 原样继承）
```

四层基线必须分开（历史事实，不得混用）：

```text
Historical intended baseline = P14 WAVE 1 manifest 所述 17 文件集合
Committed repository baseline = 0.1.13 tree（本基线，17 文件全部在位且内容自足）
Verification baseline         = committed clean-clone tree（本文冻结）
Runtime semantic baseline      = Event 契约（UUIDv7 canonical · tenant_id nullable）
                                 — 见 P15_EVENT_CONTRACT_ALIGNMENT.md
```

---

## 2. Before / After

| 条件 | 结果 | 明细 |
|---|---|---|
| Before：0.1.12 committed tree（clean clone） | 208 passed / 3 failed / 0 collection error | 1 × D-02 + 2 × F-RP-05 |
| After：0.1.13 committed tree（clean clone） | **210 passed / 1 failed / 0 collection error** | 1 × D-02（历史）· F-RP-05 failures = **0** |

```text
期望（Human Decision §17/§18）与实际一致：
  collection errors = 0
  F-RP-05 failures  = 0
  唯一失败 = D-02（CLOSED historical condition）
```

---

## 3. F-RP-05 两条断言的闭合链

| Assertion | Source | Before（committed） | After（committed） | 闭合机制 |
|---|---|---|---|---|
| `assert "uuid4" not in src` · `assert "new_event_id" in src` | `core/event/interfaces.py` | FAIL（uuid4 存在 · 无 new_event_id） | PASS | `_new_id()` 委托 `core.audit.interfaces.new_event_id()`（D-P10-02 / D-AUTH-22 实施落地） |
| `assert "Carrier faces" in src` · 五个 face · `assert "test_p10_event_audit_boundary" in src` | `docs/architecture/DEPENDENCY_RULES.md` | FAIL（段缺失） | PASS | 恢复 `D-P10-17` 的 Carrier faces 段（仅该段） |

```text
验证方式：0.1.13 candidate tree（git archive · 449 文件）在无工作区差异条件下
          直接运行 17 文件 allowlist → 210 passed / 1 failed（仅 D-02）
```

---

## 4. 依赖闭包（committed tree 条件）

```text
Wave 1 closure（import + 路径字面量）= 69 文件
  path-literal 非 clean 命中 = 0   ← 0.1.12 时的 DEPENDENCY_RULES.md / core/event/interfaces.py 已闭合
  闭包内非 clean 成员 = infrastructure/database/__init__.py（F-RP-02 remaining · 非必需）

untracked required dependencies = 0
tracked worktree-only required  = 0
```

---

## 5. D-02 保持

```text
D-02 = CLOSED（未触碰）
  tests/integration/test_runtime_db_wave1.py::test_approved_reads（assert audit == 0）
  · 保持原样 · 未被改写为 211/211
  · 未与 F-RP-05 合并
Wave 1 失败构成 = 1 × D-02（历史）+ 0 × F-RP-05
```

---

## 6. 明确排除与残留（登记，不隐藏）

```text
AGENT_RUNTIME §9（DEPENDENCY_RULES.md 工作区版本）
  = future scope · 本次未纳入 · 单独作为 future-scope documentation candidate

P09 Authorization status block 重写
  = 未纳入（保持 committed 历史文本 "design frozen — not implemented"）

tests/conftest.py · infrastructure/database/__init__.py
  = F-RP-02 remaining open · 未纳入 · 非 Wave 1 clean-clone 必需

core/event/interfaces.py docstring 引用 P10_IMPLEMENTATION_CONTRACT.md
  = 该文档当前仍未跟踪（documentation-only 交叉引用 · 非测试/运行依赖 · 非阻塞）
```

---

## 7. 结论

```text
F-RP-05 = CLOSED
  Classification = PRE-EXISTING VERIFICATION-VISIBILITY DEFECT
  Closure reason = Wave 1 committed clean-clone verification 不再依赖
                   worktree-only 的 semantic / documentation 修改

Wave 1 committed clean-clone = 210 passed / 1 failed（D-02 only）/ 0 collection error
```

**END OF P15 WAVE 1 BASELINE CLOSURE**
