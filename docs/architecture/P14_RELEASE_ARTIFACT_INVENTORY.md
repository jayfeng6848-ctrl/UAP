# UAP — P14 RELEASE ARTIFACT INVENTORY

> ```text
> 轮次 = P14 RELEASE PREPARATION（只读清点 · 2026-09-28）
> 字段 = path / type / owner phase / frozen? / release candidate? / sha256[:32] / notes
> ```

## 1. Decision / Contract / Scope（冻结引用）

```text
c283f954b29b5574c8654c5e0e863ac3  docs/architecture/PLATFORM_DECISION_LOG.md
    type = decision log · owner = Governance · frozen = 既有 D-* 与附录 A–M 冻结（O/P/Q append-only）
    RC = 是 · notes = 附录 A…Q 齐备；O/P/Q 既有正文未改写
00c3355cbcfea52bfc22b4a4d2e3c029  P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md   （contract · P14 · frozen = 是）
81323a41e1484441822b8a75deb0bc84  P14_RUNTIME_SLICE_SCOPE.md                    （scope · P14 · frozen = 是）
86716f11a8ce9ffad88d205f3e89a5f8  P14_RUNTIME_SLICE_DEPENDENCY_MAP.md           （dependency map · P14 · 是）
d8a85d0cd0fd4a312c18dfa6a1b7bb05  P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md        （acceptance matrix · P14 · 是）
```

## 2. Security artifacts（冻结引用 · 本轮零修改）

```text
3ed7ec339fbeea9784e007e522c97f16  P14_RUNTIME_PRIVILEGE_MATRIX.md                （privilege matrix · P14）
ebc535886389263c5fce201e010b0d5b  P14_PRIVILEGE_SECURITY_DECISION_LOCK.md       （decision lock · P14）
f09f786664990f2f24c2e9d45dc96327  P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md   （grant matrix · frozen = 是）
30389e9ebfd0b5157f43326883e45e62  P14_SECURITY_IMPLEMENTATION_CLOSURE_REPORT.md （closure report）
e7fa547981f2775256d7964775b5b6b6  P14_RUNTIME_CONNECTION_SECURITY_NOTE.md       （connection security note）
ea265acb03afc6aafaa6d272e8deaa98  P14_SECURITY_IMPLEMENTATION_DEPENDENCY_LOCK.md（security dependency lock）
2c879184ce8e140078f738020f58f668  P14_SECURITY_ACCEPTANCE_REPORT.md             （security acceptance）
```

## 3. Acceptance / Evidence

```text
82df49a200b7303104abcee538fe8f01  P14_RUNTIME_IMPLEMENTATION_WAVE1_FINAL_ACCEPTANCE_REPORT.md（Wave 1 ACCEPTED · frozen = 是）
a216220c97a45ed3e3d519e7235774af  P14_RUNTIME_IMPLEMENTATION_WAVE2_REPORT.md     （Wave 2 IMPLEMENTED + VERIFIED）
c66c28091cc13824bc7dcc3af997fc85  P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md（§1–§21 收敛 · 无 MAYBE/TBD/UNKNOWN）
b6868a55904eee3e0c53c4bfd48852e2  P14_OVERALL_FINAL_ACCEPTANCE_REPORT.md         （P14 OVERALL = PASS / ACCEPTED）
b7f8b1875c16b91c2be1db15fd55f654  P14_OVERALL_OI_CLOSURE_MATRIX.md               （blocking item = 0）
10d7881190ed61967bb11ba45c1e31a7  P14_RUNTIME_WAVE1_TEST_EXECUTION_MANIFEST.md   （frozen = 是）
52b72cda587a7f3c4cd26ac72ae9ba99  P14_RUNTIME_WAVE2_TEST_EXECUTION_MANIFEST.md   （含 EXPECTED TEST DATA 声明）
51a453f5c1858873525753b556438c4d  tests/integration/test_runtime_db_wave1.py      （冻结 · 含原始 assert audit == 0 · D-02）
c7ae8718bed22cc14303aa578ac14e19  tests/integration/test_wave2_audit_invariant.py （4 项 delta 不变量）
```

## 4. Implementation

```text
69d2c14064d19d5355cf867665476c34  infrastructure/database/persistence.py（Wave 1 · 冻结 · 与 D-01 引用 sha 一致）
（见 Git baseline §2.1 的 A 类 30 条）infrastructure/runtime/** · infrastructure/database/{principal,runtime}.py
（同上）services/{mapping,identity,device,session,context,audit,use_cases}/** · services/reads.py
（同上）apps/api/main.py · apps/api/{dependencies,error_mapping}.py · apps/api/routes/{identity,devices,sessions}.py
（同上）tests/integration/{wave2_testkit,test_wave2_*}.py · tests/unit/test_wave2_*.py
```

## 5. Dependency manifests / Migration（只读引用）

```text
3d8b69d6ef713706efa7c2be904d4f89  pyproject.toml          （含 argon2-cffi==25.1.0 · ENV-1）
22ceb66d257917f1f6e6d2f9e98b9886  requirements.txt        （含 argon2-cffi==25.1.0 · ENV-1）
577f0d0e018b5859696e61b4f405ab2b  migrations_alembic/env.py（冻结 · 未修改）
1251f0b10f79719379d452798baddfee  migrations_alembic/versions/0017_p13_seed.py（冻结 · 0018+ = 0）
10284d98de6be342d485f09b7a23d4ef  migrations_alembic/versions/0016_open_p10_1_trust_boundary.py（冻结）
```

## 6. Release-prep documents（本轮新增）

```text
P14_RELEASE_PREPARATION_GIT_BASELINE.md
P14_RELEASE_SCOPE_LOCK.md
P14_RELEASE_ARTIFACT_INVENTORY.md（本文件）
P14_RELEASE_CANDIDATE_REGRESSION_MATRIX.md
P14_RELEASE_CANDIDATE_MANIFEST.md
（hash 记录于 manifest §7 · 因同为 release-prep 输出，冻结时一并固化）
```

## 7. 清点结论

```text
P14 文档总数 = 63（docs/architecture/P14_*.md）
覆盖类别 = decision · contract · scope · dependency map · acceptance matrix · privilege matrix ·
          security decision lock · grant matrix · security closure · connection note ·
          security dependency lock · acceptance mapping · wave1/wave2 acceptance ·
          overall acceptance · OI matrix · test manifests · dependency manifests · release-prep
未发现缺件 · 未发现无归属 artifact
```

**END OF P14 RELEASE ARTIFACT INVENTORY（2026-09-28 · 全部类别覆盖 · 无缺件 · HARD STOP ACTIVE）**
