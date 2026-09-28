# UAP — P14 CONTRACT GAP ANALYSIS

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — DECISION PREPARATION ROUND（Phase 4）
> 问题      = 是否需要新增 `P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md`？
> 性质      = 差距分析（只读 + 分析）；**不创建 Contract**、**不做裁定**
> 约束      = 已冻结文档集合 = 4 份（RUNTIME_DOCUMENT_SET_DECISION.md §2）；
>             新增第 5 份文档须先 amend 该决策（须 Human 授权）
> 本轮未做   = 未创建 Contract · 未改任何既有文档正文 · 无 DDL/DML · commit/tag/push = 0
> ```

---

# 1. 待覆盖的五个面（依指令 Objective：Decision → Scope → Dependency → Contract → Acceptance）

```text
F-1 Decision        —— P14 自身的决策集合（13 个 OQ 裁定结果）及其载体
F-2 Scope           —— 范围与边界（Included / Excluded / Security Boundary）
F-3 Dependency      —— 依赖图与不拥有面
F-4 Implementation rules —— 实施规则：可建/不可建、模块边界与落点、实施顺序、
                            禁止构造（如禁 migration / 禁 schema / 禁扩权）、
                            失败停止条件、留证要求
F-5 Acceptance      —— 验收维度与判据（含硬门）
```

---

# 2. 现有 4 文档的覆盖度核对

```text
文档                                      F-1   F-2   F-3   F-4   F-5
（已冻结集合 · 均为 DRAFT / NOT FROZEN）
P14_RUNTIME_SLICE_PREP_REPORT.md             部分   部分   部分   ✗     ✗
  · 承载：基线 · OQ 清单（13）· 待裁决集合
  · 不承载：实施规则 · 验收判据
P14_RUNTIME_SLICE_SCOPE.md                   ✗     完整   部分   ✗     部分
  · 承载：Mission · Included/Excluded · Security Boundary（SB-1…SB-6）· 非目标
  · 不承载：实施规则与顺序 · 验收
P14_RUNTIME_SLICE_DEPENDENCY_MAP.md          ✗     部分   完整   ✗     ✗
  · 承载：三层模型 · depends on / does not own · 边界检查 · GAP-1…GAP-5
P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md       ✗     ✗      ✗     ✗     完整(DRAFT)
  · 承载：11 维度 / 49 条目判据（§2 + §5）· 状态 DRAFT/PENDING

外部承载（非 P14 文档集合）
  PLATFORM_DECISION_LOG.md                  部分   ✗      ✗     ✗     ✗
  · 承载：D-PLAT / D-AUTH / D-P13 / D-OP101 既有冻结决策（跨阶段）
    但不承载 P14 自身的新决策（13 OQ 尚未裁定，无登记位置）
  其他既有文档（CORE_DOMAIN_MODEL / DEPENDENCY_RULES / MIGRATION_STRATEGY 等）
  · 承载通用规则，但不承载 P14 专属的实施规则
```

---

# 3. 差距清单

```text
GAP-C1 【F-4 缺位 · 主要差距】实施规则无载体
  P14 尚无任何文档回答：
    · 允许新增哪些代码/模块（落地路径、包结构、命名）
    · 明确禁止的构造（migration / schema / 扩权 / 改 P13 seed / 改冻结决策）
    · 实施顺序与依赖（先建什么、后建什么）
    · 失败停止条件（硬门红 / 越界 / 无法留证）
    · 留证要求（命令 + 退出码 + 摘要 + 负向样例）
    · 与既有守卫（G-1…G-8）的对应义务
  ⇒ 现状：这些内容散落于 SCOPE（Excluded）、DEPENDENCY_MAP（守卫关系）、
     PDL（通用禁令），**无单一权威载体**。

GAP-C2 【F-1 缺位 · 结构性差距】P14 自身决策无登记位置
  13 个 OQ 一旦裁定，需要承载：OQ → Human Decision → 设计后果 → 实施后果 → 测试后果。
  当前 4 份文档均非决策记录载体；PDL 是跨阶段 canonical carrier，
  是否将 P14 决策写入 PDL（如新增附录）或写入独立 Contract，尚未裁定。

GAP-C3 【与 P13 先例的落差】
  P13 在实施前具备：P13_IMPLEMENTATION_CONTRACT.md（30.7 KB · 含实施规则 + 修订身份 +
  对象接触面 + 顺序契约 + 幂等契约 + downgrade 契约 + 触发契约 · 后被 §21 修正为现行依据）。
  P14 目前**没有**等价物 ⇒ 若直接实施，实施者需从 4 份文档 + PDL 中拼装规则。

GAP-C4 【验收面已覆盖，但依赖决策】
  ACCEPTANCE_MATRIX 已具备 49 条目判据；但其 PENDING 项依赖 13 个 OQ 裁定。
  ⇒ 不构成独立差距，属正常依赖。
```

---

# 4. 处置选项（**仅枚举 · 禁止选择**）

## OPTION 1 — 新增第 5 份文档 `P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md`

```text
形态    : amend RUNTIME_DOCUMENT_SET_DECISION（4 → 5 份），新增实施契约文档，
          承载 F-4（实施规则）+ F-1 的引用（决策仍登记于 PDL 或契约内附录）。
优点    : ① 与 P13 先例一致（P13 有独立 Contract）；
          ② 实施规则有单一权威载体 ⇒ 实施者无需拼装；
          ③ 便于冻结与版本化（可独立 FROZEN）。
风险    : ① 需 amend 已冻结文档集合决策（额外一轮登记）；
          ② 文档数量增加，存在与 SCOPE/Matrix 内容重复或漂移的风险；
          ③ 若 Contract 与 SCOPE 边界表述不一致 ⇒ 需专门一致性维护。
后续所需 Human Decision :
          ① 是否 amend 文档集合（4 → 5）；
          ② Contract 的冻结时机（13 OQ 裁定后？与 SCOPE/Matrix 同时？）；
          ③ P14 决策登记位置（PDL 附录 vs Contract 内附录）。
```

## OPTION 2 — 保持 4 份文档，把实施规则并入现有载体

```text
形态    : 在 SCOPE 内新增「Implementation Rules」章节，或在 PREP_REPORT 内扩展；
          不新增文件。
优点    : ① 不触碰已冻结的文档集合决策；
          ② 文档数量最小，避免漂移。
风险    : ① SCOPE 职责被扩张（范围文档承担规则文档职责）⇒ 职责混用；
          ② 实施规则可能被后续编辑淹没（SCOPE 已 200+ 行）；
          ③ 与 P13 先例不一致 ⇒ 跨阶段阅读体验不统一。
后续所需 Human Decision :
          ① 是否接受职责扩张；② 实施规则的章节归属与冻结要求。
```

## OPTION 3 — 混合：Contract 仅承载实施规则，决策登记于 PDL 附录

```text
形态    : 新增 Contract（承载 F-4），P14 的 13 项决策以 PDL 附录 N 形式登记（append-only），
          Contract 只引用不重复。
优点    : ① 决策载体唯一（PDL）与 P13/P0 轮先例一致；
          ② 实施规则与决策分离，各自单一职责。
风险    : ① 两处维护（PDL 附录 + Contract 引用）需要一致性纪律；
          ② 文档集合仍需 amend（新增 Contract）。
后续所需 Human Decision :
          ① 是否采用；② 附录编号（N）与登记时机；③ Contract 冻结时机。
```

---

# 5. 分析结论（**不含裁定**）

```text
① 差距客观存在：F-4（实施规则）与 F-1（P14 决策登记位置）在现有 4 份文档中**无权威载体**。
② 该差距**不阻塞**当前 PREP / 决策准备（本轮任务为 OQ 推进至 Human Decision Ready）；
   但**阻塞**"实施授权"——若无实施规则载体，实施者必须自行拼接规则，
   与项目「不得为 PASS 而自行解释」的纪律冲突。
③ 因此建议（仅建议，非结论）：在**提交 P14 IMPLEMENTATION AUTHORIZATION 之前**
   由 Human 就 OPTION 1 / 2 / 3 择一裁定，并据此 amend 文档集合或扩展既有载体。
④ 本轮**不创建**任何 Contract 文档；不修改 RUNTIME_DOCUMENT_SET_DECISION.md。
```

---

# 6. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
新增文档 = 本报告（+ 同轮 3 份）· 未创建 Contract
commit = 0 · tag = 0 · push = 0
P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 CONTRACT GAP ANALYSIS（2026-09-27 · GAP-C1…C4 登记 · OPTION 1/2/3 已枚举 · 未选择 · 未创建 Contract）**
