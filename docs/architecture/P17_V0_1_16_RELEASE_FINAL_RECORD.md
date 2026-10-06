# P17 V0.1.16 RELEASE FINAL RECORD

> 说明：本文件遵循仓库既有 release-record 模式（P16 的
> `P16_V0_1_15_RELEASE_FINAL_RECORD.md` 同为发布后生成的工作区 artifact），
> **不在 release commit 内**，因此不会产生 “release follow-up commit”，也不会
> 改变已推送的 release tree。

```text
Version            = 0.1.16
Tag                = UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME
Base Commit        = 42a4f61c20fe119af77ab822e24c8028ce653e3d   （0.1.15 · P16）
Release Commit     = 9fe282b009aba3965236402971ab963694f7ce05
Release Tree       = de420083cbb3fa01b77e7d4d0cc7c317bebba06c
Tag Object         = 1327828f884f18dd537ea2898096261449009f51   （annotated tag）
Release Subject    = release: UAP v0.1.16 P17 identity tenant space runtime
Release Date       = 2026-10-01
```

## 1. Verification summary

```text
P17 Acceptance      = PASSED
Release Candidate   = PASS
Release Integrity   = PASS

P17 tests           = 97 / 0 failed（worktree candidate · fresh clone · remote clone 三处一致）
P16                 = 33/0（unit+architecture+security）+ 8/0（integration 6 + durability 2）
P15                 = 65 / 0
Architecture        = 57 / 0
Forbidden tests     = 0（tests/unit/test_generate_build_info.py 执行次数 = 0）
OI-G-4              = 0
Core → Domain       = 0
```

```text
Security            : cross-tenant bypass = 0 · cross-space bypass = 0 · agent inheritance = 0
                      resource fail-open = 0 · authorization bypass = 0 · secret leakage = 0
                      unexpected privilege = 0
Privilege           : uap_runtime = 56 · P17 delta = 0 · uap_app = 5 · uap_migrator = 245
                      roles = 6 · default ACL = 0 · public schema PUBLIC grants = 0
                      tenants/spaces = SELECT only
Schema              : UNCHANGED（new tables = 0）
Migration           : NONE（head = 0018_p16_agent_runtime · P17 未新增 migration）
Production Event    : EMPTY（production_allowlist().is_empty = True）· Handlers = 0
Formal DB (uap)     : UNCHANGED（public 表 0 · 无 seed / fixture / projection 数据）
Temporary DBs       : 全部 DROP（现存 uap / uap_b1_test / uap_test）
```

## 2. Four-way consistency（P16 标准的延续）

```text
committed release tree   = de420083cbb3fa01b77e7d4d0cc7c317bebba06c
annotated tag peeled     = 9fe282b009aba3965236402971ab963694f7ce05（tree 同上）
remote origin/main       = 9fe282b009aba3965236402971ab963694f7ce05
remote tag object        = 1327828f884f18dd537ea2898096261449009f51（= local TAG_OBJECT）
remote tag peeled commit = 9fe282b009aba3965236402971ab963694f7ce05
fresh clone（local tag）  = HEAD 9fe282b0 · tag exact-match · version 0.1.16 · 全套测试 PASS
post-push clone（origin）= HEAD 9fe282b0 · origin/main 9fe282b0 · 全套测试 PASS
```

## 3. Manifest reproducibility

```text
docs/architecture/P17_V0_1_16_RELEASE_MANIFEST.md
  32 个 payload 行（manifest 自身按 self-hash exclusion 规则排除）
  在 fresh clone 中重算 committed blob SHA-256 → mismatches = 0
  hash basis = committed Git blob bytes（F-RP-06）
```

## 4. Payload

```text
added    = 26（identity_runtime 8 · control_plane 2 · use_cases 1 · api route 1 ·
             tests 8 · docs 6（含 manifest））
modified = 4（apps/api/main.py · apps/api/error_mapping.py · services/use_cases/__init__.py ·
             docs/architecture/PLATFORM_DECISION_LOG.md（附录 W + X · append-only 146+/0-））
version  = 3（pyproject.toml · config/settings.py · docker-compose.yml · 0.1.15 → 0.1.16）
deleted  = 0
历史脏文件 = 显式排除并保留在工作区（tracked 25 + untracked ~102 · 未进入 commit）
```

## 5. Push

```text
git push origin main                       42a4f61 → 9fe282b   （无 force）
git push origin UAP-V0.1.16-P17-...        new tag（annotated）  （无 force）
```

**END OF P17 V0.1.16 RELEASE FINAL RECORD（UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME = RELEASED · commit 9fe282b0 · tree de420083 · tag object 1327828f · 2026-10-01）**
