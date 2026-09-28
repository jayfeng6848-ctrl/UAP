# UAP — P14 SECURITY IMPLEMENTATION GRANT MATRIX

> ## 状态
>
> ```text
> 状态        = **IMPLEMENTATION PROPOSAL**（**不是**已实施）
> 依据        = PDL 附录 O（SEC-P14-01…14）· P14_RUNTIME_PRIVILEGE_MATRIX §8（重算表）
> 基线        = HEAD c420403d… · migration 0017_p13_seed · pg_default_acl = 0
> 本轮未做     = CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0 ·
>                DDL / DML = 0 · 本文件仅为设计输入
> 行列规则     = 每行必须是**单一 operation**；凡只能写成 CRUD 或 read/write 的行
>               一律标记 **NOT READY**，须拆为 SELECT / INSERT / UPDATE / DELETE
> ```

## 列定义

```text
Principal | Object | Operation | Reason | Use-case | Trust Boundary |
Required/Not Required | Negative Test | Positive Test | Revocation/Rollback
```

Principal 代号：

```text
RT = dedicated runtime principal（SEC-01 = MODEL C；SEC-02 = Trusted Internal Service Boundary 的 DB 身份）
BP = dedicated one-time bootstrap principal（SEC-11）
-- = NOT REQUIRED（显式拒绝；用于负向基线）
```

---

# 1. Runtime Principal — 读取（REQUIRED）

```text
Principal | Object                | Operation | Reason                          | Use-case   | Trust Boundary     | Req      | NegTest     | PosTest     | Revocation/Rollback
RT        | users                 | SELECT    | 读取主体以完成 verification/会话   | UC-1,UC-5  | Runtime execution  | REQUIRED | NP-R9       | PA-R1/PA-R5 | REVOKE SELECT ON users FROM <rt>
RT        | identities            | SELECT    | 读取身份记录                     | UC-1       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON identities
RT        | credentials           | SELECT    | 校验凭据（读取 hash）             | UC-2       | Runtime execution  | REQUIRED | NP-R2       | PA-R1       | REVOKE SELECT ON credentials
RT        | devices               | SELECT    | 读取设备绑定                     | UC-3       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON devices
RT        | sessions              | SELECT    | 读取会话                         | UC-5       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON sessions
RT        | tenants               | SELECT    | 读取当前 use-case 必需租户上下文    | UC-1, UC-4 | Runtime execution  | REQUIRED | NP-R3       | PA-R1       | REVOKE SELECT ON tenants
RT        | spaces                | SELECT    | 读取当前 use-case 必需空间上下文    | UC-1, UC-4 | Runtime execution  | REQUIRED | NP-R4       | PA-R1       | REVOKE SELECT ON spaces
RT        | tenant_memberships    | SELECT    | 成员关系判定输入                  | UC-4       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON tenant_memberships
RT        | memberships           | SELECT    | 成员关系判定输入                  | UC-4       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON memberships
RT        | roles                 | SELECT    | 授权判定需读角色                  | UC-4       | Runtime execution  | REQUIRED | NP-R10      | PA-R1       | REVOKE SELECT ON roles
RT        | permissions           | SELECT    | 授权判定需读权限词表               | UC-4       | Runtime execution  | REQUIRED | NP-R10      | PA-R1       | REVOKE SELECT ON permissions
RT        | role_permissions      | SELECT    | 授权判定需读绑定                  | UC-4       | Runtime execution  | REQUIRED | NP-R10      | PA-R1       | REVOKE SELECT ON role_permissions
RT        | acl_subject_types     | SELECT    | ACL 解析（subject_type 外键解析）   | UC-4       | Runtime execution  | REQUIRED | NP-R11      | PA-R1       | REVOKE SELECT ON acl_subject_types
RT        | resource_permissions  | SELECT    | ACL 判定读取                      | UC-4       | Runtime execution  | REQUIRED | NP-R1       | PA-R1       | REVOKE SELECT ON resource_permissions
RT        | events                | SELECT    | outbox 读取（实际 use-case）       | UC-1, UC-5 | Runtime execution  | REQUIRED | NP-R13      | PA-R1       | REVOKE SELECT ON events（逐分区，OI-G-2）
RT        | resources             | SELECT    | 资源读取（实际 use-case）          | UC-1, UC-4 | Runtime execution  | REQUIRED | NP-R13      | PA-R1       | REVOKE SELECT ON resources
RT        | audit_logs            | SELECT    | 审计读取（既有授权语义）            | UC-7       | Runtime execution  | REQUIRED | NP-R12      | PA-R3       | REVOKE SELECT ON audit_logs（含当期分区）
RT        | platform_state        | SELECT    | 后续 use-case 必需状态读取         | UC-1       | Runtime execution  | REQUIRED | NP-R5       | PA-R1       | REVOKE SELECT ON platform_state
RT        | platform_memberships  | SELECT    | 后续 use-case 必需状态读取         | UC-4       | Runtime execution  | REQUIRED | NP-R6       | PA-R1       | REVOKE SELECT ON platform_memberships
RT        | agents                | SELECT    | subject 解析（agent 分支）         | UC-4       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON agents
RT        | agent_versions        | SELECT    | subject 解析（版本解析）           | UC-4       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON agent_versions
RT        | agent_permissions     | SELECT    | subject 解析（权限解析）           | UC-4       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON agent_permissions
RT        | tools                 | SELECT    | subject 解析（tool 分支）          | UC-4       | Runtime execution  | REQUIRED | NP-R9       | PA-R1       | REVOKE SELECT ON tools
RT        | alembic_version       | SELECT    | readiness 探针（既有语义）         | UC-6       | Runtime execution  | REQUIRED | NP-R7       | PA-R1       | REVOKE SELECT ON alembic_version
```

---

# 2. Runtime Principal — 写入（REQUIRED · 逐动词）

```text
Principal | Object                | Operation | Reason                          | Use-case   | Trust Boundary     | Req      | NegTest | PosTest | Revocation/Rollback
RT        | users                 | INSERT    | 建立首个可登录主体                 | UC-1       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE INSERT ON users
RT        | users                 | UPDATE    | status 状态机推进                  | UC-1       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE UPDATE ON users
RT        | identities            | INSERT    | 建立身份记录                       | UC-1       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE INSERT ON identities
RT        | identities            | UPDATE    | identity verification 状态推进      | UC-1       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE UPDATE ON identities
RT        | credentials           | INSERT    | 建立凭据（Argon2id hash）           | UC-2       | Runtime execution  | REQUIRED | NP-R2   | PA-R2   | REVOKE INSERT ON credentials
RT        | credentials           | UPDATE    | rotation / revoke / expire         | UC-2       | Runtime execution  | REQUIRED | NP-R2   | PA-R2   | REVOKE UPDATE ON credentials
RT        | devices               | INSERT    | enrollment（challenge 通过后）      | UC-3       | Runtime execution  | REQUIRED | NP-R9   | PA-R4   | REVOKE INSERT ON devices
RT        | devices               | UPDATE    | revoke（撤销绑定）                  | UC-3       | Runtime execution  | REQUIRED | NP-R9   | PA-R4   | REVOKE UPDATE ON devices
RT        | sessions              | INSERT    | 建立会话（activation）              | UC-5       | Runtime execution  | REQUIRED | NP-R9   | PA-R4   | REVOKE INSERT ON sessions
RT        | sessions              | UPDATE    | 会话状态推进 / 失效                 | UC-5       | Runtime execution  | REQUIRED | NP-R9   | PA-R4   | REVOKE UPDATE ON sessions
RT        | sessions              | DELETE    | 清理失效会话（device revoke 同事务）  | UC-3, UC-5 | Runtime execution  | REQUIRED | NP-R9   | PA-R4   | REVOKE DELETE ON sessions
RT        | tenant_memberships    | INSERT    | 成员关系建立（受控 use-case）         | UC-4       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE INSERT ON tenant_memberships
RT        | tenant_memberships    | UPDATE    | 成员关系变更（受控 use-case）         | UC-4       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE UPDATE ON tenant_memberships
RT        | tenant_memberships    | DELETE    | 成员关系撤销（受控 use-case）         | UC-4       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE DELETE ON tenant_memberships
RT        | memberships           | INSERT    | 成员关系建立（受控 use-case）         | UC-4       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE INSERT ON memberships
RT        | memberships           | UPDATE    | 成员关系变更（受控 use-case）         | UC-4       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE UPDATE ON memberships
RT        | memberships           | DELETE    | 成员关系撤销（受控 use-case）         | UC-4       | Runtime execution  | REQUIRED | NP-R9   | PA-R2   | REVOKE DELETE ON memberships
RT        | events                | INSERT    | outbox 写入（实际 use-case）         | UC-1, UC-5 | Runtime execution  | REQUIRED | NP-R13  | PA-R2   | REVOKE INSERT ON events（逐分区）
RT        | events                | UPDATE    | outbox 状态推进（实际 use-case）      | UC-1, UC-5 | Runtime execution  | REQUIRED | NP-R13  | PA-R2   | REVOKE UPDATE ON events（逐分区）
RT        | resources             | INSERT    | 资源建立（实际 use-case）            | UC-1, UC-4 | Runtime execution  | REQUIRED | NP-R13  | PA-R2   | REVOKE INSERT ON resources
RT        | resources             | UPDATE    | 资源更新（实际 use-case）            | UC-1, UC-4 | Runtime execution  | REQUIRED | NP-R13  | PA-R2   | REVOKE UPDATE ON resources
RT        | audit_logs            | INSERT    | 审计写入（既有语义）                 | UC-7       | Runtime execution  | REQUIRED | NP-R12  | PA-R3   | REVOKE INSERT ON audit_logs（含当期分区）
```

---

# 3. Bootstrap Principal — 读取 / 写入（REQUIRED · 一次性）

```text
Principal | Object                | Operation | Reason                          | Use-case | Trust Boundary        | Req      | NegTest     | PosTest | Revocation/Rollback
BP        | platform_state        | SELECT    | 一次性前置校验（uninitialized）      | UC-8     | Bootstrap（one-time）  | REQUIRED | NP-B3       | PA-B4   | REVOKE SELECT ON platform_state
BP        | platform_memberships  | SELECT    | 一次性前置校验（PM 无行）            | UC-8     | Bootstrap（one-time）  | REQUIRED | NP-B3       | PA-B4   | REVOKE SELECT ON platform_memberships
BP        | platform_memberships  | INSERT    | 原子写入首个平台管理员行             | UC-8     | Bootstrap（one-time）  | REQUIRED | NP-B1, NP-B3 | PA-B2  | 删除该行（仅初始化失败回滚）；随后 REVOKE INSERT
BP        | platform_state        | UPDATE    | 翻转 uninitialized → initialized   | UC-8     | Bootstrap（one-time）  | REQUIRED | NP-B3       | PA-B2   | 回滚为 uninitialized（仅初始化失败场景）
BP        | audit_logs            | INSERT    | 写 'platform.admin.bootstrap'      | UC-8     | Bootstrap（one-time）  | REQUIRED | NP-B4       | PA-B3   | 不可撤销（审计不可变）；实施后 REVOKE
```

---

# 4. 显式 NOT REQUIRED（拒绝基线 · 防扩权）

```text
Principal | Object                | Operation | Reason                              | Req     | NegTest | PosTest | Revocation/Rollback
--        | resource_permissions  | INSERT    | SEC-09：不得改变授权边界               | NOT REQ | NP-R1   | 无      | 不适用（无授权）
--        | resource_permissions  | UPDATE    | SEC-09：同上                         | NOT REQ | NP-R1   | 无      | 不适用
--        | resource_permissions  | DELETE    | SEC-09：同上                         | NOT REQ | NP-R1   | 无      | 不适用
--        | credentials           | DELETE    | SEC-08：NO PHYSICAL DELETE           | NOT REQ | NP-R2   | 无      | 不适用
--        | tenants               | INSERT    | SEC-05：SELECT ONLY                  | NOT REQ | NP-R3   | 无      | 不适用
--        | tenants               | UPDATE    | SEC-05：同上                         | NOT REQ | NP-R3   | 无      | 不适用
--        | tenants               | DELETE    | SEC-05：同上                         | NOT REQ | NP-R3   | 无      | 不适用
--        | spaces                | INSERT    | SEC-05：SELECT ONLY                  | NOT REQ | NP-R4   | 无      | 不适用
--        | spaces                | UPDATE    | SEC-05：同上                         | NOT REQ | NP-R4   | 无      | 不适用
--        | spaces                | DELETE    | SEC-05：同上                         | NOT REQ | NP-R4   | 无      | 不适用
--        | platform_state        | INSERT    | SEC-13：bootstrap-owned              | NOT REQ | NP-R5   | 无      | 不适用
--        | platform_state        | UPDATE    | SEC-13：Runtime 不得写                | NOT REQ | NP-R5   | 无      | 不适用
--        | platform_state        | DELETE    | SEC-13：同上                         | NOT REQ | NP-R5   | 无      | 不适用
--        | platform_memberships  | INSERT    | SEC-13：bootstrap-owned              | NOT REQ | NP-R6   | 无      | 不适用
--        | platform_memberships  | UPDATE    | SEC-13：同上                         | NOT REQ | NP-R6   | 无      | 不适用
--        | platform_memberships  | DELETE    | SEC-13：同上                         | NOT REQ | NP-R6   | 无      | 不适用
--        | roles                 | INSERT    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | roles                 | UPDATE    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | roles                 | DELETE    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | permissions           | INSERT    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | permissions           | UPDATE    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | permissions           | DELETE    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | role_permissions      | INSERT    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | role_permissions      | UPDATE    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | role_permissions      | DELETE    | platform-controlled                  | NOT REQ | NP-R10  | 无      | 不适用
--        | acl_subject_types     | INSERT    | migration-only（C2 / CC-7）           | NOT REQ | NP-R11  | 无      | 不适用
--        | acl_subject_types     | UPDATE    | migration-only（C2 / CC-7）           | NOT REQ | NP-R11  | 无      | 不适用
--        | acl_subject_types     | DELETE    | migration-only（C2 / CC-7）           | NOT REQ | NP-R11  | 无      | 不适用
--        | events                | DELETE    | SEC-07：DELETE = DENY                 | NOT REQ | NP-R13  | 无      | 不适用
--        | resources             | DELETE    | SEC-07：DELETE = DENY                 | NOT REQ | NP-R13  | 无      | 不适用
--        | audit_logs            | UPDATE    | 不可变（tg_audit_immutable）           | NOT REQ | NP-R12  | 无      | 不适用
--        | audit_logs            | DELETE    | 不可变（tg_audit_immutable）           | NOT REQ | NP-R12  | 无      | 不适用
--        | sequence（public）     | SELECT    | 无序列（实测 0）                       | NOT REQ | 无      | 无      | 不适用
--        | sequence（public）     | USAGE     | 无序列（实测 0）                       | NOT REQ | 无      | 无      | 不适用
--        | function（public）     | EXECUTE   | SEC-14：仅必要时才授予；本提案不采用      | NOT REQ | 无      | 无      | 不适用
--        | schema（public）       | CREATE    | runtime 不持 DDL（D-OP101-08）        | NOT REQ | NP-R7   | 无      | 不适用
```

---

# 5. 合规检查与分区说明

```text
· 每行均为单一 operation（无 CRUD / 无 read-write 行）⇒ 无 NOT READY 行
· REQUIRED 行均带 Negative Test 与 Positive Test（NOT REQUIRED 行 PosTest = 无，属预期）
· 全部行均带 Revocation / Rollback 说明
· 无 GRANT ALL / 无 <schema> ALL / 无 ON ALL TABLES（GC-1…GC-3）
· 无 role membership 间接扩权（GC-4）· 无 uap_migrator 加入 runtime（GC-5）
· 无 runtime 继承 bootstrap authority（GC-6）· 无 default ACL（GC-7 / GC-8）

分区表处理（OI-G-2 关联）：
  · audit_logs / events / ai_request_logs 为分区表；当前分区为 *_202609
  · pg_default_acl = 0 ⇒ **新分区不自动继承授权**
  · 实施轮须**逐分区**授予；若未来确需 default ACL ⇒ 必须独立进入 Security Decision（GC-8）
```

---

# 6. 本轮工程变更

```text
CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
本文件 = IMPLEMENTATION PROPOSAL（未实施）；P14 IMPLEMENTATION = NOT AUTHORIZED
```

---

**END OF P14 SECURITY IMPLEMENTATION GRANT MATRIX（2026-09-27 · IMPLEMENTATION PROPOSAL · 逐操作行列（无 CRUD 行）· REQUIRED / NOT REQUIRED 明确 · 未实施任何授权）**
