# P15 V0.1.14 REMOTE PUSH RECORD

## 0. 结论

```text
P15 V0.1.14 REMOTE PUSH    = SUCCESS
P15 V0.1.14 REMOTE RELEASE = COMPLETE
0.1.14                     = CURRENT REMOTE RELEASE
```

```text
类型 = post-push evidence（本轮新增 · 不属于已不可变的 1bc6083 commit）
日期 = 2026-09-28
```

---

## 1. Remote 事实

```text
Remote URL            = https://github.com/jayfeng6848-ctrl/UAP.git
Remote pre-push main  = dc44c9939d7708b68e5b461a7ccb6684588d1106   （0.1.11）
Remote post-push main = 1bc60834415cb4f518cd695c93cd79bec986228e   （0.1.14）
Push 方式             = fast-forward（dc44c99..1bc6083）
Force push            = 0
Branch                = main · ahead 0 / behind 0
```

```text
Local commit  = 1bc60834415cb4f518cd695c93cd79bec986228e
Remote commit = 1bc60834415cb4f518cd695c93cd79bec986228e   （相等）
Local tree    = c368e76caba94b0f683ce0fc84800e8f5365040a
```

## 2. Tag 事实

```text
Tag                 = UAP-V0.1.14-P15-EVENT-CONSUMER
类型                = annotated（tag object type = tag）
Local tag object     = a0eb1bfcdbe1758e3a642aec18a07b245f4007f2
Remote tag object    = a0eb1bfcdbe1758e3a642aec18a07b245f4007f2（一致）
Remote peeled target = 1bc60834415cb4f518cd695c93cd79bec986228e
Local tag count      = 13（实测 `git tag --list`）

未推送：0.1.12 tag（absent）· 0.1.13 tag（不创建、不存在）
未使用：git push --tags / --follow-tags
```

## 3. Fresh Clone（来自 GitHub remote）

```text
HEAD                    = 1bc60834415cb4f518cd695c93cd79bec986228e
Tag type                = tag（annotated）
Tag target              = 1bc60834415cb4f518cd695c93cd79bec986228e
Version sources         = pyproject.toml / config/settings.py / docker-compose.yml = 0.1.14
Manifest                = 14/14 declared hashes MATCH（clone bytes；基准 = committed blob）
Alembic heads           = 0017_p13_seed（单一）
Alembic history         = 0012 → 0013 → 0014 → 0015 → 0016 → 0017
Migration cycle         = upgrade head → downgrade base → upgrade head = PASS
seed / objects          = 3 / 12 / 12 / 0 / 0 · pg_class 156 · pg_proc 22 · pg_trigger 272
```

```text
P15 smoke（4 文件）                = 65 passed / 0 failed / 0 collection error
Wave 1（17 文件）                  = 210 passed / 1 failed / 0 collection error
                                     （唯一失败 = D-02 historical：test_runtime_db_wave1::test_approved_reads）
Wave 2（9 文件）                   = 72 passed / 0 failed / 0 collection error
Foundation guards                  = alignment 9 + boundary 11 = 20 passed
Forbidden tests                    = 0 · CF-C-4 = PASS
Dependency closure（30 roots）      = closure 120 · required untracked = 0 ·
                                     required worktree-only = 0（closure 内 non-clean = 0）
Production boundary                = allowlist EMPTY · handlers 0
Core → Domain                      = 0
Event Contract                     = UUIDv7 canonical · tenant_id str | None ·
                                     NULL = platform-scoped ≠ 授权旁路
```

## 4. 安全与数据库

```text
Security anchors = roles 6 · runtime grants 51 · uap_app 5 · default ACL 0 · uap_migrator 245
                   fingerprint 51/6/5/0/245
C2               = 185e95be8bc4304edbcd3f4d5cda1eff（未变）
CC-7             = INTACT（tg_acl_subject_types_protect · tgenabled = O）
pg_class 156 · pg_proc 22 · pg_trigger 272

Formal DB `uap`        = 0 表（prestate == poststate · push 未产生 DB mutation）
Test DB `uap_b1_test`  = 0017_p13_seed · events 0（net zero）· users 0 ·
                         audit_logs 3842（test-only append-only · 未清空）
verification DB        = 完成后已删除（仅保留 uap / uap_b1_test / uap_test）
```

## 5. Release 谱系（历史事实 · 不得隐藏）

```text
0.1.11 = historical FAILED remote candidate
         commit dc44c99 · tag bc312cd · status PUBLISHED BUT RELEASE-BLOCKED
         失败原因 = clean-clone 测试无法完整收集（F-RP-04）

0.1.12 = historical corrective ancestor
         commit a238e85 · local tag dfcc694（未发布到远端）
         修复 = 补交 runtime_testkit / boundary guard + 版本 0.1.12

0.1.13 = historical foundation ancestor
         commit 5244b59 · NO TAG
         Release Gate = BLOCKED（F-RP-06：manifest hash basis 错误）
         内容 = 事件契约对齐 + Carrier faces 恢复 + Wave1 基线闭合

0.1.14 = CURRENT REMOTE RELEASE
         commit 1bc6083 · tag a0eb1bf · fast-forward 发布成功
         修复 = manifest hash basis（committed blob）+ 方法冻结 + F-RP-06 CLOSED
```

## 6. 推送后远端 tag 完整性

```text
UAP-V0.1.10-P14-RUNTIME-SLICE   = b9d3560 → 15feebad（未变）
UAP-V0.1.11-P15-EVENT-CONSUMER  = bc312cd → dc44c99（未变）
UAP-V0.1.12-P15-EVENT-CONSUMER  = ABSENT（按策略不发布）
UAP-V0.1.13-P15-EVENT-CONSUMER  = ABSENT（无 tag）
UAP-V0.1.14-P15-EVENT-CONSUMER  = a0eb1bf → 1bc6083（新增）
```

## 7. 工作区与后续

```text
Working tree = historical dirty / F-RP-02 remaining / BATCH-D / future docs 全部保留
real staged  = 0
F-RP-02      = PARTIALLY RESOLVED（remaining: tests/conftest.py ·
                                   infrastructure/database/__init__.py）— 未因推送关闭
F-RP-06      = CLOSED（canonical hash basis = committed Git blob bytes）
P16+         = FORBIDDEN
GitHub Release UI = 未创建（本轮不需要）
```

**END OF P15 V0.1.14 REMOTE PUSH RECORD（REMOTE PUSH = SUCCESS · REMOTE RELEASE = COMPLETE）**
