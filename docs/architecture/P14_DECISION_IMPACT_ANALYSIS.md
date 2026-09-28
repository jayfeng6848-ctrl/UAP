# UAP — P14 DECISION IMPACT ANALYSIS

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — DECISION IMPACT ANALYSIS ROUND（Phase 2 + Phase 3 + Phase 4）
> 性质      = 只读分析；**不输出 winner**、**不替 Human 选择任何 OPTION**
> 基线      = HEAD c420403d… · tag UAP-V0.1.9-P13-SEED · migration 0017_p13_seed · stage P14_RUNTIME_SLICE
> 本轮未做   = 未创建 runtime code / API / CLI / migration / schema · 无 DDL / DML ·
>             未改 GRANT / REVOKE / default ACL · 未改冻结决策正文 · 未 commit/tag/push
> ```

---

# Part 1 — Phase 2：OQ-P14-13 深度展开

## 1.1 当期安全实况（本轮重新验证 · 只读）

```text
uap_app
  grants（显式 · non-owner）        = 恰 5 项：
                                       alembic_version:SELECT ·
                                       audit_logs:INSERT,SELECT · audit_logs_202609:INSERT,SELECT
  schema 特权                        = public USAGE（nspacl: uap_app=U）；CREATE = false
  default privileges / default ACL   = pg_default_acl = 0（无任何默认授权）
  table access（抽查 16 表）          = 15 张表 SELECT/INSERT/UPDATE/DELETE **全 False**；
                                       仅 audit_logs = [SELECT ✔, INSERT ✔, UPDATE ✘, DELETE ✘]、
                                       alembic_version = [SELECT ✔, 其余 ✘]
  trigger behavior                   = tg_acl_subject_types_protect（O）· tg_audit_immutable（O）·
                                       tg_pm_bootstrap_gate（O）—— 均启用
  ⇒ 判定：runtime 当前**连授权判定所需的 SELECT 都不具备**；写路径完全不存在。

uap_migrator
  privileges（显式 · non-owner）       = 245 行（对象自持导致 relacl 实体化）
  schema CREATE                        = false（窗口期已回收）
  ownership                            = public 下 156 个 pg_class 对象全为 owner
  rolsuper                             = false（NOSUPERUSER）
  migration-only 行为                  = 经 UAP_MIGRATION_DATABASE_URL 独占；env.py 角色断言
                                         FAIL-CLOSED；C2/CC-7 仅对 current_user = session_user =
                                         'uap_migrator' 放行 registry 写
```

## 1.2 OPTION 对比矩阵（**8 维度 · 无 winner**）

### OPTION A — Runtime direct database access

```text
形态：为 uap_app 按最小集逐表授予 SELECT/INSERT/UPDATE/DELETE；写路径由 runtime 自身执行。

1. Architecture impact
   分层不变（apps/agent/services/core/infrastructure 不变）；
   但 runtime 直接触库的面扩大 ⇒ 与「Agent 禁直连 DB」精神存在张力（Agent 仍经 Policy/Tool 契约，
   不受影响）；services/ 成为唯一持久化归属的约束不变。
2. Security impact
   uap_app 授权面由 5 项扩至数十项；runtime 被攻破即可直接写身份/授权/成员关系表 ⇒ 风险集中。
   需依赖既有 DB 层护栏（C2 / roles is_system / membership scope / audit immutable）兜底。
3. C2 / CC-7 compatibility
   兼容：不触碰 registry ⇒ 与 C2/CC-7 不冲突（前提 OQ-P14-12 = Runtime 不触碰 registry）。
4. D-OP101 compatibility
   与 D-OP101-07（minimum required set）字面一致，但其「未获新决策前不得扩权」要求
   ⇒ 必须由 Human 新决策授权；与 OI-G-1（不得扩权）**直接张力**（须先处理该登记）。
5. Future scalability
   简单直接；但随表数增长，授权面持续膨胀，逐表维护成本上升（OI-G-2 提示新分区需逐分区授权）。
6. Implementation complexity
   低（无新增组件/角色）；但"实际读写面"需先由 OQ-01/02/09 定义后才可核定 ⇒ 依赖链长。
7. Migration requirement
   **需要**新 migration 或等价授权动作（GRANT 面变更）⇒ 触及「Runtime 路线不创建 migration」的
   Excluded 边界 ⇒ 必须另立独立授权轮。
8. Need new decision count
   至少：① 批准扩权 + 逐表最小集清单；② OI-G-1 处置；③ 承载 GRANT 的 migration/授权轮授权；
   ④ 未来分区授权流程（OI-G-2）⇒ 约 4 项新决策。
```

### OPTION B — Trusted internal runtime service boundary

```text
形态：runtime 保持低权限；写路径经受信内部边界（专用组件 / 专用角色 / 受信服务）执行。

1. Architecture impact
   新增一个内部边界组件或角色 ⇒ 分层内新增成员；须明确其归属层（services? infrastructure?）
   与调用契约（可能触及 C-5 services 结构与 C-6 契约载体两项未决）。
2. Security impact
   runtime 直接权限面保持小 ⇒ 被攻破影响面小；但风险转移至受信边界自身
   （其凭据/权限成为新的关键资产）⇒ 需额外设计其鉴权与凭据托管。
3. C2 / CC-7 compatibility
   兼容（不触碰 registry），但若受信边界被设计为复用 uap_migrator，则等于把 migration 身份
   用于 runtime 路径 ⇒ 与「migration/runtime 身份分离」的意图张力显著。
4. D-OP101 compatibility
   若为新角色 ⇒ 仍需 GRANT（新决策）；若复用 uap_migrator ⇒ 需明确评估是否违反
   D-OP101-08 的意图（runtime 不持 DDL 的镜像问题：runtime 不得经旁路获得 migration 能力）。
5. Future scalability
   边界集中，便于后续统一扩展与审计；但新增组件带来运维与调试成本。
6. Implementation complexity
   中—高（新边界 + 鉴权 + 凭据托管 + 契约）。
7. Migration requirement
   取决于形态：新角色需 CREATE ROLE（deployment 动作）+ GRANT（migration 或编排窗口）
   ⇒ 很可能仍需独立授权轮。
8. Need new decision count
   至少：① 是否设立受信边界；② 其身份形态；③ 其权限集；④ 凭据托管方案；
   ⑤ 与 OI-G-1 / 角色拓扑的关系 ⇒ 约 5 项新决策。
```

### OPTION C — CLI / bootstrap controlled privileged path

```text
形态：runtime 不扩权（或仅补最小 SELECT）；所有写动作由受信 CLI 以既有 uap_migrator 执行。

1. Architecture impact
   分层不变；runtime 成为"只读 + 无写"的服务面 ⇒ 与既有 R4/R5「bootstrap 由受信 CLI」先例一致；
   但平台失去自助入网能力 ⇒ 与产品目标（multi-user / usable）张力明显。
2. Security impact
   最小权限面；runtime 被攻破无法写身份/授权表 ⇒ 风险最低。
   代价：CLI 成为高价值操作入口（需运维纪律与审计留证）。
3. C2 / CC-7 compatibility
   兼容（CLI 以 uap_migrator 执行，落在 CC-7 受信分支语义内；但不涉及 registry 变更）。
4. D-OP101 compatibility
   与 D-OP101-07 / OI-G-1 的最强解读一致（不扩权）；
   与 D-OP101-12（REVOKE + retain role）等治理面一致。
5. Future scalability
   规模化后人工成本线性增长；若未来要开放注册，仍需另立决策（非终局形态）。
6. Implementation complexity
   低—中（CLI + 运维流程；无需新授权面）。
7. Migration requirement
   若 runtime 仅需**读权限** ⇒ 仍需一次 GRANT（migration 或授权轮）；
   若 runtime 连读都不需要（纯 CLI 驱动）⇒ 可零授权变更。
8. Need new decision count
   至少：① 是否接受人工 CLI 入驻及适用范围；② runtime 是否需读权限及最小读集；
   ③ 授权时机与承载 ⇒ 约 3 项新决策。
```

### OPTION D — Hybrid model

```text
形态（非穷举）：D-1 读侧给 uap_app 最小 SELECT + 写侧走受信路径；
                 D-2 新增专用角色（如 uap_service）承担 onboarding 写面；
                 D-3 分阶段（先 C，验证后再评估 A/B）。

1. Architecture impact
   D-1 分层不变但读写路径分离；D-2 新增角色 ⇒ 触及角色拓扑冻结面；D-3 阶段化 ⇒ 需防"临时形态固化"。
2. Security impact
   D-1 风险分层（读风险低 / 写风险隔离）；D-2 引入第三角色 ⇒ 治理复杂度上升；
   D-3 初期最安全但可能延长人工期。
3. C2 / CC-7 compatibility
   均兼容（前提：不触碰 registry）。
4. D-OP101 compatibility
   D-1 读侧扩权仍需新决策（D-OP101-07）；D-2 需评估与 D-OP101-01（RM-D 三角色）及
   D-OP101-06（uap_readonly DEFER）的关系 ⇒ 影响最大。
5. Future scalability
   D-1 最平衡；D-2 长期清晰但短期重；D-3 依赖后续轮次。
6. Implementation complexity
   D-1 中 / D-2 高 / D-3 分期（累计成本最高）。
7. Migration requirement
   D-1 需读侧 GRANT；D-2 需角色创建 + GRANT；D-3 视阶段而定 ⇒ 多数情形仍需独立授权轮。
8. Need new decision count
   D-1 ≈ 4；D-2 ≈ 6（含角色拓扑评估）；D-3 ≈ 3 + 后续轮 ⇒ 均高于 OPTION C。
```

## 1.3 矩阵摘要（**不排序 · 不推荐**）

```text
维度 × OPTION 的差异要点（压缩）：
  安全面最小      = C < D-1 < B ≈ A
  实现复杂度最低  = C < A < D-1 < B / D-2
  与 OI-G-1 张力  = C（无）< B/D-1 < A（最大）
  migration 需求  = C（可无）> A（必须）< B/D（可能）
  新决策数量最少  = C（≈3）< A/D-1（≈4）< B（≈5）< D-2（≈6）
  ⇒ 各 OPTION 在不同维度各有取舍，**无全维度占优者**；选择属 Human 价值判断（安全 vs 可用性 vs 复杂度）。
```

---

# Part 2 — Phase 3：Identity / Authorization 决策影响

## 2.1 OQ-P14-01（onboarding flow）不同方向的影响面

```text
若方向 = CLI 引导 →  影响 users（人工建立，量小）、identities（受控建立）、
                     memberships（少）、审计（每步可留证）；不影响 agents；
                     authorization runtime 仅需读侧；audit boundary 事件少而清晰。
若方向 = API 自助 →  影响 users（自动建立，量可能增长）、identities（自助绑定）、
                     audit boundary（登录/注册事件显著增加，需定义 action 与 rate 面）；
                     需新增滥用防护（属新决策）；authorization runtime 需写侧（会话/状态）。
若方向 = 邀请制   →  介于两者；需要邀请凭据的生成与撤销（新增机制 ⇒ 新决策）。
若方向 = 管理员代建 → 影响 users/identities（由管理员批量创建）；信任边界集中在管理员；
                     需定义代建权限（可能触及 RBAC 面）。
⇒ 共同影响面：users / identities / memberships / audit boundary /
             authorization runtime（读侧至少）；agents **不受影响**（P13 仅注册 subject type）。
```

## 2.2 OQ-P14-02（credential lifecycle）不同方向的影响面

```text
若托管 = 自管（库内哈希）→ 影响 credentials/identities 写入面 + 密钥材料存放（需 secret 面）；
                          需定义哈希族与参数（新决策）；不引入外部依赖。
若托管 = 外部 IdP   → 影响 identities.provider 取值使用（local/oidc/saml/… 既有 CHECK）；
                      不写 credentials（或仅存映射）；引入外部信任边界与网络依赖；
                      与 D-AUTH-18（词汇分离）关系需明确（identity provider ≠ authorization subject）。
若托管 = 设备绑定   → 影响 devices/sessions 表使用；影响认证流程与恢复路径。
⇒ 共同影响面：credentials / identities / sessions / audit boundary（认证事件）/
              authorization runtime（会话建立）；**不影响 agents**。
```

## 2.3 OQ-P14-04 / OQ-P14-05（判定位置 / 强制边界）不同方向的影响面

```text
若判定在 policy 层（core 契约 + service 编排）→ 影响 services/authorization（须建立，D-AUTH-16）；
  需读 roles/permissions/role_permissions/resource_permissions/memberships（**读侧扩权**）；
  不影响 schema；audit boundary 可记录判定结果（若裁定）。
若判定分散在 API 层 → 影响各 endpoint；一致性风险高；测试面分散。
若需 DB 层兜底 → **触发 schema 边界**（新增触发器/约束）⇒ 超出 Runtime Excluded，
  必须另立独立授权；与 D-AUTH-17（本冻结不产生 schema 变更）张力。
⇒ 影响面：authorization runtime 结构 · 读权限面 · 审计面 · 验收判据 AUT-1…AUT-4 的可判定性。
```

## 2.4 汇总（影响面矩阵 · 无推荐）

```text
对象                OQ-01   OQ-02   OQ-04   OQ-05
users                 ●       ○       ○       ○
identities            ●       ●       ○       ○
memberships           ●       ○       ●       ○
agents                ○       ○       ○       ○      （均不受影响：P13 仅注册 subject type）
authorization runtime ●       ●       ●       ●
audit boundary        ●       ●       ●       ○      （多数方向都会新增审计事件；需定义 action）
⇒ ● = 直接受影响 ／ ○ = 间接或不受影响
```

---

# Part 3 — Phase 4：Contract Architecture Analysis

## 3.1 ADD-1（Contract 载体）OPTION 对比

```text
OPTION 1 — 新增 P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md（并 amend 文档集合 4 → 5）
  governance clarity      : 高（实施规则单一权威载体；实施者可一本读完）
  future maintenance      : 中（新增一个需与 SCOPE/Matrix 保持一致的文件；漂移风险）
  consistency with P13    : 高（P13 有独立 Contract，形态一致）
  document count impact   : 4 → 5（须 amend RUNTIME_DOCUMENT_SET_DECISION.md）

OPTION 2 — Scope + Acceptance + Decision docs 承载（保持 4 份）
  governance clarity      : 中（规则分散于 SCOPE 与 PREP_REPORT；职责扩张）
  future maintenance      : 高（无新增文件；但 SCOPE 会持续膨胀）
  consistency with P13    : 低（与 P13 形态不一致）
  document count impact   : 0（不 amend 文档集合）

OPTION 3 — Contract（实施规则）+ PDL 附录（决策登记）
  governance clarity      : 高（决策与规则各自单一职责；决策沿用 canonical carrier）
  future maintenance      : 中（两处维护，需一致性纪律）
  consistency with P13    : 高（P13 决策亦在 PDL；实施规则在 Contract）
  document count impact   : 4 → 5（须 amend 文档集合）+ PDL 新增附录
```

## 3.2 ADD-2（Decision 登记位置）影响

```text
若登记于 PDL 新附录（如附录 N）：
  · 沿用 canonical carrier（与 D-P13-15 / D-OP101 登记先例一致）
  · append-only；不新增文件；跨阶段检索统一
  · 需在 PDL 追加 + 新增 END 行（既有 END 行保留）
若登记于 Contract 内附录：
  · 决策与实施规则同处一文，阅读连贯
  · 但决策载体分散（PDL 不再是唯一决策权威）⇒ 与项目「canonical carrier」原则张力
```

## 3.3 与本轮决策顺序的耦合

```text
ADD-1 / ADD-2 的选择**不阻塞** 13 项 OQ 的裁定（可先裁 OQ，后定载体）；
但 ADD-2 决定"裁定写在何处"⇒ 建议在**第 1 批 OQ 裁定之前**确定登记位置，否则需二次搬运。
（注：此为顺序建议，非内容建议；详见 P14_IMPLEMENTATION_DECISION_ORDER.md）
```

---

# 4. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
未执行任何 GRANT / REVOKE / database DML · 未新建表
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
本文档不输出 winner、不选择 OPTION；P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 DECISION IMPACT ANALYSIS（2026-09-27 · OQ-13 OPTION A–D × 8 维度 · Identity/Authorization 影响面 · Contract ADD-1/ADD-2 对比 · 未选择）**
