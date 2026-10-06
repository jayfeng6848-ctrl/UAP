# UAP — P14 RELEASE CANDIDATE REGRESSION MATRIX

> ```text
> 轮次 = P14 RELEASE PREPARATION（显式 allowlist 执行 · 2026-09-28）
> 执行 = 26 个显式文件（无目录级 pytest）· DB target = uap_b1_test（runtime 身份 = uap_runtime）
> 结果 = 282 passed · 1 failed；唯一失败 = D-02（Human OPTION B 已 CLOSED）
> ```

| Area | Required | test source | scope | result | evidence |
|---|---|---|---|---|---|
| Architecture | PASS | tests/architecture 3 文件 | 显式 | PASS 28 | work/p14_release_regression.out |
| Contract | PASS | tests/contract 2 文件 | 显式 | PASS 23 | 同上 |
| Runtime Unit | PASS | tests/unit/test_runtime_* 3 文件 | 显式 · 无 DB | PASS 20 | 同上 |
| Integration | PASS | tests/integration/test_runtime_db_wave1.py | 显式 · uap_runtime | PASS 13 + FAIL 1（D-02） | 同上 |
| Security | PASS | test_runtime_security_regression_wave1.py + test_no_secrets.py | 显式 | PASS 46 | 同上 |
| Acceptance | PASS | tests/unit 6 文件（boot/config/logging/build_info/migration_*） | 显式 | PASS 81 | 同上 |
| Wave 1 regression evidence | PASS with historical D-02 note | Wave 1 组合计 | 210 / 211 | PASS（D-02 已裁决为环境状态产物） | OI MATRIX · PDL 附录 Q |
| Wave 2 | PASS | tests/{unit,integration}/test_wave2_*.py 8 文件 | 显式 | PASS 72 | 同上 |
| Auth | PASS | test_wave2_api_security.py（缺凭据/畸形凭据/无效口令） | 显式 | PASS | 同上 |
| Identity | PASS | test_wave2_identity_security.py | 显式 | PASS 12 | 同上 |
| Credential | PASS | test_wave2_identity_security.py + test_wave2_credentials.py | 显式 | PASS（Argon2id · rotate · 无明文） | 同上 |
| Device | PASS | test_wave2_device_security.py | 显式 | PASS 13 | 同上 |
| Session | PASS | test_wave2_session_security.py | 显式 | PASS 11 | 同上 |
| Context | PASS | test_wave2_authorization_security.py + test_wave2_api_security.py::test_wrong_tenant_is_403 | 显式 | PASS | 同上 |
| Authorization | PASS | test_wave2_authorization_security.py | 显式 | PASS 10 | 同上 |
| API | PASS | test_wave2_api_security.py | 显式 | PASS 6 | 同上 |
| Transaction | PASS | test_wave2_device_security.py::test_device_revoke_revokes_its_sessions_atomically + Wave 1 transaction 用例 | 显式 | PASS | 同上 |
| Fail-Closed | PASS | test_wave2_*_security.py deny 面 + test_wave2_error_mapping.py | 显式 | PASS | 同上 |
| Replay | PASS | test_wave2_device_security.py（challenge 二次使用/过期/指纹绑定） | 显式 | PASS | 同上 |
| Revoke propagation | PASS | test_wave2_session_security.py（device/identity/credential 三类传播） | 显式 | PASS | 同上 |
| Observability | PASS | test_no_secrets.py + test_wave2_api_security.py 脱敏断言 | 显式 | PASS | 同上 |
| Error Mapping | PASS | tests/unit/test_wave2_error_mapping.py + API 503 不泄露用例 | 显式 | PASS | 同上 |
| Dependency reproducibility | PASS | 干净 venv 从 requirements.txt 安装 | 隔离环境 | PASS（20 tests + argon2id 校验） | OI MATRIX ENV-1 |

```text
执行统计
  文件数 = 26（逐文件显式）· test groups = Architecture / Contract / Runtime Unit / Integration /
           Security / Acceptance subset / Wave 2 unit / Wave 2 integration / Wave 2 audit
  结果 = 282 passed · 1 failed · 0 skipped
  唯一失败 = tests/integration/test_runtime_db_wave1.py::test_approved_reads
             （assert 926 == 0；实测 1169 行 append-only EXPECTED TEST DATA）
             ⇒ D-02 = CLOSED（Human OPTION B · PDL 附录 Q）· 不阻断 Release Candidate
  Forbidden tests executed = 0（19 个 CF-C-4 文件 + OI-G-4 文件均未执行）
  未使用目录级 pytest 参数
```

**END OF P14 RELEASE CANDIDATE REGRESSION MATRIX（2026-09-28 · 282 passed · 1 = D-02 CLOSED · HARD STOP ACTIVE）**
