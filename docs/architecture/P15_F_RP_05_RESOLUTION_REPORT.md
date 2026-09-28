# P15 F-RP-05 RESOLUTION REPORT

## 0. 文档性质

```text
类型 = 裁决 + 取证（F-RP-05 RESOLUTION GATE）
日期 = 2026-09-28
状态 = F-RP-05 = OPEN（本轮未关闭 · 未修改任何测试或生产代码）
性质 = uncommitted working-tree evidence（不进入 0.1.12 payload · 不回溯改写 0.1.11/0.1.12）
```

> 本文件只回答问题：**Wave 1 当前 frozen allowlist 究竟代表哪一个真实基线？**
> 不修 F-RP-02 · 不改 allowlist · 不推送 · 不把失败改写为通过。

---

## 1. Finding

```text
ID             = F-RP-05
Classification = PRE-EXISTING VERIFICATION-VISIBILITY DEFECT
Impact         = RELEASE VERIFICATION BLOCKER
P15 causality  = NONE
P15 scope expansion = NO
Status         = OPEN
```

Wave 1 frozen allowlist 中至少有一个测试，其通过条件依赖**工作区未提交的 tracked 文件内容**。
因此 Wave 1 的历史验收记录（210 passed / 1 failed）**不是任何一个 committed tree 的复现结果**。

---

## 2. Origin（allowlist 溯源）

```text
定义轮次 = P14 WAVE 1 INCIDENT RECOVERY + TEST SCOPE REMEDIATION（§十一–§十五）
依据     = HD-P14-REC-03（execution governance → CF-C-4 / BATCH-D；
                            semantic ownership → P14 Runtime）
载体     = docs/architecture/P14_RUNTIME_WAVE1_TEST_EXECUTION_MANIFEST.md
进入 git = 15feeba / 15feebadeecd6f7d90e81569c3e869bc20cb18c5（P14 release commit）
所属     = P14（committed 于 P14 tag 之下）· 由 P15_BATCH4 manifest §5 原样继承
```

触发该清单的事故（清单自身记载）：以目录级 `pytest` 运行，把
`tests/security/test_authorization_security.py`（CF-C-4 禁跑文件）纳入执行，
其 fixture `reset_test_database()` 先 DROP/CREATE `uap_b1_test` 再断言陈旧 head ⇒ 26 errors。

### 2.1 关键事实：allowlist 自始引用未提交文件

```text
P14 tree（15feebad）中 tests/ 文件数 = 53

Wave 1 allowlist 17 文件中，P14 tree 缺失：
  tests/architecture/test_p10_event_audit_boundary.py     ← MISSING_AT_P14

Wave 1 测试支撑模块中，P14 tree 缺失：
  tests/integration/runtime_testkit.py
  （P14 manifest 自称“P14 新增 · env 注入 runtime DSN”，但从未提交）
```

```text
⇒ allowlist 在定义的当下（P14）就已经是“文档基线 ≠ committed 基线”
⇒ 是否要求 clean clone？P14/P15 manifest 未要求；
   clean-clone 要求来自 P15 REMOTE PUSH GATE §23–27 与 RELEASE CORRECTION §22–30
⇒ 是否原本就依赖工作区-only 文件？YES（自 P14 起）
```

---

## 3. Affected tests

```text
tests/architecture/test_p10_event_audit_boundary.py
  test_five_carrier_faces_are_declared_in_dependency_rules
  test_event_contract_uses_the_canonical_uuid7_generator

（该文件已于 0.1.12 / a238e85 作为 TEST INFRASTRUCTURE 纳入 committed tree。
  本节的失败是 “committed test + committed content” 条件下的真实失败。）
```

## 4. Affected files

```text
core/event/interfaces.py                （tracked · working-tree modified · 语义变化）
docs/architecture/DEPENDENCY_RULES.md   （tracked · working-tree modified · 文档变化）
```

---

## 5. Failure A — core/event/interfaces.py

### 5.1 断言精确记录

```text
test  = test_event_contract_uses_the_canonical_uuid7_generator
读取  = core/event/interfaces.py（raw text）

assertion 1: assert "uuid4" not in src
  expected            = uuid4 不出现
  committed actual    = 出现：return str(uuid.uuid4())
  working-tree actual = 不出现
  → FAIL（committed） / PASS（worktree）

assertion 2: assert "new_event_id" in src
  expected            = 出现 canonical generator
  committed actual    = 不出现
  working-tree actual = 出现（import core.audit.interfaces.new_event_id / return new_event_id()）
  → FAIL（committed） / PASS（worktree）
```

### 5.2 变更事实（HEAD → worktree · +16 / −3）

```text
1. import 变更：删除 `import uuid`，新增
   `from core.audit.interfaces import new_event_id`
2. `_new_id()` 返回变更：`return str(uuid.uuid4())` → `return new_event_id()`
3. dataclass 字段变更：
   `tenant_id: str` → `tenant_id: str | None = None`
   （附注释：The frozen P10 schema allows NULL: platform-level events carry no tenant.）
4. 模块 docstring 新增 EventBus != Outbox（D-P10-02）说明
```

### 5.3 语义判定（不得重新定义）

```text
UUIDv4 → UUIDv7（D-AUTH-22 / D-P10-02）        = 行为语义变化
tenant_id: str → str | None（default None）    = data contract 语义变化

⇒ 属 working-tree-only SEMANTIC change
⇒ 不得归类为 documentation-only / test fixture / release metadata
⇒ 与 F-RP-02 登记一致（BATCH-B/C accepted changeset residual · DO NOT FIX）
```

---

## 6. Failure B — docs/architecture/DEPENDENCY_RULES.md

### 6.1 断言精确记录

```text
test  = test_five_carrier_faces_are_declared_in_dependency_rules
读取  = docs/architecture/DEPENDENCY_RULES.md

assertion 1: assert "Carrier faces" in src
  committed actual    = 不出现（grep 0 命中）
  working-tree actual = 出现：## Carrier faces — five distinct surfaces (D-P10-17)
  → FAIL（committed） / PASS（worktree）

assertion 2: for face in ("event","audit","operational log","trace","metric")
  committed actual    = 均不出现
  working-tree actual = 五个 face 全部出现（表格形式）
  → FAIL（committed） / PASS（worktree）

assertion 3: assert "test_p10_event_audit_boundary" in src
  committed actual    = 不出现
  working-tree actual = 出现：Enforced by tests/architecture/test_p10_event_audit_boundary.py
  → FAIL（committed） / PASS（worktree）
```

### 6.2 变更性质（HEAD → worktree · +69 / −3）

新增内容为三段**纯文档**块：

```text
1. P09 Authorization 状态块（implemented and accepted · commit 034ee97 · UAP-V0.1.8-AUTHORIZATION）
2. §9 Agent runtime boundary（design frozen · D-AGENT-01…16）  ← future scope（AGENT_RUNTIME）
3. ## Carrier faces — five distinct surfaces（D-P10-17）        ← P10 决策文档
```

```text
语义判定 = documentation-only（无代码语义 · 无 schema · 无权限 · 无 ACL · 无 producer）
但内容跨越三个来源：已发布历史（P09/P10）+ 未来 scope（AGENT_RUNTIME 设计冻结）
⇒ 不是单一来源的“漏提交历史文件”，不能整体当作 baseline repair
```

---

## 7. Wave 1 依赖闭包审计（同族缺陷）

方法：对 17 个 Wave 1 allowlist 文件做传递闭包（import 解析 + 路径字面量解析），
再逐项判定 working tree 与 HEAD 的差异。

```text
closure_size = 69（roots = 17）

闭包内非 clean 的成员：
  MODIFIED  infrastructure/database/__init__.py     ← 属 F-RP-02 残留 · 非本组失败必需

闭包内经路径字面量读取、且工作区有改动的文件：
  MODIFIED  docs/architecture/DEPENDENCY_RULES.md   （Failure B）
  MODIFIED  core/event/interfaces.py                （Failure A）
```

经验判定（以 clean tree 实测为准）：

```text
required worktree-only dependencies = 2
  core/event/interfaces.py               （TYPE B · 语义变化）
  docs/architecture/DEPENDENCY_RULES.md  （文档 delta + 未来 scope 混杂）

非必需（clean tree 下通过）：
  infrastructure/database/__init__.py · tests/conftest.py · 其余 historical dirty
```

---

## 8. 三种结果分类

### TYPE A — Required / Pre-existing / Non-semantic

```text
docs/architecture/DEPENDENCY_RULES.md（其 Carrier faces 段落）
  = required（Failure B 唯一原因）
  = pre-existing（P10 期与测试同时创建 · mtime 2026-09-25）
  = non-semantic（纯文档）
  但同一 working-tree delta 内含 future-scope（AGENT_RUNTIME）文档
  ⇒ 只能登记为 NON-P15 DOCUMENTATION DELTA / BASELINE REPAIR CANDIDATE（需拆分 + 决策）
  ⇒ 不得为 F-RP-05 临时纳入 0.1.12
```

### TYPE B — Required artifact with semantic change

```text
core/event/interfaces.py
  = required（Failure A 唯一原因）
  = 含真实 runtime / data contract 语义变化（UUIDv7 · tenant_id nullable）
  ⇒ DO NOT INCLUDE IN P15
  ⇒ 必须进入独立 foundation decision（F-RP-02 通道）
```

### TYPE C — Test baseline / governance issue

```text
Wave 1 allowlist 自 P14 起即引用未提交文件
（test_p10_event_audit_boundary.py 在 P14 tree 中不存在）
且其两条断言自始依赖工作区-only 内容
  ⇒ test baseline / governance issue
  ⇒ 登记；不修改生产代码；不修改测试结果；不改 allowlist
```

---

## 9. Wave 1 Baseline Decision

```text
WAVE 1 COMMITTED BASELINE（P14 = 15feebad）
  17 文件 allowlist 中 16 个存在 · test_p10_event_audit_boundary.py 缺失
  runtime_testkit.py 缺失
  ⇒ 该 tree 无法收集 Wave 1 allowlist（实测：file not found）

WAVE 1 WORKING-TREE DEVELOPMENT BASELINE（开发机工作区）
  含未提交的 core/event/interfaces.py（语义变化）与 DEPENDENCY_RULES.md（文档 delta）
  ⇒ 历史记录 210 passed / 1 failed 只能在此条件下成立

WAVE 1 EXPECTED VERIFICATION BASELINE（0.1.12 committed tree = a238e85）
  17 文件可全部收集（0 collection error）
  实测 = 208 passed / 3 failed
       = 1 × D-02 历史事实
       + 2 × F-RP-05
```

```text
COMMITTED BASELINE
≠
WORKTREE DEVELOPMENT BASELINE

210/1 是工作区条件记录；
208/3 才是当前 committed-tree reproduction result。
```

---

## 10. D-02 / F-RP-02 Preservation

```text
D-02 = CLOSED（未触碰）
  tests/integration/test_runtime_db_wave1.py::test_approved_reads（assert audit == 0）保持原样
  D-02 与 F-RP-05 保持分离，未合并

F-RP-02 = OPEN / REGISTERED（未变）
  tests/conftest.py · core/event/interfaces.py · infrastructure/database/__init__.py
  本轮 NOT INCLUDED IN P15 · NOT MODIFIED
```

---

## 11. Failure Reproduction（committed-tree 条件）

```text
树   = 0.1.12 candidate tree（git archive <candidate tree> · 447 文件）
环境 = 按 requirements.txt 安装（含 ENV-1 argon2-cffi==25.1.0）
DB   = uap_b1_test（0017_p13_seed）· UAP_RUNTIME_TEST_DSN 指向 uap_runtime

P15（4 文件）    = 65 passed / 0 failed / 0 collection error
Wave 1（17 文件）= 208 passed / 3 failed / 0 collection error
Wave 2（9 文件） = 72 passed / 0 failed / 0 collection error

Wave 1 的 3 failed：
  tests/architecture/test_p10_event_audit_boundary.py::test_five_carrier_faces_are_declared_in_dependency_rules
  tests/architecture/test_p10_event_audit_boundary.py::test_event_contract_uses_the_canonical_uuid7_generator
  tests/integration/test_runtime_db_wave1.py::test_approved_reads（D-02 历史事实）
```

对照（工作区条件）：同一 `test_p10_event_audit_boundary.py` = 11 passed。

---

## 12. P15 Impact

```text
P15 functional semantics         = 不受影响（本轮未修改任何 P15 production 代码）
P15 clean-clone smoke（P15 4 文件）= 不受影响（65/0）
受影响的只有“Wave 1 clean-clone regression surface 是否完全闭合”这一验证命题
```

## 13. Decision

```text
OPTION A（本轮采用）= REMAIN OPEN / FOUNDATION WORK REQUIRED

F-RP-05                = OPEN
P15 0.1.12 REMOTE PUSH  = BLOCKED
F-RP-02                = UNCHANGED
Allowlist              = 未修改（NO）
测试文件                = 未修改（未 skip / 未 xfail / 未改断言 / 未删）
生产代码                = 未修改
```

被明确禁止且未采用的选项：偷带 F-RP-02 进入 0.1.12 · 删除/弱化 Wave 1 测试 ·
把两个失败都标成 D-02 · 仅凭工作区通过就声明 Wave 1 PASS。

## 14. Future Action（必须由独立 Human Decision 启动）

```text
1. F-RP-02 通道：为 core/event/interfaces.py 的行为 / data contract 语义变化
   （UUIDv7 · tenant_id nullable）建立独立 foundation decision。

2. Baseline repair 通道：就 docs/architecture/DEPENDENCY_RULES.md 的工作区 delta
   作出裁决，并先行拆分其中 future-scope（AGENT_RUNTIME §9）与历史段落，
   不得整体追加进远端 release。

3. Governance 通道：就“Wave 1 allowlist 依赖未提交内容”建立新的 governance correction
   （允许方向：修订 allowlist / 明确 clean-clone 验收口径 / 授权基线修复），
   不得直接改测试文件或删减回归覆盖。
```

## 15. Release Impact

```text
0.1.11 = immutable remote FAILED RELEASE CANDIDATE（不改写）
0.1.12 = local corrective release（a238e85 · tag UAP-V0.1.12-P15-EVENT-CONSUMER）
         远端未推送

F-RP-05 = OPEN ⇒ P15 V0.1.12 REMOTE PUSH = BLOCKED
Push / Release / P16+ = FORBIDDEN
HARD STOP = ACTIVE
```

**END OF P15 F-RP-05 RESOLUTION REPORT（F-RP-05 = OPEN · 未提交工作区证据）**

---

## 16. 追加（2026-09-28 · FOUNDATION DECISION GATE · append-only）

本节不改写上文任何历史结论，只补充权威扫描结果：

- `core/event/interfaces.py` 的目标行为**并非无据可依**：`PLATFORM_DECISION_LOG.md` 的
  `D-P10-02`（**FROZEN**，自 `15feebad` 起已在 tracked 决策日志内）明确
  **Domain Event ID = UUIDv7 canonical**，并将 `uuid.uuid4()` 标注为
  “当前实现遗留（`core/event/interfaces.py`），未来实施阶段修正”。
- 因此上文 §8 的 TYPE B 结论应收窄为：**决策已存在；缺的是该实施的 acceptance 与提交**，
  而不是“连决策都没有”。
- `DEPENDENCY_RULES.md` 的 `Carrier faces` 段对应 `D-P10-17`（**FROZEN** · 实施期落地）；
  同文件 §9 属 AGENT_RUNTIME **未来 scope**；§8 状态块为 P09 历史状态（`034ee97` ·
  `UAP-V0.1.8-AUTHORIZATION`）。
- `DomainEvent.tenant_id` 可空性：tracked 权威中 **NO FROZEN DECISION FOUND**；
  间接支撑为 committed DB schema（`0013` · `events.tenant_id nullable`）。

详情见 `docs/architecture/F_RP_05_F_RP_02_FOUNDATION_DECISION_PACKAGE.md`。

**END OF AMENDMENT（2026-09-28 · F-RP-05 仍为 OPEN）**

---

## 17. 追加（2026-09-28 · HUMAN DECISION · append-only）

本节不改写上文任何历史结论（§13 的 Option A / “F-RP-05 = OPEN” 是决策前状态），
只登记决策结果：

```text
HD-FRP-FOUNDATION-01 = FROZEN
F-RP-05 = CLOSED
  Closure reason = Wave 1 committed clean-clone verification 不再依赖 worktree-only 修改
  Before（0.1.12 tree）= 208 passed / 3 failed / 0 collection error（1 × D-02 + 2 × F-RP-05）
  After （0.1.13 tree）= 210 passed / 1 failed / 0 collection error（D-02 only · F-RP-05 = 0）

F-RP-02 = PARTIALLY RESOLVED
  CLOSED = UUIDv7 alignment · tenant_id contract（nullable / platform-scoped）· Carrier Faces
  REMAINING OPEN = tests/conftest.py · infrastructure/database/__init__.py

Wave 1 allowlist = 17（未修改 · 未 skip · 未 xfail · 未改断言）
Real staged = 0 · 0.1.11 / 0.1.12 commit 与 tag 未修改 · remote 未推送
```

**END OF AMENDMENT（2026-09-28 · F-RP-05 = CLOSED）**
