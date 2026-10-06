# UAP — P13 HUMAN DECISION SHEET · EXACT EXTRACTION（READ-ONLY · 原样提取）

> ## 本轮性质
>
> ```text
> 轮次       = P13 Human Decision Sheet Exact Extraction / READ-ONLY
> 目标       = 从仓库实际文件原样提取 11 项待裁 OQ 的 Decision 材料，供 Human 裁定
> 提取方式   = **机械行切片**（按源文件行号原样截取，非人工重打；每块带 SRC 标记可复算）
> 本轮未做   = 未重新设计 · 未重新推荐 · 未增删改任何 Option · 未修正历史措辞 ·
>              未把 Recommended Direction 当作 Human Decision · 未为 OQ-12 发明第 4 方案 ·
>              未写 D-P13-* · 未改 §4 登记表 · 无 migration/DDL/DML/seed ·
>              无 runtime/API/worker · 无 commit/tag/push
> ```

## 0. 来源与指纹（只读实测）

| 键 | 路径 | sha256（前 24） | 行数 | 角色 |
|---|---|---|---|---|
| `SHEET` | `docs/architecture/P13_HUMAN_DECISION_SHEET.md` | `f0a29c8ac7f2901b3054e7ea` | 390 | 裁定请求面（本次提取主源；§1/§2/§3） |
| `EVID` | `docs/architecture/P13_DECISION_COMPLETION_EVIDENCE.md` | `d28d00932c28d0e3a0399020` | 316 | 证据基数（OQ-01 候选清单原文出处 §1.2/§1.3） |
| `SEED` | `docs/architecture/STEP1B_SEED_STRATEGY.md` | `a18a394e7848aa61cc8ba003` | 166 | 候选草稿原始出处（§4「初始 permissions 字典」） |

**文件定位结果**：basename 全仓匹配 = **1** ⇒ 无同名歧义，未自行选择。

**提取规则（遵守 §2 HARD RULE）**：

```text
① 保留原 OQ 编号 / 原字段顺序 / 原文（中文标点·加粗·全角符号一律不动）
② Option 标签仅按原文自身的 `**A** =` / `**B** =` / `**C** =` 标注**机械拆行**；
   原文未定义 Option A/B/C ⇒ 登记「原文未定义」，**绝不新增**
③ 原文未定义的字段 ⇒ 登记「原文未定义」并给出最近源材料出处（不补造）
④ Recommended Direction 一律保留「≠ Human Decision」原文标注
⑤ CUSTOM DECISION 保留原文输入空间，不做任何预填
```

---

## 1. FROZEN 三项只读核验（`OQ-P13-03` / `OQ-P13-06` / `OQ-P13-13`）

<!-- SRC:SHEET:37-43 -->
```text
OQ-P13-03：migration-controlled path · runtime INSERT = FORBIDDEN ·
           C2 registry protection 保持（不得删除/绕过/长期关闭）      → FROZEN marker ✓
OQ-P13-06：identity row = allowed · plaintext password / credential secret = forbidden ·
           「首个可登录主体」与「P13 创建主体记录」必须区分             → FROZEN marker ✓
OQ-P13-13：credentials = 0 · plaintext secrets = 0 · fabricated passwords = 0 → FROZEN marker ✓
```
<!-- /SRC -->

> 核验结论：三项 FROZEN marker **全部在位**；本轮**未重裁、未改写、未扩展**。

**状态总览（原文 §0 表）**：

<!-- SRC:SHEET:18-33 -->
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
<!-- /SRC -->

---

## 2. `OQ-P13-01` — permissions canonical seed list（**PENDING** · 需裁定）

### 2.1 Question / 裁定面（原文 §1「Human 必须明确裁定（5 问）」+ 其后的禁用声明）

<!-- SRC:SHEET:65-75 -->
**Human 必须明确裁定（5 问）**：

| # | 问题 | 候选/待选项 | 裁定栏 |
|---|---|---|---|
| 1 | 最终 permissions seed list 是否采用（哪一版清单） | ACCEPT AS-IS / CUSTOM / KEEP OPEN | ☐ |
| 2 | `manage` / `write` 是否映射？映射为哪个 canonical action？ | ACCEPT OPTION（映射到 `admin`/`update`…）/ CUSTOM / KEEP OPEN | ☐ |
| 3 | `system.*` 是否纳入？ | ACCEPT / CUSTOM / KEEP OPEN（NEED MORE EVIDENCE） | ☐ |
| 4 | deny 行是否存在及其具体分配？ | ACCEPT（需给出分配）/ CUSTOM / KEEP OPEN | ☐ |
| 5 | `resource_type` 是否需要受限词表？ | ACCEPT（建词表）/ CUSTOM / KEEP OPEN | ☐ |

> **在 Human 裁定之前：禁止生成 permissions seed。** 本文件不提供建议映射。
<!-- /SRC -->

```text
⚠ 原文**未定义** Option A/B/C —— 本 OQ 的裁定面为上述 5 个问题。
  按 §2 HARD RULE「不得新增 Option」，此处**不构造** Option A/B/C。
```

### 2.2 Evidence（原文 §1「证据原样呈现（未修正候选）」块）

<!-- SRC:SHEET:49-63 -->
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
<!-- /SRC -->

### 2.3 候选清单实际内容（13 项 · 逐字引自 `EVID` §1.2：key / 隐含 action / resource_type / is_system / 词表判定）

<!-- SRC:EVID:52-79 -->
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
<!-- /SRC -->

```text
⚠ deny 配置：原文 = NOT FOUND / OPEN（SEED_STRATEGY §1[10] 仅提及 role_permissions「含 deny 行」，
  无任何权威分配清单）—— **不得**据此推导 deny 行。
⚠ `system.*`：原文 = INSUFFICIENT EVIDENCE（形状占位，无具体 action）。
⚠ resource_type 词表：原文 = UNKNOWN（permissions.resource_type 无 CHECK、无文档清单）。
```

### 2.4 兼容性证据（逐字引自 `EVID` §1.3 · 实测 @0015）

<!-- SRC:EVID:81-94 -->
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
<!-- /SRC -->

### 2.5 草稿原始出处（逐字引自 `SEED` §4「初始 permissions 字典（seed 示例，B1 定稿）」）

<!-- SRC:SEED:90-110 -->
## 4. 初始 permissions 字典（seed 示例，B1 定稿）

seed 仅注入**平台级系统权限**；域级权限由 Domain 层注册（不在本阶段）：

```
system.*                    平台系统操作
tenant.read / tenant.manage
space.read  / space.manage
member.read / member.manage
resource.read / resource.write / resource.delete
agent.execute / tool.execute
audit.read
```

> 具体清单 B1 定稿前由人工审计确认 —— 本文档只给形状：`key` 满足正则 `^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$`；`is_system=true`。

> **边界声明（O-5 澄清，非规范性，不改变任何冻结决策）**：上列示例属于**未来 `permissions` 表（平台级权限字典，P13）**的 seed 草稿，**仅用于说明 `key` 的形状**；
> **不构成 B1-4 `resource_permissions.action` 的 vocabulary 冻结**，亦不得迁移为该列的取值约束（后者当前**仅 NOT NULL**，语义未冻结；**D-B14-08 = FROZEN — A（2026-09-13）**：B1-4 **零新增 semantic/format contract**）。

---

<!-- /SRC -->

### 2.6 字段对照（原文未定义者一律登记，不补造）

| 要求字段 | 原文状态 |
|---|---|
| Question | **有** —— §1 5 问表（见 2.1） |
| Evidence | **有** —— §1 证据块（2.2）+ `EVID` §1.2 候选表（2.3）+ §1.3 兼容性证据（2.4） |
| Option A / B / C | **原文未定义**（⇒ 按 HARD RULE 不新增） |
| Engineering Impact | **原文未定义**（`SHEET` §1 无此字段） |
| Compatibility Impact | **原文未定义**；最近源材料 = `EVID` §1.3（见 2.4） |
| Future Runtime Impact | **原文未定义**（`SHEET` §1 无此字段） |
| Recommended Direction | **原文明确不提供**：`本文件不提供建议映射。`（逐字，见 2.1 块末行） |
| Current HUMAN DECISION | `PENDING`（`SHEET` §0 状态表） |
| Status | `PENDING`（`SHEET` §0 状态表） |

### 2.7 已确认事实（原文口径，不得改写）

```text
`manage` ∉ D-AUTH-05 canonical action vocabulary（原文：✗ `manage` ∉ 12 词表）
`write`  ∉ D-AUTH-05 canonical action vocabulary（原文：✗ `write` ∉ 12 词表）
ck_permissions_action_canonical 将拒绝非法 action 的 seed row（DB 层实证）
system.* 证据充分性 = 按原文：INSUFFICIENT EVIDENCE
resource_type 词表状态 = 按原文：UNKNOWN / OPEN
映射（如 manage→admin / write→update）在原文中仅为**带问号的举例**，状态 = OPEN，**非事实**
```

---

## 3. `OQ-P13-12` — seed downgrade ownership / provenance（**BLOCKING** · 需裁定）

### 3.1 三候选（完整展示 · 原文 §2）

<!-- SRC:SHEET:81-87 -->
### 三候选（完整展示）

| 候选 | 机制 | 一句话 |
|---|---|---|
| **Candidate A — key-marker** | 使用明确的数据标记，使 migration-owned seed 与 runtime-created row 可区分 | 需先解决「当前无任何行级标记」的事实缺口 |
| **Candidate B — NO-OP** | P13 downgrade 不删除相关 seed rows，仅回滚 schema | 零误删风险；牺牲 downgrade 对称性 |
| **Candidate C — fail-closed** | downgrade 检测到无法可靠区分 ownership 时直接失败，不执行潜在误删 | 与 FAIL-CLOSED 族同向；有 runtime 数据后不可回退 |
<!-- /SRC -->

### 3.2 逐候选回答五问（原文 §2 · 三张表逐字，未合并未删减）

<!-- SRC:SHEET:89-119 -->
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
<!-- /SRC -->

### 3.3 核心结论 + 支撑事实（原文 §2 · 原样）

<!-- SRC:SHEET:121-128 -->
### 核心结论（必须保持，原样）

> **「这是 migration 创建的，因此 downgrade 可以安全删除」目前没有数据层证据证明。**

**支撑事实（实测 @0015）**：users/tenants/spaces/resources 有 soft-delete 字段（`deleted_at`）· roles/agents **无**对应字段 ·
`is_system` 仅存在于角色字典语义，**不能直接证明 P13 seed ownership** · FK RESTRICT 网络**不能证明**「该行由 migration 创建」·
`platform_state` 提供一次性状态机先例，**不等同于 seed provenance** · `audit_logs` immutable，**不适合作为简单 ownership marker** ·
全库**没有** seed_batch / migration_owned 等现成行级标记。
<!-- /SRC -->

### 3.4 裁定栏（原文 §2 · **不得由 Bot 自行选择 A/B/C**）

<!-- SRC:SHEET:130-138 -->
**裁定栏（不得由 Bot 自行选择 A/B/C）**：

| 候选 | 裁定 |
|---|---|
| ACCEPT OPTION A（key-marker，含标记机制定义） | ☐ |
| ACCEPT OPTION B（NO-OP） | ☐ |
| ACCEPT OPTION C（fail-closed） | ☐ |
| CUSTOM DECISION（原样记录 Human 决策内容） | ☐ |
| KEEP OPEN / NEED MORE EVIDENCE | ☐ |
<!-- /SRC -->

### 3.5 裁定交互格式与禁用声明（原文 §4 · 逐字）

<!-- SRC:SHEET:256-282 -->
**允许的结果**（必须明确记录，不得改写）：

```text
ACCEPT OPTION A            ACCEPT OPTION B            ACCEPT OPTION C
CUSTOM DECISION            KEEP OPEN / NEED MORE EVIDENCE
```

**决策登记表（Human 逐项填写；Bot 不得代填）**：

| OQ | 当前状态 | 裁定结果（Human 填） | 备注 / CUSTOM 原文 |
|---|---|---|---|
| 01 | PENDING |  |  |
| 02 | READY |  |  |
| 03 | FROZEN | —（仅核验，不得改写） |  |
| 04 | READY |  |  |
| 05 | READY |  |  |
| 06 | FROZEN | —（仅核验，不得改写） |  |
| 07 | READY |  |  |
| 08 | READY |  |  |
| 09 | READY |  |  |
| 10 | READY |  |  |
| 11 | READY |  |  |
| 12 | BLOCKING |  |  |
| 13 | FROZEN | —（仅核验，不得改写） |  |
| 14 | READY |  |  |

> **CUSTOM DECISION 必须原样记录** —— 不得由 Bot 改写成看似相近的工程结论。
<!-- /SRC -->

> 上述登记表为**空白**（原文即如此）—— 本文件**不代填**。

---

## 4. `OQ-P13-02` — System role ownership（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:144-154 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:148 -->
Option A: `platform_admin` 归 0005（P13 仅校验存在）、tenant/space 四角色随首租户/首空间补种
Option B: 全部重种
Option C: 四角色全推 runtime onboarding。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

## 5. `OQ-P13-04` — Agent subject seed（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:156-166 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:160 -->
Option A: 注册 subject type，0 个实际 Agent
Option B: 连演示 Agent 一起种。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

## 6. `OQ-P13-05` — Bootstrap tenant（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:168-178 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:172 -->
Option A: 入 seed（slug 需 Human 定名）
Option B: 不入（CLI/Runtime 建 + 角色随播）。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

## 7. `OQ-P13-07` — Platform membership（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:180-190 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:184 -->
Option A: 维持 R4/R5（CLI，非 P13）
Option B: P13 seed 写 PM。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

## 8. `OQ-P13-08` — Tenant / space membership（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:192-202 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:196 -->
Option A: 随首租户/首空间入 seed
Option B: 推 runtime。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

## 9. `OQ-P13-09` — Seed ordering（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:204-214 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:208 -->
Option A: 照 §1 顺序（registry → permissions → roles 校验 → tenant → tenant 角色 → tenant_membership → space → space 角色 → membership → role_permissions）
Option B: 其它拓扑。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

## 10. `OQ-P13-10` — Idempotency（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:216-226 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:220 -->
Option A: registry/permissions 用 WHERE NOT EXISTS、memberships/role_permissions 冲突即失败
Option B: 统一 ON CONFLICT DO NOTHING。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

## 11. `OQ-P13-11` — Trigger interaction（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:228-238 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:232 -->
Option A: 按确认 + 实施期逐触发器行为测试
Option B: 临时禁用其它触发器。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

## 12. `OQ-P13-14` — Runtime-created data protection（READY FOR HUMAN DECISION）

> **原文九字段块（逐字）**：

<!-- SRC:SHEET:240-250 -->
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
<!-- /SRC -->

> **Option 拆行（按原文自身 `**A** =` / `**B** =` / `**C** =` 标注机械拆分 · 文本逐字未改写）**：

<!-- OPTSPLIT:SHEET:244 -->
Option A: 不加 marker，靠 key 过滤 + fail-closed（与 OQ-12=C 组合）
Option B: `seed_batch` 标记列（schema 变更，超 P13 范围）
Option C: seed 行写专用 audit 事件登记。
<!-- /OPTSPLIT -->

> `Recommended Direction` 原文标注 **≠ Human Decision** ⇒ 不构成裁定。

---

## 13. 状态守卫核验（本轮实测）

```text
D-P13-01 … D-P13-14 = NOT WRITTEN      P13 DECISION FREEZE = BLOCKED
P13 IMPLEMENTATION  = NOT AUTHORIZED   0016+ = ABSENT
DDL = 0 · DML = 0 · seed INSERT = 0 · runtime = NOT AUTHORIZED
commit = 0 · tag = 0 · push = 0
```

---

## 14. HUMAN DECISION INPUT（纯输入区 · 请直接填写）

```text
================ HUMAN DECISION INPUT ================

OQ-P13-01 = ______________________

OQ-P13-02 = ______________________

OQ-P13-04 = ______________________

OQ-P13-05 = ______________________

OQ-P13-07 = ______________________

OQ-P13-08 = ______________________

OQ-P13-09 = ______________________

OQ-P13-10 = ______________________

OQ-P13-11 = ______________________

OQ-P13-12 = ______________________

OQ-P13-14 = ______________________

允许值（原文 §4）：
ACCEPT OPTION A          ACCEPT OPTION B          ACCEPT OPTION C
CUSTOM DECISION          KEEP OPEN / NEED MORE EVIDENCE
```

---

**END OF P13 HUMAN DECISION EXTRACTION（2026-09-26 · READ-ONLY · 未冻结 · 未实施）**
