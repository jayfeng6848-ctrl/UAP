# UAP — P14 PRIVILEGE / SECURITY DECISION LOCK

> ## 状态与边界
>
> ```text
> 轮次      = P14 PRIVILEGE / SECURITY HUMAN DECISION PREPARATION
> 性质      = 依赖锁定（只读分析 + 文档）；**不含任何裁定**
> 基线      = HEAD c420403d… · migration 0017_p13_seed · Security Gate = DECISION READY
> 本轮未做   = CREATE ROLE / ALTER ROLE / GRANT / REVOKE / DDL / DML / migration /
>             runtime code / bootstrap implementation = 0 · 未 commit/tag/push
> ```

---

# 1. 正式依赖链（本指令 §六）

```text
SEC-P14-01  Runtime Principal Model
        ↓
SEC-P14-03  Runtime Required Read Scope      ∥   SEC-P14-04  Runtime Required Write Scope
        ↓
SEC-P14-10  Authorization Read Path
        ↓
SEC-P14-11  Bootstrap Execution Identity   ∥  SEC-P14-12  Bootstrap Credential Source
        ↓
SEC-P14-13  platform_memberships / platform_state Bootstrap Authority
        ↓
SEC-P14-14  Privilege Granting Strategy
        ↓
Security Gate Approval（由 Human 明确）
        ↓
Runtime DB implementation（须另获 P14 IMPLEMENTATION AUTHORIZATION）
```

---

# 2. 逐项锁定

```text
SEC-P14-01  Runtime Principal Model
  Depends on            : —（根）
  Blocks                : SEC-02 · SEC-03 · SEC-04 · SEC-05 · SEC-06 · SEC-07 · SEC-08 · SEC-09 ·
                          SEC-10 · SEC-11 · SEC-13 · SEC-14
  Can proceed before    : —
  Cannot proceed before : —

SEC-P14-02  Runtime Principal Trust Boundary
  Depends on            : SEC-01
  Blocks                : SEC-04（写侧边界）· SEC-11（bootstrap 身份归属）· SEC-14
  Cannot proceed before : SEC-01

SEC-P14-03  Runtime Required Read Scope
  Depends on            : SEC-01 · SEC-02
  Blocks                : SEC-10（读取路径）· SEC-14
  Cannot proceed before : SEC-01 · SEC-02

SEC-P14-04  Runtime Required Write Scope
  Depends on            : SEC-01 · SEC-02
  Blocks                : SEC-05 · SEC-06 · SEC-07 · SEC-08 · SEC-09 · SEC-14
  Cannot proceed before : SEC-01 · SEC-02

SEC-P14-05  Tenants / Spaces Access
  Depends on            : SEC-01 · SEC-03 · SEC-04
  Blocks                : SEC-06（成员关系与容器关系）· SEC-14
  Cannot proceed before : SEC-03 · SEC-04

SEC-P14-06  Memberships Access
  Depends on            : SEC-01 · SEC-04 · SEC-05
  Blocks                : SEC-13（platform membership 归属）· SEC-14
  Cannot proceed before : SEC-04 · SEC-05

SEC-P14-07  Events / Resources Access
  Depends on            : SEC-01 · SEC-04
  Blocks                : SEC-14
  Cannot proceed before : SEC-04

SEC-P14-08  Credential Lifecycle
  Depends on            : SEC-01 · SEC-04
  Blocks                : SEC-11 / SEC-12（bootstrap 凭据是否同机制）· SEC-14
  Cannot proceed before : SEC-04

SEC-P14-09  Resource Permission Write Side
  Depends on            : SEC-01 · SEC-03（读侧）· SEC-04
  Blocks                : SEC-10（授权管理的边界）· SEC-14
  Cannot proceed before : SEC-04

SEC-P14-10  Authorization Read Path
  Depends on            : SEC-01 · SEC-03 · SEC-09
  Blocks                : SEC-14 · Runtime Authorization 实现
  Cannot proceed before : SEC-03

SEC-P14-11  Bootstrap Execution Identity
  Depends on            : SEC-01 · SEC-02 · SEC-08
  Blocks                : SEC-13 · Bootstrap 实现
  Cannot proceed before : SEC-01 · SEC-02

SEC-P14-12  Bootstrap Credential Source
  Depends on            : SEC-11 · SEC-08
  Blocks                : SEC-13 · Bootstrap 实现
  Cannot proceed before : SEC-11

SEC-P14-13  platform_memberships / platform_state Authority
  Depends on            : SEC-06 · SEC-11 · SEC-12
  Blocks                : SEC-14 · Bootstrap 实现
  Cannot proceed before : SEC-11 · SEC-12

SEC-P14-14  Privilege Granting Strategy
  Depends on            : SEC-01…SEC-13（全部）
  Blocks                : Security Gate Approval · 未来授权执行轮
  Cannot proceed before : SEC-01…SEC-13
```

---

# 3. 并行组（分析）

```text
并行组 1（内容根）  : SEC-01（独立）
并行组 2            : SEC-03 ∥ SEC-04（均依赖 01/02）
并行组 3            : SEC-05 ∥ SEC-06 ∥ SEC-07 ∥ SEC-08 ∥ SEC-09（依赖 03/04）
并行组 4            : SEC-10（依赖 03/09）
并行组 5            : SEC-11 → SEC-12 → SEC-13（链式）
并行组 6            : SEC-14（依赖全部）
完全独立            : 无（本组全部以 SEC-01 为根）
```

---

# 4. 硬性规则（依赖纪律）

```text
DL-1  任何前置 Decision 未解决，后置 Decision 不得伪装成已冻结
DL-2  **Security Gate ≠ Implementation Authorization**
DL-3  Human Decision 完成只表示 **DECISION COMPLETE**，
      不自动表示 **IMPLEMENTATION AUTHORIZED**
DL-4  在 SEC-01…SEC-14 全部裁决完成之前，Security Gate 不得进入 APPROVED 状态
DL-5  在 Security Gate 完成之前，不得执行 CREATE ROLE / GRANT / REVOKE /
      runtime implementation / database onboarding implementation / bootstrap implementation
DL-6  即使全部裁决完成，Runtime DB 实现仍须取得独立的 `P14 IMPLEMENTATION AUTHORIZATION`
```

---

# 5. P14 Security Decision Update Evidence（OI-G-1 专门章节）

> 本节回应本指令 §七：OI-G-1 本轮**不得关闭**，仅登记更新证据。

```text
OI-G-1 原始登记：「runtime 逐表 DML 矩阵不可核定（不得扩权）」· REGISTERED（BATCH-D）
本轮状态：**OI-G-1 = OPEN / ACTIVE**（未关闭）

5.1 本轮解决了哪些 UNKNOWN？
  · 文档层面：已把全部 UNKNOWN **映射为明确的 Human Decision 问题**
    （tenants/spaces/memberships → SEC-05/06 · events/resources → SEC-07 ·
     resource_permissions 写侧 → SEC-09 · credential DELETE → SEC-08 ·
     bootstrap 身份 → SEC-11 · bootstrap 凭据 → SEC-12 ·
     platform_memberships/platform_state 归属 → SEC-13）
  · **实质裁决：0 项**（本轮为 preparation，Human 尚未裁决）

5.2 哪些仍 UNKNOWN？
  · 上述全部（在 Human 裁决前保持 UNKNOWN，按 DENY 处理）

5.3 Runtime principal 是否已经决定？        → **否**（SEC-01 待裁）
5.4 Privilege Matrix 是否已可冻结？          → **否**（仍为 PROPOSED；
    待 SEC-03/04/05/06/07/08/09 裁决后，方可能由 PROPOSED → FROZEN-CANDIDATE）
5.5 Bootstrap identity 是否已经决定？        → **否**（SEC-11 待裁）
5.6 Credential source 是否已经决定？          → **否**（SEC-12 待裁）

5.7 是否仍存在"证据不足不得关闭"的理由？      → **是**，理由：
    (a) 逐表矩阵仍有 UNKNOWN 未清零（矩阵的行级三态未闭合）
    (b) principal 模型未定 ⇒ "who" 维度缺失，矩阵不完整
    (c) bootstrap 权限归属未定 ⇒ 平台初始化路径不可验证
    (d) 授权策略（SEC-14）未定 ⇒ 矩阵的落地形态未定
  ⇒ **结论：OI-G-1 保持 OPEN**；本轮的
     `P14_RUNTIME_PRIVILEGE_MATRIX.md` + 本文件 = **其正式更新证据候选**（登记备案）

5.8 何时可考虑关闭？
  · 仅当**后续 Security Implementation Gate 真正具备完整证据**时（即：逐表矩阵三态闭合 ∧
    principal 与授权策略已裁决 ∧ 授权执行轮已完成并验证 ∧ 负向探针通过）
  · 本轮不满足上述任一，故不关闭
```

---

# 6. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0
新增文档 = 本文件（+ 同轮 2 份）· 未修改任何冻结文件 · commit = 0 · tag = 0 · push = 0
P14 IMPLEMENTATION = NOT AUTHORIZED · HARD STOP = ACTIVE
```

---

# 7. Resolution Sync（append-only · 2026-09-27 · Human Decision 已下达）

> 本节为**追加**：§1–§6 的依赖锁定与 OI-G-1 记录保持为历史分析；
> 本节登记裁决后的实际状态。

## 7.1 裁决落点（依 SEC-P14-01…14）

```text
SEC-01 = OPTION C（DEDICATED RUNTIME PRINCIPAL）        ← 本锁定的**根节点**已解
SEC-02 = TRUSTED INTERNAL SERVICE BOUNDARY
SEC-03 = explicit required-read allowlist（UNKNOWN → DENY）
SEC-04 = use-case + operation 精确授予
SEC-05 = RUNTIME = SELECT ONLY（tenants / spaces）
SEC-06 = 普通 memberships 受控 use-case；platform_memberships 属 Bootstrap 边界
SEC-07 = events/resources S/I/U 允许（use-case 限定）· DELETE = DENY
SEC-08 = NO PHYSICAL DELETE
SEC-09 = RUNTIME WRITE = DENY（resource_permissions）
SEC-10 = HYBRID（Central Authorization Service + Restricted DB Read）
SEC-11 = DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL
SEC-12 = LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT
SEC-13 = BOOTSTRAP-OWNED INITIALIZATION
SEC-14 = EXACT LEAST-PRIVILEGE GRANT STRATEGY
```

## 7.2 依赖链状态（裁决后）

```text
SEC-01（已决）→ SEC-02（已决）→ SEC-03 / 04（已决）→ SEC-05…09（已决）→
SEC-10（已决）→ SEC-11 / 12（已决）→ SEC-13（已决）→ SEC-14（已决）
        ↓
Security Gate Approval（**尚未**由 Human 明确为 APPROVED —— 本轮仅完成 DECISION FREEZE）
        ↓
Runtime DB implementation（**NOT AUTHORIZED**）

⇒ 依赖链：**全部节点已裁决**；但 DL-2/DL-3 仍生效：
   Security Gate ≠ Implementation Authorization；
   Human Decision 完成 = DECISION COMPLETE，不等于 IMPLEMENTATION AUTHORIZED。
```

## 7.3 OI-G-1 证据状态更新（§5 的追加）

```text
OI-G-1 = **OPEN**（本轮不关闭 · 状态未变）

已决定（本轮新增证据）：
  principal                     = DEDICATED RUNTIME PRINCIPAL（SEC-01）
  required read scope           = explicit allowlist（SEC-03）
  write scope                   = use-case + operation 精确（SEC-04）
  bootstrap identity            = DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL（SEC-11）
  bootstrap credential source   = LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT（SEC-12）
  authorization path            = HYBRID（SEC-10）
  grant strategy                = EXACT LEAST-PRIVILEGE（SEC-14）
  privilege matrix 状态          = HUMAN-DECISION-RESOLVED / IMPLEMENTATION INPUT（UNKNOWN = 0）

仍未满足关闭条件（依 §5.8 的四条）：
  (a) 逐表矩阵三态已闭合 ✔  —— 本轮已达成
  (b) principal 与授权策略已裁决 ✔ —— 本轮已达成
  (c) **授权执行轮尚未完成**（principal / role / GRANT 尚未创建与授予）✘
  (d) **负向探针与正向断言证据尚不存在** ✘
  ⇒ 因 (c)(d) 未满足 ⇒ **OI-G-1 保持 OPEN**

关闭时机：仅当后续 **Security Implementation Gate** 完成授权执行并产出
          （正向断言 + 负向探针）证据后，方考虑关闭。
```

## 7.4 本节边界

```text
本轮：CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0 ·
      DDL / DML / migration / runtime code = 0 · commit / tag / push = 0
Security Decision = **FROZEN** · Security Implementation = **NOT STARTED** ·
P14 IMPLEMENTATION = **NOT AUTHORIZED** · HARD STOP = ACTIVE
```

---

**END OF P14 PRIVILEGE / SECURITY DECISION LOCK（2026-09-27 · §7 Resolution Sync 追加 · 14 项全部裁决 · `OI-G-1 = OPEN`（证据已更新，(c)(d) 未满足）· Security Decision = FROZEN）**
