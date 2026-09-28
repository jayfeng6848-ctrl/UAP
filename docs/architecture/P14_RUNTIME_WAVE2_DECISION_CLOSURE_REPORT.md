# UAP — P14 RUNTIME WAVE 2 DECISION CLOSURE REPORT

> ## 状态
>
> ```text
> 轮次      = P14 WAVE 2 HUMAN DECISION FREEZE
> 性质      = 决策冻结证明（**未实现任何 Wave 2 代码**）
> 基线      = HEAD c420403d5469241e8b03855428ebce435d539c9e · branch main · tags 9 · remote 0
>             migration 0017_p13_seed · 0018+ = 0 · Wave 1 = ACCEPTED
> 权威载体   = P14_RUNTIME_WAVE2_HUMAN_DECISION_SHEET.md §R（Resolution Registry）
>             + PLATFORM_DECISION_LOG.md 附录 P（canonical registration · append-only）
> ```

---

# 1. 冻结计数（§四十一 证明项）

```text
Decision 总数                = **36**
RESOLVED                     = **36**
unresolved                   = **0**
UNKNOWN                      = **0**
不再 PENDING 的 Root Blocker   = 5（SCOPE-W2-01 · VOC-W2-01…04）
REPURPOSED（Human 以该 ID 承载不同裁定）= 7
  SCOPE-W2-01 · AUTH-W2-01 · SEC-W2-01 · SEC-W2-02 · SEC-W2-03 · SEC-W2-04 · SEC-W2-05
DERIVED（由明文条款推导并注明出处）= 9
  SCOPE-W2-01(节点组成) · ID-W2-01 · ID-W2-05(device 不连带) · DV-W2-05 · SS-W2-05(UTC/即时) ·
  CTX-W2-01(assurance) · AUTH-W2-03 · API-W2-04(conflict/validation) · SEC-W2-01(重复创建可观测性) ·
  SEC-W2-03/SEC-W2-04/SEC-W2-05(原问题归属)
其余 = EXPLICIT（Human 明文条款直接裁定）

ID 唯一性                     = 无重复 · 无编号冲突（全仓扫描 36 个 W2 decision ID 各 1 次）
ID 复用                       = 0（未使用既有 D-* / SEC-P14-* / RTA-* / OQ-* 编号）
```

---

# 2. 逐项 Resolution 摘要

> 完整字段（Selected / Basis / Rationale / Affected boundary / Implementation consequence /
> Related frozen decision / Contract impact / Schema impact）见 PDL 附录 P §P.3–§P.10。

```text
Batch 0  Governance / Root
  SCOPE-W2-01  不修改 0017；Persistence Adapter / Anti-Corruption Mapping；全链同轮
  VOC-W2-01    C 双根显式映射（Domain=Identity 语义中心；anchor=users.id）
  VOC-W2-02    A 以 0017 credential 词表为准（第一期仅 password）
  VOC-W2-03    A 采用 device 五态 persistence truth
  VOC-W2-04    C 两套状态并存 + 显式映射（user 5 态 / identity 4 态）

Batch 1  Identity
  ID-W2-01     A public onboarding + fail-closed 约束
  ID-W2-02     A identities：unverified→active→suspended→revoked
  ID-W2-03     A 全局唯一（trim+lower / 大小写不敏感 / 软删除后释放）
  ID-W2-04     C credential 同时绑定 identity 与 user（且一致）
  ID-W2-05     CUSTOM revoke 传播矩阵（identity→revoked + 凭据 revoke + 同事务 session revoke）

Batch 2  Device
  DV-W2-01     B eligible user + challenge + verification ⇒ active
  DV-W2-02     B per-user fingerprint 唯一（既有约束）+ 应用层补充
  DV-W2-03     A 既有 schema 载体承载 challenge（禁止新增 device_challenges）
  DV-W2-04     A device→revoked 与其 active sessions→revoked 必须同事务原子
  DV-W2-05     A 旧设备继续有效；不 auto-kick；并发 enrollment 需幂等/单次消费

Batch 3  Session
  SS-W2-01     A human session 必须已验证设备（use-case 强制）；schema nullable 不改
  SS-W2-02     A active→expired/revoked；使用 replaced_by / absolute_expires_at
  SS-W2-03     CUSTOM granular revoke 矩阵（logout/device/identity/credential/admin）
  SS-W2-04     B 每设备允许多 session；不增 UNIQUE(device_id)；不自动踢旧登录
  SS-W2-05     B 部署配置参数；双上限；refresh 不得延长 absolute；每请求校验

Batch 4  Authenticated Context
  CTX-W2-01    A 7 项最小组成（含 authentication assurance）
  CTX-W2-02    CUSTOM tenant/space fail-closed 矩阵（无 active membership ⇒ DENY）
  CTX-W2-03    A observability 白名单（9 字段 · 禁 secret/hash）
  CTX-W2-04    A context 只带标识；AuthorizationRequest 由 service 构造

Batch 5  Authorization
  AUTH-W2-01   只消费 allow/deny；REQUIRES_APPROVAL = DEFERRED / OUT OF SCOPE
               + 复用 Stage 2 · subject=authenticated user · 评估顺序冻结
  AUTH-W2-02   A 判定只在 service + Stage 2；handler 仅适配
  AUTH-W2-03   A Wave 2 写 audit（身份/设备/会话关键事件 · payload 白名单）

Batch 6  API
  API-W2-01    A transport / adaptation only
  API-W2-02    A 与 Wave 2 同轮（路由面受 §三十一 清单限定）
  API-W2-03    A HTTP→adapter→context→authz→service
  API-W2-04    A 显式错误映射；全部 fail-closed；禁止 anonymous fallback

Batch 7  Security
  SEC-W2-01    authentication fail-closed DENY 清单（含 authorization unknown）
  SEC-W2-02    no credential leakage（logs/trace/metrics/audit/response/exception）
  SEC-W2-03    replay resistance（bounded lifetime · single-use · explicit consumption）
  SEC-W2-04    revoke propagation（identity/device/credential）+ 事务边界
  SEC-W2-05    no privilege expansion（无 role/grant/C2/CC-7/uap_runtime 边界变更）
```

---

# 3. Contract Divergence D-1…D-9 关闭证明（§三十七）

```text
D-1  聚合根                     → RESOLVED BY MAPPING（§四/§五）
D-2  credential type            → RESOLVED BY MAPPING（§七）
D-3  device status              → RESOLVED BY MAPPING（§八）
D-4  identity status            → RESOLVED BY MAPPING（§十）
D-5  identity kind vs provider  → RESOLVED BY MAPPING（§六）
D-6  user status                → RESOLVED BY MAPPING（§九）
D-7  credential algorithm       → RESOLVED BY MAPPING（§三十三）
D-8  session status             → NOT A DIVERGENCE（Domain 与 DB 已一致）
D-9  permission effect          → DEFERRED / OUT OF SCOPE（§二十六）

⇒ Contract divergence unresolved = **0**
⇒ ACTIVE UNKNOWN = **0**（§三十七 明确禁止留下 ACTIVE UNKNOWN）
```

---

# 4. 零-隐含性证明（§四十一 的 6 项 0）

```text
UNKNOWN = 0
  依据：36/36 均有 Selected（含 7 项 REPURPOSED + 9 项 DERIVED，DERIVED 全部引用明文条款号）

Contract divergence unresolved = 0
  依据：§3 的 9 项全部落到 RESOLVED BY MAPPING / NOT A DIVERGENCE / DEFERRED

Schema dependency unresolved = 0
  依据：§三十五 裁决 "New schema object required for Wave 2 = NO"；
        SCHEMA_DEPENDENCY_REGISTER = EMPTY / OPEN（NO NEW SCHEMA OBJECT REQUIRED）；
        DV-W2-03 仅保留"若证明必须则 STOP 并开独立 Schema Decision"的**条件式**路径（非未决项）

Security ambiguity = 0
  依据：§三十六 五项 Security Resolution 全量明文；SEC-W2-05 明确 0 扩权；
        Security Grant Gap = NONE（既有 51 项授权覆盖 Wave 2 主链操作）

Implicit state = 0
  依据：状态词表全部显式取自 0017（users 5 态 / identities 4 态 / devices 5 态 /
        sessions 3 态 / credentials lifecycle）；"verification in progress" 明确限定为
        Application Workflow State，不得写入 persisted status（§十一）

Implicit vocabulary = 0
  依据：credential type（§七）· device status（§八）· permission effect（§二十六）·
        subject/action/scope/effect 既有冻结词表全部显式声明；
        禁止 domain enum 未经 mapping 直接写库（§三 / §七）
```

---

# 5. 治理不变量声明（§一 / §三十八）

```text
EXISTING 0017 SCHEMA          = PERSISTENCE TRUTH
DOMAIN SEMANTICS              = EXPLICIT DOMAIN / INFRASTRUCTURE MAPPING

Schema                        = **unchanged**
Domain                        = **semantically normalized through explicit mapping**
Divergence                    = **acknowledged + resolved by boundary**
Migration                     = **0**

⇒ 本报告**不**主张"Domain 与 Schema 已一致"；只主张"分歧已被显式边界消解"。
⇒ 历史 divergence 证据（WAVE2_SCOPE §5 / SCHEMA_DEPENDENCY_REGISTER §3 /
   DECISION_IMPACT_ANALYSIS）**全部保留**，未删除、未改写为"从来不存在分歧"。
```

---

# 6. 边界输出（§四十六 · 决策输出 · 非 implementation evidence）

```text
Existing Grants Sufficient = YES
New Grant Required         = NO
New Role Required          = NO
New Schema Object Required = NO
Migration Required         = NO
C2 Change Required         = NO
CC-7 Change Required       = NO

说明：以上为 **Decision Resolution 的输出**，不构成任何 implementation 证据，
      也不构成对"实现期不会出现新需求"的承诺；实现期若出现 ⇒ 登记对应 Gap 并 STOP。
```

---

# 7. 与既有冻结决策的一致性

```text
零改写（实测）
  PDL 附录 A–O    ：未修改（append-only 追加附录 P）
  既有 D-* 正文    ：未修改
  SEC-P14-01…14   ：未修改（Wave 2 只消费）
  D-OP101-01…14   ：未修改
  D-P13-01…15     ：未修改
  RTA-01…10       ：未修改（RTA-09/10 仍为 OPTION B）
  Wave 1 Evidence Freeze（FINAL ACCEPTANCE §28）：未触发 FOUNDATION REGRESSION RISK

冲突扫描
  · 无决议与既有 SEC-P14-* 冲突
  · 无决议要求修改 C2 / CC-7 / P13 seed
  · 无决议要求新 role / 新 grant（SEC-W2-05 明文禁止）
```

---

# 8. 已知排版缺陷披露（诚实性）

```text
`P14_RUNTIME_WAVE2_HUMAN_DECISION_SHEET.md` 的**章节物理顺序**与逻辑批次顺序不一致
（本轮 append 插入锚点选择有误）。

内容完整性：36 个 Decision 区块各出现且仅出现一次 —— 无删除、无重复、无改写。
影响范围  ：纯排版（可读性）；**不影响**任何决议内容与 canonical registration。
权威记录  ：§R Resolution Registry（文件开头）+ PDL 附录 P。
处置      ：已在 Sheet §0.0 显式披露物理顺序与 canonical 阅读顺序；
            机械重排留待 BATCH-D（属 cosmetic maintenance，不阻断任何 Gate）。
```

---

# 9. 本轮工程变更

```text
新增文档 = 本文件
更新文档 = PDL（append 附录 P）· HUMAN_DECISION_SHEET（§R / §0.0 / 汇总 / footer）·
           DECISION_IMPACT_ANALYSIS · DECISION_DEPENDENCY_LOCK · ACCEPTANCE_MAPPING ·
           IMPLEMENTATION_AUTHORIZATION_SHEET（保持未授权声明）· SCHEMA_DEPENDENCY_REGISTER
未改动   ：任何 runtime code / identity / device / session / API / bootstrap CLI /
           migration / DDL / DML / role / grant / revoke / alter role / 0017 schema
Git      ：HEAD / branch / tags / remote 未变 · staged = 0 · 历史 dirty set 未 stage
DB       ：formal `uap` 未变 · `uap_b1_test` 未变 · commit / tag / push = 0
```

**END OF P14 RUNTIME WAVE 2 DECISION CLOSURE REPORT（2026-09-28 · 36/36 FROZEN · UNKNOWN 0 · Schema unchanged · Migration 0 · Wave 2 Implementation = NOT STARTED · HARD STOP ACTIVE）**
