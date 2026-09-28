# P14 Runtime Slice Human Decision Sheet

## Metadata

```text
Stage           : P14_RUNTIME_SLICE
Baseline        : 0017_p13_seed
HEAD            : c420403d5469241e8b03855428ebce435d539c9e
Release         : UAP-V0.1.9-P13-SEED
Decision status : PENDING
Sheet status    : PREPARATION ONLY —— 本轮**不执行任何 Decision**、不改动任何冻结状态
Decision maker  : Human（本 Sheet 不代裁）
Scope           : OQ-P14-01 … OQ-P14-13（13 项）+ ADD-1 / ADD-2（2 项）= 15 项
```

```text
填写规则
  · 每项在 `Human Decision` 勾选其一（A / B / C / CUSTOM），或留空表示未裁
  · 本 Sheet 不出现任何倾向性结论措辞（不标注任一选项更优 / 更强 / 更易实现）
  · 框架性结论（基线 · 冻结约束 · 影响 · 依赖 · 风险）为事实登记，非方向性主张
  · 本轮填写的 `Decision filled = 0`
```

---

# Batch 0 — Governance Meta Decisions

## ADD-2 — P14 决策登记位置

```text
Question            : P14 的裁定结果登记在何处？
Existing Facts      : PDL 为跨阶段 canonical decision carrier（D-PLAT / D-AUTH / D-P13 / D-OP101 均登记于此）；
                      PDL 近期已有 append 先例（附录 K = D-P13-15 登记 · 附录 L = OPEN-P10-1 汇总 ·
                      附录 M = P14 阶段编号与文档集合冻结）。
                      现有 P14 文档 4 份（SCOPE / DEPENDENCY_MAP / PREP_REPORT / ACCEPTANCE_MATRIX）
                      均非决策记录载体。
Frozen Constraints  : 「既有 D-* 正文零改写 · 只能 append-only」（历轮登记口径）；
                      RUNTIME_DOCUMENT_SET_DECISION.md §2 已冻结文档集合（4 份）。
Affected Components : decision carrier（PDL 附录 / Contract 内附录）· 后续全部裁定的落点
Dependency          : 无上游；**前置**于 Batch 1 起的全部裁定登记
Risk                : 若登记位置在首批裁定后才定 ⇒ 已裁内容需二次搬运（重复劳动 + 漂移风险）
```

```text
Available Options

OPTION A — 登记于 PDL 新附录（append-only）
  Description            : 在 PLATFORM_DECISION_LOG.md 追加新附录登记 P14 决策。
  Impact                 : 沿用 canonical carrier；跨阶段检索统一；PDL 继续为唯一决策权威。
  Pros                   : 与 D-P13-15 / D-OP101 的登记先例一致；不新增文件。
  Risks                  : PDL 体积继续增长；需新增 END 行（既有 END 行保留）。
  Required Follow-up     : 确认附录编号（下一可用字母）与登记格式。

OPTION B — 登记于 Contract 内附录
  Description            : 决策随实施契约文档一并登记。
  Impact                 : 决策与实施规则同处一文，阅读连贯。
  Pros                   : 单文档自洽；实施者无需跨文件跳转。
  Risks                  : 决策载体分散（PDL 不再是唯一权威）⇒ 与 canonical carrier 原则张力。
  Required Follow-up     : 需先确认 ADD-1 是否选择新增 Contract。

OPTION C — CUSTOM
  Description            : Human 指定其他登记形式。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

## ADD-1 — Contract 载体

```text
Question            : 是否新增 P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md（实施规则载体）？
Existing Facts      : 现有文档覆盖 F-2 Scope / F-3 Dependency / F-5 Acceptance，
                      但 F-4 Implementation rules 与 F-1 P14 决策登记位置无权威载体；
                      P13 先例：P13_IMPLEMENTATION_CONTRACT.md 独立存在（约 30.7 KB）。
Frozen Constraints  : RUNTIME_DOCUMENT_SET_DECISION.md §2 冻结文档集合 = 4 份；
                      新增第 5 份须先 amend 该决策。
Affected Components : 文档集合 · 实施规则载体 · 后续实施者的阅读路径
Dependency          : ADD-2（登记位置）· 前 5 批裁定内容（实施规则需有内容可写）
Risk                : 若无实施规则载体 ⇒ 实施者须自行拼接规则（与项目纪律冲突）；
                      若载体与 SCOPE/Matrix 表述不一致 ⇒ 需额外一致性维护
```

```text
Available Options

OPTION A — 新增 Contract（文档集合 4 → 5）
  Description            : 新增独立实施契约文档，并 amend 文档集合决策。
  Impact                 : 实施规则单一权威载体；与 P13 形态一致。
  Pros                   : 读者路径清晰；可独立冻结与版本化。
  Risks                  : 需额外一轮 amend；新增文件存在与 SCOPE/Matrix 漂移风险。
  Required Follow-up     : 文档集合 amend 的登记轮；Contract 冻结时机；与 ACCEPTANCE_MATRIX 的边界划分。

OPTION B — 维持 4 份，规则并入既有载体
  Description            : 在 SCOPE 或 PREP_REPORT 内扩展实施规则章节。
  Impact                 : 不触碰已冻结的文档集合决策。
  Pros                   : 文档数量不变；无 amend 轮。
  Risks                  : SCOPE 职责扩张（范围文档承担规则职责）；内容可能被后续编辑淹没。
  Required Follow-up     : 确定实施规则的章节归属与冻结要求。

OPTION C — Contract + PDL 附录（决策与规则分离）
  Description            : 新增 Contract 承载实施规则；决策登记于 PDL（见 ADD-2）。
  Impact                 : 决策与规则各自单一职责。
  Pros                   : 与 P13 的"决策在 PDL、规则在 Contract"形态一致。
  Risks                  : 两处维护，需要一致性纪律。
  Required Follow-up     : ADD-2 取 A 时方可采用；Contract 冻结时机。

OPTION D — CUSTOM
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

---

# Batch 1 — Security Root Decisions

## OQ-P14-13 — runtime privilege boundary ★

```text
Question            : uap_app 的逐表 DML 矩阵如何核定？onboarding / bootstrap 所需写路径如何提供？
Existing Facts      : uap_app 显式授权 = 恰 5 项（SCHEMA public USAGE · alembic_version SELECT ·
                      audit_logs(+当期分区) INSERT/SELECT）；CREATE = false；
                      16 张抽查表中 15 张对 uap_app **SELECT/INSERT/UPDATE/DELETE 全为 False**
                      （含 users / identities / credentials / sessions / roles / permissions /
                       role_permissions / tenants / spaces / platform_memberships /
                       tenant_memberships / memberships / resource_permissions / events / agents /
                       platform_state）；pg_default_acl = 0；
                      uap_migrator = 245 行显式授权（自持实体化）· owner 156 对象 · NOSUPERUSER · CREATE=false。
Frozen Constraints  : D-OP101-07（runtime GRANT = minimum required set · **未获新决策前不得扩权** ·
                      不得授予 runtime 任何 DDL 权限）；
                      D-OP101-08（runtime 不持 DDL · DB 层强制 + 正向断言 + 负向探针）；
                      D-P10-13 禁止项（不得给应用运行时 DDL 权限）；
                      OI-G-1（runtime 逐表 DML 矩阵不可核定 · 不得扩权 · REGISTERED / BATCH-D）；
                      OI-G-2（未来 audit_logs 分区不继承授权）；
                      D-PLAT-13（Governance Slice ≠ Runtime）。
Affected Components : uap_app 授权面 · GRANT/default ACL 面 · 受信写路径（如有）·
                      身份/授权/成员关系表的写入能力 · 审计写入面
Dependency          : 根节点（无上游）· 阻塞 OQ-01/02/03/04/09 的可实现性
Risk                : 扩权过度 ⇒ 违反 D-OP101-07 与 OI-G-1；不扩权 ⇒ onboarding / bootstrap 无法落库
```

```text
Available Options

OPTION A — Runtime direct database access
  Description            : 为 uap_app 按最小集逐表授予 SELECT/INSERT/UPDATE/DELETE；写路径由 runtime 直接执行。
  Impact                 : runtime 授权面由 5 项扩至数十项；需一次 GRANT 面变更（另立授权轮）。
  Pros                   : 实现直接；无新增组件或角色。
  Risks                  : 风险集中（runtime 被攻破即可写身份/授权表）；与 OI-G-1 张力最大；
                           未来分区需逐分区授权（OI-G-2）。
  Required Follow-up     : ① 逐表最小集清单；② OI-G-1 处置；③ 承载 GRANT 的授权轮；
                           ④ 未来分区授权流程。

OPTION B — Trusted internal runtime service boundary
  Description            : runtime 保持低权限；写路径经受信内部边界（专用组件/角色/服务）执行。
  Impact                 : 新增内部分层成员；需定义其归属层与调用契约（触及 C-5/C-6 未决项）。
  Pros                   : runtime 直接权限面小；写入路径集中便于审计。
  Risks                  : 风险转移至受信边界（其凭据成为关键资产）；
                           若复用 uap_migrator 则与身份分离意图张力显著。
  Required Follow-up     : ① 是否设立受信边界；② 其身份形态；③ 权限集；④ 凭据托管；⑤ 与 OI-G-1 及角色拓扑的关系。

OPTION C — CLI / bootstrap controlled privileged path
  Description            : runtime 不扩权（或仅补最小 SELECT）；写动作由受信 CLI 以既有 uap_migrator 执行。
  Impact                 : 平台入网改为人工驱动；runtime 成为只读或无写服务面。
  Pros                   : 权限面最小；与 R4/R5「bootstrap 由受信 CLI」先例一致。
  Risks                  : 规模化人工成本；与 multi-user / usable 产品目标张力；
                           未来若要开放注册仍需另立决策。
  Required Follow-up     : ① 是否接受人工 CLI 入驻及适用范围；② runtime 是否需读权限及最小读集；
                           ③ 授权时机与承载。

OPTION D — Hybrid model
  Description            : 组合形态，例如：读侧给 uap_app 最小 SELECT + 写侧走受信路径；
                           或新增专用角色（如 uap_service）；或分阶段（先 C，再评估 A/B）。
  Impact                 : 读写路径分离或角色数增加；分阶段可能引入临时形态。
  Pros                   : 可按风险分层。
  Risks                  : 角色/路径增多 ⇒ 治理复杂度上升；新增角色需评估与 RM-D 拓扑及
                           uap_readonly（DEFER）的关系；分阶段存在"临时固化"风险。
  Required Follow-up     : ① 是否采用混合/分阶段；② 是否允许新增数据库角色；③ 各阶段授权清单与撤回条件。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] OPTION D
  [ ] CUSTOM

Human Notes:

```

## OQ-P14-12 — C2 trust boundary usage

```text
Question            : Runtime 阶段如何使用 C2/CC-7 受信边界？是否存在需要 registry 变更的场景？
Existing Facts      : acl_subject_types = 3 行（user / role / agent）已满足 P13 基线；
                      C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff（CC-7 变体 · 受信分支 =
                      current_user = session_user = 'uap_migrator'）；
                      uap_app 对 acl_subject_types 无任何权限（4 项全 False）；tg_acl_subject_types_protect 启用。
Frozen Constraints  : D-P13-03（registry 走 migration-controlled path · runtime INSERT FORBIDDEN ·
                      C2 必须保持）· D-P13-15（受信 migration context 可建 registry seed，但
                      Does not authorize 明确不含对 Runtime 的授权）·
                      D-OP101-05（C2 判据 = CP-F / CC-7）。
Affected Components : acl_subject_types 使用面 · C2/CC-7 依赖关系 · 验收 SEC-2 / IDL-5
Dependency          : 无上游；收窄 OQ-P14-13 与 OQ-P14-01 的候选空间
Risk                : 若 Runtime 试图改 registry ⇒ 直接违反 D-P13-03/15；若确需新 subject type ⇒
                      必须另立独立授权（schema / seed 面）
```

```text
Available Options

OPTION A — 声明「Runtime 完全不触碰 registry」
  Description            : 明确 Runtime 不使用、不修改 acl_subject_types；registry 维持 P13 基线 3 行。
  Impact                 : 收窄候选空间；无需处理 C2 与 runtime 的交互。
  Pros                   : 与 D-P13-03/15 完全一致；验收 SEC-2 / IDL-5 判据清晰。
  Risks                  : 若未来确需新 subject type ⇒ 需重启独立授权（不在本路线内解决）。
  Required Follow-up     : 无（或登记为"未来变更须另立授权"）。

OPTION B — 允许未来在受信状态下评估 registry 扩展
  Description            : 不排除未来经受信 migration context 扩展 registry 的可能，但不在本路线实施。
  Impact                 : 需登记"未来变更路径"，并明确其不属于 P14 scope。
  Pros                   : 保留演进空间。
  Risks                  : 表述若不够严格 ⇒ 可能被解读为当前授权的延伸（与 D-P13-15 的
                           Does not authorize 张力）。
  Required Follow-up     : 明确未来变更的授权轮与边界表述。

OPTION C — CUSTOM
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

---

# Batch 2 — Identity Foundation

## OQ-P14-01 — runtime identity onboarding flow

```text
Question            : 首个可登录主体（users 行）由哪条路径建立？流程形态是什么？
Existing Facts      : users = 0 · tenants/spaces = 0 · platform_state = uninitialized；
                      ck_users_login 要求 email 或 username 非空；identities / devices / credentials /
                      sessions 表均存在（0 行）；services/authorization 包尚不存在（D-AUTH-16）。
Frozen Constraints  : D-P13-06（identity row allowed · credential secret forbidden ·
                      「首个可登录主体」与「P13 创建主体记录」必须区分）；
                      D-PLAT-11①（首个正式可登录主体只经 P13 建立）+ ②（禁第二套 dev bootstrap 路径）；
                      D-P13-13（credentials = 0 在 P13 侧）。
Affected Components : users / identities / memberships · onboarding 服务面 · 审计面 · authorization runtime
Dependency          : OQ-P14-13（写路径）· OQ-P14-12（边界声明）· 前置 OQ-P14-02 / OQ-P14-03
Risk                : 与 D-PLAT-11① 冲突的路径需重新解释该冻结决策；自助注册会扩大对外暴露面
```

```text
Available Options

OPTION A — 受信 CLI 引导（人工驱动）
  Description            : 由运维/管理员运行受信 CLI 建立首个主体。
  Impact                 : users 行人工建立；规模受限；audit 事件少而清晰。
  Pros                   : 权限面小；与 R4/R5 既有 CLI 先例一致。
  Risks                  : 无法自助入网；与 multi-user 目标张力。
  Required Follow-up     : CLI 形态（见 OQ-P14-09）· 凭据方案（OQ-P14-02）。

OPTION B — API 自助注册
  Description            : 通过对外接口自助建立主体。
  Impact                 : users 行自动增长；需滥用防护；审计事件显著增加。
  Pros                   : 可扩展性好。
  Risks                  : 暴露面与滥用风险；需新增防护机制（新决策）。
  Required Follow-up     : 防护策略 · 审计 action 定义 · 会话面（sessions 写路径）。

OPTION C — 邀请制
  Description            : 由既有主体签发邀请，受邀者完成主体建立。
  Impact                 : 需邀请凭据的生成 / 校验 / 撤销机制。
  Pros                   : 介于 A 与 B 之间。
  Risks                  : 新增机制（邀请生命周期）⇒ 新的待决项。
  Required Follow-up     : 邀请机制设计 · 与 OQ-P14-02 的凭据方案关系。

OPTION D — 管理员代建
  Description            : 由管理员批量创建主体记录。
  Impact                 : 信任边界集中在管理员；需定义代建权限。
  Pros                   : 可控性强。
  Risks                  : 可能触及 RBAC 面（代建权限的定义）。
  Required Follow-up     : 代建权限定义 · 通知/交付凭据方式。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] OPTION D
  [ ] CUSTOM

Human Notes:

```

## OQ-P14-02 — credential lifecycle

```text
Question            : 凭据如何建立、存储、轮换、失效？密钥材料来源？
Existing Facts      : credentials / identities / sessions 表存在（0 行）；仓库内无 KMS / 密钥管理面。
Frozen Constraints  : D-P13-13（明文 / 可逆 / 伪造密码 = 0）· SEED_STRATEGY §6（密码由 onboarding 设置）·
                      R4/R5（bootstrap 由受信 CLI + audit）· D-AUTH-18（identity provider ≠ authorization subject）。
Affected Components : credentials / identities 存储 · 认证校验路径 · 轮换与失效流程 · secret 托管 ·
                      验收 SEC-4 / IDL-2 / IDL-3 / AUDX-5
Dependency          : OQ-P14-01 · OQ-P14-10（secret 注入）· OQ-P14-13（写权限）
Risk                : 哈希/轮换/托管选择不当 ⇒ 安全事件面；引入外部 IdP ⇒ 新信任边界
```

```text
Available Options

OPTION A — 自管（库内哈希 + 本地密钥材料）
  Description            : 凭据哈希存库；密钥材料由部署面提供。
  Impact                 : 使用 credentials 表写面；需定义哈希族与参数。
  Pros                   : 无外部依赖；与既有表结构一致。
  Risks                  : 哈希参数/轮换策略设计不当即构成薄弱点；密钥材料托管需另定。
  Required Follow-up     : 哈希族与参数 · 轮换周期 · 失效与恢复 · 密钥材料托管方式。

OPTION B — 外部 IdP 托管
  Description            : 认证交由外部身份提供方，库内仅保留映射。
  Impact                 : 使用 identities.provider 既有取值；不写 credentials 或仅存映射；
                           引入网络与外部信任依赖。
  Pros                   : 认证强度与运维负担可外移。
  Risks                  : 新增信任边界与可用性依赖；与 D-AUTH-18 的词汇分离需明确表述。
  Required Follow-up     : IdP 选型与信任模型 · provider 取值使用规范 · 会话面。

OPTION C — 设备绑定凭据
  Description            : 以设备为单位的凭据形态。
  Impact                 : 使用 devices / sessions 表；影响认证与恢复流程。
  Pros                   : 强绑定，降低凭据扩散面。
  Risks                  : 恢复路径复杂（设备丢失）；多设备场景需配套策略。
  Required Follow-up     : 设备注册与撤销 · 恢复流程 · 与 OQ-P14-03 的关系。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

## OQ-P14-03 — device / user association

```text
Question            : 是否引入设备主体与用户的多设备关联？如何表达？
Existing Facts      : devices 表存在（0 行）；IDENTITY_KINDS = (user, service, device_subject)；
                      identities.provider CHECK ∈ {local, oidc, saml, device, service}；
                      acl_subject_types 白名单固定 = {user, role, agent}（3 行）。
Frozen Constraints  : D-AUTH-18（Authorization Subject Type ≠ Identity Kind ≠ Identity Provider）；
                      D-P13-04（仅注册 agent subject type）；
                      Runtime 路线 Excluded = schema evolution（只能使用既有表）。
Affected Components : devices / identities 关联表达 · 认证流程分支 · 验收 IDF-3 / IDL-6
Dependency          : OQ-P14-01 · OQ-P14-02
Risk                : 混淆 identity kind 与 authorization subject type ⇒ 违反 D-AUTH-18；
                      若需新字段 ⇒ 触犯「不新增 schema」边界
```

```text
Available Options

OPTION A — 启用设备维度（使用既有 devices / identities）
  Description            : 建立用户与设备的多对多关联，作为认证增强。
  Impact                 : 认证流程增加设备判定；使用既有表，无 schema 变更。
  Pros                   : 提升会话安全；支持多设备场景。
  Risks                  : 恢复与撤销流程复杂；需明确授权主体词汇不被污染。
  Required Follow-up     : 设备生命周期 · 撤销与恢复 · 审计事件。

OPTION B — 不启用设备维度（本期仅用户主体）
  Description            : 仅以用户主体进行认证，不使用 devices 表。
  Impact                 : 认证流程简化；devices 表保持 0 行。
  Pros                   : 实现面最小。
  Risks                  : 多设备安全能力不足（未来可能重启该议题）。
  Required Follow-up     : 无（或登记为未来议题）。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] CUSTOM

Human Notes:

```

---

# Batch 3 — Authorization Runtime

## OQ-P14-04 — runtime permission check location

```text
Question            : 授权判定在何处执行（API 边界 / service 层 / policy 层 / DB 辅助）？
Existing Facts      : 分层 apps → agent → services → intelligence → core → infrastructure；
                      D-AUTH-16：Core = 契约与纯规则 · Application/Domain service = 判定编排 ·
                      Infrastructure = 持久化/适配；services/authorization 包尚不存在。
Frozen Constraints  : D-AUTH-01 / 07 / 12（RBAC+ACL+Policy · DENY > ALLOW · FAIL CLOSED / DEFAULT DENY）·
                      D-AUTH-16（分层冻结）· 硬门 G-1…G-4。
Affected Components : authorization 判定层 · services/authorization · 验收 AUT-4（+ 间接 ABC-4）
Dependency          : OQ-P14-13（读侧权限）· 前置 OQ-P14-05 / OQ-P14-06 / OQ-P14-07 / OQ-P14-08
Risk                : 位置错误 ⇒ 越层依赖（触发硬门失败）或授权绕过面
```

```text
Available Options

OPTION A — Policy 层集中判定（core 契约 + service 编排）
  Description            : 判定逻辑集中于 policy/authorization service，由 API 层调用。
  Impact                 : 需建立 services/authorization（D-AUTH-16 已预期）；需读侧权限。
  Pros                   : 与既有分层冻结一致；判定一致性强；测试面集中。
  Risks                  : 需一次读侧授权（依赖 OQ-P14-13 结论）。
  Required Follow-up     : 读权限清单 · policy 与服务边界划分（OQ-P14-05 / 07）。

OPTION B — API 层分散判定
  Description            : 各入口自行判定。
  Impact                 : 判定逻辑分布在各 endpoint。
  Pros                   : 局部实现快。
  Risks                  : 一致性风险高；一处遗漏即绕过；测试面分散。
  Required Follow-up     : 一致性保障机制 · 审计覆盖。

OPTION C — 数据库层辅助判定
  Description            : 部分判定下推至 DB（如策略表 / 视图 / 函数）。
  Impact                 : 触及 schema 边界（新增对象）⇒ 超出 Runtime Excluded。
  Pros                   : 强制性强（难以绕过）。
  Risks                  : 违反本路线 Excluded；须另立独立授权。
  Required Follow-up     : 独立授权轮 · schema 设计（若 Human 选择此方向）。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

## OQ-P14-05 — policy enforcement boundary

```text
Question            : Policy 的强制边界在哪？是否存在必须由 DB 层兜底的判定？
Existing Facts      : DB 层强制先例 = C2（含 CC-7）· tg_roles_is_system_protect ·
                      membership scope triggers · ck_permissions_action_canonical · tg_audit_immutable。
Frozen Constraints  : Runtime Excluded = schema evolution；
                      D-OP101-08（runtime 不持 DDL · DB 层强制 + 断言 + 负向探针）· D-AUTH-12（FAIL CLOSED）。
Affected Components : policy 判定链 · 既有触发器的复用方式 · 验收 AUT-3 / SEC-2 · SCOPE §3
Dependency          : OQ-P14-04 · OQ-P14-13
Risk                : 「需 DB 兜底」⇒ 需 schema 变更 ⇒ 触犯 Excluded（须另立授权）；
                      全放应用层 ⇒ 与 FAIL CLOSED 强度要求可能不匹配
```

```text
Available Options

OPTION A — 应用层为唯一强制面（复用既有 DB 护栏，不新增）
  Description            : 判定全部在应用层；DB 层仅保留既有触发器作为防护。
  Impact                 : 无 schema 变更；与 Excluded 一致。
  Pros                   : 不触碰边界；实施面清晰。
  Risks                  : 绕过风险依赖应用层正确性（需充分测试与审计）。
  Required Follow-up     : 判定的测试与审计覆盖 · 绕过场景清单。

OPTION B — 新增 DB 层兜底（另立授权）
  Description            : 通过新增触发器 / 约束强化强制。
  Impact                 : 需要独立授权轮 + schema 设计；超出本路线 Excluded。
  Pros                   : 强制强度高。
  Risks                  : 违反本路线 Excluded；影响既有 schema 稳定性（178 ownership / 39 triggers）。
  Required Follow-up     : 独立授权轮 · schema 设计与迁移（不在本路线）。

OPTION C — 混合（应用层为主 + 明确列举需 DB 兜底的少数场景）
  Description            : 对少数高风险点请求 DB 兜底，其余在应用层。
  Impact                 : 部分触及 schema 边界（同样需独立授权）。
  Pros                   : 风险与复杂度折中。
  Risks                  : 仍需独立授权；边界表述须精确以免范围漂移。
  Required Follow-up     : 高风险点清单 · 独立授权轮。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

---

# Batch 4 — Runtime Interface

## OQ-P14-06 — API boundary

```text
Question            : 对外 API 契约形态（协议 / 版本策略 / 错误语义 / 分页与幂等约定）？
Existing Facts      : services/ = 业务持久化唯一归属（D-PLAT-01/03）；PDL 附录 C 的 C-5 / C-6 未决；
                      /health 与 /ready 已定义；compose 已有 api 服务（端口 8000）。
Frozen Constraints  : D-PLAT-01/03/04/05 · D-PLAT-14/16（readiness 语义）· D-AUTH-15（审计设计边界）。
Affected Components : 对外接口层 · 契约载体（C-6）· 验收 OPS-1 / FLM-* 的判据形态
Dependency          : OQ-P14-04 · OQ-P14-07；前置 OQ-P14-08
Risk                : 对外契约一旦发布难以变更；影响后续所有 Domain 接入
```

```text
Available Options

OPTION A — REST/JSON（含版本前缀与统一错误模型）
  Description            : 采用 REST 风格 + 显式版本策略 + 统一错误语义。
  Impact                 : 标准形态；契约文档化成本中等。
  Pros                   : 通用性高；工具链成熟。
  Risks                  : 分页/幂等约定需逐条定义。
  Required Follow-up     : 版本策略细则 · 错误码表 · 幂等键约定。

OPTION B — RPC 风格（强类型契约）
  Description            : 以强类型 RPC 契约为接口面。
  Impact                 : 需引入契约定义与代码生成环节。
  Pros                   : 类型安全；契约明确。
  Risks                  : 工具链与调试成本上升；与既有 compose/api 形态的适配需确认。
  Required Follow-up     : 契约定义语言与生成流程。

OPTION C — 内部服务面优先（暂不对外）
  Description            : 仅建立内部服务边界，对外接口延后。
  Impact                 : 缩小本阶段对外承诺面。
  Pros                   : 降低过早承诺风险。
  Risks                  : 与「practical / usable」目标的时间点张力。
  Required Follow-up     : 对外接口的后续轮次安排。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

## OQ-P14-07 — service ownership（PDL 附录 C 的 C-5）

```text
Question            : services/ 的内部结构、模块粒度与 owner？
Existing Facts      : services/ 目录存在（git 跟踪 · 14 条目 · 2026-09-23 创建）；
                      D-AUTH-16 记 services/authorization 包尚不存在；
                      PDL 附录 C 的 C-5 原文「留待 Runtime PREP」。
Frozen Constraints  : D-PLAT-01/03（services = 持久化唯一归属）· D-AUTH-16（分层冻结）·
                      G-2（core ↛ services）· G-3（agent ↛ services）。
Affected Components : services/ 内部布局 · 守卫配置 · 验收 ABC-4（间接）
Dependency          : OQ-P14-04；阻塞 OQ-P14-06
Risk                : 结构选择影响长期可维护性与守卫配置
```

```text
Available Options

OPTION A — 按能力域分包（authorization / identity / audit …）
  Description            : 每个能力域一个包，包内自带接口与实现。
  Impact                 : 结构清晰；与 D-AUTH-16 的 services/authorization 命名一致。
  Pros                   : 易于定位与测试。
  Risks                  : 包数量增加；跨能力协作的边界需定义。
  Required Follow-up     : 包子集清单 · 依赖方向规则。

OPTION B — 按层分包（service / repository / adapter）
  Description            : 以技术分层组织。
  Impact                 : 与 infrastructure 职责可能出现重叠，需小心划分。
  Pros                   : 技术关注点集中。
  Risks                  : 与 D-PLAT-03（services = 业务持久化归属）表述需对齐。
  Required Follow-up     : 与 infrastructure 的边界规则。

OPTION C — 扁平结构（少量模块）
  Description            : 单一层次的少量模块，按需再拆分。
  Impact                 : 初期最简；后期可能重构。
  Pros                   : 落地快。
  Risks                  : 规模上升后结构压力。
  Required Follow-up     : 何时重构的判据。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

## OQ-P14-09 — bootstrap process

```text
Question            : 首个平台管理员的 bootstrap 流程、执行者与凭据来源？
Existing Facts      : platform_state = 1（uninitialized）· platform_memberships = 0；
                      tg_pm_bootstrap_gate / tg_pm_last_admin 启用；
                      uap_app 对 platform_memberships / platform_state 无任何权限（4 项全 False）。
Frozen Constraints  : R4/R5（条件 = uninitialized AND PM 无行；原子流程 = 插 PM → 翻转 state →
                      audit('platform.admin.bootstrap') → COMMIT；普通 API/seed 永不写 PM；
                      无恢复 API）· D-P13-07（P13 零 PM 写入）。
Affected Components : CLI 形态 · 执行者与凭据 · audit 写入 · 验收 OPS-3 / AUD-3 / AUDX-2
Dependency          : OQ-P14-13（写路径）· OQ-P14-02（凭据来源）
Risk                : bootstrap 是平台最高权限入口；流程缺陷 ⇒ 单点或旁路风险
```

```text
Available Options

OPTION A — 离线 CLI + 人工复核（单执行者）
  Description            : 运维人员在本机运行受信 CLI 完成初始化。
  Impact                 : 依赖运维纪律；凭据由运维在受控环境提供。
  Pros                   : 实现简单；与 R4/R5 先例一致。
  Risks                  : 单点操作；凭据交接环节需谨慎。
  Required Follow-up     : 凭据来源与交接流程 · 留证要求。

OPTION B — 离线 CLI + 双人复核
  Description            : 初始化需两人分别确认（四眼原则）。
  Impact                 : 流程增加一步确认；审计更完整。
  Pros                   : 降低单点失误与内部风险。
  Risks                  : 运维流程复杂度上升。
  Required Follow-up     : 双人流程与留证格式。

OPTION C — 受信运维窗口 + 专用凭据
  Description            : 在受控窗口内以专用受信凭据执行初始化。
  Impact                 : 需专用凭据的生成、使用与回收流程。
  Pros                   : 与常规运维流程隔离。
  Risks                  : 专用凭据本身成为新资产（需托管与轮换）。
  Required Follow-up     : 凭据托管与轮换 · 窗口流程与留证。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

---

# Batch 5 — Operations

## OQ-P14-10 — deployment model

```text
Question            : 部署模型与配置 / secret 注入方式？
Existing Facts      : docker-compose.yml 存在（postgres + api + 可选 redis）；
                      D-PLAT-15 v2 要求期望 revision 由构建期只读工件承载（运行时不可覆盖）；
                      PDL 附录 C 的 C-10：docs/operations/ 部署手册缺失。
Frozen Constraints  : D-PLAT-15 v2 · D-PLAT-17 ⑦（不建 CI）· D-PLAT-08/14（配置门语义）。
Affected Components : 部署拓扑 · 配置面 · secret 注入 · 验收 OPS-4
Dependency          : OQ-P14-02（secret 托管）；前置 OQ-P14-11
Risk                : 部署与 secret 注入选择不当 ⇒ 凭据暴露或运维不可行
```

```text
Available Options

OPTION A — 单机 / 开发形态（沿用 compose）
  Description            : 以现有 compose 为运行时载体。
  Impact                 : 最小改动；适合单环境。
  Pros                   : 落地最快。
  Risks                  : 生产可用性/隔离能力有限。
  Required Follow-up     : secret 注入方式 · 与 EXPECTED_ALEMBIC_REVISION 工件的配合。

OPTION B — 容器编排（多环境）
  Description            : 以编排平台承载，区分环境与 secret 管理。
  Impact                 : 需编排清单、secret 管理与发布流程。
  Pros                   : 可扩展；环境隔离。
  Risks                  : 运维复杂度上升。
  Required Follow-up     : 编排清单 · secret 管理集成 · 发布与回滚流程。

OPTION C — 云托管
  Description            : 采用托管运行环境。
  Impact                 : 依赖云厂商能力与网络边界。
  Pros                   : 运维负担外移。
  Risks                  : 引入外部依赖与成本模型。
  Required Follow-up     : 托管选型 · 网络与凭据边界。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

## OQ-P14-08 — failure handling

```text
Question            : 失败语义（超时 / 依赖不可用 / 部分失败 / 重试 / 幂等）？
Existing Facts      : D-PLAT-16（readiness 探针 2000 ms ⇒ error ⇒ /ready 503，不重试不降级）；
                      D-PLAT-14（缺失或无效 ⇒ error + critical）；events = transactional outbox（P10）。
Frozen Constraints  : D-AUTH-12（FAIL CLOSED / DEFAULT DENY）· D-PLAT-16（不重试不降级先例）。
Affected Components : 超时/重试/幂等策略 · 部分失败补偿 · 验收 FAL-1…FAL-3 / FLM-2…FLM-4
Dependency          : OQ-P14-06
Risk                : 重试语义错误 ⇒ 重复副作用（无幂等键时尤甚）
```

```text
Available Options

OPTION A — 全面 FAIL CLOSED + 幂等键（不自动重试写操作）
  Description            : 依赖失败即拒绝；写操作要求幂等键；不自动重试。
  Impact                 : 行为确定；需幂等键设计。
  Pros                   : 与既有 FAIL CLOSED 原则一致；避免重复副作用。
  Risks                  : 可用性依赖依赖稳定性（无退避重试）。
  Required Follow-up     : 幂等键约定 · 错误分类与响应语义。

OPTION B — 有限重试（幂等操作）+ FAIL CLOSED（非幂等）
  Description            : 对幂等读/写做有限退避重试；非幂等操作直接拒绝。
  Impact                 : 提升弱网络下的可用性；需区分幂等性。
  Pros                   : 可用性与安全折中。
  Risks                  : 幂等性判定错误 ⇒ 重复副作用。
  Required Follow-up     : 幂等性判定规则 · 重试上限与退避策略。

OPTION C — 异步队列 + 补偿
  Description            : 写入经队列异步处理，失败由补偿机制处理。
  Impact                 : 引入队列组件（新依赖）与最终一致性语义。
  Pros                   : 削峰与解耦。
  Risks                  : 复杂度显著上升；可能需要新的基础设施决策。
  Required Follow-up     : 队列选型 · 幂等与补偿设计 · 与 events outbox 的关系。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

## OQ-P14-11 — observability

```text
Question            : 可观测性范围（日志 / 指标 / 追踪 / 告警）与最小可用集？
Existing Facts      : /health 与 /ready 已定义；LOG_LEVEL / LOG_FORMAT 存在于 compose 环境；
                      audit_logs 提供平台审计面（非运行指标面）。
Frozen Constraints  : D-PLAT-14/16（readiness 语义）· D-PLAT-17 ⑦（不建 CI）·
                      禁止在日志中泄露 secret。
Affected Components : 日志/指标/追踪/告警最小集 · 验收 OPS-4
Dependency          : OQ-P14-10 · OQ-P14-08
Risk                : 观测不足 ⇒ 问题不可诊断；观测过度 ⇒ 成本与隐私面
```

```text
Available Options

OPTION A — 结构化日志 + readiness（最小集）
  Description            : 仅结构化日志 + 既有 readiness/health。
  Impact                 : 依赖面最小。
  Pros                   : 实现成本低；与既有 LOG_FORMAT 一致。
  Risks                  : 缺少指标/追踪 ⇒ 性能与容量问题难定位。
  Required Follow-up     : 日志字段规范（含敏感信息过滤）。

OPTION B — 日志 + 指标
  Description            : 增加指标端点与采集。
  Impact                 : 需定义指标集与采集方式。
  Pros                   : 可观测性提升。
  Risks                  : 需新增运行组件或端点。
  Required Follow-up     : 指标清单 · 采集与存储方案。

OPTION C — 日志 + 指标 + 追踪
  Description            : 全量可观测性。
  Impact                 : 引入追踪基础设施与上下文传播。
  Pros                   : 深度诊断能力。
  Risks                  : 复杂度与成本最高；追踪上下文需贯通各层。
  Required Follow-up     : 追踪方案 · 采样策略 · 隐私过滤。
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

Human Notes:

```

---

# Sheet 状态

```text
Decision filled = 0 / 15（本轮仅生成载体，不执行 Decision）
Batch 0 Governance Meta      : ADD-2 · ADD-1
Batch 1 Security Root        : OQ-P14-13 · OQ-P14-12
Batch 2 Identity Foundation  : OQ-P14-01 · OQ-P14-02 · OQ-P14-03
Batch 3 Authorization Runtime: OQ-P14-04 · OQ-P14-05
Batch 4 Runtime Interface    : OQ-P14-06 · OQ-P14-07 · OQ-P14-09
Batch 5 Operations           : OQ-P14-10 · OQ-P14-08 · OQ-P14-11
```

```text
本轮工程变更：DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · commit/tag/push = 0
本 Sheet 不出现任何倾向性结论措辞。
P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 HUMAN DECISION SHEET（2026-09-27 · 15 项待裁 · Decision filled = 0 · PENDING）**
