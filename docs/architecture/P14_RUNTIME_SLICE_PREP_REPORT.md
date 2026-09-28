# UAP — P14_RUNTIME_SLICE PREP REPORT

> ## 阶段与边界
>
> ```text
> 阶段      = `P14_RUNTIME_SLICE`（FROZEN 编号 · PDL 附录 M.1）
> 本文档性质 = PREP 设计产物（DRAFT · NOT FROZEN）—— 只**提出问题**，不代裁
> 依据      = RUNTIME_DOCUMENT_SET_DECISION.md §2（本文件为其中 PREP_REPORT）
> 本轮未做   = 未创建 runtime code / services 实现 / API endpoint / worker / scheduler / CLI 实现 ·
>              未创建 0018+ migration · 未改 schema / P13 seed / 冻结 Decision 正文
> 回答规则   = **所有 OQ 一律标记 OPEN，等待 Human**；本报告不含任何自行裁定
> ```

---

# 1. P14_PREP_BASELINE（Phase 1 基线锁定 · 只读实测）

```text
Git
  HEAD        = c420403d5469241e8b03855428ebce435d539c9e
  branch      = main
  tags        = 9（最新 = UAP-V0.1.9-P13-SEED）
  remote      = 0
  dirty       = 112（staged 0 · modified 36 · untracked 76）

Database
  alembic_version = 0017_p13_seed
  acl_subject_types = 3 · permissions = 12 · role_permissions = 12
  users = 0 · audit_logs = 0 · platform_memberships = 0
  C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff
  uap_migrator CREATE = false

保护对象 sha256（基线锁定）
  0016_open_p10_1_trust_boundary.py  10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544
  0017_p13_seed.py                   1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e
  env.py                             577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a
  PLATFORM_DECISION_LOG.md           bc5cbf333d2b91ab554c521734b084687336347b0debfc79c28f0c16a397ea26
  P14_RUNTIME_SLICE_FORMALIZATION_GATE_REPORT.md  1462fdc0c77255135f1ea00054516aa9e10fa41eccd779d845bf96ecffe78323
  RUNTIME_DOCUMENT_SET_DECISION.md                4ffffbe049df88a3a60b1e29cbbb93a70f1e702332c8971896881e06eb8adf53

结论：P13 release 未变（0017 = current · tag/commit 未变）· 保护对象全部未变。
```

---

# 2. Open Questions（**全部 OPEN · 等待 Human Decision**）

> 记法：每项给出 `Question` / `Context`（既有事实与约束）/ `Why it needs Human`（为何不能由 Bot 裁定）。
> **不给出选定结论**；候选方向仅在有助于 Human 判断时列出，且明确标注「备选，非建议结论」。

## 2.1 Identity

### OQ-P14-01 — runtime identity onboarding flow

```text
Question : 首个可登录主体（users 行）由哪条路径建立？形态是什么？
Context  : P13 IMPL-01 = A ⇒ P13 不建 users；D-P13-06 说 identity row allowed；
           D-PLAT-11① 说首个正式可登录主体「只经 P13 建立」；
           实测 users = 0；ck_users_login 要求 email 或 username 非空（⇒ 任何 users 行自带可登录标识）。
           备选方向（非结论）：CLI 引导 / API 自助注册 / 邀请制 / 平台管理员代建。
Why Human: 决定平台对外开放形态与信任模型；且与 D-PLAT-11① 的最终解释绑定。
Status   : OPEN
```

### OQ-P14-02 — credential lifecycle

```text
Question : 凭据如何建立、存储、轮换、失效？密钥材料从哪里来？
Context  : D-P13-13：明文 / 可逆 / 伪造密码 = 0；SEED_STRATEGY §6「密码由 onboarding 设置（非 seed）」；
           identities 表存在但未使用；无 KMS/密钥管理面当前。
           备选方向（非结论）：Argon2id 哈希 + 强制定期轮换 / 外部 IdP 托管 / 设备绑定凭据。
Why Human: 属安全架构决策；且涉及是否引入外部依赖与新配置面。
Status   : OPEN
```

### OQ-P14-03 — device / user association

```text
Question : 是否引入设备主体（device_subject）与用户的多设备关联？如何表达？
Context  : core/identity.IDENTITY_KINDS = (user, service, device_subject)；
           D-AUTH-18 明文：Authorization Subject Type ≠ Identity Kind ≠ Identity Provider
           （acl_subject_types 白名单固定为 user/role/agent，**不得**加入 service/device）。
Why Human: 影响 identity 模型与认证流程；且不得与授权主体词汇混用（D-AUTH-18 约束）。
Status   : OPEN
```

## 2.2 Authorization

### OQ-P14-04 — runtime permission check location

```text
Question : 授权判定在何处执行？（API 边界 / service 层 / policy 层 / 数据库层辅助）
Context  : 既有分层 apps → agent → services → intelligence → core → infrastructure；
           Agent 禁直连 DB（Agent → Policy → Tool → Service → Database）；
           default deny / deny 优先 / FAIL CLOSED 已冻结。
Why Human: 决定横切关注点的归属与测试面（影响 C-5/C-6 未决项）。
Status   : OPEN
```

### OQ-P14-05 — policy enforcement boundary

```text
Question : Policy 的强制边界在哪？是否存在必须由 DB 层兜底的判定？
Context  : 既有 DB 层强制先例：C2（registry）· is_system roles · membership scope triggers ·
           ck_permissions_action_canonical。
           本路线**不得**新增 schema（⇒ 若要新增 DB 层强制，必须另立独立授权）。
Why Human: 涉及是否突破「不新增 schema」边界。
Status   : OPEN
```

## 2.3 Service

### OQ-P14-06 — API boundary

```text
Question : API 面对外契约形态（协议 / 版本策略 / 错误语义 / 分页与幂等约定）？
Context  : services/ 为业务持久化唯一归属（D-PLAT-01/03）；C-5、C-6 未决；
           既有 readiness/health 面已由 D-PLAT-14/16 定义（可复用）。
Why Human: 对外契约属架构决策，且影响后续所有 Domain 接入。
Status   : OPEN
```

### OQ-P14-07 — service ownership

```text
Question : services/ 的内部结构、模块粒度与 owner（C-5）？
Context  : PDL 附录 C 的 C-5 =「services/ 内部结构与模块粒度 → 留待 Runtime PREP」（即本轮）。
Why Human: 属目录/职责划分决策，影响长期可维护性。
Status   : OPEN
```

### OQ-P14-08 — failure handling

```text
Question : 失败语义（超时 / 依赖不可用 / 部分失败 / 重试策略 / 幂等）？
Context  : 既有先例：D-PLAT-16（readiness 探针 2000 ms ⇒ error ⇒ /ready 503，不重试不降级）·
           events = transactional outbox（P10）。
Why Human: 决定可用性目标与工程复杂度。
Status   : OPEN
```

## 2.4 Operations

### OQ-P14-09 — bootstrap process

```text
Question : 首个平台管理员的 bootstrap 具体流程与凭据来源？谁来执行、如何留证？
Context  : R4/R5（FROZEN）：条件 = platform_state='uninitialized' AND platform_memberships 无行；
           原子流程 = 插首行 PM → 翻转 platform_state → audit('platform.admin.bootstrap') → COMMIT；
           普通 API/seed 永不写 PM 行；无恢复 API（恢复 = 独立程序 + 人工批准 + 审计）。
           实测：platform_state = 1（uninitialized）· platform_memberships = 0。
备选方向（非结论）：离线 CLI + 人工双人复核 / 受信运维窗口 / 硬件令牌。
Why Human: 属平台最高权限入口的设计决策。
Status   : OPEN
```

### OQ-P14-10 — deployment model

```text
Question : 部署模型（单机 / 容器编排 / 云托管）与配置面（环境变量 / secret 注入）？
Context  : 既有 docker-compose.yml（postgres + api + 可选 redis）；D-PLAT-15 v2 要求
           期望 revision 由构建期只读工件承载（config/_build_info.py），运行时不可覆盖。
           PDL 附录 C 的 C-10：docs/operations/ 部署手册缺失（建议另行登记）。
Why Human: 影响运维可行性与安全面（secret 管理）。
Status   : OPEN
```

### OQ-P14-11 — observability

```text
Question : 可观测性范围（日志 / 指标 / 追踪 / 告警）与最小可用集？
Context  : 既有 /health（liveness）与 /ready（readiness，503 语义）已定义；
           D-PLAT-17 ⑦：本路线不建 CI。
Why Human: 影响运维成本与验收判据。
Status   : OPEN
```

## 2.5 Security

### OQ-P14-12 — C2 trust boundary usage

```text
Question : Runtime 阶段如何使用 C2/CC-7 的受信迁移边界？是否存在需要 registry 变更的场景？
Context  : D-P13-15（B-1 Amendment）：允许**未来受信 migration context** 建立 system registry seed，
           前提 = 数据库身份隔离已成立（现已成立）。
           但 D-P13-15 的 Does not authorize 明确不含对 Runtime 的授权；
           本路线**不得**放宽 C2，且 registry 当前 3 行已满足 P13 基线。
Why Human: 若确需 registry 变更，属「另立独立授权」的事件，须 Human 明示。
Status   : OPEN
```

### OQ-P14-13 — runtime privilege boundary（含 OI-G-1）

```text
Question : uap_app 的逐表 DML 矩阵如何核定？onboarding / bootstrap 需要写 users / roles /
           tenants / spaces / platform_memberships，但 uap_app 当前对**上述表无任何授权**。
Context  : uap_app 现持**恰 5 项**显式授权（SCHEMA public USAGE · alembic_version SELECT ·
           audit_logs(+当期分区) INSERT/SELECT）；CREATE = false。
           OI-G-1 = 「runtime 逐表 DML 矩阵不可核定（不得扩权）」· 状态 REGISTERED（BATCH-D）。
           本路线不得新增 GRANT（Excluded）⇒ 必须由 Human 选择：扩权 / 受信专用路径 / 其他。
Why Human: 这是本路线**唯一可能触碰权限面**的决定，且涉及 OI-G-1 的既有登记。
Status   : OPEN（**关键阻塞项**）
```

---

# 3. Required Human Decisions（汇总）

```text
必须裁决（13 项 · 全部 OPEN）：
  Identity      : OQ-P14-01 · OQ-P14-02 · OQ-P14-03
  Authorization : OQ-P14-04 · OQ-P14-05
  Service       : OQ-P14-06 · OQ-P14-07 · OQ-P14-08
  Operations    : OQ-P14-09 · OQ-P14-10 · OQ-P14-11
  Security      : OQ-P14-12 · OQ-P14-13

关键阻塞项（其余可并行讨论）：
  OQ-P14-13（runtime privilege boundary / OI-G-1）
    ⇒ 未定之前，Runtime 无法完成任何写路径（onboarding / bootstrap 均需写库）

已由既有决策确定、**不属于** OPEN 的部分（无需再裁）：
  · 不新增 schema · 不创建 migration · 不改授权模型 · 不改词表 · 不改 P13 seed ·
    不改 ownership / grants / default ACL · 不放宽 C2 · 不建 CI
```

---

# 4. 本轮工程变更与边界

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · services 实现 = 0 · API = 0
新增文档 = 本报告 + SCOPE + DEPENDENCY_MAP + ACCEPTANCE_MATRIX（4 份 · 冻结文档集合内）
commit = 0 · tag = 0 · push = 0

本文档 = DRAFT · NOT FROZEN。P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14_RUNTIME_SLICE PREP REPORT（2026-09-27 · PREP · DRAFT · OPEN = 13 · P14 IMPLEMENTATION = NOT AUTHORIZED）**
