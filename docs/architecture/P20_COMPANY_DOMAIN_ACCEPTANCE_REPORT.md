# P20 COMPANY DOMAIN ACCEPTANCE REPORT

```text
阶段     = P20 COMPANY DOMAIN IMPLEMENTATION ACCEPTANCE GATE（只读验收 · 不修复 · 不重构 · 不改迁移/权限/schema）
基线     = UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）+ PDL 附录 AF + 0019 + 0020
被验对象 = domains/company/ · services/company/ · 0020_p20_company_authorization · tests/company/
证据来源 = 静态扫描 + 63 架构守卫 + 26 Company 测试 + 一次性隔离库探针（uap_p20_acceptance_probe，已 DROP）
```

## 1. Phase 0 — Frozen Baseline

```text
HEAD = 08a0485b · staged = 0 · 自 release 以来 commit = 0 · tags = 16（未新增）
0019_p20_company sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未改动）
0020_p20_company_authorization sha256 = 22B6EE611CDD4281CD1BE892F6D8716FE7EA8E26BA41E21DE41EC9BC20588CA4
revision chain = 0020_p20_company_authorization → 0019_p20_company（down_revision 正确 · 单 head）
downgrade safety = 0020 downgrade 只删除本迁移所有的 role_permissions 行（迁移测试实测：
                   Company 绑定 11 → 0 · platform_admin allow 23 → 12 · 权限行仍 23 · 可再 upgrade）
正式库 uap 未执行任何 migration（0 public 表）
```

## 2. Phase 1 — Schema Acceptance（隔离库实测）

```text
company_employees
  PK(id) · FK tenant→tenants RESTRICT · FK user→users RESTRICT（user_id 可空）
  UNIQUE (tenant_id, employee_no) · UNIQUE (tenant_id, user_id) WHERE user_id IS NOT NULL
  CHECK status ∈ {active,suspended,terminated} · CHECK employee_no 形状
  CHECK (status='terminated') = (terminated_at IS NOT NULL)   ← 生命周期一致性
  无物理删除路径（运行时无 DELETE 权限 · 终止 = 状态变更）
company_assignments
  PK(id) · FK tenant→tenants RESTRICT · FK space→spaces RESTRICT · FK employee→company_employees CASCADE
  CHECK status ∈ {active,ended} · CHECK assignment_role ∈ {member,lead}
  UNIQUE (employee_id, space_id) WHERE ended_at IS NULL        ← active 唯一
  TRIGGER tg_company_assignment_tenant_consistency（BEFORE INSERT OR UPDATE · 结构一致性）
  ⇒ employee.tenant = assignment.tenant = space.tenant 无法被违反（触发器 + 应用门禁双重）

生命周期转换（域层 + 测试实测）：active→suspended ✓ · active→terminated ✓ · suspended→terminated ✓ ·
                                  terminated→* 一律 REJECT ✓（terminated 为终态）
```

## 3. Phase 2 — Domain Purity

```text
AST 扫描 domains/company/（__init__ · entities · errors · manifest · ports · values）
  forbidden_imports = []（无 sqlalchemy / psycopg / infrastructure / services / apps）
纯契约内容：Entity · Value Object · Domain Error · Port Interface（无 ORM · 无 SQL · 无授权实现）
既有守卫 test_domains_define_no_schema_or_persistence 亦 PASS（63 守卫全绿）
⇒ Domain Purity = PASS
```

## 4. Phase 3 — Service Layer

```text
固定顺序（use_cases.py 每个用例一致，代码顺序可验证）：
  1+2 授权门（集合资源解析 → AuthorizationService；缺投影即拒绝，绝不在请求路径补建）
  3   上下文校验（tenant active；assignment 另要求 space 属同租户且 active）
  4   域校验（不变量 / 生命周期）
  5   仓储写入（services/company/repository.py · 全部 tenant 谓词 · 不 commit）
  6   审计写入（同一事务）
  7   提交（RuntimeDatabase.transaction）
禁止项核查：
  bypass authorization        = 无（每个用例首步即 _authorize；无先读后判路径）
  hidden permission check     = 无（无角色/许可/ACL 自建判定）
  self-healing resource create= 无（用例只调用 projection.collection；ensure_* 仅在运维/测试路径）
  direct SQL                  = 见 F-01（登记 · 待裁定）
```

**F-01（登记 · 未修复，依本轮规则不得现场修复）**

```text
事实：services/company/use_cases.py 含 3 处直接 SQL（`text(` 计数 = 3）：
      ① 读 tenants.status（上下文门禁）② 读 spaces.status（上下文门禁）③ INSERT audit_logs（审计）
      业务对象 CRUD 全部位于 services/company/repository.py（无旁路）。
先例：P18 `services/use_cases/control_plane.py` 采用同一形态（用例内联审计 + 状态读取）且已 RELEASED。
影响：若「禁止 direct SQL」按字面严格解读 ⇒ 本项构成 BLOCKER；
      若按项目既有解释（不得在服务层旁路仓储/授权做业务 SQL）⇒ 非阻断。
处置：本轮只登记，未修改任何代码。请裁决：接受（保持现状）／要求下沉
      （上下文读取 → repository 方法；审计写入 → services/audit/writer.py 或扩展其 metadata 白名单）。
```

## 5. Phase 4 — Authorization

```text
canonical actions = 12（core.permission.vocabulary.ACTIONS 未变）
Company permissions = 11（隔离库实测 company_permissions = 11 · permissions 总数 23）
ACL subject type = 3（USER / ROLE / AGENT · 隔离库 acl_subject_types = 3 · roles = 1 未变）
未新增：action / subject type / role（0020 仅新增 role_permissions 绑定）

platform_admin 能力：Company 绑定 = 11 · allow 总数 = 23（12 platform + 11 company）
reserved capability 未进入业务路径：
  用例动作仅取 read / list / create / update（静态核查：use_cases.py 无 delete / admin 动作调用）
  company_employee.delete · company_employee.admin · company_assignment.delete = RESERVED（无用例暴露）
  O-01（观察·非阻断）：本门指令列出的 `company_assignment.admin` **不在** 0019 冻结的 11 条键中
       （实际未使用集合为 3 条：employee.delete / employee.admin / assignment.delete）。
```

## 6. Phase 5 — Resource Projection（重点）

```text
模型：resource_type = company_employee / company_assignment · natural_key = employees / assignments
      tenant 级（space_id NULL · classification INTERNAL · status active）· V1 无实例资源
Case 1 resource exists → ACCEPT（服务测试实测：create/read/list/update 全部经授权放行并落审计）
Case 2 resource missing → DENY，错误码 = RESOURCE_NOT_PROVISIONED
      （服务测试 test_missing_projection_is_denied · 未投影 tenant 直接拒绝）
      隔离库实测：新 tenant 的 company_* resources 行 = 0（不自动创建）
禁止自动创建：用例路径只读投影；创建入口仅 scripts/provision_company_resources.py（运维）
```

## 7. Phase 6 — Audit

```text
mutation 覆盖（8 条）：company_employee.create / .update / .suspend / .terminate ·
                       company_assignment.create / .update / .end
同事务：审计与业务写入共用 RuntimeDatabase.transaction（读取型用例不写审计）
回滚验证：monkeypatch 使审计写入失败 ⇒ 业务行未落库（测试实测 count = 0）
内容安全：审计 metadata 键 ⊆ 白名单（operation / employee_no / employee_id / space_id /
          fields / from / to / assignment_role）；无 select/insert/password/traceback 等字样
禁止 event：events 行数 = 0 · production allowlist = EMPTY · 无 producer / handler
```

## 8. Phase 7 — Tenant Isolation

```text
Employee：A 租户员工 + B 租户上下文 → EMPLOYEE_NOT_FOUND（tenant 谓词强制，不可见）
Assignment：A 租户员工 + B 租户空间 → SPACE_NOT_FOUND；A 分配 + B 上下文 → ASSIGNMENT_NOT_FOUND
Resource mismatch：资源属 A、请求上下文属 B → 引擎判定 DENIED（直接调用引擎实测）
另：跨租户组合由 DB 触发器兜底（isolation 测试 T6–T10 全 REJECTED）
```

## 9. Phase 8 — Regression

```text
tests/architecture = 63 passed（含 Core → Domain = 0 与域纯度守卫）
tests/company（4 模块 · 显式允许清单）= 26 passed / 0 failed
tests/unit/test_generate_build_info.py = 0 executed（冻结禁令未触碰）
events = 0 · handlers = 0 · producers = 0（allowlist is_empty = True）
常驻环境未变：uap_b1_test = 0017_p13_seed（perms 12 · company 0 · events 0）· 正式库 uap = 0 public 表
一次性验收库已 DROP（无残留）· 本轮未 commit / tag / push
```

## 10. Phase 9 — Documentation

```text
已存在：docs/architecture/P20_COMPANY_DOMAIN_IMPLEMENTATION_REPORT.md
本文件：docs/architecture/P20_COMPANY_DOMAIN_ACCEPTANCE_REPORT.md（仅记录验收结果 / 证据 / 待裁项）
未修改 PLATFORM_DECISION_LOG.md（本轮零决策改动）
```

## 11. 验收结论

```text
Schema            = PASS
Domain Purity     = PASS
Service           = PASS（附待裁项 F-01：use_cases 内联 SQL）
Authorization     = PASS
Resource Projection = PASS
Audit             = PASS
Tenant Isolation  = PASS
Regression        = PASS

P20 DOMAIN ACCEPTANCE = PASS（在 F-01 按项目既有解释「不旁路仓储/授权」的前提下）
```

**END OF P20 COMPANY DOMAIN ACCEPTANCE REPORT（8/8 项 PASS · 26 Company 测试 + 63 架构守卫全绿 · 待裁项 F-01 · 观察项 O-01 · 未修复 / 未 commit；2026-10-02）**
