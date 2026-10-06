# UAP — P13 IMPLEMENTATION ACCEPTANCE MATRIX（**DRAFT · NOT FROZEN**）

> ## 状态
>
> ```text
> 轮次      = P13 IMPLEMENTATION PREP（READ-ONLY · DESIGN-CONTRACT ONLY）
> 矩阵状态  = **DRAFT v0 · NOT FROZEN**（BLOCKER B-1 未解除 ⇒ 不冻结）
> 配套契约  = P13_IMPLEMENTATION_CONTRACT.md（DRAFT v0）
> P13 IMPLEMENTATION = NOT AUTHORIZED · 0016+ = ABSENT · DDL/DML = 0 · Runtime = NOT AUTHORIZED
> ```
>
> **状态词表**：`PLANNED`（实施期须验证）· `BLOCKED`（存在阻断项，实施前必须解除）· `OPEN`（待 Human 确认）· `PASSED`（**仅指本轮只读核验通过**，非实施通过）。
>
> **记录格式**：每项含 `requirement / evidence source / test method / expected result / failure condition`。

---

## 1. I-01 … I-19 实施验收项

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **I-01** | migration 链完整且唯一：`0016_p13_seed` ← `0015_p12_indexes`，单头，filename == revision，`branch_labels/depends_on = None`，revision ≤ 32 字符 | 契约 §4 · `D-PLAT-09` | 静态读迁移头 + `alembic heads` / `history` | 单头 = `0016_p13_seed`；链长 16；`down_revision = 0015_p12_indexes` | 多头 / 链断 / filename ≠ revision / 0017+ 出现 | **PLANNED** |
| **I-02** | **clean DB** 上 upgrade 成功（从 0001 全链至 0016） | 契约 §12 | `reset_test_database()` → `upgrade(head)`；断言 `current_revision()` | exit 0；无未预期错误；种子对象按 §7 就位 | 任一 DDL/DML 报错 | **BLOCKED**（B-1） |
| **I-03** | **幂等**：upgrade 重复执行不产生重复行 / 不报未知错误 | 契约 §13 · R2 | 连续两次 `upgrade`；比对行数与自然键集合 | 行数不变；`WHERE NOT EXISTS` 生效；无静默 upsert | 重复行 / 静默跳过冲突 / 行数变化 | **PLANNED** |
| **I-04** | **clean DB** 上 downgrade 成功、零残留 | 契约 §15 | `downgrade(0015)` → 断言残留对象数 = 0 且表/行回到 0015 态 | 残留 = 0；物理表数回到 0015 值；行数回到基线 | 残留对象 / 行数不回退 | **PLANNED** |
| **I-05** | **FAIL-CLOSED**：存在任何超出 seed baseline 的行时 downgrade 必须 RAISE + 整体回滚 + **0 DELETE** | 契约 §15 · `D-P13-12` | 构造超出基线的行（计数/键集合偏离）→ 执行 downgrade → 断言异常 + 回滚后行数**未减少** | RAISE；事务回滚；受影响表行数不变；**无任何 DELETE 生效** | 静默执行 `DELETE WHERE key IN (...)` / 部分删除 / 误删 runtime 行 | **PLANNED** |
| **I-06** | `permissions` 行集**精确等于** §7 的 12 项（无多、无少、无改名） | 契约 §7 · `D-P13-01` | 集合比对：`key` 集合 == 12 项；逐行校验 `action/resource_type/is_system` | 恰好 12 行；`is_system = true`；无条件偏离 | 出现 `system.*` / `manage` / `write` / deny / 缺项 / 多项 | **PLANNED** |
| **I-07** | canonical action 强制生效（非法 action 被 DB 拒绝） | `ck_permissions_action_canonical` · `D-AUTH-05`/`D-AUTH-25` | 尝试插入非法 action（如 `manage`）→ 断言 DB 报错；并断言 CHECK 定义未被修改 | 非法 action 被拒；CHECK 文本与 0012 态**逐字一致** | CHECK 被放宽/移除/改写 | **PLANNED** |
| **I-08** | registry 白名单生效：`key ∉ {user, role, agent}` 被拒绝 | `ck_acl_subject_types_whitelist` | 插入非法 key → 断言 DB 报错；断言 CHECK 未被修改 | 非法 key 被拒；CHECK 未变 | 白名单被放宽 / 出现 `group` 等 | **PLANNED** |
| **I-09** | role ownership：`platform_admin` **未被重复播种**；P13 **零 roles 写入** | 契约 §10 · 0005 先例 · `D-P13-02` | 比对 upgrade 前后 `roles` 行数与 `uq_roles_platform` 命中；断言 P13 源码无 roles INSERT | `roles` 行数不变（= 1 @clean）；无 roles INSERT | 出现第二个 `platform_admin` / P13 写 roles | **PLANNED** |
| **I-10** | tenant / space 边界：P13 **零写入** | 契约 §11 · `D-P13-05` | 断言 `tenants = 0` ∧ `spaces = 0`；P13 源码无对应 INSERT | 均为 0；无 INSERT 语句 | 出现租户/空间行或相关 INSERT | **PLANNED** |
| **I-11** | membership 边界：`platform_memberships` / `tenant_memberships` / `memberships` **零写入** | 契约 §11 · `D-P13-07`/`08` | 断言三表均为 0 行；P13 源码无对应 INSERT | 三表皆 0；无 INSERT | 出现任何 membership 行 | **PLANNED** |
| **I-12** | **trigger interaction**：seed 在 **39 触发器全部启用**状态下执行；逐触发器行为验证；C2 保持启用且未被绕过 | 契约 §14 · `D-P13-11`/`03` | ① 断言 seed 期间无 `DISABLE/DROP/ALTER TRIGGER` 语句；② 逐触发器行为探针；③ 断言 C2 定义未变 | seed 成功 且 全部触发器保持启用；C2 定义与 0007 态**逐字一致** | 出现 DISABLE/ALTER/绕过；或 C2 被改 | **BLOCKED（B-1）** |
| **I-13** | **no credentials**：`identities` / `credentials` 零写入；无明文/可逆凭据 | 契约 §6 · `D-P13-13`/`06` | 断言两表 0 行；源码扫描无 password/secret 字面量 | 两表 0 行；无凭据字面量 | 出现任何凭据行或 secret 字面量 | **PLANNED** |
| **I-14** | **no demo Agent**：`agents` / `agent_versions` / `agent_permissions` / `tool_executions` 零写入 | 契约 §9 · `D-P13-04` | 断言四表 0 行；源码无对应 INSERT | 四表皆 0 | 出现 demo Agent 或相关行 | **PLANNED** |
| **I-15** | **no runtime mutation**：P13 不改任何既有 schema 对象（表/列/约束/索引/触发器/函数） | 契约 §5/§16 · `D-P13-14` | upgrade 前后对象快照哈希比对（经 `pg_*`）；断言新增对象集合 = ∅（除新增行） | 对象集不变（仅数据行新增） | 出现 CREATE/ALTER/DROP 新对象 | **PLANNED** |
| **I-16** | 历史迁移完整性：`0010–0015` sha256 **逐字节未变** | 契约 §1 | `sha256` 比对 6 个文件 | 全部前缀匹配（6d990723 / cdaf8383 / 5ecd1ef3 / da1bdffd / 3be9c8c0 / 94b0d228） | 任一文件被修改 | **PASSED**（本轮实测） |
| **I-17** | 全量回归不下降（基线 = 636 passed / 0 failed / 6 skipped） | 契约 §1 · 历史账本 | `pytest -q` 全量；断言 passed ≥ 636 且 failed = 0 | failed = 0；passed ≥ 基线 | 任一失败 / 数量下降 | **PLANNED** |
| **I-18** | scope guard：`0016+` 仅 1 文件；无越界文件；无 commit/tag/push | 契约 §19 · 指令 §17 | 文件清单比对 + `git status` + tag/remote 计数 | 新增 = `0016_p13_seed.py`（+ 测试）；HEAD/tags/remote 不变 | 越界文件 / 提交 / tag / push | **PLANNED** |
| **I-19** | worktree guard：既有未提交面（P10–P12 交付物 + 同步面）**不被回退或被误改** | 契约 §19 | 轮前快照 vs 轮后比对（mtime/内容），差集 ⊆ 本轮授权集 | 差集 = 本轮授权变更 | 出现授权集外的改动 / 回退既有变更 | **PLANNED** |

---

## 2. I-20 / I-21 — OPEN 项对应的验收（依赖 Human 确认）

| ID | Requirement | Evidence source | Test method | Expected result | Failure condition | 本轮状态 |
|---|---|---|---|---|---|---|
| **I-20** | 若 `IMPL-01` = 纳入：`users` **恰 1 行**无凭据主体记录（无 credentials/identities 联动），且其身份为契约规定的 canonical 种子身份 | 契约 §2.3/§17 `IMPL-01` · `D-PLAT-11①` + `D-P13-06` | 断言 `users` 行数 = 1 ∧ 无 identities/credentials 行 ∧ `deleted_at IS NULL` | 恰 1 行；无凭据 | 0 行（`D-PLAT-11①` 无从满足）或 >1 行 | **OPEN** |
| **I-21** | 若 `IMPL-02` = 采纳：`role_permissions` **恰 12 行**（`platform_admin` × §7 · effect = allow），无 deny 行 | 契约 §17 `IMPL-02` · `D-P13-01`/`D-P13-02` · R2 | 集合比对 `(role_id, permission_id, effect)` | 恰 12 行 allow；无 deny | 出现 deny 行 / 数量偏离 / 绑定其它角色 | **OPEN** |
| **I-22** | `IMPL-03` 裁决后：`audit_logs` 在 P13 中的写入行为与裁决一致 | 契约 §17 `IMPL-03` · 先例（迁移零 audit 写入） | 断言 `audit_logs` 行数变化 == 裁决预期 | 与裁决一致（建议 = 0 变化） | 与裁决不一致 | **OPEN** |
| **I-23** | `IMPL-04` 裁决后：downward 对 `users` 行的处理满足 FAIL-CLOSED（仅在精确条件下删除，否则 RAISE） | 契约 §15/§17 `IMPL-04` · `D-P13-12` | 构造 count ≠ 1 或身份偏离 → 断言 RAISE + 回滚 + 0 DELETE | RAISE；0 DELETE | 猜测式删除 / 误删 runtime 行 | **OPEN** |

---

## 3. 覆盖度（指令 §15 要求的 19 项）

```text
I-01 migration chain        ✓        I-11 membership boundary    ✓
I-02 upgrade clean DB       ✓        I-12 trigger interaction    ✓（BLOCKED）
I-03 upgrade idempotency    ✓        I-13 no credentials         ✓
I-04 downgrade clean DB     ✓        I-14 no demo Agent          ✓
I-05 downgrade fail-closed  ✓        I-15 no runtime mutation    ✓
I-06 permissions exact set  ✓        I-16 historical integrity   ✓
I-07 canonical action       ✓        I-17 full regression        ✓
I-08 registry whitelist     ✓        I-18 scope guard            ✓
I-09 role ownership         ✓        I-19 worktree guard         ✓
I-10 tenant/space boundary  ✓        （+I-20…I-23 = OPEN 项对应验收）
                          19 / 19 覆盖 · 五字段齐备
```

---

## 4. 汇总

| 分组 | 行数 | `PASSED`（本轮只读） | `PLANNED` | `BLOCKED` | `OPEN` |
|---|---|---|---|---|---|
| I-01…I-19 | 19 | 1 | 16 | 1 | 0 |
| I-20…I-23 | 4 | 0 | 0 | 0 | 4 |
| **合计** | **23** | **1** | **16** | **1** | **4** |

```text
唯一本轮 PASSED = I-16（历史迁移完整性，本轮只读实测）
唯一 BLOCKED    = I-12（trigger interaction）—— 由 **B-1** 导致
4 项 OPEN       = I-20/I-21/I-22/I-23 —— 分别依赖 IMPL-01 / IMPL-02 / IMPL-03 / IMPL-04 的 Human 裁决
```

---

**GATE 结论（2026-09-26 · P13 IMPLEMENTATION PREP）**

```text
P13 IMPLEMENTATION PREP = **BLOCKED**（B-1）
D-PLAT-11 RECONCILIATION = **PASS**（附 IMPL-01 派生项待确认）
Implementation Contract   = **DRAFT · NOT FROZEN**（19 节齐备；因 B-1 不冻结）
Acceptance Matrix         = **COMPLETE（DRAFT）**：19/19 覆盖 + 4 OPEN 项
trigger review            = **BLOCKED**
downgrade review          = PASS（设计满足 FAIL-CLOSED；IMPL-01 依赖项已登记）
0016+ = ABSENT · DDL/DML = 0（见契约 §19 偏差披露）· Runtime = NOT AUTHORIZED
P13 IMPLEMENTATION = **NOT AUTHORIZED**
⇒ 不创建 0016 · 不实施 · 等待 Human 解除 B-1 并（可选）裁定 IMPL-01…04
```

---

## 5. B-1 裁定同步（**append-only · 2026-09-26**）

> 本节为**追加登记**：**不**修改 §1–§4 正文；**不**改写任何冻结决策；**不**产生实施授权。
> §1 的状态列（`I-12 = BLOCKED（B-1）`）**保持原样** —— 该判定在本裁定后**仍然成立**（B-1 未解除，仅其**解除路径**被裁定）。

| 项 | 内容 |
|---|---|
| Human 裁定 | `O-1 = REJECT` · `O-4 = REJECT` · `O-3 = ACCEPT AS ARCHITECTURAL DIRECTION` · `O-2 = DEFERRED` |
| 决策载体 | `D-P13-15 — B-1 Amendment（Trust Boundary Precondition）` = `FROZEN`（附录 K） |
| 对本矩阵的影响 | **无状态变更**：`I-12` 仍为 `BLOCKED`（阻塞原因由「无候选」变为「前置未就绪 = `OPEN-P10-1`」） |
| 新增前置 | `OPEN-P10-1`（Database Trust Boundary Foundation）须先冻结；**编号归属待 `OQ-OP101-03`** |
| 新增验收面 | `OPEN_P10_1_ACCEPTANCE_MATRIX.md`（`IC` / `INV` / `R` / `T` / `S` / `D` / `GATE` / `TRACE`，共 52 行） |
| `I-16`（历史迁移完整性） | 保持 `PASSED`；`0010–0015` sha256 在 `OPEN-P10-1` PREP 轮**复验未变** |
| `I-17`（全量回归） | 保持 `PLANNED`（**本裁定轮未执行全量回归** —— 无代码变更，回归面为空） |
| `I-20`…`I-23`（`OPEN` × 4） | **保持 `OPEN`**：`B-1 FINAL DIRECTION` 轮**不**裁定 `IMPL-01`…`IMPL-04`（不在该轮授权面内） |

```text
本矩阵 §1–§4 = 未改写；§5 = 纯追加
§4 汇总（23 行：PASSED 1 · PLANNED 16 · BLOCKED 1 · OPEN 4）**保持有效**（时点快照）
0007 = unchanged · C2 = unchanged · 0016+ = ABSENT · DDL/DML = 0 · commit/tag/push = 0
supersession 新增 = 0
```

---

## 6. IMPLEMENTATION DECISION SYNC（append-only · 2026-09-27）

> 本节为追加：不改写 §1–§5 表格原文；被取代的具体单元格文案逐条列于 §6.5。
> 决策来源：Human Decision 2026-09-27 — IMPL-01 = A · IMPL-02 = A · IMPL-03 = A · IMPL-04 = C。
> 判定口径：本节条目均为可机械判定（给定实施结果即可判 PASS / FAIL），无需设计再解释。

### 6.1 Scope 判定

    SCOPE-N1  P13 schema objects = no new objects
              PASS 条件：实施前后相比，新建 table / index / constraint / trigger / function 数 = 0
              FAIL 条件：出现任何新 schema 对象

### 6.2 Seed 判定（精确计数）

    SEED-N1   acl_subject_types rows = 3，且 key 集合精确为 {user, role, agent}
              PASS：count = 3 且集合精确相等（无多、无少、无改名）
    SEED-N2   permissions rows = 12，且 key 集合精确等于 D-P13-01 的 12 项
              PASS：count = 12 且逐行 action ∈ canonical 12 verb ∧ is_system = true ∧ 无 deny
              FAIL：出现 system.* / manage / write / deny / 缺项 / 多项
    SEED-N3   role_permissions rows = 12，精确等于 platform_admin × D-P13-01 的 12 项 × effect=allow
              PASS：count = 12 且 role 恒为 platform_admin 且 effect 恒为 allow 且集合精确相等
              FAIL：出现其他 role / deny / 缺项 / 多项
    SEED-N4   users rows = 0
              PASS：users 表在 upgrade 全过程中零写入（含无凭据行也不允许）
    SEED-N5   audit_logs rows = 0
              PASS：audit_logs 表在 upgrade 全过程中零写入
    SEED-N6   roles rows = 1（未变），且为既有 platform_admin（0005 所有）
              PASS：count 未变且未新增任何 role 行
    SEED-N7   platform_memberships / tenants / spaces / tenant_memberships / memberships = 未变
    SEED-N8   agents / agent_versions / agent_permissions / tool_executions = 未变（4 表均为原值）

### 6.3 Downgrade 判定

    DOWNG-N1  migration-owned only
              PASS：降级仅移除 P13 本迁移创建的 registry 3 行 + permissions 12 行 + role_permissions 12 行
    DOWNG-N2  unknown ownership => fail
              PASS：存在任何超出 clean baseline 的行 / 无法解释的依赖行 / ownership 歧义时，
                    降级 RAISE 且整条事务回滚，受影响表行数未减少（0 DELETE）
              FAIL：静默删除 / 部分删除 / 误删非 seed 行
    DOWNG-N3  users untouched
              PASS：downgrade 全过程中不存在针对 users 的 DELETE（users 计数不变）
    DOWNG-N4  predicate = deterministic ∧ ownership-bound ∧ fail-closed
              PASS：判据可机械复核（自然键 + 精确 count + 依赖行检查），
                    不依赖时间戳 / 固定 UUID / 模糊匹配

### 6.4 Boundary 判定

    BOUND-N1  0016 unchanged
              PASS：0016_open_p10_1_trust_boundary.py sha256 保持
                    10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544
    BOUND-N2  CC-7 respected
              PASS：C2 函数定义未被改写（md5 保持 185e95be8bc4304edbcd3f4d5cda1eff），
                    runtime INSERT 仍被拒（错误文本逐字一致）
    BOUND-N3  runtime identity separated
              PASS：migration = uap_migrator 且 runtime = uap_app 且双向无 fallback 且
                    无新增 GRANT / 无角色属性变更 / 无 ownership 变更
    BOUND-N4  runtime identity 与 authorization subject 不混用
              PASS：未创建 users 行（SEED-N4）且未创建任何 membership（SEED-N7）

### 6.5 与 §1–§5 的取代关系（supersession 明细 · 不改写原文）

    M-1  §1 I-01 的 revision 文案「0016_p13_seed」⇒ 由 §6.6 取代为 0017_p13_seed
    M-2  §1 I-02 状态「BLOCKED（B-1）」⇒ 解除（§6.6；B-1 机制面已由 CC-7 打开）
    M-3  §2 I-20 / I-21（OPEN，依赖 Human 确认）⇒ 关闭（IMPL-01 = A 且 IMPL-02 = A）
    M-4  §1 中 users「0 或 1」相关判定 ⇒ 由 §6.2 SEED-N4 取代（= 0）
    M-5  §1 / §5 中与 C2「无条件拒绝 INSERT」相关表述 ⇒ 由 §6.6 取代（CC-7 受信迁移边界）
    M-6  §4 汇总表（23 行时点快照）保留有效为历史；现行汇总见 §6.7

### 6.6 Revision / C2 对账

    revision      = 0017_p13_seed
    down_revision = 0016_open_p10_1_trust_boundary
    单头          = 0017（P13 完成后）且 filename == revision 且 branch_labels / depends_on = None
    C2 判据       = CC-7 受信迁移边界：受信分支（current_user = session_user = uap_migrator）
                    放行 registry 写；runtime（uap_app）行为与 0007 pre-image 逐字一致

### 6.7 现行汇总

    判定行（现行）= SCOPE-N1 + SEED-N1…N8 + DOWNG-N1…N4 + BOUND-N1…N4 = 共 17 行
    状态：全部为 PLANNED（实施期判定）；BLOCKED = 0 且 OPEN = 0
    说明：§4 的 23 行时点快照（PASSED 1 · PLANNED 16 · BLOCKED 1 · OPEN 4）保留为历史记录，不删。

### 6.8 本节边界

    本节不产生实施授权。本轮：DDL = 0 · DML = 0 · migration execution = 0 ·
    0017 = ABSENT · commit/tag/push = 0。§1–§5 表格原文未改写；§6 = 纯追加。

---

**END OF P13 IMPLEMENTATION ACCEPTANCE MATRIX（DRAFT v0 · 2026-09-26 正文 · §6 追加于 2026-09-27 · NOT FROZEN · I-12 的 B-1 前置已解除，状态以 §6.5 M-2 为准）**
