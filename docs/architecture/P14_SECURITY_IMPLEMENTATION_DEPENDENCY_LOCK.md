# UAP — P14 SECURITY IMPLEMENTATION DEPENDENCY LOCK

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CANONICAL REGISTRATION + IMPLEMENTATION GATE PREPARATION
> 性质      = 依赖锁定（设计输入）；**未实施任何权限**
> 基线      = HEAD c420403d… · migration 0017_p13_seed · DB 0017_p13_seed · 0018+ = 0
> 本轮未做   = CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0 ·
>             DDL / DML / migration / runtime code = 0 · 未 commit / tag / push
> ```

---

# 1. 正式依赖链（本指令 §十七）

```text
PDL Canonical Registration（附录 O）
        ↓
Security Decision Frozen（SEC-P14-01…14）
        ↓
Privilege / Grant Matrix（P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md）
        ↓
Runtime Principal Implementation Contract（目标状态：Gate Prep §1.1）
        ↓
Bootstrap Principal Implementation Contract（目标状态：Gate Prep §1.2）
        ↓
Negative + Positive Security Test Design（Gate Prep §2 / §3）
        ↓
Security Implementation Gate（须 Human 明确授权）
        ↓
**ONLY THEN**  CREATE ROLE / GRANT / REVOKE
        ↓
Runtime DB Integration
        ↓
Security Acceptance
```

---

# 2. 逐节点状态

```text
N-1  PDL Canonical Registration（附录 O）
      状态 = **DONE**（本轮 · append-only · pre-sha 7e80dc36… → post-sha 4775a686… ·
             前缀 3907 行零差异 · END 行 18 → 19）
      证据 = 本文件 + PDL 附录 O

N-2  Security Decision Frozen
      状态 = **DONE**（SEC-P14-01…14 = FROZEN · resolved 14 · UNKNOWN 0）
      证据 = PDL 附录 O · Decision Sheet Resolution Registry

N-3  Privilege / Grant Matrix
      状态 = **DONE（IMPLEMENTATION PROPOSAL）**
      证据 = P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md（逐操作行列 · 无 CRUD 行）

N-4  Runtime Principal Implementation Contract
      状态 = **DRAFT（目标状态已登记）** —— 见 P14_SECURITY_IMPLEMENTATION_GATE_PREP.md §1.1
      待定 = 角色命名 · INHERIT/NOINHERIT 最终选择 · 凭据注入通道实现形态

N-5  Bootstrap Principal Implementation Contract
      状态 = **DRAFT（目标状态已登记）** —— 见 Gate Prep §1.2
      待定 = 角色命名 · 凭据输入通道实现形态 · 一次性锁的运维规程

N-6  Negative + Positive Security Test Design
      状态 = **DONE（设计）** —— NP-R1…13 / NP-A1…3 / NP-M1…3 / NP-B1…4 · PA-R1…5 / PA-B1…4
      证据 = Gate Prep §2 / §3

N-7  Security Implementation Gate
      状态 = **READY（待 Human 授权）**
      注意 = READY ≠ AUTHORIZED

N-8  CREATE ROLE / GRANT / REVOKE
      状态 = **NOT EXECUTED**（本轮 = 0）

N-9  Runtime DB Integration
      状态 = **NOT STARTED**

N-10 Security Acceptance
      状态 = **NOT STARTED**
```

---

# 3. 硬性规则（依赖纪律）

```text
DL-1  **Decision Frozen ≠ Implementation Authorized**
DL-2  前置节点未完成，后置节点不得伪装为已完成（尤其 N-7 未授权前不得执行 N-8）
DL-3  Security Implementation Gate = READY 不构成授权；
      执行 CREATE ROLE / GRANT / REVOKE 须**独立 Human 授权**（下一轮）
DL-4  若实施过程中出现下列任一情形 ⇒ **STOP**：
        · 需要修改 C2 / CC-7
        · 需要 schema 变更 / 0018+ migration
        · 需要 default ACL 变更
        · 目标 grant 要求 Runtime principal 获得 ownership / DDL / CREATE ROLE / CREATE SCHEMA /
          ALTER TABLE / DROP
        · 需要 uap_migrator 进入 Runtime path
        · 需要 Runtime principal 继承 bootstrap authority
DL-5  授权执行轮完成后，须产出：正向断言 + 负向探针 + 角色/授权快照 → 方可进入 N-9
DL-6  OI-G-1 仅在 N-8 完成且证据齐备后才考虑关闭（当前 OPEN）
```

---

# 4. OI-G-1 状态（本指令 §十九）

```text
OI-G-1 = **OPEN / ACTIVE**

证据链更新：
  principal            = DECIDED（SEC-01）
  grant strategy       = DECIDED（SEC-14）
  bootstrap ownership  = DECIDED（SEC-13）

剩余关闭前置条件（全部未满足）：
  · actual principal implementation（N-4 / N-5 落地）
  · actual grants（N-8）
  · actual negative probes（N-6 执行）
  · actual positive assertions（N-6 执行）
  · actual security acceptance evidence（N-10）

⇒ OI-G-1 = OPEN 是正确状态
```

---

# 5. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · bootstrap implementation = 0
CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0
PDL = 仅追加 附录 O（append-only · 已验证前缀零差异）
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
P14 IMPLEMENTATION = NOT AUTHORIZED · HARD STOP = ACTIVE
```

---

**END OF P14 SECURITY IMPLEMENTATION DEPENDENCY LOCK（2026-09-27 · N-1…N-10 依赖链锁定 · N-7 = READY（非 AUTHORIZED）· `OI-G-1 = OPEN`）**
