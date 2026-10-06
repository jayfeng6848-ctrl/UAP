# 12_EVIDENCE_MAP — 证据地图（实际路径 · 无虚构）

> 根 = `C:\Users\19217\WorkBuddy\2026-09-07-19-22-34\uap-stage3-evidence\`（仓库外 · 审计面之外）

## batch_a\（BATCH-A 角色/所有权/授权 · Gate 69/69）

| 文件 | 证明什么 | 阶段 |
|---|---|---|
| `A1_create_roles.log` | 三角色创建（NOTICE A1-CREATED uap_migrator 等） | A-1 |
| `A1_post_verify.log` / `A1b_idempotency.log` | 属性核验 / 幂等复跑 NOOP | A-1 |
| `A2_membership.log` | membership 空集 + 禁止关系 | A-2 |
| `A3_transfer.log` / `A3_ledger_pre.tsv` / `A3_ledger_post.tsv` / `A3_who_what_old_new_why.tsv` | 178/178 所有权转移 + 逐对象台账（含 `uap (deployment/ops authority, D-OP101-04)` 身份记录） | A-3 |
| `A4_grants.log` / `A4_runtime_grant_boundary.sql` | uap_app 恰 5 项授权 | A-4 |
| `A5_*.log` / `A5_readonly_verification.sql` | 会话探针 15/15（SET ROLE 拒等） | A-5 |
| `GATE_batch_a.log` / `MANIFEST.txt` | Gate 69/69 · 工件清单 | BATCH-A |

## batch_b\（BATCH-B 配置分离 · FINAL PASS）

| 文件 | 证明什么 | 阶段 |
|---|---|---|
| `B1B2_probes.log` | B-1/B-2 CLI 探针（※ P1 为 at-head no-op，掩盖了后发现的 P0 缺陷） | B-1/2 |
| `B1_role_assertion.log` | 角色断言行为 | B-1 |
| `B3_settings_diff.txt` / `B3_test_config.log` | settings.py 纯注释变更 / 最小配置测试 | B-3 |
| `B4_gate.log` | 双 DSN testkit 23/23 | B-4 |
| `B5_gate.log` | 文档 4 载体 39/39 | B-5 |
| `B6_final_gate.log` | 独立安全核验 67/67 | B-6 |

## 根目录（OPEN-P10-1 序列 Gate 日志 · 关键项）

| 文件 | 证明什么 |
|---|---|
| `open_p10_1_prep_gate.log`（6437B） | PREP Gate 94/94 |
| `open_p10_1_decision_record_gate.log` / `decision_freeze_gate.log` / `freeze_*_gate.log` | 决策冻结（D-OP101-01…14 附录 L） |
| `open_p10_1_revision_resolution_gate.log` | RV-A 裁定（0016_open_p10_1_trust_boundary）Gate 8/8+73/73 |
| `open_p10_1_batch_a_authz_request_gate.log` | BATCH-A 授权请求 Gate 70/70 |
| `open_p10_1_batch_b_authz_request_gate.log` / `..._decision_review_gate.log` / `..._decision_submission_gate.log` | BATCH-B 授权/复审/提交 Gate 73/70/87 |
| `batch_c_authz_request_gate.log` | BATCH-C PREP Gate 86/86 |
| `batch_c_decision_review_gate.log` + `_round2/_round3` | 三轮 NOT SUBMITTED 判定 40/40 |
| `batch_c_decision_register_gate.log` | 决策登记 39/39 |
| `batch_c_implementation_preflight_gate.log` | PRE-FLIGHT P01…P20 = 23/23 |
| `batch_c_0016_implementation.log` | **0016 执行全程 + BLOCKER 插桩证据（根因实锤）** |
| `cc7_c2_functiondef_preflight.sql` | C2 pre-image 全文（md5 68678741…） |
| `c2_preauthorization_functiondef.sql` | C2 授权前固化（同 md5） |
| `p10_*` / `p11_*` / `p12_*` / `p13_*` 系列 | P10–P13 各轮 Gate/验收/回归日志 |

## 仓库内（docs/architecture/ · 新增面）

```text
OPEN_P10_1_BATCH_C_EXECUTION_AUTHORIZATION_REQUEST.md   授权请求（§1…§6）
OPEN_P10_1_BATCH_C_HUMAN_DECISION_BLOCK.md              决策块（§3 空白快照 · §6 输入登记 · END ×2）
OPEN_P10_1_BATCH_C_DECISION_RECORD.md                   决策记录（sha256[:16] 9efbc3fe031387d0）
OPEN_P10_1_BATCH_C_DECISION_REVIEW_REPORT.md            三轮 BLOCKED 判定
OPEN_P10_1_BATCH_C_IMPLEMENTATION_PRE_FLIGHT_REPORT.md  PRE-FLIGHT PASS（契约冻结）
OPEN_P10_1_BATCH_C_0016_IMPLEMENTATION_BLOCKER_REPORT.md BLOCKER 报告
OPEN_P10_1_IMPLEMENTATION_CONTRACT.md                   契约（sha256[:16] 2c1fec371de5ab3b）
PLATFORM_DECISION_LOG.md                                决策权威（sha256[:16] a83fde5c57605252）
migrations/versions/0016_open_p10_1_trust_boundary.py   0016 工件（sha256[:16] 10284d98de6be342）
handoff/ 本交接包
```

## 诊断脚本（%TEMP% · 临时 · 仓库外）

`uap_gate_batchc_decision_review.py` / `uap_gate_batchc_register.py` / `uap_gate_batchc_preflight.py` / `uap_diag_*.py`（插桩定位脚本）/ `uap_snapshot_20260927_batchc_decision_submission.json`（轮次快照 98 条目）
