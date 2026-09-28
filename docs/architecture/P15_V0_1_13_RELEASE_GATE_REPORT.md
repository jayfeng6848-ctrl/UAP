# P15 V0.1.13 RELEASE GATE REPORT

## 0. 结论

```text
P15 V0.1.13 RELEASE GATE = BLOCKED
P15 V0.1.13 TAG          = NOT CREATED

阻塞项 = payload manifest 中 1 条 SHA-256 无法从 committed artifact 复现
         （docs/architecture/DEPENDENCY_RULES.md）
其余全部 Gate 判据 = PASS
```

```text
性质     = pre-tag gate report（不含 tag object SHA；tag object 尚未存在）
状态     = uncommitted working-tree evidence（不回写已发布的 §T/§U 决策记录）
日期     = 2026-09-28
```

---

## 1. Commit Identity（PASS）

```text
HEAD     = 5244b5916e51eebc958bb3f844dbc579d66014f3
HEAD^    = a238e85710fe7f13796a89cae8816bbd1ebbfca8
TREE     = 09e1ee37aec9fbb6389ff27535352a7dac471398
subject  = release(p15): resolve F-RP-05 and align event contract
author   = UAP Platform <platform@uap.local> 2026-09-28T22:37:28+08:00
```

## 2. Payload（PASS）

```text
git diff HEAD^ HEAD → 13 files changed, 1635 insertions(+), 6 deletions(-)
added = 7 · modified = 6 · deleted = 0
与 Foundation Resolution Manifest 记载一致
```

| 分类 | 文件 |
|---|---|
| CONTRACT ALIGNMENT | `core/event/interfaces.py`（M） |
| TEST | `tests/architecture/test_event_contract_alignment.py`（A） |
| DOCUMENTATION BASELINE | `docs/architecture/DEPENDENCY_RULES.md`（M） |
| GOVERNANCE | `docs/architecture/PLATFORM_DECISION_LOG.md`（M · 94/0 纯追加 → 附录 A–T 零改写） |
| CONTRACT (docs) | `docs/architecture/P15_EVENT_CONTRACT_ALIGNMENT.md`（A） |
| RELEASE EVIDENCE | `P15_FOUNDATION_RESOLUTION_REPORT.md` · `P15_WAVE1_BASELINE_CLOSURE.md` · `F_RP_05_F_RP_02_FOUNDATION_DECISION_PACKAGE.md` · `P15_F_RP_05_RESOLUTION_REPORT.md`（A） |
| MANIFEST | `P15_V0_1_13_RELEASE_PAYLOAD_MANIFEST.md`（A） |
| RELEASE METADATA | `pyproject.toml` · `config/settings.py` · `docker-compose.yml`（M） |

未出现：future feature · BATCH-D · F-RP-02 未授权项 · 无关历史文件 ·
Wave1/Wave2 allowlist 修改 · D-02 修改（均以 `git diff --name-status HEAD^ HEAD` 实测）。

## 3. 授权内容核对（PASS）

```text
core/event/interfaces.py（committed）
  L24: from core.audit.interfaces import new_event_id
  L30: return new_event_id()          ← _new_id() 委托 canonical generator
  L39: tenant_id: str | None = None
  L6 : ``EventBus != Outbox`` ...
  uuid4 = 0 命中

DEPENDENCY_RULES.md（committed）
  "Carrier faces"        = 2 命中
  "Agent runtime boundary" = 0 · "D-AGENT-01" = 0 · "G-10" = 0
  "implemented and accepted" = 0（P09 状态块未被重写）

F-RP-02 排除项（本 commit 未触碰）
  tests/conftest.py · infrastructure/database/__init__.py · tests/unit/test_generate_build_info.py
  tests/integration/test_runtime_db_wave1.py · Wave1/Wave2 allowlist 文档
```

## 4. Clean Clone 验证（PASS）

```text
clean clone = git archive HEAD（454 文件）
required untracked dependencies = 0
required worktree-only dependencies = 0（以 clean clone 实测为准）
  · Wave1 闭包中唯一非 clean 成员 = infrastructure/database/__init__.py（非必需）
  · 注：工作区保留了被排除的 DEPENDENCY_RULES.md §9 / P09 delta（属另一批次工作），
    该 delta 非 Wave1 断言的依赖（clean clone 下 210/1，仅 D-02 失败）

P15 smoke（4 文件）   = 65 passed / 0 failed / 0 collection error
Wave 1（17 文件）     = 210 passed / 1 failed / 0 collection error
                        （唯一失败 = D-02 historical：test_approved_reads）
Wave 2（9 文件）      = 72 passed / 0 failed / 0 collection error
新增 foundation 守卫   = test_event_contract_alignment 9 + test_p10_event_audit_boundary 11 = 20 passed
Forbidden tests       = 0（tests/unit/test_generate_build_info.py 未执行）
CF-C-4                = PASS（无目录级 sweep）
```

## 5. Migration / DB（PASS）

```text
alembic heads   = 0017_p13_seed（单一 head）
alembic history = 0012 → 0013 → 0014 → 0015 → 0016 → 0017
revision 文件   = 17（0018+ = 0）
fresh cycle（隔离 verification DB uap_p15_verify · 已删除）
  upgrade head → downgrade base → upgrade head = PASS
  seed = acl_subject_types 3 · permissions 12 · role_permissions 12 · users 0 · audit_logs 0
  objects = pg_class 156 · pg_proc 22 · pg_trigger 272

Formal DB `uap` = 0 表（prestate == poststate）
Test DB `uap_b1_test` = 0017_p13_seed · events 0（net zero）· users 0 · audit_logs 3113（append-only）
```

## 6. Security / Boundary / Version（PASS）

```text
Privilege fingerprint = 51/6/5/0/245
  runtime grants 51 · roles 6 · uap_app grants 5 · default ACL 0 · uap_migrator grants 245
C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff（未变）· CC-7 触发器 tgenabled = O（INTACT）
pg_class 156 · pg_proc 22 · pg_trigger 272
Core → Domain = 0 · core/event/interfaces.py 仅依赖 stdlib + core.audit
O-3 subject vocabulary 违规 token = 0 · O-5 production allowlist = EMPTY（production_allowlist() 返回空 allowlist）
Version sources = pyproject.toml / config/settings.py / docker-compose.yml = 0.1.13
PDL = 附录 U（L5004）新增 · 附录 A–T 零改写（diff 94/0 纯追加）
historic tags = UAP-V0.1.11（bc312cd → dc44c99）· UAP-V0.1.12（dfcc694 → a238e85）未变
remote/main = dc44c99（未推送）· real staged = 0
```

## 7. 阻塞项（FAIL）

```text
Gate 判据失败：payload manifest 的 SHA-256 必须可从 committed artifact 复现（§35 / §37）
实测：12 条哈希中 11 条与 committed blob 一致，1 条不一致
```

```text
文件        = docs/architecture/DEPENDENCY_RULES.md
manifest 记 = ba82fde57f9bc183e98579e00e1dd6644e8750fb52fc9dd28dcabf3ed48afe78
committed   = 5bf516f5cf03ce1d37b195e7fb4d63663ff85cbebaa82719d5f9c5f6393c5220
clean clone = 5bf516f5cf03ce1d37b195e7fb4d63663ff85cbebaa82719d5f9c5f6393c5220（与 committed 一致）
```

根因（实测）：

```text
· 仓库 .gitattributes = `* text=auto eol=lf` ⇒ canonical checkout 全平台为 LF
· 该文件在 Windows 工作区原本带 CRLF；编辑后工作副本成为 CRLF/LF 混合行尾
· manifest 的 SHA-256 是对该工作区渲染（混合行尾）计算的
· commit 时 git 依 .gitattributes 归一化为 LF ⇒ artifact 哈希不同
⇒ 该条哈希不能从发布物复现（内容除行尾外完全一致）
```

影响：

```text
功能性 = 无（clean clone 测试全通过：P15 65/0 · Wave1 210/1(D-02) · Wave2 72/0）
完整性 = manifest 的 “payload hashes 完全一致” 声明对 1/12 条不成立
         ⇒ 按 §37/§39，不得创建 tag
```

同类风险（登记）：

```text
当前工作区仍以 CRLF 存在的 tracked 文件 = 17 个
  docs/api/README.md · docs/architecture/ARCHITECTURE.md ·
  docs/architecture/AUTHORIZATION_*.md（8）· docs/architecture/DEPENDENCY_RULES.md ·
  docs/security/README.md · services/authorization/permissions.py ·
  services/authorization/subjects.py · tests/contract/test_authorization_contract.py ·
  tests/unit/test_authorization_permissions.py · test_authorization_policy.py ·
  test_authorization_scope.py
⇒ 这些文件若进入未来 payload，必须改以 committed blob / clean archive 计算哈希
```

## 8. 建议的补救方向（需独立授权，本轮未执行）

```text
Option 1（推荐）：新增 corrective commit（0.1.14 candidate）
  · 仅修正 manifest 中该条 SHA-256 为 canonical（LF）值 5bf516f5…
  · 或将该文件行尾归一化为 LF 后重算全部哈希（保持 artifact 与 manifest 一致）
  · 并在 manifest 中明确 “hash 基准 = committed blob / clean archive，而非 Windows 工作区”

Option 2：流程修复 —— 所有 payload 哈希一律从 `git cat-file blob <tree>:<path>` 或
  `git archive` 产物计算；禁止以 Windows 工作区渲染作为哈希基准。

Option 3：若人工裁定该差异不构成 release blocker（不推荐，与 §37 直接冲突），
  需在 Decision Log 记录显式豁免，再执行 Release Gate。
```

## 9. 本轮未执行事项

```text
tag 创建 = 未执行（Gate BLOCKED）
git push = 未执行
仓库代码/测试/allowlist = 未修改（本报告为唯一新增产物，且未提交）
```

**END OF P15 V0.1.13 RELEASE GATE REPORT（BLOCKED · TAG NOT CREATED）**
