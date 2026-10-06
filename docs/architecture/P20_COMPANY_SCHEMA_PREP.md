# P20 COMPANY SCHEMA PREP

```text
性质   = SCHEMA PREP ONLY（设计输入 · NOT FROZEN · 无实现）
基线   = UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）+ PDL 附录 AC（P20 决策冻结）
本轮   = 无 CREATE TABLE / 无 migration / 无 DDL / 无 DML / 无 API / 无 worker / 无 event 激活
```

## 1. 冻结边界（继承 PDL 附录 AC）

```text
A1 = Company（首个业务模块）
A2 = tenant = 组织根 · space = 部门/组织运行分区（**不创建与 Space 平行的第二套组织容器**）
A3 = 首版不引入平台外主体（员工 = 平台 user；不扩展 ACL subject type）
A4 = YES：需要独立业务持久化模型（**≠ 立即 migration**）
A5 = 复用 canonical 12 actions（不新增 action）
A6 = 最小范围：Employee + Organization View/Assignment + Authorization + Audit
A7 = 不要求首个 Production Event
A8 = domains/company/ + Core → Domain = 0
```

## 2. 核心语义裁定（Schema Proposal · NOT FROZEN）

```text
Department 映射 = **选项 A：直接引用现有 `spaces`**
理由：A2 已冻结 space = 部门/组织运行分区；平台已有 spaces（tenant-scoped · key 唯一 ·
      owner/visibility/lifecycle）+ memberships（空间成员资格）+ P18 空间生命周期与控制面投影。
⇒ 不创建 departments 表；部门 = space（key/name 承载部门命名）
⇒ 与 A2 无冲突；若未来需要部门层级（parent），属**新决策**（当前 schema 无 parent 列）
```

## 3. 候选表（Schema Proposal · 2 张）

```text
T1 company_employees      员工业务实体（≠ users）· tenant 内组织身份与业务属性
T2 company_assignments    员工 ↔ 部门(space) 的有效分配（多对多）
不新增：departments（= spaces）· companies（= tenants）· 第二套角色/权限/成员体系
```

## 4. 与平台的关系（Identity Reference · §8）

```text
Employee ≠ User：company_employees 不复制 users 字段，仅以 user_id 引用平台身份（可空）
  · user_id NOT NULL = 员工已绑定平台账号  · user_id NULL = 员工尚未开通平台访问
  · 员工授权仍由平台 canonical 授权决定（员工身份本身不授予任何权限）
Membership：空间成员资格（memberships）由 P17 管理；company_assignments 是**业务分配**，
  两者不互相替代（assignment 不产生 tenant/space membership 授权）
Owner/creator：不产生隐式继承授权（P18 既有原则）
```

## 5. 审计 / 授权 / 事件

```text
Audit：员工与分配的安全敏感变更写 audit_logs（actor = 真实用户 · tenant/space 上下文 · correlation）
Authorization：复用 canonical 12 actions；resource_type 候选 `company_employee` / `company_assignment`
  （resource_type 为开放格式）—— 若需要新的 **permission** 行，则属新决策（当前 permissions = 12）
Event：A7 不要求 ⇒ 本 PREP **不写** event 需求；未来 Company events 须满足 P19-D02…D18 并另行授权
```

## 6. 本轮结论

```text
形成 Schema Proposal：2 张候选表 + 复用 spaces/tenants/users/audit/authorization；
不创建任何对象；migration = NOT AUTHORIZED（A4 明确"YES ≠ immediate migration"）。
后续：Schema Decision（是否采纳 + 是否建 migration）必须由新的独立 Human Decision 授权。
```

**END OF P20 COMPANY SCHEMA PREP（SCHEMA PROPOSAL · NOT FROZEN · 无实现；2026-10-01）**
