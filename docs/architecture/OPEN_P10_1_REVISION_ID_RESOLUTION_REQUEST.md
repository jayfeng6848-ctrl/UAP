# UAP — OPEN-P10-1 REVISION ID RESOLUTION REQUEST

> ## 状态
>
> ```text
> 轮次                      = OPEN-P10-1 IMPLEMENTATION BLOCKER RESOLUTION ROUND
> 文件性质                  = **DECISION REQUEST**（请求 · 非裁定 · 非授权 · 非实施）
> BATCH-A                   = **BLOCKED**（保持）
> OPEN-P10-1 IMPLEMENTATION = **BLOCKED**（保持）
> 本请求 ≠ revision 选择
> 本请求 ≠ implementation authorization
> ```
>
> 事实依据见 `OPEN_P10_1_BLOCKER_BA1_FACT_SHEET.md`（Phase 0 · STRICT READ-ONLY）。
> 待填写的裁定块见 `OPEN_P10_1_REVISION_ID_HUMAN_DECISION_BLOCK.md`（Phase 2）。
>
> 本文件**不含**任何实施动作，**不含**任何推荐或排序，**不选择** RV-A / RV-B / RV-C / RV-D。

---

## 1. 当前冲突事实

| 项 | 值 | 来源 |
|---|---|---|
| **requested revision（REQ-4-CUSTOM 逐字给出的字符串）** | `0016_open_p10_1_database_trust_boundary` | Human 2026-09-27 `OPEN-P10-1 IMPLEMENTATION AUTHORIZATION` §1 `§3.2` |
| **requested revision 长度** | **39 字符** | 实测 |
| **Alembic 限制** | `alembic_version.version_num` = `character varying`，**`max_length = 32`** | 活体 `information_schema.columns`（`uap_b1_test`）；该列宽由 **Alembic 1.19.2 自身**固定，非本项目自定义 |
| 超限 | **+7 字符** | 39 − 32 |
| 形状校验 | 通过 `^\d{4}_[a-z0-9_]+$`（`config/build_info.py::REVISION_PATTERN`） | 静态 |
| **`filename == revision` 约束** | `migrations_alembic/versions/<revision>.py`；**仓库 15/15 revision 全部满足**；4 处既有守卫直接断言该约束与 `len ≤ 32` | 实测 + 守卫 |
| 现有 revision 长度区间 | min **13** · max **30** · 全部 ≤ 32 | 实测 |
| 当前 head | `0015_p12_indexes`（**单头**） | `alembic heads` + `alembic_version` |
| 运行期后果 | `alembic upgrade` 写 `alembic_version` 时 ⇒ `ERROR: value too long for type character varying(32)` | 事务内探针（上一轮 · 已 `ROLLBACK`；见 blocker 报告 §1.2 `E-A3`/`E-A4`） |
| 39 字符串在 **FROZEN 载体**中的出现次数 | **0**（`PLATFORM_DECISION_LOG.md` 的 `# D-OP101-03` **不含**该 slug） | 全仓检索 `database_trust_boundary` ⇒ 命中仅在本轮 blocker 报告内 |
| ⇒ 治理含义 | FROZEN 冻结的是「`0016` 归属」与「P13 = `0017_p13_seed`（13 字符 · 合规）」；**未冻结任何 slug 字符串** ⇒ 确定 slug 形态**不需 supersede 任何 `FROZEN` 决策** | FACT SHEET §4.2 |

```text
三处互相独立的阻断点（任一成立即阻断）：
  ① 运行期：Alembic 写入 varchar(32) 列 ⇒ 值过长
  ② 静态  ：`filename == revision` ⇒ 文件名同样不可承载 39 字符
  ③ 构建期：`EXPECTED_ALEMBIC_REVISION` 工件必须承载**实际** revision 串，而其与 DB `alembic_version` 逐字相等
```

---

## 2. 可选路径（**逐字取自 Human 指令 §Phase 1 · 本表不做推荐、不做排序性评价**）

| 路径 | 字符串 | 长度 | ≤ 32 | 形状 | 备注 |
|---|---|---|---|---|---|
| **`RV-A`** | `0016_open_p10_1_trust_boundary` | **30** | yes | ok | 与现行最长者 `0011_p09_agent_tool_permission`（30）等长 |
| **`RV-B`** | `0016_p10_1_database_trust` | **25** | yes | ok | |
| **`RV-C`** | `0016_db_trust_boundary` | **22** | yes | ok | |
| **`RV-D`** | *CUSTOM* | 由 Human 给定（须 ≤ 32） | — | — | 亦可选择把 39 字符串**保留为文档层 canonical identity 标签**，而把实际 `revision`/文件名取 `RV-A`/`RV-B`/`RV-C` 之一 |

> **可选读法提示（事实陈述，非建议）**：REQ-4 句 6 将「canonical identity」与「实际文件名与 revision」**显式并列区分**，
> 并单独要求后者「必须满足既有 Alembic 命名规则」⇒ 「39 字符串作标签 + 合规形态作 revision」在文本上**可成立**。
> 但句 7「不得自行变体」使**合规形态的文本仍须由 Human 给出**。**本文件不采用、不推荐任何读法。**

---

## 3. 明确影响（**四种路径共同的结构性影响；差异仅在所涉字符串文本**）

### 3.1 Migration filename

```text
新增 1 个文件：migrations_alembic/versions/<revision>.py
  例（RV-A）：0016_open_p10_1_trust_boundary.py
约束：filename == revision（4 处既有守卫 + 仓库 15/15 惯例）
      length(filename − ".py") ≤ 32
文件数：15 → 16
```

### 3.2 Revision chain

```text
0016 的元信息（四种路径唯一差异 = `revision` 字面量）：
    revision      = "<选择的字符串>"
    down_revision = "0015_p12_indexes"      ← 固定，与 slug 形态无关
    branch_labels = None · depends_on = None
链长：15 → 16 · 单头：0015_p12_indexes → <选择的字符串>
`D-OP101-03`（FROZEN）冻结的内容**不受影响**：`0016` 序号归属 · P13 = `0017_p13_seed`（13 字符 · 合规）
`0017_p13_seed`：本阶段**不创建**（保持 ABSENT），且其长度无冲突
```

### 3.3 Acceptance Matrix trace（**须同步的既有断言：17 文件 / 34 处**）

```text
按 `0015_p12_indexes` 定位的现行引用（新 revision 落地后必然失效，须逐处处置）：

  tests/integration/test_agent_tool_permission_schema.py   :172 / :330 / :994 / :1032
  tests/integration/test_ai_gateway_schema.py              :70 (HEAD_REVISION) / :872 (守卫源码串)
                                                           / :1009 (len(revisions) == 15) / :1007 / :1012 / :1013
  tests/integration/test_alembic_smoke.py                  :53 / :179 / :186
  tests/integration/test_authorization_service.py          :42
  tests/integration/test_identity_schema.py                :55 / :216 / :220
  tests/integration/test_migration_lock.py                 :68 / :111 / :134
  tests/integration/test_p10_event_audit_schema.py         :60 (HEAD_REVISION) / :684 (get_heads)
  tests/integration/test_p11_triggers.py                   :65 / :391 / :503
  tests/integration/test_p12_indexes.py                    :1 / :21 / :24 / :108
  tests/integration/test_platform_timestamp_precision.py   :66 (CURRENT_HEAD)
  tests/integration/test_rbac_hardening.py                 :43
  tests/integration/test_rbac_schema.py                    :47 / :288
  tests/integration/test_resource_acl_schema.py            :106 / :238
  tests/integration/test_tenant_space_schema.py            :86
  tests/integration/test_tool_registry_schema.py           :95 / :669 / :748
  tests/security/test_authorization_security.py            :158
  tests/unit/test_generate_build_info.py                   :23 (REV ← `derive_head()` **真读图**)

  ⚠️ `test_p12_indexes.py:24`（`REVISION = "0015_p12_indexes"`）是 **P12 自身**的 revision ⇒ **必须保持 0015 不改**；
     同文件 `:108`（`get_heads() == [REVISION]`）则**必须**改为新 head。

矩阵/契约侧的追溯点：
  OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md  → `MIG-01`（filename==revision / ≤32 / 单 HEAD / down_revision）
                                                    `TEST-07`（17 文件逐项对账）· `TRACE-03`（→ MIG-01/MIG-02/TEST-07）
  OPEN_P10_1_IMPLEMENTATION_CONTRACT.md §3.3 / §6.1 / §6.2（rollback 目标）
  MIG-01 的**断言文本不变**：无论选哪条路径，其判据都是「filename == revision ∧ ≤32 ∧ 单头 ∧ down_revision == 0015_p12_indexes」
```

### 3.4 Rollback reference

```text
downgrade 目标（固定，与 slug 形态无关）：`0015_p12_indexes`
  0016.downgrade() ⇒ 复原 C2（`CC7-5`）· `REVOKE`（`D-OP101-12`）· 不 `DROP ROLE`
  契约 `RB-1…RB-6` 的文本**不因 slug 形态变化而改变**
`config/_build_info.py`（构建期工件 · git-ignored）= `EXPECTED_ALEMBIC_REVISION`
  ⇒ 必须承载**实际** revision 串；任何形态变更后须**重新生成**该工件
`scripts/generate_build_info.py`：从 Alembic 图离线推导唯一 head ⇒ **自动跟随**实际 revision，无需改码
```

### 3.5 影响差异汇总（四种路径之间）

| 差异维度 | 是否随路径不同 |
|---|---|
| migration 文件名字符串 · `revision` 字面量 | **是**（唯一差异） |
| `down_revision` / 链形状 / 单头性 | 否 |
| `MIG-01` / `TEST-07` / `TRACE-03` 的**断言文本** | 否（判据与字面量解耦，仅"期望值"随实际 revision 填） |
| 3.3 的 34 处测试同步（除 `test_p12_indexes.py:24`） | 否（处置方式相同，仅替换字面量） |
| `RB-1…RB-6` / downgrade 目标 / C2 与授权回滚面 | 否 |
| `config/_build_info.py` 工件 | 否（须重新生成，与形态无关） |
| 文档层 canonical identity（若 Human 采读法 ②） | **是**（39 字符串可保留为标签） |

---

## 4. 两点不得混淆

```text
本请求 ≠ revision 选择
    ⇒ 本文件只把冲突事实与可选路径**摆到 Human 面前**；不排序、不推荐、不预选。
    ⇒ Human 未给出 `REQ-4-CUSTOM-REVISION = …` 之前，`0016` 保持 **ABSENT**。

本请求 ≠ implementation authorization
    ⇒ `OPEN-P10-1 IMPLEMENTATION AUTHORIZATION = AUTHORIZED`（2026-09-27）已收到，
       但 **BATCH-A 的首步「确认 revision」客观不成立** ⇒ 依指令 §11 **HARD STOP**。
    ⇒ 本请求被答复（revision 形态确定）**也不自动**开启实施：BATCH-A 的其余前置
       （见 `OPEN_P10_1_REVISION_ID_HUMAN_DECISION_BLOCK.md` 的 `OI-B-1…OI-B-6`）须一并裁定。
    ⇒ `OPEN-P10-1 IMPLEMENTATION = BLOCKED` 在 Human 明确回复前**保持不变**。
```

---

**END OF OPEN-P10-1 REVISION ID RESOLUTION REQUEST（2026-09-27 · REQUEST · 不含选择 · 不含推荐 · `BATCH-A = BLOCKED` · `OPEN-P10-1 IMPLEMENTATION = BLOCKED`）**
