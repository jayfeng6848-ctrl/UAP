# UAP — P14 PRIVILEGE DECISION IMPACT ANALYSIS

> ## 状态与边界
>
> ```text
> 轮次      = P14 PRIVILEGE / SECURITY HUMAN DECISION PREPARATION
> 性质      = 影响登记（只登记影响，**不修改任何冻结文件**）
> 三态标记   = NO CHANGE（无需变更）
>             CANDIDATE CHANGE AFTER HUMAN DECISION（裁定后可能需要变更）
>             MUST CHANGE AFTER HUMAN DECISION（裁定后必须变更）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · 0018+ = 0 · Security Gate = DECISION READY
> 本轮未做   = CREATE ROLE / GRANT / REVOKE / DDL / DML / migration / runtime code = 0 · 未 commit/tag/push
> ```

---

# 1. 影响面清单（10 个对象）

```text
O-1  P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md（FROZEN）
O-2  P14_RUNTIME_PRIVILEGE_MATRIX.md（PROPOSED）
O-3  P14_RUNTIME_SLICE_SCOPE.md
O-4  P14_RUNTIME_SLICE_DEPENDENCY_MAP.md
O-5  P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md
O-6  P14 Runtime Implementation（尚未开始）
O-7  Bootstrap（尚未开始）
O-8  Authorization（runtime 侧）
O-9  Identity（runtime 侧）
O-10 Audit
O-11 Future module isolation
```

---

# 2. SEC-P14-01 — Runtime Principal Model

```text
O-1  Contract            : MUST CHANGE AFTER HUMAN DECISION（若选 A/B-复用 uap_app：
                           必须显式重述 PB-1/PB-2；若选 C：PB-4 的"独立 principal"得到具体化，
                           属**追加细化**而非改写）
O-2  Privilege Matrix    : MUST CHANGE（principal 主体确定后，矩阵的"who"列才能落地）
O-3  Scope               : CANDIDATE CHANGE（若 principal 归属改变边界表述）
O-4  Dependency Map      : CANDIDATE CHANGE（§2.4 database access model 需引用具体 principal）
O-5  Acceptance          : MUST CHANGE（PRV-1 / PRV-3 / PRV-8 的判据对象需具体化）
O-6  Runtime Impl        : MUST CHANGE（全部落库路径的实现前提）
O-7  Bootstrap           : CANDIDATE CHANGE（若 bootstrap principal 与 runtime principal 同源）
O-8  Authorization       : CANDIDATE CHANGE（读路径身份）
O-9  Identity            : CANDIDATE CHANGE（写路径身份）
O-10 Audit               : CANDIDATE CHANGE（审计写入身份）
O-11 Future isolation    : MUST CHANGE（模块复用的 principal 策略取决于本裁决）
```

---

# 3. SEC-P14-02 — Runtime Principal Trust Boundary

```text
O-1  Contract            : CANDIDATE CHANGE（§2 Security Boundary / §12 需引用边界定义）
O-2  Privilege Matrix    : CANDIDATE CHANGE（§5 禁则中"禁止复用 migration role"可具体化）
O-3  Scope               : NO CHANGE
O-4  Dependency Map      : CANDIDATE CHANGE（§2.4 与 §3 的身份归属表述）
O-5  Acceptance          : MUST CHANGE（PRV-3「migration 身份不被 runtime 取得」+ PRV-8
                           「Runtime 未使用 uap_migrator」的判据需按边界定义细化）
O-6  Runtime Impl        : MUST CHANGE（连接身份与凭据装配）
O-7  Bootstrap           : CANDIDATE CHANGE（若 bootstrap 归属"Migration/Seed/Administrative"）
O-8  Authorization       : NO CHANGE
O-9  Identity            : NO CHANGE
O-10 Audit               : NO CHANGE
O-11 Future isolation    : CANDIDATE CHANGE（未来模块是否允许进入同一边界）
```

---

# 4. SEC-P14-03 / 04 — Runtime Read / Write Scope

```text
O-1  Contract            : NO CHANGE（Contract 只定义边界原则；具体清单不写入冻结正文）
O-2  Privilege Matrix    : MUST CHANGE（REQUIRED / NOT REQUIRED / UNKNOWN 三态须清零并落表）
O-3  Scope               : CANDIDATE CHANGE（若某对象整体排除 ⇒ 影响 Excluded 清单）
O-4  Dependency Map      : NO CHANGE
O-5  Acceptance          : MUST CHANGE（PRV-1 的"与授权清单精确一致"判据依赖本裁决；
                           SEC/IDL/AUT 各条目的依赖关系可能微调）
O-6  Runtime Impl        : MUST CHANGE（实现面边界）
O-7  Bootstrap           : CANDIDATE CHANGE（若 platform_memberships / platform_state 被排除）
O-8  Authorization       : MUST CHANGE（读侧清单决定判定实现可行性）
O-9  Identity            : MUST CHANGE（写侧清单决定 onboarding/凭据/设备实现可行性）
O-10 Audit               : CANDIDATE CHANGE（audit_logs 写是否纳入）
O-11 Future isolation    : CANDIDATE CHANGE（新模块的授权申请流程）
```

---

# 5. SEC-P14-05 — Tenants / Spaces Access

```text
O-1  Contract            : CANDIDATE CHANGE（若允许 runtime 建/改 tenants/spaces ⇒ 需在
                           Contract §1「Runtime Scope」中明确，且与 P13 留白对齐）
O-2  Privilege Matrix    : MUST CHANGE（tenants / spaces 行的 REQUIRED/UNKNOWN 三态清零）
O-3  Scope               : MUST CHANGE（Included 是否含租户/空间建立）
O-4  Dependency Map      : CANDIDATE CHANGE（§2.1 identity 与 tenant 的关系）
O-5  Acceptance          : CANDIDATE CHANGE（新增租户/空间相关判定行）
O-6  Runtime Impl        : CANDIDATE CHANGE（若纳入 ⇒ 新增实现面）
O-7  Bootstrap           : CANDIDATE CHANGE（bootstrap 是否创建首个租户 —— 目前 D-P13-05 = 不创建）
O-8  Authorization       : CANDIDATE CHANGE（tenant scope 判定的数据来源）
O-9  Identity            : CANDIDATE CHANGE（主体与租户的关联时点）
O-10 Audit               : CANDIDATE CHANGE（租户/空间事件是否审计）
O-11 Future isolation    : CANDIDATE CHANGE（跨租户隔离策略）
```

---

# 6. SEC-P14-06 — Memberships Access

```text
O-1  Contract            : CANDIDATE CHANGE（membership 归属须在 Contract §3/§5 体现）
O-2  Privilege Matrix    : MUST CHANGE（memberships / tenant_memberships / platform_memberships 三行）
O-3  Scope               : MUST CHANGE（Included/Excluded 的成员关系面）
O-4  Dependency Map      : CANDIDATE CHANGE（§2.2 authorization 的 membership 依赖）
O-5  Acceptance          : CANDIDATE CHANGE（membership 变更的判定行）
O-6  Runtime Impl        : CANDIDATE CHANGE
O-7  Bootstrap           : MUST CHANGE（platform_memberships 的写权限归属 —— 与 SEC-P14-13 联动）
O-8  Authorization       : CANDIDATE CHANGE（判定需读 membership 范围）
O-9  Identity            : NO CHANGE
O-10 Audit               : CANDIDATE CHANGE（membership 变更是否审计）
O-11 Future isolation    : CANDIDATE CHANGE
```

---

# 7. SEC-P14-07 — Events / Resources Access

```text
O-1  Contract            : CANDIDATE CHANGE（若启用 outbox / resource 写入 ⇒ 需在 Contract §1 明确）
O-2  Privilege Matrix    : MUST CHANGE（events / resources 两行三态清零）
O-3  Scope               : MUST CHANGE（outbox 与资源本体是否在 P14 范围内）
O-4  Dependency Map      : CANDIDATE CHANGE（events 属 P10 outbox 面）
O-5  Acceptance          : CANDIDATE CHANGE（新增 events/resources 判定行）
O-6  Runtime Impl        : CANDIDATE CHANGE（若启用 ⇒ 新增实现面）
O-7  Bootstrap           : NO CHANGE
O-8  Authorization       : NO CHANGE（除非资源写入引入授权需求）
O-9  Identity            : NO CHANGE
O-10 Audit               : CANDIDATE CHANGE（events 与 audit 的边界）
O-11 Future isolation    : CANDIDATE CHANGE
```

---

# 8. SEC-P14-08 — Credential Lifecycle

```text
O-1  Contract            : CANDIDATE CHANGE（credential DELETE 语义须在 §4 明确；
                           若禁用 physical delete ⇒ §4 CC-4/CC-5 的表述需补充）
O-2  Privilege Matrix    : MUST CHANGE（credentials 行的 DELETE = UNKNOWN 须清零）
O-3  Scope               : NO CHANGE（凭据面已在 Included）
O-4  Dependency Map      : NO CHANGE
O-5  Acceptance          : MUST CHANGE（IDL-2 / IDL-3 的判据细化；若禁 DELETE ⇒ 新增负向判据）
O-6  Runtime Impl        : MUST CHANGE（凭据生命周期实现）
O-7  Bootstrap           : CANDIDATE CHANGE（bootstrap 凭据是否同一生命周期机制）
O-8  Authorization       : NO CHANGE
O-9  Identity            : MUST CHANGE（credential 与 identity 的分离边界）
O-10 Audit               : CANDIDATE CHANGE（凭据事件审计 action 定义）
O-11 Future isolation    : NO CHANGE
```

---

# 9. SEC-P14-09 — Resource Permission Write Side

```text
O-1  Contract            : CANDIDATE CHANGE（若 runtime 只读 ⇒ 强化 §6 AC-3/AC-6 表述；
                           若允许写 ⇒ 属**授权扩张**，须另立决策并评估 escalation）
O-2  Privilege Matrix    : MUST CHANGE（resource_permissions 行的写侧三态清零）
O-3  Scope               : CANDIDATE CHANGE（若允许写 ⇒ Included 扩展）
O-4  Dependency Map      : CANDIDATE CHANGE（§2.2）
O-5  Acceptance          : MUST CHANGE（新增/细化 ACL 写侧判定与负向判据）
O-6  Runtime Impl        : CANDIDATE CHANGE
O-7  Bootstrap           : NO CHANGE
O-8  Authorization       : MUST CHANGE（判定与授权管理的边界）
O-9  Identity            : NO CHANGE
O-10 Audit               : CANDIDATE CHANGE（ACL 变更是否审计）
O-11 Future isolation    : CANDIDATE CHANGE
```

---

# 10. SEC-P14-10 — Authorization Read Path

```text
O-1  Contract            : CANDIDATE CHANGE（§6 AC-1 已有 centralized precheck；
                           最终读路径形态可能需在 §6/§7 细化）
O-2  Privilege Matrix    : MUST CHANGE（读侧主体与范围随之确定）
O-3  Scope               : NO CHANGE
O-4  Dependency Map      : CANDIDATE CHANGE（§2.2 的读取路径）
O-5  Acceptance          : MUST CHANGE（AUT-4 判据按最终路径细化）
O-6  Runtime Impl        : MUST CHANGE（中间件与 service 的调用链）
O-7  Bootstrap           : NO CHANGE
O-8  Authorization       : MUST CHANGE（这是其核心实现形态）
O-9  Identity            : NO CHANGE
O-10 Audit               : CANDIDATE CHANGE（判定拒绝事件是否审计）
O-11 Future isolation    : CANDIDATE CHANGE（未来模块的授权读取是否复用同一路径）
```

---

# 11. SEC-P14-11 / 12 / 13 — Bootstrap Identity / Credential / Authority

```text
O-1  Contract            : MUST CHANGE AFTER HUMAN DECISION（§8 BR-1…BR-7 需纳入
                           执行身份与凭据来源；§13 Privilege Precondition 需更新为"已裁决"）
O-2  Privilege Matrix    : MUST CHANGE（bootstrap 面权限归属）
O-3  Scope               : CANDIDATE CHANGE（§2.6 bootstrap CLI 的实现边界）
O-4  Dependency Map      : CANDIDATE CHANGE（§2.4 与 P13 留白）
O-5  Acceptance          : MUST CHANGE（OPS-3 / AUD-3 / AUDX-2 判据按身份与凭据细化）
O-6  Runtime Impl        : CANDIDATE CHANGE（若 bootstrap principal 与 runtime 分离 ⇒ 影响装配）
O-7  Bootstrap           : MUST CHANGE（核心对象）
O-8  Authorization       : NO CHANGE
O-9  Identity            : CANDIDATE CHANGE（首个管理员主体与凭据的建立时点）
O-10 Audit               : MUST CHANGE（'platform.admin.bootstrap' 的写入身份与粒度）
O-11 Future isolation    : CANDIDATE CHANGE（未来恢复/迁移路径）
```

---

# 12. SEC-P14-14 — Privilege Granting Strategy

```text
O-1  Contract            : CANDIDATE CHANGE（若采用 view/function/service-mediated 路径，
                           需在 §7/§12 体现；注意**不得新增 schema 对象**除非另立授权）
O-2  Privilege Matrix    : MUST CHANGE（矩阵落地形态：逐表 / 逐列 / 视图 / 服务中介）
O-3  Scope               : CANDIDATE CHANGE（若引入 view/function 路径 ⇒ 触及 schema 边界）
O-4  Dependency Map      : CANDIDATE CHANGE（访问路径形态）
O-5  Acceptance          : MUST CHANGE（PRV-1/PRV-2/PRV-4 判据形态）
O-6  Runtime Impl        : MUST CHANGE（访问实现方式）
O-7  Bootstrap           : CANDIDATE CHANGE（bootstrap 亦须遵循同策略）
O-8  Authorization       : CANDIDATE CHANGE
O-9  Identity            : CANDIDATE CHANGE
O-10 Audit               : CANDIDATE CHANGE（若经 function/view，审计点位置变化）
O-11 Future isolation    : MUST CHANGE（授权申请与复用规范）
```

---

# 13. 汇总

```text
MUST CHANGE（裁定后必须变更）出现次数最多的对象：
  O-2 Privilege Matrix（10 次）· O-5 Acceptance（10 次）· O-1 Contract（4 次）
  O-6 Runtime Impl（6 次）· O-7 Bootstrap（3 次）· O-8 Authorization（3 次）· O-9 Identity（3 次）

NO CHANGE（全部 14 项下均无需变更）：
  无（各对象至少在 1 项决策下需关注）

说明：
  · 所有变更均为"裁定后**候选**"，本轮**不执行**任何变更
  · O-1（Contract）为 FROZEN 文件；其变更须待 Human 裁定后由**授权轮**执行，且只能 append-only
    或经 Human 明示的修订流程（不删除历史）
```

---

# 14. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · CREATE ROLE / GRANT / REVOKE = 0
新增文档 = 本文件（+ 同轮 2 份）· 未修改任何冻结文件 · commit = 0 · tag = 0 · push = 0
P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

## 15. Resolution Sync（append-only · 2026-09-27 · Human Decision 已下达）

> 本节把 §2–§12 的 `CANDIDATE CHANGE AFTER HUMAN DECISION` 推进为
> **`NO CHANGE`** 或 **`MUST CHANGE AFTER SECURITY IMPLEMENTATION`**。
> 本轮**不执行**任何变更（含不修改 Contract / Scope / Dependency / Acceptance 的冻结正文）。

```text
规则：
  · 情形一：与裁决无冲突、或裁决与既有冻结表述方向一致 ⇒ **NO CHANGE**
  · 情形二：裁决要求后续细化/扩充承载 ⇒ **MUST CHANGE AFTER SECURITY IMPLEMENTATION**
  · 若发现必须修改**冻结语义** ⇒ 不自行覆盖，改为 amendment proposal（本轮 0 项）
```

```text
SEC-01（DEDICATED RUNTIME PRINCIPAL）
  O-1 Contract   : NO CHANGE（与 PB-4 方向一致，属其具体化；无需改冻结正文）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION（"who" 须填入 principal 名）
  O-3 Scope      : NO CHANGE       O-4 Dependency : NO CHANGE
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（PRV-1/3/8 判据主体具体化）
  O-6 Runtime    : MUST CHANGE（实现前提）    O-7 Bootstrap : NO CHANGE
  O-8/O-9/O-10   : NO CHANGE                  O-11 Future   : MUST CHANGE（模块复用规范）

SEC-02（TRUSTED INTERNAL SERVICE BOUNDARY）
  O-1 Contract   : NO CHANGE（SB-1..SB-3 / PB-3/PB-4 已覆盖）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION（禁则具体化）
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（PRV-3 / PRV-8 细化）
  O-4 Dependency : NO CHANGE（§2.4 已含身份分离表述）· O-3/O-7..O-11 : NO CHANGE

SEC-03 / SEC-04（Read / Write Scope）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION（三态已闭合，须落表）
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（PRV-1 判据依赖最终清单）
  O-1 Contract   : NO CHANGE（Contract 仅定义原则）· O-3 Scope : NO CHANGE
  O-8/O-9        : MUST CHANGE AFTER SECURITY IMPLEMENTATION（实现可行性前提）
  O-10 Audit     : NO CHANGE（已含）· O-11 Future : NO CHANGE

SEC-05（TENANTS / SPACES = SELECT ONLY）
  O-1 Contract   : NO CHANGE（Contract 未要求 Runtime 建租户；与 D-P13-05 一致）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION
  O-3 Scope      : NO CHANGE（§2.3 已如此表述）· O-5 Acceptance : NO CHANGE
  O-8..O-11      : NO CHANGE

SEC-06（MEMBERSHIPS）
  O-1 Contract   : NO CHANGE（§3/§5 已含受控 use-case 语义）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION
  O-7 Bootstrap  : NO CHANGE（platform 面已归 SEC-13）
  O-5/O-8/O-10   : NO CHANGE · O-9 : NO CHANGE

SEC-07（EVENTS / RESOURCES）
  O-1 Contract   : NO CHANGE（§1 未排除；属 Runtime Scope 内）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION
  O-3 Scope      : NO CHANGE（events/resources 属正常 data path，与 §2 一致）
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（新增路由判定行）
  O-10 Audit     : NO CHANGE

SEC-08（NO PHYSICAL DELETE）
  O-1 Contract   : MUST CHANGE AFTER SECURITY IMPLEMENTATION（§4 需补充 "no physical delete" 表述）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION（credentials DELETE = DENY）
  O-9 Identity   : NO CHANGE（凭据与身份分离已冻结）
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（负向判据）

SEC-09（RESOURCE_PERMISSIONS WRITE = DENY）
  O-1 Contract   : NO CHANGE（§6 AC-3/AC-6 已含）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION
  O-8 Authorization : NO CHANGE（读路径不变；写侧 DENY）
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（self-escalation 负向判据）

SEC-10（HYBRID READ PATH）
  O-1 Contract   : MUST CHANGE AFTER SECURITY IMPLEMENTATION（§6 需追加 HYBRID 细化）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION
  O-6 Runtime    : MUST CHANGE（authorization service 形态）
  O-8 Authorization : MUST CHANGE AFTER SECURITY IMPLEMENTATION（核心实现形态）
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（AUT-4 判据细化）

SEC-11 / 12 / 13（BOOTSTRAP）
  O-1 Contract   : MUST CHANGE AFTER SECURITY IMPLEMENTATION（§8 / §13 需纳入身份、凭据与归属）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION（bootstrap 面）
  O-7 Bootstrap  : MUST CHANGE AFTER SECURITY IMPLEMENTATION（核心对象）
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（OPS-3 / AUD-3 / AUDX-2 细化）
  O-10 Audit     : NO CHANGE（既有 'platform.admin.bootstrap' 语义）
  O-9 Identity   : NO CHANGE · O-8 : NO CHANGE

SEC-14（EXACT LEAST-PRIVILEGE GRANT STRATEGY）
  O-1 Contract   : NO CHANGE（PB-2/PB-5/PB-6 已含最小权限与"另开 Gate"要求）
  O-2 Matrix     : MUST CHANGE AFTER SECURITY IMPLEMENTATION（落地形态：逐表/逐列/视图）
  O-3 Scope      : NO CHANGE（不引入新对象）
  O-5 Acceptance : MUST CHANGE AFTER SECURITY IMPLEMENTATION（PRV-1/2/4 判据形态）
  O-6/O-7/O-11   : MUST CHANGE AFTER SECURITY IMPLEMENTATION（访问实现方式与规范）
```

```text
汇总（Resolution Sync 后）
  NO CHANGE                                   : 多数 O-1 / O-3 / O-4 / O-10 条目
  MUST CHANGE AFTER SECURITY IMPLEMENTATION    : 集中于 O-2（矩阵）· O-5（验收）·
                                                O-6（Runtime 实现）· O-7（Bootstrap）·
                                                O-8（Authorization）· O-11（Future isolation）
  amendment proposal 需求（修改冻结语义）        : **0 项**

⇒ 本轮**不修改** Contract / Scope / Dependency / Acceptance 的冻结正文；
   全部变更留待 **Security Implementation Gate**（须另行授权）。
P14 IMPLEMENTATION = NOT AUTHORIZED · HARD STOP = ACTIVE
```

---

**END OF P14 PRIVILEGE DECISION IMPACT ANALYSIS（2026-09-27 · §15 Resolution Sync 追加 · 14 项决策 × 11 对象影响已推进为 NO CHANGE / MUST CHANGE AFTER SECURITY IMPLEMENTATION · 未执行任何变更）**
