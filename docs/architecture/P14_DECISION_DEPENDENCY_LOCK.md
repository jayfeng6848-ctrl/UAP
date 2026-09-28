# UAP — P14 DECISION DEPENDENCY LOCK

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — HUMAN DECISION SHEET PREPARATION（Phase 4）
> 性质      = 依赖锁定表（只读分析 + 文档）；**不含任何 Decision**
> 基线      = HEAD c420403d… · migration 0017_p13_seed · stage P14_RUNTIME_SLICE · Decision status PENDING
> 本轮未做   = 无 schema 变更 · 无 migration · 无 GRANT/REVOKE · 无 DML · 无 runtime code · 未 commit/tag/push
> ```

---

# 1. ROOT BLOCKERS（无上游 · 阻塞面最大）

```text
★ ADD-2（决策登记位置）
  Depends on            : 无
  Blocks                : 其余全部 14 项裁定的**登记落点**
  Can proceed before    : 任何内容裁定（与内容无关）
  Cannot proceed before : 无（自身即最先可决项）
  说明                   : 元决策；未定则首批裁定无处登记，可能需二次搬运。

★ OQ-P14-13（runtime privilege boundary）
  Depends on            : 无
  Blocks                : OQ-P14-01 · OQ-P14-02 · OQ-P14-03 · OQ-P14-04（读侧）· OQ-P14-09 ·
                          identity runtime · authorization middleware · bootstrap CLI · onboarding flow
  Can proceed before    : 与 OQ-P14-12 并行（两者互补：12 收窄边界，13 决定权限路径）
  Cannot proceed before : 无（自身即根）
  说明                   : 唯一"存在性"问题——未定则一切需读写数据库的行为无法落地。

★ OQ-P14-12（C2 trust boundary usage）
  Depends on            : 无
  Blocks                : OQ-P14-01 / OQ-P14-13 的边界收窄（排除"改 registry 绕开权限"分支）
  Can proceed before    : 与 OQ-P14-13 并行
  Cannot proceed before : 无
  说明                   : 低成本的边界声明；决定 SEC-2 / IDL-5 的判据前提。
```

---

# 2. 逐决策锁定表

## Batch 0 — Governance Meta

```text
ADD-2 (Decision register location)
  Depends on            : —
  Blocks                : 全部其余裁定的登记
  Can proceed before    : 任何内容裁定
  Cannot proceed before : —

ADD-1 (Contract carrier)
  Depends on            : ADD-2（若取"Contract 内附录"则与 ADD-2 强耦合）
                          以及 Batch 1–3 的结论（实施规则需有内容可写）
  Blocks                : 实施规则载体（F-4）· 实施授权轮的"规则齐备"条件
  Can proceed before    : 可先就"是否新增载体"作原则裁定
  Cannot proceed before : 不能在 ADD-2 之前定"登记位置"相关内容
```

## Batch 1 — Security Root

```text
OQ-P14-13
  Depends on            : —（根）
  Blocks                : OQ-01 · OQ-02 · OQ-03 · OQ-04（读侧）· OQ-09 · 全部写/读路径
  Can proceed before    : OQ-P14-12（并行）
  Cannot proceed before : —

OQ-P14-12
  Depends on            : —
  Blocks                : OQ-13 / OQ-01 的候选空间边界
  Can proceed before    : OQ-P14-13（并行）
  Cannot proceed before : —
```

## Batch 2 — Identity Foundation

```text
OQ-P14-01 (onboarding flow)
  Depends on            : OQ-P14-13（写路径）· OQ-P14-12（边界）
  Blocks                : OQ-P14-02 · OQ-P14-03 · identity runtime · onboarding flow
  Can proceed before    : OQ-P14-04/05（判定层，二者独立）
  Cannot proceed before : OQ-P14-13 · OQ-P14-12

OQ-P14-02 (credential lifecycle)
  Depends on            : OQ-P14-01 · OQ-P14-10（secret 注入）· OQ-P14-13
  Blocks                : onboarding flow 实现 · bootstrap（管理员凭据）· OQ-P14-11
  Can proceed before    : OQ-P14-04/05
  Cannot proceed before : OQ-P14-01 · OQ-P14-13

OQ-P14-03 (device / user association)
  Depends on            : OQ-P14-01 · OQ-P14-02
  Blocks                : identity runtime 的多设备面（非阻塞骨架）
  Can proceed before    : OQ-P14-04/05/06
  Cannot proceed before : OQ-P14-01 · OQ-P14-02
```

## Batch 3 — Authorization Runtime

```text
OQ-P14-04 (permission check location)
  Depends on            : OQ-P14-13（读侧权限存在性）
  Blocks                : OQ-P14-05 · OQ-P14-06 · OQ-P14-07 · OQ-P14-08 · authorization middleware
  Can proceed before    : OQ-P14-01/02（身份面独立）
  Cannot proceed before : OQ-P14-13

OQ-P14-05 (policy enforcement boundary)
  Depends on            : OQ-P14-04 · OQ-P14-13
  Blocks                : authorization middleware 实现 · AUT-3/AUT-4 判据固化
  Can proceed before    : OQ-P14-01/02/03
  Cannot proceed before : OQ-P14-04
```

## Batch 4 — Runtime Interface

```text
OQ-P14-06 (API boundary)
  Depends on            : OQ-P14-04 · OQ-P14-07
  Blocks                : OQ-P14-08 · API boundary 实现
  Can proceed before    : OQ-P14-01/02/03
  Cannot proceed before : OQ-P14-04 · OQ-P14-07

OQ-P14-07 (service ownership)
  Depends on            : OQ-P14-04
  Blocks                : OQ-P14-06
  Can proceed before    : OQ-P14-01/02
  Cannot proceed before : OQ-P14-04

OQ-P14-09 (bootstrap process)
  Depends on            : OQ-P14-13 · OQ-P14-02
  Blocks                : bootstrap CLI 实现 · 平台初始化
  Can proceed before    : OQ-P14-04/05/06/07
  Cannot proceed before : OQ-P14-13 · OQ-P14-02
```

## Batch 5 — Operations

```text
OQ-P14-10 (deployment model)
  Depends on            : OQ-P14-02（secret 托管）
  Blocks                : OQ-P14-11 · 部署落地
  Can proceed before    : OQ-P14-04…09（多数）
  Cannot proceed before : OQ-P14-02（若采用自管凭据，则强耦合 secret 通道）

OQ-P14-08 (failure handling)
  Depends on            : OQ-P14-06
  Blocks                : —（实施期细化）
  Can proceed before    : OQ-P14-10/11
  Cannot proceed before : OQ-P14-06

OQ-P14-11 (observability)
  Depends on            : OQ-P14-10 · OQ-P14-08
  Blocks                : —（实施期迭代）
  Can proceed before    : 其余多数项
  Cannot proceed before : OQ-P14-10
```

---

# 3. 可并行组（分析）

```text
并行组 1（内容根）：OQ-P14-13 · OQ-P14-12
并行组 2（身份 vs 授权）：{OQ-P14-01 → 02 → 03}  ∥  {OQ-P14-04 → 05}
并行组 3（接口与运维）：{OQ-P14-07 → 06} ∥ {OQ-P14-10 → 11} ∥ {OQ-P14-09}
完全独立（可与任意批次并行）：ADD-2 · ADD-1（原则层）
```

---

# 4. 解锁判定（进入 Implementation Authorization 的必要条件 · 分析）

```text
① ADD-2 已裁（登记位置确定）
② ADD-1 已裁（实施规则载体确定）
③ OQ-P14-13 / OQ-P14-12 已裁（根阻塞解除 + 边界明确）
④ Batch 2 / 3 / 4 中 A 类各项（01 · 02 · 04 · 05 · 09）已裁
⑤ 若 OQ-P14-13 结论要求 GRANT 面变更 ⇒ 已另行取得独立授权轮
⑥ ACCEPTANCE_MATRIX 的 PENDING 项已按裁定更新或明确保留
⑦ 无遗留 active contradiction
```

---

# 5. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
本文件不含 Decision；P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 DECISION DEPENDENCY LOCK（2026-09-27 · ROOT BLOCKERS = OQ-P14-13 / OQ-P14-12 / ADD-2 · 未作裁定）**
