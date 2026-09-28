# UAP — P14 RUNTIME WAVE 2 IMPLEMENTATION AUTHORIZATION SHEET

> ## 状态
>
> ```text
> 状态      = **HUMAN AUTHORIZATION REQUIRED**（未授权 · 未实现）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · Wave 1 = ACCEPTED
> 前置      = Wave 2 HUMAN DECISION SHEET 36/36 全部 RESOLVED
>             （其中 5 项 Root Blocker 必须先裁决，见 DECISION DEPENDENCY LOCK §3）
> 铁律      = 本 Sheet 不含任何授权结论；每项均为待 Human 勾选
> ```

---

# 0. 授权前必须成立的前置条件

```text
P-1  Wave 2 Human Decision Sheet 36 / 36 = RESOLVED（无 PENDING）
P-2  5 项 Root Blocker（SCOPE-W2-01 · VOC-W2-01…04）已裁决且互相一致
P-3  Schema Register §3 的 5 项 VERIFICATION PENDING 已完成只读复核
P-4  DB Operation Matrix 未出现未解决的 `SECURITY GRANT GAP`
P-5  Wave 1 Foundation 未被要求改写（若有 ⇒ FOUNDATION REGRESSION RISK 已登记并单独评估）
P-6  测试治理沿用显式 allowlist（CF-C-4 per-file）
```

---

# 1. W2-AUTH-01 — Identity Implementation

```text
Scope        : identity 建立 / 状态推进 / 唯一性判定 / 凭据关联 / 停用撤销
依赖         : ID-W2-01…05 · VOC-W2-01/02/04 · CTX-W2-01
触碰文件（预计）: services/identity/**（新增）· infrastructure 复用（不改）
禁止         : 新建 schema 对象 · 新 role · 新 grant · 修改 core 契约语义
DB 操作      : 见 DB OPERATION MATRIX §2（全部命中既有授权）
验收         : ID-W2-* 对应 Acceptance + SEC-W2-01

Human Authorization
  [ ] AUTHORIZED   [ ] NOT AUTHORIZED   [ ] CUSTOM：__________
```

---

# 2. W2-AUTH-02 — Device Implementation

```text
Scope        : enrollment · binding · revoke · replacement
依赖         : W2-AUTH-01 + DV-W2-01…05 · VOC-W2-03
触碰文件（预计）: services/device/**（新增）
禁止         : 新建 challenge 表（除非进入独立 Schema Decision）· 新 grant
DB 操作      : DB OPERATION MATRIX §3
验收         : DV-W2-* 对应 Acceptance + SEC-W2-02

Human Authorization
  [ ] AUTHORIZED   [ ] NOT AUTHORIZED   [ ] CUSTOM：__________
```

---

# 3. W2-AUTH-03 — Session Implementation

```text
Scope        : creation · lifecycle · revoke · timeout · concurrency
依赖         : W2-AUTH-01/02 + SS-W2-01…05
触碰文件（预计）: services/session/**（新增）
禁止         : 由 handler 创建 session · 新建 schema 对象 · 新 grant
DB 操作      : DB OPERATION MATRIX §4
验收         : SS-W2-* 对应 Acceptance + SEC-W2-02/03

Human Authorization
  [ ] AUTHORIZED   [ ] NOT AUTHORIZED   [ ] CUSTOM：__________
```

---

# 4. W2-AUTH-04 — Authenticated Context Implementation

```text
Scope        : P14_RUNTIME_AUTHENTICATED_CONTEXT_CONTRACT 的可实现化
依赖         : CTX-W2-01…04 · (W2-AUTH-01…03 中已授权部分)
触碰文件（预计）: infrastructure/runtime/ 或 services/context（**须 Human 指定落点**）
禁止         : 携带 secret / 整行 record · 预授权 · 缓存判定
验收         : CTX-W2-* 对应 Acceptance + SEC-W2-04

Human Authorization
  [ ] AUTHORIZED   [ ] NOT AUTHORIZED   [ ] CUSTOM：__________
```

---

# 5. W2-AUTH-05 — Authorization Integration Implementation

```text
Scope        : authenticated subject → 既有 Stage 2 映射（薄 adapter，不重写引擎）
依赖         : AUTH-W2-01…03 + CTX-W2-04
触碰文件（预计）: services/authorization/（**仅允许增补适配**，不得改判定语义）
禁止         : 第二套 authorization engine · 新 permission vocabulary ·
                handler 内授权判断 · 改写 Stage 2 baseline
验收         : AUTH-W2-* 对应 Acceptance + SEC-W2-03

Human Authorization
  [ ] AUTHORIZED   [ ] NOT AUTHORIZED   [ ] CUSTOM：__________
```

---

# 6. W2-AUTH-06 — API Adaptation Implementation

```text
Scope        : authentication adapter · 请求→context · 错误映射 · FastAPI 装配
               （含 apps/api lifespan 是否接入 RuntimeApplication —— 由 Human 明确）
依赖         : API-W2-01…04 · (W2-AUTH-04/05 若已授权)
禁止         : handler → direct DB · handler 内业务编排 · API 拥有 business authority ·
                未授权情况下改写 livez/readyz 既有语义
验收         : API-W2-* 对应 Acceptance + Wave 1 health/ready 回归不劣化

Human Authorization
  [ ] AUTHORIZED   [ ] NOT AUTHORIZED   [ ] CUSTOM：__________
```

---

# 7. W2-AUTH-07 — Wave 2 Security Test Implementation

```text
Scope        : 按 SEC-W2-01…05 与 HUMAN DECISION SHEET §二十五 清单实现测试
  Identity : unauthenticated creation · duplicate identity · revoked / expired /
             invalid credential
  Device   : wrong user · reused device · revoked device · expired challenge ·
             replay challenge
  Session  : invalid / expired / revoked session · wrong device-user binding ·
             revoked identity
  Authz    : unauthorized tenant / space / resource · default deny · deny precedence
依赖         : 对应功能的实现授权（W2-AUTH-01…06）· 测试治理（显式 allowlist）
禁止         : 运行任何 CF-C-4 禁跑文件 · 目录级 pytest 参数 ·
                以 reset_test_database() 之外的方式破坏冻结基线
要求         : integration / security 测试必须使用 UAP_RUNTIME_TEST_DSN（缺省 SKIP，不回退）

Human Authorization
  [ ] AUTHORIZED   [ ] NOT AUTHORIZED   [ ] CUSTOM：__________
```

---

# 8. 明确不在本 Sheet 范围

```text
Bootstrap CLI            = **OUT OF SCOPE**（RTA-09 = OPTION B · 需独立授权）
Schema support objects   = **SEPARATE DECISION**（RTA-10 = B）
新 role / 新 grant        = 需独立 Security Decision
Wave 1 Foundation 改写    = 需 `FOUNDATION REGRESSION RISK` + 独立评估
P15                      = FORBIDDEN
```

---

# 9. 授权后的实施顺序（候选 · 非授权）

```text
1 Identity core workflow
2 Credential lifecycle integration
3 Device enrollment
4 Device revoke
5 Session creation
6 Session revoke / expiry
7 Authenticated Runtime Context
8 Existing Authorization integration
9 API adaptation
10 Wave 2 acceptance tests

（若 Human Decision Resolution 指定不同顺序，以正式 Resolution 为准）
```

---

# 10. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 8 份）· runtime code = 0 · DB 写 = 0
commit / tag / push = 0 · Wave 2 Implementation = NOT STARTED
```

**END OF P14 RUNTIME WAVE 2 IMPLEMENTATION AUTHORIZATION SHEET（2026-09-28 · HUMAN AUTHORIZATION REQUIRED · 7 项待裁 · HARD STOP ACTIVE）**

---

# 11. Decision Freeze 后的状态确认（2026-09-28 · append-only）

```text
本轮（P14 WAVE 2 HUMAN DECISION FREEZE）**不改变**本 Sheet 的任何授权状态：

  文件状态            = **HUMAN AUTHORIZATION REQUIRED**（保持）
  W2-AUTH-01 Identity                 = [ ] AUTHORIZED  [ ] NOT AUTHORIZED   ← 未勾选
  W2-AUTH-02 Device                   = [ ] AUTHORIZED  [ ] NOT AUTHORIZED   ← 未勾选
  W2-AUTH-03 Session                  = [ ] AUTHORIZED  [ ] NOT AUTHORIZED   ← 未勾选
  W2-AUTH-04 Authenticated Context    = [ ] AUTHORIZED  [ ] NOT AUTHORIZED   ← 未勾选
  W2-AUTH-05 Authorization Integration= [ ] AUTHORIZED  [ ] NOT AUTHORIZED   ← 未勾选
  W2-AUTH-06 API Adaptation           = [ ] AUTHORIZED  [ ] NOT AUTHORIZED   ← 未勾选
  W2-AUTH-07 Wave 2 Security Tests    = [ ] AUTHORIZED  [ ] NOT AUTHORIZED   ← 未勾选

变动的前置条件（§0 P-1…P-4）状态更新：
  P-1  36/36 Human Decision RESOLVED        → **已满足**（PDL 附录 P）
  P-2  Root Blocker 已裁决且互相一致          → **已满足**（SCOPE-W2-01 + VOC-W2-01…04）
  P-3  Schema Register 5 项复核完成           → **已满足**（live 只读复核 · 见 Register §3）
  P-4  DB Operation Matrix 无未解决 GRANT GAP → **已满足**（结论：既有 51 授权覆盖）
  P-5  Wave 1 Foundation 未被要求改写          → **已满足**（0 项 MUST 改写；见 Impact §7）
  P-6  测试治理沿用显式 allowlist              → **保持**（CF-C-4 per-file）

⇒ 前置条件全部满足，但 **implementation authorization 仍为 7 项待 Human 逐项裁决**。
⇒ Decision Freeze **不等于** Implementation Authorization。
```

**END OF AUTHORIZATION SHEET §11（2026-09-28 · 仍未授权 · 7 项全部未勾选 · HARD STOP ACTIVE）**

---

# 12. HUMAN AUTHORIZATION GRANTED（2026-09-28 · 授权登记 · append-only）

> 本轮 Human 指令「P14 — WAVE 2 IMPLEMENTATION AUTHORIZATION + IDENTITY / DEVICE / SESSION」
> 已逐项授权。§11 的历史「未勾选」状态**保留为历史**（不得改写）。

```text
W2-AUTH-01 Identity                    = **AUTHORIZED**
W2-AUTH-02 Device                      = **AUTHORIZED**
W2-AUTH-03 Session                     = **AUTHORIZED**
W2-AUTH-04 Authenticated Context       = **AUTHORIZED**
W2-AUTH-05 Authorization Integration   = **AUTHORIZED**
W2-AUTH-06 API Adaptation              = **AUTHORIZED**
W2-AUTH-07 Wave 2 Security Tests       = **AUTHORIZED**

同轮边界（Human 明示）
  Bootstrap CLI          = OUT OF SCOPE
  Schema Support Objects = SEPARATE DECISION
  New Role               = FORBIDDEN
  New Grant              = FORBIDDEN
  Migration 0018+        = FORBIDDEN
  P15                    = FORBIDDEN
  COMMIT / TAG / PUSH    = FORBIDDEN

实施结果（详见 P14_RUNTIME_IMPLEMENTATION_WAVE2_REPORT.md）
  Wave 2 = IMPLEMENTED + VERIFIED（68 Wave 2 passed · 211 Wave 1 regression passed）
  Schema Mutation = 0 · Grant Mutation = 0 · Security Boundary = INTACT
```

**END OF AUTHORIZATION SHEET §12（2026-09-28 · 7 项 AUTHORIZED 并已实施验证 · HARD STOP ACTIVE）**
