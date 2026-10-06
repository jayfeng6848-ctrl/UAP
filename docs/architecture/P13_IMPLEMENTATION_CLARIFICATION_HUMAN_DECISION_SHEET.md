# UAP — P13 IMPLEMENTATION CLARIFICATION · HUMAN DECISION SHEET

> ## 轮次与边界
>
> ```text
> 轮次      = P13 IMPLEMENTATION CLARIFICATION（决策请求单 · decision-only）
> 性质      = STRICT READ-ONLY 审计 + 决策请求固化；不含实施、不含裁决
> 本轮未做  = 未创建 0017 · 未创建 migration · 无 DDL · 无 DML · 无 seed ·
>             未改 runtime / API / worker / scheduler · 未改 env.py · 未改 0016 ·
>             未修复 OI-G-4 · 未改任何冻结 Decision 正文 · 未 commit / tag / push
> 本轮已做  = 只读取证 + 事实整理 + 选项枚举 + 精确裁决请求（本文件）
> ```
>
> **裁决状态（重要）**
>
> ```text
> IMPL-01 = UNRESOLVED（HUMAN DECISION REQUIRED）
> IMPL-02 = UNRESOLVED（HUMAN DECISION REQUIRED）
> IMPL-03 = UNRESOLVED（HUMAN DECISION REQUIRED）
> IMPL-04 = UNRESOLVED（依赖 IMPL-01）
> ```
>
> 本文件不包含任何 Human 裁决内容（本轮指令未给出 IMPL-01..04 的裁定取值）。
> 依本指令 §5：BOT 不得自行替 Human 选择方案；必须 STOP → 等待 Human answer。

---

# 1. 基线（只读实测 · 2026-09-27）

```text
HEAD                  = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e
branch                = main
dirty                 = 107（staged 0 · modified 36 · untracked 71）
migration head        = 0016_open_p10_1_trust_boundary（versions = 16）
0016 sha256           = 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544
env.py sha256         = 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a
0017                  = ABSENT
P13 implementation artifacts = 0（无 *p13* migration / schema / code / test）
alembic_version       = 0016_open_p10_1_trust_boundary
uap_migrator CREATE   = false · registry rows = 0 · agents 族 = 0
```

未授权变化 = 0。

---

# 2. 权威材料识别与分类

```text
FROZEN（canonical）
  PLATFORM_DECISION_LOG.md（D-P13-01..15 · D-OP101-01..14 · 附录 J/K/L）
  P13_DECISION_FREEZE_RECORD.md（2026-09-26 冻结记录）
  P13_ACCEPTANCE_MATRIX.md（35/35 PASSED）

DRAFT / NOT FROZEN（本轮待对账对象）
  P13_IMPLEMENTATION_CONTRACT.md（含 §17 IMPL-01..04）
  P13_IMPLEMENTATION_ACCEPTANCE_MATRIX.md（含 I-01..I-19）

HISTORICAL / PRE-DECISION（不得提升为现行决策）
  P13_PREP_REPORT.md · P13_HUMAN_DECISION_EXTRACTION.md ·
  P13_DECISION_COMPLETION_EVIDENCE.md · P13_HUMAN_DECISION_SHEET.md §1..§7

SUPERSEDED-IN-PART（已有决策指针）
  P13_B1_HUMAN_DECISION_AMENDMENT.md（O-1..O-4 候选 → 已被 FINAL DIRECTION 取代）
  STEP1B_SEED_STRATEGY.md §4（13 项草稿 → 已被 D-P13-01 的 12 项取代）

EVIDENCE
  P13_DECISION_COMPLETION_FREEZE_GATE_REPORT.md（2026-09-27）
  C2 CC-7 post-image md5 = 185e95be8bc4304edbcd3f4d5cda1eff
```

---

# 3. 现行 P13 Scope（复确认）

```text
scope = canonical baseline seed only（不新建任何 schema 对象）
目标对象 = acl_subject_types · permissions · role_permissions（+ 待裁：users · audit_logs）
排除     = tenants · spaces · memberships · platform_memberships · agents 族 ·
           credentials · deny · system.* · manage · write · ownership marker
```

实测现状（`uap_b1_test` @0016）：

```text
acl_subject_types = 0 行 · permissions = 0 行 · role_permissions = 0 行
roles = 1 行（platform_admin · PLATFORM · is_system=true · 0005 所有）
users = 0 行 · platform_state = 1 行（uninitialized）· platform_memberships = 0 行
tenants = 0 · spaces = 0 · audit_logs = 0 行 · events = 0 行
```

---

# 4. IMPL-01 — `users` 首个主体记录

## 4.1 Fact（只读实测）

```text
users 形态：
  id uuid NOT NULL DEFAULT uap_uuid_v7() · email text NULL · username text NULL
  display_name NULL · status text NOT NULL · primary_identity_id uuid NULL
  failed_attempts int NOT NULL DEFAULT 0 · created_at / updated_at NOT NULL · deleted_at NULL
  无 tenant_id 列
约束：
  ck_users_login  = CHECK (email IS NOT NULL OR username IS NOT NULL)
  ck_users_status = CHECK (status IN ('pending','active','suspended','locked','deleted'))
  users_pkey      = PRIMARY KEY (id)
  （PREP 记录中的 uq_users_email / uq_users_username 在当前 pg_constraint 输出中未列出 → 实施前须复核）
触发器：tg_users_set_updated_at · tg_acl_user_hard_delete
现况：users = 0 行
```

关键事实：`ck_users_login` 要求任何 `users` 行必须携带 `email` 或 `username`
⇒ 任何 users 行都自带一个「可登录标识」，即使不含凭据。

## 4.2 Existing frozen decisions

```text
D-P13-06（FROZEN）：create/bootstrap identity row = allowed；credential secret = forbidden；
                    「首个可登录主体」与「P13 创建主体记录」必须区分；登录能力由 onboarding 提供。
D-P13-13（FROZEN）：credentials = 0 · plaintext secrets = 0 · fabricated passwords = 0
D-P13-05 / 08（FROZEN）：不创建 bootstrap tenant · 不创建 tenant/space membership
D-PLAT-11①（FROZEN）：首个正式可登录主体**只通过 P13 建立**；② 不引入第二套开发 bootstrap 身份路径
R2 / R4 / R5（FROZEN 增补）：seed 只建角色行与 role_permissions 绑定；不授予任何用户角色；
                            首个平台管理员由受信 bootstrap CLI 写 platform_memberships
SEED_STRATEGY §1[4] / §6：首管理员用户入序；首管理员密码由 onboarding 设置（非 seed）
```

张力（须由 Human 消解，不得由 Bot 消解）：

```text
T-1  D-P13-06 措辞为 identity row = allowed（许可，非义务）
T-2  D-PLAT-11① 为义务性表述（只经 P13 建立）
T-3  D-P13-08 的 rationale 原文含「P13 不创建真实 user / administrator identity」
     —— 位于理由栏而非决策正文，但与 T-2 的派生方向相反
T-4  IMPLEMENTATION_CONTRACT §2.3 将其推导为 REQUIRED-DERIVED（必须插入 1 行无凭据 users）
     —— 该推导所在契约为 DRAFT · NOT FROZEN，不构成冻结决策
```

## 4.3 Requirement 四分

```text
required by schema                     = NO（users 允许 0 行）
required by seed                       = NO（registry / permissions / role_permissions 不引用 users.id）
required by authorization model         = NO（platform_admin 绑定走 platform_memberships，由 CLI 负责）
required only by implementation convenience = NO
required by D-PLAT-11① 的字面要求        = 存在争议（见 T-1..T-4）⇒ 需 Human 裁决
```

## 4.4 Implementation consequence

```text
若选 B（插入 1 行）：需确定性 email 或 username 作为 canonical 种子身份 + status 取值；
  该行虽无凭据但自带可登录标识，存在被误认为可用账号的风险；downgrade 必须能安全识别（→ IMPL-04）。
若选 A（不插入）：D-PLAT-11① 的字面表述需由 Human 重新解释
  （该解释义务此前已登记于 PDL 附录 J.3 前置澄清项 ①）。
任一选择都不改变 schema，也不改变 uap_app / uap_migrator 权限面。
```

## 4.5 Candidate options（仅枚举 · 不推荐）

```text
选项 A：P13 不插入任何 users 行；identity 由后续受信 onboarding / CLI 建立，
        并配套 D-PLAT-11① 的正式重新解释登记。
选项 B：P13 插入恰 1 行无凭据 users 行；须指定确定性身份句柄（email 或 username 取值）与 status。
选项 C：CUSTOM（Human 自定义形态）。
```

## 4.6 Exact Human Decision request

```text
HUMAN DECISION REQUIRED
  IMPL-01-SELECTION = A / B / CUSTOM
  若为 B 或 CUSTOM，请给出：
    (a) 确定性身份句柄与取值（email / username）
    (b) status 取值
    (c) 是否需显式声明该行「不可登录 / 无凭据」的语义
    (d) 是否要求同步登记 D-PLAT-11① 的重新解释文本
```

STOP pending Human answer。

---

# 5. IMPL-02 — `role_permissions` 确定性绑定集合

## 5.1 Fact

```text
role_permissions 形态：
  PK = (role_id, permission_id, effect) · effect CHECK ∈ {allow, deny}
  conditions jsonb NULL · created_at NOT NULL
  FK: role_id → roles(id) ON DELETE CASCADE · permission_id → permissions(id) ON DELETE CASCADE
  触发器：无
现况：role_permissions = 0 行 · permissions = 0 行 · roles = 1 行（platform_admin）
permissions CHECK：ck_permissions_action_canonical =
  {read,list,create,update,delete,execute,approve,reject,publish,export,share,admin}
  ck_permissions_key = ^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$
```

## 5.2 Existing frozen decisions（逐条回答本指令 §7 清单）

```text
哪些 role 参与？              → 冻结未指定绑定集合；已知唯一系统角色 = platform_admin（0005 所有）
哪些 permission 参与？        → D-P13-01 冻结 12 项 canonical
是否只允许 canonical allow？   → 是（D-P13-01：is_system=true · effect=allow）
是否包含 deny？               → 不包含（D-P13-01 Q4）
是否包含 system.*？           → 排除（D-P13-01 Q3）
是否包含 manage / write？      → 排除（仅作输入别名 → admin / update）
是否存在 platform_admin？      → 是，1 行，属 0005（D-P13-02）
P13 是否只创建新增关系？       → 现无既有 role_permissions 行（实测 0）⇒ 无重复创建风险
既有角色关系能否重复创建？      → D-P13-10：conflict = 显式失败（禁 upsert / 禁 ON CONFLICT DO NOTHING）
```

未被冻结覆盖（因此需要裁决）：

```text
绑定的基数与组成未被任何 D-P13-* 记录指定；
D-P13-01「影响范围」列仅确认「存在确定性 role_permissions 绑定」，未裁定其内容；
契约 §17 IMPL-02 的建议方向（platform_admin × 12 = 12 行 · 全 allow）被该文件自标为「建议方向（≠ 决策）」；
R2 仅规定「seed 只建角色行与 role_permissions 绑定」，未给出集合内容。
```

## 5.3 Implementation consequence

```text
该集合直接决定：seed 行数、幂等键、downgrade clean-baseline 计数、验收矩阵判定行，
以及「P13 之后 platform_admin 是否持有任何 permission」这一授权事实。
取 0 行：platform_admin 在 P13 后仍无任何 permission 绑定。
取 12 行（全 allow）：需确认 platform_admin 持有 tenant.* / space.* / member.* 等非平台域权限是否成立
（属 Human 的业务/架构判断）。
不得包含 deny 行；不得引入 system.* / manage / write（D-P13-01）。
```

## 5.4 Candidate options（仅枚举 · 不推荐）

```text
选项 A：platform_admin × D-P13-01 全部 12 项 · effect=allow ⇒ 12 行
选项 B：0 行（P13 不建立任何绑定；留待 bootstrap / onboarding / Runtime）
选项 C：Human 指定的子集（须逐项给出 role × permission × effect 与基数）
选项 D：CUSTOM
```

## 5.5 Exact Human Decision request

```text
HUMAN DECISION REQUIRED
  IMPL-02-SELECTION = A / B / C / CUSTOM
  若为 C 或 CUSTOM，请给出：
    (a) 精确行数与逐行清单（role · permission · effect）
    (b) 幂等键与冲突语义确认（沿用 D-P13-10：conflict = 显式失败）
    (c) downgrade clean-baseline 计数（与 IMPL-04 联动）
```

STOP pending Human answer。未经裁决：`IMPL-02 = UNRESOLVED` ⇒
Implementation Agent 无法在不猜测的前提下写出 role_permissions 段。

---

# 6. IMPL-03 — P13 是否写 `audit_logs`

## 6.1 Fact

```text
audit_logs 形态：
  PK = (id, occurred_at)（分区表）
  actor_type text NOT NULL · actor_id uuid NULL（**无 FK 指向 users**）
  action NOT NULL · result NOT NULL ∈ {success,denied,error}
  risk_level NOT NULL ∈ {LOW,MEDIUM,HIGH,CRITICAL} · metadata jsonb NOT NULL
触发器：tg_audit_immutable（BEFORE DELETE OR UPDATE → 阻断）⇒ 写入后不可改
现况：audit_logs = 0 行
```

关键事实：`audit_logs` 无 users FK ⇒ 以 `actor_type='system'`、`actor_id=NULL` 写入
**不需要**任何 users 行 ⇒ IMPL-03 与 IMPL-01 在 schema 上不耦合。

## 6.2 Existing frozen decisions

```text
P10（0013 FROZEN）：提供 audit_logs / events schema；audit 不可变。
R4 / R5（FROZEN 增补）：bootstrap CLI 写 audit_logs(action='platform.admin.bootstrap', actor='system')；
                        0006 seed 只建结构；迁移先例中无 audit 写入。
SEED_STRATEGY §6（设计文本 · 非决策）：seed 事件写 audit_logs（actor=system）。
P13 决策面：D-P13-01..15 未对 audit 写入作出裁定。
```

区分（本指令 §8 要求）：

```text
schema existence        = 有（0013）
trigger-generated audit = 无（audit_logs 自身仅不可变触发器；CF-2：触发器不写 audit）
migration-explicit DML  = 先例为「无」（0005 / 0006 均不写）
runtime audit           = 属 Runtime 阶段语义
seed audit              = 未裁定（SEED §6 设计文本 vs 迁移先例相左）
```

## 6.3 Implementation consequence

```text
若写：需指定 action 名、条数、result / risk_level / classification；
  因 tg_audit_immutable，事后不可修正；并改变对象接触面与验收矩阵判定行。
若不写：与既有迁移先例一致；seed 运行审计交由部署 / 运维层。
两种选择都不改变 schema、C2 行为或权限面。
```

## 6.4 Candidate options（仅枚举 · 不推荐）

```text
选项 A：不写 audit_logs（遵循迁移先例；seed 审计交由运维层）
选项 B：写 audit_logs（须指定 action / 条数 / result / risk_level；actor_type='system'、actor_id=NULL）
选项 C：CUSTOM
```

## 6.5 Exact Human Decision request

```text
HUMAN DECISION REQUIRED
  IMPL-03-SELECTION = A / B / CUSTOM
  若为 B 或 CUSTOM，请给出：
    (a) action 字符串
    (b) 条数（1 条汇总 or 逐 seed 条目）
    (c) result / risk_level / classification 取值
    (d) downgrade 时是否需处理（注意 tg_audit_immutable 禁止删除 / 更新）
```

STOP pending Human answer。

---

# 7. IMPL-04 — downgrade 移除判据

## 7.1 Existing frozen constraints

```text
D-P13-12（FROZEN · FAIL-CLOSED）：允许降级的三前提须同时成立
  ① 无 runtime 数据超出已定义 seed baseline
  ② 无无法解释的 dependent rows
  ③ 无 ownership ambiguity
  任一不成立 ⇒ RAISE ⇒ 整条 downgrade 回滚 ⇒ 0 DELETE
  禁止：DELETE WHERE key IN (...) 作默认行为；因「理论上这些 key 是 seed」而删除
  禁止：新增 seed_batch / migration_owned / ownership marker 列（D-P13-14）
  不得单独用 is_system / natural key / FK RESTRICT / audit_logs 证明 ownership
D-P13-10（FROZEN）：role_permissions 冲突 = 显式失败
实测：全库无行级 ownership 标记列；P13 相关既有行全为 0
```

## 7.2 本指令 §9 逐问

```text
是否存在 marker？         → 否（且 D-P13-14 禁止新增）
是否允许依赖固定 UUID？    → 未裁定
是否允许依赖固定 email？   → 未裁定（且 users 行是否创建亦未裁）
是否允许依赖固定 username？→ 未裁定
是否通过唯一业务键识别？   → 部分：registry.key / permissions.key 有 UQ；role_permissions 为三列 PK；
                            users 当前可见约束中未见 UQ（待复核）
是否完全不删除？           → 未裁定（候选之一）
downgrade 安全条件？       → D-P13-12 已给出三前提；具体判据语句未细化
```

依赖关系：`IMPL-04 ⊂ f(IMPL-01, IMPL-02)`

```text
若 IMPL-01 = A 且 IMPL-02 = B ⇒ 降级面仅含 acl_subject_types(3) + permissions(12)，
                               判据可完全由 D-P13-12 三前提表达
若 IMPL-01 = B 或 IMPL-02 = A/C ⇒ 必须额外为 users / role_permissions 行定义确定性可复核判据
```

## 7.3 Candidate options（仅枚举 · 不推荐）

```text
选项 A：降级仅移除 acl_subject_types + permissions（及 Human 选定后纳入的 role_permissions），
        超 baseline 即 FAIL-CLOSED；users 行（若存在）不删除，登记为 known residue。
选项 B：移除 users 行的判据 = 「count 精确 = 1 ∧ 身份句柄恰为 canonical 取值 ∧ 无其他依赖行」，
        否则 RAISE（0 DELETE）。
选项 C：完全不删除任何行；downgrade 仅做校验，不满足 baseline 即 RAISE（永不产生 DELETE）。
选项 D：CUSTOM
```

## 7.4 Exact Human Decision request

```text
HUMAN DECISION REQUIRED
  IMPL-04-SELECTION = A / B / C / CUSTOM
  并请确认：「deterministic ∧ safe ∧ reviewable」是否作为硬性验收条件写入 Acceptance Matrix
```

STOP pending Human answer。未经裁决：`IMPL-04 = UNRESOLVED`。

---

# 8. B-1 Amendment 形式化（派生自已冻结决策 · 非新决策）

## 8.1 过时陈述与当前事实

```text
old statement（出现在 NOT FROZEN 的 DRAFT 契约中）
  位置：P13_IMPLEMENTATION_CONTRACT.md:138 / :383 / :448
  主张： 「C2 对 INSERT 无条件 RAISE，无任何豁免分支 / 无 GUC 判据 / 无角色白名单」
         「registry 在冻结集合内无合法机制」⇒ BLOCKER B-1

current fact（本轮实测）
  public.enforce_acl_subject_types_protect()
    md5(pg_get_functiondef) = 185e95be8bc4304edbcd3f4d5cda1eff（CC-7 post-image）
    含受信分支：current_user = session_user = 'uap_migrator' 时放行 registry 写
    runtime 路径仍拒 INSERT，错误文本保持 ⇒ 满足 D-P13-03「runtime INSERT = FORBIDDEN」
    函数签名不变（() RETURNS trigger · pronargs 0 · plpgsql · prosecdef false）
```

## 8.2 形式化：old → amended → new canonical

```text
old statement         = 「C2 无条件 RAISE ⇒ registry seed 无合法机制（B-1）」
classification        = AMENDED（被已冻结决策取代）
superseding decisions = D-P13-15（B-1 Amendment · FROZEN · PDL 附录 K）
                        + D-OP101-05（C2 判据 = CUSTOM / CP-F / CC-7 · FROZEN）
                        + BATCH-C 执行面（CF-C-5=B 窗口期 GRANT → verify → REVOKE）
new canonical statement = 「D-P13-03 的『受信主体』= 受信迁移身份：
                          current_user = session_user = uap_migrator（连接期实测断言，
                          env.py `_assert_effective_role` FAIL-CLOSED）；
                          该身份经 C2 的 CC-7 判据分支获得 registry 写入放行；
                          runtime（uap_app）路径行为逐字保持拒绝。」
rationale             = 数据库身份隔离已落地（BATCH-A/B/C：migration = uap_migrator，
                        runtime = uap_app，双向禁 fallback）⇒ D-P13-15 前置条件已成立；
                        O-1 与 O-4 已被 REJECT；O-2 由 D-OP101-05 = CUSTOM（CC-7）解答。
dependent contract sections（须一并更正 · 本轮未改）
  P13_IMPLEMENTATION_CONTRACT.md §3.1 事实 A · §3.2 · §3.4 · §14 · §18
  P13_IMPLEMENTATION_ACCEPTANCE_MATRIX.md 中与 C2 判据相关的行
```

## 8.3 概念分离（不得混用）

```text
trusted migration identity     = uap_migrator（数据库角色；C2 受信判据对象）
application / runtime identity = uap_app（数据库角色；C2 拒绝对象）
authorization subject          = ACL subject（user / role / agent 注册表条目）
audit actor                    = audit_logs.actor_type / actor_id（无 users FK）
seed-created user              = IMPL-01 待裁项；不自动等于 migration identity，
                                 也不自动成为 audit actor 或 authorization subject
```

本条为派生形式化：内容全部来自已冻结决策与实测事实，未新增裁定。

---

# 9. Contract / Acceptance Matrix 对账计划（受裁决门控 · 本轮未执行）

```text
门控条件：IMPL-01..04 全部获得 Human Decision 后方可执行。

Contract：
  C-1 revision identity：0016_p13_seed → 0017_p13_seed（依 D-OP101-03；只在 active Contract 内对账）
  C-2 down_revision：0016_open_p10_1_trust_boundary（依 D-OP101-03 与当前链头）
  C-3 §3 / §14 / §18 依 §8.2 更正 C2 判据陈述（AC-1）
  C-4 §5 / §6 / §12 / §15 依 IMPL-01..04 写入 users / role_permissions / audit 决定
  C-5 §17 IMPL-01..04 → RESOLVED（附 Decision 来源指针）
  C-6 §20.4 P-1..P-4 → RECONCILED（附证据指针）

Acceptance Matrix：
  M-1 I-01 的 revision 断言 → 0017_p13_seed
  M-2 I-02 解除 BLOCKED（B-1 机制面已由 CC-7 打开）
  M-3 新增 / 修订 users · role_permissions · audit_logs · downgrade 判据相关判定行
  M-4 全部判定行须可机械判定（PASS / FAIL），不得依赖设计再解释
```

---

# 10. Zero-Guess 测试（当前时点结果）

```text
Q1  建设清单是什么？                       → BLOCKED（role_permissions / users 取决于 IMPL-01/02）
Q2  哪些对象 / 记录明确不创建？              → 可唯一回答
Q3  每一条 seed 的精确内容是什么？           → BLOCKED（registry 3 / permissions 12 可答；其余不可）
Q4  每个 role 的精确 permission 集合是什么？  → BLOCKED（IMPL-02 未裁）
Q5  trigger 判据是什么？                    → BLOCKED（AC-1：契约 C2 陈述过时，须先按 §8.2 更正文本）
Q6  是否会产生 audit_logs？为什么？          → BLOCKED（IMPL-03 未裁）
Q7  downgrade 的精确移除判据是什么？         → BLOCKED（IMPL-04 未裁，且依赖 IMPL-01/02）
Q8  test obligations 是什么？               → BLOCKED（Acceptance Matrix 为 DRAFT · NOT FROZEN）
Q9  哪些现有对象绝不能改变？                 → 可唯一回答
Q10 实施失败时什么状态才算 FAIL-CLOSED？     → 可唯一回答（D-P13-12 三前提 + 0 DELETE）

结果 = 4 / 10 uniquely answerable ⇒ 6 项 BLOCKED
⇒ P13 IMPLEMENTATION READINESS = BLOCKED
```

---

# 11. 一致性 / 冲突扫描（当前时点）

```text
P09 consistency            = PASS（仅注册 subject type agent；agents 族 = 0）
Authorization consistency  = PASS（platform_admin 属 0005；零租户/空间角色；词表未改）
P10 consistency            = PASS（不写 events；audit 写入待 IMPL-03）
P11 consistency            = PASS（39 父级触发器全启用；零 DISABLE / ALTER）
P12 consistency            = PASS（无新增索引；156 + 22 = 178 ownership 未变）
0016 consistency           = PASS（CC-7 已落地；与 D-P13-15 前置一致）
B-1 amendment consistency  = PARTIAL（派生形式化成立；Contract 文本尚未更正）

AC-1 = active（DRAFT 契约陈述过时；阻塞 Q5 的可答性；本轮已给形式化处置，未改文本）
AC-2 = documentation stale（0016_p13_seed → 0017_p13_seed；待 Contract 对账轮）
AC-3 = historical / time-bound（0016+ = ABSENT 等时点事实；非现行主张）
```

---

# 12. OI-G-4

```text
ID = OI-G-4 · classification = BATCH-D / maintenance · status = REGISTERED / UNFIXED
对象 = scripts/generate_build_info.py · tests/unit/test_generate_build_info.py
P13 impact = none（未发现新的直接、可验证依赖）
本轮处置 = 未修复 · 未重分类 · 未提升为 P13 blocker / 0017 requirement / 0016 defect
```

---

# 13. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration execution = 0 · seed = 0
runtime / API / worker / scheduler change = 0
env.py = unchanged · 0016 = unchanged
migration 文件新增 = 0 · 0017 = ABSENT
被修改的既有文档 = 0（本文件为新增）
commit = 0 · tag = 0 · push = 0
```

---

# 14. 本轮结论与阻塞项

```text
P13 IMPLEMENTATION CLARIFICATION = PARTIAL（事实整理与请求单已完成；裁决未取得）
P13 IMPLEMENTATION READINESS     = BLOCKED
P13 DECISION FREEZE              = BLOCKED

精确阻塞项（全部为 HUMAN DECISION REQUIRED）
  B-1 IMPL-01 = UNRESOLVED → 阻塞 Q1 / Q3 / Q7
  B-2 IMPL-02 = UNRESOLVED → 阻塞 Q1 / Q3 / Q4 / Q7
  B-3 IMPL-03 = UNRESOLVED → 阻塞 Q3 / Q6
  B-4 IMPL-04 = UNRESOLVED → 阻塞 Q7（依赖 IMPL-01 / IMPL-02）
  B-5 C2 判据陈述更正（AC-1）→ 阻塞 Q5（形式化已备，待裁决后落文本）
  B-6 Contract / Acceptance Matrix 对账与冻结 → 阻塞 Q8

解除路径 = 取得 IMPL-01..04 Human Decision → 执行 §9 对账轮 → 重跑 §10 Zero-Guess 测试；
          10/10 方可判定 Implementation Readiness = PASS。
```

本文件不构成实施授权。`P13 IMPLEMENTATION AUTHORIZATION` 仍是独立、必需的下一步。

---

**END OF P13 IMPLEMENTATION CLARIFICATION HUMAN DECISION SHEET（2026-09-27 · `IMPL-01..04 = UNRESOLVED` · `P13 IMPLEMENTATION READINESS = BLOCKED` · awaiting Human Decision）**
