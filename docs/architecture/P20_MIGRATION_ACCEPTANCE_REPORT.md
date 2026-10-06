# P20 MIGRATION ACCEPTANCE REPORT — 0019_p20_company

```text
阶段     = P20 MIGRATION ACCEPTANCE GATE（只读验收；本轮不新建表 / 不改 migration / 不改 schema / 不改代码）
基线     = UAP-V0.1.17-P18-CONTROL-PLANE（commit 08a0485b · tags 16 · HEAD 未新增 commit）
被验对象 = migrations_alembic/versions/0019_p20_company.py
           sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（13006 bytes）
冻结权威 = PDL 附录 AC / AD / AE（D-P20S-01…16 · OPT-2）
执行环境 = 一次性隔离库 uap_p20_0019_verify（创建 → 验收 → DROP；正式库 uap 未触碰）
```

## 1. 基线与结构审查（§1 / §2）

```text
git status --short        = 29 modified（全部为历史脏文件）+ 115 untracked + 本报告 1 新增；staged = 0
git log -1 --oneline      = 08a0485 release: UAP v0.1.17 P18 control plane（HEAD 无新 commit）
git diff --check          = 仅 4 条既有 CRLF 警告（历史文件 · 未触碰）
历史 migration 改动        = 0（git diff --name-only -- migrations_alembic 为空；0018 及以前零改写）
alembic heads             = ['0019_p20_company']（单 head · 无多 head）
alembic current（共享库）  = 0017_p13_seed（uap_b1_test 未迁移 · 基线冻结）
revision / down_revision  = 0019_p20_company / 0018_p16_agent_runtime（与授权一致）
DDL 面                    = 仅 op.create_table ×2 · op.create_index ×8 · op.execute（触发器/函数/
                            GRANT/权限行/DROP）· 无动态 SQL（无 EXECUTE 拼接 · 无字符串构造的 DDL）
代码面                    = 未新增/未修改任何 API · Domain 实现 · Worker · producer · handler
                            （domains/company/ 为 HEAD 中既有 placeholder：README/__init__/manifest，
                             声明 status=placeholder、tables=[]、entrypoints=[]，本轮未触碰）
```

## 2. Schema 验收（§3 / §4 / §5）

```text
Tables                = company_employees · company_assignments（company_* 仅此两张；
                        无 departments / companies / company_users / 其他新表）
company_employees     = 11 列，实测列集合与可空集合与附录 AD 完全一致
                        （user_id / title / hired_at / terminated_at 可空，其余 NOT NULL）
                        FK tenant→tenants RESTRICT · FK user→users RESTRICT
                        UNIQUE (tenant_id, employee_no)
                        UNIQUE (tenant_id, user_id) WHERE user_id IS NOT NULL
                        CHECK status ∈ {active,suspended,terminated}
                        CHECK (status='terminated') = (terminated_at IS NOT NULL)
company_assignments   = 10 列，列集合与可空集合一致（仅 ended_at 可空）
                        FK tenant→tenants RESTRICT · FK space→spaces RESTRICT
                        FK employee→company_employees CASCADE（冻结矩阵/实体目录/关系矩阵）
                        UNIQUE (employee_id, space_id) WHERE ended_at IS NULL
                        CHECK status ∈ {active,ended} · CHECK (status='ended') = (ended_at IS NOT NULL)
spaces 是否被修改       = NO（仅作为 FK 目标与触发器只读校验对象；无 ALTER/无新 UNIQUE）
```

## 3. OPT-2 触发器与安全（§6 / §7）

```text
触发器          = tg_company_assignment_tenant_consistency
                 BEFORE INSERT OR UPDATE ON public.company_assignments · FOR EACH ROW
校验内容        = NEW.tenant_id = company_employees.tenant_id
                 NEW.tenant_id = spaces.tenant_id（不一致 ⇒ RAISE EXCEPTION ⇒ 原子回滚）
函数安全        = prosecdef = false（SECURITY INVOKER，非 DEFINER）· LANGUAGE plpgsql
                 writes_dml = false · writes_audit = false · writes_events = false
不判断          = permission / role / actor / authorization / owner / admin（纯结构一致性）
提权路径        = 无（无 SET ROLE · 无动态 SQL · 无 DML · 仅最小 tenant 字段读取）
```

## 4. 权限与运行时授权（§8 / §9）

```text
canonical action 词表 = 12（core.permission.vocabulary.ACTIONS 未变；无新增 action）
permissions 行数      = 12 → 23（+11 Company：company_employee.* ×6 · company_assignment.* ×5）
                        resource_type ∈ {company_employee, company_assignment} · is_system=false
                        action 全部取自既有 canonical 12；其中 list / create 为既有 canonical 动作
                        此前未被任何权限行使用（词表不变，仅数据使用面扩大）
acl_subject_types     = 3（与共享库一致 · 未新增）
roles / role_permissions = 1 / 12（与共享库一致 · Company 相关 role grant = 0）
uap_runtime（Company） = company_employees = INSERT,SELECT,UPDATE · company_assignments = INSERT,SELECT,UPDATE
                        无 DELETE / TRUNCATE / REFERENCES / TRIGGER；ALTER / DROP TRIGGER 实测 DENIED
```

## 5. 隔离验收测试（§10 · 一次性库实测）

```text
ACCEPT: 同租户 employee + 同租户 space 分配 → ACCEPTED（T1）
DENY  : tenant A employee + tenant B space  → REJECTED（T6）
DENY  : tenant A employee + tenant B 分配    → REJECTED（T7）
DENY  : tenant A space + tenant B 分配       → REJECTED（T8）
DENY  : UPDATE 变更 tenant 边界（space/employee）→ REJECTED（T9 / T10）
附加  : 重复 active 分配 · 不存在 space · 生命周期 CHECK · 工号 CHECK ·
        同一 (tenant_id,user_id) 第二员工身份 · uap_runtime 跨租户 INSERT → 全部 REJECTED
        uap_runtime 同租户 INSERT → ACCEPTED（SECURITY INVOKER 路径可用）
```

## 6. 迁移链与往返（§2 / §12）

```text
upgrade 0018 → 0019        = PASS（revision=0019_p20_company · company 表=2 · permissions=23）
downgrade 0019 → 0018      = PASS（company 表=0 · permissions=12 · 触发器函数=0）
upgrade again 0018 → 0019  = PASS（permissions=23 · company 表=2）
测试库 before/after        ：一次性库 before = 空库（无 alembic_version）→ after = 0019（见上）
临时库残留                  = 无（探针库已 DROP；库清单 = postgres/template0/template1/uap/uap_b1_test/uap_test）
```

## 7. 回归与平台边界（§11 / §12）

```text
Production Event Allowlist = EMPTY（production_allowlist().is_empty = True）
Handlers = 0 · Producers = 0 · events = 0（共享库与隔离库一致）
Core → Domain = 0          ：架构守卫 tests/architecture = 63 passed
共享测试库 uap_b1_test       ：0017_p13_seed · permissions 12 · company 表 0 · events 0 ·
                             uap_runtime 表级授权 56（验收前后一致，未迁移）
正式库 uap                  ：0 public 表（未执行 migration · 未触碰）
Formal DB touched          = NO
commit / tag / push        = NO（staged = 0）
```

## 8. 验收结论（§13）

```text
Schema Acceptance = PASS
Migration Chain   = PASS
Upgrade           = PASS
Downgrade         = PASS
Isolation         = PASS
Trigger           = PASS
Permissions       = PASS
Runtime Grants    = PASS
Regression        = PASS
Formal DB touched = NO
```

## 9. 非阻塞观察（供下一阶段参考 · 不影响本轮判定）

```text
O1 domains/company/manifest.py 仍是 HEAD 内既有 placeholder（status=placeholder · tables=[] ·
   permissions=['space:read','member:manage'] 冒号式占位字符串）。0019 已落地 2 张业务表后，
   该占位声明与现状不同步 —— 属 P20 COMPANY DOMAIN PREP 的范围（本轮禁止修改 Domain）。
O2 验证脚本 .p20verify/verify_0019_retry.py 仍在仓库外（sha256 B48BC5D9…）。是否提升为
   仓库内 migration 测试（§14 允许「migration related tests」）留待后续裁定。
O3 共享测试库 uap_b1_test 未迁移（保持 0017_p13_seed），Company 表在共享测试库中不存在 ——
   是否迁移属独立授权事项。
```

**END OF P20 MIGRATION ACCEPTANCE REPORT（0019_p20_company = ACCEPTED · 10/10 项 PASS · 隔离矩阵与 OPT-2 触发器实测通过 · 正式库未触碰 · 未 commit/tag/push · 下一阶段候选 = P20 COMPANY DOMAIN PREP；2026-10-02）**
