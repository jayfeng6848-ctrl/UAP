# P20 COMPANY AUTH / AUDIT MATRIX

## 1. 授权映射（复用 canonical 12 actions · A5）

| 业务操作 | action | resource_type（提案） | scope | 说明 |
|---|---|---|---|---|
| 查看员工 | `read` / `list` | `company_employee` | TENANT | 组织内可见性由授权决定 |
| 新增员工 | `create` | `company_employee` | TENANT | 需既有 permission 匹配；否则 ⇒ 新决策 |
| 修改员工 | `update` | `company_employee` | TENANT | 同上 |
| 停用/离职 | `delete`（软终止）或 `update` | `company_employee` | TENANT | 状态机变更 · 无物理删除 |
| 查看分配 | `read` / `list` | `company_assignment` | TENANT（+SPACE 语境） | 部门范围 |
| 新增/结束分配 | `create` / `update` | `company_assignment` | TENANT/SPACE | 同上 |

```text
注意（OPEN）：`permissions` 登记表当前为 12 行（P13 冻结）。上述 resource_type 为开放格式，
但若需要新的 **permission 行**（例如 company_employee.read），属**新决策**；
首版亦可复用既有语义（如 member.* / resource.*）—— 该选择必须在 Schema Decision 中明确。
```

## 2. 审计映射（audit_logs · append-only）

```text
必须审计：员工创建/修改/离职 · 分配创建/结束 · 授权失败（沿用平台约定）
actor = 真实认证用户（绝不写 DB principal）· tenant_id/space_id = 目标上下文 · correlation 复用
禁止内容：password / token / credential / secret / SQL / stack
```

## 3. 事件（A7 = 不要求）

```text
本轮不写 event 需求；未来 Company events 必须满足 P19-D02…D18 并由新的 Human Decision 授权
audit ≠ event（P19-D12）
```

**END OF P20 COMPANY AUTH AUDIT MATRIX（提案 · 含 1 项 OPEN（permission 行）；2026-10-01）**
