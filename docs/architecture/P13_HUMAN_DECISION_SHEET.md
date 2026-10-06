# UAP — P13 HUMAN DECISION SHEET（逐项裁定请求 · 尚未冻结）

> ## 本轮性质与边界
>
> ```text
> 轮次       = P13 Human Decision Completion Round（Decision Resolution / Human Decision Gate）
> 性质       = READ / ANALYZE / PRESENT EVIDENCE ONLY —— 本文件等待 Human 逐项裁定
> 本轮未做   = 未创建/修改任何 migration · 无 DDL/DML/INSERT/UPDATE/DELETE ·
>              无 runtime/API/worker/scheduler/service 实现 · 未改任何既有 migration ·
>              未改任何冻结决策原文 · 无 commit/tag/push · 未写 D-P13-01…14
> 强制纪律   = Recommended Direction ≠ Human Decision；不得据工程惯例自行补齐；
>              未完成全部 14 项前不得写入正式 D-P13-01…14
> 证据基数   = `P13_DECISION_COMPLETION_EVIDENCE.md`（2026-09-26 · 313 行）+ 本文件为裁定请求面
> ```

## 0. 状态总览与 FROZEN 核验（只读）

| OQ | 主题 | 状态 |
|---|---|---|
| 01 | permissions canonical seed list | **PENDING** |
| 02 | system role ownership | **READY FOR HUMAN DECISION** |
| 03 | registry seed 受控路径 | **FROZEN**（只核验） |
| 04 | agent subject seed | **READY FOR HUMAN DECISION** |
| 05 | bootstrap tenant | **READY FOR HUMAN DECISION** |
| 06 | bootstrap user / 凭据边界 | **FROZEN**（只核验） |
| 07 | platform membership | **READY FOR HUMAN DECISION** |
| 08 | tenant/space membership | **READY FOR HUMAN DECISION** |
| 09 | seed ordering | **READY FOR HUMAN DECISION** |
| 10 | idempotency | **READY FOR HUMAN DECISION** |
| 11 | trigger interaction | **READY FOR HUMAN DECISION** |
| 12 | downgrade ownership / provenance | **BLOCKING** |
| 13 | environment secrets | **FROZEN**（只核验） |
| 14 | runtime-data protection | **READY FOR HUMAN DECISION** |

**FROZEN 三项核验（本轮实测，仅核验未改写）**：

```text
OQ-P13-03：migration-controlled path · runtime INSERT = FORBIDDEN ·
           C2 registry protection 保持（不得删除/绕过/长期关闭）      → FROZEN marker ✓
OQ-P13-06：identity row = allowed · plaintext password / credential secret = forbidden ·
           「首个可登录主体」与「P13 创建主体记录」必须区分             → FROZEN marker ✓
OQ-P13-13：credentials = 0 · plaintext secrets = 0 · fabricated passwords = 0 → FROZEN marker ✓
```

---

## 1. `OQ-P13-01` — permissions seed list（PENDING · 需裁定）

**证据原样呈现（未修正候选）**：

```text
草拟候选清单 = 13 项（来源 STEP1B_SEED_STRATEGY.md §4 「形状示例」；明文标注「清单待人工审计」）
canonical action = 12 项（D-AUTH-05）· 存储形 = 小写（D-AUTH-25）
草拟清单中的 `manage`（×3：tenant/space/member）与 `write`（×1：resource）
    ∉ canonical vocabulary
⇒ 对应 seed row 将被 ck_permissions_action_canonical 拒绝（DB 层实证）
`system.*` = INSUFFICIENT EVIDENCE（形状占位，无具体 action）
deny 行分配清单 = NOT FOUND（§1[10] 提及「含 deny 行」但无任何权威分配清单）
resource_type 词表 = UNKNOWN（permissions.resource_type 无 CHECK、无文档清单）
key 正则两形差异：SEED_STRATEGY §4（`…(\.[a-z0-9_]+)+$` 至少一段点分）
              vs ck_permissions_key（`…(\.[a-z0-9_]+)*$` 允许单段）
      ⇒ 以数据库 CHECK 为事实基准；文档差异继续登记（OPEN）
```

**Human 必须明确裁定（5 问）**：

| # | 问题 | 候选/待选项 | 裁定栏 |
|---|---|---|---|
| 1 | 最终 permissions seed list 是否采用（哪一版清单） | ACCEPT AS-IS / CUSTOM / KEEP OPEN | ☐ |
| 2 | `manage` / `write` 是否映射？映射为哪个 canonical action？ | ACCEPT OPTION（映射到 `admin`/`update`…）/ CUSTOM / KEEP OPEN | ☐ |
| 3 | `system.*` 是否纳入？ | ACCEPT / CUSTOM / KEEP OPEN（NEED MORE EVIDENCE） | ☐ |
| 4 | deny 行是否存在及其具体分配？ | ACCEPT（需给出分配）/ CUSTOM / KEEP OPEN | ☐ |
| 5 | `resource_type` 是否需要受限词表？ | ACCEPT（建词表）/ CUSTOM / KEEP OPEN | ☐ |

> **在 Human 裁定之前：禁止生成 permissions seed。** 本文件不提供建议映射。

---

## 2. `OQ-P13-12` — seed downgrade ownership / provenance（**BLOCKING** · 需裁定）

### 三候选（完整展示）

| 候选 | 机制 | 一句话 |
|---|---|---|
| **Candidate A — key-marker** | 使用明确的数据标记，使 migration-owned seed 与 runtime-created row 可区分 | 需先解决「当前无任何行级标记」的事实缺口 |
| **Candidate B — NO-OP** | P13 downgrade 不删除相关 seed rows，仅回滚 schema | 零误删风险；牺牲 downgrade 对称性 |
| **Candidate C — fail-closed** | downgrade 检测到无法可靠区分 ownership 时直接失败，不执行潜在误删 | 与 FAIL-CLOSED 族同向；有 runtime 数据后不可回退 |

### 逐候选回答五问（引用当前实际 schema 证据）

**A — key-marker**

| 问题 | 回答 |
|---|---|
| 1. migration-owned seed 如何识别？ | 仅能按 natural key 白名单（`acl_subject_types.key` · `permissions.key` · roles `scope+ownership+key` · `tenants.slug`）；**「数据标记」当前不存在** —— 全库无 seed_batch / migration_owned 列（实测） |
| 2. runtime-created row 如何识别？ | 排除法（不在白名单即 runtime）；若 runtime 复用 seed key ⇒ 不可区分（INSUFFICIENT EVIDENCE） |
| 3. 如何防止误删 runtime 数据？ | key 精确 WHERE + FK RESTRICT 物理拦截被引用行 + 降级前计数核对；不防「key 复用」 |
| 4. 重复 migration / downgrade / upgrade 行为 | upgrade 侧 WHERE NOT EXISTS ⇒ 零新增；downgrade→upgrade 循环以白名单为幂等键 |
| 5. restore / recovery | 误删后仅可经 `audit_logs`（不可变）人工追溯重建；无自动恢复 |

**B — NO-OP**

| 问题 | 回答 |
|---|---|
| 1. migration-owned seed 如何识别？ | 不需要识别（不删除） |
| 2. runtime-created row 如何识别？ | 不适用 |
| 3. 如何防止误删 runtime 数据？ | 结构性保证：零 DELETE；但 0014 态下残留 seed 行成为「有行无 schema 依据」孤儿 |
| 4. 重复 migration / downgrade / upgrade 行为 | upgrade 幂等（WHERE NOT EXISTS 吸收已存在行）；downgrade 永远 NO-OP（确定性） |
| 5. restore / recovery | 无需恢复；但 downgrade 不再回到「干净 0014 态」，需 Human 接受该不对称 |

**C — fail-closed**

| 问题 | 回答 |
|---|---|
| 1. migration-owned seed 如何识别？ | 降级前置检查：`users/tenants > 种子集合 ∨ resource_permissions > 0 ∨ platform_memberships > 0` ⇒ RAISE 拒绝 |
| 2. runtime-created row 如何识别？ | 计数型判据（超出 seed 集合即 runtime 证据），无需行级标记 |
| 3. 如何防止误删 runtime 数据？ | 拒绝执行（零 DELETE）；干净态下才允许回滚 |
| 4. 重复 migration / downgrade / upgrade 行为 | 干净态可重复（首次删种子行后二次执行通过检查并 NO-OP） |
| 5. restore / recovery | 拒绝即回滚（无副作用）；恢复 = 人工清理 runtime 数据后重试 |

### 核心结论（必须保持，原样）

> **「这是 migration 创建的，因此 downgrade 可以安全删除」目前没有数据层证据证明。**

**支撑事实（实测 @0015）**：users/tenants/spaces/resources 有 soft-delete 字段（`deleted_at`）· roles/agents **无**对应字段 ·
`is_system` 仅存在于角色字典语义，**不能直接证明 P13 seed ownership** · FK RESTRICT 网络**不能证明**「该行由 migration 创建」·
`platform_state` 提供一次性状态机先例，**不等同于 seed provenance** · `audit_logs` immutable，**不适合作为简单 ownership marker** ·
全库**没有** seed_batch / migration_owned 等现成行级标记。

**裁定栏（不得由 Bot 自行选择 A/B/C）**：

| 候选 | 裁定 |
|---|---|
| ACCEPT OPTION A（key-marker，含标记机制定义） | ☐ |
| ACCEPT OPTION B（NO-OP） | ☐ |
| ACCEPT OPTION C（fail-closed） | ☐ |
| CUSTOM DECISION（原样记录 Human 决策内容） | ☐ |
| KEEP OPEN / NEED MORE EVIDENCE | ☐ |

---

## 3. 其余九项 OQ（九字段完整展示 · 均待裁定）

### `OQ-P13-02` — System role ownership

1. **Question**：五个内置角色的 P13 归属？
2. **Evidence**：0005 `_seed_system_roles()` 幂等已种 `platform_admin`（实测 1 行）；tenant/space 四角色按既有租户/空间**补种**（0005 时点 0 行）；R2 幂等键 = scope+ownership+key。
3. **Options**：**A** = `platform_admin` 归 0005（P13 仅校验存在）、tenant/space 四角色随首租户/首空间补种 · **B** = 全部重种 · **C** = 四角色全推 runtime onboarding。
4. **Engineering Impact**：A 与 0005 逐字同构；B 重复行风险；C 首租户无默认角色。
5. **Compatibility Impact**：A/C 合规；B 与「不得重复纳入既有 migration-controlled 行」冲突。
6. **Future Runtime Impact**：A ⇒ 首租户建立即具备默认角色（trigger 双保险在位）；C ⇒ runtime 需完整补建。
7. **Recommended Direction**：A（**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：ACCEPT OPTION A ☐ / B ☐ / C ☐ / CUSTOM ☐ / KEEP OPEN ☐

### `OQ-P13-04` — Agent subject seed

1. **Question**：`agent` subject type 是否注册？是否创建实际 Agent？
2. **Evidence**：指令 §8（may register；不得创建实际 Agent/Version/Permission/Run）；SEED_STRATEGY §5 三行含 `agent`；`ck_acl_subject_types_whitelist` 含 `'agent'`；G 依赖 `agents.id` 分派（表已建）。
3. **Options**：**A** = 注册 subject type，0 个实际 Agent · **B** = 连演示 Agent 一起种。
4. **Engineering Impact**：A 后 `agent` 即 G 合法分派目标；B 引入未设计演示数据面。
5. **Compatibility Impact**：A 与指令 §8/§5 一致；B 冲突。
6. **Future Runtime Impact**：A ⇒ 实际 Agent 由 Runtime/业务创建。
7. **Recommended Direction**：A（**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：A ☐ / B ☐ / CUSTOM ☐ / KEEP OPEN ☐

### `OQ-P13-05` — Bootstrap tenant

1. **Question**：首租户行是否属于 P13 migration seed？
2. **Evidence**：SEED_STRATEGY §1[4]（含首租户）vs R4/R5（CLI 专属面仅 PM/state）；**首租户 slug/名称 = INSUFFICIENT EVIDENCE（无权威定义）**；`uq_tenants_slug` 在位；tenants 有 `deleted_at`。
3. **Options**：**A** = 入 seed（slug 需 Human 定名）· **B** = 不入（CLI/Runtime 建 + 角色随播）。
4. **Engineering Impact**：A ⇒ 降级复杂化（与 OQ-12 联动）· B ⇒ D-PLAT-11 需重新解释。
5. **Compatibility Impact**：均不直接违冻；A 需与 OQ-12 联合裁定。
6. **Future Runtime Impact**：A ⇒ 直接有租户容器；B ⇒ Runtime/CLI 完成创建与角色随播。
7. **Recommended Direction**：与 OQ-06/12 联合裁定（**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：A ☐ / B ☐ / CUSTOM ☐ / KEEP OPEN ☐

### `OQ-P13-07` — Platform membership

1. **Question**：首名平台管理员的 `platform_memberships` 绑定归属？
2. **Evidence**：R4/R5（FROZEN 方向）= bootstrap CLI 单事务（插首行 PM + 翻转 `platform_state` + audit `platform.admin.bootstrap`）；seed 永不写 PM；`tg_pm_bootstrap_gate`/`tg_pm_last_admin` 在位（实测）；PM 现状 0 行。
3. **Options**：**A** = 维持 R4/R5（CLI，非 P13）· **B** = P13 seed 写 PM。
4. **Engineering Impact**：A = 零 PM 写入；B 击穿 bootstrap 防线与状态机。
5. **Compatibility Impact**：A = R2/R4/R5 逐字一致；B 冲突。
6. **Future Runtime Impact**：A 保留「一次性初始化窗口」。
7. **Recommended Direction**：A（**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：A ☐ / B ☐ / CUSTOM ☐ / KEEP OPEN ☐

### `OQ-P13-08` — Tenant / space membership

1. **Question**：首管理员 → tenant_admin / space_admin 的 membership 绑定是否入 seed？
2. **Evidence**：SEED_STRATEGY §1[6]/[9]（入）；R2「不给任何用户授予角色」**仅指平台级**；`tg_tm_role_scope`/`tg_membership_role_scope` 形状校验在位；依赖 OQ-05/06。
3. **Options**：**A** = 随首租户/首空间入 seed · **B** = 推 runtime。
4. **Engineering Impact**：A = 2 行 tenant_memberships + 1 行 memberships；B = 首管理员无绑定。
5. **Compatibility Impact**：A 与 §1 一致（平台级禁令不受影响）。
6. **Future Runtime Impact**：A ⇒ 首管理员持有租户/空间管理能力（平台权限仍 default deny）。
7. **Recommended Direction**：A（依赖 OQ-05/06；**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：A ☐ / B ☐ / CUSTOM ☐ / KEEP OPEN ☐

### `OQ-P13-09` — Seed ordering

1. **Question**：`0016_p13_seed` 内 upgrade 顺序？
2. **Evidence**：SEED_STRATEGY §1 十步序；PREP 静态依赖图无环；**无 deferred FK**（实测 `condeferrable=false`）；唯一适配点 = C2 受控路径（OQ-03 已 FROZEN）。
3. **Options**：**A** = 照 §1 顺序（registry → permissions → roles 校验 → tenant → tenant 角色 → tenant_membership → space → space 角色 → membership → role_permissions）· **B** = 其它拓扑。
4. **Engineering Impact**：A 每步 FK 前置已就位；B 需重排并重证无环。
5. **Compatibility Impact**：A = §1 冻结顺序 + `D-P11-12`；B 无先例。
6. **Future Runtime Impact**：仅 migration 内部差异。
7. **Recommended Direction**：A（**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：A ☐ / B ☐ / CUSTOM ☐ / KEEP OPEN ☐

### `OQ-P13-10` — Idempotency

1. **Question**：各 seed 的幂等语义？
2. **Evidence**：§6（ON CONFLICT / WHERE NOT EXISTS 只插一次）；R2（幂等键 = scope+ownership+key；**重复冲突即失败，不 upsert**）；0005/0006 先例；`uq_permissions_key`/`uq_acl_subject_types_key` 在位。
3. **Options**：**A** = registry/permissions 用 WHERE NOT EXISTS、memberships/role_permissions 冲突即失败 · **B** = 统一 ON CONFLICT DO NOTHING。
4. **Engineering Impact**：A 与先例同构；B 把重复从显式失败改为静默跳过。
5. **Compatibility Impact**：A = §6/R2 + 先例；B 明示禁止（无证据统一改写）。
6. **Future Runtime Impact**：A 保证 seed 确定性。
7. **Recommended Direction**：A（**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：A ☐ / B ☐ / CUSTOM ☐ / KEEP OPEN ☐

### `OQ-P13-11` — Trigger interaction

1. **Question**：seed 与既有 39 触发器的交互确认？
2. **Evidence**：G 仅 `resource_permissions` INSERT/UPDATE（P13 零 rp 行）；H 仅 user 硬删；I 仅 role DELETE；J 仅 agent 归档/删除；**C2 拦 registry INSERT（OQ-03 已 FROZEN：受控路径）**；B/C/D/E/F/F2/tm 族形状校验对 seed 行天然满足；`ck_acl_subject_types_whitelist` / `ck_permissions_action_canonical` 数据层词表在位。
3. **Options**：**A** = 按确认 + 实施期逐触发器行为测试 · **B** = 临时禁用其它触发器。
4. **Engineering Impact**：A 零扩大面；B 留遗忘风险。
5. **Compatibility Impact**：A = `D-P11-12`；B 冲突。
6. **Future Runtime Impact**：A ⇒ seed 与 runtime 触发器语义同构。
7. **Recommended Direction**：A（**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：A ☐ / B ☐ / CUSTOM ☐ / KEEP OPEN ☐

### `OQ-P13-14` — Runtime-created data protection

1. **Question**：runtime 数据保护机制？
2. **Evidence**：seed 行均有 natural key / `is_system`；runtime 行无统一 marker（实测无 seed_batch 类列）；FK RESTRICT 被动保护；`platform_state` = 既有一次性标记先例；`audit_logs` 不可变可追溯。
3. **Options**：**A** = 不加 marker，靠 key 过滤 + fail-closed（与 OQ-12=C 组合）· **B** = `seed_batch` 标记列（schema 变更，超 P13 范围）· **C** = seed 行写专用 audit 事件登记。
4. **Engineering Impact**：A 零 schema 变更；B 需新列（连带 C2/触发器面）；C 依赖 audit seed 写入路径。
5. **Compatibility Impact**：A 与既有 schema 冻结一致；B/C 为新增机制（需各自证据）。
6. **Future Runtime Impact**：A 的保护完全由 OQ-12 裁定承载。
7. **Recommended Direction**：A（**≠ Human Decision**）。
8. **Current HUMAN DECISION** = PENDING
9. **Status** = READY FOR HUMAN DECISION　｜　裁定栏：A ☐ / B ☐ / C ☐ / CUSTOM ☐ / KEEP OPEN ☐

---

## 4. 裁定交互格式（Human 填写）

**允许的结果**（必须明确记录，不得改写）：

```text
ACCEPT OPTION A            ACCEPT OPTION B            ACCEPT OPTION C
CUSTOM DECISION            KEEP OPEN / NEED MORE EVIDENCE
```

**决策登记表（Human 逐项填写；Bot 不得代填）**：

| OQ | 当前状态 | 裁定结果（Human 填） | 备注 / CUSTOM 原文 |
|---|---|---|---|
| 01 | **FROZEN** | **CUSTOM DECISION** | 12 项 canonical list（`D-P13-01`）；拒绝 13 项草稿；`manage`→`admin` · `write`→`update`；排除 `system.*`；无 deny 行 |
| 02 | **FROZEN** | **DELEGATED RESOLUTION**（指令 §0 授权 · 派生） | `D-P13-02`；Human 指令 §3 的「OQ-02」实为 OQ-01 Q2（manage/write 映射）⇒ 已登记重映射；**可被否决** |
| 03 | **FROZEN** | —（继承，仅核验，未改写） | `D-P13-03` |
| 04 | **FROZEN** | **ACCEPT OPTION A** | `D-P13-04`；仅注册 `agent` subject type；不创建实际 Agent |
| 05 | **FROZEN** | **ACCEPT OPTION B** | `D-P13-05`；`tenants = 0`；`D-PLAT-11` 重新解释项登记于附录 J.3 |
| 06 | **FROZEN** | —（继承，仅核验，未改写） | `D-P13-06` |
| 07 | **FROZEN** | **ACCEPT OPTION A** | `D-P13-07`；PM 归 bootstrap CLI（R4/R5） |
| 08 | **FROZEN** | **ACCEPT OPTION B** | `D-P13-08`；零 membership 播种 |
| 09 | **FROZEN** | **ACCEPT OPTION A** | `D-P13-09`；§1 十步序为唯一拓扑；step 4/6/9 = no seed |
| 10 | **FROZEN** | **ACCEPT OPTION A** | `D-P13-10`；`WHERE NOT EXISTS` / 冲突即显式失败 |
| 11 | **FROZEN** | **ACCEPT OPTION A** | `D-P13-11`；39 triggers 全启用；禁 DISABLE/DROP/ALTER |
| 12 | **FROZEN** | **ACCEPT OPTION C**（FAIL-CLOSED） | `D-P13-12`；BLOCKING **已解除**；禁 `DELETE WHERE key IN (...)`；禁 ownership marker 列 |
| 13 | **FROZEN** | —（继承，仅核验，未改写） | `D-P13-13` |
| 14 | **FROZEN** | **ACCEPT OPTION A** | `D-P13-14`；不新增 schema marker |

> **CUSTOM DECISION 必须原样记录** —— 不得由 Bot 改写成看似相近的工程结论。

---

## 5. 正式冻结条件核对（当前状态）

```text
OQ-P13-01 有明确 Human Decision   ：✗（PENDING）
OQ-P13-02 有明确 Human Decision   ：✗（READY）
OQ-P13-03 已 FROZEN               ：✓
OQ-P13-04 有明确 Human Decision   ：✗（READY）
OQ-P13-05 有明确 Human Decision   ：✗（READY）
OQ-P13-06 已 FROZEN               ：✓
OQ-P13-07 有明确 Human Decision   ：✗（READY）
OQ-P13-08 有明确 Human Decision   ：✗（READY）
OQ-P13-09 有明确 Human Decision   ：✗（READY）
OQ-P13-10 有明确 Human Decision   ：✗（READY）
OQ-P13-11 有明确 Human Decision   ：✗（READY）
OQ-P13-12 有明确 Human Decision   ：✗（BLOCKING）
OQ-P13-13 已 FROZEN               ：✓
OQ-P13-14 有明确 Human Decision   ：✗（READY）

满足项 = 3 / 14  ⇒  P13 DECISION FREEZE WRITE = NOT PERMITTED
⇒ D-P13-01…14 = NOT YET WRITTEN（本轮未写）
⇒ HARD STOP
```

## 6. 禁止事项确认（本轮遵守）

```text
未据推荐方向代替 Human 决策 ✓ · 未因候选「更常见」而自动采用 ✓ ·
未为 OQ-12 自行发明 ownership 机制 ✓ · 未为通过测试改决策 ✓ ·
未先写 migration/seed 再反推决策 ✓ · 未用 runtime 未来设计反向覆盖 P13 决策 ✓
DDL/DML/INSERT/UPDATE/DELETE = 0 ✓ · runtime/API/worker/scheduler = 0 ✓ ·
既有 migration 未改 ✓ · 冻结决策原文未改 ✓ · commit/tag/push = 0 ✓
```

---

## 7. 输入登记（2026-09-26 22:23 · Human Decision Input 收到）

> 本区为**追加登记**（append-only）：**不**修改 §1–§6、**不**填写 §4 决策登记表、**不**产生任何裁定。

### 7.1 收到的提交

对 11 个未冻结 OQ 逐项检查，提交内容与模板**逐字一致**，均为**未填写占位符**：

```text
Decision:       `ACCEPT OPTION __ / CUSTOM DECISION / KEEP OPEN`
Human Decision: `填写最终裁定`
```

受影响项：

```text
OQ-P13-01 · 02 · 04 · 05 · 07 · 08 · 09 · 10 · 11 · 12 · 14   （共 11 项）
```

### 7.2 裁定解析结果

```text
实际携带裁定的项 = 0
⇒ 新增 Human Decision = 0 · 新增 FROZEN = 0 · 新增 CUSTOM DECISION = 0 · 新增 KEEP OPEN = 0

依据（本轮指令原文）：
  「未填写的项目不得视为接受 Recommended Direction。」
  「KEEP OPEN / NEED MORE EVIDENCE = 不冻结，本轮继续保持 BLOCKED。」
```

- **未做任何推断**：既未按 Recommended Direction 补齐，也未把占位符读作 KEEP OPEN ——
  占位符**不构成**任何一种允许结果，故登记为「**未提交裁定**」而非「已裁定为 KEEP OPEN」。
- §4 决策登记表**保持空白**（Bot 不得代填）。

### 7.3 FROZEN 三项核验（只读 · 未改写）

```text
OQ-P13-03 = FROZEN ✓（marker 在位）
OQ-P13-06 = FROZEN ✓（marker 在位）
OQ-P13-13 = FROZEN ✓（marker 在位）
OQ-P13-01 = PENDING（保持）· OQ-P13-12 = BLOCKING（保持）
```

### 7.4 冻结条件

```text
满足项 = 3 / 14（仍仅 FROZEN 三项）

P13 DECISION FREEZE WRITE = NOT PERMITTED
D-P13-01 … D-P13-14       = NOT YET WRITTEN
P13 IMPLEMENTATION        = NOT AUTHORIZED
Runtime                   = NOT AUTHORIZED
0016+ = ABSENT · DDL/DML = 0 · commit/tag/push = 0
```

### 7.5 解除 BLOCKED 所需

Human 在 §4 决策登记表逐项填写（或按本回合格式重新提交已填写的裁定单），
每项给出 `ACCEPT OPTION A/B/C` · `CUSTOM DECISION`（附原文）· `KEEP OPEN / NEED MORE EVIDENCE` 之一。

> 若 Human 的意图是「全部 KEEP OPEN」，**须显式写明** —— 本轮未作此推定。

## 8. 裁定完成登记（2026-09-26 · DECISION RESOLUTION EXECUTION）

> **本区为追加登记**：**不**修改 §1–§7。§7 记录的「空白提交」为 **2026-09-26 22:23 时点事实**（历史）；
> 本节记录其后的**正式裁定**（Human 指令 `UAP — P13 HUMAN DECISION / DECISION RESOLUTION EXECUTION`）。

```text
14/14 已裁定 ⇒ D-P13-01 … D-P13-14 已写入 PLATFORM_DECISION_LOG.md（附录 J 汇总）
继承 Freeze Gate 既有 FROZEN = 3（03 / 06 / 13）
本轮 Human 架构裁定          = 10（01 / 04 / 05 / 07 / 08 / 09 / 10 / 11 / 12 / 14）
本轮 DELEGATED RESOLUTION    = 1（02 · 派生 · 可被 Human 显式否决）
P13 DECISION FREEZE          = PASS
P13 IMPLEMENTATION           = NOT AUTHORIZED（须再次显式授权）
0016+ = ABSENT · 0016_p13_seed.py = MUST NOT EXIST
```

**待 Human 知悉的两项**：

```text
① 编号重映射（不得静默）：指令 §3 标题「OQ-P13-02 — manage / write mapping」的内容
   实为 SHEET §1 表 OQ-P13-01 的第 2 问 ⇒ 已登记为 D-P13-01 的子问题闭项 Q2。
   SHEET 的 OQ-P13-02（System role ownership）由 §0 授权做派生裁定 ⇒ D-P13-02。
② D-PLAT-11 语义张力：OQ-05 = B（无 bootstrap tenant）+ OQ-08 = B（无 membership）
   ⇒「首个可登录主体」产生路径需正式重新解释（由 OQ-05 既有 Engineering Impact 预先载明）。
   已登记为实施轮前置澄清项（PDL 附录 J.3），本轮不改写、不 supersede D-PLAT-11。
```

**END OF P13 HUMAN DECISION SHEET（2026-09-26 · 14/14 已裁定 ⇒ `DECISION FREEZE = PASS`；见 §8）**

```text
P13 IMPLEMENTATION = NOT AUTHORIZED
0016+ = ABSENT · D-P13-01..14 = NOT YET WRITTEN · DDL/DML = 0 · commit/tag/push = 0
HARD STOP
```
