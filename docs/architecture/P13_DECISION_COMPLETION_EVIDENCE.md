# UAP — P13 DECISION COMPLETION EVIDENCE（Human Decision 准备专用）

> ## 状态与用途
>
> ```text
> READ-ONLY · EVIDENCE PRESENTATION · DECISION PACKAGE COMPLETION
> 本文件仅用于 Human Decision preparation —— 不构成任何决策、不产生任何 seed、
> 不修改任何冻结正文、不执行任何 DML/DDL。
> ```
>
> **决策状态登记（本轮确认，未改变）**：
> `OQ-P13-03 / 06 / 13 = FROZEN` · `OQ-P13-01 = PENDING` · `OQ-P13-12 = BLOCKING` ·
> `OQ-P13-02/04/05/07/08/09/10/11/14 = READY FOR HUMAN DECISION`。
> **禁止**：把 Recommended Direction 自动升格为 Human Decision；不得自行补齐事实
> （`NOT FOUND / UNKNOWN / INSUFFICIENT EVIDENCE / OPEN` 原样登记）。

---

## 0. 决策状态总览

| OQ | 主题 | 当前状态 |
|---|---|---|
| `OQ-P13-01` | permissions canonical seed list | **PENDING**（清单未审计 · §1 深度展开） |
| `OQ-P13-02` | system role ownership | **READY FOR HUMAN DECISION** |
| `OQ-P13-03` | registry seed 受控路径 | **FROZEN**（migration-controlled · C2 保持） |
| `OQ-P13-04` | agent subject seed | **READY FOR HUMAN DECISION** |
| `OQ-P13-05` | bootstrap tenant | **READY FOR HUMAN DECISION** |
| `OQ-P13-06` | bootstrap user / 凭据边界 | **FROZEN**（identity row allowed · credentials forbidden） |
| `OQ-P13-07` | platform membership | **READY FOR HUMAN DECISION** |
| `OQ-P13-08` | tenant/space membership | **READY FOR HUMAN DECISION** |
| `OQ-P13-09` | seed ordering | **READY FOR HUMAN DECISION** |
| `OQ-P13-10` | idempotency | **READY FOR HUMAN DECISION** |
| `OQ-P13-11` | trigger interaction | **READY FOR HUMAN DECISION** |
| `OQ-P13-12` | downgrade safety | **BLOCKING**（§2 深度展开） |
| `OQ-P13-13` | environment secrets | **FROZEN**（credentials=0 · secrets=0 · fabricated=0） |
| `OQ-P13-14` | runtime-data protection | **READY FOR HUMAN DECISION** |

---

## 1. `OQ-P13-01` 深度展开 — permissions canonical seed list

### 1.1 来源（原样登记）

| 来源 | 内容性质 |
|---|---|
| `STEP1B_SEED_STRATEGY.md` §4 | **形状示例**（key 正则 + is_system=true），明文「具体清单 B1 定稿前由人工审计确认」· 「不构成 B1-4 resource_permissions.action 的 vocabulary 冻结」 |
| `migrations_alembic/versions/0005` | permissions 表**形状**（0 行 seed；「清单未定稿，见 SEED_STRATEGY §4：仅定形状、清单待人工审计」原文） |
| `D-AUTH-05`（FROZEN） | Action 词表 = 12 项 canonical：`READ LIST CREATE UPDATE DELETE EXECUTE APPROVE REJECT PUBLISH EXPORT SHARE ADMIN` |
| `D-AUTH-25`（FROZEN） | Action canonical **存储形 = 小写**；`permissions.action` 由 `ck_permissions_action_canonical` CHECK 精确匹配小写形 |
| `D-AUTH-24`（FROZEN） | `D-B14-08` 被 `D-AUTH-05` SUPERSEDE ⇒ `resource_permissions.action` 不再 opaque |

### 1.2 候选内容（SEED_STRATEGY §4 草稿 · **未经人工审计** · 逐项与 12 动作词表比对）

| # | key（草稿） | 隐含 action | resource_type（推导） | is_system | 词表兼容判定 |
|---|---|---|---|---|---|
| 1 | `system.*` | **未定**（通配形状） | system | true | **INSUFFICIENT EVIDENCE** —— `*` 为形状占位，非具体 action |
| 2 | `tenant.read` | `read` | tenant | true | ✅ 在词表 |
| 3 | `tenant.manage` | `manage`？ | tenant | true | **✗ `manage` ∉ 12 词表**（`ck_permissions_action_canonical` 将拒绝） |
| 4 | `space.read` | `read` | space | true | ✅ |
| 5 | `space.manage` | `manage`？ | space | true | **✗** 同上 |
| 6 | `member.read` | `read` | member | true | ✅（key 中的 `member` 是词典义，非角色名 —— §2 原文澄清） |
| 7 | `member.manage` | `manage`？ | member | true | **✗** 同上 |
| 8 | `resource.read` | `read` | resource | true | ✅ |
| 9 | `resource.write` | `write` | resource | true | **✗ `write` ∉ 12 词表**（词表为 `update`/`create`/`delete`） |
| 10 | `resource.delete` | `delete` | resource | true | ✅ |
| 11 | `agent.execute` | `execute` | agent | true | ✅ |
| 12 | `tool.execute` | `execute` | tool | true | ✅ |
| 13 | `audit.read` | `read` | audit | true | ✅ |

```text
结论（原样登记，非裁定）：
  13 个草稿 key 中 9 个词表兼容 · 4 个含 ∉ 词表的隐含 action（manage ×3 · write ×1）·
  1 个（system.*）INSUFFICIENT EVIDENCE。
  候选总数（若形状即清单）= 13 行 · is_system 全 true ·
  每行 columns = id · key · resource_type · action · description · is_system · created_at。
  ⚠ resource_type 词表：permissions.resource_type 无 CHECK（实测）—— 取值惯例 UNKNOWN / OPEN。
  ⚠ deny 行清单：SEED_STRATEGY §1[10] 提及 role_permissions「含 deny 行」但 deny 行的具体
    分配（哪个角色对哪个 permission 为 deny）＝ NOT FOUND / OPEN（无任何权威清单）。
```

### 1.3 与既有 schema / 冻结决策的兼容性证据（实测 @0015）

```text
ck_permissions_action_canonical = CHECK (action = ANY (ARRAY['read','list','create','update',
    'delete','execute','approve','reject','publish','export','share','admin']))   ← 12 小写形
ck_permissions_key              = CHECK (key ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$')
uq_permissions_key              = 唯一索引（幂等锚点，WHERE NOT EXISTS 的判据）
role_permissions                = ck_role_permissions_effect CHECK (effect = ANY(['allow','deny']))
                                  · PK 复合（pk_role_permissions）· ix_role_permissions_permission
D-AUTH-25                       = 存储形精确小写 · 入站归一 NFKC→strip→casefold（不放宽存储）
D-AUTH-05                       = 「不得建立第二套 Action 词表」⇒ 候选中 manage/write 需映射到
                                  词表成员（如 manage→admin？write→update？）或经 Module 扩展
                                  通道（SC-3 = PROPOSED ONLY，未实施）—— **映射方式 OPEN**
```

**OPEN / UNKNOWN 登记（OQ-01 内，原样）**：
① 4 个 ∉ 词表的隐含 action 的**映射或改写**方案（OPEN）；② `system.*` 具体展开（INSUFFICIENT EVIDENCE）；
③ `resource_type` 取值惯例（UNKNOWN，无 CHECK 无文档清单）；④ deny 行分配清单（NOT FOUND）；
⑤ 权限数量（= 候选 13 或审计后清单，**由 Human 裁定**）。**本轮不生成 seed。**

---

## 2. `OQ-P13-12` 深度展开 — Downgrade 安全（BLOCKING · 唯一）

### 2.0 真实 schema / data model 证据（实测 @0015 · 全部为防「误删 runtime」的既有机制）

```text
① 软删列：users.deleted_at ✓ · tenants.deleted_at ✓ · spaces.deleted_at ✓ · resources.deleted_at ✓
          roles ✗ · agents ✗（无软删列 ⇒ roles/agents 的「运行时状态」无行内标记）
② is_system：roles.is_system=true 仅标记**角色字典行**；users/tenants/spaces 无任何 is_system 类标记
③ natural key：acl_subject_types.key（uq 部分索引 lower(key)+archived_at）· permissions.key（uq_permissions_key）
   · roles = scope+ownership+key（R2）· tenants.slug（uq_tenants_slug）· users = email/username UQ
④ FK RESTRICT 网：所有业务删除均为 RESTRICT（CORE_DOMAIN_MODEL）⇒ 被引用行 DELETE 物理失败
⑤ platform_state 状态机：0006 种 'uninitialized'；bootstrap CLI 一次性翻转 ⇒ 「initialized 后不可重开」
   的既有「一次性标记」先例
⑥ audit_logs：P10 不可变（tg_audit_immutable）⇒ 任何 DELETE 尝试均 RAISE —— 无「删除历史」能力
⑦ P11 触发器：I（role 被 ACL 引用禁删）· H（user 硬删清理 ACL）· G（rp 写入校验）在 seed/降级期间同样生效
⑧ rg 无「seed 批次标记」：任何表均无 seed_batch / created_by_migration 列（实测列清单）⇒
   「这是 migration 创建的」在数据层**无行内证明**（正是本 OQ 的核心困难）
```

### 2.1 候选 A — key-based ownership marker（key 过滤）

| 问题 | 回答（含证据） |
|---|---|
| migration-owned seed 如何识别？ | 仅可按 **natural key 白名单**：registry `key ∈ {user,role,agent}`（uq_acl_subject_types_key）· permissions `key ∈ 冻结清单 ∧ is_system`（uq_permissions_key）· roles `is_system=true ∧ 归属=seed 建的租户/空间` · tenants `slug = seed 常量`。**识别依赖「seed 常量清单」在 migration 中显式维护**；若清单与实际 seed 不一致 ⇒ 漏删/误删 |
| runtime-created row 如何识别？ | **无行内标记**（⑧）—— 只能**排除法**：不在白名单 key 内 ⇒ 视为 runtime。风险：runtime 恰好使用了与 seed 相同的 natural key（如 onboarding 也建 slug 同名租户）⇒ 不可区分（INSUFFICIENT EVIDENCE） |
| downgrade 如何避免误删 runtime data？ | 三重防线：natural key 精确 WHERE + FK RESTRICT 物理拦截被引用行 + 降级前**计数核对**（白名单行存在才删）。但「runtime 复用了 seed key」的场景无法防御 |
| 重复执行如何处理？ | 与 OQ-10 联动：upgrade 侧 WHERE NOT EXISTS ⇒ 二次执行零新增；downgrade→upgrade 循环以白名单为幂等键 |
| restore / recovery 如何处理？ | 误删恢复只能靠 `audit_logs`（不可变）追溯 + 人工重建；无自动恢复（PMB-1 模式：无恢复 API） |

### 2.2 候选 B — NO-OP（保留全部数据）

| 问题 | 回答 |
|---|---|
| migration-owned seed 如何识别？ | **不需要识别**（不删除任何行）—— 规避了 ⑧ 的根本困难 |
| runtime-created row 如何识别？ | 同上，不适用 |
| downgrade 如何避免误删 runtime data？ | **结构性保证**：零 DELETE ⇒ 零误删；但 `downgrade` 后 `alembic_version` 回到 0014 而数据仍在 ⇒ 后续再 upgrade 时幂等键必须吸收已存在行（WHERE NOT EXISTS 兼容 ✓） |
| 重复执行如何处理？ | upgrade 幂等（同上）；downgrade 重复执行 = 永远 NO-OP（确定性 ✓） |
| restore / recovery 如何处理？ | 无需恢复（数据未删）；但「0015 之前的干净态」不可达 ⇒ **破坏「downgrade=回到前一 schema 状态」的对称性**，且被 seed 行占据的 natural key（如 registry 三行）在 0014 态下成为「孤儿数据」（无 schema 却有行）—— 需 Human 接受 |

### 2.3 候选 C — fail-closed（存在 runtime 数据即拒绝降级）

| 问题 | 回答 |
|---|---|
| migration-owned seed 如何识别？ | 降级**前置检查**定义「runtime 数据」判据：例如 `users > 种子行数 ∨ tenants > 种子数 ∨ resource_permissions > 0 ∨ platform_memberships > 0` ⇒ 任一命中即 RAISE 拒绝降级（与 `D-P11-04` FAIL-CLOSED 同向） |
| runtime-created row 如何识别？ | 判据为**计数型**（无需行内标记）：任何超出 seed 集合的行 = runtime 证据 |
| downgrade 如何避免误删 runtime data？ | 结构性保证：拒绝执行 ⇒ 零误删；且比 B 多保住「downgrade 到干净态」的能力（当且仅当无 runtime 数据） |
| 重复执行如何处理？ | upgrade 幂等同 A/B；downgrade 在干净态可重复（first downgrade 成功后种子行已删 ⇒ 二次执行同样通过检查并 NO-OP） |
| restore / recovery 如何处理？ | 拒绝即回滚（无副作用）；恢复手段 = 人工清理 runtime 数据后重试（运维面） |

### 2.4 对比小结（原样呈现，非推荐）

```text
A：精细可回滚，但依赖「seed 常量清单」的人工维护正确性；对「runtime 复用 seed key」不设防。
B：零风险但牺牲 downgrade 对称性；0014 态下存在孤儿 seed 行。
C：fail-closed 最严（与 D-AUTH-12/D-P11-04 同向），保留干净态回滚；代价 = 有 runtime 数据后
   migration 链不可回退（运维约束）。
共同前提：⑧「无行内 seed 标记」是三案共同的证据边界；B/C 不需要行级识别，A 需要。

> **核心结论（原样保持）：「这是 migration 创建的，因此 downgrade 可以安全删除」目前没有数据层证据证明。**
指令 §14：任何一案的采用都必须由 Human 正式裁定 —— 本文件仅呈现证据。
```

---

## 3. 其余九项 OQ 完整展开（字段逐项原样）

### 3.1 `OQ-P13-02` — System role ownership — **READY FOR HUMAN DECISION**

- **Question**：五个内置角色的 P13 归属？
- **Evidence**：0005 `_seed_system_roles()` 幂等已种 `platform_admin`（实测 1 行）；tenant/space 四角色按既有租户/空间补种（0005 时点 0 行）· R2 幂等键 = scope+ownership+key · 实测 roles=1。
- **Options**：A = `platform_admin` 归 0005、P13 仅校验存在；tenant/space 四角色随首租户/首空间补种。B = 全部重种。C = 四角色全推 runtime onboarding。
- **Engineering Impact**：A 与 0005 逐字同构；B 重复行风险；C 首租户无默认角色。
- **Compatibility Impact**：A/C 合规；B 与指令 §6「不得重复纳入」冲突。
- **Future Runtime Impact**：A/C ⇒ runtime onboarding 需按 §3 双保险建默认角色；A 已有 trigger 防线。
- **Recommended Direction**：A（**未被采用为裁定**）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

### 3.2 `OQ-P13-04` — Agent subject seed — **READY FOR HUMAN DECISION**

- **Question**：`agent` subject type 是否注册？是否建实际 Agent？
- **Evidence**：指令 §8（may register；不得建实际 Agent/Version/Permission/Run）· SEED_STRATEGY §5（三行含 agent）· G 依赖 `agents.id` 分派（表已建）· `ck_acl_subject_types_whitelist` 含 'agent'。
- **Options**：A = 注册 subject type，0 个实际 Agent。B = 连演示 Agent 一起种。
- **Engineering Impact**：A 后 `agent` 即为 G 合法分派目标；B 引入未经设计的演示数据面。
- **Compatibility Impact**：A 与指令 §8/§5 一致；B 冲突。
- **Future Runtime Impact**：A 后实际 Agent 由 Runtime/业务创建。
- **Recommended Direction**：A（未被采用为裁定）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

### 3.3 `OQ-P13-05` — Bootstrap tenant — **READY FOR HUMAN DECISION**

- **Question**：首租户行是否属于 P13 migration seed？
- **Evidence**：SEED_STRATEGY §1[4]（含首租户）vs R4/R5（bootstrap CLI 专属面仅 PM/state）· slug 命名未冻结（**INSUFFICIENT EVIDENCE：首租户的 slug/名称无任何权威定义**）· `uq_tenants_slug` 在位 · tenants 有 deleted_at 软删列。
- **Options**：A = 入 seed（slug 需 Human 定名）。B = 不入（bootstrap CLI/Runtime 建，角色随播）。
- **Engineering Impact**：A ⇒ 降级复杂化（OQ-12 联动：tenants 有软删列但 slug 唯一）；B ⇒ D-PLAT-11 需重新解释。
- **Compatibility Impact**：均不直接违冻；A 需与 OQ-12 联合裁定。
- **Future Runtime Impact**：A ⇒ Runtime 直接有租户容器；B ⇒ Runtime/CLI 需完成租户创建 + 角色随播。
- **Recommended Direction**：与 OQ-06/12 联合裁定（**未被采用为裁定**）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

### 3.4 `OQ-P13-07` — Platform membership — **READY FOR HUMAN DECISION**

- **Question**：首名平台管理员的 `platform_memberships` 绑定归属？
- **Evidence**：R4/R5（FROZEN 方向）：bootstrap CLI 单事务 = 插首行 PM + 翻转 `platform_state` + audit `platform.admin.bootstrap`；seed 永不写 PM；`tg_pm_bootstrap_gate`/`tg_pm_last_admin` 在位（实测）；PM 现状 0 行。
- **Options**：A = 维持 R4/R5（CLI，非 P13）。B = P13 seed 写 PM。
- **Engineering Impact**：A = 零 PM 写入；B 击穿 bootstrap 防线与状态机。
- **Compatibility Impact**：A = R2/R4/R5 逐字一致；B 冲突。
- **Future Runtime Impact**：A 保留一次性初始化窗口。
- **Recommended Direction**：A（合规必选；**未被采用为裁定**）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

### 3.5 `OQ-P13-08` — Tenant / space membership — **READY FOR HUMAN DECISION**

- **Question**：首管理员 → tenant_admin / space_admin 的 membership 绑定是否入 seed？
- **Evidence**：SEED_STRATEGY §1[6]/[9]（入）· R2「不给任何用户授予角色」**仅指平台级** · `tg_tm_role_scope`/`tg_membership_role_scope` 形状校验在位 · OQ-05/06 联动。
- **Options**：A = 随首租户/首空间入 seed。B = 推 runtime。
- **Engineering Impact**：A = 2 行 tenant_memberships + 1 行 memberships；B = 首管理员无绑定。
- **Compatibility Impact**：A 与 §1 一致；R2 平台级禁令不受影响。
- **Future Runtime Impact**：A 后首管理员持有租户/空间管理能力（平台权限仍 default deny，PM bootstrap 之前）。
- **Recommended Direction**：A（依赖 OQ-05/06；**未被采用为裁定**）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

### 3.6 `OQ-P13-09` — Seed ordering — **READY FOR HUMAN DECISION**

- **Question**：`0016_p13_seed` 内 upgrade 顺序？
- **Evidence**：SEED_STRATEGY §1 十步序（FK 依赖修正版）· PREP 静态依赖图无环 · 无 deferred FK（实测 `condeferrable=false`）· 唯一适配点 = C2 受控路径（OQ-03 FROZEN）。
- **Options**：A = 照 §1 顺序（registry → permissions → roles 校验 → tenant → tenant 角色 → tenant_membership → space → space 角色 → membership → role_permissions）。B = 其它拓扑。
- **Engineering Impact**：A 每步 FK 前置已就位；B 需重排并重新证明无环。
- **Compatibility Impact**：A = §1 冻结顺序 + `D-P11-12`；B 无先例。
- **Future Runtime Impact**：仅 migration 内部差异。
- **Recommended Direction**：A（**未被采用为裁定**）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

### 3.7 `OQ-P13-10` — Idempotency — **READY FOR HUMAN DECISION**

- **Question**：各 seed 的幂等语义？
- **Evidence**：§6（platform_admin/acl/permissions 用 ON CONFLICT 或 WHERE NOT EXISTS）· R2（幂等键 = scope+ownership+key；**重复冲突即失败，不 upsert**）· 0005/0006 先例（WHERE NOT EXISTS / ON CONFLICT DO NOTHING）· `uq_permissions_key`/`uq_acl_subject_types_key` 在位。
- **Options**：A = registry/permissions 用 WHERE NOT EXISTS；memberships/role_permissions 冲突即失败。B = 统一 ON CONFLICT DO NOTHING。
- **Engineering Impact**：A 与先例逐字同构；B 把「重复」从显式失败改为静默跳过。
- **Compatibility Impact**：A = §6/R2 + 先例；B 被指令 §10 禁止。
- **Future Runtime Impact**：A 保证 seed 确定性。
- **Recommended Direction**：A（**未被采用为裁定**）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

### 3.8 `OQ-P13-11` — Trigger interaction — **READY FOR HUMAN DECISION**

- **Question**：seed 与既有 39 触发器的交互确认？
- **Evidence**：实测语义 —— G 仅 `resource_permissions` INSERT/UPDATE（P13 零 rp 行）；H 仅 user 硬删；I 仅 role DELETE；J 仅 agent 归档/删除；**C2 拦 registry INSERT（OQ-03 已 FROZEN：受控路径）**；B/C/D/E/F/F2/tm 族形状校验对 seed 行天然满足；`ck_acl_subject_types_whitelist`/`ck_permissions_action_canonical` 数据层词表在位。
- **Options**：A = 按确认 + 实施期逐触发器行为测试。B = 临时禁用其它触发器。
- **Engineering Impact**：A = 零扩大面；B 留遗忘风险。
- **Compatibility Impact**：A = `D-P11-12`；B 冲突。
- **Future Runtime Impact**：A 后 seed 与 runtime 触发器语义同构。
- **Recommended Direction**：A（**未被采用为裁定**）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

### 3.9 `OQ-P13-14` — Runtime-created data protection — **READY FOR HUMAN DECISION**

- **Question**：runtime 数据保护机制？
- **Evidence**：seed 行均有 natural key / is_system；runtime 行无统一 marker（实测无 seed_batch 列）；FK RESTRICT 被动保护；`platform_state` 状态机 = 既有「一次性标记」先例；audit_logs 不可变可追溯。
- **Options**：A = 不加 marker，靠 key 过滤 + fail-closed（与 OQ-12=C 组合）。B = `seed_batch` 标记列（schema 变更，超 P13 范围）。C = seed 行写专用 audit 事件登记。
- **Engineering Impact**：A 零 schema 变更；B 需新列（连带面）；C 依赖 audit seed 写入路径。
- **Compatibility Impact**：A 与既有 schema 冻结一致；B/C 均为新增机制（需各自证据）。
- **Future Runtime Impact**：A 的保护完全由 OQ-12 裁定承载。
- **Recommended Direction**：A（**未被采用为裁定**）。
- **Current HUMAN DECISION** = PENDING
- **Current STATUS** = PROPOSED

---

## 4. `OQ-P13-01 / OQ-P13-12` 状态重申（未改变）

```text
OQ-P13-01 = PENDING    permissions canonical list 尚未完成充分人工审计；
                       不得因 key pattern / is_system 已定义而自动生成完整清单（§1.2 比对表仅呈证据）
OQ-P13-12 = BLOCKING   三个候选（§2.1–2.3）均已完整回答五问并附 schema 证据；
                       任何一案的采用必须由 Human 正式裁定（§14 指令）
```

---

## 5. NOT FOUND / UNKNOWN / INSUFFICIENT EVIDENCE / OPEN 登记簿（原样）

| # | 项 | 分类 | 关联 OQ |
|---|---|---|---|
| U-1 | permissions `resource_type` 取值惯例（无 CHECK、无文档清单） | UNKNOWN | 01 |
| U-2 | `deny` 行分配清单（哪些角色对哪些 permission 为 deny） | NOT FOUND | 01 |
| U-3 | `system.*` 的具体展开 | INSUFFICIENT EVIDENCE | 01 |
| U-4 | 候选中 `manage`/`write` ∉ 12 词表的映射方案 | OPEN | 01 |
| U-5 | 首租户 slug / 名称 | INSUFFICIENT EVIDENCE | 05 |
| U-6 | 「runtime 复用 seed natural key」的防御（候选 A 内不可解） | INSUFFICIENT EVIDENCE | 12 |
| U-7 | permissions.key 正则：SEED_STRATEGY §4（至少一段点分）vs `ck_permissions_key`（允许单段）——两形不一致，以 **CHECK 为准**（数据层权威），文档形未更新 | OPEN（文档差异登记） | 01 |
| U-8 | seed 是否写 `audit_logs`（actor='system'）事件（§6 提及；路径未设计） | OPEN | 09/11 |

---

## 6. 核验块

```text
0016+ = ABSENT · 单头 = 0015_p12_indexes（链长 15）· versions = 15
0010–0015 sha256 逐字节未变 · D-P13-01…14 = NOT YET WRITTEN
INSERT/UPDATE/DELETE/DDL/DML/migration/code/test/config = 0 · commit/tag/push = 0
OQ-P13-03/06/13 = FROZEN（未改）· OQ-P13-01 = PENDING（未改）· OQ-P13-12 = BLOCKING（未改）
P13 IMPLEMENTATION = NOT AUTHORIZED · Runtime = NOT AUTHORIZED
```

**END OF P13 DECISION COMPLETION EVIDENCE（2026-09-26 · 仅用于 Human Decision preparation）**

---

## 7. 决策指针（2026-09-26 · 本文件为 **pre-decision** 证据快照）

> 本文件的 §1.2 候选表、§1.3 兼容性证据、§2.1–§2.4 三候选与 §3 九项字段均为
> **Human Decision 之前的证据面**，**保持原文不动**（append-only）。
>
> **裁定结果指针**（权威 = `PLATFORM_DECISION_LOG.md` `D-P13-01`…`D-P13-14` + 附录 J）：

```text
OQ-01 → CUSTOM DECISION：12 项 canonical list（非 §1.2 的 13 项草稿）
        manage → admin · write → update（§1.3 中原标记为 OPEN 的映射**已闭项**）
        system.* 排除 · 不创建 deny 行 · resource_type 不新增 DB 词表
OQ-12 → ACCEPT OPTION C（FAIL-CLOSED）⇒ §2.4 的「非推荐、仅呈现」已由裁定收敛
OQ-05 → ACCEPT OPTION B（不创建 bootstrap tenant）⇒ §3.3 的 slug INSUFFICIENT EVIDENCE 不再需要补证
OQ-08 → ACCEPT OPTION B（不创建 membership）
OQ-02 → DELEGATED RESOLUTION（§0 授权 · 派生）
OQ-03 / 06 / 13 → FROZEN（继承，未重裁）
其余（04 / 07 / 09 / 10 / 11 / 14）→ 见附录 J「J.1 计数」
```

> ⇒ 本文件中 §1.2 / §1.3 的 `manage`、`write`、`system.*`、deny、`resource.write` 等
> **均为历史候选语境**，**不得**被一致性扫描识别为 current decision。
