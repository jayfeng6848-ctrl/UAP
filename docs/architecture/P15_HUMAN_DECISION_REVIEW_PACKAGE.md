# UAP — P15 HUMAN DECISION REVIEW PACKAGE

> ```text
> 轮次 = STEP 3 · P15 HUMAN DECISION COMPLETION（2026-09-28）
> 性质 = 决策评审包（**未做任何选择** · 未实现 · 未改 schema/role/grant）
> Professional Default = 基于架构/安全/权限最小化/可维护性的推荐方向，
>                        **不代表 Human Decision 已完成**；最终选择权在 Human。
> 权限声明：Decision Review ≠ Implementation Authorization ≠ Migration Authorization ≠ Release Authorization
> ```

---

## P15-DEC-01 — P15 主题 / scope 组成

### Decision Question
P15 的主题与 scope 组成是什么？（决定后续 5 项决策的边界）

### Current Evidence
```text
· P14 已 RELEASED（0.1.10 · tag UAP-V0.1.10-P14-RUNTIME-SLICE）· P15 PREP = PASS（10 文档）
· 8 个候选（C-1…C-8）由 P14 遗留 + 现存资产推导（见 P15_CANDIDATE_SCOPE_DISCOVERY.md）
· P15 主题 = **UNKNOWN**（P15 PREP 未预设；须 Human 裁定）
```

### Option A — 运行时/后台能力优先（C-5 outbox consumer + C-8 审计深化）
```text
What changes: 新增 events/outbox 消费执行者与审计导出/上报语义
Benefits: 复用既有 events/audit 表（无 schema 变更）· 平台数据面闭环
Costs: 新增后台执行面（幂等/重放/审计语义需冻结）· 需 worker 边界决策
Security: Runtime security impact（新后台写入者 ⇒ SECURITY DECISION REQUIRED）
Schema: No（表已存在）· Runtime: 是 · Authorization: 部分（service 身份语义）
Migration: No · Testing: 幂等/重放/并发/审计 delta · Future impact: 高（事件驱动底座）
```

### Option B — 平台管理能力（C-2 管理类身份/设备/会话）
```text
What changes: 引入 admin-on-behalf-of-user（管理他人 device/session/credential）
Benefits: 补齐平台运营能力缺口
Costs: 触碰 authorization 词表/模型（Stage 2 不可自动扩展）
Security: **Authorization impact**（SECURITY + AUTHORIZATION DECISION REQUIRED）
Schema: 可能（新 action/effect 行 ⇒ SCHEMA DECISION REQUIRED）
Runtime: service 层 · Authorization: 是 · Migration: 可能 · Testing: deny 前置/越权全套
Future impact: 中（平台管理是该能力的前置）
```

### Option C — 基础设施与集成（C-4 Bootstrap CLI 或 C-6 AI 启用）
```text
What changes: 实现一次性 bootstrap 路径 或 启用 AI provider 链路
Benefits: 补齐安装期/能力期缺口
Costs: C-4 触及特权边界；C-6 触及外部调用与凭据注入
Security: **Privilege boundary / Runtime+AUDIT impact**（二者均需 SECURITY DECISION REQUIRED）
Schema: No（表/schema 已具备）· Runtime: 是 · Authorization: 部分 · Migration: No
Testing: 一次性不可重开 / provider 失败与超时语义 · Future impact: 高
```

### Option D — CUSTOM
```text
由 Human 指定主题组合（须同时指定顺序与授权范围）
```

### Professional Default
```text
不预设主题；建议先冻结 **scope 组合与顺序**（可含 maintenance/拒绝项），再逐项进入实现授权。
理由：其余 5 项决策的边界均取决于本项；过早选主题会把未评估的能力带进 P15。
UNKNOWN 保留：P15 最终主题选择 = UNKNOWN（证据不足以推荐具体主题）。
```

---

## P15-DEC-02 — 管理类能力与 authorization 词表

### Decision Question
是否引入 admin-on-behalf-of-user（管理他人 device/session/credential）？若是，走词表扩展还是独立模型？

### Current Evidence
```text
· FINDING-AUTHZ-1 = DEFERRED（P14 Wave2：自助操作以「认证 + 归属校验」强制）
· core/permission/vocabulary.py：ACTIONS = 12 canonical（无 identity/device/session 管理动作）
· EFFECTS = (ALLOW, DENY, REQUIRES_APPROVAL)；持久化 role_permissions.effect 仅 (allow, deny)
· 表：roles 1 行（platform_admin · PLATFORM）· permissions 12 · role_permissions 12
```

### Option A — 保持现状（不引入管理类能力）
```text
What changes: 无
Benefits: 零授权/零 schema 变更 · 维持最小权限与已验收边界
Costs: 平台运营需人工介入 DB 层
Security: No impact · Schema: No · Runtime: No · Authorization: No · Migration: No
Testing: 既有 Wave 2 deny 套件即覆盖 · Future impact: 需未来决策才可开放
```

### Option B — 引入并扩展 canonical action 词表
```text
What changes: 新增管理类 action（并可能新增 effect 行）· Stage 2 词表扩展
Benefits: 平台运营能力可通过既有授权模型审计
Costs: 触碰 P14 冻结词表与 seed（permissions/role_permissions 需新增行）
Security: **SECURITY + AUTHORIZATION DECISION REQUIRED**
Schema: 可能需要新增 action/effect 行（SCHEMA DECISION REQUIRED）
Runtime: service + API 新增受控端点 · Migration: 可能（seed）· Testing: 全套越权/deny 前置
Future impact: 高（但需承担词表治理成本）
```

### Option C — 引入但走独立 Approval/Decision model（不改 effect 词表）
```text
What changes: 新增独立审批/裁决模型承载管理类操作
Benefits: 不污染 allow/deny 语义 · 与 D-9（REQUIRES_APPROVAL deferred）方向一致
Costs: 新模型需独立 schema 支持（否则只能应用层）
Security: SECURITY DECISION REQUIRED · Schema: 可能（独立对象 ⇒ SCHEMA DECISION）
Runtime: service 层 · Authorization: 部分 · Testing: 审批链/越权/审计
Future impact: 高（审批语义未来必然需要）
```

### Professional Default
```text
Option A（保持现状）直到出现明确运营需求 + 完成 Authorization/Security 裁决。
理由：P14 已把该能力显式 DEFERRED；B 会触碰冻结词表与 seed，C 需要新对象；二者都超出"最小变更"。
```

---

## P15-DEC-03 — Bootstrap CLI 时机（RTA-09 = OPTION B）

### Decision Question
是否在 P15 实现 Bootstrap CLI（一次性本地 bootstrap）？

### Current Evidence
```text
· uap_bootstrap = 6 row grants（platform_state S/U · platform_memberships S/I · audit_logs I ×2）
· platform_state = 1 行（uninitialized）· platform_memberships = 0 行
· P14 明示：Bootstrap CLI = OUT OF SCOPE（RTA-09 = OPTION B）· 须独立授权
```

### Option A — 本轮不实现（保持 DB 层就绪、无代码）
```text
What changes: 无
Benefits: 维持 P14 已验收边界 · 无一次性特权路径风险
Costs: 首次初始化仍需人工/手工路径
Security: No impact · Schema: No · Runtime: No · Authorization: No · Migration: No
Testing: 无新增 · Future impact: 待独立授权
```

### Option B — 实现 Bootstrap CLI（一次性）
```text
What changes: 新增 CLI 入口 + 一次性 bootstrap 事务（插 PM + 翻转 platform_state + 审计）
Benefits: 补齐安装期闭环 · 可验证"不可重开"语义
Costs: 新特权路径需完整安全设计（凭据来源、不可重用、不可成为 runtime dependency）
Security: **SECURITY DECISION REQUIRED**（Privilege boundary impact）
Schema: No · Runtime: 独立路径（不得被 normal runtime 调用）· Authorization: 部分
Testing: 首次成功 + 二次拒绝 + 审计行 + 凭据边界 · Future impact: 高
```

### Professional Default
```text
Option A（不实现）直到独立授权。
理由：P14 已明确该能力须"另一独立 implementation authorization"；本轮无该授权。
```

---

## P15-DEC-04 — D-01 foundation maintenance（C-1）

### Decision Question
是否修复 `infrastructure/database/persistence.py` 的两处缺陷（undefined `err` + `.one()` 无法表达 no-row）？

### Current Evidence
```text
· 文件 sha256 = 69d2c140…（Wave 1 frozen · 未修改）
· 两处缺陷：except 引用未定义名 `err` ⇒ NameError；`_fetch_one` 用 .one() ⇒ 零行 raise
· active P14 路径已排除：Wave 2 仓库继承 services/reads.SafeReader；
  AuthorizationRepository 不继承 Wave 1 Repository（自带 _fetch/_fetch_one）
· P14 登记：D-01 = DEFERRED / NON-BLOCKING
```

### Option A — Keep Deferred
```text
What changes: 无
Benefits: 不触碰 Wave 1 Evidence Freeze · 无回归风险
Costs: 缺陷留在冻结文件中（仅对"直接使用该 helper 的新代码"有风险）
Security: No impact · Schema: No · Runtime: No（active path 不使用）· Authorization: No · Migration: No
Testing: 既有 Wave 1/2 allowlist 保持 · Future impact: 新代码须继续使用 SafeReader
```

### Option B — Foundation Change（两行修复）
```text
What changes: `_safe(err)` → `_safe(exc)`；`.one()` → `.first()`
Benefits: 消除潜在 NameError 与"no-row 不可表达"
Costs: 修改 Wave 1 已验收实现 ⇒ 触发 FOUNDATION CHANGE REQUIRED 流程
Security: No impact · Schema: No
Runtime: 影响读取路径（Wave 1 helper 语义变化）· Authorization: No
Regression scope: Wave 1 frozen set（211 项含 D-02 记录）+ Wave 2（72 项）须全量重跑
Evidence Freeze impact: Wave 1 文件 sha 变化 ⇒ 需 Human 授权 + 重新冻结记录
SafeReader 兼容性: 兼容（SafeReader 已提供正确语义；修复后两者等价）
Future impact: 低风险、可逆
```

### Professional Default
```text
Option A（Keep Deferred）。
理由：不因 P15 发布/进度压力自动修复 foundation defect；且 active path 已安全排除。
仅当证据显示 P15 某 active path 无法安全运行而必须修复时，才升级为 Option B（并需独立 foundation 授权）。
```

---

## P15-DEC-05 — FINDING-ENGINE-1（engine 双轨 · C-3）

### Decision Question
是否统一 `/ready` 探针（Wave 0 process engine）与 `RuntimeDatabase` 的 engine？

### Current Evidence
```text
· apps/api/routes/health.py → collect_components → check_database(config)（Wave 0 session engine）
· Wave 2 API 服务路径 → RuntimeApplication.database（RuntimeDatabase · uap_runtime）
· P14 登记：FINDING-ENGINE-1 = ACCEPTED COMPATIBILITY FINDING（P14 内不重构）
· 该差异不影响授权面 / 不影响 uap_runtime / 不改变 Wave 1 accepted health contract
```

### Option A — 保持现状（accepted compatibility）
```text
What changes: 无 · Benefits: 零风险、不触碰健康契约与测试
Costs: 进程内可能存在两个 engine（连接数略增）
Security: No impact · Schema: No · Runtime: health 面 · Authorization: No · Migration: No
Testing: 既有 health 契约测试保持 · Future impact: 可未来统一
```

### Option B — 统一为 RuntimeDatabase 单一 engine
```text
What changes: 修改 health 探针数据源
Benefits: 单一 engine、职责统一
Costs: 触碰 Wave 1 accepted health contract（tests/contract/test_health_contract.py）
Security: No impact · Schema: No · Runtime: 是 · Authorization: No · Migration: No
Testing: 健康契约测试需重新评估（foundation regression 风险）· Future impact: 中
```

### Professional Default
```text
Option A（保持现状）。
理由：P14 已判定为 accepted compatibility；统一会引入 foundation regression 风险而收益有限。
```

---

## P15-DEC-06 — events / outbox consumer（C-5）

### Decision Question
是否在 P15 引入 events/outbox 消费（后台执行者）？

### Current Evidence
```text
· 表存在：events / events_202609（P10 schema）· runtime 授权 events S/I/U（无 DELETE）
· 无任何 consumer；apps/worker/main.py 为 generic background scheduler（P14 明确 OUT OF SCOPE）
· P10 事件/审计边界为冻结决策；审计不可变（tg_audit_immutable）
```

### Option A — 不引入（保持 outbox 只写不消费）
```text
What changes: 无 · Benefits: 零新增后台面 · 维持最小权限
Costs: outbox 无消费者（数据只增不被处理）
Security: No impact · Schema: No · Runtime: No · Authorization: No · Migration: No
Testing: 既有套件 · Future impact: 事件驱动能力延后
```

### Option B — 引入专用 consumer
```text
What changes: 新增后台消费执行者（读取 events → 处理 → 状态推进）
Benefits: 打通事件驱动闭环 · 复用既有表（无 schema 变更）
Costs: 需冻结幂等键 / 重放语义 / 失败重试上界 / 并发消费语义 / 审计要求
Security: **SECURITY DECISION REQUIRED**（Runtime security impact · 新后台写入者）
Schema: No（表已存在）· Runtime: 是 · Authorization: 是（service 身份与 subject 语义）
Migration: No · Testing: 幂等/重放/并发/失败路径/审计 delta · Future impact: 高
```

### Professional Default
```text
先冻结 worker 边界与幂等契约，再授权实现；本轮不实现。
理由：消费语义（幂等/重放/补偿）未冻结前实现会产生不可审计的重复副作用。
```

---

# CANDIDATE → DECISION DEPENDENCY MAP（§7）

```text
C-1 D-01                      → P15-DEC-04（foundation change decision）
C-2 管理类能力                 → P15-DEC-02（authorization/security decision）
C-3 engine 双轨                → P15-DEC-05（compatibility maintenance decision）
C-4 Bootstrap CLI             → P15-DEC-03（runtime/bootstrap/security decision）
C-5 outbox consumer           → P15-DEC-06（event architecture/security/reliability decision）
C-6 AI 启用                    → P15-DEC-01（theme）= 需独立 AI architecture/security/external-integration decision（**尚未建立 ID**）
C-7 Frontend                  → P15-DEC-01（theme）= 需独立 frontend/API/auth boundary decision（**尚未建立 ID**）
C-8 审计深化                   → P15-DEC-01（theme）= 需独立 audit semantics decision（**尚未建立 ID**）

⇒ C-6 / C-7 / C-8 目前**没有**对应 Decision ID（P15 PREP 只定义 6 项）。
   若 Human 选择把它们纳入 P15 ⇒ 需要新增 P15-DEC-07…（下一轮登记），本文件不擅自编号。
```

# DECISION COMPLETION ORDER（§9）

```text
第 1 顺位：**P15-DEC-01（Theme）** —— 决定其余决策的适用范围
第 2 顺位（可并行，彼此独立）：
   · P15-DEC-02（管理类 authorization）
   · P15-DEC-03（Bootstrap CLI）
   · P15-DEC-06（outbox consumer）
第 3 顺位（独立于主题，可与任意项并行）：
   · P15-DEC-04（D-01 foundation maintenance）
   · P15-DEC-05（engine 双轨 compatibility）

why this order
  · DEC-01 限定 scope ⇒ 决定 DEC-02/03/06 是否需要被激活
  · DEC-02 是唯一可能触发 schema 的决策 ⇒ 必须在任何 "P15 需要新词表" 断言之前裁决
  · DEC-03 与 DEC-06 触及安全边界但与 DEC-02 无相互依赖 ⇒ 可并行
  · DEC-04 / DEC-05 属 maintenance，与主题无关 ⇒ 独立

independent / blocking
  independent：DEC-04 · DEC-05（可单独裁决，不阻塞其他项）
  blocking：DEC-01 阻塞 DEC-02/03/06 的"是否激活"；DEC-02 阻塞任何 schema/词表相关工作
```

# SECURITY / AUTHORIZATION / SCHEMA DECISION EXTRACTION（§10/§11/§12）

```text
SECURITY DECISIONS REQUIRED = 3
  SD-1 ← P15-DEC-02  问题：是否允许 admin-on-behalf-of-user？
                     边界变化：新增跨用户权限路径 · 新 principal：否（复用 uap_runtime）
                     新 grant：否（除非需新对象授权）· 新 action：**是**（若选 B）
                     schema support：可能（action/effect 行）⇒ 若涉及 uap_runtime/uap_bootstrap
                     grant / role / default ACL / RLS ⇒ **SECURITY IMPLEMENTATION GATE REQUIRED**
  SD-2 ← P15-DEC-03  问题：一次性 bootstrap 特权路径的凭据与不可重用语义
                     边界变化：uap_bootstrap 从"就绪但未用"变为"被调用"
                     新 principal：否 · 新 grant：否（6 项已就位）
                     若需新增 grant / role ⇒ SECURITY IMPLEMENTATION GATE REQUIRED
  SD-3 ← P15-DEC-06  问题：后台 consumer 的幂等/重放/审计与失败上界
                     边界变化：新增后台写入者（events 状态推进）
                     新 principal：否（复用 uap_runtime）· 新 grant：否（events S/I/U 已就位）
                     若需 events DELETE 或新对象 ⇒ SECURITY IMPLEMENTATION GATE REQUIRED

AUTHORIZATION DECISIONS REQUIRED = 2
  AD-1 ← P15-DEC-02  canonical action impact = **是**（新增管理类 action）
                     subject type impact = 否（USER/ROLE/AGENT 不变）
                     role / effect / ownership / admin-on-behalf / tenant-space =
                       取决于选项：B 全部可能触及；C 走独立模型
                     ⇒ 若答案 YES ⇒ **AUTHORIZATION DECISION REQUIRED**
  AD-2 ← P15-DEC-06  canonical action impact = 否（消费为后台 process，不新增用户动作）
                     subject type impact = **可能**（service/agent subject 语义需明确）
                     ⇒ 若需新 subject/role ⇒ AUTHORIZATION DECISION REQUIRED

SCHEMA DECISIONS REQUIRED = 1
  SC-1 ← P15-DEC-02（仅当选 B）
    current schema limitation : permissions/role_permissions 已有 12 canonical action；无管理类动作
    why insufficient          : 管理类操作无法用现有 12 动作表达（走 Stage 2 会恒为 DENY）
    minimal schema change     : 新增 action 行（+ 可能的 role_permissions 绑定）
    alternative no-schema     : 应用层"认证 + 归属校验"（= P14 现状 Option A）或独立 Approval 模型（C）
    migration impact          : 需要 migration（⇒ 当前 FORBIDDEN）
    rollback impact           : 可回滚（seed 行删除）· security impact：词表扩展须重新评估
    test impact               : deny/precedence 全量重跑
  ⇒ 本轮**未创建** 0018 / 新表 / 新列 / 新索引 / 新触发器 / 新函数 / 新 enum
```

---

# P15 HUMAN DECISION FORM

> 初始状态统一 = `PENDING HUMAN DECISION` · 本 BOT **未填任何选项**

```text
P15-DEC-01
Decision: P15 主题 / scope 组成
Selected Option:            （A / B / C / D-CUSTOM）
Human Status: PENDING HUMAN DECISION
Notes:

P15-DEC-02
Decision: 管理类能力与 authorization 词表
Selected Option:            （A / B / C）
Human Status: PENDING HUMAN DECISION
Notes:

P15-DEC-03
Decision: Bootstrap CLI 时机（RTA-09 = OPTION B）
Selected Option:            （A / B）
Human Status: PENDING HUMAN DECISION
Notes:

P15-DEC-04
Decision: D-01 foundation maintenance
Selected Option:            （A Keep Deferred / B Foundation Change）
Human Status: PENDING HUMAN DECISION
Notes:

P15-DEC-05
Decision: FINDING-ENGINE-1 engine 双轨
Selected Option:            （A 保持现状 / B 统一）
Human Status: PENDING HUMAN DECISION
Notes:

P15-DEC-06
Decision: events / outbox consumer
Selected Option:            （A 不引入 / B 引入专用 consumer）
Human Status: PENDING HUMAN DECISION
Notes:
```

```text
附（若 Human 需要把 C-6 / C-7 / C-8 纳入 P15）
  P15-DEC-07（AI 启用）· P15-DEC-08（Frontend）· P15-DEC-09（审计深化）
  = **尚未建立**（P15 PREP 只定义 6 项；不得擅自编号，须由 Human 指示后登记）
```

**END OF P15 HUMAN DECISION REVIEW PACKAGE（2026-09-28 · 6 decisions · 0 selected · PENDING · HARD STOP ACTIVE）**
