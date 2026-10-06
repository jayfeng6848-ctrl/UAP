# UAP — P14 RELEASE SCOPE LOCK

> ```text
> 轮次 = P14 RELEASE PREPARATION（2026-09-28）
> 性质 = Release Candidate 范围锁定（**不是** release 授权）
> 铁律 = Release Candidate scope does not grant permission to modify any excluded item.
> ```

---

# 1. Included（Release Candidate 允许包含）

```text
INC-1  P14 Runtime implementation（Wave 1 foundation）
INC-2  P14 Wave 2 accepted implementation（Identity / Credential / Device / Session /
       Authenticated Context / Authorization Integration / API Adaptation）
INC-3  P14 security boundary（uap_runtime 51 · uap_bootstrap 6 精确授权面 · 已 ACCEPTED）
INC-4  P14 dependency declaration（pyproject.toml + requirements.txt · argon2-cffi==25.1.0）
INC-5  P14 accepted tests（Wave 1 frozen set + Wave 2 security/unit/integration + audit invariant）
INC-6  P14 release documentation（本目录内的 release-prep 文档集）
INC-7  P14 acceptance evidence（Wave 1 / Wave 2 / Overall Acceptance / OI matrix / mapping）
```

---

# 2. Excluded（明确排除 · 不在本 RC 内）

```text
EXC-1   P15（任何 P15 文档 / decision / implementation）
EXC-2   future admin device-management capability（管理他人设备/会话/凭据）
EXC-3   D-01 foundation repair（infrastructure/database/persistence.py）
EXC-4   FINDING-ENGINE-1 重构（/ready 探针与 RuntimeDatabase 的 engine 统一）
EXC-5   new authorization actions（canonical vocabulary 扩展）
EXC-6   new schema（任何 table/view/function/trigger/index/sequence/type/schema）
EXC-7   new migration（0018+）
EXC-8   new DB principal（任何角色）
EXC-9   new runtime grants（GRANT / REVOKE / ALTER ROLE）
EXC-10  new RLS policy
EXC-11  new API capability（超出 §三十一 允许范围的端点：admin CRUD / permission admin /
        role admin / bootstrap / migration / schema 端点）
EXC-12  new bootstrap CLI（RTA-09 = OPTION B · OUT OF SCOPE）
EXC-13  new multi-instance infrastructure
```

---

# 3. 声明

```text
· 本 Scope Lock 为**范围声明**，不构成任何实施授权。
· Release Candidate scope **does not grant permission to modify any of the excluded items.**
· 任何对 EXC-1…EXC-13 的需求 ⇒ 新开 CHANGE / MAINTENANCE DECISION，不得在本轮或 release 轮顺手修改。
· 已被裁定关闭的事项（D-02 OPTION B）不得被复用为重新讨论的范围入口：
  Wave 1 frozen artifact 保持不动，测试库不重建，不做 GRANT/REVOKE replay。
```

---

# 4. 与既有冻结边界的关系

```text
继续生效
  · P14 Security Evidence Freeze（roles/grants/ownership/default_acl/C2/CC-7/P13 seed）
  · Wave 1 Evidence Freeze（FINAL ACCEPTANCE §28）
  · Wave 2 Decision Freeze（PDL 附录 P · 36/36）
  · D-02 裁决（PDL 附录 Q · OPTION B）
  · CF-C-4 逐文件 allowlist 测试治理
```

**END OF P14 RELEASE SCOPE LOCK（2026-09-28 · Included 7 · Excluded 13 · 不构成实施授权 · HARD STOP ACTIVE）**
