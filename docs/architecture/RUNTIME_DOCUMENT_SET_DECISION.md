# UAP — RUNTIME DOCUMENT SET DECISION

> ## 轮次与边界
>
> ```text
> 轮次     = STEP 2 Runtime Slice 正式定义冻结 · Phase 3（文档集合冻结）
> 依据     = D-PLAT-12.a ③「正式编号及文档集合须在 PREP 门冻结」
>            + Human 指令「STEP 2 — RUNTIME SLICE FORMAL DEFINITION FREEZE」（2026-09-27）
> 本文件   = 决策记录（append-only 新增）；**不创建**任何 implementation / migration / runtime code
> 冻结登记 = `PLATFORM_DECISION_LOG.md` 附录 M（M.3 ②）
> ```

---

# 1. 决策摘要

```text
采用者 = 指令建议的 4 份文档集合（命名逐字采纳）
数量调整 = 不减少
Security Boundary 独立文档 = **不新增**（改为 SCOPE 文档内的强制章节；理由见 §4）
阶段编号 = `P14_RUNTIME_SLICE`（FROZEN · 见 PDL 附录 M.1）
```

---

# 2. 冻结的文档集合（4 份 · FROZEN）

以下路径与文件名自本决策生效起为 **Runtime Slice 的正式文档集合**（本轮**仅冻结结构，不创建 implementation**）：

```text
docs/architecture/P14_RUNTIME_SLICE_PREP_REPORT.md
docs/architecture/P14_RUNTIME_SLICE_SCOPE.md
docs/architecture/P14_RUNTIME_SLICE_DEPENDENCY_MAP.md
docs/architecture/P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md
```

各文档职责（冻结）：

```text
P14_RUNTIME_SLICE_PREP_REPORT.md
  职责 = PREP 轮主报告：baseline · 实测现状 · 设计面盘点 · unknown questions ·
          required human decisions · 拟议验收策略 · 轮次边界与自证偏差

P14_RUNTIME_SLICE_SCOPE.md
  职责 = Included / Excluded 边界 · 强制章节「Security Boundary」（见 §4）·
          与 P13 / Governance Slice 的接口 · 明确非目标

P14_RUNTIME_SLICE_DEPENDENCY_MAP.md
  职责 = 依赖图（Schema Layer → Authorization/Data Baseline → Runtime Layer）·
          逐项输入依赖 · 缺失依赖登记 · 与既有 guards（G-1…G-8 · D-PLAT-17）的关系

P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md
  职责 = 验收项（可机械判定 PASS / FAIL）· 失败条件 · 证据要求 · 硬门 / advisory 划分引用
```

---

# 3. 命名规范一致性核验

```text
既有阶段文档命名先例：P09_* / P10_* / P11_* / P12_* / P13_*
  · <PHASE>_PREP_REPORT.md          → P09/P10/P11/P12/P13 均存在
  · <PHASE>_SCOPE.md                → P09 存在
  · <PHASE>_DEPENDENCY.md           → P09/B1-4/B1-5/B1-6 存在
  · <PHASE>_ACCEPTANCE_MATRIX.md    → P10/P11/P12/P13 均存在
⇒ 本集合命名与既有规范一致；不引入新后缀体系。
  （说明：既有 `*_DEPENDENCY.md` 与 `*_DEPENDENCY_MAP.md` 两种后缀并存，
    本集合采用指令给定的 `_DEPENDENCY_MAP.md`；如需与 P09 完全对齐可改为 `_DEPENDENCY.md`，
    属命名微调，需 Human 明示。）
```

---

# 4. 关于 Security Boundary 文档（不新增独立文件 · 理由）

```text
判定 = 不新增第 5 份独立文档；改为 `P14_RUNTIME_SLICE_SCOPE.md` 内**强制章节**。

理由：
① Runtime Slice **不引入新的授权模型 / 不新增 schema**（见边界决策 §5），
   其安全面基本由既有机制承载：C2/CC-7 受信迁移边界 · uap_app ↔ uap_migrator 身份分离 ·
   G-1…G-8 依赖守卫（D-PLAT-17 硬门划分）· P10 audit 面。
② 项目既有实践：安全面在阶段文档中以**章节**承载（如 P13_IMPLEMENTATION_CONTRACT §14 Trigger Contract、
   P09_SECURITY_REVIEW），仅在需要独立审查线时才单列文件（B1-4/B1-5/B1-6_SECURITY_REVIEW）。
③ 避免 carrier 增殖：4 份已覆盖 PREP / Scope / Dependency / Acceptance 四类必要面。

强制章节要求（写入 SCOPE 文档时必须覆盖）：
  · runtime 身份（uap_app）与 migration 身份（uap_migrator）不得互相获得对方权限
  · 不得放宽 C2 / CC-7 · 不得 DISABLE TRIGGER · 不得引入 GUC / application_name 信任
  · 不得新增 GRANT / 不得改 ownership / 不得改 default ACL
  · 凭据与 onboarding 设密流的 secret 边界（D-P13-13 的延续）
  · 审计面：runtime 事件是否写 audit_logs 及 actor 语义（Runtime 决策，非 P13 决策）

⇒ 若 Human 要求独立 Security Boundary 文档，按同命名规范追加：
   `P14_RUNTIME_SLICE_SECURITY_BOUNDARY.md`（须另行授权）。
```

---

# 5. 与阶段编号冻结的关系

```text
阶段编号 `P14_RUNTIME_SLICE` = FROZEN（PDL 附录 M.1 · tentative → formally frozen）
文档集合                    = FROZEN（本文件 §2）
⇒ 自本决策生效起，以上 4 个路径名可作为正式引用使用。
⇒ 但**创建**这些文档属后续 `P14 RUNTIME SLICE PREP` 轮的工作；
   本决策**不**创建它们（本轮仅冻结结构与命名）。
```

---

# 6. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · services 目录 = 未创建 · API = 未创建
新增文件 = 本文件（+ 同轮 P14_RUNTIME_SLICE_FORMALIZATION_GATE_REPORT.md）
PDL 变更 = 附录 M（EOF 纯追加）+ 1 条新 END 行 + `D-PLAT-12.a` 下方指针块（纯插入）
commit = 0 · tag = 0 · push = 0
```

---

**END OF RUNTIME DOCUMENT SET DECISION（2026-09-27 · 文档集合 4 份已冻结 · Security Boundary 以 SCOPE 强制章节承载 · P14 IMPLEMENTATION = NOT AUTHORIZED）**
