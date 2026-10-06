# P20 COMPANY CONSTRAINT / INDEX MATRIX（**FROZEN** · PDL 附录 AD）

## 1. company_employees

```text
PK      : id
FK      : tenant_id → tenants(id) ON DELETE RESTRICT（组织有员工时不得硬删）
FK      : user_id   → users(id)   ON DELETE RESTRICT（保留历史业务事实）
UNIQUE  : (tenant_id, employee_no)                      —— 组织内工号唯一（业务标识）
UNIQUE  : (tenant_id, user_id) WHERE user_id IS NOT NULL —— 同一用户在同一组织仅一个员工身份
CHECK   : status ∈ {active, suspended, terminated}
CHECK   : employee_no ~ '^[A-Za-z0-9._-]{1,64}$'
CHECK   : (status = 'terminated') = (terminated_at IS NOT NULL)   —— 生命周期一致性
NOT NULL: id · tenant_id · employee_no · display_name · status · created_at · updated_at
INDEX   : (tenant_id, status) · (tenant_id, employee_no) · (user_id) WHERE user_id IS NOT NULL
隔离     : tenant_id 由 FK + 应用层上下文双保证；跨租户查询禁止
```

## 2. company_assignments

```text
PK      : id
FK      : tenant_id   → tenants(id) ON DELETE RESTRICT
FK      : employee_id → company_employees(id) ON DELETE CASCADE（业务从属关系）
FK      : space_id    → spaces(id) ON DELETE RESTRICT（部门有分配时不得硬删）
UNIQUE  : (employee_id, space_id) WHERE ended_at IS NULL —— 同一员工在同一部门仅一个有效分配
CHECK   : status ∈ {active, ended} · assignment_role ∈ {member, lead}
CHECK   : (status = 'ended') = (ended_at IS NOT NULL)
NOT NULL: id · tenant_id · employee_id · space_id · assignment_role · status · started_at · created_at · updated_at
INDEX   : (tenant_id, space_id, status) · (employee_id, status) · (tenant_id, status)
隔离     : tenant_id + space_id 双键；space 必须属同一 tenant
          （跨租户组合的强制方式 = 应用层 + 可选 trigger ⇒ **OPEN 提案项**，见 GAP）
```

## 3. 明确不添加（未经语义支持）

```text
不添加"为了保险"的约束：如未定义语义的唯一键、无业务含义的 CHECK、与平台重复的软删除列
不添加 parent/层级列（部门层级 = 新决策）
不添加 company 版本的事件/同步列（A7 不要求事件）
```

**END OF P20 COMPANY CONSTRAINT INDEX MATRIX（FROZEN · PDL 附录 AD · 含 1 项 OPEN；2026-10-01）**
