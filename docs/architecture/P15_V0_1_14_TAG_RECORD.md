# P15 V0.1.14 TAG RECORD

## 0. 性质

```text
类型 = post-tag release record（tag object SHA 只能在创建后记录，故与 pre-tag gate report 分离）
状态 = uncommitted working-tree evidence（不进入已存在的 0.1.14 commit）
日期 = 2026-09-28
```

---

## 1. Commit

```text
Commit  = 1bc60834415cb4f518cd695c93cd79bec986228e
Parent  = 5244b5916e51eebc958bb3f844dbc579d66014f3   （0.1.13 candidate · immutable）
Tree    = c368e76caba94b0f683ce0fc84800e8f5365040a   （= 已验证候选树）
Subject = release(p15): repair canonical release manifest hashes
Author  = UAP Platform <platform@uap.local>
Diff    = 6 files changed, 352 insertions(+), 12 deletions(-)（4 modified · 2 added · 0 deleted）
```

## 2. Tag

```text
Tag        = UAP-V0.1.14-P15-EVENT-CONSUMER
Type       = annotated（object type = tag）
Tag object = a0eb1bfcdbe1758e3a642aec18a07b245f4007f2
Target     = 1bc60834415cb4f518cd695c93cd79bec986228e
Tagger     = UAP Platform <platform@uap.local>

Message    = UAP v0.1.14 - P15 Event Consumer Release Correction
             Canonical release manifest hash-basis repair.
             Committed-artifact / clean-clone hashing verified.
```

```text
未指向：a238e85（0.1.12）· dc44c99（0.1.11）· 15feebad（0.1.14 之前的历史）
```

## 3. 发布前验证（clean clone = git archive HEAD）

```text
Manifest hashes = 14/14 MATCH（12 lineage + 2 additions；基准 = committed Git blob bytes）
                  其中 0.1.13 lineage 12 条 = 12/12 MATCH（F-RP-06 已关闭）
Clean clone bytes = committed blob bytes（同 commit 下逐文件一致）

P15 allowlist（4）      = 65 passed / 0 failed / 0 collection error
Wave 1 allowlist（17）  = 210 passed / 1 failed / 0 collection error（唯一失败 = D-02 historical）
Wave 2 allowlist（9）   = 72 passed / 0 failed / 0 collection error
Foundation guards       = alignment 9 + boundary 11 = 20 passed
Forbidden tests         = 0 · CF-C-4 = PASS

Alembic = single head 0017_p13_seed · 0012→0013→0014→0015→0016→0017
          upgrade → downgrade → re-upgrade = PASS（隔离 verification DB · 已删除）
          seed = acl_subject_types 3 · permissions 12 · role_permissions 12 · users 0 · audit_logs 0
          objects = pg_class 156 · pg_proc 22 · pg_trigger 272 · 0018+ = 0

Security = roles 6 · runtime grants 51 · uap_app 5 · default ACL 0 · uap_migrator 245
           fingerprint = 51/6/5/0/245 · C2 = 185e95be8bc4304edbcd3f4d5cda1eff（未变）
           CC-7 触发器 tg_acl_subject_types_protect tgenabled = O（INTACT）
Core → Domain = 0
Event Contract = UUIDv7 canonical · tenant_id str | None · NULL = platform-scoped ≠ 授权旁路
Production Allowlist = EMPTY · Production Handlers = 0

Version Sources = pyproject.toml / config/settings.py / docker-compose.yml = 0.1.14
Formal DB `uap` = 0 表（prestate == poststate）
Test DB `uap_b1_test` = 0017_p13_seed · events 0（net zero）· users 0 · audit_logs 3599（append-only）
```

## 4. Release 谱系（不可变）

```text
0.1.11 = immutable failed REMOTE candidate（tag bc312cd → dc44c99 · RELEASE-BLOCKED）
0.1.12 = immutable local corrective candidate（tag dfcc694 → a238e85）
0.1.13 = immutable local foundation candidate（无 tag · 5244b59 · Release Gate BLOCKED）
0.1.14 = tagged local release candidate（tag a0eb1bf → 1bc6083 · NOT PUSHED）
```

```text
PUSH = FORBIDDEN
remote/main = dc44c9939d7708b68e5b461a7ccb6684588d1106（未推送）
下一阶段 = P15 V0.1.14 REMOTE PUSH GATE
```

**END OF P15 V0.1.14 TAG RECORD**
