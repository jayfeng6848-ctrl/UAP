# P15 COMMIT + TAG — POST-RELEASE RECORD

日期：2026-09-28
轮次：P15 COMMIT + TAG GATE（post-release metadata）

> **本文件不属于 P15 Release Payload。**
> 它记录 commit / tag 创建之后才可知的信息，因此按 P15 COMMIT + TAG GATE §40
> 以独立 post-release record 形式留存；写于 commit 之后，故**不得**回写进
> 已提交的 Release Payload（不会修改 commit `dc44c99`）。

---

## 1. Release Commit

```text
Commit SHA   = dc44c9939d7708b68e5b461a7ccb6684588d1106
Short SHA    = dc44c99
Parent       = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（UAP-V0.1.10-P14-RUNTIME-SLICE）
Tree         = 5945886aa4e8d728624ebe0ee9d72a9116c96288
Subject      = release(p15): accept event consumer slice
Author       = UAP Platform <platform@uap.local> · 2026-09-28 21:33:01 +0800
Committer    = UAP Platform <platform@uap.local> · 2026-09-28 21:33:01 +0800
```

```text
Files changed = 64
Insertions    = 9021
Deletions     = 46
Added         = 54 · Modified = 10 · Deleted = 0
```

## 2. Annotated Tag

```text
Tag name        = UAP-V0.1.11-P15-EVENT-CONSUMER
Tag object SHA  = bc312cd95ef65c5d4fa9a302a0832915107e5fac
Tag type        = annotated（git cat-file -t ⇒ tag）
Tag target      = dc44c9939d7708b68e5b461a7ccb6684588d1106（= P15 commit，非 P14）
Tagger          = UAP Platform <platform@uap.local> · 2026-09-28 21:33:52 +0800
```

```text
Tag message
  UAP v0.1.11 — P15 Event Consumer Slice

  P15 implementation and acceptance complete.
  P15 release candidate accepted.

  Commit: dc44c9939d7708b68e5b461a7ccb6684588d1106
  Version: 0.1.11
```

```text
签名 = 未使用 GPG（本项目既有 tag 同样未签名）；annotated tag object 完整存在
tag 不可变性 = 未删除 · 未重建 · 未移动 · 未 force-update
```

## 3. Post-Commit Integrity

```text
HEAD^              = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（= P14 release commit）
committed payload  = approved P15 candidate payload（exact）
excluded 未进入 commit：tests/conftest.py · core/event/interfaces.py ·
                        infrastructure/database/__init__.py ·
                        tests/unit/test_generate_build_info.py（= absent）
version in commit  = pyproject.toml 0.1.11 · config/settings.py 0.1.11 ·
                     docker-compose.yml 0.1.11
```

```text
committed tree 的 Alembic（git archive dc44c99 隔离 checkout）
  revisions      = 0001 … 0017（含 0013 / 0014 / 0015 / 0016）
  alembic heads  = 0017_p13_seed (head)          ← single head
  alembic history= 0016 → 0015 → 0014 → 0013 → 0012 …

isolated verification DB = uap_p15_commit_verify（已 DROP · 无残留）
  upgrade head        rc = 0 → alembic_version = 0017_p13_seed
  downgrade base      rc = 0 → alembic_version = 空
  upgrade head（再次） rc = 0 → alembic_version = 0017_p13_seed
  alembic current     rc = 0 → 0017_p13_seed (head)
  对象 = pg_class 156 · pg_proc 22 · pg_trigger 272 ·
         acl_subject_types 3 · permissions 12 · role_permissions 12
```

## 4. Git Final State

```text
HEAD            = dc44c9939d7708b68e5b461a7ccb6684588d1106
origin/main     = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（unchanged · 未 push）
branch          = main
tag count       = 11
real staged     = 0
working tree    = dirty（tracked-modified 29 · untracked 102 —— 即已登记的排除集）

P14 tag UAP-V0.1.10-P14-RUNTIME-SLICE → 15feebad（仍完好 · 未移动）
```

## 5. 状态

```text
P15 = formally committed locally
P15 = formally tagged locally
P15 = NOT PUSHED

PUSH = FORBIDDEN · GITHUB RELEASE = FORBIDDEN · P16+ = FORBIDDEN
下一阶段（须新的独立指令）= P15 REMOTE PUSH GATE
```

