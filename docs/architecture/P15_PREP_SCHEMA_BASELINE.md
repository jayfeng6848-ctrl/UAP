# UAP — P15 PREP SCHEMA BASELINE

> 轮次 = STEP 3 · P15 PREP（只读 DB 审计 · 未执行 CREATE/ALTER/DROP/DML/GRANT/REVOKE/alembic）

## 1. Test DB（uap_b1_test · P14 release 后的 schema truth）

```text
alembic_version        = 0017_p13_seed（current == head）· 0018+ = 0
migration files        = 0001 … 0017
pg_class(public r/p/i/I) = 156 · pg_proc(public) = 22 · pg_trigger = 272（parent 39）
schema count           = 1（public）
partitions             = audit_logs_202609 · events_202609（P10 既有分区）
```

## 2. 角色与权限指纹（未变）

```text
roles = 6：uap（superuser）· uap_app · uap_bootstrap · uap_migrator · uap_runtime · uap_seed
row grants：uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 · uap_migrator 245
pg_default_acl = 0 · user-defined memberships = 0 · ownership residual = 0
public schema：CREATE=false（非 uap 角色）· USAGE=true
C2  = enforce_acl_subject_types_protect() md5 185e95be8bc4304edbcd3f4d5cda1eff（trigger enabled=O）
CC-7 = 受信迁移分支（current_user ∧ session_user = uap_migrator）存在
P13 seed = acl_subject_types 3 / permissions 12 / role_permissions 12
platform_state = 1（uninitialized）· platform_memberships = 0
```

## 3. 正式库 uap

```text
tables = 0 · default_acl = 0 · memberships = 0 · roles 6（集群级）
prestate == poststate ⇒ Formal DB Mutation = 0
```

## 4. 关键既有约束（P15 必须遵守）

```text
users      ck_users_login · ck_users_status(5) · uq_users_email/username(lower, partial)
identities ck_identities_provider/status · uq_identities_email · uq_identities_ref
credentials ck_credentials_type/algorithm/secret · uq_credentials_active_password
devices    ck_devices_status(5) · uq_devices_fingerprint(user_id,fingerprint)
sessions   ck_sessions_status/expiry · uq_sessions_token · uq_sessions_refresh
memberships/tenant_memberships ck_*_status(4) + P11 触发器 enforce_roles_scope_shape /
           enforce_tm_role_scope / enforce_membership_role_scope
roles      ck_roles_key/scope/status
audit_logs tg_audit_immutable（append-only · UPDATE/DELETE 一律 RAISE · D-P10-11）
```

## 5. P15 schema 结论

```text
0017 = current schema truth（P15 分析基线）
本阶段未发现"必须新增"的 schema 对象（P15 scope 未冻结）
若任一 candidate 需要新 table/column/index/constraint/trigger/function/enum/permission
  ⇒ 登记 `SCHEMA DECISION REQUIRED`（RTA-10 = OPTION B）· 不得实现
```

**END OF P15 PREP SCHEMA BASELINE（2026-09-28 · 0017 truth · 指纹未变 · DB mutation 0 · HARD STOP ACTIVE）**
