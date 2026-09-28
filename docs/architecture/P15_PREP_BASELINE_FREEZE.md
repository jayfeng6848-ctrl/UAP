# UAP — P15 PREP BASELINE FREEZE

> 轮次 = STEP 3 · P15 PREP（分析基线锚点 · **不是 Git release tag**）

## 1. 参考锚点（hash · 实测）

```text
P14 commit              = 15feebadeecd6f7d90e81569c3e869bc20cb18c5
P14 annotated tag       = UAP-V0.1.10-P14-RUNTIME-SLICE
                          tag object = b9d356065bad6c5a42796790c832998ffedb2175
                          peeled     = 15feebadeecd6f7d90e81569c3e869bc20cb18c5
origin/main             = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（remote verified）

PLATFORM_DECISION_LOG.md                     c283f954b29b5574c8654c5e0e863ac3（附录 A–Q）
P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md 00c3355cbcfea52bfc22b4a4d2e3c029
P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md  f09f786664990f2f24c2e9d45dc96327
P14_OVERALL_FINAL_ACCEPTANCE_REPORT.md       b6868a55904eee3e0c53c4bfd48852e2
P14_REMOTE_PUSH_RECORD.md                    见 docs/architecture（post-release evidence）
infrastructure/database/persistence.py       69d2c14064d19d5355cf867665476c34（D-01 冻结）
tests/integration/test_runtime_db_wave1.py   51a453f5c1858873525753b556438c4d（D-02 冻结）
pyproject.toml / requirements.txt            3d8b69d6… / 22ceb66d…（argon2-cffi==25.1.0）
migrations_alembic/env.py                    577f0d0e018b5859696e61b4f405ab2b
```

## 2. 数据库锚点

```text
current Alembic head = 0017_p13_seed（== current）· 0018+ = 0
security fingerprint = uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 · uap_migrator 245
                       pg_default_acl 0 · memberships 0 · ownership residual 0
C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff · P13 seed = 3/12/12
formal uap = prestate == poststate（0 表）
test DB EXPECTED TEST DATA = audit_logs（append-only · 不得强制归零）
```

## 3. 声明

```text
P15 的所有分析、决策、准备文档均以上述锚点为基线。
本文件**不是** Git release tag，不构成任何发布或实现授权。
若任一锚点发生变化 ⇒ 必须重新建立基线并说明原因（不得静默接受漂移）。
```

**END OF P15 PREP BASELINE FREEZE（2026-09-28 · P14_RELEASED 锚点冻结 · HARD STOP ACTIVE）**
