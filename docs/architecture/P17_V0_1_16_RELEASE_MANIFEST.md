# P17 V0.1.16 RELEASE MANIFEST

```text
release_version  = 0.1.16
release_tag      = UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME
base_commit      = 42a4f61c20fe119af77ab822e24c8028ce653e3d   （0.1.15 · P16 RELEASED）
candidate_commit = <由 commit 阶段生成后回填于 FINAL RECORD>
migration_head   = 0018_p16_agent_runtime（单一 head；P17 未新增 migration）
hash_basis       = committed Git blob bytes（F-RP-06 冻结规则；禁止 worktree 渲染 / CRLF 变换）
```

---

## 1. Release notes（P17 = Platform Identity / Tenant / Space Runtime）

```text
主要新增：
  · platform-level User 保持 tenant-agnostic（users.tenant_id 不承载所有权）
  · 多租户 membership（一个 user 可属多个 tenant；tenant 必须显式选择，禁止 first/default/last 猜测）
  · tenant context resolution（User → Tenant Membership → Tenant → Role Context）
  · 显式 space membership（tenant membership 不隐含任意 space 访问）
  · role scope 集成（role.scope 必须与 membership scope 一致；服务端校验）
  · canonical AuthorizationService 唯一授权引擎（无第二套 engine）
  · member.read / member.admin 授权模型（read/list → member.read；create/update/delete → member.admin）
  · canonical resource projection（Control Plane / Bootstrap 负责；runtime 只消费；缺失即 DENY）
  · membership mutation + audit 原子（audit 失败 ⇒ mutation 回滚）
  · Agent tenant/space context（agent.tenant_id / agent.space_id 显式；无 owner 权限继承）
  · 严格跨租户 / 跨空间隔离（cross-tenant / cross-space = DENY by default）
  · tenant / space / membership read API + membership 管理 API（transport-only handler）

明确未包含（冻结边界）：
  · No schema expansion（new tables = 0）
  · No new migration（migration files 止于 0018）
  · No new runtime privilege（uap_runtime = 56 · delta = 0）
  · No new permission（permissions = 12 · P13 未改写）
  · Production Event Allowlist = EMPTY · Production Handlers = 0
  · Tenant / Space structural CRUD 仍属 Control Plane / Bootstrap（P17 不提供）
  · ACL / role / permission / platform-membership 管理不在 P17 运行时面
  ⇒ 本次发布不包含「tenant/space provisioning API 已全面可用」的能力声明
```

---

## 2. File allowlist（P17 release payload · 33 个路径）

### 2.1 P17 newly added（26）

```text
services/identity_runtime/__init__.py
services/identity_runtime/agent_scope.py
services/identity_runtime/authorization.py
services/identity_runtime/errors.py
services/identity_runtime/membership.py
services/identity_runtime/repository.py
services/identity_runtime/resolver.py
services/identity_runtime/resource_types.py
services/control_plane/__init__.py
services/control_plane/provisioning.py
services/use_cases/identity_runtime.py
apps/api/routes/identity_runtime.py
tests/unit/test_p17_identity_runtime.py
tests/architecture/test_p17_boundaries.py
tests/integration/test_p17_context_resolution.py
tests/integration/test_p17_membership_atomicity.py
tests/integration/test_p17_authorization.py
tests/integration/test_p17_api.py
tests/integration/test_p17_agent_scope.py
tests/integration/test_p17_acceptance.py
docs/architecture/P17_HUMAN_DECISION_PREP.md
docs/architecture/P17_IDENTITY_TENANT_SPACE_RUNTIME_IMPLEMENTATION_CONTRACT.md
docs/architecture/P17_MEMBERSHIP_AUTHORIZATION_GAP_RECORD.md
docs/architecture/P17_IMPLEMENTATION_EVIDENCE.md
docs/architecture/P17_ACCEPTANCE_EVIDENCE.md
docs/architecture/P17_V0_1_16_RELEASE_MANIFEST.md              （本文件）
```

### 2.2 P17 modified（4）

```text
apps/api/main.py                              P17 router 注册（identity-runtime）
apps/api/error_mapping.py                     IdentityRuntimeError → 既有 HTTP taxonomy 映射
services/use_cases/__init__.py                P17 use cases 导出
docs/architecture/PLATFORM_DECISION_LOG.md    附录 W（P17 freeze）+ 附录 X（authorization resolution）
                                              append-only（146 insertions · 0 deletions · A–W 未改写）
```

### 2.3 Version metadata（3）

```text
pyproject.toml · config/settings.py · docker-compose.yml    0.1.15 → 0.1.16
```

### 2.4 Explicitly EXCLUDED（historical dirty · 未纳入 release）

```text
tracked modified（25 · 历史脏文件，保持原样不进入 commit）：
  docs/api/README.md · docs/architecture/ARCHITECTURE.md · docs/architecture/CORE_DOMAIN_MODEL.md ·
  docs/architecture/DEPENDENCY_RULES.md · docs/architecture/STEP1B_*（5）· docs/security/README.md ·
  infrastructure/database/__init__.py · tests/conftest.py · tests/integration/*（14）·
  tests/security/test_authorization_security.py · tests/unit/test_generate_build_info.py
untracked historical（约 102）：AGENT_RUNTIME_*（4 · obsolete）· OPEN_P10_1_*（30）·
  P10–P14 历史文档 · handoff/（17）· 其他历史未跟踪文件
⇒ 保留在工作区，不进入 release commit；工作树允许保持 DIRTY
```

---

## 3. Canonical payload hashes（committed Git blob bytes）

计算方式：`git cat-file blob :<path>`（index blob = commit 时写入的字节）→ SHA-256。
manifest 自身不列入自身哈希（self-hash exclusion · F-RP-06）。

| path | status | sha256 (blob bytes) |
|---|---|---|
| `apps/api/error_mapping.py` | M | `6824a79cfe473d637655ffac77c6f3b27ad118b2cd44c94d5154bbd1d855a9af` |
| `apps/api/main.py` | M | `ee485da235de6201707472d9f42cf008921601afefb9bbe7c1908a68debe6edb` |
| `apps/api/routes/identity_runtime.py` | A | `d2634db911825efbbedee46c95a309c5a92206363a84f214b30a8832d71027d7` |
| `config/settings.py` | M | `58e8a6936061357b40b1f7d0feeac1274335eddfaf546940dc37c764a43245f3` |
| `docker-compose.yml` | M | `6a9f54dc6e26d57ffceca5ef27c7cb150fe1d2e3b7eaaa8448d013e96f01eab2` |
| `docs/architecture/P17_ACCEPTANCE_EVIDENCE.md` | A | `e19f3c5727d8bd680ebe2726e11bff3cf6868532a5a0942e995b93179f32a811` |
| `docs/architecture/P17_HUMAN_DECISION_PREP.md` | A | `0f1244a536c0ad03c81c7ebb43f61f593c67ee820e8a886e046604e0c0d13a3d` |
| `docs/architecture/P17_IDENTITY_TENANT_SPACE_RUNTIME_IMPLEMENTATION_CONTRACT.md` | A | `53b469d189e1a5edf6981274af46e7d18169cd6bba7a2b67242b57b0fce7a37a` |
| `docs/architecture/P17_IMPLEMENTATION_EVIDENCE.md` | A | `239183862ddb985d96efbcc6b3b58e04e2be01b7f95513a32844d5d371ce0fbe` |
| `docs/architecture/P17_MEMBERSHIP_AUTHORIZATION_GAP_RECORD.md` | A | `eb3bef3368f17fa37a49caa305ab5546f967edbd1f39d159cc358e6204959dd7` |
| `docs/architecture/PLATFORM_DECISION_LOG.md` | M | `c747657000d9f9fdcb3d8fce6c79b6c9b0ad0ef059d95e688ca97fc141c9de1e` |
| `pyproject.toml` | M | `524ea5e8ac2d675899e27bd66cc237973a84c7207ab4d2c7b5c59d49fe34b2f9` |
| `services/control_plane/__init__.py` | A | `d74acb88d7298cb147ce8c09889bdae8e654737b7d4bbbe5222319c591f0c424` |
| `services/control_plane/provisioning.py` | A | `25233254b7600626305eb350981740c8df3187a0cfc58927fc333a6e43886cc5` |
| `services/identity_runtime/__init__.py` | A | `bd9fd7d7451061e70739d7ae7c6c7b6d7c09c71b24949b792289588b9fde2f2d` |
| `services/identity_runtime/agent_scope.py` | A | `a6c8a9cafd72dd8ed7c80cb97a5a9b688c6d66b778dc942a0e443fee8168c3f9` |
| `services/identity_runtime/authorization.py` | A | `02130ec1387268b9da173857782166e1e8914d6e48e1e89975d49c7030fbefff` |
| `services/identity_runtime/errors.py` | A | `be6ad3c798d2829bd7388c38b3d709eabaa09bff5cd5b61e155d8a498816396d` |
| `services/identity_runtime/membership.py` | A | `34106fd3d1d230d5950903a5c1b26f104c506c31065c485dff569c37f713d473` |
| `services/identity_runtime/repository.py` | A | `9e7c26c22ff4c80fa3207d39fa7ee96f4e37ca1b503601b53ed9c9d8b9762a69` |
| `services/identity_runtime/resolver.py` | A | `3ef1089395255a077385bdb5670d303b51709718baf4b46ca813e5f730ed7e5d` |
| `services/identity_runtime/resource_types.py` | A | `0408591694dbcc2fb63e45076532450592e116dfbf879b94fe099e5fdddf6c38` |
| `services/use_cases/__init__.py` | M | `2c3b6bd54d2c303e31bc15041d328b1eb8ee65ca423b9768a24f3e9400e140ca` |
| `services/use_cases/identity_runtime.py` | A | `f868fd0884fb7c3879a32bfc13e025459029af02410c1e45dcf0c946a491d87f` |
| `tests/architecture/test_p17_boundaries.py` | A | `24bdd589d409b380cba617cdee316b30d8872b60cbff73f8d8d2f65b4c297ae8` |
| `tests/integration/test_p17_acceptance.py` | A | `fb5ffec5f70e6074100e95d19963440d13688d1054f5d3a9aee1fede131432e4` |
| `tests/integration/test_p17_agent_scope.py` | A | `e646ac65cdc35216c478c4f7c6312049889cd908dfcf76b00ecf5697d54f1740` |
| `tests/integration/test_p17_api.py` | A | `09ca3d610d8130dfd85892645d952f1bfb7d16f8c9fb39c01a907e3bba610574` |
| `tests/integration/test_p17_authorization.py` | A | `8c1fbb4c7c641775c9fe14cbe9a616444c9262cbc5a8c383db1b8de003fed716` |
| `tests/integration/test_p17_context_resolution.py` | A | `f4183b301a4d8772af0bb422f61130379a0c50908706d5b1f2f655396053c6f2` |
| `tests/integration/test_p17_membership_atomicity.py` | A | `1f1df10dc4dc53d0cf0f660e38f68d4c190984a7b2de6c085ed2bd7b1320055c` |
| `tests/unit/test_p17_identity_runtime.py` | A | `bcafb78f28dc97d503ae3d6a5adc5c13c0172017de6be06eafbdeeb5529bc1d6` |

```text
说明：blob 哈希与工作区文件哈希不同是预期行为（.gitattributes: * text=auto eol=lf）。
      release 权威字节 = committed blob（F-RP-06）；clean clone 可完全重现本表。
```

---

## 4. Test results（release candidate 复验）

```text
P17（8 文件显式 allowlist）      = 97 passed / 0 failed / 0 skipped
P16 unit/arch/security           = 33 passed / 0 failed
P16 integration + R-1 durability = 8 passed / 0 failed（6 scenarios + 2）
P15（4 文件显式 allowlist）       = 65 passed / 0 failed
architecture guards              = 57 passed / 0 failed
forbidden tests = 0 · OI-G-4 = 0 · 目录级 pytest = 0 · skip/xfail/deselect = 0
Core → Domain = 0
```

## 5. Security / DB / boundary

```text
cross-tenant bypass = 0 · cross-space bypass = 0 · agent/user inheritance = 0
visibility bypass = 0 · resource fail-open = 0 · authorization bypass = 0
secret leakage = 0 · unexpected privilege = 0

uap_runtime grants = 56（delta = 0）· uap_app = 5 · uap_migrator = 245 · roles = 6
default ACL = 0 · public schema PUBLIC grants = 0 · tenants/spaces = SELECT only

schema = UNCHANGED（new tables = 0）· migration = NONE · head = 0018_p16_agent_runtime
Production Event Allowlist = EMPTY · Production Handlers = 0
Formal DB（uap）= prestate == poststate
临时测试库 = 全部 DROP（仅保留 uap / uap_b1_test / uap_test）
```

---

**END OF P17 V0.1.16 RELEASE MANIFEST（P17 payload = 33 paths · 26 added + 4 modified + 3 version · hash basis = committed blob bytes · 历史脏文件显式排除；2026-10-01）**
