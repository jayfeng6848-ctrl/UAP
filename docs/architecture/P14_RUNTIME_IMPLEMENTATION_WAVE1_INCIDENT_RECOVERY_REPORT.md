# UAP — P14 RUNTIME IMPLEMENTATION WAVE 1 INCIDENT RECOVERY REPORT

> ## 状态
>
> ```text
> 轮次      = P14 WAVE 1 INCIDENT RECOVERY + TEST SCOPE REMEDIATION + EVIDENCE RESTORATION
> 授权      = HD-P14-REC-01（AUTHORIZED — RESTORE uap_b1_test · TARGET = uap_b1_test ONLY）
>             HD-P14-REC-02（REGISTER ONLY · 不顺手修复）
>             HD-P14-REC-03（新载体双归属：execution governance → BATCH-D；semantics → P14）
> 结果      = 测试库 RESTORED（逐指纹一致）· 正式库 UNCHANGED · 活体证据重新取得
> Git       = HEAD c420403d… · commit / tag / push = 0
> ```

---

# 1. Incident Summary

```text
时间      = 2026-09-28（P14 RUNTIME IMPLEMENTATION WAVE 1 的测试执行阶段）
类别      = CF-C-4 TEST EXECUTION SCOPE VIOLATION
直接诱因   = Agent 以目录级参数运行 pytest，连通 `tests/security/` 把 CF-C-4 禁跑文件
            tests/security/test_authorization_security.py 纳入执行
后果      = 该文件 fixture 的 reset_test_database() 在断言之前 DROP/CREATE uap_b1_test
            ⇒ SECURITY EVIDENCE FREEZE 的**库内基线**被摧毁（仓库文件与 Git 未受影响）
当前状态   = 已恢复（HD-P14-REC-01）；证据已重新取得；事故证据独立保留（本文件）
```

---

# 2. Triggering Test File

```text
file = tests/security/test_authorization_security.py
fixture:
    @pytest.fixture()
    def env():
        reset_test_database()                                  # (A) DROP/CREATE uap_b1_test
        upgrade(make_config(lock_mode="fail"), "head")
        assert current_revision() == "0015_p12_indexes"         # (B) 陈旧断言 ⇒ 必失败
        ...
        yield engine, ids
        engine.dispose()
        reset_test_database()                                  # (C) 再次 DROP/CREATE

触发命令:
    python -m pytest -q tests/unit tests/architecture tests/security tests/contract \
           --ignore=tests/unit/test_generate_build_info.py
结果:
    275 passed · 26 errors（errors 全属上述 fixture 的 setup 失败）
```

---

# 3. CF-C-4 Scope Violation

```text
CF-C-4（现行裁定 = C）原文语义：integration / reset_test_database 冲突**延后 BATCH-D**；
19 个含 reset_test_database() 的文件在 BATCH-D 决议前**禁跑**
（integration 18 + tests/security/test_authorization_security.py）。

违规点 = 使用 **目录级** pytest 参数（tests/security），使禁跑文件被递归发现并执行。
⇒ 本文件是事故的**执行范围缺陷**，而非 P14 Runtime 语义缺陷。
```

---

# 4. Destructive Fixture Behavior

```text
tests.integration.alembic_testkit.reset_test_database():
    admin DSN → postgres 库（身份 uap）
    DROP DATABASE IF EXISTS "uap_b1_test" WITH (FORCE)
    CREATE DATABASE "uap_b1_test"

特性（事故放大因素）:
  · 无 autouse，但位于 fixture **setup 的前段** —— 断言之前即已破坏
  · setup 失败时该 fixture 自身 teardown 不执行；而 reset 已在 setup 内完成
  · 因此"测试失败"与"数据库已被重建"同时发生，且失败本身不阻止破坏
```

---

# 5. Actual Database Impact（catalog 实测）

```text
事故前（2026-09-28 · work/wave1_pre_freeze.json）
  alembic_version 0017_p13_seed · pg_class(public) 156 · pg_proc(public) 22
  parent triggers 39 · pg_trigger 272 · pg_default_acl 0 · user memberships 0
  grants uap_app 5 · uap_bootstrap 6 · uap_seed 0 · uap_migrator 245 · uap_runtime 51
  C2 md5 185e95be8bc4304edbcd3f4d5cda1eff · registry/permissions/role_permissions 3/12/12
  public nspacl {pg_database_owner=UC, =U, uap_app=U, uap_runtime=U, uap_bootstrap=U}

事故后（work/wave1_post_incident_state.json）
  alembic_version 表不存在 · pg_class 0 · pg_proc 0 · C2 函数不存在 · trigger 0
  grants 仅 uap（超用户隐式）· public nspacl {pg_database_owner=UC, =U}
  角色本体 6 个仍在（属性与口令未变 —— 角色是集群级对象）
```

---

# 6. Formal DB Impact = 0

```text
正式库 `uap`：事故前后**均未参与任何动作**
  事故前 prestate : pg_class 0 · pg_proc 0 · default_acl 0 · grants 仅 uap · roles 6
  恢复后 poststate: 同上（prestate == poststate ⇒ **UNCHANGED = True**）
本恢复轮对 `uap` 执行的动作 = 0（仅 SELECT 读取）
⇒ Formal Security Evidence Freeze = **INTACT**
```

---

# 7. Test DB Impact

```text
uap_b1_test：事故期间 DESTROYED → 恢复后 **RESTORED**
恢复方式 = 既有 migration chain（0017）+ 冻结 Security DB Boundary 的精确重放
恢复后与事故前基线：**28 项指纹逐项 SAME（0 diff）**
永久测试数据残留 = 0（users 0 · audit_logs 0；所有写入均在事务内回滚）
```

---

# 8. Recovery Steps（实际执行序列）

```text
R-0  只读 Prestate（work/recovery_prestate.py）
       → uap_b1_test = 空库；uap（formal）状态记录完毕
R-1  打开 CF-C-5=B 窗口：GRANT CREATE ON SCHEMA public TO uap_migrator
       （实测：CREATE false → true；nspacl 出现 uap_migrator=C）
R-2  迁移恢复（identity = uap_migrator · UAP_MIGRATION_DATABASE_URL 单源）
       python -m alembic -c alembic.ini upgrade head          → exit 0
R-3  关闭窗口：REVOKE CREATE ON SCHEMA public FROM uap_migrator
R-4  精确重放冻结授权（identity = uap · schema owner）
       USAGE：uap_app · uap_runtime · uap_bootstrap
       表授权：uap_app 5 · uap_runtime 51 · uap_bootstrap 6
R-5  逐向校验（集合相等 · 无缺无多）+ 指纹对账
R-6  按 allowlist 重跑合法测试（6 组）并复核零漂移
```

```text
未执行：CREATE ROLE · ALTER ROLE · 口令重置 · ALTER OWNER · 0018 migration ·
        env.py 修改 · migration 文件修改 · 任何针对 `uap` 的 DDL/DML
```

---

# 9. Migration Recovery Evidence

```text
command   = python -m alembic -c alembic.ini upgrade head
identity  = UAP_MIGRATION_DATABASE_URL → uap_migrator（env.py 角色断言通过）
exit      = 0

恢复后实测
  alembic_version                 = 0017_p13_seed        （期望 0017_p13_seed）
  0018+                           = 0
  pg_class(public, r/p/i/I)       = 156                   （= 事故前 156）
  pg_proc(public)                 = 22                    （= 事故前 22）
  parent triggers                 = 39                    （= 事故前 39）
  pg_trigger total                = 272                   （= 事故前 272）
  ownership residual (rel/proc)   = 0 / 0                 （全部 owner = uap_migrator）
  public schema owner             = pg_database_owner
  C2 md5                          = 185e95be8bc4304edbcd3f4d5cda1eff（与事故前**逐字节一致**）
  registry/permissions/role_permissions = 3 / 12 / 12
```

```text
⇒ catalog 计数与事故前**完全一致**，无需按 §八 引入"系统目录差异"解释：
  差异 = 0，因此不构成 project object drift。
```

---

# 10. Security Grant Replay Evidence

```text
重放源 = P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md + P14_SECURITY_IMPLEMENTATION_REPORT.md §6/§12
         （既已批准、实施、验收；本轮**不重新设计权限**）

集合相等校验（集合比较，双向：无缺、无多）
  [OK] uap_runtime  = 51 项（SELECT 26 · INSERT 12 · UPDATE 10 · DELETE 3）
  [OK] uap_bootstrap=  6 项（platform_state S/U · platform_memberships S/I · audit_logs I · audit_logs_202609 I）
  [OK] uap_app      =  5 项（alembic_version S · audit_logs S/I · audit_logs_202609 S/I）
  [OK] uap_seed     =  0 项

计数（information_schema.role_table_grants）
  uap_app 5 · uap_bootstrap 6 · uap_migrator 245 · uap_runtime 51 · uap_seed 0

其他不变量
  [OK] public nspacl = {pg_database_owner=UC, =U, uap_app=U, uap_runtime=U, uap_bootstrap=U}
  [OK] pg_default_acl = 0
  [OK] ownership residual（pg_class / pg_proc）= 0 / 0
  [OK] function EXECUTE grants（uap_runtime / uap_bootstrap / uap_app / uap_seed）= 0/0/0/0
  [OK] user-defined memberships = 0
  [OK] 无 GRANT ALL / 无 ON ALL TABLES / 未使用 ALTER DEFAULT PRIVILEGES

⇒ verify failures = 0
```

---

# 11. Test Execution Scope Correction

```text
新增治理载体 = docs/architecture/P14_RUNTIME_WAVE1_TEST_EXECUTION_MANIFEST.md
  · EXPLICIT ALLOWLIST（逐文件 · 25 条 · 6 组）——禁止目录级参数
  · DENY SET（CF-C-4 19 条 + OI-G-4 1 条）
  · DESTRUCTIVE FIXTURE 治理（allowed / forbidden / target / recovery）
  · 间接执行封堵：directory discovery · recursion · import side effect · fixture reuse
  · 本次执行组 = Architecture → Contract → Unit → Integration → Security allowed → Acceptance subset

本轮实际执行（全部为显式文件参数 · 未出现任何 DENY 文件）
  1 Architecture                     28 passed
  2 Contract                         23 passed
  3 Runtime Unit                     20 passed
  4 Runtime Integration              13 passed
  5 Security allowed                 46 passed
  6 P14 acceptance subset            81 passed
  合计                             = 211 passed · 0 failed · 0 deny-file executed
```

---

# 12. Stale Head OI Registration

```text
ID                 = OI-G-9（扫描现行台账后取下一个未占用编号；现行最大 OI-G-8）
Status             = REGISTERED / UNFIXED · Owner stage = BATCH-D
Active 面           = tests/security/test_authorization_security.py:158
Latent 面           = 16 个 CF-C-4 integration 载体（详见 BATCH-D OI REGISTRATION §2）
Expected head      = 0017_p13_seed · bad expectation = 0015_p12_indexes
Related（不重复）    = tests/unit/test_generate_build_info.py（既有 OI-G-4）
本轮处置            = REGISTER ONLY（依 HD-P14-REC-02 · 未顺手修复）
```

---

# 13. New Test Carrier BATCH-D Governance

```text
双归属（HD-P14-REC-03）：execution governance → CF-C-4 / BATCH-D；
                        semantic ownership → P14 Runtime
登记字段 = file / type / destructive-non-destructive / allowed context /
           forbidden context / fixture dependency / DB target / head assumption
登记载体 = docs/architecture/P14_RUNTIME_WAVE1_BATCHD_OI_REGISTRATION.md §3
物理迁移 = 0（未移动任何文件）
```

---

# 14. Post-Recovery Validation

```text
uap_b1_test 指纹对账（恢复后 vs 事故前基线 · 28 项键）
  DIFF keys = NONE
  roles 6（属性/口令未变）· memberships 0 · default_acl 0 · nspacl 一致
  grants 5 / 6 / 245 / 51 / 0 · pg_class 156 · pg_proc 22 · owner residual 0
  C2 md5 一致 · c2 trigger 一致 · parent triggers 39 · pg_trigger 272
  registry / permissions / role_permissions = 3 / 12 / 12
  users 0 · audit_logs 0 · alembic_version 0017_p13_seed · 0018+ = 0
  受保护文件 sha256（env.py / 0016 / 0017 / PDL）= 未变

正式库 uap
  prestate == poststate ⇒ UNCHANGED = True（pg_class 0 · pg_proc 0 · default_acl 0 ·
  grants 仅 uap · roles 6）

测试执行后再复核（§7 / §9 事故面不得复现）
  uap_b1_test 仍与基线 0 diff · formal uap 仍 UNCHANGED
```

```text
恢复过程中顺带发现并修复的 **Wave 1 实现缺陷**（由新取得证据暴露）
  D-W1-1（真实 fail-closed 缺陷）
    file   = infrastructure/database/runtime.py
    defect = `except PrincipalAssertionError:` 引用未导入名称 ⇒ 抛出 NameError
             而非既定的 PrincipalAssertionError（fail-closed 语义被破坏）
    fix    = 在 `infrastructure.runtime.errors` 导入列表中补入 PrincipalAssertionError
    verify = tests/integration/test_runtime_db_wave1.py::
             test_principal_assertion_is_enforced_not_merely_configured（PASS）
  D-W1-2（测试载荷缺陷）
    file   = tests/integration/test_runtime_db_wave1.py
    defect = 回滚证明用例插入 users 时未满足 `ck_users_login`
    fix    = 载荷补 email（仍全程事务内回滚 · 无残留）
  ⇒ 两项均由本轮"可执行的活体证据"发现，未越出 Wave 1 范围
```

---

# 15. Wave 1 Evidence Status

```text
历史证据（不改写）
  P14 SECURITY IMPLEMENTATION 原始 evidence = 保持历史（P14_SECURITY_* 全部文件未修改）
  Incident Report（WAVE1_INCIDENT_REPORT）= 独立保留 · 不删除 · 不覆盖

本轮重新取得的活体证据
  Runtime DB live evidence      = 已取得（13 passed · current_user = session_user = uap_runtime）
  Persistence live evidence     = 已取得（approved SELECT · begin · commit proof via pg_xact_status
                                  = 'committed' · rollback observed = 'aborted' · 无残留）
  Security live evidence        = 已取得（46 passed · DENY 面逐项 42501 · ALLOW 面与 Matrix 一致）

判定
  Formal Security Evidence Freeze = INTACT（正式库未被触碰）
  Test Evidence Baseline           = RESTORED（逐指纹一致）
  P14 Runtime Wave 1               = READY FOR FINAL ACCEPTANCE（状态由 BLOCKED 解除）

本轮不做
  Identity / Device / Session / API / Bootstrap CLI = NOT STARTED
  Wave 2 = NOT STARTED · P15 = FORBIDDEN
  commit / tag / push = 0
```

**END OF P14 RUNTIME IMPLEMENTATION WAVE 1 INCIDENT RECOVERY REPORT（2026-09-28 · 测试库 RESTORED · 正式库 INTACT · 活体证据重取得 · 未 commit/tag/push · HARD STOP ACTIVE）**
