# UAP — P14 SECURITY ACCEPTANCE REPORT

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY IMPLEMENTATION + SECURITY ACCEPTANCE GATE
> 性质      = 逐项验收（**每项 PASS 均附实际 evidence**；不因"角色创建成功"自动判定）
> 证据来源   = 本轮 catalog 查询 / 正负向探针 / 事务内 DML 证明 / rollback 证明（见实施报告）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · DB 0017_p13_seed
> ```

---

# 1. Security Decision 逐项验收（SEC-P14-01 … SEC-P14-14）

```text
SEC-P14-01  Runtime Principal Model = DEDICATED RUNTIME PRINCIPAL ................ **PASS**
  evidence：`uap_runtime` 已创建（独立于 uap_app / uap_migrator / uap_seed）；
            pg_has_role(uap_runtime → migrator/app/seed/bootstrap) 全 False；
            属性 = NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOINHERIT/NOREPLICATION/NOBYPASSRLS。

SEC-P14-02  Trust Boundary = TRUSTED INTERNAL SERVICE BOUNDARY ...... **PASS**
  evidence：runtime 身份 = uap_runtime（current_user = session_user = 'uap_runtime'）；
            migration 身份 = uap_migrator（未被 runtime 使用）；seed = uap_seed（未参与）；
            bootstrap = uap_bootstrap（独立）；C2/CC-7 未改（md5 185e95be…）。

SEC-P14-03  Explicit required-read allowlist ....................... **PASS**
  evidence：SELECT 仅 26 项（24 父表 + 2 分区），逐项对应 Grant Matrix；
            未授权对象 SELECT 全部 False（实测 NP-A3 / 负向探针）；UNKNOWN = 0。

SEC-P14-04  Use-case + operation exact write ....................... **PASS**
  evidence：INSERT 12 / UPDATE 10 / DELETE 3，逐对象逐动词；
            users.DELETE=False · credentials.DELETE=False · tenants/spaces 写全 False（catalog 实测）。

SEC-P14-05  Tenants / Spaces = SELECT ONLY ......................... **PASS**
  evidence：tenants SELECT=True；tenants INSERT/UPDATE/DELETE 实际尝试 → DENIED ×3；
            spaces SELECT=True；spaces INSERT/UPDATE/DELETE → DENIED ×3。

SEC-P14-06  Membership = service-mediated（普通 vs platform 分离） .... **PASS**
  evidence：runtime 对 memberships / tenant_memberships 具备 S/I/U/D（受控 use-case）；
            对 platform_memberships 仅 SELECT（INSERT/UPDATE/DELETE → DENIED ×3）。

SEC-P14-07  Events / Resources = S/I/U（DELETE = DENY） .............. **PASS**
  evidence：events S/I/U=True · DELETE 实测 DENIED；resources S/I/U=True · DELETE DENIED。

SEC-P14-08  NO PHYSICAL CREDENTIAL DELETE ......................... **PASS**
  evidence：credentials DELETE=False（catalog）+ 实际 DELETE 尝试 → DENIED；
            credentials 具备 INSERT/UPDATE/SELECT（issue / rotate / revoke / expire 路径）。

SEC-P14-09  resource_permissions WRITE = DENY ..................... **PASS**
  evidence：catalog INSERT/UPDATE/DELETE 全 False；实际尝试 INSERT/UPDATE/DELETE → DENIED ×3；
            SELECT=True（授权判定读取）⇒ 无 self-escalation 闭环。

SEC-P14-10  HYBRID authorization read path ......................... **PASS**
  evidence：roles / permissions / role_permissions / acl_subject_types / resource_permissions
            均为 SELECT only（写侧全部 DENIED）；
            未新增任何 handler 直连/授权表写权限；
            default deny / deny precedence / ABAC 语义由应用层承载（未在 DB 层新增机制）；
            DB RLS 未启用（relrowsecurity=true 的表 = 0）。

SEC-P14-11  DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL ................. **PASS**
  evidence：`uap_bootstrap` 已创建且独立；未被用作 runtime 身份；
            对 users/credentials/tenants 等 → DENIED（broad CRUD 被拒）；
            对 platform_memberships/platform_state 具备规定权限（catalog 断言 5/5）。

SEC-P14-12  LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT ...... **PASS（边界层面）**
  evidence：本轮未创建任何 CLI，也未在仓库/日志/审计中写入任何 secret 材料
            （证据产物 0 secret；报告与探针输出均不含凭据）；
            凭据输入通道设计见 P14_RUNTIME_CONNECTION_SECURITY_NOTE.md（未实施）。
            说明：full 凭据通道实现属后续 Bootstrap CLI 轮（本轮 = 边界层面 PASS）。

SEC-P14-13  BOOTSTRAP-OWNED INITIALIZATION ......................... **PASS**
  evidence：uap_bootstrap 对 platform_memberships(S,I) / platform_state(S,U) 具备权限；
            uap_runtime 对二者仅 SELECT（写 → DENIED ×6）；
            platform_state 仍 1 行 uninitialized · platform_memberships 仍 0 行（本轮未执行 bootstrap）。

SEC-P14-14  EXACT LEAST-PRIVILEGE GRANT STRATEGY ................... **PASS**
  evidence：57 项 row-grants 全部 object-level + operation-level；
            无 GRANT ALL / 无 `<schema> ALL` / 无 `ON ALL TABLES` / 无继承型授权；
            无 sequence 授权（public 无序列）；无 function EXECUTE 授权（uap_runtime=0）；
            pg_default_acl 保持 0（未使用 ALTER DEFAULT PRIVILEGES）。
```

```text
汇总：SEC-01…SEC-14 = 14 / 14 PASS（SEC-12 为边界层面 PASS，实现轮归属已登记）
```

---

# 2. 安全属性验收

```text
Least Privilege      = **PASS**
  evidence：runtime 51 / bootstrap 6 项逐操作授予；未授权组合实测全 DENIED；
            role 属性全最小；无 ownership；无 DDL。

No Broad Grant       = **PASS**
  evidence：未出现 GRANT ALL / schema ALL / ON ALL TABLES；未出现 CRUD 级模糊授权。

No Self Escalation   = **PASS**
  evidence：resource_permissions 写 = DENIED ×3；SET ROLE uap_migrator = DENIED；
            CREATE ROLE = DENIED；membership 全 False；无继承扩权路径。

Runtime/Migration    = **PASS**
  evidence：runtime 身份 ≠ migrator；uap_runtime → uap_migrator membership False；
            runtime 无法 SET ROLE 到 migrator；migrator 未被 runtime 使用。

Runtime/Bootstrap    = **PASS**
  evidence：两个独立角色，互不继承（pg_has_role 双向 False）；
            runtime 无 platform_* 写权限；bootstrap 无 runtime broad CRUD。

Bootstrap/Migration  = **PASS**
  evidence：uap_bootstrap → uap_migrator membership False；SET ROLE migrator = DENIED；
            CREATE TABLE = DENIED；migrator 边界未放宽（CREATE=false · grants 245 未变）。

C2 Compatibility     = **PASS**
  evidence：C2 md5 未变（185e95be8bc4304edbcd3f4d5cda1eff）；
            runtime 对 acl_subject_types 仅 SELECT（写侧 DENIED ×3）。

CC-7 Compatibility   = **PASS**
  evidence：CC-7 受信分支未修改；migrator ownership 未变更；runtime 未获 migration function 权限。

Negative Probes      = **PASS**
  evidence：runtime 38 + app 3 + migrator 3 + bootstrap 10 = 54 次尝试 · unexpected ALLOWED = 0。

Positive Assertions  = **PASS**
  evidence：26 项 catalog 断言全 OK；3 项事务内 DML 证明 ALLOWED 且已回滚（无残留）；
            bootstrap 5 项 catalog 断言 OK。

Rollback Evidence    = **PASS**
  evidence：public.tools/SELECT 精确 REVOKE → 验证 False → re-GRANT → 验证 True；
            未使用 REVOKE ALL；净变更 0。
```

---

# 3. Residue / Integrity 验收

```text
Unexpected Roles        = 0（roles = 6：uap / uap_app / uap_bootstrap / uap_migrator / uap_runtime / uap_seed）
Unexpected Memberships  = 0（user-defined = 0）
Unexpected Grants       = 0（runtime 51 · bootstrap 6 · app 5 · seed 0 · migrator 245）
Unexpected REVOKE       = 0
DB Data Residue         = 0（3/12/12 · users 0 · audit_logs 0 · events 0 · resources 0 ·
                             credentials 0 · devices 0 · sessions 0 · identities 0 ·
                             platform_state 1(uninitialized) · platform_memberships 0）
Default ACL             = 0（未引入）
Protected Object Integrity = PASS（0017 / 0016 / env.py sha 未变 ·
                                   pg_class 156 · pg_proc 22 · ownership residual 0 · C2 未变）
```

---

# 4. 验收结论

```text
P14 SECURITY ACCEPTANCE = **PASS**
  · Security Decisions        = 14 / 14 PASS
  · 安全属性                  = 11 / 11 PASS
  · Residue / Integrity       = PASS
  · OI-G-1                    = CLOSED（10 项关闭条件全部满足）

边界声明：
  · 本验收仅覆盖 **DATABASE SECURITY BOUNDARY**
  · Runtime Code Implementation = NOT STARTED
  · Database Onboarding         = NOT STARTED
  · Bootstrap CLI               = NOT STARTED
  · 不得因 Security DB Boundary 已落地而开始 Runtime application implementation
  · COMMIT / TAG / PUSH / P15   = FORBIDDEN（本轮未执行）
```

---

**END OF P14 SECURITY ACCEPTANCE REPORT（2026-09-27 · `SEC-01…14 = 14/14 PASS` · 安全属性 11/11 PASS · `OI-G-1 = CLOSED` · 验收范围 = DATABASE SECURITY BOUNDARY ONLY）**
