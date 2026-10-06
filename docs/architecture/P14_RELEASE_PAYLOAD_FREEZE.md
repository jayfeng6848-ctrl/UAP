# UAP — P14 RELEASE PAYLOAD FREEZE

> ```text
> 轮次 = P14 RELEASE GATE（§11 · staging 前冻结 · 2026-09-28）
> Version Identity = IDENTIFIED（0.1.10 · tag UAP-V0.1.10-P14-RUNTIME-SLICE）
> Payload = A(30) + B(67) = **97 path entries** → 展开 **118 files**
> Aggregate digest（对 "hash:path" 排序行取 sha256）= af7f2aad5dd6c7e2f807121f08b9a31bdd198e4cc41c89358d30f52816918542
> ```

---

# 1. Payload 组成

```text
A 类（P14 RC owned · 30 条）= implementation / tests / dependency manifests
  services/mapping/ · services/reads.py · services/identity/ · services/device/ ·
  services/session/ · services/context/ · services/audit/ · services/use_cases/ ·
  infrastructure/runtime/ · infrastructure/database/{persistence,principal,runtime}.py ·
  apps/api/main.py · apps/api/{dependencies,error_mapping}.py ·
  apps/api/routes/{identity,devices,sessions}.py ·
  tests/unit/test_wave2_{vocabulary_mapping,credentials,error_mapping}.py ·
  tests/integration/wave2_testkit.py · tests/integration/test_wave2_{identity,device,session,
  authorization,api}_security.py · tests/integration/test_wave2_audit_invariant.py ·
  pyproject.toml · requirements.txt

B 类（P14 accepted evidence / frozen canonical · 67 条）
  tests/integration/test_runtime_db_wave1.py（D-02 冻结）·
  tests/integration/test_runtime_security_regression_wave1.py ·
  tests/unit/test_runtime_{error_taxonomy,retry_boundary,lifecycle_boundary}.py ·
  docs/architecture/PLATFORM_DECISION_LOG.md（附录 A–Q）·
  docs/architecture/P14_*.md（**不含** 本轮 release-prep/gate 8 份 post-classification 文档）

⇒ 97 条 path entry 展开为 118 个文件（其中 8 条为目录 entry：
   infrastructure/runtime/ (4) · services/{mapping(3),identity(5),device(4),session(4),
   context(5),audit(2),use_cases(2)} = 29 files）
```

---

# 2. 每个 payload 文件的 sha256

```text
完整「sha256 : path」清单（97 条 · 文件条目为文件 hash，目录条目为其内部文件的聚合 digest）
  由冻结脚本生成并留档：work/p14_payload_freeze.txt · work/p14_release_payload.json
聚合承诺（Aggregate digest）= af7f2aad5dd6c7e2f807121f08b9a31bdd198e4cc41c89358d30f52816918542

验证方式：staging 前后重算上述 97 条的 hash 清单并比较该聚合值；
任何变化 ⇒ 立即 STOP（不得偷偷接受变化）。
实测：staging 前后聚合 digest 未变（staging 未修改任何 payload 文件）。
```

---

# 3. 排除项（不得进入 payload）

```text
C 类 historical dirty = 110（P14 之前既有 dirty）⇒ 未 stage · 未清理 · 未重排
D 类 BATCH-D = 2（tests/security/test_authorization_security.py · tests/unit/test_generate_build_info.py）
                ⇒ 未 stage（commit 后实测仍为 dirty）
E 类 unknown = 0
post-classification release 文档 = 8（P14_RELEASE_* 5 份 release-prep + 3 份 gate）
                ⇒ 按 Human 冻结的 97 口径排除；commit 后仍为 untracked
```

---

# 4. Staging 结果（实测）

```text
payload path entries staged = 97（逐条 git add -- <path>，无 git add -A / . / commit -am）
staged files（展开后）      = 118
staged ∩ C = 0 · staged ∩ D = 0
git diff --cached --check   = exit 0（无空白损坏）
```

**END OF P14 RELEASE PAYLOAD FREEZE（2026-09-28 · 97 entries / 118 files · digest af7f2aad… · HARD STOP ACTIVE）**
