# UAP — P14 OVERALL FINAL ACCEPTANCE REPORT

> ## 状态
>
> ```text
> 轮次      = P14 OVERALL FINAL ACCEPTANCE + RELEASE READINESS GATE
> 基线      = HEAD c420403d5469241e8b03855428ebce435d539c9e · main · tags 9 · remote 0 · staged 0
> 结论      = **P14 OVERALL ACCEPTANCE = PASS**（D-02 经 Human 裁决 OPTION B 关闭）
> 其余      = Security Boundary · Wave 1 · Wave 2 · Cross-wave · Schema · Privilege ·
>             ENV-1 · D-01 · OI 矩阵 全部 PASS / CLOSED / DEFERRED-without-blocking
> ```
>
> ### D-02 Human 裁决（2026-09-28 · canonical registration = PDL 附录 Q）
>
> ```text
> Selected = **OPTION B**
>   · 不授权测试库重建（无 reset）· 不授权 GRANT/REVOKE replay
>   · 不授权 schema / migration / role 操作
>   · **不改变 Wave 1 frozen artifact**（原始 `assert audit == 0` 保持并冻结）
>   · 该断言 = Wave-1-only baseline 断言；其在含 append-only EXPECTED TEST DATA 的库状态下的
>     失败 = **环境状态产物**（非代码回归 · 非验收缺陷）
>   · 审计不变量由独立 Wave 2 测试覆盖（test_wave2_audit_invariant.py · 4 用例）
> ⇒ D-02 = **CLOSED** ⇒ 唯一 blocking item 解除
> ```

---

# 1. Executive Summary

```text
P14 = Wave 1（runtime foundation）+ Wave 2（Identity/Device/Session/Context/Authz/API）
      + Security DB Boundary，均 IMPLEMENTED + VERIFIED 且已 ACCEPTED。

本轮 Overall Gate 的全部实质判据均通过：
  · Decision freeze 完整性（36/36 Wave 2 + SEC-P14-01…14 + RTA-01…10）· PDL 附录 O/P 未改写
  · Security Evidence Freeze INTACT（roles/grants/ownership/default_acl/C2/P13/schema 全未变）
  · Wave 2 = 72 passed · Wave 1 frozen set = 210 passed
  · Schema Mutation = 0 · Privilege Mutation = 0 · Formal DB prestate == poststate
  · ENV-1 CLOSED（依赖清单 + 干净环境验证）· D-01 DEFERRED/NON-BLOCKING（active path 已排除）

原唯一阻塞项 **D-02** 已由 Human 裁决 **OPTION B** 关闭（PDL 附录 Q）：
按 §七 Step A 已把 Wave 1 的 `assert audit_logs == 0` **逐字节恢复且不再改动**；
audit_logs 为 append-only 且含 926 行 Wave 2 EXPECTED TEST DATA（§二十七 明令不得强制归零），
故该断言在本库状态下的失败被裁决为**环境状态产物**，审计不变量改由独立 Wave 2 测试覆盖。
详见 P14_OVERALL_OI_CLOSURE_MATRIX.md「D-02 证据与阻塞说明」。
```

---

# 2. P14 Scope

```text
Wave 1（ACCEPTED）：Application Bootstrap · Configuration · uap_runtime Connection ·
  Principal Verification · Pool · Transaction · Persistence Adapter · Domain Boundary ·
  Authorization Integration Boundary · Lifecycle · Health · Observability · Error Taxonomy
Wave 2（ACCEPTED）：Identity · Credential · Device · Session · Authenticated Context ·
  Stage 2 Authorization integration · API adaptation · Wave 2 security tests
Security DB Boundary（ACCEPTED）：uap_runtime 51 · uap_bootstrap 6 精确授权面
明确排除：Bootstrap CLI（OUT OF SCOPE）· Schema support objects（SEPARATE DECISION）· P15（FORBIDDEN）
```

---

# 3. Decision Freeze

```text
P14 Runtime Decisions  = FROZEN（附表 N）
P14 Security Decisions = FROZEN（附录 O：SEC-P14-01…14 · 14 resolved · 0 unresolved · 0 UNKNOWN）
P14 Wave 2 Decisions   = FROZEN（附录 P：36/36 · 0 unresolved）
Authorization traces   = RTA-01…08 AUTHORIZED · RTA-09/10 = OPTION B · W2-AUTH-01…07 AUTHORIZED
一致性检查：无未决 Decision · implementation 与 frozen Decision 无冲突 ·
  无 obsolete model 被当现行 · 无重复词表 · 无第二套 authorization engine ·
  无第二套 DB principal model（runtime 仍唯一使用 uap_runtime）
```

---

# 4. Security Boundary

```text
uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 · uap_migrator 245（全部未变）
roles = 6（属性未变）· user memberships = 0 · default_acl = 0 · ownership residual = 0
public nspacl 未变 · schema CREATE=false 未变 · function EXECUTE（runtime/bootstrap/app/seed）= 0
C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff（未变）· CC-7 触发器存在且 enabled=O
P13 seed = registry 3 / permissions 12 / role_permissions 12（未变）
⇒ Security Evidence Freeze = **INTACT**
```

---

# 5. Wave 1 Acceptance

```text
Wave 1 = ACCEPTED（FINAL ACCEPTANCE REPORT §21 ACCEPTED）
本轮复测：Architecture 28 · Contract 23 · Runtime Unit 20 · Runtime Integration 13 ·
  Security Regression 46 · Acceptance subset 81
⇒ **210 passed · 1 failed**（唯一失败 = D-02 的 audit 基线断言 · 见 §7）
Wave 1 基础行为（bootstrap / connection / pool / transaction / lifecycle / health /
  observability / error taxonomy / authz boundary）均未被 Wave 2 破坏
```

---

# 6. Wave 1 Incident

```text
CF-C-4 TEST EXECUTION SCOPE VIOLATION（2026-09-28）：
  classified ✅（INCIDENT REPORT 保留原文 · 未重写为"未发生"）
  recovered  ✅（uap_b1_test 逐指纹恢复 · 28 项键 0 diff）
  governed   ✅（TEST EXECUTION MANIFEST 逐文件 allowlist · 19+1 禁跑清单）
  prevented  ✅（Wave 1 与 Wave 2 两轮均以显式文件参数执行 · Forbidden tests executed = 0）
历史证据：INCIDENT REPORT 与 INCIDENT RECOVERY REPORT **完整保留**
```

---

# 7. Wave 2 Acceptance

```text
Wave 2 = ACCEPTED（IMPLEMENTATION WAVE 2 REPORT · §15）
本轮复测（显式 allowlist）：Unit 14 · Identity 12 · Device 13 · Session 11 ·
  Authorization 10 · API 6 · **Audit invariant 4（本轮新增）** ⇒ **72 passed · 0 failed**
新增独立测试（§七 Step B）：tests/integration/test_wave2_audit_invariant.py
  · 纯读路径不追加审计（+0）
  · 成功认证恰好 +1 · 拒绝认证恰好 +1（result=denied · 不含明文口令）
  · device revoke 恰好 +1（action=device.revoked · risk=HIGH · metadata 含 sessions_revoked=1）
⇒ "Wave 2 audit invariant = independently tested" 成立
```

---

# 8. Cross-Wave Verification

```text
Wave1 foundation → Wave2 Identity → Device → Session → Authorization → API
  · application startup → authenticated flow：apps/api lifespan 复用 Wave 1 RuntimeApplication
    （uap_runtime principal 断言）· API 端到端登录/session/logout 往返通过
  · DB connection → identity persistence：users+identities+credentials 单事务落库
  · transaction → device/session atomicity：device revoke 与其 active sessions 同事务
  · auth context → authorization：ContextBuilder + AuthorizationAdapter → Stage 2（default deny）
  · authorization → API：无 tenant membership ⇒ 403 · 多候选 ⇒ 400 context_required
  · API error mapping → security：8 类 → 401/403/400/422/409/503/500 · 安全类模糊化
  · observability → redaction：describe()/log_fields() 白名单 · no_secrets 通过
⇒ Cross-wave verification = **PASS**
```

---

# 9. Schema Boundary

```text
new tables = 0 · views = 0 · functions = 0 · triggers = 0 · indexes = 0 ·
sequences = 0 · types = 0 · schema = 0 · migrations = 0
实测：pg_class 156 · pg_proc 22 · pg_trigger 272 · parent triggers 39（与冻结基线一致）
alembic = 0017_p13_seed · 0018+ = 0 · migrations_alembic/** 未修改
⇒ Wave 1 + Wave 2 均未突破 RTA-10
```

---

# 10. Privilege Boundary

```text
CREATE ROLE / GRANT / REVOKE / ALTER ROLE = 0（Wave 1 · Wave 2 · 本轮）
uap_runtime / uap_bootstrap / uap_app / uap_migrator / uap_seed = 全部 unchanged
无 new role · 无 new grant · 无 role membership drift · 无 default ACL drift
Security Grant Gap = NONE（Wave 2 主链操作全部落在既有 51 项授权内）
```

---

# 11. Test Governance

```text
CF-C-4 = 逐文件 allowlist（Wave 1 manifest + Wave 2 manifest）
本轮执行：Wave 1 frozen set 17 文件 + Wave 2 set 9 文件（+ 干净 venv 4 文件）
Forbidden tests executed = **0**（19 个 CF-C-4 文件 + OI-G-4 文件均未执行）
未使用任何目录级 pytest 参数
```

---

# 12. Dependency Reproducibility

```text
ENV-1 = **CLOSED**
  权威清单（pyproject.toml [project].dependencies + requirements.txt）各加 `argon2-cffi==25.1.0`
  干净 venv 从清单安装（exit 0）→ import argon2 25.1.0 → Wave2 Unit + Wave1 taxonomy = 20 passed
  → 哈希前缀 argon2id · verify True · 错误口令拒绝
⇒ 不再依赖"机器上刚好装过的包"
```

---

# 13. OI Matrix

```text
P14_OVERALL_OI_CLOSURE_MATRIX.md 已生成，含 OI-G-1 · OI-G-4 · OI-G-9 · D-01 · D-02 ·
  ENV-1 · FINDING-AUTHZ-1 · FINDING-ENGINE-1 · FINDING-P11-1 · FINDING-IDX-1
状态分布：CLOSED 2（OI-G-1 · ENV-1）· DEFERRED 2（D-01 · FINDING-AUTHZ-1）·
  ACCEPTED 1（FINDING-ENGINE-1）· OPEN/REGISTERED 2（OI-G-4 · OI-G-9 · 非阻断）·
  INFO 2 · **BLOCKED 1（D-02）**
⇒ 存在 1 个 blocking item ⇒ Overall = BLOCKED（§三十六）
```

---

# 14. Known Deferred Findings

```text
D-01      DEFERRED / NON-BLOCKING FOUNDATION MAINTENANCE
          （Wave 1 persistence.py 未改 · SafeReader = approved path · active path 已排除）
FINDING-AUTHZ-1  ACCEPTED / DEFERRED CAPABILITY（管理类操作需独立 Human Decision）
FINDING-ENGINE-1 ACCEPTED COMPATIBILITY FINDING（P14 内不重构）
OI-G-4 / OI-G-9  BATCH-D / maintenance（非阻断 · 未修）
```

---

# 15. Git Integrity

```text
HEAD = c420403d5469241e8b03855428ebce435d539c9e（未变）
branch = main（未变）· tags = 9（未变）· remote = 0 · staged = 0
prestate dirty = 204 → 本轮结束 dirty = 207（+3：OI 矩阵 · 本报告 · 审计不变量测试）
  （实测校正：prestate dirty = 204 → poststate = 209，新增 5 条路径：
    pyproject.toml · requirements.txt · OI 矩阵 · 本报告 · tests/integration/test_wave2_audit_invariant.py）
历史 dirty set 未 stage · COMMIT / TAG / PUSH = 0 / 0 / 0
```

---

# 16. DB Integrity

```text
Formal DB uap：prestate == poststate = **True**（本轮仅只读）
  （pg_class 0 · pg_proc 0 · default_acl 0 · memberships 0 · roles 6 · grants 仅 uap 隐式）
Test DB uap_b1_test：边界锚点全部未变（见 §4）
  EXPECTED TEST DATA：audit_logs（append-only · 不可删除 · **不得强制归零**）
    本轮 Wave 2 结束时 926 行 → 最终验收轮结束时实测 **1169 行**（增量来自本轮重跑）
  users / identities / credentials / devices / sessions / tenants / spaces /
  memberships / tenant_memberships = 0（已清理回基线）· roles = 1（platform_admin）·
  platform_state = 1（未初始化）
```

---

# 17. Acceptance Mapping

```text
P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md §20 已做最终归类：
  VERIFIED / IMPLEMENTED / ACCEPTED / DEFERRED / OUT OF SCOPE / SEPARATE DECISION
无 MAYBE / TBD / UNKNOWN；Deferred 未当作 PASS
```

---

# 18. Final Disposition

```text
P14 OVERALL ACCEPTANCE = **PASS**
P14 Overall Status     = **ACCEPTED**（IMPLEMENTED + VERIFIED + ACCEPTED）

成立依据
  · D-02 = CLOSED（Human OPTION B · PDL 附录 Q）
  · Security Boundary / Evidence Freeze = INTACT
  · Wave 1 = ACCEPTED（artifact 完整 · frozen set 210/211，唯一失败项 = 已裁决的环境状态产物）
  · Wave 2 = ACCEPTED（72 passed）
  · Cross-wave = VERIFIED · Schema/Privilege Mutation = 0 · Formal DB Mutation = 0
  · ENV-1 = CLOSED（依赖清单 + 干净环境验证）
  · D-01 = DEFERRED / NON-BLOCKING（active path 已排除）
  · FINDING-AUTHZ-1 = DEFERRED · FINDING-ENGINE-1 = ACCEPTED（均非阻断）
  · OI 矩阵：blocking item = 0

本轮不做（明确边界）
  RELEASE / COMMIT / TAG / PUSH / P15 / Bootstrap CLI / 任何 schema 或权限变更
  ⇒ Overall Accepted ≠ Released；Release 需另开 P14 RELEASE PREPARATION + RELEASE GATE

后续变更规则（§三十二 Final Evidence Freeze）
  任何对 P14 已接受行为的修改 ⇒ 新开 CHANGE / MAINTENANCE DECISION，不得直接在工作树覆盖
```

**END OF P14 OVERALL FINAL ACCEPTANCE REPORT（2026-09-28 · P14 OVERALL = PASS / ACCEPTED · D-02 CLOSED by Human OPTION B · 未 commit/tag/push · HARD STOP ACTIVE）**
