# P15 BASELINE INTEGRITY REPAIR RECORD

日期：2026-09-28
轮次：**P15 RELEASE GATE** — Release Baseline Integrity Repair
性质：**仓库基线完整性修复**（非 P15 功能、非 schema 语义变更）

```text
P15 functional scope impact = NONE
new Alembic revision        = 0（0018+ = 0）
schema semantics change     = 0
security change             = 0
commit / tag / push         = 0
```

---

## 1. Finding F-RP-01

```text
ID             = F-RP-01
Classification = PRE-EXISTING REPOSITORY BASELINE INTEGRITY DEFECT
Scope          = P10.1 / P11 / P12 historical repository state
Origin         = PRE-P15
P15 causality  = NONE
```

### 1.1 Original state（committed tree @ `15feebad`）

```text
git ls-tree --name-only HEAD migrations_alembic/versions/
  0001_baseline.py … 0012_authz_enforcement.py
  0017_p13_seed.py
（缺 0013 / 0014 / 0015 / 0016）

0017_p13_seed.py                   down_revision = "0016_open_p10_1_trust_boundary"
0016_open_p10_1_trust_boundary.py  revision      = "0016_open_p10_1_trust_boundary"
                                   down_revision = "0015_p12_indexes"
```

### 1.2 Impact assessment（实测，非推断）

在 `git archive HEAD` 的隔离 checkout 中实测（不含任何 working-tree-only 文件）：

```text
$ python -m alembic -c alembic.ini heads
UserWarning: Revision 0016_open_p10_1_trust_boundary referenced from
  0016_open_p10_1_trust_boundary -> 0017_p13_seed (head) ... is not present
  → command FAILS

$ python -m alembic -c alembic.ini history
  → 同一 UserWarning + FAILS

$ python -m alembic -c alembic.ini upgrade head --sql
  → 同一 UserWarning + FAILS
```

```text
⇒ IMPACT = RELEASE BLOCKER
   committed repository 无法重建 Alembic graph，更无法 upgrade head。
   “本机 working tree 可用” 不能作为 Release Ready 的依据。
```

### 1.3 Forensic proof that 0013–0016 are HISTORICAL（非 P15 生成）

| Migration | SHA256 | size | mtime | revision / down_revision |
|---|---|---|---|---|
| `0013_p10_event_audit.py` | `da1bdffd4ddd2202f1132557701d3fe23e8aeee035527561cbb1b4cc5b7a3937` | 15169 | 2026-09-25 23:24 | `0013_p10_event_audit` ← `0012_authz_enforcement` |
| `0014_p11_triggers.py` | `3be9c8c092869c8d3ffb29bed7e755af5f4305861c420034c41e0f2836e0357f` | 7779 | 2026-09-26 12:13 | `0014_p11_triggers` ← `0013_p10_event_audit` |
| `0015_p12_indexes.py` | `94b0d22800c8971ef6968dfeb72a88c6ac11d467d17a2f741692598adaf98031` | 4434 | 2026-09-26 15:33 | `0015_p12_indexes` ← `0014_p11_triggers` |
| `0016_open_p10_1_trust_boundary.py` | `10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544` | 4477 | 2026-09-27 20:58 | `0016_open_p10_1_trust_boundary` ← `0015_p12_indexes` |

```text
证据
 1. mtime 全部早于 P15 implementation（2026-09-28）⇒ 非 P15 生成
 2. 0016 的 SHA256 = 10284d98… 与 P14 / handoff 冻结记录中的 0016 hash 完全一致
 3. revision 链连续：0012 → 0013 → 0014 → 0015 → 0016 → 0017（depends_on 均为 None）
 4. 50+ 份历史文档引用这些 revision（P10 / P11 / P12 / OPEN_P10_1 / PLATFORM_DECISION_LOG 等）
 5. uap_b1_test 现处于 0017_p13_seed，该状态只能由 0013→0016 实际执行得到
⇒ 判定：working-tree 版本即历史已验收 / 已使用版本，未作任何内容改写
```

---

## 2. Repair authorization 与 scope

```text
Authorized by = P15 RELEASE GATE §6 Option A（独立 Baseline Integrity Repair）
Meaning       = 使已存在的历史 migration files 进入 repository（committed tree）
禁止（已遵守）= rename / renumber / rewrite revision id / 改 down_revision 语义 /
                merge / squash / 新建 0018 / 修改 0017 绕过 0016 /
                删除这些 working-tree migration
```

### 2.1 Scope 说明（含 1 项显式扩展，供 Human 复核）

§6 的最小范围 = `0013–0016`。实测中发现**第二处同族基线缺陷 F-RP-03**（见 §4）：
committed 的 `migrations_alembic/env.py` 仍是 **P0 fix 之前**的版本，`alembic.ini` 仍携带可执行 DSN。
若不同时纳入，则 “fresh clone 能否 upgrade head” 仍会失败（迁移不会持久化）。

因此本轮将下列文件一并纳入 **BASELINE INTEGRITY REPAIR**（全部为**已验收的工作树状态**，未新写内容）：

```text
migrations_alembic/versions/0013_p10_event_audit.py
migrations_alembic/versions/0014_p11_triggers.py
migrations_alembic/versions/0015_p12_indexes.py
migrations_alembic/versions/0016_open_p10_1_trust_boundary.py
migrations_alembic/env.py              （migration identity + P0 fix）
alembic.ini                            （移除可执行 DSN · 与 env.py 配对）
migrations_alembic/README.md           （同一变更的子系统文档）
.env.example                           （记录 UAP_MIGRATION_DATABASE_URL 键）
README.md                              （记录双 DSN 身份）

repair file count = 9
未修改任何 migration 的 revision / down_revision / upgrade / downgrade 语义
```

---

## 3. Files repaired — pre / post SHA256

| Path | Status | Pre-image (HEAD blob) | Post-image (worktree) |
|---|---|---|---|
| `migrations_alembic/versions/0013_p10_event_audit.py` | untracked → include | ABSENT（never committed） | `da1bdffd4ddd2202f1132557701d3fe23e8aeee035527561cbb1b4cc5b7a3937` |
| `migrations_alembic/versions/0014_p11_triggers.py` | untracked → include | ABSENT | `3be9c8c092869c8d3ffb29bed7e755af5f4305861c420034c41e0f2836e0357f` |
| `migrations_alembic/versions/0015_p12_indexes.py` | untracked → include | ABSENT | `94b0d22800c8971ef6968dfeb72a88c6ac11d467d17a2f741692598adaf98031` |
| `migrations_alembic/versions/0016_open_p10_1_trust_boundary.py` | untracked → include | ABSENT | `10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544` |
| `migrations_alembic/env.py` | M | `44ae7966c68b6e3cfe331f428bdedd7aa6d358881ef1addfc4562fe40452ba61` | `577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a` |
| `alembic.ini` | M | `3a6f5ad9105ad0270ad40ed1f50d368730804cc14726982d2bb515757b88dbf8` | `2eccf6473d859d0f3eb14aac60b75fe8fa23bcf902b4b341a92a0cfe1b831f5f` |
| `migrations_alembic/README.md` | M | `b43e785dafc071122bb412189187abb07aeeefff5ea55e8991cefeb72a8994d4` | `3c44245a805506e61dea24e65df7837f0a785c9ca423339d08464cdcdada1f2d` |
| `.env.example` | M | `861d23d85aeb9b98843661273a790c13bc5cd6e25f4abe913a4e60749d79bead` | `b95436542da3273709a746685e7fda8800a602aee4a323e737fdc22568718564` |
| `README.md` | M | `6c374b22f15de37756b589e0d4137774c075781aff02a69b6fb6c42eb865d72b` | `ef81a770286374aca2d0987cdf93cd3dbe9334d5e4278a44c2ffe9c69c8b5707` |

```text
pre-image 口径 = git cat-file blob HEAD:<path> 的原始字节 SHA-256
                 （未跟踪文件 ⇒ ABSENT，不是推测值）
```

---

## 4. Finding F-RP-03（同族基线缺陷 · 本轮一并修复）

```text
ID             = F-RP-03
Classification = PRE-EXISTING REPOSITORY BASELINE INTEGRITY DEFECT
事实           = committed migrations_alembic/env.py 为 P0 fix 之前版本
                 （pre-image sha256 = 44ae7966…；无 connection.rollback()，
                  无 UAP_MIGRATION_DATABASE_URL fail-closed 身份解析）
                 committed alembic.ini 仍携带可执行 DSN（可充当 fallback）
Release impact = 若只修 0013–0016，fresh clone 的 upgrade head 仍无法持久化
Remediation    = BASELINE INTEGRITY REPAIR（纳入 env.py / alembic.ini / README）
P15 causality  = NONE
```

残留（**未修 · 需独立裁决**）：

```text
F-RP-02（RESIDUAL）
  同一 BATCH-B/C 已验收变更集中，仍有 3 个文件未纳入本轮 payload：
    tests/conftest.py                  （dual-DSN 测试夹具）
    core/event/interfaces.py            （EventBus != Outbox · UUIDv7 · nullable tenant_id）
    infrastructure/database/__init__.py （导出 RuntimeDatabase / Repository 等）
  理由 = 不满足任何 Release Gate 判据（不影响 migration chain 与版本一致性），
         且 core/event/interfaces.py 属行为语义变更 ⇒ 超出 Release Integrity scope
  处置 = REGISTER / DO NOT FIX（需独立裁决）
```

---

## 5. Alembic graph verification

```text
BEFORE（committed tree）
  alembic heads          = FAIL（Revision 0016_open_p10_1_trust_boundary … is not present）
  alembic history        = FAIL
  alembic upgrade --sql  = FAIL

AFTER（candidate tree = HEAD + baseline repair + P15 payload）
  alembic heads          = 0017_p13_seed (head)          ← single head
  alembic history        = 0017 → 0016 → 0015 → 0014 → 0013 → 0012 → 0011 …
  alembic current        = 0017_p13_seed (head)
```

---

## 6. Fresh-clone / isolated-DB validation

```text
方法
  isolated checkout = git archive HEAD（committed tree）
                    + overlay：baseline repair + P15 payload（= candidate commit 内容）
  isolated database = uap_p15_release_verify（新建 · owner uap_migrator）
                      ≠ 正式库 uap ≠ 测试库 uap_b1_test
  migration identity = UAP_MIGRATION_DATABASE_URL（uap_migrator）
```

```text
observed results
  upgrade head        rc = 0   → alembic_version = 0017_p13_seed
  downgrade base      rc = 0   → alembic_version = （空）
  upgrade head again  rc = 0   → alembic_version = 0017_p13_seed
  alembic current     rc = 0   → "0017_p13_seed (head)"

isolated DB object state after upgrade（两轮一致）
  pg_class(public) = 156 · pg_proc(public) = 22 · pg_trigger = 272
  events = 0 · acl_subject_types = 3 · permissions = 12 · role_permissions = 12
  ⇒ 与 P13/P14 冻结基线 156/22/272 与 3/12/12 完全一致

cleanup
  uap_p15_release_verify 已 DROP；数据库列表 = postgres / template0 / template1 /
  uap / uap_b1_test / uap_test（无残留验证库）
```

---

## 7. DB / Security validation after repair

```text
FORMAL PRODUCTION-LIKE DB（uap）      = 0 对象 · prestate == poststate
TEST DB（uap_b1_test · 冻结锚点）     = 未受影响
  alembic_version      = 0017_p13_seed（未变）
  0018+                = 0
  roles                = 6
  privilege fingerprint= 51 / 6 / 5 / 0 / 245（未变）
  default ACL          = 0（未变）
  C2 md5               = 185e95be8bc4304edbcd3f4d5cda1eff（未变）
  CC-7                 = INTACT（tg_acl_subject_types_protect · tgenabled = O）
  P13 seed             = acl_subject_types 3 · permissions 12 · role_permissions 12（未变）
  pg_class/proc/trigger= 156 / 22 / 272（未变）
  user memberships     = 0 · ownership residual = 0

Core → Domain = 0（architecture 测试通过）
```

---

## 8. Final classification

```text
F-RP-01  Status = CLOSED
         Classification = PRE-EXISTING REPOSITORY BASELINE INTEGRITY DEFECT
         Remediation = BASELINE INTEGRITY REPAIR
         P15 functional scope impact = NONE
         Release blocking = RESOLVED

F-RP-03  Status = CLOSED（同族缺陷 · 一并修复）
F-RP-02  Status = REGISTERED / DO NOT FIX（残留 3 文件 · 需独立裁决）
```

```text
revision semantics unchanged · historical source already existing ·
required to restore committed Alembic graph
```

