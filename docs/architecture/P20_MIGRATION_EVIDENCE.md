# P20 MIGRATION IMPLEMENTATION EVIDENCE — 0019_p20_company

```text
阶段       = P20 MIGRATION AUTHORIZATION — RETRY AFTER OPT-2 FREEZE
授权依据   = 本轮指令 §3–§10（创建 0019_p20_company · OPT-2 结构隔离）
冻结权威   = PDL 附录 AC / AD / AE（D-P20S-01…16）
基线       = UAP-V0.1.17-P18-CONTROL-PLANE（commit 08a0485b · tags 16）
执行环境   = 一次性隔离库 uap_p20_0019_verify（创建 → 验证 → DROP；正式库 uap 只读未触碰）
产物       = migrations_alembic/versions/0019_p20_company.py
             sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（13006 bytes）
```

## 1. 交付物内容（唯一新增仓库产物）

```text
revision      = 0019_p20_company
down_revision = 0018_p16_agent_runtime

company_employees    PK id(uap_uuid_v7) · FK tenant→tenants RESTRICT · FK user→users RESTRICT（可空）
                     UNIQUE (tenant_id, employee_no) · UNIQUE (tenant_id, user_id) WHERE user_id IS NOT NULL
                     CHECK status ∈ {active,suspended,terminated} · CHECK employee_no 格式
                     CHECK (status='terminated') = (terminated_at IS NOT NULL)
                     INDEX (tenant_id,status) · (user_id) WHERE user_id IS NOT NULL
                     TRIGGER tg_company_employees_set_updated_at（复用 set_updated_at()）
company_assignments  PK id(uap_uuid_v7) · FK tenant→tenants RESTRICT · FK space→spaces RESTRICT
                     · FK employee→company_employees CASCADE
                     CHECK status ∈ {active,ended} · CHECK assignment_role ∈ {member,lead}
                     CHECK (status='ended') = (ended_at IS NOT NULL)
                     UNIQUE (employee_id, space_id) WHERE ended_at IS NULL
                     INDEX (tenant_id,space_id,status) · (employee_id,status) · (tenant_id,status)
                     TRIGGER tg_company_assignments_set_updated_at（复用 set_updated_at()）
OPT-2 结构触发器      enforce_company_assignment_tenant_consistency()
                     BEFORE INSERT OR UPDATE ON company_assignments · SECURITY INVOKER（默认）
                     · 仅校验 NEW.tenant_id = employee.tenant_id AND = spaces.tenant_id
                     · 失败 RAISE EXCEPTION（原子回滚）· 不授权 / 不 DML / 不写 audit / 不产生事件
permission seed      11 条 Company business permission（company_employee.* ×6 · company_assignment.* ×5）
                     action 全部取自既有 canonical 12 actions · is_system = false · 无 deny · 无 role grant
运行时授权           uap_runtime：company_employees / company_assignments 均 SELECT, INSERT, UPDATE
                     （无 DELETE / TRUNCATE / REFERENCES / TRIGGER）
```

## 2. 前置状态 / 后置状态（§13）

```text
BEFORE（一次性库）：alembic_version 不存在（空库）
AFTER （一次性库）：revision = 0019_p20_company · company 表 = 2 · permissions = 23（12 + 11）
正式库 uap          ：0 public 表（未触碰 · 前后一致）
共享测试库 uap_b1_test：alembic = 0017_p13_seed · permissions = 12 · company 表 = 0 ·
                        events = 0 · uap_runtime 表级授权 = 56（前后一致）
临时库残留          ：无（探针库已 DROP；库清单 = postgres / template0 / template1 / uap / uap_b1_test / uap_test）
```

## 3. 迁移往返（§12）

```text
upgrade 0018 → 0019        = PASS
downgrade 0019 → 0018      = PASS（company 表 = 0 · permissions = 12 · 触发器函数 = 0）
upgrade again 0018 → 0019  = PASS（revision = 0019_p20_company · permissions = 23 · company 表 = 2）
```

## 4. 隔离与结构测试矩阵（§12 · 全部实测）

```text
T1  same-tenant INSERT                        → ACCEPTED
T2  same-tenant 业务字段 UPDATE                → PASS
T3  重复 active assignment（部分唯一）          → REJECTED（IntegrityError）
T4  生命周期 UPDATE（ended + ended_at）         → PASS
T5  结束后的再次分配                            → ACCEPTED（符合部分唯一语义）
T6  tenant A employee + tenant B space         → REJECTED（触发器）
T7  tenant A employee + tenant B assignment    → REJECTED（触发器）
T8  employee A + space B + assignment tenant A → REJECTED（触发器）
T9  UPDATE 改 space 至他租户                    → REJECTED（触发器）
T10 UPDATE 改 employee 至他租户                 → REJECTED（触发器）
T11 不存在的 space                              → REJECTED
T12 terminated 但 terminated_at IS NULL         → REJECTED（CHECK）
T13 非法 employee_no                            → REJECTED（CHECK）
T14/T15 同一 (tenant_id, user_id) 第二员工身份   → REJECTED（部分唯一 · D-P20S-07）
T16 uap_runtime 同租户 INSERT                   → ACCEPTED（触发器 SECURITY INVOKER 下可用）
T17 uap_runtime 跨租户 INSERT                   → REJECTED（触发器）
T18 uap_runtime DELETE                          → REJECTED（无 DELETE 权限）
T19 uap_runtime ALTER TABLE                     → REJECTED
T20 uap_runtime DROP TRIGGER                    → REJECTED
```

```text
触发器函数实测：prosecdef = false（SECURITY INVOKER）· language = plpgsql ·
                writes_dml = false · writes_audit = false · writes_events = false
permissions  ：total = 23 · company = 11 · action ⊆ canonical 12 · resource_type ∈
                {company_employee, company_assignment} · is_system 全 false ·
                company 相关 role_permissions = 0 · acl_subject_types = 3（未变）
runtime 授权  ：company_assignments = INSERT,SELECT,UPDATE · company_employees = INSERT,SELECT,UPDATE
```

## 5. 与冻结矩阵的一致性（含 1 项显式取舍）

```text
① company_assignments.employee_id 删除动作：
   授权文 §5 只写「employee_id → company_employees.id」（未指定删除动作），
   冻结矩阵 / 实体目录 / 关系矩阵三处一致写明 ON DELETE CASCADE（「员工删除随删分配」）。
   本轮采用 CASCADE（依冻结矩阵）。D-P20S-09 的「无物理 DELETE」是运行时权限规则
   （uap_runtime 无 DELETE · 终止 = 状态变更），应用路径不可达该级联。
   （越界草稿曾写 RESTRICT —— 已按冻结矩阵修正。）
② hired_at = 可空（实体目录：NULL · 可变 · 未列入 NOT NULL 清单）；草稿曾写 NOT NULL DEFAULT now() —— 已修正。
③ 索引集按冻结矩阵对齐：employees (tenant_id,status) ＋ (tenant_id,employee_no 由唯一约束承担) ＋
   (user_id) WHERE user_id IS NOT NULL ；assignments (tenant_id,space_id,status) ＋
   (employee_id,status) ＋ (tenant_id,status)。未添加任何「保险型」无语义约束。
④ OPT-2：未创建 (tenant_id, space_id) → spaces(tenant_id, id) 复合 FK；未修改 spaces；未新增 UNIQUE 到 spaces。
```

## 6. 未做（边界声明）

```text
未修改 tenants / spaces / memberships / users / roles / identities / audit_logs / events ·
未修改任何既有 permission 行（仅新增 11 条 Company 行）· 未 seed role_permissions ·
未新增 ACL subject type / canonical action · 未实现 Company Domain / API / worker / producer / handler ·
未激活生产事件（Allowlist EMPTY · Handlers 0 · Producers 0 · events 0）·
未修改任何历史 migration（0018 及以前零改写）· 正式库 uap 未触碰 · 未 commit / tag / push
```

## 7. 复现方式与遗留

```text
复现：在一次性隔离库上运行 alembic upgrade head（0018 → 0019）；
      验证脚本 = .p20verify/verify_0019_retry.py
      （sha256 B48BC5D956AF28FEC15C51091EB678EAB96536FCC64AE43287929551A7C4288E，
       当前位于仓库外会话工作目录，未随本轮授权写入仓库）。
遗留：① 是否把该验证脚本提升为仓库内 migration 测试（§14 允许「migration related tests」），
        留待 P20 MIGRATION ACCEPTANCE GATE 裁定；
      ② 共享测试库 uap_b1_test 未迁移（保持冻结基线 0017_p13_seed，等待独立授权）。
```

**END OF P20 MIGRATION IMPLEMENTATION EVIDENCE（0019_p20_company 已实现并在一次性隔离库验证 · upgrade/downgrade/upgrade-again 全 PASS · 结构隔离矩阵 T1–T20 全符合预期 · 正式库与共享测试库未变 · 未 commit/tag/push；2026-10-02）**
