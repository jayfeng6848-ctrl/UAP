# UAP — P14 SECURITY IMPLEMENTATION CLOSURE REPORT

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY IMPLEMENTATION CLOSURE + RUNTIME IMPLEMENTATION AUTHORIZATION PREPARATION
> 状态      = **SECURITY IMPLEMENTATION CLOSED**
> 可宣称    = `P14 Security Database Boundary Implemented and Accepted`
> 不可宣称  = `P14 Runtime Implemented`（Runtime code / onboarding / bootstrap CLI 均未开始）
> 基线      = HEAD c420403d5469241e8b03855428ebce435d539c9e · migration 0017_p13_seed · 0018+ = 0
> 本轮未做   = 未新增 role / grant / revoke / DDL / DML / migration / runtime code ·
>             未修改 uap_runtime / uap_bootstrap 及其既有 grants · 未 commit / tag / push
> ```

---

# 1. Implementation Authorization Evidence

```text
授权来源 = Human 指令「P14 — SECURITY IMPLEMENTATION + SECURITY ACCEPTANCE GATE」（2026-09-27）
          其 §0 明文允许执行真正的 CREATE ROLE / ALTER ROLE / GRANT / REVOKE / 安全相关 DDL /
          Security privilege probes / 权限验证；实施身份 = uap（deployment-ops authority · D-OP101-04）
本轮复核 = 未使用「Gate = READY」作为授权依据；授权来自该指令正文声明
```

---

# 2. Runtime Principal Final Identity

```text
rolname      = uap_runtime
attributes   = LOGIN · NOSUPERUSER · NOCREATEDB · NOCREATEROLE · NOINHERIT · NOREPLICATION · NOBYPASSRLS
schema       = public USAGE = true · CREATE = false
ownership    = 0（不拥有任何 public 对象）
memberships  = 0（不属于任何角色）
function EXECUTE = 0
nspacl 体现   = public nspacl 含 `uap_runtime=U`
（本轮 revalidation 只读实测，未做任何修改）
```

---

# 3. Bootstrap Principal Final Identity

```text
rolname      = uap_bootstrap
attributes   = LOGIN · NOSUPERUSER · NOCREATEDB · NOCREATEROLE · NOINHERIT · NOREPLICATION · NOBYPASSRLS
schema       = public USAGE = true · CREATE = false
memberships  = 0 · function EXECUTE = 0
boundary     = dedicated one-time bootstrap boundary（SEC-11/12/13）
未参与       = Runtime role inheritance（双向 pg_has_role 全 False）
```

---

# 4. Exact Grant Fingerprint（§六 重新计算 · 非复述）

```text
principal        row-grants   期望    说明
uap_runtime          51        51     SELECT 26 · INSERT 12 · UPDATE 10 · DELETE 3
uap_bootstrap         6         6     platform_state(S,U) · platform_memberships(S,I) ·
                                      audit_logs(I) · audit_logs_202609(I)
uap_app               5         5     未变（BATCH-A 5 项）
uap_seed              0         0     未变
uap_migrator        245       245     未变（自持实体化）
pg_default_acl        0         0     未引入
function EXECUTE    runtime 0 / bootstrap 0 / uap_app 0（未授予任何函数执行权）
sequences           public 无序列（0）
⇒ 实测与 Matrix 逐项一致，**无「权限等价」式自行接受**
```

---

# 5. Role Security Attributes（§四 / §五 逐项）

```text
uap_runtime ：
  LOGIN ✔ · NOSUPERUSER ✔ · NOCREATEDB ✔ · NOCREATEROLE ✔ · NOINHERIT ✔ ·
  NOREPLICATION ✔ · NOBYPASSRLS ✔ · schema CREATE=false ✔ · 无 unexpected ownership ✔ ·
  无 unexpected memberships ✔ · 无 unexpected function EXECUTE ✔ · 无 unexpected schema privilege ✔
  （schema privilege 仅 USAGE）· 无 migration authority ✔ · 无 bootstrap authority ✔
uap_bootstrap ：
  dedicated ✔ · one-time bootstrap boundary ✔ · 不属 Runtime inheritance ✔ · 不属 migrator ✔ ·
  无 broad Runtime CRUD ✔ · 无 resource_permissions write ✔ · 无 migration DDL ✔ ·
  无 CREATE ROLE ✔ · 无 CREATE SCHEMA ✔ · 无任意 schema governance ✔
```

---

# 6. Membership Proof

```text
user-defined memberships = 0（全集群）
pg_has_role 双向矩阵（实施后 revalidation）：
  uap_runtime   → migrator / app / seed / bootstrap = (False, False, False, False)
  uap_bootstrap → migrator / runtime / app          = (False, False, False)
  uap_app       → runtime / bootstrap               = (False, False)
  uap_migrator  → runtime / bootstrap               = (False, False)
⇒ 无任何 inheritance-based 扩权路径
```

---

# 7. Positive Assertions

```text
Runtime（catalog + 事务内 DML 证明）
  · approved read   = ALLOWED（26 项 SELECT 断言全 OK）
  · approved insert = ALLOWED（users / audit_logs / events 事务内 INSERT 成功后 rollback）
  · approved update = ALLOWED（credentials.U / events.U 等断言 True）
  · approved delete = ALLOWED **仅 Matrix 明确者**（sessions / tenant_memberships / memberships = True；
                      其余对象 DELETE 断言 False）
Bootstrap（catalog）
  · platform_state S/U = True/True · platform_memberships S/I = True/True · audit_logs I = True（5/5）
```

---

# 8. Negative Probes

```text
累计尝试 = 54 次 · unexpected ALLOWED = **0**
Runtime（38）：resource_permissions 写 ×3 · credentials DELETE · tenants 写 ×3 · spaces 写 ×3 ·
  platform_state 写 ×3 · platform_memberships 写 ×3 · CREATE TABLE / ALTER TABLE / DROP TABLE /
  CREATE SCHEMA ×4 · SET ROLE migrator · CREATE ROLE · roles/permissions/role_permissions 写 ×5 ·
  acl_subject_types 写 ×3 · audit_logs U/D ×2 · events/resources DELETE ×2
uap_app（3）：users SELECT/INSERT · credentials INSERT → DENIED
uap_migrator（3）：属性/边界/C2 未变（无越界能力）
Bootstrap（10）：broad CRUD ×3 · migration ×2 · SET ROLE migrator · resource_permissions ×2 ·
  roles/platform_* 删除 ×3
```

---

# 9. Revoke / Rollback Proof

```text
对象/动词 = public.tools / SELECT（uap_runtime）
  pre   : SELECT=True · 51 row-grants
  REVOKE: SELECT=False · 50 row-grants（精确回收）
  re-GRANT: SELECT=True · 51 row-grants（可复原）
⇒ 精确回收路径存在且可逆；未使用 `REVOKE ALL`；净变更 = 0
```

---

# 10. C2 / CC-7 Proof

```text
C2 md5（本轮 revalidation）= 185e95be8bc4304edbcd3f4d5cda1eff —— 与实施前一致
CC-7 = 未修改（受信分支语义不变）· migrator ownership 未变
Runtime 对 acl_subject_types = SELECT only（写 → DENIED）⇒ 不依赖 C2/CC-7 获得信任
```

---

# 11. Protected-Object Proof

```text
0017_p13_seed.py                  1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e（未变）
0016_open_p10_1_trust_boundary.py 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544（未变）
env.py                            577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a（未变）
pg_class 156 · pg_proc 22 · registry/permissions/role_permissions = 3/12/12 · ownership residual 0
pg_default_acl 0 · 无 role membership drift · 无 ownership mutation · 无 function execution drift
```

---

# 12. OI-G-1 Closure Proof

```text
关闭 10 条件（已在上轮实测，本轮 revalidation 未变更）：
  principal 实体创建 ✔ · bootstrap principal 创建 ✔ · exact grants 授予 ✔ ·
  catalog evidence 完整 ✔ · negative probes 完整 ✔ · positive assertions 完整 ✔ ·
  无 UNKNOWN ✔ · 无 unexpected privilege ✔ · 无 C2/CC-7 drift ✔ · Security Acceptance PASS ✔
⇒ **OI-G-1 = CLOSED**（保持）
注：Runtime 业务实现带来的**新增**权限需求若出现，须重开 Security Decision，不得沿用本状态自动扩权
```

---

# 13. Final DB Snapshot

```text
roles = 6：uap · uap_app · uap_bootstrap · uap_migrator · uap_runtime · uap_seed
grants = runtime 51 · bootstrap 6 · app 5 · seed 0 · migrator 245
memberships = 0 · default_acl = 0 · pg_class 156 · pg_proc 22
registry/permissions/role_permissions = 3/12/12 · platform_state = 1(uninitialized)
alembic = 0017_p13_seed · 0018+ = 0 · migration files = 17
C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff
Git：HEAD c420403d…（未变）· branch main · tags 9 · remote 0 · staged 0 · dirty 143
```

---

# 14. Final Security Acceptance Result

```text
P14 SECURITY ACCEPTANCE = PASS（SEC-01…14 = 14/14 · 安全属性 11/11 · 见
                                 P14_SECURITY_ACCEPTANCE_REPORT.md）
P14 Security Database Boundary = **IMPLEMENTED AND ACCEPTED**
Runtime Implementation = NOT STARTED · Human Runtime Authorization = REQUIRED
```

---

# 15. SEC-01 … SEC-14 Traceability Matrix（§三）

```text
Decision → Principal → Object → Operation → Implementation Evidence → Positive → Negative → Acceptance

SEC-01 DEDICATED RUNTIME PRINCIPAL
  → uap_runtime → （角色本体）→ CREATE ROLE → 角色创建证据 + 属性 catalog → PA-R5 →
    NP-R9（membership False）→ PASS
SEC-02 TRUSTED INTERNAL SERVICE BOUNDARY
  → uap_runtime / uap_migrator / uap_bootstrap 分工 → 连接身份断言 → 3 身份分离证据 →
    PA-R5 → NP-R9 / NP-M1..M3 → PASS
SEC-03 explicit required-read allowlist
  → uap_runtime → 26 对象 → SELECT → 26 项授权 + catalog 断言 → PA-R1 → NP-A3（未授权 SELECT 拒）→ PASS
SEC-04 use-case + operation exact write
  → uap_runtime → 10/9/3 对象 → INSERT/UPDATE/DELETE → 逐动词授权 → PA-R2/R3/R4 →
    NP-R1..R13 → PASS
SEC-05 TENANTS/SPACES = SELECT ONLY
  → uap_runtime → tenants/spaces → SELECT → 2 项 SELECT 授权 → PA-R1 →
    NP-R3（写 ×3 DENIED）/ NP-R4（写 ×3 DENIED）→ PASS
SEC-06 MEMBERSHIP = SERVICE-MEDIATED
  → uap_runtime → memberships/tenant_memberships vs platform_memberships → S/I/U/D vs SELECT →
    授权差异证据 → PA-R2 → NP-R6（platform 写 ×3 DENIED）→ PASS
SEC-07 EVENTS/RESOURCES = S/I/U
  → uap_runtime → events/resources → S/I/U（DELETE DENY）→ 6 项授权 → PA-R2 →
    NP-R13（DELETE ×2 DENIED）→ PASS
SEC-08 NO PHYSICAL CREDENTIAL DELETE
  → uap_runtime → credentials → S/I/U（无 DELETE）→ 3 项授权 → PA-R2 →
    NP-R2（DELETE DENIED）→ PASS
SEC-09 RESOURCE_PERMISSIONS WRITE = DENY
  → uap_runtime → resource_permissions → SELECT only → 1 项授权 → PA-R1 →
    NP-R1（写 ×3 DENIED）→ PASS
SEC-10 HYBRID AUTHORIZATION READ PATH
  → uap_runtime → roles/permissions/role_permissions/acl_subject_types/resource_permissions →
    SELECT only → 5 项读授权 + 无写授权 → PA-R1 → NP-R10/R11（写 DENIED）→ PASS
SEC-11 DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL
  → uap_bootstrap → 角色本体 → CREATE ROLE → 角色创建 + 属性证据 → PA-B（5）→
    NP-B1..B4（×10 DENIED）→ PASS
SEC-12 LOCAL OPERATOR-CONTROLLED SECRET INPUT
  → （凭据通道设计）→ 无 DB 对象 → 设计登记（Connection Security Note）→ 证据产物 0 secret →
    N/A（边界层面）→ PASS
SEC-13 BOOTSTRAP-OWNED INITIALIZATION
  → uap_bootstrap → platform_memberships/platform_state → S/I + S/U → 4 项授权 →
    PA-B → NP-B4（DELETE ×2 DENIED）+ 运行时侧 NP-R5/R6 → PASS
SEC-14 EXACT LEAST-PRIVILEGE GRANT STRATEGY
  → uap_runtime + uap_bootstrap → 全部对象 → 全部动词 → 57 row-grants 逐操作 →
    无 broad grant 证据 → NP（无越权）→ PASS

Traceability gaps = **0**（14/14 均有实现证据 + 正向 + 负向 + 验收结果）
```

---

# 16. Security Evidence Freeze（§十）

```text
自本报告起冻结以下事实（Runtime implementation 不得未经独立 Gate 修改）：
  uap_runtime（身份与属性）· uap_bootstrap（身份与属性）· exact grants（51 + 6 + 5 + 0 + 245）·
  negative probes 结果 · positive assertions 结果 · role attributes · membership = 0 ·
  rollback 路径 · C2 md5 · CC-7 · pg_default_acl = 0 · protected objects（0016 / 0017 / env.py /
  pg_class 156 / pg_proc 22 / P13 seed 3/12/12）
```

---

# 17. 本轮工程变更

```text
DB mutation = 0（无 new role / grant / revoke / DDL / DML）· migration = 0 · runtime code = 0
新增文档 = 本报告（+ 同轮 6 份）· commit = 0 · tag = 0 · push = 0 · P15 = 未进入
P14 RUNTIME IMPLEMENTATION = **NOT AUTHORIZED** · HARD STOP = ACTIVE
```

---

**END OF P14 SECURITY IMPLEMENTATION CLOSURE REPORT（2026-09-27 · **SECURITY IMPLEMENTATION CLOSED** · `P14 Security Database Boundary Implemented and Accepted` · SEC-01…14 traceability gaps = 0 · `OI-G-1 = CLOSED` · Runtime = NOT IMPLEMENTED）**
