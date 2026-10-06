# P11 — ACCEPTANCE MATRIX（Triggers / Cross-table Constraints · DECISION FREEZE APPLIED）

> **状态（2026-09-25 更新）**：`OQ-P11-01`…`OQ-P11-14` 已**全部冻结**为 `D-P11-01`…`D-P11-14`
> （见 `PLATFORM_DECISION_LOG.md` 附录 H）；`CF-1`/`CF-2`/`CF-3` **CLARIFIED** · `CF-4` **INTENTIONAL / FROZEN**。
> 全部条目处于 **`FROZEN-DESIGN`（决策已冻结 → 待实施）** 或 **`ASSET`（既有冻结 / 先例）** 或
> **`PASSED`（本轮只读实测通过）** 或 **`BLOCKED`（实施未授权）**。
> **数字为脚本实测**（按 ID 前缀分组、**逐行只取状态列**计数），非估算。
> **不构成验收结论**；**本轮零实施**（无 trigger / 无 function / 无 migration / 无代码 / 无测试变更）。

## 0. ID 前缀映射

| 前缀 | 类别 | 前缀 | 类别 |
|---|---|---|---|
| `BASE-` | 基线与保护 | `REC-` | 递归审阅 |
| `INV-` | 触发器清单完整性 | `DEP-` | 依赖审阅 |
| `GHIJ-` | G/H/I/J 完备性 | `MIG-` | 迁移影响 |
| `OWN-` | P10 / P11 所有权 | `P09-` | P09 保护 |
| `XTAB-` | 跨表不变量映射 | `DAUTH-` | D-AUTH 保护 |
| `FUNC-` | 函数安全审阅 | `DPLAT-` | D-PLAT 保护 |
| `SCOPE-` | 范围保护 | `CONS-` | 跨决策扫描 |
| `GATE-` | 门禁汇总 | `TRACE-` | **OQ ↔ Matrix 追溯（14 / 14）** |

> **状态词表**：`ASSET` = 既有冻结资产 / 既有先例 · `PASSED` = 本轮只读实测通过 ·
> **`FROZEN-DESIGN`** = **决策已冻结**（`D-P11-01..14`），实施待授权 · `BLOCKED` = 被实施门禁明确阻塞。
>
> > **词表升级（语义映射 1:1）**：原 `PENDING` → **`FROZEN-DESIGN`**；`CONS-01..04` 与 `GATE-01` → **`PASSED`**；
> > `GATE-02`/`GATE-03` → **`BLOCKED`**（实施未授权）。
>
> ⚠ **canonical 编号重映射**：本轮 Human Decision 的 **`OQ-P11-06` = Version Immutability（`K`）**、
> **`OQ-P11-07` = Tenant / Space / Authorization 边界**；PREP 轮编号**相反**。本矩阵 `TRACE-06`/`TRACE-07`
> 已按 canonical 重排（见 §16）。
>
> **状态提取规则（指令 §10 强制）**：状态**只**从**状态列（行末单元格）**提取；
> **不扫描整行文本**（避免正文中的状态词污染分类）。Markdown 比对统一执行
> **双侧归一**（去 emphasis / 去反引号 / 统一空白 / 统一大小写）。

---

## 1. BASE — 基线与保护

| ID | 要求 | 证据 | 状态 |
|---|---|---|---|
| BASE-01 | HEAD = `034ee97…` · tag `UAP-V0.1.8-AUTHORIZATION` · tags = 8 · remote = none | git | **PASSED** |
| BASE-02 | `alembic heads` = 单头 `0012_authz_enforcement` · `0013+ = 0` | 命令 | **PASSED** |
| BASE-03 | `0010` / `0011` / `0012` sha256 = 保护值（逐字节未变） | sha256sum | **PASSED** |
| BASE-04 | 本轮 0 DDL · 0 DML · 0 trigger · 0 function · 0 migration · 0 `alembic upgrade\|downgrade` | git + 命令 | **PASSED** |
| BASE-05 | 本轮 0 code / test / config 变更 | git diff | **PASSED** |
| BASE-06 | 本轮 0 既有文档修改 · 0 commit · 0 tag · 0 push | git status/log | **PASSED** |

## 2. INV — 触发器清单完整性

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| INV-01 | 迁移内 `CREATE TRIGGER` 实测清点 = **24 语句 / 8 migration** | 命令 | **PASSED** |
| INV-02 | A–M 清单**逐项对账**完成（15 项 A/B/C/C2/D/E/F/F2/G/H/I/J/K/L/M） | `STEP1B_TRIGGER_INVENTORY.md` | **PASSED** |
| INV-03 | 已实现 9 项识别（A/B/C/C2/D/E/F/F2/K） | 命令（0003–0011） | **PASSED** |
| INV-04 | `L`（`tg_audit_immutable`）= **P10-owned**，未实现且不在 P11 | `D-P10-11` | **PASSED** |
| INV-05 | `M`（events 无 trigger）= 无对象（非缺口） | 清单 §M | **PASSED** |
| INV-06 | **清单缺口 6 项**识别（`GAP-INV-1`） | 命令（0005/0006/0011） | **PASSED** |
| INV-07 | 同名异义 trigger 搜索 = **0 命中** ⇒ 无 `DO NOT MERGE` 需求 | 命令 | **PASSED** |
| INV-08 | 触发器物量**权威口径**（24 语句 vs 15 不变量触发器）冻结 | `OQ-P11-01` | `FROZEN-DESIGN` |
| INV-09 | 清单缺口（6 项）处置方式 → append-only 注记 + 不重排 letter | `OQ-P11-13` | `FROZEN-DESIGN` |
| INV-10 | A–M 清单**归属**（已实现 9 项仅复核、不重做） | `OQ-P11-01` | `FROZEN-DESIGN` |

## 3. GHIJ — G/H/I/J 完备性

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| GHIJ-01 | `G` `tg_acl_subject_exists` @ `resource_permissions` · BEFORE I/U OF subject 列 · 存在性 | `TRIGGER_INVENTORY` §G | `FROZEN-DESIGN` |
| GHIJ-02 | `H` `tg_acl_user_hard_delete` @ `users` · AFTER DELETE · 清理该 user ACL | §H | `FROZEN-DESIGN` |
| GHIJ-03 | `I` `tg_acl_role_delete_block` @ `roles` · BEFORE DELETE · 被引用则 RAISE | §I | `FROZEN-DESIGN` |
| GHIJ-04 | `J` `tg_agent_acl_expire` @ `agents` · AFTER · ACL 到期（`inherited=true, expires_at=now()`） | §J | `FROZEN-DESIGN` |
| GHIJ-05 | 时机确认：G/I = `BEFORE` · H/J = `AFTER` | `OQ-P11-03` | `FROZEN-DESIGN` |
| GHIJ-06 | `J` 双事件确认（`AFTER UPDATE OF status` **+** `AFTER DELETE`） | `OQ-P11-03` | `FROZEN-DESIGN` |
| GHIJ-07 | 失败语义 = `RAISE EXCEPTION` + 事务回滚（fail closed） | `OQ-P11-04` | `FROZEN-DESIGN` |
| GHIJ-08 | **禁止吞异常**（无 `EXCEPTION … THEN NULL`） | `OQ-P11-04` | `FROZEN-DESIGN` |
| GHIJ-09 | `G` 仅做**存在性**校验（不追加同租户约束） | `OQ-P11-07` | `FROZEN-DESIGN` |
| GHIJ-10 | `I` 与 `C`（BEFORE DELETE，同表）触发顺序澄清：字母序 · 语义独立 · 任一 RAISE 均回滚 | 本轮分析 | **PASSED** |
| GHIJ-11 | 四者依赖的**实测列/状态值**均存在（`inherited` · `expires_at` · `agents.status` 四值 · `acl_subject_types.key` 三值） | 命令（0007/0011） | **PASSED** |
| GHIJ-12 | 四者**独立**（表/时机/目的互异），**不得合并**为单一 trigger | 清单 + 本轮分析 | **ASSET** |
| GHIJ-13 | `G` **不得引用 `groups`**；**不得**承担 Authorization Evaluation | `D-P11-02` | `FROZEN-DESIGN` |
| GHIJ-14 | `H` **仅硬删除流程**清理 user ACL；**软删除不得通过 H 清理** | `D-P11-02` | `FROZEN-DESIGN` |
| GHIJ-15 | `I` 语义 = **ACL reference protection**，**不是**授权求值器 | `D-P11-02` | `FROZEN-DESIGN` |
| GHIJ-16 | `J` **不负责删除 agent 本身**（仅使 ACL 失效） | `D-P11-02` | `FROZEN-DESIGN` |

## 4. OWN — P10 / P11 所有权

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| OWN-01 | `tg_audit_immutable` **未实现**（`CREATE TRIGGER … audit_logs` = 0） | 命令 | **PASSED** |
| OWN-02 | P11 **四项禁止**：MUST NOT duplicate / replace / weaken / relocate L | `OQ-P11-10` · `D-P10-11` | `FROZEN-DESIGN` |
| OWN-03 | G/H/I/J 与 `events` / `audit_logs` / outbox **零交叠**（不读不写） | 本轮分析 | **PASSED** |
| OWN-04 | **禁止** P11 新增承载 audit 写入的 trigger | `OQ-P11-14` · `D-P10-11` | `FROZEN-DESIGN` |
| OWN-05 | `K`（`tg_version_immutable`）已实现 · 边界确认（P11 不重做、不含 L） | `OQ-P11-06` | `FROZEN-DESIGN` |
| OWN-06 | P10 冻结（`D-P10-01..18`）未被触碰 | PDL 附录 G | **PASSED** |
| OWN-07 | P11 **不得** CREATE / MODIFY `audit_logs` 或 `events` 的 trigger；**不得** replace `tg_audit_immutable` | `D-P11-10` | `FROZEN-DESIGN` |

## 5. XTAB — 跨表不变量 → 机制映射

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| XTAB-01 | `V-1`…`V-18` 机制映射表完成（18 项） | 本 PREP §6 | **PASSED** |
| XTAB-02 | **application rule 未被无依据提升为 trigger**（`V-15`…`V-18` 四项明确排除） | 指令 §5 · `B1-4_DEPENDENCY:102-103` | **PASSED** |
| XTAB-03 | `V-1`/`V-2`/`V-3` 判定为 **trigger**（FK/CHECK 不可表达）并给出依据 | 冻结文档 | **PASSED** |
| XTAB-04 | `V-4` 机制**不对称**（role 归档 → 授权层 · agent 归档 → trigger J）待裁定 | `OQ-P11-05` | `FROZEN-DESIGN` |
| XTAB-05 | `V-17`/`V-18`（role 归档 deny 跳过 · membership removed 实时校验）确认为**授权层职责** | `B1-4_SCHEMA_DESIGN:136/140` | **ASSET** |
| XTAB-06 | 机制选择依据完备（CASCADE 白名单 · RESTRICT 语义 · 多态边无 FK） | `CORE` §11.1 · `B1-4_DEPENDENCY:53` | **PASSED** |

## 6. FUNC — 函数安全审阅

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| FUNC-01 | 全仓 `SECURITY DEFINER` = **0**（8 migration / 24 trigger / 15 函数） | 命令 | **PASSED** |
| FUNC-02 | `G/H/I/J` 拟用 **`SECURITY INVOKER`**（默认），不引入提权面 | `OQ-P11-08` | `FROZEN-DESIGN` |
| FUNC-03 | `SECURITY DEFINER` **政策**（永久禁止 / 例外条件）待冻结 | `OQ-P11-08` | `FROZEN-DESIGN` |
| FUNC-04 | `search_path` / **schema-qualified** 引用政策待冻结 | `OQ-P11-08` | `FROZEN-DESIGN` |
| FUNC-05 | **security-definer privilege escalation** 风险 = 无（不引入） | 本轮分析 | **PASSED** |
| FUNC-06 | **cross-tenant leakage** 评估（`G` 仅存在性 · 是否需同租户） | `OQ-P11-07` | `FROZEN-DESIGN` |
| FUNC-07 | 函数设计要项登记齐全（WHEN / BEFORE-AFTER / 操作 / OLD-NEW / 失败 / 异常 / 命名 `enforce_*`） | 本 PREP §8.1 | **ASSET** |
| FUNC-08 | **本轮不得引入任何 `SECURITY DEFINER` function**（`INVOKER` = canonical） | `D-P11-08` | `FROZEN-DESIGN` |

## 7. REC — 递归审阅

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| REC-01 | `G` / `I` **无 hidden DML** ⇒ 无递归面 | 本轮分析 | **PASSED** |
| REC-02 | `H` 的 `DELETE` **不触发任何 trigger**（`resource_permissions` 无 DELETE 触发器；`G` 为 I/U） | 本轮分析 | **PASSED** |
| REC-03 | `J` 的 `UPDATE` **不触发 `G`**（SET 列表不含 `subject_type_id`/`subject_id`） | 本轮分析 | **PASSED** |
| REC-04 | **无互递归**（`resource_permissions` 上无回写 `agents`/`users`/`roles` 的触发器） | 本轮分析 | **PASSED** |
| REC-06 | **禁止增加 trigger chain**；`J` 的 SET 列表**不得**含 `subject_type_id` / `subject_id` | `D-P11-09` | `FROZEN-DESIGN` |
| REC-05 | 递归**禁令**冻结（禁写自身表 / 禁写 P10 对象 / J 为唯一受控 hidden DML / 禁写 `acl_subject_types`） | `OQ-P11-09` | `FROZEN-DESIGN` |

## 8. DEP — 依赖审阅

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| DEP-01 | `G/H/I/J` 表依赖（`users`/`roles`/`agents`/`acl_subject_types`/`resource_permissions`）**全部已存在** | 命令 | **PASSED** |
| DEP-02 | 历史阻断"引用不存在的 `agents`"**已随 P09（0011）解除** | `B1-4_DEPENDENCY:64` + 命令 | **PASSED** |
| DEP-03 | trigger **先于** P13 seed | `OQ-P11-12` · `DEPENDENCY:193` | `FROZEN-DESIGN` |
| DEP-04 | P11 **不新增索引**（复用既有 `ix_rp_subject`，0007 已建） | `OQ-P11-11` | `FROZEN-DESIGN` |
| DEP-05 | P11 **零 seed**（不插 `acl_subject_types`/`roles`/`users`/`permissions`） | `OQ-P11-12` | `FROZEN-DESIGN` |
| DEP-06 | `P10 → P11 → P12 → P13` 顺序未变更 | `D-PLAT-09` | **ASSET** |
| DEP-07 | `P11 semantic correctness` **MUST NOT** depend on `P12 business semantics`；所需性能支持缺失时**记录为 P12 dependency** | `D-P11-11` | `FROZEN-DESIGN` |

## 9. MIG — 迁移影响

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| MIG-01 | 本轮 migration = **0**（versions/ = 12 文件） | 命令 | **PASSED** |
| MIG-02 | 单头 `0012` · `0013+ = 0` | 命令 | **PASSED** |
| MIG-03 | P11 预计新增对象（**待授权**）：`trigger 4` · `function 4` · `table 0` · `index 0` · `seed 0` | 本 PREP §9 | `FROZEN-DESIGN` |
| MIG-04 | downgrade 顺序先例：**先 `DROP TRIGGER` 再 `DROP FUNCTION`**（0007 先例） | `0007` downgrade | **ASSET** |
| MIG-05 | `alembic upgrade\|downgrade` **未执行**（仅 `heads` 只读查询） | 命令 | **PASSED** |

## 10. P09 — P09 保护

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| P09-01 | `0011` sha256 = 保护值（逐字节未变） | 命令 | **PASSED** |
| P09-02 | P09 四表（`agents`/`agent_versions`/`agent_permissions`/`tool_executions`）未被触碰 | git diff | **PASSED** |
| P09-03 | P09 相关测试文件未被修改 | git diff | **PASSED** |

## 11. DAUTH — D-AUTH 保护

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| DAUTH-01 | `D-AUTH` 条目仍 = **25**（22 FROZEN + 3 DEFERRED） | PDL | **PASSED** |
| DAUTH-02 | `D-AUTH-15` / `D-AUTH-23` 未变（无 supersession） | PDL | **PASSED** |
| DAUTH-03 | **trigger ≠ authorization evaluation / ACL evaluation / policy engine** 边界确认（含 `G` 是否需同租户） | `OQ-P11-07` | `FROZEN-DESIGN` |

## 12. DPLAT — D-PLAT 保护

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| DPLAT-01 | `D-PLAT-09` 路线 A **未 supersede** | PDL | **PASSED** |
| DPLAT-02 | `D-PLAT-10`（P11 = G/H/I/J）**未被修订** | PDL | **PASSED** |
| DPLAT-03 | `D-P10-01..18`（P10 冻结）**未被触碰** | PDL 附录 G | **PASSED** |
| DPLAT-04 | `D-PLAT-11`（首个主体只经 P13）未被触碰 | PDL | **PASSED** |

## 13. SCOPE — 范围保护

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| SCOPE-01 | P11 **未扩张**至 P10 / P12 / P13 / Agent Runtime / AI Gateway Runtime / Tool Runtime / worker | 指令 §3 | **PASSED** |
| SCOPE-02 | P11 **不含** seed 工作 | `OQ-P11-12` | `FROZEN-DESIGN` |
| SCOPE-03 | P11 **不含** index 工作（属 P12） | `OQ-P11-11` | `FROZEN-DESIGN` |
| SCOPE-04 | P11 **未吞入** business authorization semantics | 指令 §3 | **PASSED** |
| SCOPE-05 | 本轮变更文件仅 **P11 文档 + 2 处 append-only clarification**（全部 `.md`） | git status | **PASSED** |
| SCOPE-06 | P11 **只建立 structural protection**（不承担授权决策/ACL 求值/策略引擎） | `D-P11-07` | `FROZEN-DESIGN` |

## 14. CONS — 跨决策扫描（Charter §7）

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| CONS-01 | `CF-1` **`GAP-INV-1`** = **CLARIFIED**（supplementary inventory gap · inventory completeness issue，**非** implementation gap） | `D-P11-013` · 附录 H.2 | **PASSED** |
| CONS-02 | `CF-2` = **CLARIFIED**（P3 陈旧 audit-writing 陈述；保持 application/service + P10 audit boundary） | `D-P11-014` · 附录 H.2 | **PASSED** |
| CONS-03 | `CF-3` = **CLARIFIED**（`P09-after is an explicit phase freeze, not a dependency-derived conclusion`） | `D-P11-013` · 附录 H.2 | **PASSED** |
| CONS-04 | `CF-4` = **INTENTIONAL / FROZEN**（role/agent 机制不对称 · 不得强制统一） | `D-P11-05` · 附录 H.2 | **PASSED** |
| CONS-05 | 陈旧"P11 已实现"声明扫描 = **0 命中** | 命令 | **PASSED** |
| CONS-06 | `FROZEN` vs `FROZEN` 冲突新增 = **0** | 本轮分析 | **PASSED** |
| CONS-07 | **编号重映射（`OQ-P11-06` ↔ `07`）已显式登记**（PDL 区段 + 本文档 §16 + PREP append-only 注记） | `D-P11-06` / `D-P11-07` | **PASSED** |

## 15. GATE — 门禁汇总

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| GATE-01 | `P11 DECISION FREEZE = PASSED`（14/14 OQ `FROZEN` ⇒ `D-P11-01..14`） | `PLATFORM_DECISION_LOG.md` 附录 H | **PASSED** |
| GATE-02 | `P11 IMPLEMENTATION = NOT AUTHORIZED` | 本轮指令 §4/§5 | **BLOCKED** |
| GATE-03 | `P12` / `P13` = `NOT AUTHORIZED` | `D-PLAT-09` · `D-P11-11` / `D-P11-12` | **BLOCKED** |
| GATE-04 | `Runtime Implementation Gate = CLOSED` | `D-AGENT-16` | **ASSET** |
| GATE-05 | `commit` / `tag` / `push` = 未执行 | 命令 | **PASSED** |

## 16. OQ ↔ MATRIX TRACEABILITY（**14 / 14**）

> 指令 §10 要求 **100% 追溯**。下表逐项列出每个 OQ 的矩阵落点（**非关键字命中；为显式映射**）。

| ID | OQ | 决策域 | 主要验收行 | 状态 |
|---|---|---|---|---|
| TRACE-01 | `OQ-P11-01` | trigger inventory ownership | `INV-08` · `INV-10` | **PASSED** |
| TRACE-02 | `OQ-P11-02` | G/H/I/J exact semantics | `GHIJ-01` · `GHIJ-02` · `GHIJ-03` · `GHIJ-04` | **PASSED** |
| TRACE-03 | `OQ-P11-03` | trigger timing | `GHIJ-05` · `GHIJ-06` | **PASSED** |
| TRACE-04 | `OQ-P11-04` | trigger failure semantics | `GHIJ-07` · `GHIJ-08` | **PASSED** |
| TRACE-05 | `OQ-P11-05` | cross-table consistency（V-4） | `XTAB-04` · `CONS-04` | **PASSED** |
| TRACE-06 | `OQ-P11-06` | **Existing Version Immutability Boundary**（canonical） | `OWN-05` | **PASSED** |
| TRACE-07 | `OQ-P11-07` | **Tenant / Space / Authorization Boundary**（canonical） | `GHIJ-09` · `FUNC-06` · `DAUTH-03` · `SCOPE-06` | **PASSED** |
| TRACE-08 | `OQ-P11-08` | security-definer / search_path | `FUNC-02` · `FUNC-03` · `FUNC-04` | **PASSED** |
| TRACE-09 | `OQ-P11-09` | recursion policy | `REC-05` | **PASSED** |
| TRACE-10 | `OQ-P11-10` | P10 / P11 ownership | `OWN-02` | **PASSED** |
| TRACE-11 | `OQ-P11-11` | P11 / P12 dependency | `DEP-04` · `SCOPE-03` | **PASSED** |
| TRACE-12 | `OQ-P11-12` | P11 / P13 dependency | `DEP-03` · `DEP-05` · `SCOPE-02` | **PASSED** |
| TRACE-13 | `OQ-P11-13` | 清单缺口 `GAP-INV-1` 处置 | `INV-09` · `CONS-01` | **PASSED** |
| TRACE-14 | `OQ-P11-14` | 既有 P3 不一致处置 | `OWN-04` · `CONS-02` · `CONS-03` | **PASSED** |

> **追溯完备性（脚本核对）**：`OQ-P11` 条目 **14** · 本表行 **14** ⇒ **100%**。

## 17. 汇总

| 分类 | 行数 | `ASSET` | `PASSED` | `FROZEN-DESIGN` | `BLOCKED` |
|---|---|---|---|---|---|
| BASE | 6 | 0 | 6 | 0 | 0 |
| INV | 10 | 0 | 7 | 3 | 0 |
| GHIJ | 16 | 1 | 2 | 13 | 0 |
| OWN | 7 | 0 | 3 | 4 | 0 |
| XTAB | 6 | 1 | 4 | 1 | 0 |
| FUNC | 8 | 1 | 2 | 5 | 0 |
| REC | 6 | 0 | 4 | 2 | 0 |
| DEP | 7 | 1 | 2 | 4 | 0 |
| MIG | 5 | 1 | 3 | 1 | 0 |
| P09 | 3 | 0 | 3 | 0 | 0 |
| DAUTH | 3 | 0 | 2 | 1 | 0 |
| DPLAT | 4 | 0 | 4 | 0 | 0 |
| SCOPE | 6 | 0 | 3 | 3 | 0 |
| CONS | 7 | 0 | 7 | 0 | 0 |
| GATE | 5 | 1 | 2 | 0 | 2 |
| TRACE | 14 | 0 | 14 | 0 | 0 |
| **合计** | **113** | **6** | **68** | **37** | **2** |

> **计数口径**：按 **ID 前缀**分组、**仅取状态列（行末单元格）** 判定主状态（不扫描整行文本）。
> **一致性断言（脚本已验证）**：`ASSET + PASSED + FROZEN-DESIGN + BLOCKED == 行数合计`。
> `FROZEN-DESIGN` = **决策已冻结**（`D-P11-01..14`），实施待授权（**无一项表示已实施**）。
> `TRACE` 组 = **14 行** ⇒ **OQ ↔ Matrix 追溯 = 14 / 14 = 100%**（canonical 编号）。
> `BLOCKED` = `GATE-02`（P11 实施未授权）+ `GATE-03`（P12/P13 未授权）。

---

**END OF P11 ACCEPTANCE MATRIX（2026-09-25 · READ-ONLY PREP · 全 103 行 = `ASSET` 6 + `PASSED` 62 + `PENDING` 35）**
**END OF P11 ACCEPTANCE MATRIX（P11 Decision Freeze 同步 · 词表升级 + 10 新行 + canonical TRACE 重排 + `CF-1..CF-4` 处置 ⇒ 实测 **113** 行 = `ASSET` 6 + `PASSED` 68 + `FROZEN-DESIGN` 37 + `BLOCKED` 2；2026-09-25）**
