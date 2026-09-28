# UAP — P14 RUNTIME SLICE FORMALIZATION GATE REPORT

> ## 轮次与边界
>
> ```text
> 轮次     = STEP 2 — RUNTIME SLICE FORMAL DEFINITION FREEZE
> 本轮未做 = 未创建 runtime code · 未创建 services 目录 · 未创建 API · 未创建 migration ·
>            未创建 schema · 未创建 P14 implementation 文件 · 未修改 P13 migration ·
>            未修改任何冻结 Decision 正文 · 未 commit / tag / push
> 本轮已做 = 治理复核（Phase 1）· 阶段编号正式冻结（Phase 2）· 文档集合冻结（Phase 3，
>            见 RUNTIME_DOCUMENT_SET_DECISION.md）· 附录 C 裁决（Phase 4）·
>            Boundary 定义（Phase 5）· PREP 入口条件（Phase 6）
> 冻结登记 = PLATFORM_DECISION_LOG.md 附录 M（EOF 纯追加）+ D-PLAT-12.a 下方指针块（纯插入）
> ```

---

# 1. Phase 1 — RUNTIME_STAGE_GOVERNANCE_REVIEW

## 1.1 为什么 Runtime 必须晚于 P13

```text
D-PLAT-12（FROZEN）：
  决策 = Runtime **必须在 P10、P11、P12、P13 完成并验收后**开始；
         Runtime 开工前必须先定义正式阶段文档、范围、依赖与验收门。
  影响面 = Runtime 的起点被硬性绑定于 P13 验收通过。

P09 侧旁证（D-P09-07 = A · FROZEN）：
  P09 = SCHEMA ONLY —— 明确排除 agent/ 代码层 runtime、Agent Runtime、Tool Runtime、
  HTTP API / Socket / Worker / Scheduler / Celery、AI Provider / AI Route runtime。

技术理由（数据层强制）：
  Runtime 需要「可认证主体 + 可判定授权 + 可审计事件」三件套；
  这三者分别由 0005/0007（授权与 ACL）、0012（action canonical）、0013（events/audit_logs）、
  0014（triggers）、0015（indexes）、0016（trust boundary）、0017（P13 seed baseline）承载。
  ⇒ 在这些结构就位之前启动 runtime，等于在无授权基线、无审计面的库上运行（default deny 下不可用，
     或被迫扩权 ⇒ 违反 D-B14-02「提前实施 = 静默扩权」的先例）。

现状：P13 已 IMPLEMENTED & PERSISTED、已 ACCEPTED、已 commit（c420403d）、已 tag（UAP-V0.1.9-P13-SEED）
⇒ D-PLAT-12 的前置条件**已满足**，Runtime 路线的 PREP 门**可以合法开启**。
```

## 1.2 Runtime 与 Governance Slice 的边界

```text
D-PLAT-13（FROZEN · 2026-09-23 经 Human 正式裁定 · Q-1 APPROVED）：
  ① Governance / Gate Slice = **独立 Slice**，**不属于** Runtime Slice；
  ② 其内容 = 迁移治理 + 层边界门控（配置门 · readiness schema 门 · legacy 启动路径停用 · 依赖守卫），
     **不含任何业务运行时能力**；
  ③ D-PLAT-12 / 12.a 原文与 FROZEN 状态保持不变；
  ④ Runtime 阶段名称与编号继续保持 provisional，其冻结属未来 PREP 门（= **本轮**）；
  ⑤ **本 Slice 不是 `P14`** —— 不得创建任何 `P14` 文件、引用或阶段编号。

该 Slice 的状态（实测）：GOVERNANCE_GATE_SLICE_IMPLEMENTATION_REPORT.md
  Status = IMPLEMENTATION COMPLETE · VERIFICATION COMPLETE · ACCEPTANCE READY（2026-09-23）
  相关冻结决策 = D-PLAT-14（readiness 配置键/失败语义）· D-PLAT-15 v2（期望 revision 注入形态）·
                 D-PLAT-16（readiness 探针独立短超时 2000 ms）· D-PLAT-17（Guard 门级划分）
  ⇒ 边界结论：Governance Slice **提供 Runtime 的前置治理门**（配置门 / readiness 门 / 依赖守卫），
     但**不提供**任何 runtime 能力；两者不可混称。
```

## 1.3 当前暂定名称的治理状态（冻结前）

```text
D-PLAT-12.a（FROZEN · 来源 OD-8）：
  ① 路线名 = `STEP 2 — Runtime Slice`
  ② 首阶段**暂定** = `P14_RUNTIME_SLICE`
  ③ **正式编号及文档集合须在 PREP 门冻结**
  待确认 ⚠ 「暂定」⇒ 不得在 PREP 门之前作为既成编号使用；不得据 `P14` 创建任何文件或引用
  影响面（冻结时点）= `P14` 全仓 0 命中；`RUNTIME_SLICE` / `Runtime Slice` 亦 0 命中

⇒ 冻结前状态 = **provisional（暂定）**；本轮的 PREP 门即为解除该暂定状态的唯一合法时点。
```

## 1.4 当前允许冻结的内容

```text
① 阶段编号（`P14_RUNTIME_SLICE`）—— tentative → formally frozen
② 正式文档集合与命名（4 份）
③ 附录 C 的 C-8（是否加注 STEP1B_SCHEMA_DEPENDENCY 的 P06–P13 表）与 C-9（架构依赖图关联）
④ Runtime Slice 的 Scope Boundary（Included / Excluded）
⑤ Runtime Slice PREP 的入口条件

不允许（本轮）：创建 runtime code / services / API / schema / migration ·
                修改任何冻结 Decision 正文 · 修改 P13 migration · commit / tag / push
```

---

# 2. Phase 2 — 阶段编号正式冻结（登记路径）

```text
previous : `P14_RUNTIME_SLICE` = tentative
current  : `P14_RUNTIME_SLICE` = **formally frozen**（本 PREP 门 · 2026-09-27）
路线名    : `STEP 2 — Runtime Slice`（正式冻结）

登记载体（append-only · 既有冻结正文零改写）：
  · PLATFORM_DECISION_LOG.md → 附录 M（EOF 纯追加）
  · PLATFORM_DECISION_LOG.md → `D-PLAT-12.a` 下方指针块（纯插入）
  · 新增 1 条 END 行（旧 16 条 END 行全部保留）

登记路径说明：
  指令原拟使用 `D-PLAT-16` 作为登记 ID；**实测 `D-PLAT-16` 已被占用**
  （# D-PLAT-16 — readiness 迁移探针的独立短超时：2000 ms · 2026-09-23 · FROZEN），
  `D-PLAT-17`（Guard 门级划分）亦已占用。
  ⇒ 采用指令明确给出的替代路径：**在 `D-PLAT-12.a` 下新增正式登记附录**（附录 M）。
  ⇒ 若 Human 希望另立顶层条目（如 `D-PLAT-18`），须另行授权；本轮不自行编号。
```

---

# 3. Phase 3 — 文档集合冻结（摘要）

```text
冻结集合（4 份 · 命名逐字采纳指令建议）：
  docs/architecture/P14_RUNTIME_SLICE_PREP_REPORT.md
  docs/architecture/P14_RUNTIME_SLICE_SCOPE.md
  docs/architecture/P14_RUNTIME_SLICE_DEPENDENCY_MAP.md
  docs/architecture/P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md

数量：不减少（4 份覆盖 PREP / Scope / Dependency / Acceptance 四类必要面）
Security Boundary：**不新增独立文件**，作为 `P14_RUNTIME_SLICE_SCOPE.md` 的强制章节
   （理由与强制章节清单见 `RUNTIME_DOCUMENT_SET_DECISION.md` §4）
本轮不创建上述 4 份文档（仅冻结结构与命名）。
```

---

# 4. Phase 4 — 附录 C 裁决

## 4.1 C-8 — 是否将 Runtime Slice 加入 STEP1B_SCHEMA_DEPENDENCY 的 P06–P13 表

```text
裁定 = **RESOLVED：不加注**（采纳 D-PLAT-12.a 待确认项的原建议）

原则：
  STEP1B_SCHEMA_DEPENDENCY 的 P06–P13 表语义 = **schema 阶段链**；
  Runtime Slice **不属于 schema phase**、**不引入 schema**（见 §5 Excluded）。
  把 Runtime 写入该表会污染 schema 阶段语义（先例 D-PLAT-13：不引入 schema 阶段编号）。

记法（正式表述）：
  Runtime Slice = separate execution layer, not a schema dependency phase.

历史保护：**P06–P13 历史表零修改**（不插行、不加注、不重排）。
承载载体：本裁决 + PDL 附录 M + 未来 `P14_RUNTIME_SLICE_DEPENDENCY_MAP.md`。
```

## 4.2 C-9 — Runtime Slice 与架构依赖图的关联

```text
裁定 = **RESOLVED：确立三层关系模型**

  Schema Layer（0001–0017 迁移链：结构 + 约束 + 触发器 + 索引 + trust boundary）
        │
        ▼
  Authorization / Data Baseline（P13 seed：registry 3 · permissions 12 · role_permissions 12；
                                 身份隔离 = uap_migrator（migration）/ uap_app（runtime））
        │
        ▼
  Runtime Layer（P14_RUNTIME_SLICE：执行行为 / API-service 边界 / onboarding /
                 runtime 授权执行 / 运维接口）

语义约束：
  · 下层是上层的**前置**，反向依赖 = 0（Runtime 不得被 Schema/Data 层依赖）
  · 跨层约束仍由既有守卫承载：G-1…G-8（D-PLAT-17 硬门 / advisory 划分）
    （core ↛ SQLAlchemy/psycopg · core ↛ services · agent ↛ services ·
      domains ↛ {services, infrastructure} · apps ↛ SQLAlchemy/psycopg（advisory）等）
  · Runtime Layer 的依赖图详述登记于未来 `P14_RUNTIME_SLICE_DEPENDENCY_MAP.md`（本轮不创建）
  · 不修改任何既有依赖规则文档
```

---

# 5. Phase 5 — Runtime Slice Boundary（冻结）

## 5.1 Included（属于 Runtime Slice）

```text
· runtime execution layer（进程 / 服务宿主与生命周期）
· API / service boundary（对外接口层与其契约面）
· identity onboarding flow（首个可登录主体的建立与设密；承接 P13 未建 users/凭据的缺口）
· runtime authorization enforcement（以既有 RBAC/ABAC/resource ACL 面执行判定，不新增模型）
· operational interface（健康 / readiness 运维面，复用 D-PLAT-14/16 既有门）
· platform bootstrap CLI 的落地（首个平台管理员写入 platform_memberships；R4/R5 语义）
```

## 5.2 Excluded（明确不属于 Runtime Slice）

```text
· schema redesign
· migration（不新增 0018+；不改 0001–0017）
· permission vocabulary change（不改 D-AUTH-05 canonical action 词表；不改 P13 的 12 项）
· new authorization model（不改 RBAC/ABAC/ACL 模型；不新增 subject type）
· P13 seed modification（registry 3 / permissions 12 / role_permissions 12 不得改动）
· database ownership change（178 对象所有权拓扑不得变更）
· 不得放宽 C2 / CC-7 · 不得 DISABLE TRIGGER · 不得引入 GUC / application_name 信任
· 不得新增 GRANT / REVOKE / default ACL（除经独立 Human 授权的运维窗口）
```

---

# 6. Phase 6 — PREP Entry Criteria（Runtime Slice PREP 启动条件）

```text
必要条件（全部须为 PASS 方可启动 PREP）：

E-1 Stage ID frozen
    `P14_RUNTIME_SLICE` = formally frozen（PDL 附录 M.1）· 状态 = ✅ 本轮达成

E-2 Document set frozen
    4 份文档集合与命名已冻结（RUNTIME_DOCUMENT_SET_DECISION.md §2）· 状态 = ✅ 本轮达成

E-3 Dependency map frozen
    Schema → Authorization/Data Baseline → Runtime 三层关系与跨层约束已冻结（本报告 §4.2）·
    详图由未来 DEPENDENCY_MAP 承载 · 状态 = ✅ 本轮达成（关系冻结；详图待 PREP 产出）

E-4 Boundary frozen
    Included / Excluded 已冻结（本报告 §5）· 状态 = ✅ 本轮达成

E-5 Acceptance strategy defined
    验收策略载体已冻结（P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md 的职责与判据形态：
    机械判定 PASS/FAIL + 失败条件 + 证据要求 + 硬门/advisory 引用）· 状态 = ✅ 本轮达成

附加前置（沿用既有决策，非本轮新增）：
  · P13 ACCEPTED（已完成 · commit c420403d · tag UAP-V0.1.9-P13-SEED）
  · Governance / Gate Slice 已 ACCEPTANCE READY（D-PLAT-13/14/15/16/17）
  · 任何 migration / DDL 需求 ⇒ 必须另立独立授权（不得纳入 Runtime Slice）
```

---

# 7. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · services 目录 = 未创建 · API = 未创建
PDL 变更面 = 附录 M（EOF 纯追加）· 1 条新 END 行 · `D-PLAT-12.a` 下方指针块（纯插入）
            既有 `D-*` 正文零改写 · 无删除 · supersession 新增 = 0
新增文档 = RUNTIME_DOCUMENT_SET_DECISION.md · 本报告
未创建   = P14_RUNTIME_SLICE_{PREP_REPORT,SCOPE,DEPENDENCY_MAP,ACCEPTANCE_MATRIX}.md（留待 PREP 轮）
           P14_IMPLEMENTATION* · 0018* · runtime code
commit = 0 · tag = 0 · push = 0
```

---

# 8. Gate 结论

```text
RUNTIME FORMALIZATION = PASS
  Phase 1 治理复核         = COMPLETE（四问逐项作答）
  Phase 2 阶段编号冻结     = FROZEN（`P14_RUNTIME_SLICE` · tentative → formally frozen · PDL 附录 M）
  Phase 3 文档集合冻结     = FROZEN（4 份 · 命名逐字采纳）
  Phase 4 附录 C           = C-8 RESOLVED（不加注）· C-9 RESOLVED（三层关系模型）
  Phase 5 Boundary         = FROZEN（Included 6 项 / Excluded 8 类）
  Phase 6 PREP 入口条件     = E-1…E-5 全部达成

P14 IMPLEMENTATION = NOT AUTHORIZED（本报告不产生任何实施授权）
```

---

**END OF P14 RUNTIME SLICE FORMALIZATION GATE REPORT（2026-09-27 · `RUNTIME FORMALIZATION = PASS` · `P14_RUNTIME_SLICE` FROZEN · 文档集合 FROZEN · C-8/C-9 RESOLVED · `P14 IMPLEMENTATION = NOT AUTHORIZED`）**
