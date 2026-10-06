# UAP — OPEN-P10-1 IMPLEMENTATION ACCEPTANCE MATRIX

> ## 状态
>
> ```text
> 轮次      = OPEN-P10-1 IMPLEMENTATION PREP（READ-ONLY · DESIGN-CONTRACT ONLY）
> 矩阵状态  = **DRAFT · NOT IMPLEMENTED · NOT FROZEN**
> 配套契约  = OPEN_P10_1_IMPLEMENTATION_CONTRACT.md（Phase 1）· OPEN_P10_1_IMPLEMENTATION_PREP_BASELINE_REPORT.md（Phase 0）
> 未实施    = CREATE ROLE = 0 · GRANT/REVOKE = 0 · ALTER ROLE/OWNER = 0 · CREATE|ALTER|DROP FUNCTION = 0 ·
>             C2 modification = 0 · 0007 modification = 0 · 0016/0017 = ABSENT · DDL/DML = 0 · migration created = 0 ·
>             runtime modified = 0 · commit/tag/push = 0
> 性质声明  = **Decision Freeze ≠ Implementation Authorization** · `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED`
> ```
>
> **状态词表**：`PLANNED`（实施期须验证）· `BLOCKED`（存在阻断项，实施前必须解除）· `OPEN`（待 Human 裁定）·
> `PASSED`（**仅指本轮只读核验通过**，非实施通过）。
> **状态格口径**：状态**恒为最后一格**且取值**精确等值**；`TRACE-nn` 行仅 3 列（无状态列），**不计入**状态汇总。

---

## 1. `B` — 本轮只读基线证明（**`PASSED`**）

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **B-01** | C2 保持未变更（无身份判据） | 基线 §3.3 · `D-OP101-05` 未执行 | 只读读取 `pg_get_functiondef('enforce_acl_subject_types_protect')` | `INSERT` 段无条件 `RAISE`；**不含** `current_user` / `session_user` / `pg_has_role` | 出现任一判据 | **PASSED** |
| **B-02** | `0007` 保持未变更 | 基线 §3.4 | sha256 比对 `0007_b1_4_resource_acl.py` | `9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef` | 任一差异 | **PASSED** |
| **B-03** | `0016` / `0017` = ABSENT | 基线 §2 | 文件清单 + `alembic heads` | 单 HEAD = `0015_p12_indexes`；`versions/001[6-7]*` = 0 | 出现 `0016`/`0017` 或多个 HEAD | **PASSED** |
| **B-04** | 未创建任何角色 | 基线 §3.1 | `pg_roles` 计数（非 `pg_%`） | = **1**（仅 `uap`） | > 1 | **PASSED** |

---

## 2. `MIG` — Migration Acceptance

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **MIG-01** | revision 链正确：新 revision（`0016`）单 HEAD、`filename == revision`、revision id ≤ 32 字符、`down_revision` 指向 `0015_p12_indexes`、`branch_labels/depends_on = None` | 契约 §3.3 · `D-OP101-03` · 基线 §2 | 静态读迁移头 + `alembic heads` / `history` | 单 HEAD；链长 +1；无多头 / 断链 | 多头 / 链断 / `filename ≠ revision` / 越界 revision | **PLANNED** |
| **MIG-02** | downgrade 可逆：clean DB 上 `downgrade` 成功且**零残留**（对象与授权回到改造前基线） | 契约 §6.2 · `D-OP101-12` | `downgrade(0015)` → 断言残留对象数 = 0 且权限/所有权回到基线 | 残留 = 0；所有权与授权回到基线 | 残留对象 / 授权未回收 / 所有权未回退 | **PLANNED** |
| **MIG-03** | 所有权正确：**156** 对象 owner 全量转移至 `uap_migrator`（含表 / 索引 / 函数 / 分区父与子表） | 契约 §3.9 · `D-OP101-09` · 基线 §3.2 | `pg_class.relowner` / `pg_proc.proowner` 全量盘点 | owner 集合 = `{uap_migrator}`；**无混合所有权** | 存在仍归 `uap` 的对象且未登记 | **PLANNED** |
| **MIG-04** | 迁移**不创建角色**（角色归环境预置） | 契约 §3.4 · `D-OP101-04` | 迁移源码扫描 `CREATE ROLE` / `CREATE USER` | 可执行语句 = **0**（当前实测 = 0） | 出现任一角色创建语句 | **PLANNED** |
| **MIG-05** | GRANT 在**每个数据库**逐一落地（`GRANT` 不跨库） | 契约 §3.7 / §6.1 · `D-OP101-07` · 基线 `C-5` | 逐库读取 `information_schema.role_table_grants` | 每个目标库的授权集合一致且 == 约定最小集 | 某库缺失 / 集合不一致 | **PLANNED** |
| **MIG-06** | 不引入 `SECURITY DEFINER` | 契约 §3.5 · `D-P11-08` · 基线 §3.2 | 全库 `pg_proc.prosecdef` 断言 = 0 | 全库 `prosecdef = 0` | 任一为 true | **PLANNED** |
| **MIG-07** | downgrade **不含** `DROP ROLE` | 契约 §6.2 · `D-OP101-12` | 迁移源码扫描 `DROP ROLE` / `REASSIGN` | 命中 = **0** | 出现 `DROP ROLE` | **PLANNED** |
| **MIG-08** | 迁移确定性：连续两次升级后对象集合哈希一致；重复执行**幂等**（不产生重复授权 / 不报未知错误） | 契约 §6.1 · `D-P13-10` 同源纪律 | 升级 → 记录对象哈希 → 往返 → 再升级 → 比对哈希 | 两次哈希逐条一致；重复执行不产生重复授权 | 哈希不一致 / 重复授权 / 静默跳过 | **PLANNED** |

---

## 3. `SEC` — Security Acceptance

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **SEC-01** | runtime 角色**不能 DDL**（DB 层强制 + 正向断言 + 负向探针） | 契约 §3.8 · `D-OP101-08` · 基线 §3.1 | `has_schema_privilege` / `has_table_privilege` 逐项断言 + 以 runtime 身份尝试 DDL 必失败 | 全部 DDL 权限 = false；探针报错 | 任一 DDL 权限为 true / 探针成功 | **PLANNED** |
| **SEC-02** | runtime 角色**不能绕过 C2**（registry `INSERT` 仍被拒） | 契约 §3.5 · `D-OP101-05` · `D-P13-11` | 以 runtime 身份 `INSERT INTO acl_subject_types` | 被拒 | 写入成功 | **BLOCKED** |
| **SEC-03** | 迁移身份分离**可证**：生效 URL 的角色部分 ≠ runtime 角色；`SET ROLE` 到 migration 身份失败 | 契约 §3.10 / R-02.3 · `D-OP101-10` · 基线 `C-1…C-4` | 读取两路径的 `current_user` / `session_user`；以 runtime 身份 `SET ROLE` 断言失败 | 两路径角色不同；`SET ROLE` 失败 | 角色相同 / `SET ROLE` 成功 | **PLANNED** |
| **SEC-04** | 判据**不可伪造**：GUC / `application_name` / session flag / `SET ROLE` 均不能放行 | 契约 §3.2 · `D-OP101-05` · 基线 §3.3 | 以 runtime 身份伪造后重试 registry `INSERT` | 全部仍 DENY | 任一伪造成功 | **PLANNED** |
| **SEC-05** | C2 拒绝消息**逐字节一致**（`CC7-2`） | 契约 §5.1 · `D-OP101-05` · 基线 §3.3 | 捕获错误消息与 `0007` 原版**逐字节**比对 | 逐字节相同 | 任一差异 | **BLOCKED** |
| **SEC-06** | 受信 migration 身份获 `INSERT` 例外，**仅限** registry 目标行（`CC7-3`） | 契约 §5.1 · `D-OP101-05` | 以受信身份写入 registry；并断言其它表/其它操作无额外放行 | 目标行写入成功；放行面 = 仅 registry `INSERT` | 放行面溢出 | **BLOCKED** |
| **SEC-07** | 非 `INSERT` 保护语义**逐字不变**（`CC7-4`） | 契约 §5.1 · `D-OP101-05` | 比对 `DELETE` / `UPDATE(key immutable)` 分支文本 + 行为探针 | 文本逐字不变；行为与改前一致 | 任一差异 | **BLOCKED** |
| **SEC-08** | 实施期触发器**未被 `DISABLE`**（`CC7-1`） | 契约 §5.1 · `D-OP101-05` · `D-P13-11` | 断言 `pg_trigger.tgenabled = 'O'`；扫描迁移源码无 `DISABLE TRIGGER` / `ALTER TRIGGER` | 全程 `tgenabled = 'O'`；命中 = 0 | 出现禁用窗口 / 任一语句 | **BLOCKED** |
| **SEC-09** | downgrade 后 C2 恢复为**授权前版本**（`CC7-5`） | 契约 §5.1 / §6.2 · `D-OP101-05` / `D-OP101-12` | `pg_get_functiondef` 与授权前版本**逐字节**比对 | 逐字节相同 | 任一差异 | **BLOCKED** |

---

## 4. `RUN` — Runtime Acceptance

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **RUN-01** | 应用 DSN 分离：runtime 使用 runtime 键；migration 使用独立键；二者**不得**互相覆盖 | 契约 §3.10 · `D-OP101-10` · 基线 `C-1`/`C-3` | 配置面断言（键存在性与取值来源）+ 启动后 `current_user` 断言 | 两键存在且生效角色不同；migration 键不被 runtime 键覆盖 | 共用同一键 / 被覆盖 | **PLANNED** |
| **RUN-02** | 最小权限验证：runtime 的实际权限集合 == 约定最小集（无多、无少） | 契约 §3.7 · `D-OP101-07` | 逐表逐动词比对 `role_table_grants` 与约定矩阵 | 集合相等 | 多授 / 少授 | **PLANNED** |
| **RUN-03** | readiness 门不受影响：`/ready` 的迁移状态语义与 `EXPECTED_ALEMBIC_REVISION` 工件行为不变 | 契约 §1 · `D-PLAT-14`/`D-PLAT-15` | 契约测试 + 单头探针 | 语义不变；工件仍为构建期权威 | 语义变化 / 工件可被运行时覆盖 | **PLANNED** |
| **RUN-04** | runtime **行为无变化**（除权限面收窄外）：连接、ORM 层、功能路径与改造前一致 | 契约 §3.10 · `D-OP101-07` | 全量回归不下降（历史基线 **636 passed / 0 failed / 6 skipped**） | failed = 0；passed ≥ 基线 | 任一失败 / 数量下降 | **PLANNED** |

---

## 5. `TEST` — Test Acceptance

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **TEST-01** | 角色生命周期夹具：幂等预置受信 + runtime 角色；重复运行不报错、不重复创建 | 契约 §3.11 / R-01.5 · `D-OP101-11` · 基线 `T-6` | 连续两次运行夹具 | 第二次为幂等 no-op（或属性一致时跳过） | 第二次报错 / 重复创建 / 属性不一致却静默沿用 | **PLANNED** |
| **TEST-02** | 负向权限测试：以 runtime 身份执行 DDL 必失败（SEC-01 的负向面） | 契约 §3.8 · `D-OP101-08` | 负向探针（仅一次性测试库） | 报错 | 探针成功 | **PLANNED** |
| **TEST-03** | 集群隔离测试：测试不创建/删除影响其它库的集群级角色；库重建后角色仍在且状态一致 | 契约 R-01.2 / R-01.3 · `D-OP101-11` · 基线 `T-6` | `reset_test_database()` 后盘点 `pg_roles`；断言无 `DROP ROLE` | 角色集合不变；无跨库泄漏 | 角色消失 / 泄漏 / 被删除 | **PLANNED** |
| **TEST-04** | 双 DSN 夹具：同时提供 runtime / migration 两套连接能力 | 契约 §3.11 · `D-OP101-11` | 夹具能力断言 + 真实双角色会话 | 两套 DSN 均可用且角色互异 | 无法提供双角色 / 角色相同 | **PLANNED** |
| **TEST-05** | 八项可证性测试套件全通过（`D-OP101-13` 判据的可执行形式） | 契约 §3.13 · `D-OP101-13` · `OI-2` | 执行八项测试（含 C2 的 ALLOW / 复原项） | 八项全通过 | 任一项未通过 | **BLOCKED** |
| **TEST-06** | 既有守卫 rationale 同步：**断言谓词不变**，仅 rationale 文本更新，且集合运算证明最小改动 | 契约 §3.14 · `D-OP101-14` | 解析真实测试文件取 forbidden 集；与裁定名单求交 | `removed ⊆ {rationale 文本}` 且 `remaining ∩ 需改集 = ∅` | 断言被改 / 扩大改动面 / 守卫被删 | **PLANNED** |
| **TEST-07** | 测试同步面逐项对账：**17** 个引用 `0015_p12_indexes` 的文件、链长断言 `== 15`、heads 断言、`HEAD_REVISION` 常量 | 契约 §3.3 · `D-OP101-03` · 基线 `T-1…T-4` | 静态扫描 + 逐断言核对 | 每一处均被明确处置（更新或显式保留） | 存在未处置引用 / 断言失效 | **PLANNED** |

---

## 6. `GATE` 与 `OI`

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **GATE-01** | `D-OP101-13` 判据达成：**拓扑落地** **且** **八项测试全通过** | 契约 §3.13 · `D-OP101-13` | 判据重算（拓扑证据 + 八项测试结果） | 两者同时成立 | 仅其一成立 / 以文档声明代替证据 | **BLOCKED** |
| **GATE-02** | `CC-7 Implementation Gate` 全开（6 项条件） | 契约 §5 | 逐条核对 `G-CC7-1…6` | 6 / 6 满足 | 任一未满足 | **BLOCKED** |
| **GATE-03** | 本 PREP 轮**未实施**：`CREATE ROLE`/`GRANT`/`REVOKE`/`ALTER OWNER`/函数改写/DDL/DML/migration/commit/tag/push 全为 0 | 契约 §9 | 文件清单 + 活库只读断言 + `git diff` 审计 | 全部为 0 | 任一非 0 | **PASSED** |
| **GATE-04** | 「Decision Freeze ≠ Implementation Authorization」在基线与契约中**显式声明**且未被违反 | 契约 X-1 · 基线状态块 | 文本断言 + 活库证据 | 声明在位；本轮无实施动作 | 声明缺失 / 被违反 | **PASSED** |
| **OI-1** | 所有权转移的**成员资格前提**（`D-OP101-09 × D-OP101-02`）须 Human 裁定 | 契约 §8 `OI-1` · `R-06` | 等待 Human 裁定 | 已裁定并登记 | 未裁定即实施 | **OPEN** |
| **OI-2** | **C2 改写归属轮次**（`OPEN-P10-1` 内 vs `P13 B-1 Amendment`）须 Human 裁定 | 契约 §8 `OI-2` · `D-OP101-13` | 等待 Human 裁定 | 已裁定并登记 | 未裁定即实施 | **OPEN** |
| **OI-3** | 独立键**键名**与 `.env.example` 空值语义须 Human 裁定 | 契约 §8 `OI-3` · `D-OP101-10` | 等待 Human 裁定 | 已裁定并登记 | 未裁定即实施 | **OPEN** |

---

## 7. `TRACE` — `D-OP101-NN` ↔ Matrix 追溯（**100% 覆盖**）

| ID | Decision | 追溯目标 |
|---|---|---|
| `TRACE-01` | `D-OP101-01` | `SEC-03` · `TEST-01` · `MIG-04` |
| `TRACE-02` | `D-OP101-02` | `SEC-03` · `SEC-04` · `TEST-03` |
| `TRACE-03` | `D-OP101-03` | `MIG-01` · `MIG-02` · `TEST-07` |
| `TRACE-04` | `D-OP101-04` | `MIG-04` · `TEST-01` · `TEST-03` |
| `TRACE-05` | `D-OP101-05` | `SEC-02` · `SEC-05` · `SEC-06` · `SEC-07` · `SEC-08` · `SEC-09` |
| `TRACE-06` | `D-OP101-06` | `MIG-04` · `SEC-01` |
| `TRACE-07` | `D-OP101-07` | `SEC-01` · `RUN-02` · `MIG-05` |
| `TRACE-08` | `D-OP101-08` | `SEC-01` · `TEST-02` |
| `TRACE-09` | `D-OP101-09` | `MIG-03` · `MIG-02` · `OI-1` |
| `TRACE-10` | `D-OP101-10` | `RUN-01` · `SEC-03` · `OI-3` |
| `TRACE-11` | `D-OP101-11` | `TEST-01` · `TEST-03` · `TEST-04` |
| `TRACE-12` | `D-OP101-12` | `MIG-02` · `MIG-07` · `SEC-09` |
| `TRACE-13` | `D-OP101-13` | `GATE-01` · `TEST-05` · `OI-2` |
| `TRACE-14` | `D-OP101-14` | `TEST-06` |

```text
Decision 总数 = 14 · TRACE 行 = 14 ⇒ 追溯覆盖 = **14 / 14 = 100%**
```

---

## 8. 汇总

| 分组 | 行数 | `PASSED` | `PLANNED` | `BLOCKED` | `OPEN` |
|---|---|---|---|---|---|
| `B` | 4 | 4 | 0 | 0 | 0 |
| `MIG` | 8 | 0 | 8 | 0 | 0 |
| `SEC` | 9 | 0 | 3 | 6 | 0 |
| `RUN` | 4 | 0 | 4 | 0 | 0 |
| `TEST` | 7 | 0 | 6 | 1 | 0 |
| `GATE` + `OI` | 7 | 2 | 0 | 2 | 3 |
| **合计（不含 `TRACE`）** | **39** | **6** | **21** | **9** | **3** |

```text
行数核对   : 4 + 8 + 9 + 4 + 7 + 7 = 39 ✔
状态核对   : 6 + 21 + 9 + 3 = 39 ✔
TRACE 行   = 14（3 列 · 无状态列 · 不计入状态汇总）
矩阵总行数 = 53（39 状态行 + 14 TRACE 行）
本轮 PASSED = 6（4 项基线只读证明 + GATE-03 未实施证明 + GATE-04 性质声明核验）
BLOCKED    = 9（6 项 C2 相关 SEC + TEST-05 + GATE-01/GATE-02）
OPEN       = 3（OI-1 / OI-2 / OI-3 —— 须 Human 裁定）
```

---

**GATE 结论（2026-09-27 · OPEN-P10-1 IMPLEMENTATION PREP）**

```text
OPEN-P10-1 IMPLEMENTATION PREP = **COMPLETE**（文档与矩阵齐备）
Decision consumption           = `D-OP101-01…14` → **mapped 14 / 14**
实施风险                        = `R-01…R-04` 重点展开 · `R-05…R-08` 登记
`CC-7 Implementation Gate`      = **CLOSED**（6 项条件中 5 项未满足）
一致性扫描                      = raw 158 · 需后续同步 `IO-1`（4 行）/ `IO-2`（2 行）· **本轮零修改**
开放项                          = `OI-1` / `OI-2` / `OI-3`（**须 Human 裁定**）
DDL = 0 · DML = 0 · CREATE ROLE = 0 · GRANT = 0 · REVOKE = 0 · ALTER OWNER = 0 ·
函数改写 = 0 · C2 modification = 0 · 0007 modification = 0 · migration created = 0 · runtime modified = 0 ·
commit = 0 · tag = 0 · push = 0
⇒ `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED`
⇒ HARD STOP —— 等 Human 明确 `OPEN-P10-1 IMPLEMENTATION AUTHORIZATION = AUTHORIZED`
```

**END OF OPEN-P10-1 IMPLEMENTATION ACCEPTANCE MATRIX（2026-09-27 · DRAFT · NOT IMPLEMENTED · NOT FROZEN）**
