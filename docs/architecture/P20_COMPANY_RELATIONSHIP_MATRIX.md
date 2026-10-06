# P20 COMPANY RELATIONSHIP MATRIX（**FROZEN** · PDL 附录 AD）

```text
tenant 1──N space(部门) · tenant 1──N company_employees · company_employees 1──N company_assignments
company_assignments N──1 space · company_employees 0..1──1 users(平台身份)
```

| 关系 | 基数 | 语义 | 授权影响 |
|---|---|---|---|
| tenant → space | 1:N | 部门必属一个组织（spaces.tenant_id NOT NULL + FK RESTRICT） | 无（容器） |
| tenant → company_employees | 1:N | 员工只属一个组织（跨租户 = DENY） | 无（业务实体） |
| company_employees → users | 0..1 : 1 | user_id 可空（未开通平台账号） | **无**：员工身份不授予权限 |
| company_employees ↔ space | M:N（经 assignments） | 一个员工可分配多个部门；一个部门可有多名员工 | **无**：assignment 不产生 membership 授权 |
| employee → assignments | 1:N（CASCADE） | 员工删除随删分配 | 无 |
| space → assignments | 1:N（RESTRICT） | 部门有分配时不可硬删（与平台 RESTRICT 语义一致） | 无 |

```text
跨租户/跨空间：一切业务读写在 actor 的 tenant/space 上下文内（P17）；cross-tenant / cross-space = DENY
owner / creator / platform_admin 不产生隐式继承授权（继承 P18 原则）
```

**END OF P20 COMPANY RELATIONSHIP MATRIX（FROZEN · PDL 附录 AD；2026-10-01）**
