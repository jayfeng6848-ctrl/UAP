# UAP — P11 IMPLEMENTATION CONTRACT（Triggers / Cross-table Constraints）

> ## 状态
>
> ```text
> DESIGN FROZEN
> IMPLEMENTATION AUTHORIZED（2026-09-26 Human Authorization）
> IMPLEMENTED · ACCEPTED（0014_p11_triggers）
> ```
>
> **本文件是设计契约，不是实施记录**。本轮为 **READ-ONLY / IMPLEMENTATION CONTRACT PREPARATION**：
> **未创建任何 migration / trigger / function**；**未执行任何 DDL / DML**；**未修改任何 code / test / config**。
> `P11 IMPLEMENTATION = NOT AUTHORIZED` · `P12 IMPLEMENTATION = NOT AUTHORIZED` ·
> `P13 = NOT AUTHORIZED` · `Runtime Implementation Gate = CLOSED`。
> 实施期唯一入口 = `0014_p11_triggers`（§8），验收口径 = `P11_IMPLEMENTATION_ACCEPTANCE_MATRIX.md`。

---

## 1. 权威基础（Authoritative Frozen Basis）

| 来源 | 用途 |
|---|---|
| `D-P11-01 … D-P11-14`（`PLATFORM_DECISION_LOG.md` §P11，全部 FROZEN 2026-09-25） | **唯一语义权威**：scope / 语义 / timing / 失败语义 / 安全 / 递归 / 三向边界 |
| `P11_DECISION_RESOLUTION.md`（17 节 · EXIT CHECK PASSED） | OQ → D-P11 的裁定链 |
| `P11_PREP_REPORT.md`（24 CREATE TRIGGER 语句 / 8 migration 实测） | 既有触发器物量与 GAP-INV-1 |
| `P11_ACCEPTANCE_MATRIX.md` | 冻结轮验收口径 |
| `D-P10-01 … D-P10-18` · `P10_IMPLEMENTATION_CONTRACT.md`（含 §16 实施记录） | P10 交付事实与 P10/P11 边界 |
| `STEP1B_TRIGGER_INVENTORY.md` §G/§H/§I/§J（原始语义） | G/H/I/J 的原始定义（经 `D-P11-02` 冻结吸收） |
| `STEP1B_SCHEMA_DEPENDENCY.md` / `STEP1B_CONSTRAINT_MATRIX.md` / `STEP1B_INDEX_STRATEGY.md` / `STEP1B_SEED_STRATEGY.md` | 依赖、不变量、索引与 seed 边界 |
| `migrations_alembic/versions/0013_p10_event_audit.py`（sha256 `da1bdffd4ddd2202…`） | `down_revision` 锚点与"不得修改"对象 |

**P10 现状确认（实测，2026-09-26）**：

```text
P10 implementation = actually present   （0013 已入库；测试库 current = 0013_p10_event_audit；
                                         events 22 列 / audit_logs 19 列 / tg_audit_immutable 在位）
P10 acceptance = PASS                   （p10_impl_acceptance.log 12/12 · 596 passed / 0 failed）
P10/P11 boundary = intact               （audit_logs / events 上除 L 外零 trigger —— §5 逐条复核）
```

---

## 2. 基线与实测清单（Contract 轮实测 · 2026-09-26）

### 2.1 Baseline

```text
HEAD      = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e（tag UAP-V0.1.8-AUTHORIZATION）
tags = 8 · remote = none · 新 commit 未授权（工作树含 P10 轮未提交变更 = 轮次起始快照）
alembic   = 单头 0013_p10_event_audit（链长 13）· 0014+ = ABSENT
protected = 0010 6d9907237f80e9da · 0011 cdaf8383630335db · 0012 5ecd1ef30b403fb4（逐字节未变）
0013      = da1bdffd4ddd2202（P10 交付 · 本轮只读）
```

### 2.2 既有触发器实测（测试库 @0013 · `tgparentid = 0` 父级口径）

```text
父级触发器 = 35 · 触发器函数 = 17（16 个 enforce_*/专用 + 1 个共享 set_updated_at）
SECURITY DEFINER = 0（全部 prosecdef=false）· SET search_path = 0
CREATE TRIGGER 语句（迁移源内）= 24（8 migration）· P11 后 = 28
```

| 字母 | 触发器 | 表 | 相位 | 来源 |
|---|---|---|---|---|
| A | `tg_*_set_updated_at` ×16 | 各带 `updated_at` 表 | BEFORE UPDATE | 各表建时 |
| B/C | `tg_roles_scope_shape` / `tg_roles_is_system_protect` | roles | BEFORE I/U · BEFORE I/U/D | 0004 |
| C2 | `tg_acl_subject_types_protect` | acl_subject_types | BEFORE I/U/D | 0007 |
| D/E/F | `tg_tm_role_scope` / `tg_membership_role_scope` / `tg_membership_tenant_consistency` | tenant_memberships / memberships | BEFORE I/U | 0005 |
| F2 | `tg_resources_tenant_space_consistency` | resources | BEFORE I/U | 0007 |
| K | `tg_version_immutable` ×2 | agent_versions / tool_versions | BEFORE U/D | 0008 / 0011 |
| GAP-INV-1（6 个，非 letter） | `tg_pm_role_scope` · `tg_pm_last_admin` · `tg_roles_pm_lifecycle` · `tg_platform_state_guard` · `tg_pm_bootstrap_gate` · `tg_agents_tenant_space_consistency` | platform_memberships / roles / platform_state / agents | 见 0005/0006/0011 | 0005 ×4 · 0006 ×2 中 2 · 0011 ×1 |
| **L** | **`tg_audit_immutable`** | **audit_logs** | **BEFORE U/D** | **0013（P10-owned）** |
| G/H/I/J | **不存在（实测 0 命中）** | — | — | **P11 = 本契约** |

### 2.3 同表碰撞分析（§12 要求 · 实测 `pg_get_triggerdef`）

| 目标表 | 既有触发器（相位） | P11 新增 | 碰撞结论 |
|---|---|---|---|
| `resource_permissions`（G） | **无任何触发器** | G = BEFORE INSERT OR UPDATE OF(subject_type_id, subject_id) | **无碰撞**；G 为该表首个触发器 |
| `users`（H） | `tg_users_set_updated_at`（BEFORE UPDATE） | H = AFTER DELETE | **无碰撞**（事件不相交） |
| `roles`（I） | `tg_roles_is_system_protect`（BEFORE I/U/D）· `tg_roles_pm_lifecycle`（**BEFORE DELETE OR UPDATE OF status**）· `tg_roles_scope_shape`（BEFORE I/U）· `tg_roles_set_updated_at`（BEFORE UPDATE） | I = BEFORE DELETE | **同相位共存（见下）** |
| `agents`（J） | `tg_agents_set_updated_at`（BEFORE UPDATE）· `tg_agents_tenant_space_consistency`（BEFORE I/U） | J = AFTER UPDATE OF status OR AFTER DELETE | **无碰撞**（AFTER vs BEFORE） |

**I 与 roles 既有 BEFORE DELETE 触发器的行为级兼容分析（冻结要求）**：

```text
1. 三个 BEFORE DELETE 触发器（tg_acl_role_delete_block / tg_roles_is_system_protect /
   tg_roles_pm_lifecycle）按 PG 语义以【名称字典序】依次触发；任一 RAISE 均使整条
   DELETE 语句失败回滚（D-P11-04），故触发次序不影响最终可删性判定。
2. 判定条件互不重叠：I 看 ACL 引用（resource_permissions）；is_system_protect 看
   is_system；pm_lifecycle 看 platform_admin 的 active platform_memberships 绑定。
   I 不读、不判定、不改写后两者的条件 ⇒ 无语义干扰。
3. I 通过时 RETURN OLD（不短路后续触发器）；I 拒绝时 RAISE ⇒ 与既有两个触发器的
   拒绝路径等价（同一失败语义）。
4. 命名不冲突：tg_acl_role_delete_block 字典序最前 ⇒ 最先执行（仅性能面，非语义面）。
结论：行为级兼容 ✅（实施后须以行为测试复核本分析 —— 矩阵 TRIG-24）
```

### 2.4 命名冲突检查（实测 `pg_proc` / `pg_trigger`）

```text
enforce_acl_subject_exists / enforce_acl_user_hard_delete /
enforce_acl_role_delete_block / enforce_agent_acl_expire   = 0 命中 ✅
tg_acl_subject_exists / tg_acl_user_hard_delete /
tg_acl_role_delete_block / tg_agent_acl_expire             = 0 命中 ✅
```

---

## 3. G/H/I/J 逐项契约（语义权威 = `D-P11-02`）

> 以下函数体为**设计级规范**（实施期按此落 `0014`，命名/结构不得偏离；错误消息文案允许微调）。
> 语言一律 `LANGUAGE plpgsql`；默认 **SECURITY INVOKER**（§7）；每个函数只依赖其目标表与
> 冻结允许的查找表，**不引用 `groups`**，**不做授权求值**。

### 3.1 G — `tg_acl_subject_exists`

```text
table  = resource_permissions
timing = BEFORE INSERT OR UPDATE OF subject_type_id, subject_id
FOR EACH ROW
```

```sql
CREATE OR REPLACE FUNCTION enforce_acl_subject_exists() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_key text;
BEGIN
    -- subject type 必须已注册（FK 已拦"不存在的 type 行"，此处为纵深防御 + key 词表闸门）
    SELECT key INTO v_key FROM acl_subject_types WHERE id = NEW.subject_type_id;
    IF v_key IS NULL THEN
        RAISE EXCEPTION 'acl subject type % is not registered', NEW.subject_type_id;
    END IF;
    IF v_key = 'user' THEN
        IF NOT EXISTS (SELECT 1 FROM users  WHERE id = NEW.subject_id) THEN
            RAISE EXCEPTION 'acl subject user % does not exist', NEW.subject_id;
        END IF;
    ELSIF v_key = 'role' THEN
        IF NOT EXISTS (SELECT 1 FROM roles WHERE id = NEW.subject_id) THEN
            RAISE EXCEPTION 'acl subject role % does not exist', NEW.subject_id;
        END IF;
    ELSIF v_key = 'agent' THEN
        IF NOT EXISTS (SELECT 1 FROM agents WHERE id = NEW.subject_id) THEN
            RAISE EXCEPTION 'acl subject agent % does not exist', NEW.subject_id;
        END IF;
    ELSE
        RAISE EXCEPTION 'unregistered acl subject type key %', v_key;
    END IF;
    RETURN NEW;
END;
$$;
```

```text
职责边界（冻结）：
  必须  reject nonexistent subject（user/role/agent 三向存在性）
        reject unregistered subject type（type 行不存在 / key ∉ {user,role,agent}）
  禁止  引用 groups（P2-02 · D-P11-02）
        authorization evaluation / DENY-ALLOW 计算 / 跨租户策略判定（D-P11-07）
        —— G = subject existence ≠ subject is authorized
```

### 3.2 H — `tg_acl_user_hard_delete`

```text
table  = users
timing = AFTER DELETE
FOR EACH ROW
```

```sql
CREATE OR REPLACE FUNCTION enforce_acl_user_hard_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM resource_permissions rp
     WHERE rp.subject_id = OLD.id
       AND rp.subject_type_id = (SELECT id FROM acl_subject_types WHERE key = 'user');
    RETURN NULL;   -- AFTER ROW 触发器返回值被忽略
END;
$$;
```

```text
职责边界（冻结）：
  只针对【硬删除】清理该 user 的 ACL 行（subject_type = user）。
  软删除（UPDATE archived_at 等）不触发 AFTER DELETE ⇒ ACL 保留 ✅（行为测试 SEC-BEH-02）
  不删 role ACL · 不删 agent ACL · 不删其他 subject 的 ACL（WHERE 双条件限定）
  内部 DELETE 失败 ⇒ 整个外层硬删事务回滚（D-P11-04）
```

### 3.3 I — `tg_acl_role_delete_block`

```text
table  = roles
timing = BEFORE DELETE
FOR EACH ROW
```

```sql
CREATE OR REPLACE FUNCTION enforce_acl_role_delete_block() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM resource_permissions rp
                WHERE rp.subject_id = OLD.id
                  AND rp.subject_type_id = (SELECT id FROM acl_subject_types
                                             WHERE key = 'role')) THEN
        RAISE EXCEPTION 'role % is still referenced by resource_permissions', OLD.id;
    END IF;
    RETURN OLD;    -- 未被引用 ⇒ 允许删除（不短路后续触发器）
END;
$$;
```

```text
性质（冻结）：ACL reference protection（复刻 RESTRICT 语义），不是授权求值器。
兼容性：与 roles 既有 3 个 BEFORE DELETE 触发器行为级兼容（§2.3 分析）。
```

### 3.4 J — `tg_agent_acl_expire`

```text
table  = agents
timing = AFTER UPDATE OF status OR AFTER DELETE
FOR EACH ROW
```

```sql
CREATE OR REPLACE FUNCTION enforce_agent_acl_expire() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    -- 仅"归档"这一 status 迁移使 ACL 到期；其他 status 变更不动作
    IF TG_OP = 'UPDATE' AND NEW.status <> 'archived' THEN
        RETURN NULL;
    END IF;
    UPDATE resource_permissions
       SET inherited = true, expires_at = now()
     WHERE subject_id = OLD.id
       AND subject_type_id = (SELECT id FROM acl_subject_types WHERE key = 'agent');
    RETURN NULL;
END;
$$;
```

```text
职责边界（冻结 D-P11-02 / D-P11-09）：
  agent archived（status → 'archived'）或删除 ⇒ 其 agent ACL 行：
      inherited = true · expires_at = now()   （数据保留，仅失效）
  严格禁止：修改 subject_type_id / subject_id（⇒ 不会触发 G，可测断言）
            删除 ACL 行 · 调用授权引擎 · 删除 agent 行本身
  J 不区分 OLD/NEW.id：agents.id 为 PK 不可变，UPDATE 时 OLD.id = NEW.id
  J 的隐藏 DML 不写 audit（D-P11-14）；J→G 递归 = 无（SET 列表不含 G 监听列）
```

### 3.5 触发器挂载语句（设计规范）

```sql
CREATE TRIGGER tg_acl_subject_exists
    BEFORE INSERT OR UPDATE OF subject_type_id, subject_id
    ON resource_permissions FOR EACH ROW EXECUTE FUNCTION enforce_acl_subject_exists();

CREATE TRIGGER tg_acl_user_hard_delete
    AFTER DELETE ON users FOR EACH ROW EXECUTE FUNCTION enforce_acl_user_hard_delete();

CREATE TRIGGER tg_acl_role_delete_block
    BEFORE DELETE ON roles FOR EACH ROW EXECUTE FUNCTION enforce_acl_role_delete_block();

CREATE TRIGGER tg_agent_acl_expire
    AFTER UPDATE OF status OR AFTER DELETE ON agents
    FOR EACH ROW EXECUTE FUNCTION enforce_agent_acl_expire();
```

预期 `tgtype` 位（验收用 · ROW=1 BEFORE=2 INSERT=4 DELETE=8 UPDATE=16）：

```text
G = 23（1+2+4+16，含 UPDATE OF 列清单）· H = 9（1+8，AFTER）
I = 11（1+2+8）· J = 25（1+8+16，AFTER U/D）
```

---

## 4. Function 安全设计（`D-P11-08` / 指令 §7）

```text
SECURITY INVOKER  = canonical（不写该子句 = 默认 INVOKER，与既有 17 个函数一致）
SECURITY DEFINER  = 0（全仓实测 0，P11 不得引入）
SET search_path   = 0（函数体遵循 0011 先例：对象名不限定 schema、依赖会话 search_path；
                      实施后须以 pg_get_functiondef 断言无 search_path 设置 —— 矩阵 SEC-03）
unqualified refs  = 与既有先例一致（enforce_roles_scope_shape 等同样直接引用表名）
privilege escalation = 无（INVOKER 语义下函数以调用者权限执行；无 DDL、无 GRANT、无角色操作）
trigger recursion = G/H/I 无隐藏 DML；J 的 UPDATE SET 列表 = {inherited, expires_at}
                    ⊄ G 监听列 {subject_type_id, subject_id} ⇒ J 不触发 G（D-P11-09）
                    H 的 DELETE 不命中 G（G 无 DELETE 事件）
transaction rollback = 全部 RAISE → 当前事务失败回滚（D-P11-04 · 与 D-AUTH-12 FAIL CLOSED 同向）
禁写面            = 4 个函数均不 INSERT/UPDATE/DELETE audit_logs，不触碰 events / outbox
```

---

## 5. P10 边界（`D-P11-10`）

```text
P11 不得 CREATE/MODIFY audit_logs trigger        ⇒ 本契约 4 个目标表不含 audit_logs ✅
P11 不得 CREATE/MODIFY events trigger            ⇒ 不含 events ✅（OBX5 断言保持）
P11 不得 replace tg_audit_immutable              ⇒ 0013 逐字节未动（§8）✅
P11 不写 audit 行                                 ⇒ 4 个函数无 audit_logs 写路径 ✅
P11 不改 outbox 行为                              ⇒ 不触碰 events 任何列 ✅
tg_audit_immutable = P10-owned（D-P10-11，未 supersede）—— 实施后归属复核 = 矩阵 P10B-03
```

---

## 6. P12 边界与性能 Handoff（`D-P11-11` · 指令 §13）

```text
P11 migration 内 index = 0（CREATE/DROP INDEX = 0）· 不得将 0015 提前进入 0014
P11 语义正确性不依赖 P12（全部查找路径已有既有索引承载 ⇒ 下方 handoff 表无新增缺口）
```

**trigger → required lookup → P12 index dependency（逐项实测）**

| Trigger | 查找路径 | 承载索引 | 状态 |
|---|---|---|---|
| G | `acl_subject_types(id)` · `users(id)` · `roles(id)` · `agents(id)` | 各表 PK（`_pkey`） | **已覆盖** |
| G/H/I/J 公共反查 | `resource_permissions(subject_type_id, subject_id)` | **`ix_rp_subject`**（0007 / P06 已建，实测在位） | **已覆盖** |
| H | `users(id)`（OLD.id） | PK | **已覆盖** |
| I | `roles(id)`（OLD.id） | PK | **已覆盖** |
| J | `agents(id)`（OLD.id） | PK | **已覆盖** |

```text
P12 新增依赖 = 0（D-P11-11 依据栏的"现状无缺口"实测成立）
注：ix_rp_subject 为 P06 交付（不在 P12 CREATE 清单内），本表仅登记"被 P11 复用"。
```

---

## 7. P13 边界（`D-P11-12`）

```text
P11 migration seed = 0：禁 INSERT acl_subject_types / bootstrap user / bootstrap role /
                       agent subject seed / 任何业务行（含"为便于自测"的携带 seed）
时序要求：G/H/I/J 必须在 P13 seed 之前挂载（0014 在 0015/0016 之前 ⇒ 链序天然满足）
实施后验证：4 个触发器存在性（head @0014）先于任何 P13 seed 行为 —— 矩阵 P13B-01/02
```

---

## 8. 迁移设计 —— `0014_p11_triggers`（只写不建）

```python
revision     = "0014_p11_triggers"      # 16 字符 ≤ 32；filename == revision
down_revision = "0013_p10_event_audit"  # D-PLAT-09 链序（NUM-1 冻结分配）
branch_labels = None
depends_on    = None                    # ⇒ 单头 0014_p11_triggers（链长 14）
```

**upgrade 顺序**（依赖决定：函数必须先于触发器；4 对触发器相互独立，按 G→H→I→J 固定序）：

```text
1. CREATE OR REPLACE FUNCTION enforce_acl_subject_exists()
2. CREATE OR REPLACE FUNCTION enforce_acl_user_hard_delete()
3. CREATE OR REPLACE FUNCTION enforce_acl_role_delete_block()
4. CREATE OR REPLACE FUNCTION enforce_agent_acl_expire()
5. CREATE TRIGGER tg_acl_subject_exists      ON resource_permissions   （G）
6. CREATE TRIGGER tg_acl_user_hard_delete    ON users                  （H）
7. CREATE TRIGGER tg_acl_role_delete_block   ON roles                  （I）
8. CREATE TRIGGER tg_agent_acl_expire        ON agents                 （J）
```

**downgrade 顺序（严格逆序）**：

```text
1. DROP TRIGGER tg_agent_acl_expire      ON agents
2. DROP TRIGGER tg_acl_role_delete_block ON roles
3. DROP TRIGGER tg_acl_user_hard_delete  ON users
4. DROP TRIGGER tg_acl_subject_exists    ON resource_permissions
5. DROP FUNCTION enforce_agent_acl_expire()
6. DROP FUNCTION enforce_acl_role_delete_block()
7. DROP FUNCTION enforce_acl_user_hard_delete()
8. DROP FUNCTION enforce_acl_subject_exists()
```

```text
对象清单 = 4 trigger + 4 function（表 0 · 列 0 · 索引 0 · seed 0 · FK 0 · CHECK 0）
禁项     = 不得修改 0013_p10_event_audit · 禁 CONCURRENTLY · 禁 RLS / GRANT /
           SECURITY DEFINER / SET search_path / DEFAULT 分区 / 任何 seed
零残留   = downgrade 后 8 个对象全部消失，物理表数回到 35（含 alembic_version），
           其余对象集与轮前逐项一致（往返哈希断言 —— 矩阵 DOWNG/RT 组）
```

---

## 9. 既有对象保护（指令 §12）

```text
既有 24 条 CREATE TRIGGER（8 migration）+ L（0013）语义不变：实施前后以
"父级触发器全清单（tgparentid=0）+ 定义哈希"两次比对证明 —— 除 +4（G/H/I/J）外逐项一致
不得重复函数名 / 触发器名（§2.4 实测 0 命中为前置条件）
不得同表碰撞（§2.3 分析）· 不得改变既有触发器次序语义（I 兼容分析 = §2.3）
GAP-INV-1 的 6 个非 letter 触发器（D-P11-13）：不重排 / 不插 letter / 不迁入 G/H/I/J / 不重分类
K = tg_version_immutable（D-P11-06）：不重建 / 不改语义 / 不移所有权
L = tg_audit_immutable（D-P11-10）：保持 P10-owned
```

---

## 10. 测试同步设计（指令 §14 · **实施期执行，本轮零改动**）

### 10.1 同步面实测（P11 实施将触碰的断言，逐文件）

| # | 文件 | 断言 | P11 后状态 | 处置 |
|---|---|---|---|---|
| S1 | `test_agent_tool_permission_schema.py::test_t12_acl_triggers_g_h_i_j_absent` | G/H/I/J 不存在 | **FAIL** | **翻转**为存在性 + 规范表挂载断言（docstring 注明 D-P11-01 接管；D-P09-06 的历史语义保留于注释） |
| S2 | `test_agent_tool_permission_schema.py`（T-2x exact trigger set，`triggers == P09_TRIGGERS`） | P09 表触发器精确集 | **FAIL**（agents 将多出 J） | `P09_TRIGGERS ∪ {tg_agent_acl_expire}` + 注明"0014 交付"（保持 head 精确集语义） |
| S3 | `test_agent_tool_permission_schema.py`（downgrade 段 `triggers == set()`，~L993） | 0011 降级后无 P09 触发器 | 视降级目标而定 | 实施期核对降级锚点：若从 head 降级则 0014 先被摘除、断言自然成立；若钉 0011 需同步。**记为核对项 SS-01** |
| S4 | `test_resource_acl_schema.py::test_g_h_i_j_absent_and_rls_disabled` | G/H/I/J 不存在 | **FAIL** | **拆分**：G/H/I/J 存在性移入新 P11 套件；RLS 禁用断言保留（head 口径仍成立） |
| S5 | `test_resource_acl_schema.py::test_trigger_set_is_exactly_three` | B14 表触发器精确集 | **FAIL**（resource_permissions 多出 G） | 期望集 `∪ {tg_acl_subject_exists}` + 注明"0014 交付"（其余两表不变） |
| S6 | `test_tool_registry_schema.py::test_tsec4_g_h_i_j_absent` | G/H/I/J 计数 = 0 | **FAIL** | **翻转**为 4（含规范表断言移交 P11 套件后，此处保留最小存在性） |
| S7 | `test_tool_registry_schema.py::test_tm8_head_and_trigger_set` | `head == "0013_p10_event_audit"` | **FAIL** | head 常量 → `0014_p11_triggers`（B15 触发器精确集不受影响） |
| S8 | `test_p10_event_audit_schema.py::test_bnd1_no_p11_triggers` | G/H/I/J 不存在（"yet"） | **FAIL** | **改写为所有权不相交不变式**：P10 表（events/audit_logs）无 P11 触发器 ∧ 4 张 P11 目标表无 P10 触发器 —— 该不变式在任何 head 恒真，优于时点断言 |
| S9 | `test_platform_timestamp_precision.py::test_pg6`（触发器总数 == 36） | 全部非内部触发器计数 | **FAIL** | 36 → **40**（4 个新触发器均在非分区表 ⇒ 无子分区克隆行；注释同步） |
| S10 | head 断言面（16 文件，见 §13.2） | `current_revision() == 0013…` / `HEAD_REVISION` / `get_heads()` / 链长 13 | **FAIL** | 0013 → `0014_p11_triggers` · 链长 13 → **14**（`P11_TRIGGERS` 常量定义保留给 S8/S4 引用） |
| S11 | `tests/architecture/test_p10_event_audit_boundary.py` | head / 触发器面引用 | 视具体断言 | 实施期逐条核对（预期仅 head 常量） |

### 10.2 不触碰面（明确排除）

```text
P12 契约/测试（0015 相关期望）一律不动 · T-22 forbidden 集不动（GUARD-1 属 P12 实施期）
identity / tenant_space 套件的触发器断言为【子集断言】（`<=` / `in`）⇒ H/J 新增不破坏，零改动
alembic_smoke 精确表集合不含触发器 ⇒ 零改动（仅 head 常量，归 S10）
authorization_service / rbac* / ai_gateway / security / migration_lock / generate_build_info：
  仅 head/链长常量（归 S10）
```

### 10.3 翻转原则（冻结措辞的映射）

```text
"P11 triggers absent → present" 在【head 口径的守卫】上执行（S1/S4/S6/S8）；
"absent" 作为【各 revision 自身性质】的历史断言一律不删除语义，由翻转后断言 +
  注释（指向 D-P11-01）承载；不修改任何 D-P09 / D-P11 决策正文。
```

---

## 11. 行为测试设计 —— 新增 `tests/integration/test_p11_triggers.py`（实施期）

**夹具模式（复用既有先例）**：

```text
registry fixture：ALTER TABLE acl_subject_types DISABLE TRIGGER tg_acl_subject_types_protect
                  → INSERT user/role/agent 三行 → ENABLE（先例：test_resource_acl_schema.py:171-184）
users / roles / agents 夹具：直接 INSERT（满足各自 CHECK 与 tenant/space 一致性触发器）
G/I 拒绝路径：独立连接 + pytest.raises(DBAPIError) + rollback（RAISE 即事务失败）
```

**必测行为（指令 §16 逐条）**：

| 组 | 用例 | 期望 |
|---|---|---|
| G-BEH | INSERT resource_permissions，subject = 存在 user / role / agent | PASS ×3 |
| G-BEH | subject_id 指向不存在的 user / role / agent | RAISE ×3 → 回滚 |
| G-BEH | subject_type 未注册（无 type 行）/ key 非法（`group` 等） | RAISE ×2 |
| G-BEH | UPDATE 仅改非监听列（如 conditions） | **不触发 G**（PASS） |
| H-BEH | 建带 ACL 的 user → 硬 DELETE | ACL 行被清理；role/agent ACL 不受影响 |
| H-BEH | user 软删除（UPDATE archived_at） | ACL **保留** |
| I-BEH | 删除被 ACL 引用的 role | RAISE → 回滚，role 仍在 |
| I-BEH | 删除未被引用的 role | PASS |
| I-BEH | is_system role / platform_admin 绑定 role 的删除路径 | 既有触发器行为不变（§2.3 兼容性复核） |
| J-BEH | agent status → archived | 其 ACL `inherited=true ∧ expires_at≈now()`；行保留 |
| J-BEH | agent 其他 status 迁移（active↔disabled） | **不动作**（expires_at 不变） |
| J-BEH | DELETE agent | 其 ACL 到期 |
| J-BEH | J 触发后无异常（递归证明） | J 的 UPDATE 不触发 G（D-P11-09 可测断言） |
| SEC | 4 函数 `prosecdef=false` · 无 search_path · 无 SECURITY DEFINER | 断言 |
| DOWNG | downgrade 0014 → 0013 | 8 对象零残留 |
| RT | upgrade → downgrade → upgrade | 对象集哈希一致 |

```text
所有失败路径必须证明事务回滚（失败后行集与失败前一致 —— 断言内建）
不携带任何 seed 落库（夹具行随测试连接回滚或测试末清理；不进入迁移）
```

---

## 12. 验收矩阵设计

`P11_IMPLEMENTATION_ACCEPTANCE_MATRIX.md`（本轮同步创建）分组：

```text
MIG（迁移身份/顺序/零残留）· TRIGGER（G/H/I/J 逐个 + 碰撞/命名/清单哈希）
FUNC（4 函数逐个）· SEC（INVOKER / search_path / 递归 / 回滚 / 禁写面）
P10B / P12B / P13B（三向边界）· REGRESSION（全量回归不下降）· DOWNGRADE · ROUNDTRIP
TEST（同步面 S1-S11 逐项落地 + 新套件）· SCOPE / GATE（授权面）
TRACE-nn：指令 §0-§18 每一节 ↔ 矩阵行 100% 追溯
逐个验证 G/H/I/J（禁止只数总触发器数）—— TRIGGER 组按字母分行
```

---

## 13. 连带同步面（实测预估 · 实施期以全量回归为准）

### 13.1 对象计数（实施后预期）

```text
父级触发器 35 → 39 · 触发器函数 17 → 21 · CREATE TRIGGER 语句 24 → 28
链长 13 → 14 · head = 0014_p11_triggers · 迁移文件 13 → 14
物理表数不变（35 含 alembic_version）· P10/P12/P13 对象面零变化
```

### 13.2 head 断言文件（0013 → 0014，实施期同步）

```text
tests/architecture/test_p10_event_audit_boundary.py
tests/integration/{agent_tool_permission_schema, ai_gateway_schema, alembic_smoke,
  authorization_service, identity_schema, migration_lock, p10_event_audit_schema,
  platform_timestamp_precision, rbac_hardening, rbac_schema, resource_acl_schema,
  tenant_space_schema, tool_registry_schema}.py
tests/security/test_authorization_security.py
tests/unit/test_generate_build_info.py
（+ 本轮新增的 tests/integration/test_p11_triggers.py 直接断言 0014）
```

---

## 14. Zero-Implementation Check（本轮实测）

```text
0014+ = ABSENT（versions = 13）· migration changes = 0 · DDL = 0 · DML = 0
trigger implementation = 0 · function implementation = 0 · code = 0 · tests = 0 · config = 0
commit = 0 · tag = 0 · push = 0
本轮新增/修改文件 = 仅 2 份设计文档（本契约 + P11_IMPLEMENTATION_ACCEPTANCE_MATRIX.md）+ harness 留档（仓库外）
P11 IMPLEMENTATION = NOT AUTHORIZED · P12 = NOT AUTHORIZED · P13 = NOT AUTHORIZED · Runtime = NOT AUTHORIZED
```

## 15. 跨决策扫描（Charter §7 义务 · 本轮执行）

```text
扫描范围：PLATFORM_DECISION_LOG.md（D-PLAT 17 / D-AUTH 25 / D-AGENT 16 / D-P10 18 / D-P11 14 /
          D-P12 15）+ 全部 *_IMPLEMENTATION_CONTRACT.md + P11 冻结包
ACTIVE vs FROZEN   ：无冲突（D-P11-01..14 全 FROZEN；无 PENDING/PROPOSED 残留）
FROZEN vs FROZEN   ：D-P11-10 ↔ D-P10-11（L 归属）一致 · D-P11-11 ↔ D-P12 索引边界一致 ·
                     D-P11-04 ↔ D-AUTH-12（FAIL CLOSED）同向 · D-P11-12 ↔ D-PLAT-11（seed 时序）一致
SCHEMA vs DECISION ：G/H/I/J 依赖的列/表/状态词表（resource_permissions.inherited/.expires_at ·
                     acl_subject_types.key ∈ {user,role,agent} · agents.status ∈
                     {draft,active,disabled,archived}）实测全部在位（§2.2/§3）
supersession 恒 = 1（D-B14-08）· 本契约不产生新决策、不改写任何冻结正文
```

---

---

## 16. 实施记录（2026-09-26 · IMPLEMENTATION AUTHORIZATION）

```text
revision                 = 0014_p11_triggers（sha256 3be9c8c092869c8d…）
down_revision            = 0013_p10_event_audit
single head              = 0014_p11_triggers（链长 14 · 0015+ = ABSENT）

triggers（新建）          = 4（G tg_acl_subject_exists · H tg_acl_user_hard_delete ·
                              I tg_acl_role_delete_block · J tg_agent_acl_expire）
functions（新建）         = 4（全部 SECURITY INVOKER · 无 search_path · 全库 prosecdef = 0）
tgtype                    = G 23 · H 9 · I 11 · J 25（与设计预测逐位一致）
index = 0 · seed = 0 · FK = 0 · RLS = 0 · GRANT = 0
既有触发器                 = 35 → 39（父级）· 40（含子分区克隆）· 函数 17 → 21
```

**行为验收（全部 PASS）**：G valid×3 / missing×3 / 未注册 type / 非 'group' 词表双闸
（`ck_acl_subject_types_whitelist` + G else 分支）/ 非监听列 UPDATE 不触发 ·
H 硬删清理（soft=1 → hard=0）/ 软删保留 · I 引用拒 / 无引用过 / 与 is_system、
pm_lifecycle 行为级兼容 · J 归档到期（inherited=true ∧ expires_at）/ 非归档迁移不动作 /
删除保留到期 / subject 列零改动（J→G 递归 = 无）· D-P11-05 不对称（role 归档 ACL 不动）。
**降级零残留**（8 对象全消 · 物理表 35）· **往返对象集一致**（8 = 8）。

**验收**：`p11_impl_acceptance.log` **20/20 PASS**（exit 0）·
`p11_impl_full_regression.log` **623 passed / 0 failed / 6 skipped**（exit 0，基线 596 ⇒ 净增 27）。

**END OF P11 IMPLEMENTATION CONTRACT（2026-09-26 · DESIGN FROZEN · IMPLEMENTATION AUTHORIZED → IMPLEMENTED）**
