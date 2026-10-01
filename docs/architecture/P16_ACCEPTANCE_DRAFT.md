# P16 ACCEPTANCE DRAFT

## 0. 性质

```text
DRAFT ONLY（proposed acceptance criteria · NOT ACCEPTED · NOT FROZEN）
任何条目在 Human Decision 之前不构成验收依据。
```

---

## 1. 候选验收判据（按面）

### A. Architecture

```text
A-1 Core → Domain = 0 保持（由既有守卫测试验证）
A-2 core/ 不依赖 services / infrastructure / domains
A-3 agent/intelligence 契约层不被 core 反向依赖
A-4 禁止 vendor SDK 直接 import（FORBIDDEN_DIRECT_IMPORTS 守卫扩展）
A-5 运行时只经 RuntimeDatabase 边界访问 DB（无旁路 SQL）
A-6 依赖图与 P16_DEPENDENCY_IMPACT.md 提案一致
```

### B. Security

```text
B-1 Actor provenance 全程保留（不得伪造 system/service actor）
B-2 授权在 tool 之前完成（ToolGate 前置）；无授权即无执行
B-3 无授权缓存 · DENY>ALLOW · fail-closed（异常 ⇒ DENY）
B-4 凭据不进入 DB / log / audit / event / prompt / response（含异常路径）
B-5 runtime principal 与 DSN 一致（principal 断言生效）
B-6 禁止借用 uap_migrator / uap_bootstrap / platform_admin
B-7 tenant/space 隔离；NULL tenant 语义 = platform-scoped（不得重解释）
B-8 三审计分离（授权审计 ≠ 工具执行审计 ≠ agent run 审计）
```

### C. Data

```text
C-1 既有表优先复用；新增表必须由 Human Decision 授权
C-2 迁移链保持单一 head（0017_p13_seed + 经批准的 0018+）
C-3 不修改 0013–0017 历史迁移
C-4 新增 grant 必须最小化且可复现（记录 grant 清单差异）
C-5 正式库 uap 保持 prestate == poststate
```

### D. Event / Consumer

```text
D-1 若激活 event：event_type 受 ck_events_event_type 约束（namespace.aggregate.action）
D-2 幂等可证明（event_id 主身份；不新增 dedup 表）
D-3 handler 失败按 P15 冻结模型重试（attempts/backoff 5→600s · MAX_ATTEMPTS 10）
D-4 生产 allowlist 由 EMPTY 变为显式白名单（不可使用通配）
D-5 未授权事件类型不得被消费（保持 CLOSED allowlist 语义）
```

### E. Tests

```text
E-1 逐文件显式 allowlist 执行（禁止目录级 pytest / collect-only sweep）
E-2 P14/P15 frozen 测试不被修改（D-02 保持历史失败事实）
E-3 CF-C-4 denylist 保持 executed = 0
E-4 新增 unit/architecture 守卫随实现同 commit 落地
E-5 若涉及 DB：integration 测试使用专用测试库与 runtime 身份
E-6 clean clone 可复现（无 worktree-only 依赖）
```

### F. Release

```text
F-1 payload 哈希基准 = committed Git blob bytes（F-RP-06 冻结规则）
F-2 manifest = commit = clean clone（双向完整性）
F-3 版本元数据内部一致（pyproject / settings / compose）
F-4 全链证据（tests · DB state · security anchors · manifest）
```

## 2. P16 Test Surface Map（只读实测）

| 类别 | 文件 | 现状 | P16 关系 |
|---|---|---|---|
| P13 seed 相关 | `tests/integration/test_authorization_service.py` 等（DENY 面） | frozen historical | 不得修改 |
| P14 runtime | `tests/integration/test_runtime_db_wave1.py` · `test_runtime_security_regression_wave1.py` · `tests/unit/test_runtime_*` · `tests/integration/runtime_testkit.py` | Wave 1 allowlist（17） | 可复用；D-02 历史失败保持 |
| P15 consumer | `tests/unit/test_p15_consumer_kernel.py` · `test_p15_worker.py` · `test_p15_worker_entry.py` · `tests/integration/test_p15_claim.py` | P15 allowlist（4） | 可复用；不得修改 |
| Agent/Tool schema | `tests/integration/test_agent_tool_permission_schema.py` · `test_tool_registry_schema.py` · `test_ai_gateway_schema.py` | **DENY 面（executed = 0）** | 需在 P16 授权后决定是否解禁 |
| Architecture guards | `tests/architecture/test_dependency_rules.py` · `test_p10_event_audit_boundary.py` · `test_event_contract_alignment.py` · `test_agent_resource_scope_opaque.py` | Wave 1 / 新增 | 可扩展（新增 P16 守卫） |
| Security | `tests/security/test_no_secrets.py` · `test_authorization_security.py`(DENY) | 混合 | no_secrets 可复用（扫描新代码） |
| Test DB 依赖 | 全部 integration + `runtime_testkit` | 需 `UAP_RUNTIME_TEST_DSN` | P16 集成测试将依赖测试库与 grant |
| 禁止执行 | `tests/unit/test_generate_build_info.py` | OI-G-4 | 保持 executed = 0 |

```text
新增测试建议类别（提案）
  · architecture: runtime 依赖方向 / 禁止 SDK / principal 断言
  · security: 凭据不得进入 log/audit/event（静态 + 行为）
  · unit: routing 决策表 · 授权绑定解析 · 幂等判定
  · integration（若涉 DB）: run → tool_executions → audit（逐文件 allowlist）
```

## 3. 证据要求（提案）

```text
· 每个验收项必须可复现：命令 + 输出 + 时间 + 环境（含 DB 身份）
· 安全项必须给出负路径证据（拒绝 / 失败 / 未泄漏）
· 事件项必须给出幂等证明（重复投递不产生二次副作用）
· 哈希 / manifest 必须取自 committed artifact
· 不得使用“看起来正确”的表述替代测量
```

**END OF P16 ACCEPTANCE DRAFT（DRAFT ONLY）**
