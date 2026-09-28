# UAP — P14 PRIVILEGE / SECURITY HUMAN DECISION SHEET

> ## Metadata
>
> ```text
> Stage                     = P14_RUNTIME_SLICE
> Baseline                  = HEAD c420403d5469241e8b03855428ebce435d539c9e · migration 0017_p13_seed
>                             DB = 0017_p13_seed · 0018+ = 0
> Decision status           = **HUMAN DECISION RESOLVED**（14 / 14 resolved · 2026-09-27）
>                             权威裁决记录见文末 **Resolution Registry**；
>                             上文各条目的候选方案与勾选框**保留为历史候选**（未删除），其未勾选状态不代表未裁决
> Security Gate             = DECISION READY（非 SECURITY APPROVED）
> Implementation Preflight  = READY
> P14 IMPLEMENTATION        = **NOT AUTHORIZED**
> HARD STOP                 = ACTIVE
> Decision count            = 14（SEC-P14-01 … SEC-P14-14）
> 模型命名口径               = 本 Sheet 采用：MODEL A = directly expand uap_app ·
>                             MODEL B = trusted internal boundary ·
>                             MODEL C = dedicated runtime principal
>                            （注：前轮 PREFLIGHT 报告曾用 B = dedicated principal / C = service boundary + principal；
>                             本 Sheet 的命名以本指令为准，二者对应关系见各条目说明）
> ```

---

# 0. Security Decision Consistency Audit（只读实测 · 2026-09-27）

```text
Principal facts
  roles                 = ['uap', 'uap_app', 'uap_migrator', 'uap_seed']（4 个非内建角色）
  uap_app 表级授权       = alembic_version:SELECT · audit_logs:INSERT,SELECT ·
                          audit_logs_202609:INSERT,SELECT（共 5 项）
  uap_app CREATE=public  = False · USAGE = True
  uap_migrator          = CREATE=False · rolsuper=False（migration-only）
  user-defined membership = 0 · pg_default_acl = 0
  C2 md5                = 185e95be8bc4304edbcd3f4d5cda1eff（CC-7 变体 · 未变）

Contract 冻结原文（§12）
  PB-1  uap_app = 保持当前最小权限（5 项 + schema USAGE · CREATE = false）
  PB-2  不授予宽泛 DB 写权限
  PB-3  Runtime 不使用 uap_migrator
  PB-4  Runtime 使用独立 runtime / trusted service principal（形态属独立 Gate）
  PB-5  新 DB role / GRANT / privilege 不并入本轮 Runtime implementation
  PB-6  新 privilege 必须另开 Privilege / Security Gate
  TR-1  uap_app ≠ uap_migrator · TR-2 runtime ≠ migration trust · TR-3 new GRANT/role ≠ implicit implementation

UNKNOWN 相关对象现状（行数）
  tenants 0 · spaces 0 · tenant_memberships 0 · memberships 0 · platform_memberships 0 ·
  platform_state 1(uninitialized) · events 0 · resources 0 · resource_permissions 0 ·
  credentials 0 · devices 0 · sessions 0 · users 0 · identities 0 · audit_logs 0

审计结论：与 PREFLIGHT 报告一致；无漂移。MODEL A 与 PB-1/PB-2 的冲突为**客观存在**（见 SEC-P14-01）。
```

---

# SEC-P14-01 — Runtime Principal Model

```text
Question        : Runtime 采用哪种 principal 模型？
Existing Facts  : 现无 runtime 专用 principal；uap_app 仅 5 项授权（连授权判定所需 SELECT 都没有）。
Frozen Constraints : Contract §12 PB-1…PB-6 · TR-1…TR-3 · OQ-P14-13 = OPTION B
                    （Trusted Internal Service Boundary）· D-OP101-07（未获新决策前不得扩权）
Affected        : 全部后续 SEC 决策 · Privilege Matrix · Contract §12 表述
Dependency      : 根决策（阻塞 SEC-02…14）
```

```text
Options

A. directly expand uap_app
   Impact          : uap_app 授权面从 5 项扩至 ~26 项（含身份/凭据/会话写）
   Pros            : 实现最简；无需新 principal
   Risks           : 风险集中；与最小权限原则张力最大
   Compatibility   : ⚠ **CONTRACT CONFLICT** —— 直接违反 Contract §12 **PB-1**（uap_app 保持当前最小权限）
                     与 **PB-2**（不授予宽泛 DB 写权限）；且与 OQ-P14-13 = OPTION B 方向相反
   Follow-up       : 若选 A，必须**显式重述** PB-1/PB-2（或以新 Decision supersede）——不得以措辞弱化

B. trusted internal boundary（复用已有 principal）
   Impact          : 采用受信内部边界承载写路径，但边界身份**复用现有角色**
   Pros            : 不新增角色；边界集中
   Risks           : 复用对象须逐一评估：
                     · 复用 uap_app ⇒ 等价于 A（**CONTRACT CONFLICT**，违反 PB-1）
                     · 复用 uap_seed ⇒ 与 RM-D 中 uap_seed「仅 registry seed 受信 context」的
                       既有语义冲突（需 Human 重述该角色用途）
                     · 复用 uap_migrator ⇒ **CONTRACT CONFLICT**（违反 PB-3 / TR-1 / TR-2）
   Compatibility   : 取决于复用对象；除 uap_seed（需重述）外，其余均与 PB 冲突
   Follow-up       : 明确复用哪个 principal，并同步处理对应重述

C. dedicated runtime principal
   Impact          : 新建专用 runtime 角色（或等价受信主体），按最小集授权
   Pros            : 身份可区分、可独立轮换、审计清晰；**与 PB-4 直接一致**
   Risks           : 需新增角色与凭据（属独立 Gate · PB-5/PB-6）
   Compatibility   : ✅ 与 PB-4 / PB-6 兼容；新角色创建属独立授权轮
   Follow-up       : 若选 C，须进一步决定：
                     · principal 命名规范
                     · 是否单独 credential
                     · 是否单独 rotation
                     · 是否单独 revoke
                     · 是否允许多个 Runtime process 共用
                     · 是否允许未来模块复用

D. 其他明确模型（Human 自定义）
```

```text
Human Decision:
  [ ] OPTION A（若选：须同时说明 PB-1/PB-2 的重述方式）
  [ ] OPTION B（若选：须指明复用哪个 principal）
  [ ] OPTION C（若选：须回答上述 6 个 follow-up）
  [ ] CUSTOM

Human Notes:

```

---

# SEC-P14-02 — Runtime Principal Trust Boundary

```text
Question        : Runtime principal 属于哪一类信任边界？
                   （Runtime execution / Migration·Seed·Administrative / Internal Service Boundary）
Existing Facts  : 现有三类身份：uap（deployment-ops）· uap_seed（seed）· uap_migrator（migration）
                  · uap_app（runtime 现状）。
Frozen Constraints : TR-1/TR-2（身份不得混用）· PB-3（Runtime 不使用 uap_migrator）
Affected        : Contract §2 Security Boundary · §12 · Privilege Matrix §4/§5
Dependency      : SEC-P14-01
```

```text
需明确回答：
  ① Runtime principal 归属（三选一或 CUSTOM）
  ② **uap_migrator 是否永远不进入 Runtime execution path**（要求 Yes/No + 理由）
  ③ Runtime principal 是否允许持有任何 migration-only 能力（要求 Yes/No）

Available Options
  A. Runtime execution
  B. Migration / Seed / Administrative（除 uap_migrator 外的受信管理身份）
  C. Internal Service Boundary
  D. CUSTOM
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

② uap_migrator 永不进入 Runtime path : [ ] 是   [ ] 否（若否，须说明）
③ Runtime principal 可持 migration-only 能力 : [ ] 否   [ ] 是（若是，须说明）

Human Notes:

```

---

# SEC-P14-03 — Runtime Required Read Scope

```text
Question        : Runtime 允许读取哪些对象？（逐项裁决；**所有 UNKNOWN 必须清零**）
Existing Facts  : uap_app 对下列全部对象当前**零 SELECT**（除 audit_logs / alembic_version）。
Frozen Constraints : Contract §6 AC-1/AC-4（判定需数据）· 最小权限（unknown = DENY）
Affected        : Privilege Matrix §2 · Acceptance PRV-1
Dependency      : SEC-P14-01 · 影响 SEC-P14-10
```

```text
逐项裁决（Human 在每行选择一个；默认安全位 = NOT REQUIRED）

对象                   REQUIRED   NOT REQUIRED   UNKNOWN
tenants                   [ ]         [ ]          [ ]
spaces                    [ ]         [ ]          [ ]
memberships               [ ]         [ ]          [ ]
users                     [ ]         [ ]          [ ]
identities                [ ]         [ ]          [ ]
devices                   [ ]         [ ]          [ ]
sessions                  [ ]         [ ]          [ ]
roles                     [ ]         [ ]          [ ]
permissions               [ ]         [ ]          [ ]
role_permissions          [ ]         [ ]          [ ]
acl_subject_types         [ ]         [ ]          [ ]
resource_permissions      [ ]         [ ]          [ ]
agents                    [ ]         [ ]          [ ]
agent_versions            [ ]         [ ]          [ ]
agent_permissions         [ ]         [ ]          [ ]
tools                     [ ]         [ ]          [ ]
platform_state            [ ]         [ ]          [ ]
platform_memberships      [ ]         [ ]          [ ]
audit_logs                [ ]         [ ]          [ ]

要求：UNKNOWN 列在裁决后必须为空（全项二选一）。
```

```text
Human Notes:

```

---

# SEC-P14-04 — Runtime Required Write Scope

```text
Question        : Runtime 允许哪些写操作？（必须严格区分 INSERT / UPDATE / DELETE）
Existing Facts  : uap_app 对下列对象当前**零写权限**。
Frozen Constraints : Contract §3/§4/§5/§6/§8 · platform-controlled 默认禁写
Affected        : Privilege Matrix §2/§3 · Acceptance PRV-1 / DOWNG 类判据
Dependency      : SEC-P14-01 · SEC-P14-02
```

```text
逐项裁决（每行分别勾选动作；未勾选 = DENY）

操作                       INSERT   UPDATE   DELETE
onboarding identity          [ ]      [ ]      [ ]
device enrollment            [ ]      [ ]      [ ]
session creation             [ ]      [ ]      [ ]
membership change            [ ]      [ ]      [ ]
agent-related write          [ ]      [ ]      [ ]
tool execution write         [ ]      [ ]      [ ]
audit write                  [ ]      [ ]      [ ]
resource write               [ ]      [ ]      [ ]
resource_permission write    [ ]      [ ]      [ ]
platform membership write    [ ]      [ ]      [ ]
platform state write         [ ]      [ ]      [ ]

说明：不得以「可写」笼统授权；每个动作须独立裁定（见 SEC-P14-09 / 13 的专门条目）。
```

```text
Human Notes:

```

---

# SEC-P14-05 — Tenants / Spaces Access

```text
Question        : Runtime 对 tenants / spaces 的访问范围？
Existing Facts  : 两表均 0 行；uap_app 零权限；P13 决策（D-P13-05/08）把 tenant/space 建立留给
                  onboarding/runtime，但**未定义** Runtime 的具体权限面。
Frozen Constraints : D-P13-05（P13 不建 bootstrap tenant）· D-P13-08（P13 不建 membership）·
                    Contract「Runtime 不新增 schema」
Affected        : Privilege Matrix（tenants/spaces 行）· Scope §2.3 · Acceptance AUT/IDF 类
Dependency      : SEC-P14-01 · SEC-P14-06
```

```text
需明确回答：
  ① Runtime 是否直接读取           [ ] 是  [ ] 否
  ② Runtime 是否允许创建           [ ] 是  [ ] 否
  ③ Runtime 是否允许更新           [ ] 是  [ ] 否
  ④ Runtime 是否允许删除           [ ] 是  [ ] 否
  ⑤ 哪一个 service / use-case 可以访问（请填写）
  ⑥ 是否必须通过 service abstraction  [ ] 是  [ ] 否
  ⑦ 是否允许跨 tenant 查询           [ ] 是（须说明范围） [ ] 否

默认安全要求：任何未明确授权的跨 tenant 行为均**不得成立**。
```

```text
Human Notes:

```

---

# SEC-P14-06 — Memberships Access

```text
Question        : memberships（租户/空间级）与 platform_memberships（平台级）分别由谁改写？
Existing Facts  : memberships / tenant_memberships / platform_memberships 均 0 行；
                  platform_state = uninitialized（bootstrap 未执行）。
Frozen Constraints : D-P13-07（P13 零 PM 写入 · 首个平台管理员由 bootstrap CLI 产生）·
                    R4/R5（bootstrap 原子流程 + 无恢复 API）· D-P13-08（P13 不建 membership）
Affected        : Privilege Matrix · Bootstrap（SEC-P14-11/13）· Acceptance AUT/PRV 类
Dependency      : SEC-P14-01 · 阻塞 SEC-P14-13
```

```text
需明确回答（两部分**分别**裁决，不得合并）：

A. memberships / tenant_memberships（租户·空间级）
  ① membership 是否由 Runtime 修改                     [ ] 是  [ ] 否
  ② 谁负责 membership creation                          （请填写）
  ③ 谁负责 membership revoke                            （请填写）
  ④ Runtime 是否仅能读取**当前 actor 的** membership     [ ] 是  [ ] 否
  ⑤ 是否要求特定 use-case 才能触发                       [ ] 是  [ ] 否

B. platform_memberships（平台级）
  ⑥ 是否允许 platform-level membership 变更由 Runtime 执行 [ ] 是  [ ] 否
  ⑦ 若否，由谁执行（bootstrap path / operator / 其他）      （请填写）
```

```text
Human Notes:

```

---

# SEC-P14-07 — Events / Resources Access

```text
Question        : events 与 resources 分别如何裁决？（必须**拆开**裁决）
Existing Facts  : events 0 行（P10 transactional outbox）· resources 0 行 · resource_permissions 0 行；
                  uap_app 对三者零权限。
Frozen Constraints : P10（events = outbox）· Contract §12 PB-2/PB-5 · 「避免为以后方便提前授权」
Affected        : Privilege Matrix（events/resources 行）· P14 Scope 边界
Dependency      : SEC-P14-01 · SEC-P14-09
```

```text
A. events
  ① Runtime SELECT  [ ] 是  [ ] 否      ② Runtime INSERT  [ ] 是  [ ] 否
  ③ Runtime UPDATE  [ ] 是  [ ] 否      ④ Runtime DELETE  [ ] 是  [ ] 否
  ⑤ 归属： normal runtime / administrative·bootstrap / 未来模块（P14 不实现）   （请选择）

B. resources
  ⑥ Runtime SELECT  [ ] 是  [ ] 否      ⑦ Runtime INSERT  [ ] 是  [ ] 否
  ⑧ Runtime UPDATE  [ ] 是  [ ] 否      ⑨ Runtime DELETE  [ ] 是  [ ] 否
  ⑩ 归属： normal runtime / administrative·bootstrap / 未来模块（P14 不实现）   （请选择）

要求：必须避免「为以后方便」提前授权。
```

```text
Human Notes:

```

---

# SEC-P14-08 — Credential Lifecycle

```text
Question        : credential 的生命周期权限如何裁决（尤其 DELETE）？
Existing Facts  : credentials 0 行；Security Gate 中 credential DELETE = UNKNOWN。
Frozen Constraints : OQ-P14-02（credential 隶属 identity · Argon2id hash · rotation · revoke ·
                    expire · 禁 plaintext · 禁 secrets 写日志）—— **核心语义不得改变**
Affected        : Privilege Matrix（credentials 行）· Contract §4 · Acceptance IDL-2/3 · SEC-4
Dependency      : SEC-P14-01
```

```text
需明确回答：
  ① credential 是否允许 DELETE                        [ ] 是  [ ] 否
  ② 是否应以 revoke / expire 替代 physical delete       [ ] 是  [ ] 否
  ③ rotation 是否以 UPDATE 实现                        [ ] 是  [ ] 否
  ④ credential metadata 是否与 identity 分离            [ ] 是  [ ] 否
  ⑤ 是否允许 Runtime 永久保存旧 credential              [ ] 是（须说明保留期）  [ ] 否
  ⑥ 是否允许 plaintext 出现在 logs / audit / exceptions [ ] 否（固定要求）  [ ] 是
```

```text
Human Notes:

```

---

# SEC-P14-09 — Resource Permission Write Side

```text
Question        : Runtime 是否可写 resource_permissions？
Existing Facts  : resource_permissions 0 行；Runtime 需读该表做 ACL 判定；
                  Security Gate 中写侧 = UNKNOWN。
Frozen Constraints : Contract §6 AC-3/AC-6 · 最小权限 · platform-controlled 精神
Affected        : Privilege Matrix（resource_permissions 行）· Acceptance AUT 类
Dependency      : SEC-P14-01 · SEC-P14-10
```

```text
需明确回答：
  ① Runtime 是否 INSERT    [ ] 是  [ ] 否
  ② Runtime 是否 UPDATE    [ ] 是  [ ] 否
  ③ Runtime 是否 DELETE    [ ] 是  [ ] 否
  ④ 是否允许 Runtime 改变**自身** authorization scope  [ ] 是（**须特别说明风险接受**） [ ] 否
  ⑤ 是否必须由更高权限 administration / service boundary 执行 [ ] 是  [ ] 否
  ⑥ Runtime 是否**只读不写**（安全默认位）               [ ] 是  [ ] 否

重点：privilege escalation 风险。**不得因需要读取授权信息而默认允许修改授权信息。**
```

```text
Human Notes:

```

---

# SEC-P14-10 — Authorization Read Path

```text
Question        : Runtime 的授权判定数据来自哪里？
Existing Facts  : 需读 roles / permissions / role_permissions / acl_subject_types /
                  resource_permissions；uap_app 对上述全部零 SELECT；
                  Contract §6 AC-1 已定 centralized precheck + service/use-case enforcement。
Frozen Constraints : Contract §6 AC-1…AC-6 · §7 SC-1/SC-2（handler 不直接 SQL）· D-AUTH-16
Affected        : Privilege Matrix 读侧 · Contract §6/§7 实施路径 · Acceptance AUT-4
Dependency      : SEC-P14-01 · SEC-P14-03
```

```text
Available Options

A. 直接读取 PostgreSQL authorization tables（各 handler/service 自行 SELECT）
   Compatibility : 与 Contract §7 SC-1（handler 不直接 SQL）**张力**——若在 service 层读则相容；
                   但"不同 handler 自行决定是否 SELECT"明确不被允许（见条目末句）
B. 通过 dedicated authorization service / use-case（统一入口）
   Compatibility : 与 AC-1 / SC-2 一致；读权限集中在 authorization service
C. hybrid：service 统一入口 + restricted DB read
   Compatibility : 与 AC-1 一致；需明确"restricted"的边界与最小读集
D. CUSTOM

硬性要求（无论选哪个）：**不得让不同 handler 自行决定是否 SELECT 授权表**。
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

# SEC-P14-11 — Bootstrap Execution Identity

```text
Question        : bootstrap CLI 以什么 principal 执行？
Existing Facts  : bootstrap 需写 platform_memberships（首行）+ platform_state（翻转）+ audit_logs；
                  uap_app 对前两者零权限；platform_state 现为 uninitialized。
Frozen Constraints : R4/R5（一次性 · 原子 · 无恢复 API）· D-P13-07 · Contract §8 BR-1…BR-7 ·
                    PB-3（Runtime 不使用 uap_migrator）
Affected        : Privilege Matrix · Bootstrap 安全 · Acceptance OPS-3 / AUD-3
Dependency      : SEC-P14-01 · SEC-P14-02 · 阻塞 SEC-P14-13
```

```text
Available Options

A. uap_migrator
   Compatibility : ⚠ **CONTRACT CONFLICT** —— 与 PB-3（Runtime 不使用 uap_migrator）张力；
                   且 uap_migrator 语义为 migration execution identity，非 bootstrap 身份
B. uap_seed
   Compatibility : ⚠ 与其 RM-D 语义（"仅 registry seed 的受信 context"）张力；
                   若要采用，须 Human 显式重述该角色用途
C. dedicated bootstrap / admin principal
   Compatibility : ✅ 与 PB-4 精神一致（独立受信主体）；新角色属独立 Gate
D. 其他方案（CUSTOM）

需同时说明：
  · bootstrap 是一次性 privileged operation
  · bootstrap principal 是否允许进入正常 Runtime path
  · 是否长期存在
  · 是否需要单独 credential
  · bootstrap 后是否撤销 / 禁用
  · 是否能够修改 platform_memberships
  · 是否能够修改 platform_state
```

```text
Human Decision:
  [ ] OPTION A
  [ ] OPTION B
  [ ] OPTION C
  [ ] CUSTOM

上述 7 项说明（请逐条填写）：

```

---

# SEC-P14-12 — Bootstrap Credential Source

```text
Question        : bootstrap CLI 的凭据从哪里获得？
Existing Facts  : 当前无任何 bootstrap 凭据机制；DB 侧 pg_default_acl = 0；
                  安全基线要求 no plaintext secrets / no secrets in logs。
Frozen Constraints : OQ-P14-02（禁 plaintext · 禁 secrets 写日志）· 安全基线
Affected        : Bootstrap 流程 · 运维手册（C-10）· Acceptance SEC-4 / AUDX-5
Dependency      : SEC-P14-11
```

```text
需明确回答：
  ① CLI credential 来源                       （请填写）
  ② 是否支持 environment variable              [ ] 是  [ ] 否
  ③ 是否支持 local secret file                 [ ] 是  [ ] 否
  ④ 是否允许 interactive prompt                 [ ] 是  [ ] 否
  ⑤ 是否允许 hard-coded secret                  [ ] 否（固定要求）  [ ] 是（须说明风险接受）
  ⑥ 是否允许记录到 shell history / logs          [ ] 否（固定要求）  [ ] 是
  ⑦ 是否需要 one-time bootstrap token           [ ] 是  [ ] 否
  ⑧ bootstrap 完成后该 credential 是否失效       [ ] 是  [ ] 否
```

```text
Human Notes:

```

---

# SEC-P14-13 — platform_memberships / platform_state Bootstrap Authority

```text
Question        : platform_memberships 与 platform_state 由谁**原子**写入？
Existing Facts  : 两表分别 0 行 / uninitialized；R4/R5 规定原子流程；
                  tg_pm_bootstrap_gate / tg_pm_last_admin 强制保护。
Frozen Constraints : R4/R5（FROZEN）· D-P13-07 · Contract §8 BR-7
Affected        : Bootstrap authority · Acceptance OPS-3 · Privilege Matrix
Dependency      : SEC-P14-11 · SEC-P14-12
```

```text
需明确回答：
  ① normal Runtime 不得默认获得该权限                     [ ] 同意（固定要求）
  ② bootstrap path 是否**独占**该能力                      [ ] 是  [ ] 否
  ③ 是否允许再次 bootstrap                                [ ] 否（固定要求）  [ ] 是
  ④ one-time state lock 如何体现（请说明具体判据）
  ⑤ bootstrap 完成后 Runtime 能否**读取** platform_state / platform_memberships
                                                          [ ] 是  [ ] 否
  ⑥ Runtime 能否**修改**上述两表                            [ ] 否（默认安全位）  [ ] 是（须说明）
```

```text
Human Notes:

```

---

# SEC-P14-14 — Privilege Granting Strategy

```text
Question        : 未来授权采用什么策略？
Existing Facts  : 当前无 default ACL；既有授权为逐表显式授予；无序列；无函数 EXECUTE 授予 runtime。
Frozen Constraints : D-OP101-07（minimum required set）· D-OP101-08（runtime 不持 DDL）·
                    PB-2（不授予宽泛写）· 最小权限原则
Affected        : 未来授权执行轮 · Privilege Matrix 的落地形态 · Acceptance PRV-1/2/4
Dependency      : SEC-P14-01…13 全部
```

```text
可选策略（可多选组合，但须明确最终形态）
  [ ] schema-level access        （注意：仅 USAGE；禁止 schema-level write）
  [ ] table-level exact grants   （逐表逐动词）
  [ ] column-level grants        （按列最小化）
  [ ] sequence-level grants      （本项目当前无序列）
  [ ] function EXECUTE           （若采用受信函数路径）
  [ ] view-based restricted access（以视图暴露受限读面）
  [ ] service-mediated access    （经受信服务边界访问，DB 权限最小）

硬性要求：
  · least privilege
  · NO BROAD GRANT
  · **禁止 GRANT ALL** 或任何等效宽泛授权作为 Runtime 快速闭合方案
```

```text
Human Notes:

```

---

# 附：UNKNOWN 覆盖与 Bootstrap 覆盖核对

```text
UNKNOWN 来源（前轮 Security Gate）→ 对应 Decision
  tenants / spaces / tenant_memberships / memberships   → SEC-P14-03 · 05 · 06
  events                                                → SEC-P14-07
  resources                                             → SEC-P14-07
  resource_permissions 写侧                              → SEC-P14-09
  credential DELETE                                     → SEC-P14-08
  bootstrap execution identity                          → SEC-P14-11
  bootstrap credential source                            → SEC-P14-12
  platform_memberships / platform_state authority        → SEC-P14-13
⇒ 覆盖 = 完整（无 UNKNOWN 遗漏）

Bootstrap 空白 → 对应 Decision
  执行身份 → SEC-P14-11 · 凭据来源 → SEC-P14-12 · 授权边界 → SEC-P14-13 · 授权策略 → SEC-P14-14
⇒ 覆盖 = 完整
```

---

# 状态

```text
Decision filled = 0 / 14（本轮仅生成载体）
P14 IMPLEMENTATION = NOT AUTHORIZED · HARD STOP = ACTIVE
本轮：CREATE ROLE / ALTER ROLE / GRANT / REVOKE / DDL / DML / migration / runtime code = 0
本 Sheet 不出现任何倾向性结论措辞（不标注任一选项更优 / 更强 / 更易实现）。
```

---

# RESOLUTION REGISTRY（HUMAN DECISION RESOLVED · 2026-09-27）

> **本 Registry 为权威裁决记录**。上文 §SEC-P14-01…14 的候选方案与勾选框保留为**历史候选证据**
> （依"不得删除历史候选方案"），未勾选状态**不代表未裁决**；一切以后本 Registry 为准。
> 本轮不执行任何 GRANT / CREATE ROLE / DDL / DML / runtime code。

---

## SEC-P14-01 — Runtime Principal Model

```text
selected option        : **OPTION C — DEDICATED RUNTIME PRINCIPAL**
resolution             : Runtime **不复用** uap_app / uap_migrator / uap_seed；
                         新建 dedicated runtime principal
rationale              : 身份可区分 · 生命周期独立 · 与 OQ-P14-13 = OPTION B（Trusted Internal
                         Service Boundary）配套；避免扩大 uap_app 造成风险集中
affected boundary      : Runtime execution trust domain
implementation consequence : 后续 Security Implementation Gate 需创建该 principal 与其凭据
related frozen decision : Contract §12 PB-1 / PB-2 / PB-3 / PB-4 · OQ-P14-13 = OPTION B ·
                         D-OP101-07 / D-OP101-08 · TR-1 / TR-2 / TR-3
contract amendment     : **NO**（与 PB-4「独立 runtime / trusted service principal」方向一致，
                         属其具体化）；须建立 MODEL C 命名对应关系（见下"命名对应"）
登记要点               : · uap_app 继续保持当前最小权限
                         · 不通过扩大 uap_app 直接闭合 Runtime 权限缺口
                         · uap_migrator 不进入 Runtime execution path
                         · uap_seed 不承担 Runtime principal 角色
                         · Runtime principal 属 Runtime execution trust domain
                         · privilege lifecycle 与 migration / seed lifecycle 分离
                         · credential rotation / revoke / lifecycle 独立
```

## SEC-P14-02 — Runtime Trust Boundary

```text
selected option        : **TRUSTED INTERNAL SERVICE BOUNDARY**
resolution             : Runtime principal 即该受信内部 Service Boundary 的**数据库身份**
rationale              : 与 OQ-P14-13 = OPTION B 直接对应；使写路径集中、可审计
affected boundary      : Runtime ↔ DB 的信任边界
implementation consequence : 服务层经该 principal 访问 DB；迁移/种子/引导身份各自独立
related frozen decision : Contract §2 SB-1/SB-2/SB-3 · §12 PB-3/PB-4 · TR-1 / TR-2
contract amendment     : **NO**
登记要点               : · Runtime service → dedicated runtime principal
                         · migration → uap_migrator
                         · seed → uap_seed
                         · bootstrap → dedicated one-time bootstrap authority
                         · uap_app 不因 Runtime 缺口而扩权
                         · Runtime 不模拟 / 不继承 / 不绕过 C2 / CC-7
                         · C2 / CC-7 继续保持 migration trust semantics
                         · 不得使用 GUC / application_name 等方式伪造信任身份
```

## SEC-P14-03 — Runtime Required Read Scope

```text
selected option        : **explicit required-read allowlist**
resolution             : 仅 P14 Runtime use-case 实际需要的对象可进入 REQUIRED
rationale              : 最小权限 + 避免"未来可能用到"式提前授权
affected boundary      : 读面（Runtime → DB）
implementation consequence : 矩阵须把每对象重算为 REQUIRED / NOT REQUIRED / DENY
related frozen decision : Contract §6 AC-1/AC-4 · §12 PB-2/PB-7
contract amendment     : **NO**（属矩阵更新）
登记要点               : 逐项覆盖 tenant/space context · membership · user/identity ·
                         device/session · roles/permissions/role_permissions ·
                         acl_subject_types · resource_permissions · agents 族 · tools ·
                         events/resources · platform state 读取
                         ⇒ **无明确 Required 证据 ⇒ UNKNOWN → DENY**；
                           Security Gate 意义上的 UNKNOWN 必须清零
```

## SEC-P14-04 — Runtime Required Write Scope

```text
selected option        : **use-case + operation 精确授予**
resolution             : 写权限按 use-case 与具体操作（SELECT / INSERT / UPDATE / DELETE）授予
rationale              : 禁止模糊"可写"；避免 broad CRUD
affected boundary      : 写面（Runtime → DB）
implementation consequence : 矩阵须逐对象标注四类动词归属；未明确 = DENY
related frozen decision : Contract §3/§4/§5/§6/§8 · §12 PB-2
contract amendment     : **NO**
登记要点               : 可进入正常 Runtime write path 的类别 = identity onboarding ·
                         device enrollment · session lifecycle ·
                         经 authorization service 允许的 membership mutation ·
                         正常 Runtime 所需 business records · tool execution · audit write
                         禁止：broad CRUD · all-table write
```

## SEC-P14-05 — Tenants / Spaces

```text
selected option        : **RUNTIME = SELECT ONLY**
resolution             : Runtime 只读当前 use-case 必需的 tenant / space context
rationale              : tenant/space administration 不属普通 Runtime authority
affected boundary      : 租户/空间数据面
implementation consequence : 矩阵 tenants/spaces 行 = SELECT only；写侧一律 DENY
related frozen decision : D-P13-05（P13 不建 bootstrap tenant）· Contract §12
contract amendment     : **CANDIDATE**（Scope §2.3 / §6 可细化归属表述）
登记要点               : 不负责 tenant creation / deletion / 任意 tenant·space mutation ·
                         不允许跨 tenant 任意扫描
```

## SEC-P14-06 — Memberships

```text
selected option        : 普通 memberships 进入**受控 runtime use-case**（Service / Use-case mediated）
resolution             : 不得 handler direct SQL；不得把 membership 权限等价为 platform administration
rationale              : 业务成员关系与平台管理权限职责不同
affected boundary      : 成员关系面
implementation consequence : membership 变更须经 use-case；platform_memberships 另属 Bootstrap 边界
related frozen decision : D-P13-07 / R4 / R5 · Contract §3/§5
contract amendment     : **NO**
登记要点               : 严格区分 tenant memberships 与 platform_memberships；
                         platform_memberships 属 Bootstrap / platform authority 边界
```

## SEC-P14-07 — Events / Resources

```text
selected option        : **最小操作集合**（正常 Runtime data path）
resolution             : SELECT / INSERT / UPDATE 允许（仅实际 use-case）；**DELETE = DENY**
rationale              : 硬删除需独立 Security Review；不以"未来可能需要"为由授权
affected boundary      : 事件与资源数据面
implementation consequence : 矩阵 events/resources 行 = S/I/U（use-case 限定）· DELETE DENY
related frozen decision : P10（events = transactional outbox）· Contract §12
contract amendment     : **CANDIDATE**（Scope 可细化 events/resources 归属）
登记要点               : 仅当存在明确、经独立 Security Review 的硬删除需求时，才允许追加 DELETE
```

## SEC-P14-08 — Credential Lifecycle

```text
selected option        : **NO PHYSICAL DELETE**
resolution             : lifecycle = issue → active → rotate → revoke/expire
rationale              : 保留可审计轨迹；避免凭据被物理销毁导致审计断裂
affected boundary      : 凭据面
implementation consequence : 矩阵 credentials 行 DELETE = DENY；rotation/revoke/expire 走 UPDATE
related frozen decision : **OQ-P14-02 核心语义不得改变**（Argon2id hash · 禁 plaintext ·
                         禁 secrets 写日志 · rotation/revoke/expire）
contract amendment     : **CANDIDATE**（Contract §4 可补充 "no physical delete" 表述）
登记要点               : 允许 = 必要 credential metadata 更新 · rotation · revoke · expire
                         禁止 = plaintext storage · plaintext logging · secret 出现在
                         audit payload / exception / 普通 operational log
```

## SEC-P14-09 — Resource Permission Write Side

```text
selected option        : **RUNTIME WRITE = DENY**
resolution             : Runtime 不允许经自身 Runtime path 修改 resource_permissions
rationale              : Runtime 不得拥有改变自身或当前 actor authorization boundary 的能力
affected boundary      : 授权模型面
implementation consequence : 矩阵 resource_permissions 行写侧 = DENY；读侧保留（依 SEC-03）
related frozen decision : Contract §6 AC-3/AC-6 · §12
contract amendment     : **NO**
登记要点               : 授权模型 mutation 属更高权限 administration / security boundary；
                         不得建立 Runtime → resource_permissions write → self-escalation 闭环
```

## SEC-P14-10 — Authorization Read Path

```text
selected option        : **HYBRID** —— Central Authorization Service / Use-case
                         + Restricted Runtime DB Read
resolution             : 集中式 precheck；service/use-case 为 mandatory enforcement point；
                         DB read 仅提供授权 service 所需最小数据
rationale              : 与 Contract §6 AC-1 / §7 SC-2 一致；避免授权读取散落
affected boundary      : 授权判定面
implementation consequence : authorization service 统一入口；读取路径集中
related frozen decision : Contract §6 AC-1…AC-5 · §7 SC-1/SC-2 · D-AUTH-07 / D-AUTH-12 /
                         D-AUTH-16
contract amendment     : **CANDIDATE**（Contract §6 可追加 HYBRID 细节细化）
登记要点               : · precheck centralized · service/use-case mandatory enforcement
                         · handler 不自行决定授权 · handler 不散落直接读取 authorization tables
                         · DB read 最小集 · default deny · deny precedence
                         · ABAC 语义保持既有 P14 Decision · **DB RLS 不作为 P14 primary model**
```

## SEC-P14-11 — Bootstrap Execution Identity

```text
selected option        : **DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL**
resolution             : bootstrap 使用专用一次性引导身份（非 uap_migrator / 非 runtime principal /
                         非 uap_app）
rationale              : Bootstrap Authority 与 Runtime Authority 必须分离
affected boundary      : 引导面
implementation consequence : 后续 Security Implementation Gate 才可创建（本轮不得 CREATE ROLE）
related frozen decision : R4 / R5 · D-P13-07 · Contract §8 · §12 PB-3
contract amendment     : **CANDIDATE**（Contract §8 / §13 需纳入执行身份）
登记要点               : · 不使用 uap_migrator / Runtime principal / uap_app
                         · 不将 bootstrap authority 暴露给 normal Runtime
                         · 仅用于受控本地 operator bootstrap
                         · bootstrap authority 生命周期与 Runtime principal 分离
                         · 若需新增 PostgreSQL role ⇒ 只能在后续独立 Security Implementation Gate
                           经授权后实施；**本轮不得 CREATE ROLE**
```

## SEC-P14-12 — Bootstrap Credential Source

```text
selected option        : 默认 **LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT**
                         （受控部署环境允许 LOCAL SECRET FILE / CONTAINER SECRET）
resolution             : 凭据不入 CLI 参数、不入源码、不落明文持久化、不进 shell history / 日志 / 审计
rationale              : 与"no plaintext secrets / no secrets in logs"一致
affected boundary      : 引导凭据面
implementation consequence : 凭据输入通道与生命周期受 bootstrap boundary 控制
related frozen decision : OQ-P14-02（禁 plaintext / 禁 secrets 写日志）· 安全基线
contract amendment     : **CANDIDATE**（Contract §8 / §13 需纳入凭据来源）
登记要点               : 禁止 = CLI argument 携带 secret · 源码 hard-code ·
                         plaintext persistent storage · shell history 暴露 ·
                         operational log 暴露 · audit log 暴露
                         bootstrap credential 在完成 one-time bootstrap 后
                         **不得自动成为正常 Runtime credential**
```

## SEC-P14-13 — platform_memberships / platform_state

```text
selected option        : **BOOTSTRAP-OWNED INITIALIZATION**
resolution             : 两表由 dedicated bootstrap authority **原子初始化**
rationale              : 维持 R4/R5 的一次性语义与状态锁
affected boundary      : 平台初始化面
implementation consequence : normal Runtime 仅可读（依 SEC-03 的 use-case 限定）；写侧 DENY
related frozen decision : R4 / R5（FROZEN）· D-P13-07 · Contract §8 BR-7
contract amendment     : **CANDIDATE**（Contract §8/§13 需纳入所有权表述）
登记要点               : · normal Runtime 可读取后续 use-case 必需状态
                         · 不得重新执行 bootstrap · 不得修改 bootstrap-owned initialization state
                         · 不得绕过 one-time state lock
                         · **Bootstrap Authority ≠ Runtime Authority**
```

## SEC-P14-14 — Privilege Granting Strategy

```text
selected option        : **EXACT LEAST-PRIVILEGE GRANT STRATEGY**
resolution             : 逐对象 + 逐操作精确授权；默认 DENY；禁一切宽泛授权
rationale              : 最小权限原则；避免 privilege shortcut 闭合缺口
affected boundary      : 未来授权执行轮
implementation consequence : 授权动作须在**独立 Security Implementation Gate** 实施
related frozen decision : D-OP101-07（minimum required set）· D-OP101-08（runtime 不持 DDL）·
                         Contract §12 PB-2 / PB-5 / PB-6
contract amendment     : **CANDIDATE**（未来授权轮与矩阵落地形态）
登记要点               : · exact table/object privilege · exact operation privilege
                         · 仅必要时授予 sequence · 仅必要时授予 function EXECUTE
                         · 仅必要时使用 restricted views · schema-level 仅保留必要 USAGE
                         · 默认 DENY · **不使用 GRANT ALL** · 不授予宽泛 schema write
                         · 不通过继承型权限间接扩大 Runtime authority
                         · 不使用 privilege shortcut 闭合当前缺口
```

---

## 命名对应（correspondence · 不产生第二套语义）

```text
本 Sheet 命名（依本指令）：
  MODEL A = directly expand uap_app
  MODEL B = trusted internal boundary
  MODEL C = dedicated runtime principal

历史文档命名（P14 PRIVILEGE / SECURITY GATE REPORT §8）：
  MODEL A = uap_app direct least-privilege runtime access   ≡ 本 Sheet MODEL A
  MODEL B = dedicated runtime principal                     ≡ 本 Sheet MODEL C
  MODEL C = service boundary + dedicated runtime principal  ≡ 本 Sheet MODEL B + C 的组合形态

⇒ 最终选定 = 本 Sheet MODEL C（dedicated runtime principal）
            + SEC-P14-02 的 TRUSTED INTERNAL SERVICE BOUNDARY 定位
  即：**独立 runtime principal 作为受信内部 Service Boundary 的数据库身份**
  二者为同一方案的两个侧面，不构成第二套语义。
```

## Registry 汇总

```text
resolved = 14 / 14 · unresolved = 0 · UNKNOWN 待清零项 = 0（由 SEC-03/04 的矩阵重算闭合）
bootstrap gap = 0（SEC-11 / 12 / 13 已闭合）
Contract conflict = 0 unresolved（原 MODEL A / B-reuse 的 CONTRACT CONFLICT 因选定 MODEL C 而避免）
Contract amendment = 0 必须 · 6 项 CANDIDATE（SEC-05 / 07 / 08 / 10 / 11 / 12 / 13 / 14 中部分）
implementation authorization leakage = 0（本轮未授权任何实施）
Security Decision = FROZEN · Security Implementation = NOT STARTED
P14 IMPLEMENTATION = NOT AUTHORIZED · HARD STOP = ACTIVE
```

---

**END OF P14 PRIVILEGE / SECURITY HUMAN DECISION SHEET（2026-09-27 · **HUMAN DECISION RESOLVED 14 / 14** · Resolution Registry 为权威记录 · Security Decision = FROZEN · 未执行任何实施）**
