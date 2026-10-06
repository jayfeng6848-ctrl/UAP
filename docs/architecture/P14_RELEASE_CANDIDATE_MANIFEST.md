# UAP — P14 RELEASE CANDIDATE MANIFEST

> ```text
> Project                 = UAP
> Phase                   = P14 Runtime Slice
> Status                  = **RELEASE CANDIDATE PREPARED**
> Acceptance              = ACCEPTED（P14 OVERALL = PASS）
> Decision Integrity      = PASS
> Security Boundary       = PASS
> Wave 1                  = ACCEPTED
> Wave 2                  = ACCEPTED
> Cross-Wave              = PASS
> D-01                    = DEFERRED / NON-BLOCKING
> D-02                    = CLOSED（Human OPTION B · PDL 附录 Q）
> ENV-1                   = CLOSED
> P15                     = NOT STARTED
> Commit                  = NOT YET
> Tag                     = NOT YET
> Push                    = NOT YET
> ```

---

# 1. Release Candidate Identity（§15 · 不创建 Git 版本身份）

```text
Release status   = **CANDIDATE**
Git commit       = **NOT CREATED**
Tag              = **NOT CREATED**
Push             = **NOT PERFORMED**
version          = **VERSION_PENDING_RELEASE_GATE**

命名约定观察（只读）
  · 既有 tag 命名 = `UAP-V<semver>-<PHASE-SLUG>`（9 条 · 全部 annotated）
  · 最后 tag = `UAP-V0.1.9-P13-SEED`（指向 c420403d…）
  · 项目**未**在任何现行文件中冻结 "P14 的正式版本号"
  ⇒ 按 §15 规定登记 `VERSION_PENDING_RELEASE_GATE`，**不自行发明版本号**
```

---

# 2. Git baseline

```text
HEAD = c420403d5469241e8b03855428ebce435d539c9e · branch = main · tags = 9（annotated）
remote = 0 · staged = 0 · dirty = 209（prestate）/ 214（release-prep 结束时）
分类：A（P14 RC owned）30 · B（P14 evidence/frozen）67 · C（历史 dirty）110 ·
      D（BATCH-D）2 · E（未分类）0
详见 P14_RELEASE_PREPARATION_GIT_BASELINE.md
```

---

# 3. Artifact inventory

```text
完整清点见 P14_RELEASE_ARTIFACT_INVENTORY.md（7 类 · 无缺件）
关键 hash（sha256[:32]）
  PLATFORM_DECISION_LOG.md                     = c283f954b29b5574c8654c5e0e863ac3
  P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md = 00c3355cbcfea52bfc22b4a4d2e3c029
  P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md  = f09f786664990f2f24c2e9d45dc96327
  P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md = c66c28091cc13824bc7dcc3af997fc85
  P14_OVERALL_FINAL_ACCEPTANCE_REPORT.md       = b6868a55904eee3e0c53c4bfd48852e2
  P14_OVERALL_OI_CLOSURE_MATRIX.md             = b7f8b1875c16b91c2be1db15fd55f654
  tests/integration/test_runtime_db_wave1.py   = 51a453f5c1858873525753b556438c4d（冻结 · D-02）
  tests/integration/test_wave2_audit_invariant.py = c7ae8718bed22cc14303aa578ac14e19
  infrastructure/database/persistence.py       = 69d2c14064d19d5355cf867665476c34（冻结 · D-01）
  pyproject.toml                               = 3d8b69d6ef713706efa7c2be904d4f89
  requirements.txt                             = 22ceb66d257917f1f6e6d2f9e98b9886
  migrations_alembic/env.py                    = 577f0d0e018b5859696e61b4f405ab2b
```

---

# 4. Test matrix

```text
完整矩阵见 P14_RELEASE_CANDIDATE_REGRESSION_MATRIX.md
执行 = 26 个显式文件（无目录级 pytest）· 结果 = **282 passed · 1 failed**
唯一失败 = D-02（CLOSED · Human OPTION B）· Forbidden tests executed = 0
干净 venv 依赖复现 = PASS（20 tests + argon2id 校验）
```

---

# 5. Security fingerprint（只读实测 · 2026-09-28）

```text
uap_runtime = 51 row grants · uap_bootstrap = 6 · uap_app = 5 · uap_seed = 0 · uap_migrator = 245
pg_default_acl = 0 · user-defined memberships = 0 · ownership residual = 0
schema CREATE（非 uap 角色）= false · USAGE = true（未变）
C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff（未变）· tg_acl_subject_types_protect（enabled=O）
P13 seed = registry 3 / permissions 12 / role_permissions 12（未变）
pg_class（public, r/p/i/I）= 156 · pg_proc（public）= 22 · pg_trigger = 272（未变）
roles = 6（属性未变）· alembic_version = 0017_p13_seed · 0018+ = 0
unexpected privilege = 0 · uap_runtime / uap_bootstrap 无超出 frozen grant matrix 的新权限
⇒ Security Evidence Freeze = **INTACT**
```

---

# 6. DB evidence

```text
Formal DB `uap`：prestate == poststate = **True**（本轮/本阶段仅只读）
  Schema / Migration / Role / Grant / Revoke / Unexpected mutation = 0
Test DB `uap_b1_test`：边界锚点全未变（见 §5）
  EXPECTED TEST DATA = audit_logs 1169 行（append-only · 不可删除 · 不得强制归零 · D-02 裁决口径）
  users / identities / credentials / devices / sessions / tenants / spaces /
  memberships / tenant_memberships = 0 · roles = 1（platform_admin）· platform_state = 1
```

---

# 7. Release-prep 文档（本轮新增 · 5 份）

```text
P14_RELEASE_PREPARATION_GIT_BASELINE.md
P14_RELEASE_SCOPE_LOCK.md
P14_RELEASE_ARTIFACT_INVENTORY.md
P14_RELEASE_CANDIDATE_REGRESSION_MATRIX.md
P14_RELEASE_CANDIDATE_MANIFEST.md（本文件）
```

---

# 8. Consistency scan（§14 · 只读全局搜索）

```text
扫描词 = P14 / P14_RUNTIME_SLICE / IMPLEMENTED / VERIFIED / ACCEPTED / RELEASED /
         D-01 / D-02 / ENV-1 / Appendix O|P|Q / uap_runtime / uap_bootstrap / 51 / 6 / 245 /
         argon2-cffi

禁止性语义冲突检测（全部 0 命中）
  "P14 = RELEASED" · "P14 = COMMITTED" · "P14 = TAGGED" · "P14 = PUSHED" ·
  "P15 = STARTED" · "D-02 = OPEN" · "ENV-1 = OPEN" · "D-01 = BLOCKING" ·
  "security grants changed"

分类结论
  · historical statement：旧批次报告中出现 "Release Gate" 等词（历史语境）⇒ 不改
  · current statement：P14 现行状态 = ACCEPTED + CANDIDATE（本文件与 OVERALL REPORT）⇒ 一致
  · release-prep metadata：本批 5 份文档 ⇒ 允许
  · actual inconsistency = **0**
  · false positive = 0
⇒ 未修改任何 frozen document
```

---

# 9. Scope exclusions（见 P14_RELEASE_SCOPE_LOCK.md）

```text
EXC-1 P15 · EXC-2 admin device-management · EXC-3 D-01 repair · EXC-4 FINDING-ENGINE-1 重构 ·
EXC-5 new authorization actions · EXC-6 new schema · EXC-7 new migration · EXC-8 new DB principal ·
EXC-9 new runtime grants · EXC-10 new RLS policy · EXC-11 new API capability ·
EXC-12 new bootstrap CLI · EXC-13 new multi-instance infrastructure
⇒ Release Candidate scope does not grant permission to modify any of the excluded items.
```

---

# 10. Known deferred findings（不阻断 Release Candidate）

```text
D-01              DEFERRED / NON-BLOCKING（Wave 1 persistence.py 冻结 · SafeReader 为 approved path）
FINDING-AUTHZ-1   DEFERRED（管理类操作 = SEPARATE HUMAN DECISION · 未扩词表）
FINDING-ENGINE-1  ACCEPTED COMPATIBILITY FINDING（P14 内不重构）
OI-G-4 / OI-G-9   BATCH-D maintenance（未修 · 非阻断）
D-02              CLOSED（Human OPTION B · Wave 1 artifact 冻结 · 不变量由 Wave 2 独立测试覆盖）
ENV-1             CLOSED（依赖清单 + 干净环境验证）
```

---

# 11. 边界声明

```text
· 本 Manifest 只声明 **Release Candidate Prepared**，不声明 RELEASED。
· 不给出"建议直接发布 / 建议 commit / 建议 tag"之类判断（本轮职责边界）。
· 下一步需另开 **P14 RELEASE GATE**（Human 授权）；在此之前：
    Release Gate = NOT EXECUTED · Commit = FORBIDDEN · Tag = FORBIDDEN · Push = FORBIDDEN · P15 = FORBIDDEN
```

**END OF P14 RELEASE CANDIDATE MANIFEST（2026-09-28 · RELEASE CANDIDATE PREPARED · version = VERSION_PENDING_RELEASE_GATE · HARD STOP ACTIVE）**
