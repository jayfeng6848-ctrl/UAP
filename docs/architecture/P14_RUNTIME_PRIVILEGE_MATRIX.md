# UAP — P14 RUNTIME PRIVILEGE MATRIX

> ## 状态与边界
>
> ```text
> 轮次      = P14 PRIVILEGE / SECURITY GATE（Phase 8）
> 性质      = 最小权限矩阵（分析产物）· 状态 = **HUMAN-DECISION-RESOLVED / IMPLEMENTATION INPUT**
>             （2026-09-27 由 PROPOSED 推进；依 SEC-P14-01…14 裁决重算 · **仍非已授予权限**）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · DB 0017_p13_seed
> 依据      = PDL 附录 N（15 项 HUMAN DECISION）· P14 Implementation Contract（FROZEN）
> 本轮未做   = 未执行 GRANT / REVOKE / CREATE ROLE / ALTER DEFAULT PRIVILEGES ·
>             无 DDL / DML / migration / runtime code · 未 commit/tag/push
> 铁律      = **unknown = DENY · unneeded = DENY**；禁止 GRANT ALL · schema-wide write ·
>             table-wide unnecessary DELETE · migration-role reuse
> ```

---

# 1. Runtime use-case 清单（来源：Contract §3–§11）

```text
UC-1  staged onboarding：pending → identity verification → credential/device verification
      → activation/session（Contract §3 IC-1/IC-2）
UC-2  credential 生命周期：建立（Argon2id hash）/ rotation / revoke / expire（§4）
UC-3  device 绑定与撤销：显式 enrollment/challenge；revoke 同事务撤销 active sessions（§5）
UC-4  authorization 判定：centralized precheck + service/use-case enforcement（§6）
UC-5  session 管理：activation/session 建立与失效（§3 + §5）
UC-6  readiness 探针：读取迁移版本状态（D-PLAT-14/16 · 既有）
UC-7  audit 写入：平台审计事件（Contract §11 OB-6 + 既有 audit 契约）
UC-8  bootstrap：**operator CLI 路径**（§8）—— 不在 runtime principal 面内（见 §4）
```

---

# 2. 逐表最小权限矩阵（REQUIRED / NOT REQUIRED / UNKNOWN）

记法：`R` = REQUIRED · `-` = NOT REQUIRED · `?` = UNKNOWN（**按 DENY 处理**）

```text
表                        SELECT  INSERT  UPDATE  DELETE   依据 / 说明
-----------------------   ------  ------  ------  ------   ------------------------------------
users                       R       R       R       -      UC-1 建立主体 + status 状态机推进
identities                  R       R       R       -      UC-1 identity verification / 绑定
credentials                 R       R       R       ?      UC-2 hash 建立/轮换/撤销；DELETE = ?
devices                     R       R       R       -      UC-3 enrollment / revoke（撤销用 UPDATE）
sessions                    R       R       R       R      UC-5 建立/失效；device revoke 同事务撤销
tenants                     ?       ?       ?       ?      P13 留白（见 §5 UNKNOWN 登记）
spaces                      ?       ?       ?       ?      同上
tenant_memberships          ?       ?       ?       ?      同上
memberships                 ?       ?       ?       ?      同上
roles                       R       -       -       -      UC-4 判定需读；**写 = platform-controlled**
permissions                 R       -       -       -      UC-4 判定需读；写 = platform-controlled
role_permissions            R       -       -       -      UC-4 判定需读；写 = platform-controlled
acl_subject_types           R       -       -       -      UC-4 ACL 解析需读；写 = migration-only
platform_memberships        -       -       -       -      UC-8 bootstrap 属 operator 路径（非 runtime）
platform_state              -       -       -       -      同上
resource_permissions        R       ?       ?       ?      UC-4 判定需读；写（grant/revoke）= ?
events                      ?       ?       ?       ?      P10 outbox 是否在 P14 启用 = 未裁
audit_logs                  R       R       -       -      UC-7 写读；不可变⇒无 UPDATE/DELETE
agents                      -       -       -       -      P14 不涉及 agent runtime（P13 仅注册 subject type）
agent_versions              -       -       -       -      同上
agent_permissions           -       -       -       -      同上
tool_executions             -       -       -       -      同上
tools / tool_permissions    -       -       -       -      本阶段不涉及
ai_providers/routes/policies/models - - -   -            本阶段不涉及
resources                   ?       ?       ?       ?      P14 Contract 未涉及资源本体写入
alembic_version             R       -       -       -      UC-6 readiness（既有授权已含）
sequence                    -       -       -       -      public 无序列（实测 0）
函数 EXECUTE                 -       -       -       -      runtime 不调用任何 DB 函数（实测 uap_app = 0）
```

---

# 3. REQUIRED 权限的逐项理由（who / what / on what / use-case / why）

```text
PR-01  users          SELECT  UC-1/UC-5  读取主体以完成 verification / session 建立
PR-02  users          INSERT  UC-1       建立首个可登录主体（staged onboarding）
PR-03  users          UPDATE  UC-1       推进 status（pending → active / suspended / locked）
PR-04  identities      SELECT  UC-1       读取身份记录
PR-05  identities      INSERT  UC-1       建立身份记录
PR-06  identities      UPDATE  UC-1       identity verification 状态推进
PR-07  credentials     SELECT  UC-2       校验凭据（读取 hash）
PR-08  credentials     INSERT  UC-2       建立凭据（Argon2id hash）
PR-09  credentials     UPDATE  UC-2       rotation / revoke / expire
PR-10  devices         SELECT  UC-3       读取设备绑定
PR-11  devices         INSERT  UC-3       enrollment（显式 challenge 通过后）
PR-12  devices         UPDATE  UC-3       revoke（撤销绑定）
PR-13  sessions        SELECT  UC-5       读取会话
PR-14  sessions        INSERT  UC-5       建立会话（activation）
PR-15  sessions        UPDATE  UC-5       会话状态推进 / 失效
PR-16  sessions        DELETE  UC-5       清理失效会话（含 device revoke 同事务撤销）
PR-17  roles           SELECT  UC-4       授权判定需读取角色
PR-18  permissions     SELECT  UC-4       授权判定需读取权限词表
PR-19  role_permissions SELECT UC-4       授权判定需读取绑定
PR-20  acl_subject_types SELECT UC-4      ACL 解析（subject_type 外键解析）
PR-21  resource_permissions SELECT UC-4   ACL 判定读取
PR-22  audit_logs      SELECT  UC-7       审计读取（既有授权已含）
PR-23  audit_logs      INSERT  UC-7       审计写入（既有授权已含）
PR-24  alembic_version SELECT  UC-6       readiness 探针（既有授权已含）
```

```text
备注：以上为**候选**（PROPOSED），不构成授权。任何授权动作须经独立的
      Privilege / Security Gate 决策（见 P14_PRIVILEGE_SECURITY_GATE_REPORT.md）。
```

---

# 4. UNKNOWN 与 NOT REQUIRED 的处置规则

```text
UNKNOWN（一律 DENY，直至 Human 明确）：
  · tenants / spaces / tenant_memberships / memberships（P13 留白，P14 未裁）
  · credentials.DELETE
  · resource_permissions 的 INSERT / UPDATE / DELETE（第三方 grant/revoke 是否属 P14）
  · events（outbox 是否在 P14 启用）
  · resources 本体写入

NOT REQUIRED（明确 DENY）：
  · roles / permissions / role_permissions / acl_subject_types 的任何写
    （platform-controlled · Contract §12 PB + §9 敏感操作）
  · platform_memberships / platform_state 的 runtime 写（bootstrap = operator CLI）
  · audit_logs 的 UPDATE / DELETE（不可变 · tg_audit_immutable）
  · agents / agent_versions / agent_permissions / tool_executions / tools / ai_* 的全部操作
  · 任何 schema DDL（runtime 不持 DDL · D-OP101-08）
  · 任何序列操作（public 无序列）
  · 任何函数 EXECUTE（runtime 不调用 DB 函数）
```

---

# 5. 禁则（矩阵层）

```text
· 禁止 GRANT ALL
· 禁止 schema-wide write（不授予 public schema 上的写/建）
· 禁止 table-wide unnecessary DELETE（仅 sessions 为 REQUIRED，且限定自有语义）
· 禁止复用 migration role（uap_migrator 不得作为 runtime 身份）
· 禁止以 application_name / GUC / 会话变量 / 触发器禁用伪造信任（TR-2）
· 未知即拒绝：任何未列为 REQUIRED 的组合一律 DENY
```

---

# 6. 与既有授权面的关系（对照 · 不执行变更）

```text
uap_app 现状（实测）：audit_logs(S,I) · alembic_version(S) · schema USAGE
本矩阵 REQUIRED 集（候选）远大于现状 ⇒ 形成 gap（见安全门报告 §5）
处置路径（已冻结）：OQ-P14-13 = OPTION B —— 写路径经受信内部边界；
                    runtime principal 与其授权属**独立 Gate**（本矩阵为输入候选之一）
```

---

# 7. 状态

```text
本矩阵状态 = PROPOSED · NOT AUTHORIZED · DECISION READY（供 Security Gate 使用）
本轮：GRANT = 0 · REVOKE = 0 · CREATE ROLE = 0 · DDL/DML = 0
P14 IMPLEMENTATION = NOT AUTHORIZED
```

---

# 8. Resolution Recalculation（append-only · 2026-09-27 · 依 SEC-P14-01…14）

> 本节为**权威重算表**：依 Human 裁决把每对象重算为 `REQUIRED(R)` 或 `DENY`，
> **UNKNOWN 清零**。本节取代 §2 的三态列（§2 保留为历史分析）。
> 本节内容为**授权输入**，**不是已授予权限**；实际 GRANT 须在独立 Security Implementation Gate 授权后执行。

```text
对象                     SELECT   INSERT   UPDATE   DELETE    依据（SEC / 既有冻结）
----------------------   ------   ------   ------   ------    ----------------------------------
users                      R        R        R        DENY     SEC-03/04（staged onboarding）
identities                 R        R        R        DENY     同上
credentials                R        R        R        DENY     SEC-08（NO PHYSICAL DELETE）
devices                    R        R        R        DENY     SEC-04（enrollment · revoke=UPDATE）
sessions                   R        R        R        R        SEC-04（session lifecycle）
tenants                    R       DENY     DENY     DENY     SEC-05（SELECT ONLY）
spaces                     R       DENY     DENY     DENY     SEC-05（SELECT ONLY）
tenant_memberships         R        R        R        R        SEC-06（service-mediated use-case）
memberships                R        R        R        R        SEC-06（service-mediated use-case）
roles                      R       DENY     DENY     DENY     platform-controlled（SEC-09 精神）
permissions                R       DENY     DENY     DENY     platform-controlled
role_permissions           R       DENY     DENY     DENY     platform-controlled
acl_subject_types          R       DENY     DENY     DENY     migration-controlled（C2 / CC-7）
resource_permissions       R       DENY     DENY     DENY     SEC-09（RUNTIME WRITE = DENY）
events                     R        R        R       DENY     SEC-07（DELETE DENY）
resources                  R        R        R       DENY     SEC-07（DELETE DENY）
audit_logs                 R        R       DENY     DENY     不可变（tg_audit_immutable）
platform_memberships       R       DENY     DENY     DENY     SEC-13（bootstrap-owned）
platform_state             R       DENY     DENY     DENY     SEC-13（bootstrap-owned）
agents                     R       DENY     DENY     DENY     SEC-03（subject 解析读取）
agent_versions             R       DENY     DENY     DENY     同上
agent_permissions          R       DENY     DENY     DENY     同上
tools                      R       DENY     DENY     DENY     同上
alembic_version            R       DENY     DENY     DENY     readiness（既有授权已含）
sequence                  DENY     DENY     DENY     DENY     无序列（实测 0）
function EXECUTE          DENY     DENY     DENY     DENY     SEC-14（仅必要时才授予）
```

## 8.1 Who / What / Object / Operation / Why / Boundary / Deny-by-default

```text
Who        : **dedicated runtime principal**（SEC-01 = MODEL C；SEC-02 = 受信内部 Service Boundary
             的数据库身份）—— 该 principal **尚不存在**，由 Security Implementation Gate 创建
What       : 上表所列 R 组合（逐对象 × 逐动词）
Object     : public schema 下的具体表（见上表）
Operation  : SELECT / INSERT / UPDATE / DELETE（逐格明确）
Why        : 每格依据列已指向具体 SEC 裁决或既有冻结约束
Boundary   : Runtime execution trust domain ≠ migration trust（uap_migrator）≠ seed（uap_seed）
             ≠ bootstrap authority（SEC-11）≠ 现状 runtime identity（uap_app）
Deny-by-default : 表中未标 R 的组合全部 DENY；任何新增需求须经独立 Security Review
```

## 8.2 不变式（重算后仍成立）

```text
· uap_app = 保持 5 项授权 + schema USAGE · CREATE = false（**不变**）
· uap_migrator = migration-only（**不被 runtime 使用**）· uap_seed = 不承担 runtime 角色
· 无 GRANT / CREATE ROLE / default ACL 变更（本轮 = 0）
· 禁 GRANT ALL · 禁宽泛 schema write · 禁继承型权限间接扩权（SEC-14）
· UNKNOWN 残留 = 0
```

---

**END OF P14 RUNTIME PRIVILEGE MATRIX（2026-09-27 · **HUMAN-DECISION-RESOLVED / IMPLEMENTATION INPUT** · §8 重算表为权威 · UNKNOWN = 0 · 未执行任何授权）**
