# P15 BATCH 4 — TEST EXECUTION REPORT

日期：2026-09-28
执行环境：

```text
python      = C:\Users\19217\.workbuddy\binaries\python\envs\uap\Scripts\python.exe（Python 3.13.14）
pytest      = 8.3.4 · pluggy 1.6.0 · anyio 4.15.1
rootdir     = C:\Users\19217\WorkBuddy\2026-09-07-19-22-34\uap
configfile  = pyproject.toml
test DSN    = $env:UAP_RUNTIME_TEST_DSN = postgresql+psycopg://uap_runtime:uap_runtime@localhost:5432/uap_b1_test
extra args  = -p no:cacheprovider
执行方式     = 逐文件显式 allowlist（无目录级 discovery）
```

---

## 1. 逐组结果

| 组 | 文件 | 结果 |
|---|---|---|
| P15-KERNEL | `tests/unit/test_p15_consumer_kernel.py` | **13 passed** |
| P15-CLAIM | `tests/integration/test_p15_claim.py` | **13 passed** |
| P15-WORKER | `tests/unit/test_p15_worker.py` | **30 passed** |
| P15-ENTRY | `tests/unit/test_p15_worker_entry.py` | **9 passed** |
| P14 Wave 1 | 17 文件（见 manifest §5） | **210 passed + 1 failed** |
| Wave 2 | 9 文件（见 manifest §6） | **72 passed** |

```text
P15 合计   = 65 passed · 0 failed
回归合计   = 282 passed + 1 failed（Wave 1 D-02 历史记录）
总执行     = 347 passed · 1 failed · 0 skipped · 0 error
```

---

## 2. Wave 1 唯一失败项（历史事实 · 保持原样）

```text
file    = tests/integration/test_runtime_db_wave1.py
test    = test_approved_reads
assert  = assert audit == 0
actual  = 1412
```

```text
判定 = D-02 CLOSED 的历史记录（Wave 1 = 210/211）
处置 = 未修改该断言 · 未修改该文件（sha256 = 51a453f5c1858873525753b556438c4d42240fb393e5b4b770d058a3b0b25c46，与 P14 frozen 值一致）
      审计不变量由 tests/integration/test_wave2_audit_invariant.py 的 delta 语义覆盖
禁止 = 改写为 211/211 · 弱化断言 · 调整 audit_logs
```

---

## 3. O-2 canonical check（§16 / §24）

```text
实测序列 = [5, 10, 20, 40, 80, 160, 320, 600, 600]
canonical = min(5 * 2^(attempt - 1), 600)
cap       = 600
contains 640 = False
attempt 8 / 9 = 600 / 600（Human 澄清后的正确值；"+640s" 版本不适用）
```

---

## 4. 数据库动作

```text
P15 单元测试（kernel / worker / worker_entry）      0 DB 连接（全部依赖注入）
P15 集成测试（test_p15_claim.py）                   仅 uap_b1_test · identity = uap_runtime · 自清理净零
P14 Wave 1 / Wave 2 回归                            仅 uap_b1_test
正式库 uap                                          read-only · prestate == poststate

未执行：DROP DATABASE / DROP SCHEMA / reset_test_database() / GRANT / REVOKE /
        ROLE mutation / alembic upgrade|downgrade / DELETE audit_logs / TRUNCATE
```

---

## 5. 审计表状态（append-only · 不归零）

```text
            before   after    delta
audit_logs   1412  →  1655     +243      （EXPECTED TEST DATA）

说明：audit_logs 为 append-only（tg_audit_immutable，连超级用户亦拒 DELETE）。
本 Batch 未对 audit_logs 执行任何 DML；增长来自 Wave 1/Wave 2 已接受的测试路径。
禁止：DELETE / TRUNCATE / reset。
```

---

## 6. 测试数据净零

```text
events            = 0（执行前后一致）
users             = 0（执行前后一致）
agents family     = 0（执行前后一致）
acl_subject_types = 3 · permissions = 12 · role_permissions = 12（执行前后一致）
```

---

## 7. 数据库边界锚点（执行前 / 执行后）

```text
test db  uap_b1_test prestate == poststate : False —— 唯一差异 = audit_logs +243（预期）
formal db uap        prestate == poststate : True

alembic_version  0017_p13_seed（前后一致）
0018+            0（前后一致）
grants           51 / 6 / 5 / 0 / 245（前后一致）
default_acl      0（前后一致）
C2 md5           185e95be8bc4304edbcd3f4d5cda1eff（前后一致）
P13 seed         3 / 12 / 12（前后一致）
pg_class / pg_proc / pg_trigger  156 / 22 / 272（前后一致）
user memberships 0 · ownership residual 0 · public schema CREATE false（全部非超级用户）
D-01 persistence.py sha256 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6（不变）
```

---

## 8. 未执行的测试（CF-C-4 / OI-G-4）

```text
CF-C-4 19 文件 executed = 0
tests/unit/test_generate_build_info.py（OI-G-4）executed = 0
目录级 pytest / --collect-only = 0
```

