# P20 COMPANY SCHEMA GAP RECORD

```text
性质 = P20 SCHEMA PREP 附件（缺口登记 · OPEN · 未粉饰）
```

## GAP-P20S-1 部门层级未定义

```text
Observation：A2 冻结 department = space，但 spaces 无 parent 列（平台无资源父子树）。
Impact     ：若业务需要"部门树"，属新 schema 决策（不得自行加 parent 列）。
状态       ：OPEN
```

## GAP-P20S-2 授权 permission 行未定

```text
Observation：canonical 12 actions 可复用，但 `permissions` 登记表 12 行中无 company 语义；
             是否新增 permission 行（新决策）或复用既有语义，尚未裁定。
状态       ：OPEN（须在 Schema Decision 中明确）
```

## GAP-P20S-3 跨租户/跨空间一致性的强制方式

```text
Observation：company_assignments 需保证 space.tenant_id = tenant_id；
             平台既有做法对 memberships 使用 trigger，对 resources 使用 trigger。
             本轮**未**决定是否为业务表添加同类 trigger（属 schema 决策）。
状态       ：OPEN（提案：复用平台既有 trigger 模式 · 或应用层强校验 + 验收测试）
```

## GAP-P20S-4 员工身份与平台身份的关系细节

```text
Observation：Employee ≠ User 已确立；user_id 可空。但"员工必须先有平台账号吗"、
             "员工离职是否级联处理 tenant/space membership"未定义（后者涉及 P17/P18 语义）。
状态       ：OPEN（须在 Schema Decision 中明确，且不得改写 P17/P18 冻结语义）
```

## GAP-P20S-5 迁移与权限物化

```text
Observation：若采纳业务表，需要 migration（新决策）+ 业务表的 uap_runtime 授权面
             （新增 GRANT = 新 privilege surface ⇒ 独立决策）。
状态       ：OPEN
```

## GAP-P20S-6 领域落位实现细节

```text
Observation：A8 冻结 `domains/company/`，但 domain 层与 services/infrastructure 的
             具体分工与守卫断言尚未细化（Core → Domain = 0 已冻结）。
状态       ：OPEN（随实现轮一并细化）
```

**END OF P20 COMPANY SCHEMA GAP RECORD（GAP-P20S-1…6 = OPEN；2026-10-01）**
