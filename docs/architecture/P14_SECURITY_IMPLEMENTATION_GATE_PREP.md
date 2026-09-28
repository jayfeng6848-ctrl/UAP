# UAP — P14 SECURITY IMPLEMENTATION GATE PREPARATION

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CANONICAL REGISTRATION + SECURITY IMPLEMENTATION GATE PREPARATION
> 状态      = **IMPLEMENTATION GATE PREPARATION**
> 明确不是  = IMPLEMENTED / SECURITY APPROVED / P14 IMPLEMENTATION AUTHORIZED
> 依据      = PDL **附录 O**（SEC-P14-01…14 canonical registration）· Decision Sheet（RESOLVED）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · DB 0017_p13_seed · 0018+ = 0
> 本轮未做   = CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0 ·
>             DDL / DML / migration / runtime code / bootstrap implementation = 0 · 未 commit/tag/push
> ```

---

# 1. Future Implementation Inventory

> 本节只登记**目标状态**；**不得**据此执行任何 CREATE ROLE / GRANT。

## 1.1 Runtime Principal — 目标状态

```text
字段                      目标状态（依 SEC-01 / 02 / 03 / 04 / 14）
-----------------------   ------------------------------------------------------------
role identity             专用 runtime principal（命名待实施轮确定；不得复用
                           uap_app / uap_migrator / uap_seed）
login / connect semantics LOGIN（受信内部 Service Boundary 的数据库身份）；经网络连接
                           （pg_hba 走 scram，与既有约定一致）
ownership                  **不拥有任何业务表 / migration metadata / seed schema 治理对象**
role membership            不属于任何既有角色（user-defined membership = 0 为基线要求）
NOSUPERUSER               必须
NOCREATEDB                必须
NOCREATEROLE              必须
NOINHERIT / INHERIT       **目标 = NOINHERIT**（避免经继承获得未审权限；
                           与 SEC-14「no inheritance-based expansion」一致）
                           ——若实施轮选择 INHERIT，须显式给出理由并加负向探针
schema CREATE             **false**（runtime 不持 DDL · D-OP101-08）
credential lifecycle      独立于 migration / seed（SEC-01 / 02）
rotation                   独立轮换（SEC-01）
revocation                 独立撤销（SEC-01 / 14）
secret storage             见 P14_RUNTIME_CONNECTION_SECURITY_NOTE.md
connection usage           仅经受信内部 Service Boundary；不用于 migration / bootstrap
```

## 1.2 Bootstrap Principal — 目标状态（须与 Runtime principal 分离）

```text
字段                      目标状态（依 SEC-11 / 12 / 13）
-----------------------   ------------------------------------------------------------
role identity             dedicated one-time bootstrap principal（命名待实施轮确定）
login / connect semantics 受控本地 operator 执行（local CLI）；**无公开网络 bootstrap endpoint**
目标权限范围               仅覆盖：one-time bootstrap · `platform_memberships` ·
                           `platform_state` · 必要的 initialization transaction ·
                           必要验证 · one-time lock
lifecycle                 一次性；bootstrap 完成后与 Runtime principal 分离；
                           凭据不得自动成为正常 Runtime credential（SEC-12）
不变量                     **Bootstrap Principal ≠ uap_migrator**
                           **Bootstrap Principal ≠ Runtime Principal**
                           **Bootstrap Principal ≠ uap_app**
```

---

# 2. Negative Security Probes（设计 · 不得执行）

## 2.1 Runtime principal negative probes

```text
NP-R1  修改 resource_permissions           → 必须被拒（SEC-09）
NP-R2  删除 credential（physical delete）  → 必须被拒（SEC-08）
NP-R3  修改 tenants                        → 必须被拒（SEC-05：INSERT/UPDATE/DELETE 皆拒）
NP-R4  修改 spaces                         → 必须被拒（SEC-05）
NP-R5  修改 platform_state                 → 必须被拒（SEC-13）
NP-R6  修改 platform_memberships           → 必须被拒（SEC-13）
NP-R7  执行 migration-only capability      → 必须被拒（schema DDL / registry 写 / 0018+）
NP-R8  执行 bootstrap-only capability      → 必须被拒（SEC-11 / 13）
NP-R9  获得额外 role membership（SET ROLE / 继承）→ 必须失败（SEC-14 · NOINHERIT 目标）
NP-R10 修改 roles / permissions / role_permissions → 必须被拒（platform-controlled）
NP-R11 修改 acl_subject_types              → 必须被拒（C2 / CC-7 · migration-only）
NP-R12 UPDATE / DELETE audit_logs          → 必须被拒（tg_audit_immutable）
NP-R13 events / resources DELETE           → 必须被拒（SEC-07）
```

## 2.2 uap_app negative probes

```text
NP-A1  uap_app 表级授权集合 = 实施前快照（5 项）  → 不得因 P14 Security Implementation 变化
NP-A2  uap_app schema CREATE = false              → 不得变化
NP-A3  uap_app 对 users/roles/tenants 等仍零权限   → 不得变化
```

## 2.3 uap_migrator negative probes

```text
NP-M1  uap_migrator 不得出现在 Runtime service execution path（连接身份断言）
NP-M2  uap_migrator 不得成为 Runtime DB credential（凭据来源断言）
NP-M3  uap_migrator schema CREATE = false 保持（窗口期不得开启）
```

## 2.4 Bootstrap principal negative probes

```text
NP-B1  bootstrap 完成后不得成为正常 Runtime principal
NP-B2  普通 Runtime 不得经 bootstrap path 获权
NP-B3  第二次 bootstrap 必须被拒（one-time state lock）
NP-B4  bootstrap principal 不得用于日常业务读写
```

---

# 3. Positive Security Assertions（设计 · 不得执行）

## 3.1 Runtime principal

```text
PA-R1  可执行 approved runtime required reads（依矩阵 R 的 SELECT）
PA-R2  可执行 approved runtime writes（依矩阵 R 的 INSERT/UPDATE/DELETE）
PA-R3  可执行 approved audit writes（audit_logs INSERT）
PA-R4  可执行 approved session / device / onboarding path（sessions/devices/credentials/users/identities）
PA-R5  连接身份断言 = 该 principal（current_user = session_user）
```

## 3.2 Bootstrap principal

```text
PA-B1  可完成一次性 bootstrap（local CLI 路径）
PA-B2  可原子写入 bootstrap-owned state（platform_memberships 首行 + platform_state 翻转）
PA-B3  可成功建立平台初始状态（含 audit 'platform.admin.bootstrap'）
PA-B4  完成后 one-time lock 生效（第二次调用被拒）
```

---

# 4. Privilege Grant 最终约束（Grant Constraint Set）

```text
GC-1  禁止 `GRANT ALL`
GC-2  禁止 `GRANT <schema> ALL`
GC-3  禁止 `GRANT INSERT, UPDATE, DELETE ON ALL TABLES`
GC-4  禁止通过 role membership 间接获得不需要的权限
GC-5  禁止把 `uap_migrator` 加入 Runtime role
GC-6  禁止让 Runtime principal 继承 bootstrap authority
GC-7  禁止通过 default ACL 形成未来表自动扩权
GC-8  本 P14 baseline：`pg_default_acl = 0`（实测）；
      后续若确需改变 default ACL ⇒ **必须独立进入 Security Decision**
GC-9  授权必须 object-level + operation-level（SEC-14）；无法精确到动词的行 = NOT READY
```

---

# 5. C2 / CC-7 Compatibility Review

```text
证明要求：Runtime principal 的所有预期权限**不依赖** C2 或 CC-7 来获得 Runtime 信任。

复核结论：
  · C2 = **migration-only trust boundary**（受信分支仅对 current_user = session_user =
    'uap_migrator' 放行 registry 写）
  · CC-7 = **migration ownership / execution boundary**（同上语义的判据形态）
  · Runtime authorization 使用 **application / service authorization**（SEC-10 = HYBRID），
    **不使用** migration trust
  · Runtime principal 对 acl_subject_types 的预期权限 = **SELECT only**（矩阵 §8），
    不依赖 C2 的任何放行分支
  · Runtime principal 不触碰 registry 写 ⇒ 无需 C2 豁免

⇒ **无需修改 C2 / CC-7** ⇒ 本项 = **PASS**（非 BLOCKED）
```

---

# 6. Schema / Ownership Boundary（实施禁令）

```text
Runtime principal 目标状态**明确不含**：
  · 不拥有业务表
  · 不拥有 migration metadata
  · 不拥有 P13 seed schema governance authority
  · 不获得 migration function ownership
  · 不获得 CREATE ROLE
  · 不获得 CREATE SCHEMA
  · 不获得 ALTER TABLE
  · 不获得 DROP
  · 不获得任意 DDL capability

若任何目标 grant 突然要求上述任一 ⇒ **BLOCKED**（停止并上报）
```

---

# 7. Audit / Observability Boundary

```text
必须确认：Runtime privilege implementation **不会**将
  password · credential hash · token · secret · raw sensitive payload
写入 audit_logs 或 operational logs。

必须保留的审计上下文（依 Contract §11 OB-2 与既有 audit 契约）：
  request_id · correlation_id · actor · operation · decision · outcome

约束：
  · operational logs 与 audit_logs 分离（OQ-P14-11）
  · audit_logs 不可变（tg_audit_immutable）
  · 本轮不写任何 audit_logs（DML = 0）
```

---

# 8. OI-G-1 状态（§十九）

```text
OI-G-1 = **OPEN / ACTIVE**（本轮仍不关闭）

证据链更新：
  此前 UNKNOWN            →  现在
  principal               →  **DECIDED**（SEC-01 = dedicated runtime principal）
  grant strategy          →  **DECIDED**（SEC-14 = exact least-privilege）
  bootstrap ownership     →  **DECIDED**（SEC-13 = bootstrap-owned initialization）

剩余关闭前置条件（全部未满足）：
  · actual principal implementation
  · actual grants
  · actual negative probes
  · actual positive assertions
  · actual security acceptance evidence

⇒ OI-G-1 = OPEN 是**正确状态**
```

---

# 9. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · bootstrap implementation = 0
CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0
新增文档 = 本文件（+ 同轮 3 份）· PDL = 仅追加 Appendix O · commit = 0 · tag = 0 · push = 0
```

---

**END OF P14 SECURITY IMPLEMENTATION GATE PREPARATION（2026-09-27 · `IMPLEMENTATION GATE PREPARATION`（非 IMPLEMENTED / 非 SECURITY APPROVED / 非 AUTHORIZED）· C2/CC-7 兼容 = PASS · OI-G-1 = OPEN）**
