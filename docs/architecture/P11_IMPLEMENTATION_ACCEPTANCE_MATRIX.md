# UAP — P11 IMPLEMENTATION ACCEPTANCE MATRIX（Triggers / Cross-table Constraints）

> ## 状态
>
> ```text
> DESIGN FROZEN
> IMPLEMENTATION AUTHORIZED（2026-09-26 Human Authorization）
> IMPLEMENTED · ACCEPTED
> ```
>
> 本矩阵是 `P11_IMPLEMENTATION_CONTRACT.md` 的**验收口径**。
> **契约轮**：`PASSED` = 只读核对通过；`PLANNED` = 设计已冻结、实施未授权。
> **实施轮（2026-09-26）**：全部 `PLANNED` 行已按 §14 的实施证据转为 **`PASSED`**。

---

## 1. MIG — 迁移（`0014_p11_triggers`）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| MIG-01 | `revision = "0014_p11_triggers"`（16 ≤32 字符）· `filename == revision` | 指令 §11 · 契约 §8 | **PASSED** |
| MIG-02 | `down_revision = "0013_p10_event_audit"` · `branch_labels = None` · `depends_on = None` | `D-PLAT-09` · NUM-1 冻结分配 | **PASSED** |
| MIG-03 | 单头：`alembic heads` = 仅 `0014_p11_triggers` · 链长 14 · 无分叉 | 指令 §11 | **PASSED** |
| MIG-04 | `0015+` = ABSENT（本轮及实施轮均不得创建 0015） | 指令 §0/§9 | **PASSED** |
| MIG-05 | upgrade 顺序 = 4 functions → G → H → I → J（函数先于触发器） | 指令 §11 · 契约 §8 | **PASSED** |
| MIG-06 | 0013_p10_event_audit 逐字节未变（sha256 `da1bdffd4ddd2202…`） | 指令 §11 · 契约 §8 | **PASSED** |
| MIG-07 | 迁移内 seed = 0（无任何 `INSERT INTO`）· 禁 CONCURRENTLY | `D-P11-12` | **PASSED** |
| MIG-08 | 迁移内 index = 0（CREATE/DROP INDEX = 0）· 无 0015 对象混入 | `D-P11-11` | **PASSED** |

## 2. TRIGGER — 逐个验证（禁止只数总数）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| TRIG-01 | **G** `tg_acl_subject_exists` 存在，挂载 `resource_permissions` · `BEFORE INSERT OR UPDATE OF subject_type_id, subject_id`（tgtype 23 + OF 列清单） | `D-P11-02/03` | **PASSED** |
| TRIG-02 | **G** 行为：valid user/role/agent → PASS ×3；missing ×3 → RAISE；未注册 type/非法 key（group）→ RAISE | 指令 §16 · 契约 §11 | **PASSED** |
| TRIG-03 | **G** 不引用 `groups`（函数体静态断言） | `P2-02` · `D-P11-02` | **PASSED** |
| TRIG-04 | **H** `tg_acl_user_hard_delete` 存在，挂载 `users` · `AFTER DELETE`（tgtype 9） | `D-P11-02/03` | **PASSED** |
| TRIG-05 | **H** 行为：硬删 user → 其 user-ACL 清理；软删 user → ACL 保留 | 指令 §16 | **PASSED** |
| TRIG-06 | **H** 不删 role ACL / agent ACL（WHERE 双条件限定 + 行为测试） | 指令 §4 | **PASSED** |
| TRIG-07 | **I** `tg_acl_role_delete_block` 存在，挂载 `roles` · `BEFORE DELETE`（tgtype 11） | `D-P11-02/03` | **PASSED** |
| TRIG-08 | **I** 行为：被 ACL 引用 → RAISE；未引用 → PASS（引用保护 ≠ 授权求值） | 指令 §16 · `D-P11-07` | **PASSED** |
| TRIG-09 | **I** 与 roles 既有 3 个 BEFORE DELETE 触发器行为级兼容（is_system / pm_lifecycle 场景复核） | 契约 §2.3 | **PASSED** |
| TRIG-10 | **J** `tg_agent_acl_expire` 存在，挂载 `agents` · `AFTER UPDATE OF status OR AFTER DELETE`（tgtype 25） | `D-P11-02/03` | **PASSED** |
| TRIG-11 | **J** 行为：status → archived ⇒ ACL `inherited=true ∧ expires_at≈now()`；其他 status 迁移不动作；DELETE agent ⇒ ACL 到期 | 指令 §16 | **PASSED** |
| TRIG-12 | **J** 隐藏 DML 不触发 G（SET 列表 ∉ G 监听列）· 不删 ACL 行 · 不改 subject 列 | `D-P11-09` | **PASSED** |
| TRIG-13 | 命名：4 个 trigger 名 / 4 个函数名实施前 0 命中、实施后恰好 1（无重复） | 契约 §2.4 | **PASSED** |
| TRIG-14 | 同表碰撞：G = resource_permissions 首个触发器 · H/J 事件不相交 · I 兼容（TRIG-09） | 契约 §2.3 | **PASSED** |
| TRIG-15 | 既有 24 条 CREATE TRIGGER + L 的**定义哈希清单**实施前后逐项一致（仅 +4） | 指令 §12 · 契约 §9 | **PASSED** |
| TRIG-16 | GAP-INV-1 的 6 个非 letter 触发器未被重排/迁入/重分类 | `D-P11-13` | **PASSED** |
| TRIG-17 | K = `tg_version_immutable`（agent/tool_versions）语义与所有权不变 | `D-P11-06` | **PASSED** |
| TRIG-18 | 触发器计数终态：父级 35→39 · 函数 17→21 · 语句 24→28 · pg6 总数 36→40 | 契约 §13.1 | **PASSED** |

## 3. FUNC — 4 个函数逐个

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| FUNC-01 | `enforce_acl_subject_exists()`：三向 key 分派 + RAISE 语义 = 契约 §3.1 | `D-P11-02` | **PASSED** |
| FUNC-02 | `enforce_acl_user_hard_delete()`：DELETE 范围 = 该 user 的 ACL = 契约 §3.2 | `D-P11-02` | **PASSED** |
| FUNC-03 | `enforce_acl_role_delete_block()`：EXISTS → RAISE / else RETURN OLD = 契约 §3.3 | `D-P11-02` | **PASSED** |
| FUNC-04 | `enforce_agent_acl_expire()`：非 archived 迁移短路 + SET 列表 = 契约 §3.4 | `D-P11-02/09` | **PASSED** |
| FUNC-05 | 全部 `LANGUAGE plpgsql` · 无 DDL / 无 GRANT / 无角色操作 | 契约 §4 | **PASSED** |

## 4. SEC — 安全面

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| SEC-01 | 4 函数 `prosecdef = false`（SECURITY INVOKER）· `SECURITY DEFINER` 全库 = 0 | `D-P11-08` | **PASSED** |
| SEC-02 | `pg_get_functiondef` 无 `SET search_path`（4 函数） | 指令 §7 | **PASSED** |
| SEC-03 | 无 privilege escalation 面（INVOKER + 无 DDL/GRANT） | 指令 §7 | **PASSED** |
| SEC-04 | 递归与回滚：G/H/I 无隐藏 DML · J→G 递归 = 无 · 全部 RAISE → 事务回滚（行为测试内建断言） | `D-P11-04/09` | **PASSED** |
| SEC-05 | 禁写面：4 函数不 INSERT/UPDATE/DELETE `audit_logs`，不触碰 `events`/outbox | `D-P11-14` · 指令 §8 | **PASSED** |
| SEC-06 | RLS = 0 · GRANT = 0 · 无额外权限体系 | `D-P11-07` · 指令 §7 | **PASSED** |

## 5. P10B — P10 边界（`D-P11-10`）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| P10B-01 | `tg_audit_immutable` 仍挂 `audit_logs` · 定义未变 · 归属 P10 | `D-P10-11` | **PASSED** |
| P10B-02 | `events` 上触发器 = 0（OBX5 保持）；outbox 列/行为零变化 | 契约 §5 | **PASSED** |
| P10B-03 | P10 表/列（events 22 · audit_logs 19）零变化；0013 未被修改（MIG-06） | 契约 §5 | **PASSED** |
| P10B-04 | 4 个新目标表不含任何 P10 触发器（所有权不相交不变式） | 契约 §10.1 S8 | **PASSED** |

## 6. P12B — P12 边界（`D-P11-11`）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| P12B-01 | 实施后 `ix_events_*` / `ix_audit_*` 等 P12 索引 = 0 · `0015` 未提前 | 指令 §9 | **PASSED** |
| P12B-02 | P11→P12 handoff 表：全部查找路径已覆盖（PK ×4 + `ix_rp_subject`）· **新增 P12 依赖 = 0** | 契约 §6（本轮实测） | **PASSED** |
| P12B-03 | P11 语义正确性不依赖 P12（handoff 表为证） | `D-P11-11`（本轮实测） | **PASSED** |

## 7. P13B — P13 边界（`D-P11-12`）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| P13B-01 | 实施轮零 seed（迁移无 INSERT + 行为夹具不落库） | 指令 §10 | **PASSED** |
| P13B-02 | head @0014 时 G/H/I/J 已挂载（trigger 先于 P13 seed 的链序证明） | 契约 §7 | **PASSED** |

## 8. REGRESSION — 回归

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| REG-01 | 全量回归：基线 596 passed / 0 failed / 6 skipped **不下降** | P10 实施轮基线 | **PASSED** |
| REG-02 | 新增套件 `test_p11_triggers.py` 全绿（指令 §16 全部行为） | 契约 §11 | **PASSED** |
| REG-03 | 既有套件同步后全绿（S1–S11 逐项 + head 面） | 契约 §10 | **PASSED** |

## 9. DOWNGRADE / ROUNDTRIP

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| DOWNG-01 | downgrade 0014→0013 逆序摘除（4 trigger → 4 function）· 8 对象零残留 | 指令 §11 · 契约 §8 | **PASSED** |
| DOWNG-02 | 零残留细目：pg_class/pg_proc/pg_trigger/information_schema 无 P11 残留 · 物理表 35 不变 | 契约 §8 | **PASSED** |
| RT-01 | upgrade → downgrade → upgrade：对象集哈希两次一致（迁移确定性） | P10 先例 | **PASSED** |
| RT-02 | 往返后 G/H/I/J 行为抽查（至少各 1 例）仍正确 | 契约 §11 | **PASSED** |

## 10. TEST — 测试同步（实施期执行 · S1–S11 = 契约 §10.1 处置表）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| TEST-01 | S1（P09 套件 T-12 翻转）· S2（P09_TRIGGERS ∪ J）· S3（SS-01 降级锚点核对） | 契约 §10.1 | **PASSED** |
| TEST-02 | S4（resource_acl 拆分）· S5（B14 精确集 ∪ G）· S6（TSEC4 翻转）· S7（TM8 head） | 契约 §10.1 | **PASSED** |
| TEST-03 | S8（BND1 → 所有权不相交不变式）· S9（pg6 36→40） | 契约 §10.1 | **PASSED** |
| TEST-04 | S10/S11（head 面 16 文件 + 链长 14 + 架构守卫常量） | 契约 §13.2 | **PASSED** |
| TEST-05 | 不触碰面：P12 契约/测试、T-22 forbidden 集、identity/tenant_space 子集断言 | 契约 §10.2（口径本轮冻结） | **PASSED** |

## 11. SCOPE / GATE — 本轮（契约轮）只读核对

| ID | 检查 | 证据 | 状态 |
|---|---|---|---|
| SCOPE-01 | `0014+` = ABSENT · versions = 13 · 单头 `0013` | harness 实测 | **PASSED** |
| SCOPE-02 | migration/DDL/DML/code/test/config 变更 = 0 · trigger/function implementation = 0 | harness 实测 | **PASSED** |
| SCOPE-03 | 本轮变更文件 ⊆ {本契约 · 本矩阵}（+仓库外 harness/证据）· 无非 `.md` 变更 | `git status --porcelain` | **PASSED** |
| SCOPE-04 | protected：`0010`/`0011`/`0012`/`0013` sha256 逐字节未变 | harness 实测 | **PASSED** |
| SCOPE-05 | commit = 0 · tag = 0 · push = 0（HEAD 仍 `034ee97` · tags 8 · remote 0） | harness 实测 | **PASSED** |
| GATE-01 | `P11 IMPLEMENTATION = NOT AUTHORIZED` · P12/P13/Runtime = NOT AUTHORIZED · Runtime Gate = CLOSED | 指令 §17/§18 | **PASSED** |
| XD-01 | 跨决策扫描（Charter §7）：ACTIVE vs FROZEN / FROZEN vs FROZEN / SCHEMA vs DECISION 无冲突 · supersession 恒 = 1 | 契约 §15 | **PASSED** |

## 12. TRACE — 指令节 ↔ 矩阵 100% 追溯

| TRACE | 指令节 | 矩阵行 |
|---|---|---|
| TRACE-01 | §0 Baseline / §1 Frozen Basis | SCOPE-01..05 · XD-01 · 契约 §1/§2.1 |
| TRACE-02 | §2 Canonical Scope | TRIG-01/04/07/10 · TRIG-15/16/17 |
| TRACE-03 | §3–§6 G/H/I/J 契约 | TRIG-01..12 · FUNC-01..04 |
| TRACE-04 | §7 Function Security | SEC-01..06 · FUNC-05 |
| TRACE-05 | §8 P10 Boundary | P10B-01..04 |
| TRACE-06 | §9 P12 Boundary | P12B-01..03 · MIG-08 |
| TRACE-07 | §10 P13 Boundary | P13B-01..02 · MIG-07 |
| TRACE-08 | §11 Migration Design | MIG-01..06 · DOWNG-01..02 · RT-01..02 |
| TRACE-09 | §12 Existing Protection | TRIG-13..17 · 契约 §2.3/§2.4/§9 |
| TRACE-10 | §13 P12 Handoff | P12B-02..03 |
| TRACE-11 | §14 Test Sync | TEST-01..05 |
| TRACE-12 | §15 Acceptance Matrix | 本矩阵全部组 |
| TRACE-13 | §16 Behavior Tests | TRIG-02/05/08/11/12 · REG-02 |
| TRACE-14 | §17 Zero-Unauthorized-Change | SCOPE-01..05 · GATE-01 |
| TRACE-15 | §18 Final Output | §13 汇总 + Final Gate 报告 |

## 13. 汇总（**脚本实测** · 实施轮复核 `p11_impl_acceptance.log`；TRACE 表不计状态）

| 分组 | 行数 | `PASSED` | `PLANNED` | `BLOCKED` |
|---|---|---|---|---|
| DOWNG | 2 | 2 | 0 | 0 |
| FUNC | 5 | 5 | 0 | 0 |
| GATE | 1 | 1 | 0 | 0 |
| MIG | 8 | 8 | 0 | 0 |
| P10B | 4 | 4 | 0 | 0 |
| P12B | 3 | 3 | 0 | 0 |
| P13B | 2 | 2 | 0 | 0 |
| REG | 3 | 3 | 0 | 0 |
| RT | 2 | 2 | 0 | 0 |
| SCOPE | 5 | 5 | 0 | 0 |
| SEC | 6 | 6 | 0 | 0 |
| TEST | 5 | 5 | 0 | 0 |
| TRIG | 18 | 18 | 0 | 0 |
| XD | 1 | 1 | 0 | 0 |
| **合计** | **65** | **65** | **0** | **0** |

## 14. IMPL — 实施结果（2026-09-26 · `p11_impl_acceptance.log`）

> 授权：`UAP P11 — IMPLEMENTATION AUTHORIZATION`（§0 `P11 IMPLEMENTATION = AUTHORIZED`）。
> 实施对象：`migrations_alembic/versions/0014_p11_triggers.py`（sha256 `3be9c8c092869c8d…`）。

| # | 检查 | 证据 | 结果 |
|---|---|---|---|
| IMPL-01 | revision 身份 / 单头 / 链长 | `down_revision = 0013_p10_event_audit` · head = `0014_p11_triggers` · 链长 **14** · `0015+` = 0 | **PASSED** |
| IMPL-02 | 既有 migration 逐字节未变 | `0010`/`0011`/`0012`/`0013` sha256 未变 | **PASSED** |
| IMPL-03 | 4 trigger 挂载 canonical 表 + tgtype 23/9/11/25 | `pg_get_triggerdef` 全量比对 | **PASSED** |
| IMPL-04 | 4 function · SECURITY INVOKER · 无 search_path · 全库 prosecdef = 0 | `pg_get_functiondef` | **PASSED** |
| IMPL-05 | 行为：G（valid×3 / missing×3 / 未注册 / group 双闸 / 非监听列不触发）· H（硬删清理 / 软删保留 / 仅 user 面）· I（引用拒 / 无引用过 / 与既有 roles DELETE 触发器兼容）· J（归档到期 / 非归档不动作 / 删除保留到期 / subject 零改 ⇒ J→G 递归无）· D-P11-05 不对称（role 归档 ACL 不动） | `test_p11_triggers.py` **27/27** | **PASSED** |
| IMPL-06 | 边界：L 不变 · events 0 trigger · P10 列 22/19 · P12 索引 0（`ix_rp_subject` 在位）· seed = 0 | harness #12–14 | **PASSED** |
| IMPL-07 | 降级零残留 + 往返对象集一致 | 8→0 · 物理表 35 · 快照 8=8 | **PASSED** |
| IMPL-08 | 计数终态 | 父级触发器 **39** · 全部 **40** · 函数 **21** | **PASSED** |
| IMPL-09 | Scope | 新文件 = 0014 + `test_p11_triggers.py` · 既有测试同步 **15 文件**（S1–S11 + 7 处回归修复）· PDL 内容删除行 = 1（顶部 Status，既有） | **PASSED** |

**测试**：全量回归 **623 passed / 0 failed / 6 skipped**（exit 0 · 34m57s）；基线 596 ⇒ 净增 **27**（全部为新 P11 套件），无回归。

**强制同步面（实施期实测 22 处编辑）**：head 断言 0013→0014（**26 处 / 15 文件**）· 链长 13→14 · AM5 父节点 → 0013 ·
pg6 触发器总数 36→40 · T-12 / TSEC4 / resource_acl absent→present 翻转（3 文件）· B14 精确集 ∪ G · P09_TRIGGERS ∪ J ·
BND1 → 所有权不相交不变式 · MIG2 钉在 0013 · T-19 / MIG1 head 常量 ·
**G/H 行为连带 4 处**：`zero_seed`（G 先于 FK ⇒ 异常型 IntegrityError→DBAPIError）· `b14_08`（伪造 subject → 真实 role）·
`acl_cascades`（伪造 subject → 真实 user）· `b14_09`（**H 与 granted_by SET NULL 的行为交互**：被删 actor/owner 不得任 subject ⇒ 引入第三 user 专职 subject）。

**证据（仓库外）**：`p11_impl_acceptance.log`（20/20 · exit 0）· `p11_impl_full_regression.log`（623/0/6）·
`p11_contract_gate.log`（契约轮 21/21）。

**状态**：`P11 = IMPLEMENTED / ACCEPTED` · `P12 = NOT AUTHORIZED` · `P13 = NOT AUTHORIZED` · `Runtime = NOT AUTHORIZED` ·
`commit / tag / push = NOT YET AUTHORIZED`。

**END OF P11 IMPLEMENTATION ACCEPTANCE MATRIX
