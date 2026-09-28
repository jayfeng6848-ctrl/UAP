# UAP — P14 SECURITY IMPLEMENTATION REPORT

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY IMPLEMENTATION（独立 Security Implementation Gate）
> 状态      = **IMPLEMENTED**（数据库安全边界已落地并通过验证）
> 明确不是   = P14 RUNTIME IMPLEMENTED（Runtime application 未开始）
> 基线      = HEAD c420403d5469241e8b03855428ebce435d539c9e · migration 0017_p13_seed
> 目标库    = uap_b1_test（集群级角色变更影响全集群角色拓扑）
> 本轮未做   = 未创建 runtime code / API / CLI / onboarding / bootstrap CLI /
>            0018+ migration · 未 commit / tag / push · 未进入 P15
> ```

---

# 1. Implementation Authorization Evidence

```text
授权来源 = Human 指令「P14 — SECURITY IMPLEMENTATION + SECURITY ACCEPTANCE GATE」（2026-09-27）
授权原文（逐字）：
  · 「现在进入：**P14 SECURITY IMPLEMENTATION**」
  · 「# 0. 最重要的授权条件：本任务允许执行真正的：
       * CREATE ROLE · * ALTER ROLE · * GRANT · * REVOKE · * 安全相关 DDL ·
       * Security privilege probes · * 权限验证」
  · 同条 §0 的条件：「只有在当前执行上下文已经由 Human 明确授权 P14 SECURITY IMPLEMENTATION
       的情况下才能进行实际数据库 mutation」⇒ 该条件由上述指令本身满足
    （指令声明进入该阶段并明确允许上述 mutation，且给出 §一 实施目标与 §八 Grant Matrix 第一权威）
未依赖  = 「Security Implementation Gate = READY」作为授权依据（未发生该误用）
实施身份 = `uap`（deployment-ops authority · D-OP101-04）执行 CREATE ROLE / GRANT
```

---

# 2. Pre-State（§三 baseline · 只读实测）

```text
Git  : HEAD c420403d… · branch main · tags 9 · remote 0 · staged 0 · dirty 141
       历史 dirty set 已保存至仓库外 work/p14_secpre_dirty.txt（未被清理 / 未被 stage）
DB   : alembic 0017_p13_seed · migration files 17 · 0018+ = 0
       roles = 4（uap / uap_app / uap_migrator / uap_seed）
       pg_auth_members total = 3（全内建）· user-defined membership = 0
       uap_app grants = 5 · uap_seed grants = 0 · uap_migrator grants = 245
       pg_default_acl = 0 · pg_class public = 156 · pg_proc public = 22
       registry / permissions / role_permissions = 3 / 12 / 12
       C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff
       public nspacl = {pg_database_owner=UC, =U, uap_app=U}
```

---

# 3. Role Creation Evidence（§四 / §五 / §六）

```text
Role naming gate：
  · 仓库无 canonical runtime/bootstrab principal 命名约定（仅 Gate Report 中出现过 "uap_runtime" 举例）
  ⇒ 采用最小、可审计、与既有 `uap_*` 一致的 deterministic 名：
       chosen implementation identifier #1 = `uap_runtime`   （DEDICATED RUNTIME PRINCIPAL）
       chosen implementation identifier #2 = `uap_bootstrap` （DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL）
  · 未由名字衍生任何新权限语义；未复用 uap_app / uap_migrator / uap_seed
  · 两个角色**互相独立**，未互为继承

创建（identity = uap/uap）：
  CREATE ROLE uap_runtime   LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
  CREATE ROLE uap_bootstrap LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS

角色总数 = 6（预期 6）；unexpected roles = 0
```

---

# 4. Role Attributes（catalog 实测）

```text
rolname        | rolsuper | rolcreatedb | rolcreaterole | rolinherit | rolreplication | rolbypassrls | rolcanlogin
uap_bootstrap  |    f     |      f      |       f       |     f      |       f        |      f       |     t
uap_runtime    |    f     |      f      |       f       |     f      |       f        |      f       |     t
```

```text
⇒ NOSUPERUSER / NOCREATEDB / NOCREATEROLE / NOINHERIT / NOREPLICATION / NOBYPASSRLS 全部满足
⇒ LOGIN = true（依 Connection Security Note 的认证边界；无宽泛管理员属性）
⇒ schema CREATE = false（负向探针 NP-R7/NP-B2 实测被拒）
```

---

# 5. Membership Evidence（§七）

```text
user-defined role memberships = 0（实施后实测）
负向断言（pg_has_role）：
  uap_runtime  → uap_migrator / uap_app / uap_seed / uap_bootstrap = (False, False, False, False)
  uap_bootstrap→ uap_migrator / uap_runtime / uap_app              = (False, False, False)
  uap_app      → uap_runtime / uap_bootstrap                       = (False, False)
  uap_migrator → uap_runtime / uap_bootstrap                       = (False, False)
⇒ 未使用任何 role inheritance / group role 扩权；全部权限为 direct exact grants
```

---

# 6. Exact Grant Evidence（§八 / §九 / §十）

```text
第一权威 = P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md（逐行执行 · 无现场新增权限）

uap_runtime（51 row-grants）
  SELECT ×26 = users, identities, credentials, devices, sessions, tenants, spaces,
               tenant_memberships, memberships, roles, permissions, role_permissions,
               acl_subject_types, resource_permissions, events, resources, audit_logs,
               platform_state, platform_memberships, agents, agent_versions,
               agent_permissions, tools, alembic_version
               + audit_logs_202609, events_202609（分区，逐分区）
  INSERT ×12 = users, identities, credentials, devices, sessions, tenant_memberships,
               memberships, events, resources, audit_logs
               + audit_logs_202609, events_202609（分区）
  UPDATE ×10 = users, identities, credentials, devices, sessions, tenant_memberships,
               memberships, events, resources + events_202609（分区）
  DELETE ×3  = sessions, tenant_memberships, memberships
  + schema USAGE on public

uap_bootstrap（6 row-grants）
  platform_state        : SELECT, UPDATE
  platform_memberships  : SELECT, INSERT
  audit_logs            : INSERT
  audit_logs_202609     : INSERT
  + schema USAGE on public

未变更
  uap_app     = 5（未增未减）· uap_seed = 0 · uap_migrator = 245（未变）
  pg_default_acl = 0（未使用 ALTER DEFAULT PRIVILEGES）

禁止项核验：无 GRANT ALL · 无 `<schema> ALL` · 无 `ON ALL TABLES` · 无 role inheritance 扩权
```

---

# 7. Positive Assertions（§十九）

```text
catalog 断言（has_table_privilege）26 项逐项 OK（含 12 项应 True、14 项应 False）
  USAGE=True / CREATE=False · users(S,I,U)=True, users(D)=False · credentials(U)=True, credentials(D)=False ·
  sessions(D)=True · tenants(S)=True, tenants(I)=False · spaces(U)=False ·
  resource_permissions(S)=True, (I)=False · platform_state(S)=True, (U)=False ·
  platform_memberships(S)=True, (I)=False · audit_logs(I)=True, (U,D)=False ·
  events(U)=True, (D)=False · roles(S)=True, (I)=False · acl_subject_types(S)=True, (I)=False ·
  alembic_version(S)=True

事务内 DML 正向证明（BEGIN → 断言 → ROLLBACK，无残留）
  PA-R2  users      INSERT → ALLOWED → rollback ✔
  PA-R3  audit_logs INSERT → ALLOWED → rollback ✔
  PA-R2  events     INSERT → ALLOWED → rollback ✔

Bootstrap 正向断言（catalog · 依"路径依赖未实现 CLI 时允许 DATABASE PRIVILEGE ASSERTION"）
  PA-B: platform_state SELECT/UPDATE = True,True · platform_memberships SELECT/INSERT = True,True ·
        audit_logs INSERT = True · schema USAGE/CREATE = True,False  ⇒ 5/5 OK
```

---

# 8. Negative Probes（§二十）

```text
Runtime principal（NP-R1…R13）· 共 38 次尝试 · unexpected ALLOWED = **0**
  NP-R1 resource_permissions INSERT/UPDATE/DELETE → DENIED ×3
  NP-R2 credentials DELETE                      → DENIED
  NP-R3 tenants INSERT/UPDATE/DELETE            → DENIED ×3
  NP-R4 spaces INSERT/UPDATE/DELETE             → DENIED ×3
  NP-R5 platform_state INSERT/UPDATE/DELETE     → DENIED ×3
  NP-R6 platform_memberships INSERT/UPDATE/DELETE → DENIED ×3
  NP-R7 CREATE TABLE / ALTER TABLE / DROP TABLE / CREATE SCHEMA → DENIED ×4
  NP-R9 SET ROLE uap_migrator → DENIED；CREATE ROLE → DENIED；4 项 pg_has_role 全 False
  NP-R10 roles / permissions / role_permissions 写 → DENIED ×5
  NP-R11 acl_subject_types INSERT/UPDATE/DELETE → DENIED ×3
  NP-R12 audit_logs UPDATE/DELETE → DENIED ×2
  NP-R13 events / resources DELETE → DENIED ×2

uap_app（NP-A1…A3）· unexpected ALLOWED = 0
  grants = 5（未变）· CREATE = false · 无 membership · users SELECT/INSERT、credentials INSERT → DENIED

uap_migrator（NP-M1…M3）
  属性未变（NOSUPERUSER · NOCREATEDB · NOCREATEROLE）· CREATE = false · C2 md5 未变 ·
  无 runtime/bootstrap membership · grants = 245（未变）· 未被用作 runtime 身份

Bootstrap principal（NP-B1…B4）· 共 10 次尝试 · unexpected ALLOWED = 0
  NP-B1 users / credentials / tenants 写 → DENIED ×3（broad CRUD 被拒）
  NP-B2 CREATE TABLE / ALTER TABLE / SET ROLE uap_migrator → DENIED ×3
  NP-B3 resource_permissions INSERT / DELETE → DENIED ×2
  NP-B4 roles INSERT / platform_memberships DELETE / platform_state DELETE → DENIED ×3
        + membership(bp→migrator/runtime/app) 全 False
```

---

# 9. Revoke / Rollback Evidence（§二十二）

```text
对象/动词 = `public.tools` / SELECT（uap_runtime）
  pre-state          : SELECT=True · runtime row-grants = 51
  mutation (REVOKE)  : REVOKE SELECT ON TABLE public.tools FROM uap_runtime
  verification       : SELECT=False · row-grants = 50
  rollback (re-GRANT): GRANT SELECT ON TABLE public.tools TO uap_runtime
  post-state         : SELECT=True · row-grants = 51
  ⇒ RESULT = PASS（权限可被**精确**回收并可复原）
  · 未使用 `REVOKE ALL` 作为回滚方式（按对象/动词精确回收）
  · 最终净变更 = 0（无 unexpected REVOKE 残留）
```

---

# 10. C2 / CC-7 Compatibility（§十七）

```text
C2 md5（实施后）= 185e95be8bc4304edbcd3f4d5cda1eff —— 与实施前**一致**
CC-7           = 未修改（受信分支语义不变）
Runtime principal 对 acl_subject_types = **SELECT only**（无 INSERT/UPDATE/DELETE）
  ⇒ Runtime 权限与信任**不依赖** C2 / CC-7
  ⇒ 未要求修改 C2 / CC-7 / migrator ownership / 未给 runtime migration function access
⇒ C2 Compatibility = PASS · CC-7 Compatibility = PASS
```

---

# 11. Protected Object Integrity（§二十四）

```text
0017_p13_seed.py                   sha256 1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e（未变）
0016_open_p10_1_trust_boundary.py  sha256 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544（未变）
env.py                             sha256 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a（未变）
P13 schema objects                 pg_class 156 · pg_proc 22（未变）
P13 seed data                      registry/permissions/role_permissions = 3/12/12（未变）
C2 / CC-7                          md5 未变
ownership                          owner residual = 0 · 全部仍归 uap_migrator
⇒ drift = 0
```

---

# 12. DB Residue（§二十三）

```text
expected new roles      = 2 → actual 2（uap_runtime · uap_bootstrap）· unexpected = 0
expected new memberships = 0 → actual 0 · unexpected = 0
expected grants         = runtime 51 + bootstrap 6 = 57 → actual 57 · unexpected = 0
unexpected REVOKE       = 0（rollback 后净零）
unexpected ownership    = 0 · unexpected DDL = 0（pg_class/pg_proc 未变）
unexpected data mutation = 0（用户/审计/事件/资源/凭据/设备/会话/身份 均为 0；
                            platform_state 仍 1 行 uninitialized；platform_memberships 仍 0）
0018+                   = 0
pg_default_acl          = 0

schema public nspacl（实施后）
  {pg_database_owner=UC, =U, uap_app=U, uap_runtime=U, uap_bootstrap=U}
  ⇒ 新增仅 2 项 USAGE（预期内）；未新增任何 schema CREATE
```

---

# 13. OI-G-1 Status（§二十七）

```text
关闭条件逐项核对：
  1. dedicated Runtime principal 已实际创建            ✔（uap_runtime）
  2. Bootstrap principal 已实际创建                    ✔（uap_bootstrap）
  3. Exact grants 已实际授予                           ✔（51 + 6 · 逐操作）
  4. actual catalog evidence 完整                      ✔（pg_roles / pg_auth_members /
                                                         role_table_grants / nspacl /
                                                         pg_default_acl / ownership / 函数权限）
  5. Negative probes 完整                              ✔（38 + 3 + 2 + 10 = 53 次尝试 · 0 意外放行）
  6. Positive assertions 完整                          ✔（26 catalog + 3 wrapped DML + BP 5 项）
  7. 无 UNKNOWN                                        ✔
  8. 无 unexpected privilege                           ✔
  9. 无 C2 / CC-7 drift                                ✔
 10. Security Acceptance 已 PASS                       ✔（见 P14_SECURITY_ACCEPTANCE_REPORT.md）
⇒ **OI-G-1 = CLOSED**（全部 10 项条件满足；关闭依据为上述可复核证据，非"为了 Gate 好看"）
   注：Runtime 业务实现（onboarding / session / CLI）尚未开始，其**新增**权限需求若出现，
       须重新开启相应 Security Decision，不得沿用本轮的"已关闭"状态自动扩权。
```

---

# 14. Final Security Gate

```text
FINAL GATE — P14 SECURITY IMPLEMENTATION

Authorization Evidence           = PASS
Runtime Principal                = PASS（uap_runtime）
Bootstrap Principal              = PASS（uap_bootstrap）
Role Security Attributes         = PASS（NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOINHERIT/
                                        NOREPLICATION/NOBYPASSRLS · LOGIN · CREATE=false）
Exact Grant Implementation       = PASS（第 Matrix 逐行 · 57 row-grants · 无宽泛授权）
Runtime Positive Assertions      = PASS（26 catalog + 3 wrapped DML）
Runtime Negative Probes          = PASS（38 次尝试 · 0 意外放行）
Bootstrap Positive Assertions    = PASS（5 项 catalog 断言）
Bootstrap Negative Probes        = PASS（10 次尝试 · 0 意外放行）
uap_app Isolation                = PASS（grants 5 未变 · CREATE false · 无 membership）
uap_migrator Isolation           = PASS（属性/权限/边界未变 · grants 245 未变）
Default ACL Integrity            = PASS（pg_default_acl = 0）
C2 Compatibility                 = PASS
CC-7 Compatibility               = PASS
Rollback / Revoke Evidence       = PASS（逐对象/动词精确回收 + 复原）
Privilege Residue Scan           = PASS
Protected Object Integrity       = PASS
Security Acceptance              = PASS

Unexpected Roles                 = 0
Unexpected Memberships           = 0
Unexpected Grants                = 0
Unexpected REVOKE                = 0
DB Data Residue                  = 0

OI-G-1                           = CLOSED
Runtime Code Implementation      = NOT STARTED
Database Onboarding              = NOT STARTED
Bootstrap CLI                    = NOT STARTED

P14 SECURITY IMPLEMENTATION      = PASS

COMMIT                           = FORBIDDEN（本轮未执行）
TAG                              = FORBIDDEN（本轮未执行）
PUSH                             = FORBIDDEN（本轮未执行）
P15                              = FORBIDDEN（未进入）

HARD STOP                        = ACTIVE
```

---

**END OF P14 SECURITY IMPLEMENTATION REPORT（2026-09-27 · **IMPLEMENTED** · 2 principals + 57 exact grants · 53 negative probes 0 意外放行 · OI-G-1 = CLOSED · Runtime Code / Onboarding / Bootstrap CLI = NOT STARTED）**
