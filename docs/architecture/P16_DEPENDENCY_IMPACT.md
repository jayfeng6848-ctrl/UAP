# P16 DEPENDENCY IMPACT

## 0. 性质

```text
ANALYSIS ONLY（NOT FROZEN）
范围 = 依赖方向 · DB/migration 影响 · API 影响 · 测试影响 · clean-clone 风险 · 既有 finding 影响
```

---

## 1. 依赖方向（提案）

```text
建议落位（PROPOSAL）
  core/event · core/audit · core/permission      = 既有契约（不动）
  core/agent（或 agent/）                        = Run / ToolProposal / 错误契约（纯数据 + Protocol）
  services/agent（新）                           = Run 编排 · 授权绑定 · tool 调度
  services/ai（或 intelligence/gateway 实现）     = routing · request log 写入
  intelligence/providers（实现）                  = adapter（不得被 core/ 引用）
  infrastructure/                                = HTTP 客户端 · secret 解析 · DB 边界

必须保持
  Core → Domain = 0
  core ↛ services · core ↛ infrastructure
  agent ↛ services（执行必须经 Authorization 与 Tool）
  runtime ↛ 直接 DB（必须经 RuntimeDatabase + principal 断言）
  vendor SDK 不得出现在 core/ · intelligence/ 默认契约层（既有守卫）
```

```text
风险：P16 天然诱发 core → infrastructure（HTTP 客户端）与 core → services（tool 调用）。
⇒ 实现必须把这些放在 services/ 或 infrastructure/，不得进入 core/。
```

## 2. DB / Migration 影响

```text
当前 = 0017_p13_seed（single head）· 0018+ = 0

候选 schema 变更（全部需要 Human Decision · 本阶段不创建）
  · agent_runs / agent_run_steps（未入库契约中的 DESIGN ONLY 对象）
  · 若 D10 允许平台级 agent ⇒ agents.tenant_id NOT NULL 约束变更
  · 若需要 run 索引 / 分区维护 ⇒ 新索引或运维流程

候选 grant 变更（必须独立 Gate）
  uap_runtime 需新增（实测当前为零）：
    ai_providers(SELECT) · ai_models(SELECT) · ai_routes(SELECT) · ai_policies(SELECT) ·
    ai_request_logs(INSERT) · tool_versions(SELECT) · tool_permissions(SELECT) ·
    tool_executions(INSERT,UPDATE)
  ⇒ 或改为新增专用 principal（P16-D11）

禁止：本阶段创建 migration / 修改 0013–0017 / 变更既有 grant
```

## 3. API 影响

```text
现有 API（实测）= health · meta · identity · devices · sessions（5 组路由 · 无 AI/Agent 端点）

候选（PROPOSAL）
  minimum required : 1 个 agent run 触发端点（若 D13 = A）
  optional         : run 状态查询 / 结果读取
  not needed       : tool 直接调用端点（tool 只能由 runtime 内部调用）

历史边界：handler code no SQL（API 层不得直连数据库）⇒ 保持成立，须由 architecture 守卫验证
```

## 4. 测试影响

```text
可复用：P14 Wave1（17）· P15（4）· Wave2（9）· architecture guards
需扩展：dependency guards（新增 runtime/SDK 规则）· security（凭据不泄漏）
需新增：routing 决策 · 授权绑定 · 幂等（unit）；run→tool_executions→audit（integration · 需授权）
不得触碰：P14/P15 frozen 测试 · D-02 历史失败 · CF-C-4 denylist · OI-G-4 禁跑文件
新增测试若进入禁止集 = 需要 Human Decision 才能解禁
test DB 依赖：integration 需 uap_b1_test + UAP_RUNTIME_TEST_DSN（现状可满足）
```

## 5. Clean-Clone 风险扫描（只登记，不修复）

| 风险类 | 实测 | 影响 | 处置建议 |
|---|---|---|---|
| worktree-only modules | 无（Wave1/P15/Wave2 闭包 = clean） | — | 保持 |
| untracked runtime dependencies | 0 | — | 保持 |
| 设计权威未入库 | AGENT_RUNTIME_*（4 份）untracked（F-P16-03） | P16 契约层不在发布物内 | 独立 governance 决定是否入库 |
| 缺失 test helper | 0（0.1.12 已修 F-RP-04） | — | 保持 |
| 文档被测试引用 | `test_p10_event_audit_boundary` 读 `DEPENDENCY_RULES.md`（已 committed） | 已闭合 | 保持 |
| config 缺失 | 无（alembic.ini · .env.example 均在库） | — | 保持 |
| generated files | `config/_build_info.py`（构建期生成 · 测试用 monkeypatch 模拟） | 非必需 | 保持 |
| 行尾敏感 manifest | 17 个 tracked 文件在 Windows 工作区为 CRLF（F-P16-11） | 哈希基准风险（已由 F-RP-06 规则覆盖） | 一律用 committed blob 计算哈希 |

```text
结论：clean-clone 层面当前无 P16 阻塞项；唯一结构性风险是“设计权威未入库”（F-P16-03）
```

## 6. F-RP-02 Remaining 影响评估（不修复）

| 文件 | 工作区 delta | 是否被现有 allowlist 依赖 | P16 影响分类 |
|---|---|---|---|
| `tests/conftest.py` | +38（dual-DSN 说明 + `migration_dsn` / `runtime_dsn` fixtures） | 否（无测试请求该 fixture） | **P16 dependency candidate**（若 P16 integration 需要 dual-DSN 夹具） |
| `infrastructure/database/__init__.py` | +8（导出 RuntimeDatabase / Repository / principal helpers） | 否（唯一包级 import 是 health） | **P16 irrelevant**（当前不需要；如 P16 采用包级导入则成为 dependency） |

```text
结论：F-RP-02 remaining = 当前不与 P16 冲突；不得因 P16 顺手修复；
      若 P16 决定使用 dual-DSN 夹具或包级导出，需在 P16 授权范围内显式引用（或独立授权纳入）
```

## 7. 既有 Deferred Findings 影响

```text
D-01（persistence.py 缺陷 · DEFERRED / NON-BLOCKING）
  现状 = 未触碰 · P16 活跃路径应继续使用 SafeReader / RuntimeDatabase（不得依赖 D-01）
  若 P16 认为必须修 D-01 ⇒ 独立 foundation decision（不得绕过）

OI-G-4 / BATCH-D（generate_build_info 硬编码 revision）
  现状 = registered / unfixed · 禁跑测试保持 executed = 0
  P16 不得顺手修复；若 P16 需要 build_info 参与验收 ⇒ 独立决定

F-RP-06（manifest hash basis）= CLOSED · P16 必须沿用 canonical 基准
P13 / P14 / P15 冻结语义 = 全部继承，不得修改
```

## 8. 依赖影响总结

```text
阻塞 P16 实施的三项 = 运行时 principal/grant（D11/D12）· tool 执行边界（D06）· 凭据边界（D07）
可并行推进的 = 契约落地（core/agent）· routing 设计（D04）· 授权绑定解析（D06 前半）· 测试矩阵设计（D14）
明确不进 P16 = C-7 · C-2 · C-4 · C-8 · D-01 repair · marketplace / multi-agent / memory / RAG /
              workflow engine / billing / admin UI / streaming / 具体 worker 框架
```

**END OF P16 DEPENDENCY IMPACT（ANALYSIS ONLY）**
