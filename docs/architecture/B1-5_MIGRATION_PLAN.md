# B1-5 — Migration Plan（PREP）

Status: **PREP / PLAN — NO migration created in PREP · NO DDL · NO DML**

---

## 1. Revision 元信息

| 项 | 值 |
|---|---|
| 预计 revision id | `0008_b1_5_tool_registry`（命名待定，风格对齐 `0007_b1_4_resource_acl`） |
| 实施前提 | **9 项 Decision 已全部 FROZEN — A**（2026-09-14）⇒ 剩余条件 = **FINAL PREP GATE + 显式实施授权**（`APPROVE B1-5 IMPLEMENTATION`） |
| `down_revision` | `0007_b1_4_resource_acl` |
| 当前 head（基线条） | `0007_b1_4_resource_acl` |
| 单事务 | **是**（沿用 B1-0 Migration Contract） |
| 本轮创建 | ❌ **不创建** |

---

## 2. upgrade 顺序（7 步）

```
[1] 建表 tools
      · 列（15 列：id/tenant_id/key/name/description/risk_level/timeout_ms/
        retry_policy/idempotency_mode/audit_policy/approval_required/enabled/
        disabled_at/created_at/updated_at）
      · PK(id) · FK(`tenant_id NULL → tenants.id ON DELETE RESTRICT`)〔**D-B15-02 = FROZEN — A**（NULL = 平台级 Tool）〕
      · CK ×4（risk_level / timeout_ms / idempotency_mode / audit_policy）
      · 部分唯一索引 ×2（uq_tools_platform / uq_tools_tenant）

[2] 建表 tool_versions
      · 列（12 列）
      · PK(id) · FK(tool_id → tools.id CASCADE) · UQ(tool_id, version)

[3] 建表 tool_permissions
      · 列（7 列）
      · PK(id) · FK ×3（tool_id CASCADE / version_id CASCADE / permission_id CASCADE）
      · CK ×1（effect）· unique INDEX uq_tool_perm（表达式 COALESCE）

[4] function
      · CREATE FUNCTION enforce_tool_versions_immutable()
        （RAISE 型，风格对齐 enforce_acl_subject_types_protect）

[5] trigger（2 个）
      · tg_tools_set_updated_at        BEFORE UPDATE ON tools
                                       → EXECUTE FUNCTION set_updated_at()   ← 复用 P00
      · tg_version_immutable     BEFORE UPDATE OR DELETE ON tool_versions
                                       → EXECUTE FUNCTION enforce_tool_versions_immutable()

[6] 校验（migration 内不做业务校验；由测试承担）

[7] seed
      · 无（B1-5 = 零 seed；P13 才有 seed）
```

**依赖顺序依据**：`B1-5_DEPENDENCY.md` §2 拓扑序（tools → tool_versions → tool_permissions）。

---

## 3. downgrade 顺序（严格逆序，无 orphan）

```
[1] DROP TRIGGER tg_version_immutable ON tool_versions
[2] DROP TRIGGER tg_tools_set_updated_at     ON tools
[3] DROP FUNCTION IF EXISTS enforce_tool_versions_immutable()
[4] DROP INDEX  IF EXISTS uq_tool_perm
[5] DROP TABLE  IF EXISTS tool_permissions
[6] DROP TABLE  IF EXISTS tool_versions
[7] DROP TABLE  IF EXISTS tools
```

**不 DROP**：
- `set_updated_at()`（P00 共用，B1-1~B1-4 依赖）
- `uap_uuid_v7()`（P00 共用）
- 任何 B1-0~B1-4 既有对象

> 注：`uq_tools_platform` / `uq_tools_tenant` / `uq_tool_versions` 随 `DROP TABLE` 自动移除，无需显式 DROP。

---

## 4. 幂等与可逆性要求

| 要求 | 说明 |
|---|---|
| 可逆 | downgrade 后回到 `0007` 状态：B1-5 三表/2 trigger/1 function/全部索引 = 0 残留 |
| 不破坏历史语义 | 不改 `0001`–`0007` 任何对象；`set_updated_at` / `uap_uuid_v7` 唯一实例保持 |
| 单事务 | 失败整体回滚，无半成品 schema |
| 不新建旧函数 | `set_updated_at` **复用**，不 `CREATE OR REPLACE` 覆盖 |

---

## 5. 迁移护栏（Production Guard）

| 项 | 状态 |
|---|---|
| P3-3（裸 `alembic upgrade head` 指向正式库） | **KEEP DEFERRED**（既有控制缺口，B1-4 已登记） |
| B1-5 实施阶段要求 | **禁止**裸 `alembic upgrade head`；必须以显式 URL / `config.attributes["url"]` 指向 **disposable 库**（沿用 `tests/integration/alembic_testkit.py` 机制） |
| formal `uap` 库 | **全程保持 0 tables**（PREP 阶段已确认） |
| 本轮 | 不执行任何 upgrade/downgrade |

---

## 6. 影响面预判

| 项 | 变化 |
|---|---|
| 业务表数 | 17 → **20**（+3） |
| 物理表数 | 18 → **21**（+3；`alembic_version` 不变） |
| 新增 trigger | +2（累计 B1-5 域内 2 个；G/H/I/J 仍 0） |
| 新增 function | +1 |
| 既有测试影响 | 预计 **W-2 类夹具更新**：硬断言 `head == 0007_b1_4_resource_acl` 的测试需更新为 `0008`；期望表集合需增 3 表（**实施阶段处理，PREP 不改测试**） |
| B1-4 canonical count（84） | **不变** —— B1-5 使用独立编号空间 |

---

## 7. 本轮禁止事项（重申）

```
NO migration created      ✅ 已遵守
NO DDL                    ✅ 已遵守
NO DML                    ✅ 已遵守
NO 修改 0001–0007         ✅ 已遵守
NO 修改 env.py            ✅ 已遵守
NO 修改 B1-4 sealed files ✅ 已遵守
```
