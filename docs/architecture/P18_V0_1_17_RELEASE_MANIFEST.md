# P18 V0.1.17 RELEASE MANIFEST

```text
release_version  = 0.1.17
release_tag      = UAP-V0.1.17-P18-CONTROL-PLANE
base_commit      = 9fe282b009aba3965236402971ab963694f7ce05   （0.1.16 · P17 RELEASED）
base_tree        = de420083cbb3fa01b77e7d4d0cc7c317bebba06c
candidate_commit = <commit 阶段回填于 FINAL RECORD>
migration_head   = 0018_p16_agent_runtime（P18 未新增 migration）
hash_basis       = committed Git blob bytes（F-RP-06：禁止 worktree 渲染 / CRLF 变换）
```

## 1. Release notes（P18 = Platform Control Plane / Tenant-Space Lifecycle）

```text
主要新增：
  · 专用控制面 DB 主体 uap_control（D01 · 版本化 role provisioning · 最小权限 23 grants）
  · Control Plane 授权模型（D06 + 附录 AA）：所有控制面授权一律 PLATFORM scope，
    resource / object identity 仅作审计与用例上下文（既有 canonical AuthorizationService，
    新增唯一 additive 入口 resource=None + 显式 resource_type）
  · Tenant 生命周期（provisioning→active · active↔suspended · active/suspended→archived ·
    archived→active · archived→deleted · deleted 终态 · 无物理删除）
  · Space 生命周期（create→active · active↔archived · archived→deleted · deleted 终态）
  · 原子 provisioning：对象 + 管理员角色 + role_permissions + canonical 资源投影 +
    初始成员 + 审计 同事务；任一失败整体回滚（无半初始化）
  · 初始管理员显式指定（tenant：任意 active 用户；space：须已属目标 tenant）
  · 非 system 作用域管理员角色（tenant_admin / space_admin · 绑定既有 canonical permission）
  · 幂等：自然键 exact replay；不一致 = CONFLICT
  · 控制面 API（/control 命名空间 · 无 DELETE 端点 · 无通用 CRUD · 防枚举）
  · 主体分离（F-P18-I-04 Option ①）：认证 = 应用身份边界；结构写 = 专用 uap_control 连接
  · D14 运行时生命周期门禁：仅 ACTIVE Tenant/Space 可建立普通运行时上下文；
    Agent Run admission 同样受门禁（active 语义逐字不变）

明确未包含（冻结边界）：
  · No schema change（new tables = 0）· No new migration（head 保持 0018）
  · No new permission（permissions = 12）· No expansion of uap_runtime（保持 56）
  · Production Event Allowlist = EMPTY · Production Handlers = 0
  · Tenant/Space 物理删除 · ACL 管理 · 业务模块
```

## 2. File allowlist（P18 release payload · 35 路径）

```text
modified（15）：apps/api/{dependencies,error_mapping,main}.py · config/settings.py ·
  docker-compose.yml · docs/architecture/PLATFORM_DECISION_LOG.md（附录 AA · append-only）·
  pyproject.toml · services/agent/use_cases.py ·
  services/authorization/{audit,permissions,service}.py ·
  services/identity_runtime/{__init__,agent_scope,errors,resolver}.py ·
  services/use_cases/__init__.py · tests/architecture/test_p17_boundaries.py ·
  tests/unit/test_p17_identity_runtime.py
added（20）：apps/api/routes/control_plane.py · scripts/role_provisioning.py ·
  services/control_plane/{errors,repository}.py · services/use_cases/control_plane.py ·
  tests/architecture/test_p18_control_plane_boundaries.py ·
  tests/unit/test_p18_pre_resource_authorization.py ·
  tests/integration/test_p18_{control_plane_authorization,control_plane_provisioning,
    control_plane_metadata_and_gate,control_api_http}.py ·
  docs/architecture/P18_{HUMAN_DECISION_PREP,DEPENDENCY_MAP,
    CONTROL_PLANE_TENANT_SPACE_LIFECYCLE_IMPLEMENTATION_CONTRACT,CONTROL_PLANE_GAP_RECORD,
    IMPLEMENTATION_EVIDENCE,ACCEPTANCE_EVIDENCE}.md
excluded：全部历史脏文件（tracked 28 + untracked ~105）原样保留、未纳入
```

## 3. Canonical payload hashes（committed Git blob bytes · manifest 自身排除）

```text
apps/api/dependencies.py                             a4ab7b09af96828e3a13a929d0cf809b1f26e3b6ad2956617d07d66921fdc326
apps/api/error_mapping.py                            5c270ddfcf0686c17ea4431f5574731c0958b3150af36d4a2668343d9db8f2e8
apps/api/main.py                                     bd2f7194ba4da43a64999bd4c58c730afb658bba79d5c48d13f9441aad59b0c7
apps/api/routes/control_plane.py                     1f70058c473743a82d75be2038bc9f3fa22d3186abbb07404764ca6e79c59da5
config/settings.py                                   2dad095c0730ea26c88fb02eacace8e187f61f548a4e596f3a54665538685fec
docker-compose.yml                                   b9500e9c9a8768c2ea9bd6754aa7cc5b77c344c7e69f7b090722540a169ed542
docs/architecture/P18_ACCEPTANCE_EVIDENCE.md         6f89a1a2d3c15080a14af2d35b7a2aafb1ea63c26037d98b834975c03dba1683
docs/architecture/P18_CONTROL_PLANE_GAP_RECORD.md    1031261686d1cfd2229c9fd9b55c03b10fa50d2fd3e6167dd704c98760c168c9
docs/architecture/P18_CONTROL_PLANE_TENANT_SPACE_LIFECYCLE_IMPLEMENTATION_CONTRACT.md
                                                     24e7710549fdd5638409ec4d16840508f59cd235a76ab100b4601a8f8f26115a
docs/architecture/P18_DEPENDENCY_MAP.md              df0facee0f72b27323a0c290dbcb24bfc05eccd9996362cfef9fb32d0538be7c
docs/architecture/P18_HUMAN_DECISION_PREP.md         5621b5a5ba60ce4fabadbcb848c81aaec09aa35dd1c8ec40e83ce48a5f47c7ab
docs/architecture/P18_IMPLEMENTATION_EVIDENCE.md     65f09d22b53da22e6bced4e73031f0a190a72cd3b6f51b1744faea4b3b34cb8f
docs/architecture/PLATFORM_DECISION_LOG.md           e623fccff79427c458e770186cb7e3be0ce6908ce59d8bbff7dab37841e3cf2d
pyproject.toml                                       5b6196d7bec176f5be24a8c9462eb01296e52d2a689f962bf9bbc06e08f7f3d5
scripts/role_provisioning.py                         419a7b6c050aa8e54f61afc6c1e4b5ad3bb176c8fef2fd54ef73ba9414e03874
services/agent/use_cases.py                          9097d4139e1781636cd5d6c361647715383d4127c2cdef468974488362803e9f
services/authorization/audit.py                       c7233866d4b7fc73008b2069385a44d2329d70c44c937ea61c1b2c007cce5aef
services/authorization/permissions.py                 0016d6e6a9ab25877559a7a0e65ea854fdd3e8ed94d20c1dc18cd10f9aea1cee
services/authorization/service.py                     1d4b00c73e092fc0127fc7916c839c2a76681455fc98dd06cf3eba0475eac74d
services/control_plane/errors.py                      f3029c68e22ba888196288c46133b79b47d8a0fc9fcda055d7142d2170a6e91c
services/control_plane/repository.py                  696f5d063a394f523a8552b7276c0579d56e28275a496b88ee50fb0c92f06413
services/identity_runtime/__init__.py                 44cfbb792d0e85f01249086313c05bf7af7310e616c571fca8d1745752405958
services/identity_runtime/agent_scope.py              e999ddd1eae7e8240179f24ab3714eac80352551abdfcc6ff247ca64b620c0bf
services/identity_runtime/errors.py                   4ca6ee11756f828db69cb3e0ddddfd37465b7c64bb847b7bf8c77173ec464a50
services/identity_runtime/resolver.py                 dcd2623a7c980b458ffe03e0692a1965395329949a7204f12258602e69ad3bfc
services/use_cases/__init__.py                        5a6faffd7f7fd1e9ee053fe4b5fcc7c2461a3c3f8e2534bbcba7689d21ace901
services/use_cases/control_plane.py                   dfbacde1cf57204e1f9df36ae5be92bbccd1083a26ac5553d78b501450fdc0e2
tests/architecture/test_p17_boundaries.py             f968b02de9ed78e444d465d46528af00547271f62e6d61ca0fec6eb1ed08b80a
tests/architecture/test_p18_control_plane_boundaries.py 00a22fd68d36c6df227c0cdf2b59a2291f26f805ecb12a477c6286fdcfb03d1e
tests/integration/test_p18_control_api_http.py        9863e7f0b64e35d4456c40f1db9920905ddc2acb7852eebb478d284659fc7806
tests/integration/test_p18_control_plane_authorization.py 0b6a91543529d1b925badf27377e75e10226cdfc4717cb30a49454e15943a858
tests/integration/test_p18_control_plane_metadata_and_gate.py 942567042173d58a27dd460c65c8d029258703c3a5b9e30c62a039119ac7f65a
tests/integration/test_p18_control_plane_provisioning.py 2808d2a1575577f0510683a3af326a72b5d29288ad99d35ea9af9268e760381d
tests/unit/test_p17_identity_runtime.py               087bf009bdb728ac9c5858e5f42019fd925999a2c293acc6136d285bc1580e4b
tests/unit/test_p18_pre_resource_authorization.py     60a2dde4f6a2f9b08d9991d3b39cf4ac8b1a3a097f83e560e9c29a9278409295
```

```text
验证方式：clean clone 中 `git cat-file blob <commit>:<path>` → SHA-256，须与本表逐行一致
（manifest 自身不列入自身哈希 · self-hash exclusion）
```

**END OF P18 V0.1.17 RELEASE MANIFEST（P18 payload = 35 paths · 15 modified + 20 added · hash basis = committed blob bytes；2026-10-01）**
