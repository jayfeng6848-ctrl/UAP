# UAP — P14 PRIVILEGE / SECURITY GATE REPORT

> ## 状态
>
> ```text
> 轮次      = P14 PRIVILEGE / SECURITY GATE（Phase 2–15）
> 状态      = **DECISION READY**（不是 SECURITY APPROVED）
> 含义      = 取证与方案已齐备，等待 Human Security Decision；本报告不产生任何授权
> 基线      = HEAD c420403d… · migration 0017_p13_seed · DB 0017_p13_seed · tags 9
> 本轮未做   = CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0 ·
>             无 DDL / DML / migration / runtime code / API / CLI · 未 commit/tag/push
> ```

---

# 1. Baseline（Phase 2 只读实测）

```text
HEAD            = c420403d5469241e8b03855428ebce435d539c9e
branch          = main · tags = 9 · remote = 0 · dirty = 130
migration head  = 0017_p13_seed · versions = 17 · 0018+ = 0
database        = alembic_version = 0017_p13_seed
```

---

# 2. Current Roles

```text
4 个非内建角色（实测 pg_roles）：

  uap            super=true  createdb=true  createrole=true  replication=true  bypassrls=true  canlogin=true
                 （集群引导 / deployment-ops authority · D-OP101-04）
  uap_seed       NOSUPERUSER · NOCREATEDB · NOCREATEROLE · NOREPLICATION · NOBYPASSRLS · LOGIN
                 （RM-D 种子角色 · 当前零权限）
  uap_migrator   NOSUPERUSER · NOCREATEDB · NOCREATEROLE · NOREPLICATION · NOBYPASSRLS · LOGIN
                 （唯一 migration execution identity）
  uap_app        NOSUPERUSER · NOCREATEDB · NOCREATEROLE · NOREPLICATION · NOBYPASSRLS · LOGIN
                 （唯一 runtime identity）

user-defined role membership = 0（pg_auth_members 共 3 行，全为 PG 内建）
```

---

# 3. Current Grants

```text
表级（non-owner 口径）
  uap_app（恰 5 项）: alembic_version:SELECT · audit_logs:INSERT,SELECT ·
                      audit_logs_202609:INSERT,SELECT
  对 15 张关键表（users / identities / credentials / devices / sessions / roles / tenants /
  spaces / platform_memberships / tenant_memberships / memberships / resource_permissions /
  events / agents / platform_state）**全部 False（含 SELECT）**
  uap_seed : 表级 0 项（全表全动词 False）
  uap_migrator : 245 行（对象自持导致的 relacl 实体化，非外部授予）

schema 级
  public nspacl = {pg_database_owner=UC/pg_database_owner, =U/pg_database_owner, uap_app=U/pg_database_owner}
  ⇒ uap_app 仅 USAGE；**CREATE = false**（含 uap_migrator · 窗口期已回收）

序列（sequence）授予
  public 序列数 = 0 ⇒ 无序列授权面

函数 EXECUTE
  uap_app = 0 · uap_seed = 0 · uap_migrator = 22（自持实体化）
```

---

# 4. Current Ownership / Default ACL / Trigger / RLS

```text
Ownership
  pg_class（public, r/p/i/I）= 156 → 全部 owner = uap_migrator（残留 0）
  pg_proc（public）        = 22  → 全部 owner = uap_migrator

Default ACL
  pg_default_acl = 0（无任何默认授权 ⇒ 未来新对象不自动继承权限）

Trigger state
  父级（非内部）= 39 · 非内部合计 = 40（含 1 个分区克隆）
  关键：tg_acl_subject_types_protect(C2/CC-7) · tg_audit_immutable · tg_pm_bootstrap_gate ·
        tg_roles_is_system_protect · membership scope 族 —— 全部 enabled

RLS state
  relrowsecurity = true 的表 = **0**（未启用 RLS）
  （与 OQ-P14-05 的"不使用 DB RLS 作为主授权机制"一致）
```

---

# 5. Runtime Required Access 与 Gap（Phase 3/4/5）

```text
详细矩阵见 P14_RUNTIME_PRIVILEGE_MATRIX.md（REQUIRED 24 项 · UNKNOWN 一律 DENY）

CURRENT vs REQUIRED（uap_app 口径）
  missing SELECT : users · identities · credentials · devices · sessions · roles · permissions ·
                   role_permissions · acl_subject_types · resource_permissions
                   （**注意：连授权判定所需的只读都不具备**）
  missing INSERT : users · identities · credentials · devices · sessions
  missing UPDATE : users · identities · credentials · devices · sessions
  missing DELETE : sessions
  missing EXECUTE: 无（runtime 不调用 DB 函数）
  already present: audit_logs(S,I) · alembic_version(S) · schema USAGE

GAP 规模（候选）：约 10 项 SELECT + 5 项 INSERT + 5 项 UPDATE + 1 项 DELETE
  ⇒ 若全部授予 uap_app，将使其授权面从 5 项扩至 ~26 项，
    与 OQ-P14-13 已冻结的 OPTION B（Trusted Internal Service Boundary）**方向相反**
    ⇒ 本 gap **不应以直接扩权方式闭合**；解决方式 = 受信内部边界（见 §8 MODEL C）

UNKNOWN（按 DENY 处理 · 需 Human 明确）
  tenants / spaces / tenant_memberships / memberships（P13 留白）
  credentials.DELETE · resource_permissions 写侧 · events · resources
```

---

# 6. Threat Model（本 Gate 关注面 · 分析）

```text
T-1  runtime 越权直写平台受控面（registry / roles / permissions / role_permissions）
     ⇒ 缓解：platform-controlled 默认禁写（Contract §12 + 本报告 §9）
T-2 runtime 冒用 migration 身份（复用 uap_migrator / SET ROLE / 继承 migration privilege）
     ⇒ 缓解：TR-1/TR-2 + Contract §12 PB-3；验证见 §7
T-3 以 application_name / GUC / 会话变量 / 触发器禁用伪造信任
     ⇒ 缓解：D-P13-15 明令禁止；CC-7 判据基于 current_user ∧ session_user
T-4 凭据泄露（明文 / 可逆 / 写日志）
     ⇒ 缓解：OQ-P14-02（Argon2id hash · rotation/revoke/expire · 禁 plaintext · 禁写日志）
T-5 设备/会话跨用户绑定
     ⇒ 缓解：OQ-P14-03（1 Device : 1 User · revoke 同事务撤销 sessions）
T-6 以 DB 权限替代业务授权（把"能连库"当作"有业务权限"）
     ⇒ 缓解：Contract §6 AC-3 + §12 的"两层分离"（见 §12）
T-7 bootstrap 被二次执行或经网络触发
     ⇒ 缓解：OQ-P14-09（local CLI · one-time · state lock · 无公开 endpoint）
T-8 审计面与运维日志混用导致审计不可靠
     ⇒ 缓解：OQ-P14-11（分离）+ tg_audit_immutable
```

---

# 7. Trust Boundary Test（Phase 7）

```text
必须成立（当前均成立，且本轮未改变）：
  · uap_migrator = migration-only trust（CC-7 受信分支：current_user = session_user = 'uap_migrator'）
  · uap_app      = runtime application role（当前仅 audit/alembic 读 + 审计写）
  · runtime principal（未来）= runtime trust（尚未创建）

绝不能发生（本轮只读验证，未触发）：
  × runtime → uap_migrator（身份切换 / 复用其凭据）
  × runtime → migration privilege inheritance（角色成员关系 / GRANT 传递）
  × 以 application_name / GUC / session variable / trigger disable 伪造信任

验证手段（未来实施后须执行，本轮不执行）：
  · 负向探针：runtime principal 尝试 SET ROLE uap_migrator ⇒ 必须失败
  · 负向探针：runtime principal 对 registry INSERT/DELETE ⇒ 必须被 C2 拒
  · 正向断言：runtime principal 连接身份 ≠ uap_migrator（current_user / session_user）
```

---

# 8. Principal Architecture Options（Phase 6 · **不选择**）

## MODEL A — uap_app direct least-privilege runtime access

```text
描述        : 直接把 §5 的 REQUIRED 集授予 uap_app，由 uap_app 承担全部 runtime 访问。
security isolation  : 低（runtime 与现有 application role 合一，权限面显著扩大）
blast radius        : 大（uap_app 被攻破即可写身份/凭据/会话）
credential separation: 无（单一 runtime 凭据）
rotation            : 需轮换 uap_app 凭据（影响面广）
auditability        : 中等（可审计，但无法区分"哪个组件"用了同一身份）
deployment complexity: 低
multi-instance      : 良好（无状态共享凭据）
future scalability  : 差（权限面随功能增长持续膨胀）
CC-7 兼容           : 兼容（不触碰 registry）
P14 Contract 兼容    : **与 OQ-P14-13 = OPTION B 方向相反**（Contract §12 PB-1/PB-2 明确
                      "uap_app 保持当前最小权限""不授予宽泛 DB 写权限"）
```

## MODEL B — dedicated runtime principal

```text
描述        : 新建专用 runtime 角色（如 uap_runtime），按最小集授予所需读写；
              uap_app 维持现状或退役。
security isolation  : 中—高（runtime 身份与迁移/既有角色分离）
blast radius        : 中（受限于专用角色的最小集）
credential separation: 有（独立凭据）
rotation            : 可独立轮换
auditability        : 高（身份可区分）
deployment complexity: 中（新增凭据分发与配置）
multi-instance      : 良好
future scalability  : 中—好（可按功能增授，但仍需逐表维护）
CC-7 兼容           : 兼容
P14 Contract 兼容    : 与 Contract §12 PB-4（"独立 runtime / trusted service principal"）一致；
                      但 Contract §12 PB-5/PB-6 要求"新 role/GRANT 不并入本轮，
                      须另开 Privilege / Security Gate" ⇒ 本模型即该 Gate 的候选
```

## MODEL C — service boundary + dedicated runtime principal

```text
描述        : 受信内部服务边界（Contract §7 SC-2 的 services 层）+ 专用 runtime principal；
              写路径经受信边界执行，principal 仅持该边界所需的最小集。
security isolation  : 高（读写路径分离；边界可单独审计与限流）
blast radius        : 小（runtime 进程侧权限最小；权限集中在受信边界）
credential separation: 有（边界凭据 vs 服务凭据可分离）
rotation            : 可分段轮换
auditability        : 最高（边界是唯一高权限入口，审计点集中）
deployment complexity: 高（新增边界组件/角色与凭据托管）
multi-instance      : 良好（边界可水平扩展）
future scalability  : 好（新增能力只需扩展边界）
CC-7 兼容           : 兼容
P14 Contract 兼容    : **与 OQ-P14-13 = OPTION B（Trusted Internal Service Boundary）直接对应**；
                      亦与 Contract §7 SC-1/SC-2（handler 不直接 SQL · services 编排）一致
```

```text
⇒ 三模型的取舍（隔离强度 vs 复杂度）差异明显；**本报告不选择**。
   注意：Contract §12 PB 已冻结"uap_app 保持最小权限 + 独立 principal + 新 role/GRANT 另开 Gate"，
   MODEL A 与该冻结表述存在直接张力（需 Human 在 Security Decision 中确认或重述）。
```

---

# 9. Sensitive Operations（Phase 9 · 分类判定）

```text
操作类别                      判定                         依据
---------------------------   ---------------------------   --------------------------------
credential writes             trusted service（受信边界）    OQ-P14-02 · Contract §4
user deletion                 operator-only / 不提供         P14 Contract 无删除主体需求
membership changes            UNKNOWN（见 §5）               P13 留白 · P14 未裁
platform membership changes   operator-only（bootstrap CLI） OQ-P14-09 · R4/R5
role changes                  **Runtime 不得写**（platform-controlled）
permission changes            **Runtime 不得写**（platform-controlled）
audit writes                  direct runtime（已具备）        Contract §11 OB-6
session revocation            trusted service               OQ-P14-03（同事务撤销）
bootstrap                     operator-only（local CLI）     OQ-P14-09

platform-controlled（默认 Runtime 禁写 · 除非另有冻结 Decision）：
  permission catalog（permissions 表）· role_permissions · acl_subject_types · migration registry
  ⇒ 本轮无任何冻结 Decision 授权 Runtime 写上述任一对象
```

---

# 10. Bootstrap Privilege（Phase 10）

```text
bootstrap 需要写哪些对象？
  · platform_memberships（插入首行）
  · platform_state（uninitialized → initialized）
  · audit_logs（action = 'platform.admin.bootstrap'）

这些权限由谁持有？
  · **不由 uap_app 持有**（实测 platform_memberships / platform_state 对 uap_app 全 False）
  · 依 OQ-P14-09 = local operator-controlled CLI ⇒ 由**受信 CLI 执行身份**持有
    （其身份形态属本 Gate 的待裁项：复用 deployment authority uap / 专用 bootstrap 凭据 / 其他）

bootstrap credential 从哪里来？
  · UNKNOWN（未裁）—— 属本 Gate 的 Decision 项

bootstrap 完成后如何撤销/锁定？
  · R4/R5 既有语义：成功即路径永久关闭（platform_state = initialized 为权威判据 +
    platform_memberships 非空为次前置）；无恢复 API

bootstrap 是否还能执行第二次？
  · 不能（tg_pm_bootstrap_gate 强制；条件 = uninitialized AND PM 无行）

fail-closed 要求：
  · 任一条件不满足 ⇒ 拒绝；失败整体回滚；不得留下半成品
```

---

# 11. Identity Security（Phase 11）

```text
对象 × 动作矩阵（依 OQ-P14-01/02/03 与 Contract §3–§5）

              create        read          update        revoke        expire        delete
user          REQUIRED      REQUIRED      REQUIRED      -             -             NOT REQUIRED
identity      REQUIRED      REQUIRED      REQUIRED      -             -             NOT REQUIRED
credential    REQUIRED      REQUIRED      REQUIRED      REQUIRED      REQUIRED      UNKNOWN
device        REQUIRED      REQUIRED      REQUIRED      REQUIRED      -             NOT REQUIRED
session       REQUIRED      REQUIRED      REQUIRED      REQUIRED      REQUIRED      REQUIRED

不变式（须在实施后验证；本轮不执行）
  secret plaintext = 0
  secret logging   = 0
  credential reuse = 0
  device cross-user binding = 0
  session cross-user binding = 0
```

---

# 12. Authorization Runtime Precheck（Phase 12）

```text
必须遵循的调用链（Contract §6 AC-1/AC-2 + §7 SC-1）：
  request → authentication → authorization precheck → service/use-case → database access

禁止：
  × handler → SQL（跳过 precheck 与服务层）
  × database permission → replace application authorization

两层职责分离（不得互相替代）：
  · 数据库权限回答：who may access DB operation（机制层）
  · Application authorization 回答：who may perform business action（业务层）
  ⇒ 两者必须同时成立；任一单独成立都不足以放行。
```

---

# 13. Audit Boundary（Phase 13 · 仅形成规则 · 不写审计）

```text
操作类别 → 输出面归属（规则 · 待实施轮落地）

操作                           operational log   audit event   说明
---------------------------    ---------------   -----------   --------------------------------
服务启动 / 配置加载             必须              —            运维面
readiness / liveness 探针       必须              —            运维面（D-PLAT-14/16）
请求级追踪（request/corr ID）    必须              —            OQ-P14-11
主体建立（onboarding 成功）      必须              必须          审计：主体生命周期（action 待定）
凭据建立 / 轮换 / 撤销 / 到期     必须              必须          审计：凭据生命周期（action 待定）
设备 enrollment / revoke        必须              必须          审计：设备生命周期（action 待定）
会话建立 / 撤销                 必须              按裁定         取决于是否纳入审计范围（未裁）
授权拒绝（default deny 命中）    必须              必须          审计：安全事件
bootstrap                       必须              必须          action = 'platform.admin.bootstrap'（R4/R5 既有）
平台受控面写尝试（应失败）        必须              按裁定         拒绝事件（若纳入）

约束：
  · 不修改 audit_logs schema
  · 本轮不写 audit_logs
  · operational logs 与 audit_logs **分离**（OQ-P14-11）
  · 具体 action 字符串与条数 → 属实施轮契约细化（不得在此固化未裁内容）
```

---

# 14. Fail-Closed Rules（汇总）

```text
FC-1 未知权限组合 ⇒ 拒绝（unknown = DENY）
FC-2 非 REQUIRED 组合 ⇒ 拒绝（unneeded = DENY）
FC-3 授权判定依赖不可用 / 不确定 ⇒ 拒绝（D-AUTH-12）
FC-4 事务失败 ⇒ rollback（不留半成品）
FC-5 bootstrap 条件不满足（已初始化 / PM 非空）⇒ 拒绝，且路径永久关闭
FC-6 设备撤销 ⇒ 同事务撤销其 active sessions；失败则整体回滚
FC-7 迁移身份 / 受控面写入尝试 ⇒ 拒绝并（按裁定）记录
FC-8 任何需要新授权的操作在授权前 ⇒ 拒绝
```

---

# 15. Security Preconditions（进入实施前必须满足）

```text
SP-1  Human Security Decision 已下达：选定 principal 模型（A / B / C / CUSTOM）
SP-2  若选 B/C：专用 runtime principal 的形态、凭据托管、轮换方式已定
SP-3  最小权限集已由 Human 逐项确认（本报告 §5 + MATRIX 的 REQUIRED 24 项，
      其中 UNKNOWN 项须先裁定）
SP-4  bootstrap 执行身份与凭据来源已定（§10 的两个 UNKNOWN）
SP-5  UNKNOWN 项（tenants/spaces/memberships/events/resources/credential DELETE/
      resource_permissions 写侧）已逐项裁定
SP-6  OI-G-1 处置结论已定（见 §16）
SP-7  授权执行轮（GRANT / CREATE ROLE）已**另行**获得授权
      —— 本轮明确不执行
```

---

# 16. OI-G-1 状态（Phase 14）

```text
OI-G-1 = 「runtime 逐表 DML 矩阵不可核定（不得扩权）」· 原状态 REGISTERED（BATCH-D）

本轮评估：
  · 已产出 P14_RUNTIME_PRIVILEGE_MATRIX.md（逐表 × 逐动词 × use-case × 理由）
    ⇒ 具备"矩阵候选"证据
  · 但矩阵中仍有 **UNKNOWN 项**（tenants/spaces/memberships/events/resources/
    credential DELETE/resource_permissions 写侧）**未裁**
  · 且 principal 模型未选定（§8）

⇒ 依"本轮不得关闭 OI-G-1，除非现有证据已经完整证明"：
   **OI-G-1 = ACTIVE（保持 OPEN）**
   本轮的 privilege matrix = 其**正式更新证据候选**（登记备案，不构成关闭）
```

---

# 17. 本轮工程变更

```text
CREATE ROLE = 0 · ALTER ROLE = 0 · GRANT = 0 · REVOKE = 0 · ALTER DEFAULT PRIVILEGES = 0
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · API = 0 · CLI = 0
新增文档 = 本报告 + P14_RUNTIME_PRIVILEGE_MATRIX.md + P14_RUNTIME_IMPLEMENTATION_PREFLIGHT.md
commit = 0 · tag = 0 · push = 0
```

---

**END OF P14 PRIVILEGE / SECURITY GATE REPORT（2026-09-27 · **DECISION READY**（非 SECURITY APPROVED）· OI-G-1 = ACTIVE · 未执行任何授权动作）**
