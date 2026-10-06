# UAP — P13 B-1 HUMAN DECISION AMENDMENT

> ## 状态
>
> ```text
> 轮次        = P13 B-1 HUMAN DECISION AMENDMENT（READ-ONLY 可行性分析 → PROPOSED AMENDMENT）
> 文档状态    = **PROPOSED AMENDMENT · 未冻结 · 未批准**
> Gate 结果   = **B-1 AMENDMENT PREP = READY FOR HUMAN DECISION**
> 本轮未做    = 未创建 0016 · 未修改 0007 · 未修改 C2 · 未执行 migration · 未 seed · 未提交 · 未 DDL/DML
> P13 IMPLEMENTATION = **NOT AUTHORIZED**（保持）
> ```
>
> **本轮目标（单一）**：把 B-1 从「无法实施的冻结矛盾」收敛为**有明确安全边界、明确影响范围、可供 Human 正式冻结的最小架构变更**。
> **本轮不做**：不重新设计 P13；不裁定 `IMPL-01`…`IMPL-04`；不为 `D-PLAT-11` 的已通过对账翻案。

> ## ⛔ 决策更新（2026-09-26 · **append-only 指针** · 不改写本文件正文）
>
> ```text
> 本文件的 `PROPOSED AMENDMENT · 未冻结` 状态 = **2026-09-26 B-1 AMENDMENT PREP 时点快照**（历史）。
> Human 已就此下达正式裁定：`O-1 = REJECT` · `O-4 = REJECT` · `O-3 = ACCEPT AS ARCHITECTURAL DIRECTION` · `O-2 = DEFERRED`。
> 登记载体：`D-P13-15 — B-1 Amendment（Trust Boundary Precondition）`（`FROZEN`）+ 附录 **K**。
> 裁定全记录：`P13_B1_HUMAN_DECISION_FINAL_DIRECTION.md`。
> 后续：执行顺序调整为 `OPEN-P10-1 → P13 B-1 Amendment → P13 Implementation`
>       ⇒ 本文件的 §7 `A-1`…`A-5` **不得**视为已批准；`P13 IMPLEMENTATION` = **NOT AUTHORIZED**。
> 本文件 §1–§12 正文**保持原样**（历史证据），§13 为追加登记。
> ```

---


## 1. B-1 原始事实（本轮复验 · 只读）

```text
F-1  C2 `enforce_acl_subject_types_protect()` 对 INSERT **无条件 RAISE**（无豁免分支 / 无 GUC 判据 / 无角色白名单）
     —— 0007 创建（D-B14-12 = A）；函数属性实测：prosecdef = false · lang = plpgsql · owner = uap · proconfig = (none)
F-2  全仓**无任何迁移**插入 `acl_subject_types`（grep = 0）⇒ 设计所称 "migration-controlled path" **从未实现**
F-3  `acl_subject_types` @0015 实测 = **0 行**（registry 恒为空；`resource_permissions` 因此不可写）
F-4  同源设施 `enforce_roles_is_system_protect()`（0005）同样拒绝 `is_system = true` 的 roles INSERT
F-5  `D-P13-03` 要求 registry seed 走 migration-controlled path（不得绕过 C2）；`D-P13-04` 要求注册 `agent`
F-6  `D-P13-11` 禁止 DISABLE TRIGGER / ALTER TRIGGER / 绕过 C2 / **临时关闭保护后再恢复**
⇒ 结论：**真实 frozen-decision conflict**（非实现技巧问题）。**不得以"换一种写法"绕过。**
```

---

## 2. 冻结决策冲突链

```text
D-P13-04（必须注册 user / role / agent）
        ↓ 依赖
D-P13-03（registry seed 必须由 migration-controlled path 完成；C2 必须保持；不得绕过）
        ↓ 与……不可同时满足
D-P13-11（禁 DISABLE / 禁临时关闭后复原 / 禁 ALTER TRIGGER / 禁绕过 C2）
        ↓ 而
C2 事实（F-1/F-2）：插入 registry 的**唯一合法出口不存在**；保护触发器对一切 INSERT 抛错
        ⇒ **交集 = ∅** ⇒ B-1
```

---

## 3. 只读技术基线（**决定性事实**：当前不存在可强制执行的信任边界）

```text
B-1  迁移与运行时使用**同一数据库角色**：
       alembic.ini              sqlalchemy.url = postgresql+psycopg://uap:uap@localhost:5432/uap
       config/settings.py        DATABASE_URL   = postgresql+psycopg://uap:uap@localhost:5432/uap
       tests/integration/alembic_testkit.py  BASE_DSN = ...//uap:uap@localhost:5432/<test db>
     实测：current_user = uap · session_user = uap
B-2  该角色为**超级用户**：pg_roles 实测 `uap` → rolsuper = true · bypassrls = true · createdb = true
     ⇒ runtime 侧**具备**执行 `session_replication_role` / `ALTER TABLE … DISABLE TRIGGER` 的能力
       （**既有安全事实，登记为 `SEC-F1`**；本轮未执行任何此类动作）
B-3  `acl_subject_types` 的表权限：`uap` 持有 INSERT/UPDATE/DELETE/SELECT/TRUNCATE/TRIGGER/REFERENCES
     —— 权限层**不构成**额外边界（角色同时是 owner）
B-4  自定义 GUC **可被任意普通会话伪造**（本轮实测探针）：
       probe 1（未设置）        → NULL
       probe 2（普通会话 set_config('uap.probe_ctx','p13', true)）→ 读回 'p13'   ⇒ **无权限门槛，可伪造**
       probe 3（新会话）        → 空（事务级设置确实自动复原 ⇒ 可做"事务范围"，但**不提供信任**）
B-5  跨迁移函数替换先例 = **0**：22 个函数中**无任何**同名函数被两个迁移定义
     ⇒ 以 0016 改写 0007 所建 C2 函数体 = **新先例，需 Human 明确授权**
B-6  `D-P11-08`（FROZEN）：`SECURITY INVOKER` = canonical；**明确禁止** `SECURITY DEFINER`（除非新 Human Decision）
B-7  `OPEN-P10-1`（**显式 DEFERRED 开放项**）：「DB 角色体系 + `GRANT` 归属」；归属说明「**非 P10**；随角色体系立项统一裁定」；
     禁止「不得在 P10 单方面创造权限模型；**不得给应用运行时 DDL 权限**」
```

> **B-1 与 B-4 合读**：在当前信任模型（单角色 + 超级用户）下，**库内没有任何信号能区分"迁移"与"运行时"**。
> 这决定了后续所有候选机制的安全性上限。

---

## 4. 候选机制逐项分析（A–H · 只读 · **不选择**）

> 说明：**任何**"受控豁免"最终都必须**改写 C2 的判断逻辑**（因为 C2 无条件 RAISE）——改写本身不等于绕过，
> 其安全性**完全取决于所承载的受信信号**。故下表把「信号机制」与「载体（C2 改写）」分开评估。

### M-1 自定义 GUC / 会话变量

| 问 | 回答 |
|---|---|
| A 谁能触发 | 任意能建立连接的客户端（自定义 GUC **无权限门槛**） |
| B runtime 是否可能触发 | **是**（同一连接 `set_config` 即可）——实测 probe 2 |
| C 普通 SQL client 是否可伪造 | **是**（实测） |
| D migration 能否稳定使用 | 能（事务级 `SET LOCAL` 可自动复原） |
| E 是否需修改 0007 对象 | 需要（C2 必须新增判据分支） |
| F 是否改变 C2 runtime 保护边界 | **是** —— 判据可伪造 ⇒ C2 实质降级为"可选择性保护" |
| G downgrade 是否留下弱化 | 取决于是否复原 C2 原文本（漏复原 = 永久弱化） |
| H 八项测试可否证明 | **不能**证明"runtime impossible"（只能证明"未伪造时 DENY"） |
| 判定 | **不满足 §7** |

### M-2 数据库角色判据（`current_user` / `session_user`）

| 问 | 回答 |
|---|---|
| A 谁能触发 | 由连接所用角色决定（`SET ROLE` 需角色成员资格） |
| B runtime 是否可能触发 | **当前：是（B-1）** —— 迁移与 runtime 同角色 `uap`；若引入**独立受信角色**且 runtime 角色**非其成员**，则**否** |
| C 普通 SQL client 是否可伪造 | 同角色下**无法区分**；独立角色 + 严格非成员 + 最小 GRANT ⇒ **不可伪造** |
| D migration 能否稳定使用 | 能（迁移以受信角色连接执行） |
| E 是否需修改 0007 对象 | 需要（C2 新增 `current_user` 判据）；**且前置需解决 `OPEN-P10-1`**（B-7：角色体系为显式 DEFERRED 项） |
| F 是否改变 C2 runtime 保护边界 | 为**受信角色**开一个**最小例外**；runtime 角色仍无条件被阻断 ⇒ 边界**不削弱**（前提严格） |
| G downgrade 是否留下弱化 | 必须复原 C2 原函数**并**回收该角色/GRANT，否则留下持久例外主体 |
| H 八项测试可否证明 | **可全部证明**（见 §8 测试矩阵） |
| 判定 | **唯一能满足 §7 的机制族**；前置 = `OPEN-P10-1` 立项 |

### M-3 `SECURITY DEFINER` 函数

| 问 | 回答 |
|---|---|
| A 谁能触发 | 函数 owner（当前即 `uap`） |
| B runtime 是否可能触发 | **是**（同角色/同 owner） |
| C 是否可伪造 | 同 B |
| D migration 能否稳定使用 | **技术上无效**：C2 是 BEFORE ROW 触发器，**始终抛错**——**权限提升不能阻止触发器执行** ⇒ 该机制无法达成目标 |
| E 是否需修改 0007 对象 | 不改 C2（因无效果）；但需新建 DEFINER 函数 |
| F 是否改变 C2 边界 | 不变（因为无效果） |
| G downgrade 影响 | 需删除新函数 |
| H 八项测试 | **不通过**（ALLOW 无法达成） |
| 判定 | **技术无效** + `D-P11-08` **明文禁止** |

### M-4 C2 函数改写（载体 · 与 M-1/M-2 正交）

| 问 | 回答 |
|---|---|
| A 谁能触发 | 不适用（是载体） |
| B runtime 影响 | 取决于所承载信号 |
| C 伪造 | 取决于所承载信号 |
| D migration 可用 | 可用（`CREATE OR REPLACE FUNCTION`） |
| E 是否需修改 0007 对象 | **是** —— 覆盖 0007 所建函数体；**先例 = 0（B-5）** ⇒ 新先例，须 Human 明确授权 |
| F 是否改变边界 | 取决于信号（M-2 ⇒ 不削弱；M-1 ⇒ 削弱） |
| G downgrade | **必须**在 0016 downgrade 中**复原 C2 原函数文本** |
| H 八项测试 | 取决于信号 |
| 判定 | **必需载体**；安全性由信号决定 |

### M-5 触发器状态控制（`DISABLE TRIGGER` / `session_replication_role` / `ALTER TRIGGER`）

```text
⇒ 已被 **D-P13-11 明文禁止**（含"临时关闭保护后再恢复"）；`session_replication_role` 另需超级用户
  —— 而 B-2 显示 runtime 角色**恰好具备**该能力，这本身是既有安全事实 `SEC-F1`。
⇒ **不评估为实现路径**（禁止），仅登记。
```

### M-6 路径迁移（由部署期 CLI / runtime 插入，P13 迁移不写 registry）

| 问 | 回答 |
|---|---|
| A 谁能触发 | 部署期受信 CLI（R4 称「独立凭据」） |
| B runtime 是否可能触发 | 若 CLI 与 runtime **同角色** ⇒ 是；独立角色 ⇒ 否 |
| C 是否可伪造 | 同 B |
| D migration 可用 | 不适用（不由迁移执行） |
| E 是否需修改 0007 对象 | **是** —— C2 仍阻断**一切** INSERT，路径改变不解决触发器问题 |
| F 是否改变边界 | 同 M-2 的严格前提 |
| G downgrade | 行由部署期建立 ⇒ P13 迁移**不持有其创建事实**，与 `D-P13-12` FAIL-CLOSED 的所有权证明直接交互 |
| H 八项测试 | 依赖角色分离 |
| 判定 | 与 M-2 **同源**；额外需**重述 `D-P13-03`** 的 "migration-controlled path" |

### M-7 新增 schema 对象（switch / marker 表）

```text
⇒ 需 `CREATE`（冻结未授权）· 仍不足以单独提供信任（仍需 C2 判据）· 触及 D-P13-14「不新增 schema marker」
⇒ 不满足
```

---

## 5. O-1 … O-4 正式候选（**全部保留 · 均未批准**）

| 编号 | 方案 | 实质 | 与既有冻结的关系 |
|---|---|---|---|
| **O-1** | 受控 DISABLE 授权 | 迁移内 `DISABLE TRIGGER → INSERT → ENABLE`（同事务） | **与 `D-P13-11` 直接冲突**（明文禁止"临时关闭后再恢复"）⇒ 必须 amend `D-P13-11` |
| **O-2** | C2 受控豁免 | 改写 C2，为**受信 migration/deployment context**开最小例外；runtime 语义逐字不变 | 需 amend 链：`D-P13-03` 保持核心目标 · `D-P13-11` 保持核心原则 · 需 Human 批准 **新先例 M-4** · 前置 `OPEN-P10-1` |
| **O-3** | 移交部署期受信路径 | registry 三行由部署期受信步骤建立；P13 仅校验存在 | 需**重述 `D-P13-03`** 的 migration-controlled path；C2 仍需豁免（同 O-2 前置） |
| **O-4** | 承认 registry 保持空 | 不建立 registry 行 | 影响 `D-P13-04` 与 `D-PLAT-11` 影响面（`resource_permissions` 在 P13 后仍不可写）⇒ 需重述 |

**每题的安全边界 / 影响（O-1～O-4）**

| 维度 | O-1 | O-2 | O-3 | O-4 |
|---|---|---|---|---|
| 对 0007 既有 C2 的影响 | 不改函数，但**运行时状态被临时改变** | **改写函数体**（覆盖 0007 对象；新先例） | 同 O-2（C2 必须豁免） | 不变 |
| 对 `D-P13-03` 的影响 | 冲突（须 amend） | 保持核心目标，需定义"受信 context" | **重述** path 定义 | 保持，但目标不可达 |
| 对 `D-P13-11` 的影响 | 直接冲突（须 amend） | 保持核心原则；"受信 context ≠ 绕过"须逐字界定 | 同 O-2 | 不冲突 |
| 对 runtime protection 的影响 | **窗口期内全局弱化**（任何并发会话均可写 registry） | runtime 路径**逐字不变**（前提：M-2 严格前提） | 同 O-2 | 不变 |
| downgrade 影响 | 无须回收 | **必须**复原 C2 原文本 + 回收角色/GRANT | 同 O-2 + 行所有权证明问题（`D-P13-12`） | 不变 |
| 前置条件 | Human amend `D-P13-11` | **`OPEN-P10-1` 立项（角色分离）** + 批准新先例 | 同 O-2 + 重述 `D-P13-03` | Human 重述 |
| 本轮判定 | 与冻结直接冲突 | **技术上可满足 §7，但前置未就绪** | 同 O-2 | 需重述 |

---

## 6. §7 准则对照（**分析结论 · 非选择**）

| 机制 | migration-only | least privilege | runtime impossible | auditable | transaction-scoped | 不永久削弱 C2 | 无需 DISABLE | 不用 replication_role | downgrade 后 C2 完整 |
|---|---|---|---|---|---|---|---|---|---|
| M-1 GUC | ✓ | ✓ | **✗** | ✗ | ✓ | 条件性 | ✓ | ✓ | 条件性 |
| **M-2 角色** | ✓ | ✓（最小 GRANT） | **✓（需 `OPEN-P10-1`）** | ✓ | ✓ | ✓ | ✓ | ✓ | 需回收 |
| M-3 DEFINER | — | ✗ | ✗ | — | — | — | — | — | — |
| M-4 改写（载体） | 载体 | 载体 | 取决于信号 | ✓ | ✓ | ✓ | ✓ | ✓ | 必须复原 |
| M-5 状态控制 | ✗（被禁） | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| M-6 路径迁移 | ✗ | ✓ | 条件性 | ✓ | ✓ | ✓ | ✓ | ✓ | 条件性 |
| M-7 新对象 | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | — |

**分析结论（**非**机制选择）**

```text
① 在**现有**信任模型（单角色 + 超级用户，B-1/B-2）下，**没有任何机制**能满足 §7 的
   「runtime impossible」与「不形成 runtime authorization bypass」——因为库内无法区分调用者。
② 唯一可满足全部准则的**机制族** = 「可强制执行的调用者身份分离」（M-2 / M-6 + M-4 载体），
   其**前置条件**是解决 `OPEN-P10-1`（DB 角色体系 + GRANT 归属）——该角色体系为**显式 DEFERRED 项**，
   且既有冻结明文「不得给应用运行时 DDL 权限」。
③ 因此：**O-2 在当前授权范围内不可落地**（不是不可行，而是**前置未就绪**）；
   按指令 §7「若 O-2 无法满足则继续评估 O-3」——O-3 与 O-2 **同源同前置**（C2 仍需豁免；
   额外需重述 `D-P13-03` 的 path 定义）。
④ **具体采用哪一族中的哪一种实现，以及是否先立项解决 `OPEN-P10-1`，属 Human 决策 —— 本文件不代选。**
```

---

## 7. PROPOSED AMENDMENT（最小架构变更 · 供 Human 冻结）

> **性质**：**提案**，非批准。为避免超范围，以下仅描述**若采用 O-2 所需的最小变更边界**；是否采用由 Human 决定。

```text
A-1（前置 · 独立立项）解决 `OPEN-P10-1` 的最小切片：
      · 为 registry seed 引入**专用受信角色**（migration/deployment identity）
      · runtime 应用角色**不得**为该角色成员（禁止 `SET ROLE` 伪造）
      · 最小 GRANT：受信角色对 `acl_subject_types` 仅 INSERT（不改 C2 之外的表权限）
      · 遵守既有约束「不得给应用运行时 DDL 权限」
A-2（受限改动面）以 `0016` 改写 C2 函数体（`CREATE OR REPLACE FUNCTION`，覆盖 0007 对象）：
      · 新增**唯一**分支：当调用者 = A-1 的受信角色 **且** `TG_OP='INSERT'` 时放行
      · 其余分支（DELETE / key 变更 / 其他一切 INSERT）**逐字不变**，错误消息保持一致
      · **不得**引入 `SECURITY DEFINER`（`D-P11-08`）；**不得**使用 GUC / 会话变量 / `session_replication_role`
A-3（复原义务）`0016` 的 downgrade **必须**：复原 C2 原函数文本 → 回收 A-1 的角色/GRANT
      · 否则视为「永久弱化 C2」，违反 §7 的「downgrade 后 C2 仍完整有效」
A-4（新先例授权）Human 须明确批准：**跨迁移函数替换**（当前先例 = 0，B-5）
A-5（审计与可证性）实施期必须提供 §8 的八项测试证据链；**不得**以"未伪造时 DENY"替代"runtime impossible"
```

**八项可证性测试（A-5 的验收形式 · 实施期执行）**

```text
① ordinary runtime INSERT            → DENY（错误消息与 0007 原版逐字一致）
② ordinary SQL client INSERT         → DENY
③ 伪造尝试（set_config / SET ROLE / 伪装 application_name）→ DENY
④ trusted migration seed INSERT      → ALLOW（仅 registry 三行）
⑤ 迁移事务结束 → protection restored（同会话连续 insert 被拒）
⑥ 后续 runtime INSERT                → DENY
⑦ downgrade 后 C2 定义 = 0007 原文本（逐字）
⑧ downgrade 后 ②/③/⑥ 仍为 DENY
```

---

## 8. amendment / supersession 链（§9 要求 · **不删除任何原决策**）

```text
若采用 O-2（或 O-3）：
  D-P13-03（原文：migration-controlled path）
      ↓ **保持核心目标**：registry seed 必须由受信 migration/deployment path 完成
      ↓ 需新增/补注：受信 context 的定义（引用 A-1）
  D-P13-11（原文：不得 DISABLE TRIGGER / 临时关闭 / ALTER TRIGGER / 绕过 C2）
      ↓ **保持核心安全原则**：不得削弱或临时移除保护
      ↓ 需逐字界定：**「允许受信 migration context」≠「允许绕过 C2」**（见 §9）
  ⇒ 建议载体：新增 `D-P13-15`（B-1 amendment）+ 在 `D-P13-03`/`D-P13-11` 加**指针式补注**（append-only）
  ⇒ **禁止**：删除原决策 · 静默改写 · 以"技术上更常见"为由自动采用

若采用 O-1：需 amend `D-P13-11`（移除"临时关闭"禁令）—— 与 §7 准则冲突，须 Human 明确知悉该冲突。
若采用 O-4：需重述 `D-P13-04` 与 `D-PLAT-11` 影响面（P13 后 ACL 仍不可用）。
```

---

## 9. 语义区分（**必须逐字成立**）

```text
「允许受信 migration context」= C2 的判据集合中新增一个**不可伪造**的受信主体；
                            runtime 路径的判定结果**逐字不变**（仍无条件 RAISE 同一错误）；
                            该主体仅用于 registry seed，无其他放行面。

「允许绕过 C2」            = 在 runtime 或任意路径上降低/移除/临时关闭 C2 的阻断能力
                            （DISABLE、session_replication_role、可伪造的判据、functions 替换成空判据）。

判别法（可机读）：runtime INSERT 是否**仍然**得到与 0007 原版**逐字相同**的拒绝消息，
                 且伪造尝试（GUC / SET ROLE / application_name）是否**仍然**被拒。
                 任一不成立 ⇒ 属"绕过"，不属"受信 context"。
```

---

## 10. `IMPL-01` … `IMPL-04` 状态（**本轮未变**）

```text
IMPL-01  P13 是否 INSERT 1 行无凭据 `users`（首个主体记录）   = REQUIRED-DERIVED · 待 Human 确认
IMPL-02  `role_permissions` 绑定集合（platform_admin × 12 allow）= 派生 · 待 Human 确认
IMPL-03  P13 是否写 `audit_logs`（先例 = 迁移零 audit 写入）    = OPEN
IMPL-04  `users` 行的降级移除依据（依 `D-P13-12` FAIL-CLOSED）  = 依赖 IMPL-01
⇒ 本轮**不**裁定、**不**污染 B-1 amendment。
```

---

## 11. Gate 检查（指令 §11 · 逐项）

| 检查项 | 结果 |
|---|---|
| frozen decision conflict = identified | ✅ §1/§2（F-1…F-6 + 交集 = ∅） |
| O-1～O-4 = documented | ✅ §5（四项全保留，均未批准） |
| C2 security boundary = reviewed | ✅ §3/§4（函数属性实测 · 无条件 RAISE · 判据可伪造性） |
| runtime bypass = reviewed | ✅ §4 M-1/M-5 + §9（含"绕过"判别法） |
| migration trust boundary = reviewed | ✅ §3 B-1/B-2/B-4（**单角色 + 超级用户 ⇒ 无信任边界**） |
| downgrade = reviewed | ✅ §4 G 行 + §7 A-3 + §8 测试⑦⑧ |
| predecessor impact = reviewed | ✅ B-5（跨迁移函数替换先例 = 0）· B-6（`D-P11-08`）· B-7（`OPEN-P10-1`） |
| 0007 impact = identified | ✅ §5 第 1 行（须改写 0007 所建对象） |
| P13 scope impact = identified | ✅ §7 A-1（前置立项）· §10（IMPL 不扩张） |
| `D-P13-03` impact = identified | ✅ §5 第 2 行 + §8 |
| `D-P13-11` impact = identified | ✅ §5 第 3 行 + §8 + §9 |

```text
B-1 AMENDMENT PREP = **READY FOR HUMAN DECISION**
（不得输出 IMPLEMENTATION PASS）
```

---

## 12. 本轮边界与自证偏差

```text
0016_p13_seed.py = ABSENT · 0016+ = ABSENT · DDL = 0 · DML = 0 · seed INSERT = 0
runtime mutation = 0 · 0007 modification = 0 · commit = 0 · tag = 0 · push = 0
P13 IMPLEMENTATION = NOT AUTHORIZED

自证偏差（如实披露）：
 ① 本轮为取得 B-1/B-4 证据，在**一次性测试库**执行了只读查询 + **一次事务本地 `set_config` 探针**
    （`is_local = true` ⇒ 事务结束自动失效；新会话复验为未设置 ⇒ 无持久影响；非 DDL/DML）。
 ② 上一轮已披露的 `reset_test_database()` + `alembic upgrade head` 偏差**沿用于本轮基线**（当时已披露）。
 ③ 本轮**未**执行 `session_replication_role` / `DISABLE TRIGGER` 等任何会改变触发器状态的语句
    （仅在 §3 B-2 登记"该角色具备此能力"这一既有事实 `SEC-F1`）。
```

---

---

## 13. FINAL DIRECTION 登记（**append-only · 2026-09-26**）

> 本节为**追加登记**：**不**修改 §1–§12 正文；**不**改写任何 `D-*` 决策；**不**产生实施授权。

### 13.1 Human 裁定（逐字）

```text
O-1 = REJECT
O-4 = REJECT
O-3 = ACCEPT AS ARCHITECTURAL DIRECTION
O-2 = DEFERRED
```

### 13.2 与本文件 §8「amendment / supersession 链」的对应

| 本文件 §8 预设（`若采用 …`） | Human 裁定 | 落地后果 |
|---|---|---|
| 若采用 `O-2` ⇒ 需 amend `D-P13-03` / `D-P13-11` + 新先例 `M-4` | **`O-2` = DEFERRED** | `D-P13-03` / `D-P13-11` **本轮未 amend、未改写**；`M-4` 新先例**未批准** |
| 若采用 `O-1` ⇒ 需 amend `D-P13-11` 移除"临时关闭"禁令 | **`O-1` = REJECT** | `D-P13-11` **原样保留**（禁令未被移除） |
| （`O-3` 与 `O-2` 同源同前置） | **`O-3` = ACCEPT AS ARCHITECTURAL DIRECTION** | 方向被接受；其**前置 = `OPEN-P10-1`（数据库身份隔离）** |
| 若采用 `O-4` ⇒ 需重述 `D-P13-04` 与 `D-PLAT-11` 影响面 | **`O-4` = REJECT** | 不作任何重述；registry 注册要求**保持有效** |

### 13.3 本文件 §6「分析结论」的现行效力

```text
§6 ① 在现有信任模型下无任何机制满足 §7「runtime impossible」        —— **仍成立**（实测复验 FD-1…FD-7）
§6 ② 唯一可满足准则的机制族 = 可强制执行的调用者身份分离（M-2/M-6 + M-4 载体）—— **仍成立**
§6 ③ `O-2`「不可落地 = 前置未就绪（≠ 不可行）」                    —— **被 Human 采纳**（O-2 = DEFERRED，非 REJECT）
§6 ④ 「属 Human 决策 —— 本文件不代选」                              —— **已完成**（Human 已裁定 O-1…O-4）
```

### 13.4 本文件 §7 `A-1`…`A-5` 的状态（**未批准**）

```text
A-1（前置立项 OPEN-P10-1）      = **已被采纳为方向**（Human §3 执行顺序 + §4 目标）
A-2（0016 改写 C2 函数体）      = **未批准**（`O-2` = DEFERRED；不授权 C2 修改）
A-3（复原义务）                 = 未批准（属将来实施契约的内容）
A-4（新先例：跨迁移函数替换）    = **未批准**（先例 = 0 保持）
A-5（八项可证性测试）           = 未批准（将于 `OPEN-P10-1` 冻结/实施期形式化）
```

### 13.5 下游

```text
D-P13-15 = FROZEN（B-1 Amendment · Trust Boundary Precondition）
下一阶段  = OPEN-P10-1 PREP（Database Trust Boundary Design · 只读设计）
          ⇒ 交付物：OPEN_P10_1_PREP_REPORT.md · OPEN_P10_1_DECISION_RESOLUTION.md · OPEN_P10_1_ACCEPTANCE_MATRIX.md
P13 IMPLEMENTATION = **NOT AUTHORIZED**（保持）
```

### 13.6 本节边界

```text
本文件 §1–§12 = 未改写（逐行未变）；§13 = 纯追加
0007 = unchanged · C2 = unchanged · 0016+ = ABSENT · DDL/DML = 0 · commit/tag/push = 0
supersession 新增 = 0 · 未 supersede / 未改写任何 D-* 决策正文
```

---

## 14. CANONICAL TRUST-BOUNDARY STATEMENT（**append-only · 2026-09-27 · Human Decision 登记**）

> 本节为**追加**：不改写 §1–§13 任何一行；**不删除任何历史证据**；不 supersede 任何 `D-*` 正文。
> 来源：Human 于 2026-09-27 完成 P13 Implementation Clarification 裁决，并下达
> 「P13 Contract Amendment & Implementation Readiness Gate」指令 §9。

### 14.1 Canonical Statement（**现行实施依据**）

```text
CC-7 provides the trusted migration execution boundary.

uap_migrator         : migration identity
uap_app              : runtime identity
authorization subject: independent model concept
                       （ACL subject = acl_subject_types 注册条目：user / role / agent）

migration trust  !=  user identity
```

### 14.2 `D-P13-03`「受信主体」的形式化（派生自已冻结决策 · 非新决策）

```text
「受信主体」= 受信迁移身份：current_user = session_user = uap_migrator
              （连接期持续实测断言；env.py `_assert_effective_role` FAIL-CLOSED）
该身份经 C2 的 CC-7 判据分支获得 registry 写入放行；
runtime（uap_app）路径行为与 0007 pre-image 逐字保持一致（INSERT denied）。

C2 post-image：md5(pg_get_functiondef) = 185e95be8bc4304edbcd3f4d5cda1eff
签名不变：() RETURNS trigger · pronargs = 0 · LANGUAGE plpgsql · prosecdef = false
```

### 14.3 old statement → supersession 登记（保留历史 · 不作现行依据）

```text
old statement（仅作历史依据 · 不再是当前实施依据）
  「C2 对 INSERT 无条件 RAISE，无任何豁免分支 / 无 GUC 判据 / 无角色白名单」
  「registry 在冻结集合内无合法机制」（BLOCKER B-1）
  位置：§1 F-1 · §2 · §3 · §6（记录的是 0007 原始函数体与 FROZEN 时点基线）

classification = SUPERSEDED（作为实施依据）
superseded by  = D-P13-15（B-1 Amendment · FROZEN · PDL 附录 K）
                 + D-OP101-05（C2 判据形态 = CUSTOM DECISION = CP-F / CC-7 · FROZEN）
                 + BATCH-C 执行面（CF-C-5 = B：窗口期 GRANT → verify → REVOKE）

保留原则：§1–§13 的历史事实陈述不删除、不改写（其记录缺陷发现时点的真实基线）；
          但其不得再作为当前实施依据引用。
```

### 14.4 依赖文档同步

```text
P13_IMPLEMENTATION_CONTRACT.md               → §21（实施决策 + C2 判据对账 · append-only）
P13_IMPLEMENTATION_ACCEPTANCE_MATRIX.md      → §6（实施决策同步 · append-only）
P13_IMPLEMENTATION_READINESS_GATE_REPORT.md  → 本轮 Gate 报告（新增）
```

### 14.5 本节边界

```text
本节不产生实施授权。P13 IMPLEMENTATION = NOT AUTHORIZED（保持）。
本轮：DDL = 0 · DML = 0 · migration = 0 · 0017 = ABSENT · commit/tag/push = 0
§1–§13 逐行未变；§14 = 纯追加。
```

---

**END OF P13 B-1 HUMAN DECISION AMENDMENT（2026-09-26 · §14 追加于 2026-09-27 · Gate = `HUMAN DECISION = REGISTERED（B-1 Amendment）` · `P13 IMPLEMENTATION = NOT AUTHORIZED`）**
