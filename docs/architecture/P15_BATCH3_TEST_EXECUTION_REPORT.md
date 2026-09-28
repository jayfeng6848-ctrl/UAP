# P15 BATCH 3 — TEST EXECUTION REPORT

日期：2026-09-28
执行环境：

```text
python      = C:\Users\19217\.workbuddy\binaries\python\envs\uap\Scripts\python.exe（Python 3.13.14）
pytest      = 8.3.4
rootdir     = C:\Users\19217\WorkBuddy\2026-09-07-19-22-34\uap
configfile  = pyproject.toml
test DSN    = $env:UAP_RUNTIME_TEST_DSN = postgresql+psycopg://uap_runtime:uap_runtime@localhost:5432/uap_b1_test
extra args  = -p no:cacheprovider（避免在仓库写入 .pytest_cache）
```

---

## 1. 显式执行的测试文件

| 组 | 文件 | 说明 |
|---|---|---|
| Batch 1 regression | `tests/unit/test_p15_consumer_kernel.py` | 纯逻辑 kernel（无 I/O） |
| Batch 2 regression | `tests/integration/test_p15_claim.py` | 真库 claim / lease / heartbeat / recovery |
| Batch 3 tests | `tests/unit/test_p15_worker.py` | worker lifecycle / concurrency / shutdown（离线） |

执行方式：**逐文件显式 allowlist**。未使用 `pytest`、`pytest tests/`、
`pytest tests/unit/`、`pytest tests/integration/` 等目录级 discovery。

---

## 2. 结果

```text
tests/unit/test_p15_consumer_kernel.py   13 passed in 0.05s
tests/integration/test_p15_claim.py      13 passed in 1.38s
tests/unit/test_p15_worker.py            30 passed in 1.44s
                                         --------------------
合计                                      56 passed · 0 failed · 0 skipped · 0 error
```

（另有一次三文件合并执行的等价运行：`56 passed in 2.94s`。）

---

## 3. Batch 3 测试分组（30 项）

```text
config           3  默认值符合 O-4/O-2 · 15 类非法取值 fail closed · 默认值合法
state machine    4  CREATED→STARTING→RUNNING→DRAINING→STOPPED · 非法迁移拒绝 · from CREATED stop
startup          2  fail-closed（probe 抛错）· 必须取得 runtime DB 依赖
poll             4  空队列 claim 0 · claim 受 batch 与容量约束 · poll 失败 backoff · recovery 间隔
execution        9  delivered · unsupported→dead · handler 未绑定→dead · retryable→retry ·
                    non-retryable→dead · ownership loss 前不执行副作用 · heartbeat DB failure ·
                    执行期周期性续租 · 监控发现所有权丢失则不写 delivered · finalize 失败不宣称成功
concurrency      1  peak active <= 4（counter + lock 证明，非仅靠 sleep）
shutdown         4  空队列停机 · 有界 drain 完成 · 超期 abandoned 且不 delivered · stop 幂等
observability    2  事件词表齐备且无 secret · 生产注册表为空 / 测试注册表显式
```

---

## 4. 数据库动作

```text
tests/unit/test_p15_worker.py            0 DB 连接（全部依赖注入）
tests/unit/test_p15_consumer_kernel.py   0 DB 连接
tests/integration/test_p15_claim.py      仅对 uap_b1_test 读写 events（自清理 ⇒ events 净 0）
正式库 uap                               read-only · prestate == poststate
```

未执行（本次运行中）：

```text
DROP DATABASE / DROP SCHEMA = 0
reset_test_database()      = 0
GRANT / REVOKE             = 0
ROLE mutation              = 0
alembic upgrade/downgrade  = 0
```

---

## 5. 审计表行为

```text
audit_logs = append-only（tg_audit_immutable 亦拒绝超级用户 DELETE）
本 Batch 未对 audit_logs 执行任何 DML，也未要求 audit_logs == 0
（实测 uap_b1_test.audit_logs 行数在执行前后保持一致）
```

---

## 6. 未执行的测试（CF-C-4 / OI-G-4）

```text
CF-C-4 禁跑集合（19 条）executed = 0
tests/unit/test_generate_build_info.py（OI-G-4 · REGISTERED / UNFIXED）executed = 0
禁止理由与清单见 P15_BATCH3_TEST_EXECUTION_MANIFEST.md
```

---

## 7. 数据库锚点（执行前 / 执行后一致）

```text
alembic_version        0017_p13_seed（前后一致）
0018+                  0（前后一致）
grant fingerprint      51 / 6 / 5 / 0 / 245（前后一致）
default_acl            0（前后一致）
C2 md5                 185e95be8bc4304edbcd3f4d5cda1eff（前后一致）
P13 seed               3 / 12 / 12（前后一致）
pg_class / pg_proc / pg_trigger   156 / 22 / 272（前后一致）
uap_b1_test prestate == poststate  = True
uap（正式库）prestate == poststate = True
```

