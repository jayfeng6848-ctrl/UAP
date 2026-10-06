# 06_D_OP101_DECISION_STATE — OPEN-P10-1 决策（D-OP101-01…14 · 全部 FROZEN）

> 权威 = PDL（sha256[:16] `a83fde5c57605252`）附录 L。下表为 PDL 决策表**逐字摘录**。新 Agent **不得重新解释、不得重开、不得推断扩展**。

| ID | 议题 | 决策（逐字） | 状态 |
|---|---|---|---|
| `D-OP101-01` | 角色拓扑 | `ACCEPT OPTION D` ⇒ **`RM-D`**（`uap_seed`/`uap_migrator`/`uap_app`） | **FROZEN** |
| `D-OP101-02` | migration identity 的权限等级 | `ACCEPT OPTION A` ⇒ **必须 `NOSUPERUSER`** | **FROZEN** |
| `D-OP101-03` | revision 编号归属 | **`CUSTOM DECISION`**（`0016` 归 `OPEN-P10-1`；P13 seed = `0017_p13_seed`，不授权创建） | **FROZEN** |
| `D-OP101-04` | 角色创建者 | `ACCEPT OPTION C` ⇒ **deployment / orchestration / operations 预置** | **FROZEN** |
| `D-OP101-05` | C2 判据形态 | **`CUSTOM DECISION`**（**`CP-F`**：`current_user` ∧ `session_user` 合取；**批准 `CC-7`**） | **FROZEN** |
| `D-OP101-06` | 是否同时落地 `uap_readonly` | `ACCEPT OPTION B` ⇒ **DEFER** | **FROZEN** |
| `D-OP101-07` | runtime GRANT 矩阵范围 | `ACCEPT OPTION C` ⇒ **minimum required set** | **FROZEN** |
| `D-OP101-08` | 「runtime 不持 DDL」是否由 DB 层强制 | `ACCEPT OPTION C` ⇒ **DB enforced + positive assertion + negative probe** | **FROZEN** |
| `D-OP101-09` | 既有 156 对象的所有权 | `ACCEPT OPTION B` ⇒ **full ownership transition** | **FROZEN** |
| `D-OP101-10` | 配置 / 环境面承载双身份 | `ACCEPT OPTION A` ⇒ **independent migration/runtime keys + explicit resolution chain** | **FROZEN** |
| `D-OP101-11` | 测试基建与集群级角色 | `ACCEPT OPTION A` ⇒ **testkit role provisioning + dual DSN fixtures** | **FROZEN** |
| `D-OP101-12` | downgrade 语义 | `ACCEPT OPTION B` ⇒ **REVOKE and retain cluster role** | **FROZEN** |
| `D-OP101-13` | 「身份隔离已成立」的机读判据 | `ACCEPT OPTION C` ⇒ **topology landed + complete eight-test proof** | **FROZEN** |
| `D-OP101-14` | 既有守卫 rationale 的同步口径 | `ACCEPT OPTION A` ⇒ **update rationale while retaining existing assertions** | **FROZEN** |

## BATCH-C Human Decision（在其上叠加 · 载体 = `OPEN_P10_1_BATCH_C_DECISION_RECORD.md`，sha256[:16] `9efbc3fe031387d0`）

```text
BATCH-C START AUTHORIZATION = AUTHORIZED
CF-C-1 = A（仅批准向 uap_migrator 授予 0016 所需 schema CREATE；不触 uap_app 5 grants）
CF-C-2 = A（NOSUPERUSER 等属性保持；最小必要 privilege provision）
CF-C-3 = A（ownership 不变 · 不转移 178 对象 · 不新建 owner role）
CF-C-4 = C（integration/reset 冲突延后 BATCH-D；本批只用独立最小探针）
CC-7 MODEL = CUSTOM（Trusted Migration Identity Model = CP-F；实现形态 A/B ⇒ OI-DC-1）
             ⇒ PRE-FLIGHT 已 RESOLVE TO INLINE（OI-DC-1 关闭）
MIGRATION ROLE POLICY = A（uap_migrator-only；current_user = session_user = uap_migrator）
OWNERSHIP POLICY = A（Preserve Existing Ownership）
CF-C-5 = B（Windowed Privilege + Post-Migration Revocation；对齐 D-OP101-12）
CF-C-6 = A（0016 仅 CC-7 · 0017 归属不变）
CF-C-7 = CONFIRM（CC-7 落地并验证后才允许 registry/seed 后续流程）
```

## 与 P13 决策的相容性（PDL 附录 L 逐字）

```text
D-P13-03（migration-controlled path）：核心目标保持；受信主体由本组（RM-D + CP-F）形式化
D-P13-11（禁 trigger bypass）：保持原样；D-OP101-05 不触及触发器状态（仅函数体判据）⇒ 相容
D-P13-15（B-1 Amendment）：未改写；其 Does not authorize 含「C2 修改」⇒ D-OP101-05 的 CC-7 仍不构成实施授权
D-P13-01…14 / D-PLAT-11 / CORE §13：未改写；CORE §13 保持为 RM-D 的子集（uap_seed 为扩展角色）
```
