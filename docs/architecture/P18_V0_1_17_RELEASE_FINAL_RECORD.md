# P18 V0.1.17 RELEASE FINAL RECORD

> 发布后生成的工作区 artifact（沿用 P16/P17 既有 pattern），**不在 release commit 内**，
> 因此不产生 release follow-up commit，也不改变已推送的 release tree。

```text
Version            = 0.1.17
Tag                = UAP-V0.1.17-P18-CONTROL-PLANE（annotated）
Base Commit        = 9fe282b009aba3965236402971ab963694f7ce05   （0.1.16 · P17）
Base Tree          = de420083cbb3fa01b77e7d4d0cc7c317bebba06c
Release Commit     = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
Release Tree       = d0af7d5ca181df5872c5af67cf73ae01f2d87d4c
Tag Object         = 753610cdbd67eb7917a4041f70694e8ffba82cac
Release Subject    = release: UAP v0.1.17 P18 control plane
Release Date       = 2026-10-01
Payload            = 36 文件（35 P18 payload + release manifest）
```

## 1. Verification summary

```text
P18 ACCEPTANCE      = PASSED（独立验收 · 见 P18_ACCEPTANCE_EVIDENCE.md）
Release Candidate   = PASS（精确 staging · 候选树全量测试通过）
Release Integrity   = PASS

P18 = 33/0 · P17 = 97/0 · P15 = 65/0 · P16 = 24/0（单元+安全）+ 8/0（集成）
architecture guards = 63/0 · Core → Domain = 0 · forbidden tests = 0 · OI-G-4 = 0
worktree / tag-clone / origin-clone 三处一致：227 + 63 全绿（0 failed）
```

```text
Security : cross-tenant = DENY · cross-space = DENY · owner inheritance = 0 · visibility bypass = 0 ·
           resource fail-open = 0 · authorization bypass = 0 · secret leakage = 0 · unexpected privilege = 0
Privilege: uap_control = 23 grants（冻结 ceiling · 自校验全空）· uap_runtime = 56（未变）·
           uap_migrator = 245 · uap_app = 7（月分区数依赖）· default ACL = 0
Role     : 7 个 uap* 主体；uap_control = LOGIN / NOSUPERUSER / NOCREATEDB / NOCREATEROLE /
           NOREPLICATION / NOBYPASSRLS / NOINHERIT
Schema   : UNCHANGED　Migration = NONE　head = 0018_p16_agent_runtime　permissions = 12
Event    : Allowlist = EMPTY · Handlers = 0
Formal DB: uap public 表 0 · prestate == poststate（未触碰）
Temporary DBs: 全部 DROP（现存 uap / uap_b1_test / uap_test）
```

## 2. Four-way consistency（P16/P17 标准延续）

```text
committed release tree   = d0af7d5ca181df5872c5af67cf73ae01f2d87d4c
annotated tag peeled     = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（tree 同上）
remote origin/main       = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
remote tag object        = 753610cdbd67eb7917a4041f70694e8ffba82cac（= local TAG_OBJECT）
remote tag peeled commit = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
fresh clone（local tag）  = HEAD 08a0485b · tag exact-match · version 0.1.17 · 227+63 全绿
post-push clone（origin）= HEAD 08a0485b · origin/main 08a0485b · version 0.1.17 · 227 全绿
manifest reproducibility = 35 行 payload 哈希在 clone 中重算 → mismatches = 0
```

## 3. Push

```text
git push origin main                        9fe282b → 08a0485   （无 force）
git push origin UAP-V0.1.17-P18-CONTROL-PLANE  new annotated tag（无 force）
```

**END OF P18 V0.1.17 RELEASE FINAL RECORD（UAP-V0.1.17-P18-CONTROL-PLANE = RELEASED · commit 08a0485b · tree d0af7d5c · tag object 753610cd · 2026-10-01）**
