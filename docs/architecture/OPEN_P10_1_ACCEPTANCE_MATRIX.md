# UAP — OPEN-P10-1 ACCEPTANCE MATRIX（**DRAFT · NOT FROZEN**）

> ## 状态
>
> ```text
> 轮次      = OPEN-P10-1 PREP（STRICT READ-ONLY · 设计阶段）
> 矩阵状态  = **DRAFT · NOT FROZEN**（裁定条件满足 0 / 7 ⇒ 不冻结）
> 配套契约  = OPEN_P10_1_PREP_REPORT.md（DRAFT）· OPEN_P10_1_DECISION_RESOLUTION.md（REQUEST SHEET）
> 未实施    = CREATE ROLE = 0 · GRANT/REVOKE = 0 · migration 新增/改动 = 0 · 0016+ = ABSENT · 0007 / C2 unchanged
> ```
>
> **状态词表**：`PENDING`（待 Human 裁定）· `PLANNED`（实施期须验证）· `BLOCKED`（存在阻断项，实施前必须解除）·
> `PASSED`（**仅指本轮只读核验通过**，非实施通过）· `OPEN`（待确认）。
>
> **记录格式**：每项含 `requirement / evidence source / test method / expected result / failure condition`。
> **状态格口径**：状态**恒为最后一格**且取值**精确等值**（内联注记移入证据列）。
> **`TRACE-nn` 行仅 3 列（无状态列）**，**不计入**状态汇总（防止把追溯目标文本误当状态）。

---

## 1. `IC` — 身份分离契约（设计层声明 · 实施期验证）

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **IC-1** | 存在**至少两个**数据库角色：`R_mig`（migration trust context）与 `R_app`（runtime application context） | PREP §5.1 · Human 裁定 §4 | 查询 `pg_roles` 断言两角色均存在且不同 | 两角色存在且互异 | 仅一个角色 / 角色相同 | **PLANNED** |
| **IC-2** | `R_app` **不是** `R_mig` 的成员（直接或间接）⇒ `SET ROLE R_mig` 在 runtime 凭据下**失败** | PREP §5.1 · Amendment `M-2` C 行 | 以 `R_app` 凭据执行 `SET ROLE R_mig`，断言报错 | 报错（权限不足 / 非成员） | `SET ROLE` 成功 ⇒ 提权可行 | **PLANNED** |
| **IC-3** | `R_mig` 与 `R_app` 凭据**不同**且由**不同配置键**承载（不得共用同一 DSN） | PREP §5.1/§9 · `E-8`…`E-12` | 配置面断言（键集合与取值来源）+ 启动后 `current_user` 断言 | 两键存在；两路径 `current_user` 不同 | 共用同一键 / 同一 DSN | **PLANNED** |
| **IC-4** | `R_app` **不持 DDL**（无 schema `CREATE` / 无对象 `ALTER`/`DROP` 权限） | `D-P10-13` 禁止项 · PREP §5.1 | `has_schema_privilege` / `has_table_privilege` 逐项断言 + 负向探针（尝试 DDL 必失败） | 全部为 false；DDL 探针报错 | 任一 DDL 权限为 true | **PLANNED** |
| **IC-5** | C2 放行判据**只**可为服务端身份（`current_user`/`session_user`/`pg_has_role`）；**不得**可为 GUC / `application_name` / 会话参数 / 临时标志 | Human 裁定 §2 + §5 · `CP-3`/`CP-4` | 函数体文本断言（禁用词表）+ 伪造探针 | 函数体不含禁用语料；伪造后仍 DENY | 出现 GUC / `application_name` 判据 | **PLANNED** |
| **IC-6** | `R_app` 路径的 registry INSERT 判定结果 = **与 0007 原版逐字相同的拒绝** | Amendment §9 判别法 · `D-P13-03` | 双角色对照探针：runtime INSERT ⇒ 捕获错误消息；与 0007 原文逐字节比对 | 消息逐字节一致 | 消息被改写 / 放宽 | **PLANNED** |
| **IC-7** | downgrade 后：C2 定义 = 0007 原文本（逐字节）· `R_mig`/`R_app` 及其 GRANT **无残留** | Amendment `A-3` · `D-P13-12` 同源纪律 | `pg_get_functiondef` 比对 + `pg_roles` / `role_table_grants` 盘点 | 函数定义逐字节相同；角色与授权均无残留 | 函数被改写 / 角色或授权残留 | **PLANNED** |

---

## 2. `INV` — 目标态不变量（`INV-01`…`INV-08`）

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **INV-01** | runtime 角色 ≠ migration 角色 | PREP §5.3 · Human 裁定 §4 | 两路径 `SELECT current_user, session_user` | 两者不同 | 相同 | **PLANNED** |
| **INV-02** | runtime **无法**成为 migration 角色 | PREP §5.3 · Human §5「runtime 可获得 migration 权限 = 不得」 | 以 runtime 凭据 `SET ROLE R_mig` 断言失败；并断言 `pg_auth_members` 无该成员关系 | `SET ROLE` 失败；无成员关系 | 成功 / 存在成员关系 | **PLANNED** |
| **INV-03** | runtime registry INSERT = **DENY** | Human 裁定 §4 · `D-P13-03` | runtime 凭据 `INSERT INTO acl_subject_types` | 被拒；消息 = 0007 原版逐字 | 写入成功 / 消息不同 | **PLANNED** |
| **INV-04** | 受信 context registry seed = **ALLOW**（仅目标行） | Human 裁定 §4 · `D-P13-04` | 受信凭据插入 registry 目标行；并断言其他一切写入仍被拒 | 目标行写入成功；其余被拒 | 受信路径无法写入 / 放行面超出目标 | **PLANNED** |
| **INV-05** | runtime **不持 DDL** | `D-P10-13` · PREP §5.3 | 权限面逐项断言（schema / 表 / 函数） | 全部 DDL 权限 = false | 任一持有 | **PLANNED** |
| **INV-06** | 判据**不可伪造** | Human §2/§5 · Amendment `M-1` | 以 runtime 凭据伪造 GUC（`set_config`）/ `application_name` / `SET ROLE` 后重试 INSERT | 全部仍 DENY | 任一伪造成功 | **PLANNED** |
| **INV-07** | downgrade 后 C2 定义**逐字节复原** | Amendment `A-3` | `pg_get_functiondef` 与 0007 原文比对 | 逐字节相同 | 任一差异 | **PLANNED** |
| **INV-08** | downgrade 后**无残留受信主体** | Amendment `A-3` · PREP §5.3 | `pg_roles` / `pg_auth_members` / `role_table_grants` 盘点 | 无 `R_mig` 实体与任何授权残留 | 任一残留 | **PLANNED** |

---

## 3. `R` — 角色 / 权限面裁定依赖项（**全部 `BLOCKED`：待 OQ 裁定**）

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **R-01** | 角色拓扑唯一确定（`RM-A` / `RM-B` / `RM-C` / `RM-D`） | `OQ-OP101-01` · PREP §6 | 决策载体文本断言（拓扑编号唯一出现） | 恰一个拓扑被 `FROZEN` | 多选 / 未选 | **BLOCKED** |
| **R-02** | migration identity 权限等级确定（`OQ-OP101-02`） | `OQ-OP101-02` · PREP §6 | `pg_roles.rolsuper` 断言与决策一致性 | 与裁定一致 | 与裁定不一致 | **BLOCKED** |
| **R-03** | C2 判据形态确定（`CP-A` / `CP-B`） | `OQ-OP101-05` · PREP §7 | 函数体文本断言（判据形态唯一） | 恰一种被 `FROZEN` | 未选 / 混用 `CP-C`（已排除） | **BLOCKED** |
| **R-04** | runtime GRANT 矩阵范围确定（表 × 动词） | `OQ-OP101-07` · PREP §3.2 | 矩阵逐项断言（集合相等） | 矩阵 == 决策集合 | 多授 / 少授 / 未定 | **BLOCKED** |
| **R-05** | 既有 156 对象所有权处置确定 | `OQ-OP101-09` · PREP §6 | `pg_class.relowner` 断言 | 与裁定一致 | 与裁定不一致 | **BLOCKED** |
| **R-06** | 角色创建位置确定（迁移 / 独立 bootstrap / 编排） | `OQ-OP101-04` · PREP §8 | 迁移源码断言（`CREATE ROLE` 存在性或不存在性唯一） | 与裁定一致 | 双写 / 未定 | **BLOCKED** |

---

## 4. `T` — 连带同步面

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **T-01** | revision 链与常量同步面（17 个测试文件 · 链长 `== 15` 断言 · `heads` 断言 · `HEAD_REVISION` 常量）在编号裁定后**逐项对账** | PREP §4.3/§10 · `OQ-OP101-03` | 静态扫描 `0015_p12_indexes` 引用面 + 逐个断言语义核对 | 引用面逐项明确处置 | 存在未处置引用 | **PLANNED** |
| **T-02** | 既有负向守卫 rationale（`G-1`/`G-2`/`G-3`）的同步口径经 Human 裁定；**断言谓词不改** | PREP §4.4 · `OQ-OP101-14` · skill 教训 16 | 解析真实测试文件取出 forbiden 集；与裁定名单求交；集合运算证明 | `removed ⊆ {rationale 文本}` 且 `remaining ∩ 需改集 = ∅` | 未裁定即改测试 / 扩大改动面 | **BLOCKED** |
| **T-03** | 测试基建支持双身份（预置 cluster 级角色 + 双 DSN 夹具 + 幂等/清理） | `OQ-OP101-11` · PREP §10 `T-3` | testkit 能力断言 + 真实双角色会话端到端 | 双角色夹具可用；角色幂等 | 无法提供双角色 / 角色泄漏 | **PLANNED** |
| **T-04** | 配置面同步（`config/settings.py` · `alembic.ini` · `.env.example` · `docker-compose.yml`） | `OQ-OP101-10` · PREP §9 | 配置键存在性与取值来源断言 | 与裁定一致 | 与裁定不一致 | **PLANNED** |
| **T-05** | 文档面同步（`CORE` §13「尚未实现」表述 · `MIGRATION_STRATEGY` §9 · `P10_IMPLEMENTATION_*` 的 `DEFER` 历史陈述）以**附录式现行口径声明**处理，不改写历史正文 | PREP §10 `T-5` | 陈旧声明二次裁决（raw / adjudicated 双报） | 历史正文零改写；现行口径可机读 | 改写了历史正文 | **PLANNED** |
| **T-06** | 守卫面：若新增"角色/GRANT 存在"的正向断言，须同时保留历史时点表述 | PREP §10 `T-6` | 断言集合运算（新增 ⊆ 正向集，历史保留） | 两类断言并存且互不矛盾 | 历史断言被删 | **PLANNED** |

---

## 5. `S` — 安全 / 伪造面（Human 明令禁止项）

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **S-01** | **不得**使用 `DISABLE TRIGGER` / `ALTER TRIGGER` 作为路径 | Human §5 · `D-P13-11` · FINAL DIRECTION `CP-1` | 源码 / 迁移文本断言 + 运行时探针（无禁用窗口） | 语料中无此类语句 | 出现任一语句 | **PLANNED** |
| **S-02** | **不得**使用 `session_replication_role` | Human §5 · FINAL DIRECTION `CP-2` | 文本断言 + 探针 | 语料中无该设置 | 出现 | **PLANNED** |
| **S-03** | **不得**以普通 GUC 作为安全机制 | Human §5 · FINAL DIRECTION `CP-3` · 实测 `E-14`…`E-16` | 禁用语料断言 + 伪造探针（`set_config` 后仍 DENY） | 伪造后仍 DENY | 伪造可放行 | **PLANNED** |
| **S-04** | **不得**以 `application_name` 判断作为安全机制 | Human §5 · FINAL DIRECTION `CP-4`（**本轮新增为显式禁止项**） | 禁用语料断言 + 伪造探针 | 伪造后仍 DENY | 伪造可放行 | **PLANNED** |
| **S-05** | **不得**引入 `SECURITY DEFINER` | `D-P11-08` · PREP §7 `CC-3` | `pg_proc.prosecdef` 全库断言 = 0 | 全库 `prosecdef = 0` | 任一为 true | **PLANNED** |

---

## 6. `D` — 本轮只读已证明项（**本轮 `PASSED`**）

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **D-01** | `0007_b1_4_resource_acl.py` **未被修改** | PREP §2 · 状态保持 §8 | `git status` 无该路径 | 无修改记录 | 出现修改 | **PASSED** |
| **D-02** | C2 **未变更**（未 `CREATE OR REPLACE FUNCTION` / 未 `DISABLE` / 未 `ALTER TRIGGER`） | PREP §2 · 状态保持 §8 | 本轮操作留痕审查（无此类语句执行） | 本轮 0 次 | 任一执行 | **PASSED** |
| **D-03** | `0016+` = **ABSENT**（单头 = `0015_p12_indexes`；`versions/001[6-9]*` = 0） | PREP §2 | 文件清单 + `alembic heads` | 单头；该模式文件数 = 0 | 出现 `0016+` / 多头 | **PASSED** |
| **D-04** | `0010–0015` sha256 **逐字节未变** | PREP §2 | 6 个文件 sha256 比对 | 前缀全匹配（`6d990723` / `cdaf8383` / `5ecd1ef3` / `da1bdffd` / `3be9c8c0` / `94b0d228`） | 任一不匹配 | **PASSED** |

---

## 7. `GATE`

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **GATE-01** | 冻结条件 `14 / 14` 裁定 + 7 项条件全满足 | RESOLUTION §15.2 | 逐项核对（`PENDING` 计数） | `PENDING = 0` 且 7 / 7 满足 | 存在 `PENDING` / 条件未满 | **PENDING** |
| **GATE-02** | 未实施：`CREATE ROLE` = 0 · `GRANT`/`REVOKE` = 0 · migration 新增/改动 = 0 · DDL/DML = 0 · commit/tag/push = 0 | PREP §0/§11 | 文件清单 + 语句留痕审查 | 全部为 0 | 任一非 0 | **PASSED** |

---

## 8. `TRACE` — `OQ` ↔ Matrix 追溯（**100% 覆盖**）

| ID | OQ | 追溯目标 |
|---|---|---|
| `TRACE-01` | `OQ-OP101-01` | `R-01` · `INV-01` |
| `TRACE-02` | `OQ-OP101-02` | `R-02` · `INV-02` · `IC-2` |
| `TRACE-03` | `OQ-OP101-03` | `T-01` · PREP §8 `MIG-2` |
| `TRACE-04` | `OQ-OP101-04` | `R-06` · PREP §8 `MIG-1` |
| `TRACE-05` | `OQ-OP101-05` | `R-03` · `IC-5` · `INV-03` · `INV-04` |
| `TRACE-06` | `OQ-OP101-06` | `R-01`（拓扑子集） · PREP `OUT-8` |
| `TRACE-07` | `OQ-OP101-07` | `R-04` · `INV-05` |
| `TRACE-08` | `OQ-OP101-08` | `IC-4` · `INV-05` · `S-01` |
| `TRACE-09` | `OQ-OP101-09` | `R-05` · `IC-4` |
| `TRACE-10` | `OQ-OP101-10` | `T-04` · `IC-3` |
| `TRACE-11` | `OQ-OP101-11` | `T-03` · `IC-2` |
| `TRACE-12` | `OQ-OP101-12` | `IC-7` · `INV-07` · `INV-08` |
| `TRACE-13` | `OQ-OP101-13` | `INV-01`…`INV-08` · GATE-01 |
| `TRACE-14` | `OQ-OP101-14` | `T-02` · PREP §4.4 `G-1`/`G-2`/`G-3` |

```text
OQ 总数 = 14 · TRACE 行 = 14 ⇒ 追溯覆盖 = **14 / 14 = 100%**
```

---

## 9. 汇总

| 分组 | 行数 | `PASSED` | `PLANNED` | `BLOCKED` | `PENDING` | `OPEN` |
|---|---|---|---|---|---|---|
| `IC` | 7 | 0 | 7 | 0 | 0 | 0 |
| `INV` | 8 | 0 | 8 | 0 | 0 | 0 |
| `R` | 6 | 0 | 0 | 6 | 0 | 0 |
| `T` | 6 | 0 | 5 | 1 | 0 | 0 |
| `S` | 5 | 0 | 5 | 0 | 0 | 0 |
| `D` | 4 | 4 | 0 | 0 | 0 | 0 |
| `GATE` | 2 | 1 | 0 | 0 | 1 | 0 |
| **合计（不含 `TRACE`）** | **38** | **5** | **25** | **7** | **1** | **0** |

```text
行数核对      : 7 + 8 + 6 + 6 + 5 + 4 + 2 = 38 ✔
状态核对      : 5 + 25 + 7 + 1 + 0 = 38 ✔
TRACE 行      = 14（3 列 · 无状态列 · 不计入状态汇总）
矩阵总行数    = 52（38 状态行 + 14 TRACE 行）
本轮 PASSED   = 5（4 项只读状态证明 + GATE-02 未实施证明）
唯一 PENDING  = GATE-01（冻结条件 0 / 7）
BLOCKED 全部来自裁定依赖（R-01…R-06 + T-02）
```

---

**GATE 结论（2026-09-26 · OPEN-P10-1 PREP）**

```text
OPEN-P10-1 PREP            = **READY FOR HUMAN DECISION**
Design contract (IC/INV)   = 记录完备（7 + 8 项），实施期验证
裁定依赖 (R/T-02)          = **BLOCKED**（`OQ-OP101-01…14` 全部 PENDING）
本轮只读证明 (D)           = **PASSED × 4**
未实施证明 (GATE-02)       = **PASSED**
冻结条件                   = **0 / 7** ⇒ `DECISION FREEZE WRITE = NOT PERMITTED`
下游                       = P13 B-1 Amendment（挂起）→ P13 Implementation（NOT AUTHORIZED）
⇒ 等待：`OQ-OP101-01`…`OQ-OP101-14` 的 Human 裁定（填毕 `OPEN_P10_1_DECISION_RESOLUTION.md` §1–§14）
```

**END OF OPEN-P10-1 ACCEPTANCE MATRIX（DRAFT · 2026-09-26 · NOT FROZEN）**
