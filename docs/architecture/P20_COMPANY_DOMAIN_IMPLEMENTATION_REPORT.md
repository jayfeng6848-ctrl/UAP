# P20 COMPANY DOMAIN IMPLEMENTATION REPORT

```yaml
Stage: P20 Company Domain Implementation (authorized by
       "P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION EXECUTION CONTRACT")

Domain implementation = PASS

API = NOT IMPLEMENTED
Event = NOT IMPLEMENTED
Worker = NOT IMPLEMENTED

Migration: 0020_p20_company_authorization — CREATED (head, single head)
Permissions: 11 grants to platform_admin — APPLIED (idempotent; downgrade removes only its own rows)
Resources: collection projection (pre-built operator path) — IMPLEMENTED (missing = DENY)
Authorization: 26 Company tests PASS (incl. deny / cross-tenant / resource-mismatch)
Audit: 8 mutation actions in the same transaction — VERIFIED (incl. rollback on audit failure)
Core→Domain: PASS (architecture guards 63 passed)

Commit: NO
Tag: NO
Push: NO
Hard Stop: ACTIVE
```

## 1. Phase 0 — precheck (read-only, measured)

```text
HEAD = 08a0485b · staged = 0
0019_p20_company sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未改动）
company_employees / company_assignments = 2 tables（隔离库实测）
permissions = 23（12 platform + 11 company）· acl_subject_types = 3 · roles = 1（未变）
events = 0 · production allowlist = EMPTY
Core → Domain = 0（dependency guards 14 passed）
⇒ 全部满足，未触发 STOP
```

## 2. Phase 1 — Human Decisions applied

```text
G1（权限授予）= 迁移 0020_p20_company_authorization：
   把 0019 seed 的 11 条 Company 权限绑定到既有 platform_admin（role_permissions · effect=allow）
   不新增 role / subject type / canonical action；不修改既有 permission 行；幂等（NOT EXISTS）
   downgrade 只删除本迁移所有的绑定（platform_admin × 11 × allow），权限行本身保留
   delete / admin 权限键保留在词表中，但 V1 不开放任何用例

G2（资源投影）= 预建集合资源模式：
   每 tenant × 每 resource_type 一行（company_employee/employees · company_assignment/assignments）
   tenant scope（space_id NULL · classification INTERNAL · status active）
   缺失 = DENY（RESOURCE_NOT_PROVISIONED）· 业务请求路径不创建 · domain 不创建
   运维入口：scripts/provision_company_resources.py（--status / --tenant / --all）
```

## 3. Phase 2–7 — implemented artifacts

```text
domains/company/（纯契约 · 无 ORM/SQL/infrastructure/授权实现）
  entities.py    Employee / Assignment 实体 + 不变量（terminated⇔terminated_at、ended⇔ended_at）
  values.py      生命周期词表与转换表（active/suspended/terminated · active/ended · member/lead）
  ports.py       EmployeeRepository / AssignmentRepository / ResourceProjectionRepository（仅接口）
  errors.py      CompanyDomainError + DomainErrorCode
  __init__.py    契约导出面
  manifest.py    placeholder → active（tables=2 · 11 个 canonical 权限键 · core_dependencies）
  README.md      状态与边界同步

services/company/（编排 · 单一授权引擎 · 同事务审计）
  errors.py      稳定错误码 + 域错误/DB 约束映射（不泄露 SQL/约束名/堆栈）
  repository.py  三个仓储的 SQLAlchemy 实现（全部携带 tenant 谓词 · 不 commit）
  projection.py  集合资源 collection/ensure/backfill（operator 路径）
  use_cases.py   11 个用例，固定顺序：授权+资源解析 → 上下文门禁 → 域校验 → 仓储写入 → 审计 → 提交
  __init__.py    服务导出面

migrations_alembic/versions/0020_p20_company_authorization.py
scripts/provision_company_resources.py
tests/company/（company_testkit.py · conftest.py · 4 个测试模块）
tests/architecture/test_dependency_rules.py（守卫改为显式 ACTIVE_DOMAINS 白名单）
```

## 4. Phase 8 — test results

```text
tests/company/test_company_authorization_migration.py  （0020 授权 + downgrade 归属 + 再 upgrade）
tests/company/test_company_domain.py                   （生命周期 / 不变量 / 非法转换 / 域纯度）
tests/company/test_company_repository.py               （CRUD / tenant 谓词 / 约束映射）
tests/company/test_company_service.py                  （授权拒绝 / 投影缺失拒绝 / 跨租户 / 审计回滚）
                          ---------------------------------------------
                          Company suite = 26 passed / 0 failed

tests/architecture（既有守卫全量，含本轮修改的 domain manifest 守卫）= 63 passed
tests/unit/test_generate_build_info.py = 0 executed（冻结禁令未触碰）

隔离验证（专用一次性库，运行后 DROP）：
  uap_p20_domain_test（服务/仓储/域）· uap_p20_authz_test（迁移授权）
  迁移授权实测：permissions 23 · platform_admin allow 绑定 23（12+11）· Company 绑定 = 11
               downgrade → Company 绑定 = 0 · platform_admin 绑定回到 12 · 权限行仍 23
               re-upgrade → Company 绑定 = 11（可逆且可重复）
  跨租户实测（全部 DENY / 不可见）：
    employee + space（异租户空间）→ SPACE_NOT_FOUND
    employee + assignment（异租户上下文）→ EMPLOYEE_NOT_FOUND / ASSIGNMENT_NOT_FOUND
    resource mismatch（资源属 A、上下文属 B）→ 引擎 DENIED
    tenant C 未投影 → RESOURCE_NOT_PROVISIONED（不自动补建）
```

## 5. 实现说明（与本轮授权的对应与小幅工程判断）

```text
N1 用例范围：按授权 Phase 5 实现 11 个用例（employee: create/get/list/update/suspend/terminate；
   assignment: create/get/list/update/end）。仓库层保留 bind_user（schema/D-P20D-05 语义），
   但**未**暴露 bind 用例（授权清单未包含），故未创建对应端点/入口。
N2 权限词表使用面：11 条 Company 权限中 8 条被使用（read/list/create/update × 2 类）；
   未使用 3 条（company_employee.delete · company_employee.admin · company_assignment.delete，
   依 D-P20D-03/04 = RESERVED）。
N3 守卫变更：`test_domain_manifests_are_placeholders` → `test_domain_manifests_match_activation_state`，
   改为显式 ACTIVE_DOMAINS = {company} 白名单（其余域仍必须 placeholder）——授权 Phase 2 所覆盖。
N4 域文档措辞：为满足既有文本级纯度守卫（禁止域内出现持久化库字面量），domain 文档改为
   「no ORM / persistence library」表述；纯为文案，无功能变化。
N5 G7（共享测试库）未获裁定 ⇒ uap_b1_test 保持 0017_p13_seed 冻结；Company 测试使用
   专用一次性库（uap_p20_domain_test / uap_p20_authz_test）。
N6 授权与资源解析在实现中是**同一道门**（步骤 1+2）：引擎按 resources.id 解析资源，
   缺投影即拒绝，且绝不在请求路径补建——与 P17-AUTH-Q1 先例一致。
```

## 6. 边界（本轮未做）

```text
未创建 API / 路由 / DTO · 未创建 Worker / Scheduler · 未创建 Event / Producer / Handler ·
未激活 P19（Allowlist EMPTY 不变）· 未修改既有平台 schema（0019 及以前零改写）·
未修改 P17/P18 control plane · 未新增 ACL subject type / canonical action / 角色体系 ·
未 GRANT/REVOKE 表权限（0019 的 Company 表授权即为所需的全部）·
未触碰正式库 uap 与共享测试库 uap_b1_test · 未 commit / tag / push
```

## 7. 下一阶段

```text
P20 DOMAIN IMPLEMENTATION ACCEPTANCE GATE（须独立授权）
  届时可复核：契约/实现一致性、26 项 Company 测试、63 项架构守卫、
             0020 迁移与降级所有权、集合资源运维路径、以及 N5（共享测试库策略）与
             G3（manifest/守卫长期形态）的最终裁定
```

**END OF P20 COMPANY DOMAIN IMPLEMENTATION REPORT（Domain implementation = PASS · 11 use cases · 0020 grants 11 · collection projection pre-built · 26 Company tests + 63 architecture guards PASS · API/Worker/Event 未实现 · 未 commit；2026-10-02）**
