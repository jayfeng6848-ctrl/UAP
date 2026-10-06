# UAP — BLOCKER `B-A1` FACT SHEET（revision 标识冲突）

> ## 状态
>
> ```text
> 轮次                      = OPEN-P10-1 IMPLEMENTATION BLOCKER RESOLUTION ROUND
> 性质                      = **STRICT READ-ONLY**（本文件为事实固化，不含任何实施动作、不含任何选择）
> BATCH-A                   = **BLOCKED**（保持）
> OPEN-P10-1 IMPLEMENTATION = **BLOCKED**（保持）
> 本文件不做                 = 不选择 RV-A / RV-B / RV-C / RV-D（Human 指令 §Phase 0 明令禁止）
> ```
>
> **本文件为 Phase 0 输出**：只重新读取并确认阻断事实。裁定请求见
> `OPEN_P10_1_REVISION_ID_RESOLUTION_REQUEST.md`。
>
> 本轮未做：`CREATE ROLE` · `GRANT` · `REVOKE` · `ALTER OWNER` · `CREATE|ALTER|DROP FUNCTION` · `C2 修改` ·
> `0007 修改` · migration 创建 · `DDL` · `DML` · `alembic upgrade|downgrade` · code/config/testkit 修改 ·
> `commit` · `tag` · `push`。数据库侧**仅 `SELECT` 类只读查询**（**本轮无任何写入探针**）。

---

## 1. `alembic_version` 当前约束（**活体实测 · 只读**）

| 项 | 实测值 | 取证方式 |
|---|---|---|
| 表 | `public.alembic_version` | `information_schema.columns` |
| 列 | `version_num` | 同上 |
| `data_type` | `character varying` | 同上 |
| `udt_name` | `varchar` | 同上 |
| **`character_maximum_length`** | **`32`** | 同上 |
| `is_nullable` | `NO` | 同上 |
| 主键 | `alembic_version_pkc`（`version_num`） | 既有基线 |
| 当前 head | **`0015_p12_indexes`** | `SELECT version_num` + `alembic heads` ⇒ **单头** |
| 该表存在于 | **仅 `uap_b1_test`** | `uap` / `uap_test` 均**无** `alembic_version`（前者 base、后者仅 legacy 两表） |

```text
列宽来源：Alembic 1.19.2 自身的 `version_table` DDL 固定为 `VARCHAR(32)`（非本仓库自定义）
⇒ 该 32 是**上游硬约束**，不因本项目配置而改变；新建库亦为 varchar(32)。
```

---

## 2. 现有 revision 命名规则（**实测 15/15 一致**）

```text
15 个 revision 全部满足：
  ① `filename == revision`（`migrations_alembic/versions/<revision>.py`）  ⇒ 15/15 True
  ② 长度 ≤ 32                                                            ⇒ 15/15 True（max = 30，min = 13）
  ③ 形状 = `^\d{4}_[a-z0-9_]+$`（`config/build_info.py::REVISION_PATTERN`，为**构建期工件校验器所复用**）
  ④ 4 位零填充序号 + `_` + 小写 slug
```

| revision | len | | revision | len |
|---|---|---|---|---|
| `0001_baseline` | 13 | | `0009_timestamp_precision` | 24 |
| `0002_b1_0_infrastructure` | 24 | | `0010_b1_6_ai_gateway` | 20 |
| `0003_b1_1_root_identity` | 23 | | `0011_p09_agent_tool_permission` | **30（现行最长）** |
| `0004_b1_2_tenant_space` | 22 | | `0012_authz_enforcement` | 22 |
| `0005_b1_3_authorization` | 23 | | `0013_p10_event_audit` | 20 |
| `0006_b1_3_bootstrap_state` | 25 | | `0014_p11_triggers` | 17 |
| `0007_b1_4_resource_acl` | 22 | | `0015_p12_indexes` | 16 |
| `0008_b1_5_tool_registry` | 23 | | | |

**仓库内既有守卫（4 处，file-scoped）直接断言该规则**：

| 守卫 | 断言 |
|---|---|
| `tests/integration/test_agent_tool_permission_schema.py:324-325` | `path.stem == "0011_p09_agent_tool_permission"` · `len(path.stem) <= 32` |
| `tests/integration/test_ai_gateway_schema.py:880 / 922 / 923` | `MIGRATION_FILE.stem == REVISION` · `len(REVISION) <= 32` |
| `tests/integration/test_p10_event_audit_schema.py:677-678` | `MIGRATION_FILE.stem == REVISION` · `len(REVISION) <= 32` |
| `tests/integration/test_p12_indexes.py:98-99` | `MIGRATION_FILE.stem == REVISION` · `len(REVISION) <= 32` |

`REVISION_PATTERN` 亦被构建期工件校验复用：`config/build_info.py:34/46`（`is_valid_revision`）⇒ 任何 revision 必须同时通过该模式。

---

## 3. 冲突量化

```text
requested revision（REQ-4 授权消息）  = 0016_open_p10_1_database_trust_boundary
  长度                                = **39**
  形状                                = 通过 `^\d{4}_[a-z0-9_]+$`
  长度约束                            = **不通过**（39 > 32，超限 **7**）

⇒ 阻断在三个**互相独立**的点同时成立：
  ① 运行期：Alembic 写 `alembic_version.version_num` ⇒ `value too long for type character varying(32)`
     （证据见 `OPEN_P10_1_IMPLEMENTATION_BATCH_A_BLOCKER_REPORT.md` §1.2 `E-A3`：事务内探针 +
      `E-A4` 30 字符对照可插入，两探针均已 `ROLLBACK` ⇒ 净 DML = 0）
  ② 静态：`filename == revision` 约定 ⇒ 文件名同样不可用
  ③ 构建期：`config/build_info.py::REVISION_PATTERN` 通过，但工件与 DB 比对时仍受 ① 约束
     （`EXPECTED_ALEMBIC_REVISION` 工件必须承载**实际** revision 串）
```

---

## 4. REQ-4 原始授权文本（**逐字**）与其性质判定

### 4.1 逐字文本（Human 2026-09-27 `IMPLEMENTATION AUTHORIZATION` §1 `§3.2` 块）

```text
REQ-4-CUSTOM =
OPEN-P10-1 独占 migration revision = 0016。
P13 seed 不占用 0016。
后续 P13 seed revision = 0017_p13_seed，
但本轮不得创建或实现 0017。
0016 revision 的 canonical identity：
0016_open_p10_1_database_trust_boundary
实际文件名与 revision 必须满足既有 Alembic 命名规则；
如既有命名规则要求完全按批准字符串落名，不得自行变体。
```

### 4.2 **决定性事实**：39 字符串的**唯一来源**是这条授权消息

全仓检索 `database_trust_boundary`（排除 `.git/`）命中 **4 行，全部位于本轮新写的
`OPEN_P10_1_IMPLEMENTATION_BATCH_A_BLOCKER_REPORT.md` 之内**（它是在**引用**授权消息）。

```text
⇒ 已冻结的权威载体 PLATFORM_DECISION_LOG.md 的 `# D-OP101-03`（`FROZEN · CUSTOM DECISION`）**不含**该 slug。
   其逐字原文只写：
     0016 归属 OPEN-P10-1 Database Trust Boundary Foundation；
     P13 seed 不占用 0016；
     P13 seed 在 OPEN-P10-1 完成并冻结、前置条件满足后使用下一连续 revision，
     即由后续 P13 Implementation Contract 正式登记为 0017_p13_seed。
     本裁定不授权创建 0016 或 0017。
⇒ 即：**FROZEN 决策冻结的是「`0016` 的归属」与「P13 = `0017_p13_seed`」，并**未**冻结任何 revision slug 字符串。**
   `0017_p13_seed`（13 字符）**合规**，不受本阻断影响。
⇒ 结论：**修订该 slug 的形态，不需要 supersede / 改写任何 `FROZEN` PDL 决策。**
   （`D-OP101-03` 的「影响范围」字段仅要求 P13 实施契约轮把 `0016_p13_seed` 重登记为 `0017_p13_seed`。）
```

### 4.3 该文本是否要求 39 字符串**作为 Alembic revision**？—— **两种读法均存活，Bot 不裁**

| 读法 | 依据（均逐字） | 是否自洽 |
|---|---|---|
| **读法 ①：39 字符串 = `revision` 本体** | 句 5「`0016` revision 的 canonical identity：」把该串**紧接在 `revision` 之后**；工程语用中 "canonical identity" 常即指 revision id | 与「实际文件名与 revision 必须满足既有 Alembic 命名规则」**冲突**（39 > 32）⇒ 需 Human 落一处 |
| **读法 ②：39 字符串 = 文档层 canonical identity（标签）**，实际 `revision`/文件名取合规形态 | 句 6 把「canonical identity」与「**实际文件名与 revision**」**显式并列区分**，并单独要求后者「必须满足既有 Alembic 命名规则」 | 自洽；但**合规形态的具体字符串文本中未给出** ⇒ 仍需 Human 指定 |

**关键限定**：句 7「如既有命名规则要求完全按批准字符串落名，**不得自行变体**」
⇒ 无论取哪种读法，**Bot 都不得自行生成合规形态**（这正是本轮 HARD STOP 的原因）。

### 4.4 阻断**不**触及的项（避免误扩大）

```text
· `0016` 这个**序号**本身：`D-OP101-03`（FROZEN）与 REQ-4 句 1 一致 ⇒ 无争议，继续有效
· `P13 seed = 0017_p13_seed`：13 字符，合规 ⇒ 不受影响
· `down_revision = "0015_p12_indexes"` 链式关系 ⇒ 与 slug 形态无关
· `D-OP101-03` FROZEN 记录本身 ⇒ 无需修改（见 4.2）
```

---

## 5. 本轮 Gate

| ID | 断言 | 实测 | 结果 |
|---|---|---|---|
| `F-01` | `alembic_version.version_num` 列宽 | `32`（`character varying`） | **PASS** |
| `F-02` | 当前 head 唯一 | `0015_p12_indexes`（单头） | **PASS** |
| `F-03` | 15 个 revision 全部 `filename == revision` | 15 / 15 | **PASS** |
| `F-04` | 15 个 revision 全部 ≤ 32 | max 30 / min 13 | **PASS** |
| `F-05` | 请求串长度 | 39 | **PASS** |
| `F-06` | 39 串在 PDL `D-OP101-03` 中出现次数 | **0** | **PASS** |
| `F-07` | 39 串全仓出现位置 | 仅本轮 blocker 报告内（4 行） | **PASS** |
| `F-08` | 未创建任何角色 / 授权 | 非 `pg_%` 角色 = 1 · 显式 GRANT 到非 owner = 0 | **PASS** |
| `F-09` | migration 集合未变 | 15 个 · `0016` / `0017` ABSENT | **PASS** |
| `F-10` | C2 / `0007` 未变 | C2 `md5` = `6867874166ae36966763c1026ab2af19` · `0007` sha `9e0105b9…` | **PASS** |
| `F-11` | 本轮无写入探针 | 数据库侧仅 `SELECT` | **PASS** |
| `F-12` | `HEAD` / tags / remote | `034ee97c…` · 8 · none | **PASS** |
| `F-13` | 本轮未做任何选择 | 本文件不含 RV 选择、不含推荐、不含排序性评价 | **PASS** |

---

## 6. 事实表结论

```text
BLOCKER `B-A1` 可复现 = 是（三项独立阻断点，见 §3）
REQ-4 文本性质    = **同时支持两种读法**（§4.3）；FROZEN 载体 **未**冻结任何 slug（§4.2）
⇒ 解除方式        = 唯一：Human 给出合规 revision 形态（或明示读法 ② 并把 slug 降为文档标签）
⇒ Bot 动作        = **不做选择**；请求见 `OPEN_P10_1_REVISION_ID_RESOLUTION_REQUEST.md`
```

---

## 7. 自证缺陷（如实披露）

```text
真实缺口 = **0**（本文件不含任何选择、推荐或排序；Phase 0 仅为事实固化）
脚本缺陷 = **5 项**（Gate harness v1 → v2 修正，全部非内容问题）：

① 路径前缀未归一（教训 29 **第 2 次复发**）：`os.walk` + `os.path.join` 在 Windows 产生 `./` 前缀，
   与 `git status` 风格的正斜杠无前缀路径做集合比较 ⇒ 假阴。修正：剥离前导 `./` 后再比对，
   并**同时断言集合内容**（而非仅断言行数）。
② 断言作用于**错误的文档**（教训 61 **第 4 次复发**）：把「四个候选字符串」的检查写在 FACT SHEET 上，
   而候选按 Human 指令只应出现在 **REQUEST** 上 ⇒ 假阴。修正：FACT SHEET 只断言「requested 串 + 长度 +
   列宽」，并**反向断言 FACT SHEET 不含 `RV-*` 候选**，另由 REQUEST 的断言覆盖候选枚举。
③ 否定式/自指式命中（教训 51 ② **第 3 次复发**）：BLOCK 的 §5「反向保证」逐字引用了 `` `**已选**` `` 这一
   被禁止的标记 ⇒ 「不得出现」类断言假阳。修正：改为否定式感知断言，并**双报** `affirmative=0 / raw=1`。
④ 同 ③ 的**第 4 次复发**，且发生在**本文件自身**：§7 的缺陷描述逐字引用了 `**已选**` ⇒ C6 假阳。
   修正后修正版仍假阳 ⇒ 根因是**否定词落在相邻行**（中文长句硬换行），逐行判定看不见 ⇒
   最终改为**邻行窗口（±1 行）**判定。
⑤ 同 ③ 的**第 5 次复发**：§7 的「未执行写入探针」描述逐字引用了 `BEGIN; INSERT` ⇒ D1 假阳。
   修正：同一套否定式感知 + 邻行窗口处置。

**通则（本轮新增，已回写 skill）**：任何 `token not in doc` 形式的断言，若**被检查文档本身**会
（在缺陷描述、反向保证、勘误块中）**引用**该 token，则该断言**必须**做否定式感知且**必须**用
**邻行窗口**而非逐行判定 —— 否则断言会随文档的自披露内容而失效。

另：本轮**未执行任何写入探针**（上一轮的 `BEGIN; INSERT …; ROLLBACK;` 探针仅作为**已留档证据**被引用），
     使「STRICT READ-ONLY」在本轮为**字面成立**。

Gate harness = %TEMP%/op_p10_1_decision_input_gate.py → ../uap-stage3-evidence/open_p10_1_decision_input_gate.log
             = **55 / 55 PASS**（exit 0）
```

---

**END OF BLOCKER `B-A1` FACT SHEET（2026-09-27 · STRICT READ-ONLY · 不含选择 · `BATCH-A = BLOCKED` · `0016 = ABSENT`）**
