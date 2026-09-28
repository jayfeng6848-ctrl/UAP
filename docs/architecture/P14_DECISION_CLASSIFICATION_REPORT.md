# UAP — P14 DECISION CLASSIFICATION REPORT

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — DECISION PREPARATION ROUND（Phase 1 + Phase 2）
> 性质      = 只读取证 + 分类；**不含任何裁定**
> 基线      = HEAD c420403d5469241e8b03855428ebce435d539c9e · tag UAP-V0.1.9-P13-SEED
>             migration 0017_p13_seed · DB: registry 3 / permissions 12 / role_permissions 12 /
>             users 0 / audit_logs 0
> 固化规则   = 每个 OQ **不填写** Decision / Approved / Rejected / Frozen；
>             任何方向性文字仅作 OPTION，不得写入 FINAL DECISION
> 本轮未做   = 未创建 0018+ · 未改 migrations_alembic · 未改 env.py · 未改 P13/P14 冻结正文 ·
>             未创建 runtime code / services / API / CLI / worker · 无 DDL / DML ·
>             未改 GRANT / REVOKE / default ACL · 未改权限模型 · 未 commit / tag / push
> ```

---

# Part 1 — OQ 完整取证（OQ-P14-01 … OQ-P14-13）

---

## OQ-P14-01 — runtime identity onboarding flow

```text
ID                  : OQ-P14-01
Current Question    : 首个可登录主体（users 行）由哪条路径建立？流程形态是什么？
Existing Facts      : users = 0 行；tenants/spaces = 0；platform_state = 1(uninitialized)；
                      ck_users_login 要求 email 或 username 非空（任何 users 行自带可登录标识）；
                      identities / devices / credentials / sessions 表均已存在（P13 时 0 行）；
                      services/ 目录存在但无 authorization 包（D-AUTH-16 记「包尚不存在」）。
Frozen Constraints  : D-P13-06（identity row allowed · credential secret forbidden ·
                      「首个可登录主体」与「P13 创建主体记录」必须区分）；
                      D-PLAT-11①（首个正式可登录主体只经 P13 建立）+ ②（禁第二套 dev bootstrap 路径）；
                      D-P13-13（credentials = 0 在 P13 侧）。
Affected Layer      : authorization + runtime + security（identity 面）
Dependency          : D-P14-02（凭据生命周期）· OQ-P14-13（写路径权限）· OQ-P14-09（bootstrap 路径）
Risk If Wrong       : 若选择与 D-PLAT-11① 冲突的路径 ⇒ 需重新解释该冻结决策（须 Human 明示）；
                      若选择自助注册 ⇒ 平台对外暴露面与滥用风险显著上升。
Evidence            : PREP_REPORT §2.1 · users/identities/devices/credentials 实测计数 ·
                      PDL D-PLAT-11 · D-P13-06。
Human Decision Required : YES —— 路径形态（CLI 引导 / API 自助 / 邀请制 / 管理员代建 / 其他）
```

---

## OQ-P14-02 — credential lifecycle

```text
ID                  : OQ-P14-02
Current Question    : 凭据如何建立、存储、轮换、失效？密钥材料来源？
Existing Facts      : credentials 表存在（0 行）；identities 表存在（0 行）；
                      仓库内无 KMS / 密钥管理面；settings 面仅有 DATABASE_URL 等配置。
Frozen Constraints  : D-P13-13（明文 / 可逆 / 伪造密码 = 0）；
                      SEED_STRATEGY §6（首管理员密码由 onboarding 流程设置，非 seed）；
                      R4/R5（bootstrap 由受信 CLI 执行 + audit）。
Affected Layer      : security + operations + runtime
Dependency          : OQ-P14-01（主体建立）· OQ-P14-10（部署与 secret 注入）· OQ-P14-13（凭据表写权限）
Risk If Wrong       : 哈希算法 / 轮换策略 / 密钥托管选择错误 ⇒ 安全事件面；
                      若引入外部 IdP ⇒ 新增依赖与信任边界，须评估与 D-AUTH-18 词汇分离的关系。
Evidence            : PREP_REPORT §2.2 · credentials 表存在性实测 · D-P13-13 原文 · SEED_STRATEGY §6。
Human Decision Required : YES —— 凭据形态、哈希算法族、轮换与失效策略、密钥材料托管方式
```

---

## OQ-P14-03 — device / user association

```text
ID                  : OQ-P14-03
Current Question    : 是否引入设备主体与用户的多设备关联？如何表达？
Existing Facts      : devices 表存在（0 行）；IDENTITY_KINDS = (user, service, device_subject)；
                      identities.provider CHECK ∈ {local, oidc, saml, device, service}；
                      acl_subject_types 白名单固定 = {user, role, agent}（3 行已 seed）。
Frozen Constraints  : D-AUTH-18（Authorization Subject Type ≠ Identity Kind ≠ Identity Provider；
                      不得把 identity provider 值当作授权主体类型）；
                      D-P13-04（仅注册 agent subject type）；
                      Runtime 路线不得新增 schema ⇒ 只能使用既有 devices / identities 表。
Affected Layer      : authorization + runtime（identity 面）
Dependency          : OQ-P14-01 · OQ-P14-02
Risk If Wrong       : 混淆 identity kind 与 authorization subject type ⇒ 违反 D-AUTH-18；
                      若需新表字段 ⇒ 触犯「不新增 schema」边界（须另立授权）。
Evidence            : DEPENDENCY_MAP §2.1 · acl_subject_types 实测 3 行 · PDL D-AUTH-18 原文。
Human Decision Required : YES —— 是否启用设备维度，及其与用户身份的关联表达
```

---

## OQ-P14-04 — runtime permission check location

```text
ID                  : OQ-P14-04
Current Question    : 授权判定在何处执行（API 边界 / service 层 / policy 层 / DB 辅助）？
Existing Facts      : 分层 apps → agent → services → intelligence → core → infrastructure；
                      D-AUTH-16：Core = 契约与纯规则 · Application/Domain service = 判定编排 ·
                      Infrastructure = 持久化/适配；services/authorization 包尚不存在；
                      Agent 只能经 Authorization/Policy/Tool 契约访问受控能力。
Frozen Constraints  : D-AUTH-01（RBAC+ACL+Policy）· D-AUTH-07（DENY > ALLOW）·
                      D-AUTH-12（FAIL CLOSED / DEFAULT DENY）· D-AUTH-16（分层冻结）·
                      G-1…G-4 硬门（core ↛ SQLAlchemy · core ↛ services · agent ↛ services ·
                      domains ↛ {services, infrastructure}）。
Affected Layer      : authorization + runtime
Dependency          : OQ-P14-05（Policy 强制边界）· OQ-P14-07（services 结构）
Risk If Wrong       : 判定位置错误 ⇒ 越层依赖（直接触发硬门失败）或授权绕过面。
Evidence            : DEPENDENCY_MAP §2.2 · D-AUTH-16 原文 · tests/architecture 28 passed。
Human Decision Required : YES —— 判定层的归属与调用链形态
```

---

## OQ-P14-05 — policy enforcement boundary

```text
ID                  : OQ-P14-05
Current Question    : Policy 的强制边界在哪？是否存在必须由 DB 层兜底的判定？
Existing Facts      : DB 层强制先例 = C2（registry 保护，现含 CC-7 受信分支）·
                      tg_roles_is_system_protect · membership scope triggers ·
                      ck_permissions_action_canonical · tg_audit_immutable；
                      platform 侧 registry 保护已由 0016 完成。
Frozen Constraints  : Runtime 路线 Excluded = schema evolution（不得新增 trigger / 约束）；
                      D-OP101-08（runtime 不持 DDL 由 DB 层强制 + 正向断言 + 负向探针）；
                      D-AUTH-12（FAIL CLOSED）。
Affected Layer      : authorization + security（+ 潜在 schema 边界）
Dependency          : OQ-P14-04 · OQ-P14-13
Risk If Wrong       : 若判定"必须 DB 兜底" ⇒ 需 schema 变更 ⇒ 触犯本路线 Excluded（须另立授权）；
                      若全部放应用层 ⇒ 与 FAIL CLOSED 的强度要求可能不匹配。
Evidence            : SCOPE §3/§4 · PDL D-OP101-08 · 既有 DB 强制触发器清单（实测）。
Human Decision Required : YES —— 是否接受"应用层为唯一强制面"，或需另立 schema 授权
```

---

## OQ-P14-06 — API boundary

```text
ID                  : OQ-P14-06
Current Question    : 对外 API 契约形态（协议 / 版本策略 / 错误语义 / 分页与幂等约定）？
Existing Facts      : services/ = 业务持久化唯一归属（D-PLAT-01/03）；C-5（services 内部结构）、
                      C-6（domains 公开契约载体）均为未决；既有 /health 与 /ready 已定义；
                      docker-compose 已有 api 服务定义（端口 8000）。
Frozen Constraints  : D-PLAT-01/03/04/05（分层与 owner）· D-PLAT-14/16（readiness 语义）·
                      D-AUTH-15（Authorization Audit 设计边界）。
Affected Layer      : runtime + operations
Dependency          : OQ-P14-04 · OQ-P14-07 · OQ-P14-08
Risk If Wrong       : 对外契约一旦发布难以变更；影响后续所有 Domain 接入。
Evidence            : DEPENDENCY_MAP §2.2 · PDL 附录 C（C-5 / C-6）· compose 实测。
Human Decision Required : YES —— 协议族与契约策略（可延后至 PREP 收尾）
```

---

## OQ-P14-07 — service ownership

```text
ID                  : OQ-P14-07
Current Question    : services/ 的内部结构、模块粒度与 owner（PDL 附录 C 的 C-5）？
Existing Facts      : services/ 目录存在（git 跟踪 · 14 条目 · 2026-09-23 创建）；
                      D-AUTH-16 记 services/authorization/ 包尚不存在，须先建立；
                      C-5 原文「留待 Runtime PREP」（即本阶段）。
Frozen Constraints  : D-PLAT-01/03（services = 持久化唯一归属）· D-AUTH-16（分层冻结）·
                      G-2（core ↛ services）· G-3（agent ↛ services）。
Affected Layer      : runtime
Dependency          : OQ-P14-04
Risk If Wrong       : 结构选择错误会长期影响可维护性与守卫配置。
Evidence            : 实测 services/ 目录 · PDL 附录 C 的 C-5 · D-AUTH-16 影响面栏。
Human Decision Required : YES —— 目录与模块粒度（可延后至 PREP 收尾）
```

---

## OQ-P14-08 — failure handling

```text
ID                  : OQ-P14-08
Current Question    : 失败语义（超时 / 依赖不可用 / 部分失败 / 重试 / 幂等）？
Existing Facts      : D-PLAT-16 已定 readiness 探针超时 2000 ms ⇒ error ⇒ /ready 503（不重试不降级）；
                      D-PLAT-14 已定「缺失或无效 ⇒ error + critical」；
                      events = transactional outbox（P10）。
Frozen Constraints  : D-PLAT-12（FAIL CLOSED 原则面）· D-AUTH-12（FAIL CLOSED / DEFAULT DENY）·
                      D-PLAT-16（不重试不降级先例）。
Affected Layer      : runtime + operations
Dependency          : OQ-P14-06 · OQ-P14-10 · OQ-P14-11
Risk If Wrong       : 重试语义错误 ⇒ 重复副作用（尤在无幂等键时）。
Evidence            : ACCEPTANCE_MATRIX §2.6（FAL-1…FAL-3）· PDL D-PLAT-14/16。
Human Decision Required : YES（可在实施阶段细化）
```

---

## OQ-P14-09 — bootstrap process

```text
ID                  : OQ-P14-09
Current Question    : 首个平台管理员的 bootstrap 流程、执行者与凭据来源？
Existing Facts      : platform_state = 1（uninitialized）· platform_memberships = 0；
                      tg_pm_bootstrap_gate / tg_pm_last_admin 既有保护；
                      uap_app 对 platform_memberships / platform_state **无任何权限**（实测 4 项全 False）。
Frozen Constraints  : R4/R5（条件 = uninitialized AND PM 无行；原子流程 = 插 PM → 翻转 state →
                      audit('platform.admin.bootstrap') → COMMIT；普通 API/seed 永不写 PM；
                      无恢复 API）；D-P13-07（P13 零 PM 写入）。
Affected Layer      : security + operations + runtime
Dependency          : OQ-P14-02（凭据）· OQ-P14-13（写 platform_memberships / platform_state 的权限路径）
Risk If Wrong       : bootstrap 是平台最高权限入口；流程缺陷 ⇒ 单点或旁路风险。
Evidence            : PREP_REPORT §2.4 · PDL R4/R5 · uap_app 权限矩阵实测。
Human Decision Required : YES —— 执行形态（离线 CLI / 运维窗口 / 双人复核等）与凭据来源
```

---

## OQ-P14-10 — deployment model

```text
ID                  : OQ-P14-10
Current Question    : 部署模型（单机 / 编排 / 云托管）与配置与 secret 注入方式？
Existing Facts      : docker-compose.yml 存在（postgres + api + 可选 redis）；
                      D-PLAT-15 v2：期望 revision 由构建期只读工件承载（运行时不可覆盖）；
                      PDL 附录 C 的 C-10：docs/operations/ 部署手册缺失。
Frozen Constraints  : D-PLAT-15 v2 · D-PLAT-17 ⑦（不建 CI）· D-PLAT-08/14（配置门语义）。
Affected Layer      : operations + security
Dependency          : OQ-P14-02（secret 托管）· OQ-P14-11
Risk If Wrong       : 部署模型与 secret 注入方式错误 ⇒ 凭据暴露或运维不可行。
Evidence            : compose 实测 · PDL 附录 C（C-10）· D-PLAT-15 v2。
Human Decision Required : YES —— 部署形态与 secret 注入通道
```

---

## OQ-P14-11 — observability

```text
ID                  : OQ-P14-11
Current Question    : 可观测性范围（日志 / 指标 / 追踪 / 告警）与最小可用集？
Existing Facts      : /health（liveness）与 /ready（readiness 503 语义）已定义；
                      LOG_LEVEL / LOG_FORMAT 存在于 compose 环境；
                      audit_logs 提供平台审计面（非运行指标面）。
Frozen Constraints  : D-PLAT-14/16（readiness 语义）· D-PLAT-17 ⑦（本路线不建 CI）·
                      禁止在日志中泄露 secret（安全基线）。
Affected Layer      : operations
Dependency          : OQ-P14-08 · OQ-P14-10
Risk If Wrong       : 观测不足 ⇒ 运行期问题不可诊断；观测过度 ⇒ 成本与隐私面。
Evidence            : ACCEPTANCE_MATRIX §2.5（OPS-1/OPS-4）· compose 实测。
Human Decision Required : YES（可在实施阶段细化）
```

---

## OQ-P14-12 — C2 trust boundary usage

```text
ID                  : OQ-P14-12
Current Question    : Runtime 阶段如何使用 C2/CC-7 受信边界？是否存在需要 registry 变更的场景？
Existing Facts      : acl_subject_types = 3 行（user/role/agent）已满足 P13 基线；
                      C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff（CC-7 变体）；
                      CC-7 受信分支 = current_user = session_user = 'uap_migrator'；
                      runtime（uap_app）对 acl_subject_types 无任何权限（实测 4 项全 False）。
Frozen Constraints  : D-P13-03（registry 走 migration-controlled path · runtime INSERT FORBIDDEN ·
                      C2 必须保持）· D-P13-15（受信 migration context 可建 registry seed，
                      但 Does not authorize 明确不含对 Runtime 的授权）·
                      D-OP101-05（C2 判据形态 = CP-F / CC-7）。
Affected Layer      : security
Dependency          : OQ-P14-13
Risk If Wrong       : 若 Runtime 试图改 registry ⇒ 直接违反 D-P13-03/15 与 C2 设计；
                      若确需新 subject type ⇒ 必须另立独立授权（schema/seed 面）。
Evidence            : PDL D-P13-03/15 · D-OP101-05 · acl_subject_types 实测 · C2 函数体实测。
Human Decision Required : YES —— 是否声明"Runtime 完全不触碰 registry"，或另有安排
```

---

## OQ-P14-13 — runtime privilege boundary（含 OI-G-1）★ 关键

```text
ID                  : OQ-P14-13
Current Question    : uap_app 的逐表 DML 矩阵如何核定？onboarding / bootstrap 所需的写路径如何提供？
Existing Facts      : uap_app 显式授权 = **恰 5 项**（SCHEMA public USAGE · alembic_version SELECT ·
                      audit_logs INSERT/SELECT · audit_logs_202609 INSERT/SELECT）；
                      对 users / identities / roles / tenants / spaces / memberships /
                      platform_memberships / resource_permissions / events / agents / platform_state
                      等 **15 张关键表全部无权限**（SELECT/INSERT/UPDATE/DELETE 均 False，实测）；
                      uap_migrator 拥有 156 个 pg_class 对象（ownership 178 拓扑的一部分）；
                      pg_default_acl = 0（无默认授权 ⇒ 新表/分区不自动继承）。
Frozen Constraints  : D-OP101-07（runtime GRANT = minimum required set；**不得在未获新决策前扩权**；
                      不得授予 runtime 任何 DDL 权限）；
                      D-OP101-08（runtime 不持 DDL 由 DB 层强制 + 正向断言 + 负向探针）；
                      D-P10-13 禁止项「不得给应用运行时 DDL 权限」；
                      OI-G-1（runtime 逐表 DML 矩阵不可核定 · REGISTERED · BATCH-D）；
                      OI-G-2（未来 audit_logs 分区不继承授权）；
                      本轮 HARD RULES：禁止修改 GRANT / REVOKE / default ACL。
Affected Layer      : security + authorization + operations（+ 与 schema/治理面的边界）
Dependency          : OQ-P14-01 / 02 / 09（都需要写库）· OQ-P14-12
Risk If Wrong       : 这是本路线**唯一可能触碰权限面**的决策：
                      扩权过度 ⇒ 违反 D-OP101-07 的「最小集 + 未获新决策前不得扩权」；
                      不扩权 ⇒ onboarding / bootstrap 无法落库（功能不可实现）。
Evidence            : 本报告新增实测权限矩阵（见 P14_PRIVILEGE_BOUNDARY_ANALYSIS.md §1）·
                      PDL D-OP101-07/08 · handoff OI-G-1 / OI-G-2。
Human Decision Required : YES —— 必须选择写路径模型（详见 PRIVILEGE_BOUNDARY_ANALYSIS 的 OPTION A–D）
```

---

# Part 2 — 决策分层（A / B / C）

## 分类定义

```text
A = 必须先冻结才能实现（实现前必须取得 Human Decision；未定则实现无法正确开始）
B = 可 Runtime PREP 后置（PREP 收尾前必须定；不阻塞架构骨架）
C = 实现阶段再决定（可在实现轮内按既定原则细化，不构成架构选择）
```

## 分类结果

```text
A（7 项 · 实现前必须冻结）
  OQ-P14-01  identity onboarding flow      —— 决定身份模型与对外暴露面
  OQ-P14-02  credential lifecycle          —— 安全关键
  OQ-P14-04  permission check location     —— 分层归属，影响全部实现代码位置
  OQ-P14-05  policy enforcement boundary   —— 触碰「不新增 schema」边界
  OQ-P14-09  bootstrap process             —— 平台最高权限入口
  OQ-P14-12  C2 trust boundary usage       —— 安全边界声明
  OQ-P14-13  runtime privilege boundary    —— ★ 关键阻塞项（写路径存在性）

B（4 项 · 可 PREP 后置）
  OQ-P14-03  device / user association     —— 依赖 01/02 定后即可收敛
  OQ-P14-06  API boundary                  —— 对外契约，可后置至 PREP 收尾
  OQ-P14-07  service ownership（C-5）       —— 目录/粒度，可后置
  OQ-P14-10  deployment model              —— 运维面，可后置

C（2 项 · 实现阶段再决定）
  OQ-P14-08  failure handling              —— 在既定 FAIL CLOSED 原则下细化
  OQ-P14-11  observability                 —— 范围与深度可迭代
```

```text
合计：A 7 · B 4 · C 2 = 13 ✓（与 OQ 总数一致）
```

## 阻塞关系（分析 · 非结论）

```text
OQ-P14-13（A）⇒ 阻塞 OQ-P14-01 / OQ-P14-02 / OQ-P14-09 的**可实现性**
                 （三者都需要写库，而写权限路径未定）
OQ-P14-01（A）⇒ 前置 OQ-P14-02 / OQ-P14-03
OQ-P14-04（A）⇒ 前置 OQ-P14-06 / OQ-P14-07 / OQ-P14-08
⇒ 建议 Human 决策顺序（仅为顺序建议，非内容建议）：13 → 01/02 → 04/05/09/12 → B → C
```

---

# 3. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
新增文档 = 本报告（+ 同轮 3 份）
commit = 0 · tag = 0 · push = 0
本文档无 Decision 字段取值；P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 DECISION CLASSIFICATION REPORT（2026-09-27 · OQ 13 项取证完毕 · A7/B4/C2 · 未作任何裁定 · P14 IMPLEMENTATION = NOT AUTHORIZED）**
