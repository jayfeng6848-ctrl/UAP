# UAP — P14 RUNTIME WAVE 2 DECISION IMPACT ANALYSIS

> ## 状态
>
> ```text
> 状态      = **DECISION PREPARATION**（影响分析 · 未实施）
> 依据      = P14_RUNTIME_WAVE2_HUMAN_DECISION_SHEET.md（36 项）·
>             Wave 1 FINAL ACCEPTANCE REPORT（Foundation 冻结）
> 口径      = NO CHANGE（N）· CANDIDATE CHANGE AFTER HUMAN DECISION（C）·
>             MUST CHANGE AFTER HUMAN DECISION（M）
> 铁律      = 本分析**不预设**任何选项；M/C 仅表示"该决定一旦作出将影响该层"
> ```

---

# 1. 影响矩阵

维度缩写：

```text
W1F = Wave 1 Foundation（Bootstrap/Connection/Pool/Transaction/Persistence/Lifecycle/
      Health/Observability/Error Taxonomy/Authz Integration Boundary）
SB  = Security DB Boundary（uap_runtime 51 / uap_bootstrap 6 / default ACL / ownership）
ID  = Identity · DV = Device · SS = Session · AZ = Authorization(Stage 2) · API = API 层
P   = Persistence（repository/adapter 面）· OBS = Observability · ACC = Acceptance/测试
```

| Decision | W1F | SB | ID | DV | SS | AZ | API | P | OBS | ACC |
|---|---|---|---|---|---|---|---|---|---|---|
| SCOPE-W2-01 | N | N | C | C | C | N | C | C | N | M |
| VOC-W2-01 | N | N | M | M | M | C | N | M | N | M |
| VOC-W2-02 | N | N | M | N | C | N | N | M | N | M |
| VOC-W2-03 | N | N | N | M | M | N | N | M | N | M |
| VOC-W2-04 | N | N | M | C | M | C | N | M | N | M |
| ID-W2-01 | N | N | M | C | N | C | C | M | N | M |
| ID-W2-02 | N | N | M | C | C | C | N | M | N | M |
| ID-W2-03 | N | C | M | N | N | N | N | M | N | M |
| ID-W2-04 | N | N | M | N | C | N | N | M | N | M |
| ID-W2-05 | N | N | M | M | M | C | N | M | N | M |
| DV-W2-01 | N | N | C | M | C | C | C | M | N | M |
| DV-W2-02 | N | C | N | M | C | N | N | M | N | M |
| DV-W2-03 | N | C | N | M | C | N | C | M | N | M |
| DV-W2-04 | C | N | N | M | M | N | N | M | N | M |
| DV-W2-05 | N | N | N | M | C | N | N | M | N | M |
| SS-W2-01 | C | N | M | M | M | C | C | M | N | M |
| SS-W2-02 | N | N | N | N | M | C | N | M | N | M |
| SS-W2-03 | C | N | C | C | M | C | N | M | N | M |
| SS-W2-04 | N | C | N | N | M | N | N | M | N | M |
| SS-W2-05 | N | N | N | N | M | C | N | M | C | M |
| CTX-W2-01 | N | N | C | C | M | M | C | C | N | M |
| CTX-W2-02 | N | N | C | N | C | M | C | C | N | M |
| CTX-W2-03 | N | N | N | N | N | N | C | N | M | M |
| CTX-W2-04 | N | N | N | N | N | M | C | C | N | M |
| AUTH-W2-01 | N | N | N | N | N | M | C | N | N | M |
| AUTH-W2-02 | N | N | N | N | N | M | M | N | N | M |
| AUTH-W2-03 | N | C | C | C | C | C | N | M | C | M |
| API-W2-01 | N | N | N | N | N | N | M | N | N | M |
| API-W2-02 | N | N | C | C | C | N | M | C | N | M |
| API-W2-03 | N | N | N | N | N | C | M | C | N | M |
| API-W2-04 | N | N | N | N | N | C | M | N | C | M |
| SEC-W2-01 | N | N | M | N | N | N | C | M | N | M |
| SEC-W2-02 | N | N | C | M | C | N | C | M | C | M |
| SEC-W2-03 | N | N | N | N | N | M | C | N | N | M |
| SEC-W2-04 | N | N | M | M | M | N | C | M | M | M |
| SEC-W2-05 | N | N | M | N | N | N | N | M | N | M |

```text
统计（N / C / M）
  W1F : 34 / 2 / 0      ← 仅 SCOPE-W2-01 与 DV/SS 相关项可能影响 Foundation 侧语义
  SB  : 33 / 3 / 0      ← 无 MUST；可能产生 SECURITY GRANT GAP（见 §3）
  AZ  : 19 / 12 / 5
  API : 13 / 12 / 11
  ACC : 0 / 0 / 36      ← 每项决定都会改变验收面（必然）
```

---

# 2. Wave 1 Foundation 影响（重点）

```text
标记为 C 的三处（**均未构成 MUST**，且都不是"改写 Wave 1 已验收行为"）：
  DV-W2-04（device revoke 原子性）→ 需要**使用** Wave 1 Transaction Boundary
                                     （复用，不修改）
  SS-W2-01（session 创建前置）    → 同上（复用事务边界 + principal）
  SS-W2-03（revoke 传播矩阵）     → 同上

⇒ 结论：36 项决定中**没有一项**要求改写 Wave 1 已验收的行为语义。
   若 Human 最终选择的选项确实要求改写（例如修改 transaction 语义 / lifecycle /
   repository 契约 / authorization integration），必须先登记：
        `FOUNDATION REGRESSION RISK` / `WAVE1 FOUNDATION CHANGE REQUIRED`
   并按 FINAL ACCEPTANCE REPORT §28 的 Evidence Freeze 规则单独提出影响评估。
```

---

# 3. Security Boundary 影响与 Escalation 触发条件

```text
标记为 C 的四处（可能触发 Security 侧动作）：
  ID-W2-03（唯一性）      → 若需 DB 层唯一约束 ⇒ `SCHEMA DEPENDENCY`（RTA-10）
  DV-W2-02（ownership）   → 若需 fingerprint 唯一约束 ⇒ `SCHEMA DEPENDENCY`
  DV-W2-03（challenge）   → 若判定必须新增表 ⇒ `SCHEMA DEPENDENCY`
  SS-W2-04（并发）        → 若需 session 唯一约束 ⇒ `SCHEMA DEPENDENCY`

任何一项若最终要求新增 privilege（GRANT / REVOKE / ALTER ROLE）：
  → 登记 `SECURITY GRANT GAP` → **STOP** → 独立 Security Decision
  （OI-G-1 已 CLOSED 不构成自动扩权许可 · SEC-14 = EXACT LEAST-PRIVILEGE GRANT）
```

---

# 4. 与既有决策的一致性检查

```text
本 36 项决定**不**修改以下既有对象（只作输入）：
  SEC-P14-01…14（PDL 附录 O）· D-PLAT-* · D-AUTH-* · D-OP101-01…14 ·
  D-P13-01…15 · RTA-01…10 · RTA/CF/BB 系列

冲突扫描结果（本轮只读）
  · 无决定与既有 SEC-P14 冲突（SEC-05/06/07/08/09/13/14 均被本 Sheet 引用而非改写）
  · 无决定要求修改 C2 / CC-7 / P13 seed（已在 Scope EX-9…EX-11 明确排除）
  · 唯一"语义落差"为 §5 的 CONTRACT DIVERGENCE D-1…D-8 —— 已登记为 VOC-W2-01…04，
    属**待裁决**而非冲突：裁决后不要求修改任何既有冻结正文
```

---

# 5. 未决影响（Unknown = 0 声明）

```text
本分析覆盖 36 / 36 决定 × 10 维度 = 360 个影响单元，**无 UNKNOWN 单元**。
凡"具体参数未定"者（如 SS-W2-05 秒数、DV-W2-03 TTL），其影响对象仍被明确标识为 M/C，
不构成未知边界。
```

---

# 6. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 8 份）· runtime code = 0 · DB 写 = 0 · migration = 0
commit / tag / push = 0
```

**END OF P14 RUNTIME WAVE 2 DECISION IMPACT ANALYSIS（2026-09-28 · 36 decisions × 10 dimensions · 无 MUST 改写 Foundation · HARD STOP ACTIVE）**

---

# 7. 裁决后最终影响状态（§四十二 · 2026-09-28 Human Freeze）

> 口径切换为裁决后三态：`NO CHANGE` / `IMPLEMENTATION MAPPING REQUIRED` / `DEFERRED`。
> **不得**存在 MAYBE / TBD / UNKNOWN。§1 的维度矩阵保留为**决策前分析**（历史）。

| Decision | 最终状态 | 说明（裁决依据 → 实现含义） |
|---|---|---|
| SCOPE-W2-01 | IMPLEMENTATION MAPPING REQUIRED | §三 ⇒ 必须新增 anti-corruption mapping 层（Domain ↔ 0017） |
| VOC-W2-01 | IMPLEMENTATION MAPPING REQUIRED | §四/§五 ⇒ Domain Identity ↔ `users.id` anchor 显式映射 |
| VOC-W2-02 | IMPLEMENTATION MAPPING REQUIRED | §七 ⇒ Domain CredentialType ↔ `credentials.type` 映射（仅 password 实现） |
| VOC-W2-03 | IMPLEMENTATION MAPPING REQUIRED | §八 ⇒ Domain 3 态 ↔ DB 5 态映射（不得二值化） |
| VOC-W2-04 | IMPLEMENTATION MAPPING REQUIRED | §九/§十 ⇒ user 5 态 + identity 4 态两张映射表 |
| ID-W2-01 | IMPLEMENTATION MAPPING REQUIRED | onboarding use-case（含 abuse 边界） |
| ID-W2-02 | NO CHANGE | 状态集合直接取自 0017 `identities.status` |
| ID-W2-03 | NO CHANGE | 沿用既有唯一索引（全局 / lower / soft-delete 释放） |
| ID-W2-04 | NO CHANGE | 0017 已强制双 FK NOT NULL（应用层校验一致性） |
| ID-W2-05 | IMPLEMENTATION MAPPING REQUIRED | revoke 传播矩阵需 service 同事务实现 |
| DV-W2-01 | IMPLEMENTATION MAPPING REQUIRED | challenge + verification 两步流程 |
| DV-W2-02 | NO CHANGE | 沿用 `UNIQUE(user_id, fingerprint)`；应用层补充 trust policy |
| DV-W2-03 | IMPLEMENTATION MAPPING REQUIRED | challenge 需落在既有载体（无新表） |
| DV-W2-04 | IMPLEMENTATION MAPPING REQUIRED | device+session 同事务原子 revoke |
| DV-W2-05 | NO CHANGE | 不 auto-kick；并发 enrollment 由 SEC-W2-03 语义覆盖 |
| SS-W2-01 | IMPLEMENTATION MAPPING REQUIRED | use-case 强制 device 绑定（schema nullable 不改） |
| SS-W2-02 | NO CHANGE | 状态集合与 DB 一致 |
| SS-W2-03 | IMPLEMENTATION MAPPING REQUIRED | granular revoke 矩阵需按 scope 实现 |
| SS-W2-04 | NO CHANGE | 无需新约束；并发会话为默认行为 |
| SS-W2-05 | IMPLEMENTATION MAPPING REQUIRED | 双上限 + 配置化 TTL + 每请求校验 |
| CTX-W2-01 | IMPLEMENTATION MAPPING REQUIRED | 7 项最小 context + assurance 派生 |
| CTX-W2-02 | IMPLEMENTATION MAPPING REQUIRED | tenant/space fail-closed 矩阵（service 解析） |
| CTX-W2-03 | NO CHANGE | 沿用 Wave 1 脱敏白名单（不新增字段面） |
| CTX-W2-04 | NO CHANGE | 不预构造 AuthorizationRequest / 不缓存判定 |
| AUTH-W2-01 | IMPLEMENTATION MAPPING REQUIRED | effect 仅 allow/deny；RequiresApproval 无实现路径 |
| AUTH-W2-02 | NO CHANGE | 既有 RUNTIME-G-04/05 与 DL-2 已定义判定位置 |
| AUTH-W2-03 | IMPLEMENTATION MAPPING REQUIRED | audit 写入点与 payload 白名单 |
| API-W2-01 | NO CHANGE | 既有 API 定位（transport/adaptation） |
| API-W2-02 | IMPLEMENTATION MAPPING REQUIRED | 路由面按 §三十一 清单实现 |
| API-W2-03 | NO CHANGE | 既有链路（HTTP→adapter→context→authz→service） |
| API-W2-04 | IMPLEMENTATION MAPPING REQUIRED | 8 类错误 → HTTP 映射表 + security 类模糊化 |
| SEC-W2-01 | NO CHANGE | 默认拒绝语义（SEC-P14-03 已冻结） |
| SEC-W2-02 | NO CHANGE | 沿用 Wave 1 redaction（六面禁泄露） |
| SEC-W2-03 | IMPLEMENTATION MAPPING REQUIRED | challenge/session material 的 bounded+single-use 语义 |
| SEC-W2-04 | IMPLEMENTATION MAPPING REQUIRED | 传播矩阵 + 事务边界（与 ID/DV/SS 同理） |
| SEC-W2-05 | NO CHANGE | 无 role/grant/C2/CC-7/uap_runtime 变更 |

```text
统计：NO CHANGE = 16 · IMPLEMENTATION MAPPING REQUIRED = 20 · DEFERRED = 0
（D-9 / REQUIRES_APPROVAL 属 AUTH-W2-01 决议内的 **DEFERRED 子项**，
  不另设为第 37 项 Decision。）

Foundation 影响（复核）：**0 项**要求改写 Wave 1 已验收行为；
  所有"IMPLEMENTATION MAPPING REQUIRED"项均为**新增实现**（service/repository/API 面），
  复用而不修改 Wave 1 的 Connection / Transaction / Persistence / Lifecycle / Taxonomy /
  Observability / Authorization Integration Boundary。
  若实现期出现改写需求 ⇒ 登记 `FOUNDATION REGRESSION RISK` 并 STOP。

MAYBE / TBD / UNKNOWN = 0
```

**END OF IMPACT ANALYSIS §7（2026-09-28 · 裁决后三态 · 无 MAYBE/TBD/UNKNOWN · HARD STOP ACTIVE）**
