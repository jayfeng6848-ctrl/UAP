# UAP — P14 RUNTIME IMPLEMENTATION GUARDRAILS

> ## 状态
>
> ```text
> 轮次      = P14 RUNTIME IMPLEMENTATION HUMAN AUTHORIZATION + IMPLEMENTATION GATE（§十三）
> 状态      = FROZEN（**在任何代码修改之前**建立之实现护栏）
> 适用期    = 自本文件起至 P14 Runtime Implementation Acceptance 完成
> 基线      = Security DB Boundary = IMPLEMENTED + ACCEPTED · OI-G-1 = CLOSED · 0018+ = 0
> 本轮未做   = 未写任何 Runtime code · 未 DDL / DML / grant / role
> ```

---

# 1. 十五条实现护栏（RUNTIME-G-01 … RUNTIME-G-15）

```text
RUNTIME-G-01  normal runtime uses `uap_runtime`
              ⇒ 唯一 runtime 连接身份；current_user = session_user = 'uap_runtime' 必须正向断言

RUNTIME-G-02  never use `uap_migrator`
              ⇒ 不得读取/使用 migrator credential；不得 SET ROLE；migrator 不得出现在 runtime path

RUNTIME-G-03  never use `uap_bootstrap` for normal runtime
              ⇒ bootstrap 身份仅用于一次性本地 bootstrap；runtime 不得调用

RUNTIME-G-04  authorization is centralized
              ⇒ centralized precheck + service mandatory enforcement（SEC-10 HYBRID）

RUNTIME-G-05  handler has no direct SQL
              ⇒ handler = transport/adaptation；SQL 仅经 service/repository

RUNTIME-G-06  unknown access is denied
              ⇒ default deny；判定不确定/依赖不可用 ⇒ DENY（FAIL CLOSED）

RUNTIME-G-07  `resource_permissions` write remains denied
              ⇒ 无 INSERT/UPDATE/DELETE（DB 层已拒；代码不得尝试绕过）

RUNTIME-G-08  `platform_memberships` write remains denied
              ⇒ normal Runtime 无 INSERT/UPDATE/DELETE

RUNTIME-G-09  `platform_state` write remains denied
              ⇒ normal Runtime 无 INSERT/UPDATE/DELETE（仅 SELECT）

RUNTIME-G-10  credentials are never plaintext
              ⇒ Argon2id hash；禁 plaintext storage / logging / audit payload / exception

RUNTIME-G-11  no Runtime schema creation
              ⇒ 不得创建 table/view/matview/function/procedure/trigger/index/sequence/type/schema

RUNTIME-G-12  no migration from Runtime startup
              ⇒ 启动路径不得触发 Alembic / DDL / schema 自愈

RUNTIME-G-13  C2 unchanged
              ⇒ md5 185e95be8bc4304edbcd3f4d5cda1eff 必须保持

RUNTIME-G-14  CC-7 unchanged
              ⇒ 受信迁移分支语义不得修改

RUNTIME-G-15  P13 seed unchanged
              ⇒ registry 3 / permissions 12 / role_permissions 12 不得改动
```

---

# 2. 护栏的执行方式

```text
GR-1  架构级：tests/architecture 守卫（AST）——G-04/G-05/G-11/G-12 的结构性检查
GR-2  契约级：tests/contract —— readiness 组件 critical（G-06 相关既有门）
GR-3  安全级：定向安全探针（negative/positive）——G-01…G-03 / G-07…G-09 / G-13…G-15
GR-4  纪律级：代码评审必查项——G-05 / G-10 / G-12 的人工确认
GR-5  冻结资产对照：每个 milestone 后重跑 Security Regression（PRV-1…PRV-8）+
      C2 / CC-7 / P13 seed / grants / default ACL 指纹比对
```

```text
任一护栏被违反 ⇒ **BLOCKED / STOP**，保留现场并上报；不得以"临时/后续修正"掩盖。
```

---

# 3. 与既有安全边界的关系

```text
本护栏**不新增**任何权限或约束语义；它把既已冻结的 Security Decision（SEC-P14-01…14）
与 Runtime Security Invariants（RUNTIME-SEC-01…10）翻译为**实施期可即时判定的 15 条禁令**。

对照：
  RUNTIME-G-01/02/03 ← SEC-01/02/11 · RUNTIME-SEC-01/02/03/04
  RUNTIME-G-04/05/06 ← SEC-10 · Contract §6/§7 · RUNTIME-SEC-05/06
  RUNTIME-G-07       ← SEC-09 · RUNTIME-SEC-07
  RUNTIME-G-08/09    ← SEC-13 · RUNTIME-SEC-08
  RUNTIME-G-10       ← SEC-08
  RUNTIME-G-11/12    ← SEC-14 + RTA-10（no implicit schema object）
  RUNTIME-G-13/14/15 ← SEC-12 + C2/CC-7/P13 冻结
```

---

# 4. 触发护栏的典型违规情形（预防性示例）

```text
· 为方便集成测试而在 conftest 内 CREATE VIEW / FUNCTION          → 违反 G-11（且 RTA-10 禁止）
· 启动时自动执行 alembic upgrade                                  → 违反 G-12
· handler 内直接 `conn.execute("SELECT ...")`                      → 违反 G-05（且违反 DC-18）
· 因缺 SELECT 权限而申请 GRANT                                    → 违反 G-02/G-03 精神 + §十四（须 STOP 报 SECURITY GAP）
· 把口令明文写入结构化日志用于排障                                → 违反 G-10
· 为"修一下授权"而 UPDATE resource_permissions                    → 违反 G-07
· 用 platform_state 作为 runtime 特性开关                         → 违反 G-09
```

---

# 5. 本轮工程变更

```text
未写任何 Runtime code · DDL / DML / migration / new role / grant / revoke = 0
新增文档 = 本文件（+ 同轮 1 份）· commit = 0 · tag = 0 · push = 0
P14 RUNTIME IMPLEMENTATION = 未开始（本文件为其实施前护栏）
```

---

**END OF P14 RUNTIME IMPLEMENTATION GUARDRAILS（2026-09-27 · FROZEN · RUNTIME-G-01…15 · 实施前生效）**
