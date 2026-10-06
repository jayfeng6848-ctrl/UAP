# P20 COMPANY SCHEMA MATRIX（**FROZEN** · PDL 附录 AD）

| 业务概念 | 平台映射 | 是否新表 | 证据 / 约束 |
|---|---|---|---|
| 公司/组织 | `tenants`（A2 = 组织根） | NO | PDL 附录 AC A2 · 平台既有 tenants 生命周期 |
| 部门 | `spaces`（A2 = 部门/组织运行分区） | **NO** | A2 + 既有 spaces（tenant-scoped · key 唯一 · visibility · lifecycle） |
| 部门成员资格 | `memberships`（P17） | NO | P17 membership runtime（member.read/member.admin） |
| 员工 | `company_employees` | **YES（提案）** | Employee ≠ User；业务属性不属平台身份表 |
| 员工分配 | `company_assignments` | **YES（提案）** | 员工 ↔ space 多对多有效分配（业务语义） |
| 员工权限 | canonical 授权（复用 12 actions） | NO | A5；若需新 permission ⇒ 新决策 |
| 员工生命周期 | `company_employees.status` + audit | NO（新列属提案） | A6 最小范围 |
| 部门生命周期 | `spaces.status`（P18） | NO | P18 空间生命周期与控制面 |
| 事件 | 不激活（A7） | NO | P19-D01 OPTION D · P19-D18 首激活门 |

```text
全部为 SCHEMA PROPOSAL · NOT FROZEN；本轮不创建任何对象。
```

**END OF P20 COMPANY SCHEMA MATRIX（FROZEN · PDL 附录 AD；2026-10-01）**
