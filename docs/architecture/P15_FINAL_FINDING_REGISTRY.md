# P15 FINAL FINDING REGISTRY

日期：2026-09-28
轮次：P15 IMPLEMENTATION — Batch 4（Full Acceptance + Cross-Wave Regression + Final Closure）

---

## 1. 分类总表

| ID | 分类 | 内容 | 状态 | 阻塞性 |
|---|---|---|---|---|
| D-01 | 既有缺陷 | `infrastructure/database/persistence.py` Repository helper 缺陷 | DEFERRED | 非阻塞 |
| D-02 | 历史记录 | Wave 1 `assert audit == 0` 陈旧断言 | CLOSED（历史） | 非阻塞 |
| FINDING-AUTHZ-1 | 既有发现 | 授权语义待批（`REQUIRES_APPROVAL`） | DEFERRED / OUT OF P15 SCOPE | 非阻塞 |
| FINDING-ENGINE-1 | 既有发现 | 单 engine 复用边界 | ACCEPTED | 非阻塞 |
| ENV-1 | 既有缺口 | `argon2-cffi` 依赖声明 | CLOSED（P14 已解决） | 非阻塞 |
| F-B4-01 | 证据完备性 | Batch 1/2 contemporaneous evidence 缺失 | RETROSPECTIVE（已补齐并标注） | 非阻塞 |
| F-B4-02 | 证据完备性 | `services/consumer/__init__.py` pre-image 不可得 | UNAVAILABLE（untracked） | 非阻塞 |
| F-B4-03 | 治理判定 | worker process entry 是否 contract-required | 已判定 = 需要 · 已最小补齐 · PASS | 非阻塞 |
| F-B4-04 | 技术边界 | `SafeReader(Repository)` 继承边（D-01 关联） | REGISTERED（P15 活跃路径不受影响） | 非阻塞 |
| F-B4-05 | 文档不一致 | P14 FILE_INVENTORY 记 `apps/worker/main.py` 为 43 行，实际提交版为 28 行 | REGISTERED（历史文档时点差异） | 非阻塞 |
| F-B4-06 | 运行时限制 | handler 线程不可强制中断；drain 超期后线程自然结束、结果丢弃 | REGISTERED（Python runtime 限制） | 非阻塞 |
| F-B4-07 | 未实现（设计） | `apps/worker/**` 未接真实 production handler | 符合 O-5（allowlist EMPTY） | 非阻塞 |
| F-B4-08 | EXPECTED P15 GOVERNANCE DELTA | `PLATFORM_DECISION_LOG.md` 新增附录 T（P15 acceptance closure · append-only） | CLOSED（P15 OVERALL ACCEPTANCE 裁决） | 否 |

```text
BLOCKING FINDINGS = 0
```

---

## 2. 逐项说明

### D-01（DEFERRED · 非阻塞）

```text
文件    = infrastructure/database/persistence.py
sha256  = 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6（本轮未变）
缺陷    = (1) except 分支引用未定义名 err；(2) _fetch_one 用 .one() 无法表达“未找到”
P15 影响 = 0
  · P15 活跃路径 = Worker → ClaimService → EventRepository(SafeReader)
  · SafeReader 覆写了 _fetch_one / _fetch_all（正确语义）
  · 因此 defective helper 不会被调用
处置    = 不修（修复 foundation 属独立 decision）
```

### F-B4-04（REGISTERED · 非阻塞）

```text
内容 = services/reads.py 的 SafeReader 继承自 infrastructure/database/persistence.Repository
影响 = 行为上安全（helper 被覆写）；结构上仍存在一条到 D-01 文件的 import/继承边
不改理由 = services/reads.py 是 P14 Wave 2 已接受文件，修改其继承关系属 P14 语义变更（BATCH 4 §0 禁止）
建议 = 若需彻底切断，应作为独立 decision（BATCH-D / maintenance）
```

### F-B4-03（治理判定 · PASS）

```text
判定依据 = P15 Contract §2「IN（实现载体）：apps/worker/**（专用 consumer 入口）」
         + P15_IMPLEMENTATION_PREP §Implementation scope（IN）
反向证据 = P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md 将 apps/worker 列为 OUT OF SCOPE
           P14 FILE_INVENTORY：apps/worker/main.py「Contract 未要求 ⇒ 不自动纳入」
结论     = 需要 runnable consumer entry ⇒ 属真实 P15 gap（OUTCOME B）
处置     = 最小补齐 apps/worker/main.py（未引入新框架/新 security 面）
测试     = tests/unit/test_p15_worker_entry.py（9 passed）
```

### F-B4-07（设计正确状态 · 非缺陷）

```text
production allowlist = EMPTY
production handler registry = EMPTY
production event producers = NONE（events 行数 = 0）
⇒ 这是 P15 当前正确产品状态，不是缺陷（BATCH 4 §70）
```

### F-B4-08（CLOSED · EXPECTED P15 GOVERNANCE DELTA · 非阻塞）

```text
复核方式 = 逐条比对 work/p14_release_payload.json（payload_count = 97）
结果     = files_checked = 89 · directories_skipped = 8 · changed = 1 · missing = 0

唯一变化 = docs/architecture/PLATFORM_DECISION_LOG.md
  P14 release 时 hash = 4775a686855c5240cb7f5ec2b255a59c92b78baf40acdb60baa7ad52ee8bb2ed
  当前 hash            = 9221b4d78b6543eb9d289593f15bf968da8e73ae62a546db8d0cb194ae5a5c83

原因 = BATCH 4 §5 明确授权：Batch 4 的 final acceptance closure 只能以 append-only 方式登记；
       当前最后附录为 S ⇒ 追加附录 T（P15 IMPLEMENTATION ACCEPTANCE CLOSURE）。
       附录 A–S 正文零改写（append-only）。

P14 完整性判定 = INTACT
  · P14 release commit 15feebad 未变 · P14 tag UAP-V0.1.10-P14-RUNTIME-SLICE 未变
  · origin/main = 15feebad 未变 · tag 总数 10 未新增 · 无新 commit / tag / push
  · 其余 88 个 payload 文件 hash 全部未变 · missing = 0

说明 = PDL 是“活文档”；发布后的 append-only 治理登记不改变 P14 的 release history。
       若 Human 要求严格保持 PDL 在 payload 中的原始 hash，可将附录 T 迁出为独立文档
       —— 本轮不自行回滚（回滚会丢失 §5 授权的验收登记）。

P15 OVERALL ACCEPTANCE 最终裁决（2026-09-28 · 正式落档）：
  Classification = EXPECTED P15 GOVERNANCE DELTA
  Status         = CLOSED
  Blocking       = NO
  Remediation    = NONE
  · P14 historical payload immutability = PASS（commit / tag / origin/main / 其余 88 payload 文件未变）
  · Current P15 PDL mutation            = EXPECTED（P14 之后沿用同一个 PDL，以 append-only 附录延续）
  · 处置 = **不回滚附录 T** · 不改为独立 top-level decision system · 不视为污染
  · 后续 P15 Release Preparation 必须**重新计算 P15 Release Payload**，不得复用 P14 payload hash
  · 详见 docs/architecture/P15_OVERALL_ACCEPTANCE_CLOSURE.md §2
```

---

## 3. 既有 ID 复核

```text
D-01        = DEFERRED（未修 · hash 未变）
D-02        = CLOSED historical（Wave 1 210/211 · 断言保持原样）
ENV-1       = CLOSED（P14：argon2-cffi 已入 pyproject.toml + requirements.txt）
OI-G-1      = CLOSED（历史）
OI-G-4      = REGISTERED / UNFIXED（本次未执行该文件 ⇒ CF-C-4 compliant）
OI-G-9      = REGISTERED（历史事故 · 未修 fixture）
FINDING-AUTHZ-1 = DEFERRED / OUT OF P15 SCOPE
FINDING-ENGINE-1 = ACCEPTED
```

---

## 4. 本轮新增发现（无 blocker）

```text
F-B4-01  Batch 1/2 contemporaneous evidence 不存在（已在 Retrospective 文档中明确标注
         "NOT original execution report"，未伪装成原始报告）
F-B4-02  services/consumer/__init__.py pre-image = UNAVAILABLE（untracked ⇒ 不可恢复）
F-B4-05  P14 FILE_INVENTORY 的 43 行记录与提交版 28 行不一致（历史文档时点快照，不改写）
F-B4-06  Python 线程不可强制中断（已记录为 implementation detail）
```
