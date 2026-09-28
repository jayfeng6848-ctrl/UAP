# UAP — P14 RUNTIME IMPLEMENTATION AUTHORIZATION CLOSURE REPORT

> ## 状态
>
> ```text
> 轮次      = P14 RUNTIME IMPLEMENTATION HUMAN AUTHORIZATION + IMPLEMENTATION GATE
> 状态      = **AUTHORIZATION CLOSED**
> 含义      = Runtime 主链已获明确 implementation AUTHORIZED（可开始下一轮实现）
> 本轮性质   = 授权登记 + 防护栏建立；**本轮仍不写任何 Runtime code**
> 基线      = HEAD c420403d5469241e8b03855428ebce435d539c9e · migration 0017_p13_seed · 0018+ = 0
>             Security DB Boundary = IMPLEMENTED + ACCEPTED · OI-G-1 = CLOSED
> ```

---

# 1. Human Decision 完成度（§十二 证明项 1）

```text
10 / 10 RTA 已完成 Human Decision：
  RTA-01 … RTA-08 = **AUTHORIZED**（8 项）
  RTA-09 = **OPTION B / SEPARATE**（Bootstrap CLI 不与 Runtime 同轮）
  RTA-10 = **OPTION B / SEPARATE SCHEMA DECISION**（不得隐式创建 schema support object）
  ID 完整性 = 无重复 · 无重编号 · 无第二套 RTA ID（Sheet 的 10 个 ID 与 Registry 一一对应）
载体 = P14_RUNTIME_IMPLEMENTATION_AUTHORIZATION_SHEET.md（**HUMAN AUTHORIZATION RESOLVED** ·
       Resolution Registry 为权威记录；§1 候选与勾选框保留为历史）
```

---

# 2. Runtime 主链授权范围（§十二 证明项 2）

```text
已授权（RTA-01…RTA-08）：
  · Authorization = AUTHORIZED
  · 范围 = Runtime process · API boundary · service layer · repository/persistence layer ·
          centralized authorization integration · identity/device/session workflow ·
          operational health · observability · 测试
  · 约束 = 严格服从 P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md 与
          P14_RUNTIME_IMPLEMENTATION_FILE_INVENTORY.md；**不得扩大 scope**
  · 连接身份 = uap_runtime（RTA-02）
  · 认证/授权/事务/错误/观测语义 = 依 RTA-03…RTA-08 冻结表述
```

---

# 3. Bootstrap CLI 明确排除（§十二 证明项 3）

```text
RTA-09 = OPTION B ⇒ BOOTSTRAP CLI = **OUT OF SCOPE**（本轮及 Runtime 实施轮内均不实现）
冻结不变量：
  Runtime API      ≠ Bootstrap CLI
  Runtime Principal ≠ Bootstrap Principal
禁止：Runtime 调用 Bootstrap CLI 作为 normal request path
实现时机：须另一独立的 implementation authorization
DB 层现状：uap_bootstrap 的 6 项权限已就位（已 ACCEPTED），但**未被任何代码使用**
```

---

# 4. Schema Support Object 排除 + 独立决策边界（§十二 证明项 4）

```text
RTA-10 = OPTION B ⇒ **不得隐式创建任何 schema support object**
  覆盖对象：table · view · materialized view · function · procedure · trigger · index ·
           sequence · type · schema
触发条件（实施期）：现有 schema 无法完成某功能
→ 登记 `SCHEMA DEPENDENCY DISCOVERED`
→ `STOP AT SCHEMA BOUNDARY`
→ 建立独立 `Schema Decision`

明令禁止：
  · 自行写 migration · 创建 0018 · 手动 DDL
  · 临时 CREATE VIEW / CREATE FUNCTION
  · 把 support object 藏在 test fixture
  · 把 schema modification 藏在 startup hook
```

---

# 5. Security Boundary 不被重新授权（§十二 证明项 5）

```text
本轮的授权**不包含**任何权限变更：
  · 未新增 role · 未 GRANT · 未 REVOKE · 未 ALTER ROLE
  · uap_runtime（51）/ uap_bootstrap（6）/ uap_app（5）/ uap_seed（0）/ uap_migrator（245）全部未变
  · pg_default_acl = 0 未变
若实施期发现缺 privilege ⇒ **STOP** 并建立 `SECURITY GAP`；**不得自行扩权**（§十四）
若实施期发现 required operation 被 PostgreSQL DENY ⇒ 报告 `SECURITY GRANT GAP` 并停止该 use-case（§十六）
```

---

# 6. Security Evidence Freeze 不间断保护（§十二 证明项 6）

```text
以下冻结资产在 Runtime implementation 期间**持续受保护**，不得被实施层修改：
  uap_runtime grants / uap_bootstrap grants / uap_app grants / uap_migrator grants /
  default_acl = 0 / C2 / CC-7 / P13 seed / ownership 拓扑 / 178 对象归属
获取方式：Runtime implementation **无权**自行 GRANT / REVOKE / ALTER ROLE / CREATE ROLE ——
          即使某功能"不方便"
监督方式：每次 milestone 后重跑 Security Regression（PRV-1…PRV-8）+ 冻结资产指纹对照
```

---

# 7. Implementation Guardrails（§十三）

```text
已建立：P14_RUNTIME_IMPLEMENTATION_GUARDRAILS.md（RUNTIME-G-01 … RUNTIME-G-15）
作用：在任何代码修改**之前**冻结 15 条实现禁令，作为实施期的即时判据
```

---

# 8. 首轮实施边界与顺序（§十五）

```text
下一轮（P14 RUNTIME IMPLEMENTATION）必须按序推进，不得一开始堆全部功能：
  1. Application Runtime bootstrap
  2. Runtime DB connection（uap_runtime）
  3. Persistence adapter
  4. Authorization integration
  5. Identity workflow
  6. Device workflow
  7. Session workflow
  8. API boundary
  9. Observability
 10. Acceptance tests

每层完成后的最低要求：compile → unit test → integration test → security regression
（阶段性通过 ≠ P14 最终 Gate；最终 Acceptance 仍须独立 Gate）

起步禁止：不许从 Bootstrap CLI / migration / 新 schema object 开始；不得修改 security grants。
```

---

# 9. 验收与 Git 政策（§十七 / §十八 / §十九 / §二十）

```text
Acceptance：
  · P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md 的 PLANNED 项可在**有真实 test evidence**后
    推进为 IMPLEMENTED / VERIFIED
  · **不得因代码写完就标 PASS**；必须区分 implemented 与 verified
  · 最终 Acceptance 须单独 Gate
安全测试义务：
  · Allowed tests：approved reads / writes / authorization lookups / onboarding /
                   device-session operations
  · Denied tests：resource_permissions mutation · platform_memberships mutation ·
                  platform_state mutation · tenants/spaces mutation · credential physical delete ·
                  schema DDL · role creation · migrator access
  · 目标：Runtime code 即使有 bug，PostgreSQL security boundary 仍是第二道防线
Git：
  · Runtime code 可修改；**COMMIT / TAG / PUSH 仍 FORBIDDEN**
  · 不得 stage 历史 dirty set
  · 每个 milestone 记录 `Runtime Implementation Change Boundary`
    （newly modified files / unrelated dirty files / frozen files untouched）
Migration / Schema：
  · 整个 Runtime implementation 期间 **0018+ = FORBIDDEN**
  · 发现任何 new table/view/function/trigger/index/schema/type/sequence ⇒
    `SCHEMA DECISION REQUIRED`（不自行 DDL、不建 migration、不用 startup migration）
```

---

# 10. 停止条件（§二十一 · 实施期适用）

```text
出现下列任一 ⇒ 立即 `BLOCKED / STOP` 并保留现场：
  Runtime 需要新 privilege / 修改 Security Matrix / 新 role / GRANT·REVOKE /
  修改 C2 / 修改 CC-7 / 改变 P13 seed / 新 schema object /
  Runtime architecture 与 frozen Contract 冲突 / Handler 出现 direct SQL /
  authorization 出现 bypass / Bootstrap CLI 被 Runtime path 依赖 /
  uap_migrator 出现在 Runtime connection path / uap_bootstrap 出现在 normal Runtime path /
  credential 出现在 logs / negative security probe unexpected ALLOWED
```

---

# 11. 本轮工程变更

```text
runtime code / API / service / repository / identity / device / session / authorization /
bootstrap CLI 实现 = 0
DDL = 0 · DML = 0 · migration = 0 · new role = 0 · GRANT = 0 · REVOKE = 0
新增文档 = 本报告 + P14_RUNTIME_IMPLEMENTATION_GUARDRAILS.md（2 份）
修改文档 = P14_RUNTIME_IMPLEMENTATION_AUTHORIZATION_SHEET.md（append-only Resolution Registry）
commit = 0 · tag = 0 · push = 0 · P15 = 未进入
P14 RUNTIME IMPLEMENTATION = 下一轮开始（本轮 = AUTHORIZATION CLOSED，未实施）
```

---

**END OF P14 RUNTIME IMPLEMENTATION AUTHORIZATION CLOSURE REPORT（2026-09-27 · **AUTHORIZATION CLOSED** · 10/10 RTA resolved · Runtime 主链 AUTHORIZED · Bootstrap CLI = OUT OF SCOPE · Schema support object = SEPARATE DECISION REQUIRED · Security Boundary 未被重新授权）**
