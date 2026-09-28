# P15 F-RP-06 HASH-BASIS RECORD

## 0. Finding

```text
ID             = F-RP-06
Classification = PRE-EXISTING RELEASE MANIFEST HASH-BASIS DEFECT
Impact         = RELEASE BLOCKER（0.1.13 Release Gate 因此 BLOCKED）
P15 functional causality = NONE
Status         = CLOSED（本轮修复：manifest 修正 + hash method 冻结）
```

```text
0.1.13 Release Gate 实测：
  manifest declared hashes = 12
  canonical（committed blob）match = 11
  mismatch = 1
```

---

## 1. Affected file

```text
docs/architecture/DEPENDENCY_RULES.md
```

## 2. 三份字节对照（同一 commit 5244b5916e51eebc958bb3f844dbc579d66014f3）

| 来源 | SHA-256 | 说明 |
|---|---|---|
| Manifest（当时记录值） | `ba82fde57f9bc183e98579e00e1dd6644e8750fb52fc9dd28dcabf3ed48afe78` | Windows 工作区渲染（CRLF/LF 混合行尾） |
| Committed Git blob | `5bf516f5cf03ce1d37b195e7fb4d63663ff85cbebaa82719d5f9c5f6393c5220` | `git cat-file blob HEAD:…`（canonical） |
| Clean clone（`git archive`） | `5bf516f5cf03ce1d37b195e7fb4d63663ff85cbebaa82719d5f9c5f6393c5220` | 与 committed blob 一致 |

```text
committed blob = clean clone  ⇒ 发布物自洽
manifest       ≠ committed    ⇒ 记录基准错误
```

（补充事实：本轮之后工作区该文件已被恢复为“含被排除的 AGENT_RUNTIME §9 / P09 delta”的
另一批次版本，其当前工作区渲染 sha256 = `6d194f4481bedb97703eec0d515497937d3ea1123d01f0cb7733d6f005e4e9c6`。
该工作区版本**不是** 0.1.13/0.1.14 发布物内容，仅作历史工作保留。）

## 3. Root cause

```text
· 仓库 .gitattributes = `* text=auto eol=lf` ⇒ canonical checkout 全平台 LF
· 该文件在 Windows 工作区原本为 CRLF；编辑后工作副本成为 CRLF/LF 混合行尾
· manifest 的 SHA-256 取自 “Windows worktree rendering”
· commit 时 git 依 .gitattributes 归一化为 LF ⇒ Git blob 字节与工作区渲染不同
· 结果：manifest 声明的哈希无法从发布物（committed blob / clean clone）复现
```

```text
内容差异 = 仅行尾（无字符内容差异、无功能差异）
功能影响 = 0（clean clone 测试全通过：P15 65/0 · Wave1 210/1(D-02) · Wave2 72/0）
但违反 §35/§37 “Manifest = Commit = Clean Clone” 的哈希判据 ⇒ Release Gate BLOCKED
```

## 4. Canonical hash source（本轮起正式冻结）

```text
优先级：
  1. git object blob          ← 推荐
  2. git archive canonical file
  3. clean clone file
  4. working tree file        ← FORBIDDEN as release hash source

推荐取法：
  git cat-file blob <tree>:<path>   （等价：git show <commit>:<path>）
  将 bytes 直接送入 SHA-256
```

```text
CRLF / LF 规则：
  Windows worktree line endings ≠ release artifact bytes
  .gitattributes = `* text=auto eol=lf` ⇒ release artifact canonical representation = LF
```

## 5. Resolution（0.1.14）

```text
1. docs/architecture/P15_V0_1_13_RELEASE_PAYLOAD_MANIFEST.md
   · 将该行 SHA-256 修正为 canonical blob 值 5bf516f5…
   · 更新 3 条版本元数据行（版本推进至 0.1.14 后的 canonical 值）
   · 新增 “Canonical Hash Method” 段（冻结基准 + 禁止工作区渲染）
   · 新增 “0.1.14 Corrective Payload” 段（登记本轮新增产物）
2. 版本元数据 0.1.13 → 0.1.14（pyproject / settings / compose）
3. 本记录（F-RP-06 evidence）
```

```text
未做（按契约明确禁止）：
  · 不批量归一化 17 个 CRLF tracked 文件的行尾
  · 不触碰 AUTHORIZATION / historical / P13 / P14 / BATCH-D 面文件
  · 不修改 0.1.11 / 0.1.12 / 0.1.13 的 commit 与 tag
```

## 6. Regression prevention

```text
· 所有 Release Payload 哈希一律从 committed blob / clean archive 计算
· manifest 增加 “Hash Basis = committed blob bytes” 声明
· 后续 Gate 的复算步骤固定为：
    ① git cat-file blob <tree>:<path> → ② SHA-256 → ③ 与 manifest 比对
· 若同一文件同时存在工作区渲染与 artifact 渲染，以 artifact 为准
```

```text
同类风险登记（未处理，非本轮范围）：
  当前工作区仍以 CRLF 存在的 tracked 文件 = 17
  （docs/api/README.md · docs/architecture/ARCHITECTURE.md · AUTHORIZATION_*.md（8）·
    docs/architecture/DEPENDENCY_RULES.md · docs/security/README.md ·
    services/authorization/permissions.py · subjects.py ·
    tests/contract/test_authorization_contract.py ·
    tests/unit/test_authorization_{permissions,policy,scope}.py）
  ⇒ 若进入未来 payload，必须按 §4 的 canonical 基准计算
```

**END OF P15 F-RP-06 HASH-BASIS RECORD**
