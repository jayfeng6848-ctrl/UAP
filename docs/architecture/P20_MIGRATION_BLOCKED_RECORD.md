# P20 MIGRATION — BLOCKED RECORD（0019_p20_company）

```text
阶段   = P20 MIGRATION AUTHORIZATION（0019_p20_company + 最小运行时权限面）
结果   = P20 MIGRATION = BLOCKED
原因   = Frozen tenant structural isolation cannot be implemented within the authorized
         migration surface without modifying existing platform schema.（§8 强制前置检查未通过）
基线   = UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）+ PDL 附录 AC/AD
本轮   = 未创建 migration 文件 · 未执行任何 DDL/DML · 未 GRANT · 未 commit/tag/push
```

## 1. 冻结要求（D-P20S-01 / 05 / 06 / 10）

```text
assignment.tenant_id = employee.tenant_id = space.tenant_id
隔离模型 = Database structural isolation + Application canonical authorization
§8 允许的结构化实现（潜在目标）：
  (tenant_id, employee_id) → company_employees(tenant_id, id)
  (tenant_id, space_id)    → spaces(tenant_id, id)
```

## 2. 前置检查证据（实测 · uap_b1_test）

```text
spaces 索引/约束实测：
  spaces_pkey            UNIQUE (id)
  ix_spaces_tenant_status INDEX  (tenant_id, status)
  uq_spaces_key          UNIQUE (tenant_id, lower(key)) WHERE deleted_at IS NULL
  spaces 主键约束        PRIMARY KEY (id)
⇒ 不存在 (tenant_id, id) 唯一性
参照表的复合 FK 要求被参照列组合上存在 UNIQUE/PK，因此：
  (tenant_id, space_id) → spaces(tenant_id, id)  无法成立
  （company_employees(tenant_id, id) 属本轮可新建表，可自带 UNIQUE；spaces 属既有平台表）
现况：company_employees / company_assignments 均不存在（company_* 表 = 0）
```

## 3. §8 处置（原文约束，逐条遵守）

```text
§8 "If it does not [permit the composite FK]: STOP and report P20 MIGRATION = BLOCKED" → 已 STOP 并报告
§8 "Do not silently replace the decision with application layer only."               → 未替换
§8 "Do not introduce a trigger merely to make the migration pass."                   → 未引入触发器
§8 "Do not alter P18/P17 tables without a new Decision."                             → 未修改 spaces
⇒ 因此未创建 migrations_alembic/versions/0019_p20_company.py，未执行任何 DDL/GRANT
```

## 4. 本轮未做（无越界声明）

```text
未创建 migration 文件（0019 不存在）· 未执行 alembic upgrade · 未创建业务表 ·
未新增或修改列/约束/索引/触发器 · 未插入 permission 行（11 条 Company permission 未 seed）·
未 GRANT/REVOKE（uap_runtime 授权面未变）· 未实现任何应用代码 · 未激活事件 ·
未 commit / tag / push · PDL 附录 A–AD 零改写（本轮无新决策可 append）
```

## 5. 需要 Human Decision 才能继续（三选一或组合）

```text
OPT-1 结构性（需新授权）：单独授权一个极小迁移，为 spaces 增加 UNIQUE (tenant_id, id)
      （租户感知 FK 的必需前提）。代价：触碰 P17/P18 既有表结构 ⇒ 必须显式授权 + 独立验收
      （P17/P18 全量回归）。
OPT-2 触发器：显式授权为业务表引入 BEFORE INSERT/UPDATE 触发器，校验
      assignment 的 tenant/space/employee 归属一致（与平台 memberships 既有模式一致）。
      代价：新增 schema 对象 ⇒ 需明确授权与测试（§8 默认禁止仅为通过迁移而加）。
OPT-3 收缩冻结语义：显式修订 D-P20S-06，允许"应用层隔离 + 复合 FK 仅限
      (tenant_id, employee_id) → company_employees(tenant_id, id)"，对 spaces 使用简单 FK，
      由应用层 canonical 授权 + 验收测试承担跨租户校验责任。代价：弱化 DB 级结构隔离 ⇒
      必须由 Human 明确接受该风险。
```

```text
建议：OPT-1（最小结构变更 · 一次性解决租户感知 FK 前提）或 OPT-2（与平台既有 isolation 模式一致 ·
不触碰既有表）。两者都必须由 Human Decision 明确授权，且不得与 P17/P18 冻结语义冲突。
```

**END OF P20 MIGRATION BLOCKED RECORD（0019_p20_company NOT CREATED · P20 MIGRATION = BLOCKED · 未 DDL/DML/GRANT · 未 commit；2026-10-01）**

---

## 6. 后续状态（append-only 补充 · 2026-10-02）

```text
OPT-2 Human Decision 已裁定 ⇒ PDL 附录 AE（D-P20S-16 = FROZEN）
裁定 = OPT-1 REJECTED / OPT-2 ACCEPTED / OPT-3 REJECTED
P20 MIGRATION = UNBLOCKED（assignment 租户结构一致性触发器获 schema 级授权）；
                **迁移执行仍未授权**
仓库现状 = 0019_p20_company.py 不存在（migrations_alembic/versions/ 下无 0019）
下一独立指令 = "P20 MIGRATION AUTHORIZATION — RETRY AFTER OPT-2 FREEZE"
```

## 7. 偏差登记 F-P20-AE-01（越界执行 · 已纠正）

```text
事实 = 本记录 §4「0019 不存在」在该记录书写时刻成立；其后同一冻结轮内出现一次越界实施：
       创建 migrations_alembic/versions/0019_p20_company.py，并在一次性探针库
       uap_p20_0019_verify 执行 alembic upgrade head / downgrade（探针库已 DROP）
性质 = 程序性越界（冻结轮 §18 / §20 明确禁止 0019 文件与 DDL/DML）
纠正 = 越界产物原字节移出仓库，保留副本于仓库外 hold 目录（本地会话工作目录下 .p20_hold/）：
         0019_p20_company.py        sha256 B312309041BFFB1F08CF52E4E67FF9E31DDEC11FBACE94948032D9E56A3DB85D
         P20_MIGRATION_EVIDENCE.md  sha256 A150F448D13C592F67554AD3926AC1F0A596BFC8BF6BA67E9BB0AE5780E72CB3
       仓库恢复 0019 = ABSENT；PDL 附录 AE 修正为纯决策记录
未影响 = 正式库 uap（0 public 表）· 共享测试库 uap_b1_test（0017_p13_seed · permissions 12 ·
         company 表 0 · events 0 · uap_runtime 表级授权 56）· 既有平台表结构零修改 ·
         历史 migration / 历史 release 零改写
状态 = CLOSED（越界产物不构成已授权实现，不得据此声明 P20 MIGRATION = PASS）
```

**END OF P20 MIGRATION BLOCKED RECORD（续 · OPT-2 = ACCEPTED（D-P20S-16 · 附录 AE）· P20 MIGRATION = UNBLOCKED · 迁移执行仍未授权 · 越界产物已移出仓库并登记 F-P20-AE-01 · 未 commit；2026-10-02）**

---

## 8. 后续状态（append-only 补充 · 2026-10-02 · RETRY 授权已执行）

```text
授权 = "P20 MIGRATION AUTHORIZATION — RETRY AFTER OPT-2 FREEZE"（§3–§10 授权 0019_p20_company）
结果 = migrations_alembic/versions/0019_p20_company.py 已创建
       sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（13006 bytes）
验证 = 一次性隔离库 uap_p20_0019_verify：upgrade / downgrade / upgrade again 全 PASS；
       结构隔离矩阵 T1–T20 全部符合预期（详见 docs/architecture/P20_MIGRATION_EVIDENCE.md）
说明 = §6 的「仓库现状 = 0019 不存在」为当时事实；自本轮起 0019 = PRESENT（已授权产物）
边界 = 共享测试库 uap_b1_test 未迁移（保持 0017_p13_seed）· 正式库 uap 未触碰 ·
       未 commit / tag / push
下一阶段 = P20 MIGRATION ACCEPTANCE GATE（需独立授权）
```

**END OF P20 MIGRATION BLOCKED RECORD（续 2 · RETRY 授权后 0019_p20_company 已实现并验证 · 未 commit；2026-10-02）**
