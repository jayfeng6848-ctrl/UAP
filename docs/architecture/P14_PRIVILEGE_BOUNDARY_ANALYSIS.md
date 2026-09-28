# UAP — P14 PRIVILEGE BOUNDARY ANALYSIS

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — DECISION PREPARATION ROUND（Phase 3）
> 对象      = OQ-P14-13（runtime privilege boundary · 含 OI-G-1）
> 性质      = 只读取证 + 候选枚举；**不选择任何 OPTION**、**不做裁定**
> 本轮未做   = 未执行任何 GRANT / REVOKE / ALTER OWNER / default ACL 变更 ·
>             无 DDL / DML · 未创建 runtime code · 未改冻结决策
> ```

---

# 1. 现状取证（只读实测 · `uap_b1_test` @0017）

## 1.1 角色与授权面

```text
uap_app 显式授权（non-owner 口径）= **恰 5 项**
  alembic_version      : SELECT
  audit_logs           : INSERT · SELECT
  audit_logs_202609    : INSERT · SELECT
  + SCHEMA public USAGE（namespace ACL：uap_app=U）
  （CREATE on public = false）

uap_migrator 显式授权（non-owner 口径）= 245 行（对象自持导致 relacl 实体化，非外部授予）
uap_migrator：CREATE on public = false · 非超级用户

pg_default_acl = 0（无默认授权 ⇒ 未来新表 / 新分区不自动继承任何权限）

所有权：public 下 pg_class（r/p/i/I）= 156 全部 owner = uap_migrator
        pg_proc = 22 全部 owner = uap_migrator · ownership 残留 = 0
```

## 1.2 uap_app 逐表权限矩阵（实测）

```text
table                    SELECT  INSERT  UPDATE  DELETE
users                    False   False   False   False
identities               False   False   False   False
roles                    False   False   False   False
permissions              False   False   False   False
role_permissions         False   False   False   False
tenants                  False   False   False   False
spaces                   False   False   False   False
platform_memberships     False   False   False   False
tenant_memberships       False   False   False   False
memberships              False   False   False   False
resource_permissions     False   False   False   False
audit_logs               True    True    False   False
alembic_version          True    False   False   False
events                   False   False   False   False
agents                   False   False   False   False
platform_state           False   False   False   False

⇒ 结论：runtime 当前**只能**读 alembic_version、写读 audit_logs；
        对全部业务/授权/身份表（15 张抽样中 13 张）**零权限**（连 SELECT 都没有）。
```

## 1.3 既有安全触发器（DB 层强制面 · 实测）

```text
父级触发器 39（非内部合计 40）· 相关者：
  tg_acl_subject_types_protect（C2 · acl_subject_types · tgenabled='O'）
  tg_roles_is_system_protect（roles · 拒 runtime 建 is_system 行）
  tg_roles_pm_lifecycle / tg_roles_scope_shape / tg_acl_role_delete_block
  tg_pm_bootstrap_gate / tg_pm_last_admin（platform_memberships）
  tg_tm_role_scope / tg_membership_role_scope（membership scope 校验）
  tg_audit_immutable（audit_logs 禁 UPDATE/DELETE）
  tg_acl_user_hard_delete（users AFTER DELETE）
  G/H/I/J 族（ACL 主体存在性 / 一致性）
```

## 1.4 CC-7 行为（实测函数体）

```text
public.enforce_acl_subject_types_protect()
  IF current_user = 'uap_migrator' AND session_user = 'uap_migrator' THEN
      DELETE → RETURN OLD ; 其余 → RETURN NEW      （受信分支：放行）
  END IF
  INSERT → RAISE 'runtime INSERT denied ...'
  DELETE → RAISE '... cannot be deleted (retire via archived_at)'
  UPDATE(key 变更) → RAISE 'key is immutable'

md5 = 185e95be8bc4304edbcd3f4d5cda1eff · 签名 () RETURNS trigger · plpgsql · prosecdef=false
```

---

# 2. 三问作答

## 2.1 哪些 runtime 行为需要数据库写权限？

```text
按 SCOPE §2 的 Included 6 项逐项推导（**分析**，非结论）：

W-1 identity onboarding（OQ-P14-01/02）
    · 建首个可登录主体 ⇒ users INSERT（+ identities / credentials 行）
    · 设密 / 轮换 ⇒ credentials（或 identities）INSERT/UPDATE
    · 会话面 ⇒ sessions INSERT/UPDATE/DELETE（若自建会话）
W-2 tenant / space 建立（D-P13-05/08 留给 Runtime 的部分）
    · tenants INSERT · spaces INSERT
    · 每租户/空间系统角色补种 ⇒ roles INSERT（含 is_system=true ⇒ 受 tg_roles_is_system_protect 约束）
    · tenant_memberships / memberships INSERT
W-3 bootstrap（OQ-P14-09）
    · platform_memberships INSERT（首行）· platform_state UPDATE（uninitialized → initialized）
    · audit_logs INSERT（platform.admin.bootstrap）
W-4 runtime 授权执行（OQ-P14-04/05）
    · 读：roles / permissions / role_permissions / resource_permissions / memberships（**至少 SELECT**）
    · 写：resource_permissions / role_permissions 的授予与撤销（若 runtime 承担 grant/revoke）
W-5 审计（SEC-5 / AUD-1）
    · audit_logs INSERT（已具备）
W-6 事件（若启用 outbox）
    · events INSERT + 发布路径（当前无权限）

⇒ 需要写权限的行为集中在 W-1 / W-2 / W-3 /（可能）W-4 的写侧；
  需要**读权限**的行为覆盖 W-4 的读侧（当前连 SELECT 都没有）。
```

## 2.2 哪些表需要写？

```text
（按上节推导的候选集合 · 仅为枚举，非建议）

写候选：users · identities · credentials · sessions ·
        tenants · spaces · roles（系统角色补种）· tenant_memberships · memberships ·
        platform_memberships · platform_state · resource_permissions · role_permissions ·
        audit_logs（已具备）· events（若启用）

读候选（授权判定所需）：roles · permissions · role_permissions · resource_permissions ·
        memberships / tenant_memberships · tenants · spaces · users · platform_memberships ·
        agents / agent_versions / agent_permissions / tools / tool_permissions（若涉及 agent 执行）
```

## 2.3 这些写权限是否违反既有决策？

```text
① 对 D-OP101-07（runtime GRANT = minimum required set）
   「禁止：不得过度授权；**不得在未获新决策前扩权**（禁止以扩权替代"最小集"）；
     不得授予 runtime 任何 DDL 权限」
   ⇒ 判定：**任何 GRANT 动作本身就是"新决策"事件**。
     本路线 HARD RULES 明令「禁止修改 GRANT / REVOKE / default ACL」⇒
     在**本轮**不得执行；且从 D-OP101-07 的字面看，扩权必须由 Human 以新决策形式授权。
     ⇒ 结论：**不是"违反"，而是"必须由 Human 先行授权"**（未授权即扩权才构成违反）。

② 对 D-OP101-08 / D-P10-13（runtime 不持 DDL）
   ⇒ 判定：本轮候选 OPTION 均**只涉及 DML 面**（SELECT/INSERT/UPDATE/DELETE），
     不涉及 DDL ⇒ 与「不得授予 runtime 任何 DDL 权限」**不冲突**。
     但 OPTION B/C 涉及"以更高权限角色执行写" ⇒ 需单独评估是否等价于变相授予 DDL/治理能力。

③ 对 C2 / CC-7
   ⇒ 判定：只有"Runtime 需要写 acl_subject_types"才会冲突；**当前无任何 runtime 需求要求改 registry**
     （registry 3 行已满足基线）⇒ **不冲突**（前提：Human 确认 OQ-P14-12 为「Runtime 不触碰 registry」）。

④ 对 OI-G-1（runtime 逐表 DML 矩阵不可核定 · 不得扩权）
   ⇒ 判定：OI-G-1 正是本议题的既有登记。
     其状态 = REGISTERED（BATCH-D）；本路线若要扩权，**必须先关闭或重述 OI-G-1**，
     否则任何扩权都与该登记的"不得扩权"表述冲突。

⑤ 对 D-PLAT-13（Governance / Gate Slice 定性）
   ⇒ 判定：D-PLAT-13 规定 Governance Slice **不属于** Runtime、且不得创建 P14 引用；
     它**不直接**约束 runtime 权限面。
     但若把"放权/授权编排"混入 Governance Slice 或反之，会造成阶段混称 ⇒ 应避免。

⑥ 对 D-B14-02（先例 · D-PLAT-13 背景引用为"提前实施 = 静默扩权"）
   ⇒ 判定：该先例确立原则——**提前实施需另案批准 + 修订冻结文档**。
     据此，本议题若倾向扩权，应走"新决策 + 文档登记"而非静默实施。

⑦ 对 OI-G-2（未来 audit_logs 分区不继承授权 · pg_default_acl = 0）
   ⇒ 判定：若未来新增分区且 runtime 需写 audit_logs，必须**逐分区授权**（或引入 default ACL，
     但 default ACL 变更属本路线 Excluded）。这是一个**连带待决项**。

总判定（分析）
  · 不存在"可自行执行"的写路径扩权；
  · 所有候选路径都需要 **Human 明确决策 + 独立授权**；
  · 其中 OPTION A（直接扩权）将同时触发 OI-G-1 的重述需求。
```

---

# 3. 候选模型（**仅枚举 · 禁止选择**）

## OPTION A — runtime direct DML（按最小集逐表 GRANT 给 uap_app）

```text
形态    : 为 uap_app 按"实际读写面"逐表授予 SELECT / INSERT / UPDATE / DELETE 最小集；
          写路径由 runtime 自身执行。
优点    : ① 实现最简单，无额外服务/角色；② 与 D-OP101-07「minimum required set」字面一致；
          ③ 权限面集中在一个角色，便于审计。
风险    : ① 授权面从 5 项扩张到数十项 ⇒ 攻击面显著增大（runtime 被攻破即可直接写身份/授权表）；
          ② 需逐表核定（当前"实际读写面"尚未定义 ⇒ 依赖 OQ-P14-01/02/09 先定）；
          ③ 与 OI-G-1（不得扩权）直接张力。
冲突点  : 与 OI-G-1 的既有登记冲突（须先关闭/重述）；
          与 D-OP101-07 的"未获新决策前不得扩权"要求 ⇒ 必须由 Human 新决策授权（非自动违反）。
后续所需 Human Decision :
          ① 是否批准扩权（含"最小集"的逐表清单）；
          ② 是否重述/关闭 OI-G-1；
          ③ 是否接受"runtime 直接持写权限"的安全风险等级；
          ④ 是否同步为未来分区建立逐分区授权流程（OI-G-2）。
```

## OPTION B — trusted internal service boundary（受信边界承担写路径）

```text
形态    : runtime **不**直接持业务表写权限；写入经一个受信内部边界执行
          （例如：专用受信组件 / 独立角色 / 受信服务 + 最小接口），runtime 只经该接口请求写入。
优点    : ① 缩小 runtime 直接权限面（runtime 可保持低权限）；
          ② 与既有「migration 身份 vs runtime 身份」分离思想同向；
          ③ 写入路径集中，便于审计与限流。
风险    : ① 引入新的组件/角色 ⇒ 新信任边界本身需要设计与验证（否则成为新单点）；
          ② 若受信组件持高权限 ⇒ 风险转移而非消除；需明确其身份与凭据托管；
          ③ 复杂度与运维成本上升。
冲突点  : 与"不新增 schema"不冲突；与"不新增 GRANT"的张力取决于是否给新角色授权
          （新角色也要 GRANT ⇒ 仍需 Human 授权）；
          若新组件被定义为"migration-only authority 的复用"，需评估是否触及 D-OP101-08 的意图。
后续所需 Human Decision :
          ① 是否设立受信内部边界（及其身份形态：新角色 / 复用 uap_migrator / 其他）；
          ② 该边界的凭据托管与调用鉴权方式；
          ③ 其权限集（最小集）与审计要求；
          ④ 与 OI-G-1 的关系。
```

## OPTION C — existing migration-only authority（写路径全部留在 migration / CLI 侧）

```text
形态    : runtime 保持当前权限（或仅补读权限）；所有写动作（onboarding / bootstrap /
          租户空间建立）由受信 CLI 以 uap_migrator（或同等受信身份）执行。
优点    : ① 完全不需要 runtime 扩权 ⇒ 与 OI-G-1 / D-OP101-07 的最强解读一致；
          ② 与 R4/R5「bootstrap 由受信 CLI 执行」既有先例一致；
          ③ 安全面最小（runtime 无法写身份/授权表）。
风险    : ① **平台失去自助能力**：任何新用户/租户/空间都需要人工运行 CLI
             ⇒ 与"practical / usable / multi-user / multi-device"产品目标张力明显；
          ② 运维负担随规模线性增长；
          ③ 若未来要开放注册，仍需另立决策（不是终局形态）。
冲突点  : 与既有冻结决策**无直接冲突**；但与产品目标（可用性）存在张力，
          该张力须由 Human 判断是否可接受。
后续所需 Human Decision :
          ① 是否接受"人工 CLI 驱动的入驻模式"及其适用范围（永久 / 过渡）；
          ② runtime 是否至少需要**读权限**（当前连 SELECT 都没有）；
          ③ 若需要读权限 ⇒ 读侧最小集清单与授权时机。
```

## OPTION D — 其他（混合 / 专用角色 / 分阶段）

```text
形态（非穷举 · 仅示例，非建议）：
  D-1 混合：读侧给 uap_app 最小 SELECT 集；写侧走受信路径（A 的读 + C 的写）
  D-2 新专用角色：如 uap_service（仅 onboarding 写面），与 uap_app 分离
  D-3 分阶段：先 C（人工驱动）→ 验证后再评估 A/B
优点    : 可按风险分层，读/写解耦。
风险    : ① 角色/路径增多 ⇒ 治理复杂度上升（每新增角色都触发一套属性/所有权/审计问题）；
          ② D-2 引入新角色 ⇒ 触及 178 ownership 拓扑与角色拓扑冻结面，须谨慎；
          ③ 分阶段可能造成"临时形态固化"。
冲突点  : D-2 若新增角色 ⇒ 需评估与 `D-PLAT` 角色拓扑（RM-D）及 `D-OP101-01/06`（uap_readonly DEFER）的关系。
后续所需 Human Decision :
          ① 是否采用混合/分阶段；② 是否允许新增数据库角色；③ 各阶段授权清单与撤回条件。
```

---

# 4. 与既有登记的关系（汇总）

```text
OI-G-1（runtime 逐表 DML 矩阵不可核定 · 不得扩权 · REGISTERED / BATCH-D）
  ⇒ 本议题即为其具体化；任何 OPTION A/B/D-2 均需先处理该登记
OI-G-2（未来 audit_logs 分区不继承授权）
  ⇒ 与 OPTION A 的审计写入面连带；需逐分区授权或引入 default ACL（后者属 Excluded）
D-OP101-07（minimum required set · 未获新决策前不得扩权）
  ⇒ 所有 OPTION 的授权动作都必须是"新决策"的产物
D-OP101-08 / D-P10-13（runtime 不持 DDL）
  ⇒ 四个 OPTION 均不涉及 DDL ⇒ 不冲突
C2 / CC-7（D-P13-03 / D-13-15 / D-OP101-05）
  ⇒ 只要 Runtime 不触碰 registry ⇒ 不冲突
D-PLAT-13（Governance Slice 定性）
  ⇒ 不直接约束；但须避免"授权编排"被表述为 Governance Slice 或反之
```

---

# 5. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
未执行任何 GRANT / REVOKE / ALTER OWNER / default ACL 变更
新增文档 = 本报告（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
本文档不选择任何 OPTION；P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 PRIVILEGE BOUNDARY ANALYSIS（2026-09-27 · OQ-P14-13 · OPTION A/B/C/D 已枚举 · 未选择 · P14 IMPLEMENTATION = NOT AUTHORIZED）**
