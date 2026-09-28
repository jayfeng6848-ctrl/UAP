# UAP — P14 DECISION DEPENDENCY GRAPH

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — DECISION IMPACT ANALYSIS ROUND（Phase 1）
> 性质      = 只读分析；**不替 Human 选择任何 OPTION**、不做裁定
> 基线      = HEAD c420403d… · tag UAP-V0.1.9-P13-SEED · migration 0017_p13_seed · stage P14_RUNTIME_SLICE
> 本轮未做   = 未创建 runtime code / API / CLI / migration / schema · 无 DDL / DML ·
>             未改 GRANT/REVOKE · 未改冻结决策正文 · 未 commit/tag/push
> ```

---

# 1. 依赖图（逐 OQ）

## OQ-P14-01 — identity onboarding flow

```text
OQ-ID                : OQ-P14-01
depends_on           : OQ-P14-13（写路径存在性）· OQ-P14-12（是否触碰 registry 的边界声明）
blocks               : OQ-P14-02 · OQ-P14-03 · identity runtime 实现 · onboarding flow 实现
affected_documents   : P14_RUNTIME_SLICE_SCOPE（Included §2.3）· DEPENDENCY_MAP（§2.1）·
                       PREP_REPORT §2.1 · ACCEPTANCE_MATRIX（IDF-1 / IDL-1）
affected_components  : users / identities / credentials / sessions 写路径 ·
                       onboarding 服务面 · 认证入口
implementation_stage : Identity runtime（实现前必须冻结）
```

## OQ-P14-02 — credential lifecycle

```text
OQ-ID                : OQ-P14-02
depends_on           : OQ-P14-01（主体形态）· OQ-P14-10（secret 注入通道）· OQ-P14-13（写权限）
blocks               : onboarding flow 实现 · bootstrap（首个管理员凭据）· OQ-P14-11
affected_documents   : SCOPE §2.3 / §4（SB-4）· DEPENDENCY_MAP §2.1 · PREP_REPORT §2.2 ·
                       ACCEPTANCE_MATRIX（SEC-4 / IDL-2 / IDL-3）
affected_components  : credentials / identities 存储 · 认证校验路径 · 轮换与失效流程 · 密钥托管
implementation_stage : Identity runtime + Security（实现前必须冻结）
```

## OQ-P14-03 — device / user association

```text
OQ-ID                : OQ-P14-03
depends_on           : OQ-P14-01 · OQ-P14-02
blocks               : identity runtime 的多设备面（非阻塞骨架）
affected_documents   : DEPENDENCY_MAP §2.1（IDENTITY_KINDS 与 D-AUTH-18 分离）·
                       PREP_REPORT §2.3 · ACCEPTANCE_MATRIX（IDF-3 / IDL-6）
affected_components  : devices / identities 关联表达 · 认证流程分支
implementation_stage : Identity runtime（PREP 收尾前冻结即可）
```

## OQ-P14-04 — runtime permission check location

```text
OQ-ID                : OQ-P14-04
depends_on           : OQ-P14-13（读侧权限是否存在，决定判定能否在 runtime 侧完成）
blocks               : OQ-P14-05 · OQ-P14-06 · OQ-P14-07 · OQ-P14-08 ·
                       authorization middleware 实现
affected_documents   : DEPENDENCY_MAP §2.2 · SCOPE §2.4 · PREP_REPORT §2.4 ·
                       ACCEPTANCE_MATRIX（AUT-1…AUT-4 · ABC-1…ABC-4）
affected_components  : authorization 判定层（core 契约 / service 编排 / DB 访问）·
                       services/authorization（D-AUTH-16 记「包尚不存在」）
implementation_stage : Authorization runtime（实现前必须冻结）
```

## OQ-P14-05 — policy enforcement boundary

```text
OQ-ID                : OQ-P14-05
depends_on           : OQ-P14-04 · OQ-P14-13（若需 DB 兜底则触及 schema 边界）
blocks               : authorization middleware 实现 · 验收判据 AUT-3/AUT-4 固化
affected_documents   : SCOPE §3（Excluded：schema evolution）· DEPENDENCY_MAP §2.2 ·
                       PREP_REPORT §2.5 · ACCEPTANCE_MATRIX（AUT-3 / SEC-2）
affected_components  : policy 判定链 · 既有 DB 层强制触发器（C2 / roles / membership scope）的复用方式
implementation_stage : Authorization runtime（实现前必须冻结）
```

## OQ-P14-06 — API boundary

```text
OQ-ID                : OQ-P14-06
depends_on           : OQ-P14-04（判定层）· OQ-P14-07（服务归属）
blocks               : OQ-P14-08 · API boundary 实现
affected_documents   : DEPENDENCY_MAP §2.2 · PREP_REPORT §2.6 · ACCEPTANCE_MATRIX（OPS-1 / FLM-*）
affected_components  : 对外接口层 · 错误与版本语义 · 契约载体（PDL 附录 C 的 C-6 未决）
implementation_stage : Service/API（PREP 收尾前冻结即可）
```

## OQ-P14-07 — service ownership（C-5）

```text
OQ-ID                : OQ-P14-07
depends_on           : OQ-P14-04
blocks               : OQ-P14-06
affected_documents   : DEPENDENCY_MAP §3 · PREP_REPORT §2.7 · PDL 附录 C（C-5）
affected_components  : services/ 内部结构与模块粒度 · 守卫配置（G-2 / G-3）
implementation_stage : Service/API（PREP 收尾前冻结即可）
```

## OQ-P14-08 — failure handling

```text
OQ-ID                : OQ-P14-08
depends_on           : OQ-P14-06
blocks               : 无（实施期细化）
affected_documents   : PREP_REPORT §2.8 · ACCEPTANCE_MATRIX（FAL-1…FAL-3 / FLM-1…FLM-5）
affected_components  : 超时/重试/幂等策略 · 部分失败补偿
implementation_stage : 实施阶段细化
```

## OQ-P14-09 — bootstrap process

```text
OQ-ID                : OQ-P14-09
depends_on           : OQ-P14-13（platform_memberships / platform_state 写路径）·
                       OQ-P14-02（管理员凭据来源）
blocks               : bootstrap CLI 实现 · 平台初始化
affected_documents   : SCOPE §2.6 · DEPENDENCY_MAP §2.2/§2.3 · PREP_REPORT §2.9 ·
                       ACCEPTANCE_MATRIX（OPS-3 / AUDX-1）
affected_components  : CLI 形态 · 执行者与凭据 · audit('platform.admin.bootstrap') 写入
implementation_stage : Bootstrap（实现前必须冻结）
```

## OQ-P14-10 — deployment model

```text
OQ-ID                : OQ-P14-10
depends_on           : OQ-P14-02（secret 托管）
blocks               : OQ-P14-11 · 部署与 secret 注入落地
affected_documents   : PREP_REPORT §2.10 · ACCEPTANCE_MATRIX（OPS-4）
affected_components  : 部署拓扑 · 配置面 · secret 注入通道 · PDL 附录 C（C-10 部署手册）
implementation_stage : Operations（PREP 收尾前冻结即可）
```

## OQ-P14-11 — observability

```text
OQ-ID                : OQ-P14-11
depends_on           : OQ-P14-10 · OQ-P14-08
blocks               : 无（实施期迭代）
affected_documents   : PREP_REPORT §2.11 · ACCEPTANCE_MATRIX（OPS-4）
affected_components  : 日志 / 指标 / 追踪 / 告警最小集
implementation_stage : 实施阶段细化
```

## OQ-P14-12 — C2 trust boundary usage

```text
OQ-ID                : OQ-P14-12
depends_on           : 无上游（属边界声明）
blocks               : OQ-P14-01 / OQ-P14-13 的边界界定（"Runtime 是否完全不触碰 registry"）
affected_documents   : SCOPE §4（SB-2）· DEPENDENCY_MAP §2.2 · PREP_REPORT §2.12 ·
                       ACCEPTANCE_MATRIX（SEC-2 / IDL-5）
affected_components  : acl_subject_types 使用面 · C2/CC-7 依赖关系
implementation_stage : Security（实现前必须冻结）
```

## OQ-P14-13 — runtime privilege boundary ★

```text
OQ-ID                : OQ-P14-13
depends_on           : 无上游（根节点 · 关键阻塞）
blocks               : OQ-P14-01 · 02 · 03 · 04（读侧）· 09 ·
                       identity runtime · authorization middleware · bootstrap CLI · onboarding flow
                       以及一切需要读写数据库的行为
affected_documents   : P14_PRIVILEGE_BOUNDARY_ANALYSIS（全文）· SCOPE §4 · DEPENDENCY_MAP §2.4 ·
                       PREP_REPORT §2.13 · ACCEPTANCE_MATRIX（PRV-1…PRV-6）
affected_components  : uap_app 授权面 · 受信写路径（如有）· GRANT 面 · default ACL 面
implementation_stage : 全部（前置阻塞）
```

---

# 2. 关键前置关系（"先于什么"）

```text
identity runtime      ← 必须先定：OQ-P14-13 → OQ-P14-12 → OQ-P14-01 → OQ-P14-02 → OQ-P14-03
authorization middleware ← 必须先定：OQ-P14-13（读侧）→ OQ-P14-04 → OQ-P14-05
bootstrap CLI         ← 必须先定：OQ-P14-13 → OQ-P14-02（管理员凭据）→ OQ-P14-09
onboarding flow       ← 必须先定：OQ-P14-13 → OQ-P14-01 → OQ-P14-02
API boundary          ← 必须先定：OQ-P14-04 → OQ-P14-07 → OQ-P14-06
```

---

# 3. 图摘要（机读）

```text
根节点（无上游）      : OQ-P14-13 · OQ-P14-12
一级依赖（只依赖根）  : OQ-P14-01(→13,12) · OQ-P14-04(→13) · OQ-P14-10(→02)
二级                : OQ-P14-02(→01,10,13) · OQ-P14-05(→04,13) · OQ-P14-07(→04) · OQ-P14-12(根)
三级                : OQ-P14-03(→01,02) · OQ-P14-06(→04,07) · OQ-P14-09(→13,02) · OQ-P14-11(→10,08)
四级                : OQ-P14-08(→06)

无环校验 = PASS（拓扑序存在：13/12 → 01/04/10 → 02/05/07 → 03/06/09/11 → 08）
```

---

# 4. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 DECISION DEPENDENCY GRAPH（2026-09-27 · 13 OQ 依赖图完成 · 无环 · 未作裁定）**
