# UAP v0.1.15 P16 Release Final Record

```text
Release              = UAP-V0.1.15-P16-AGENT-RUNTIME
Base                 = 1bc60834415cb4f518cd695c93cd79bec986228e（0.1.14）
Release Commit       = 42a4f61c20fe119af77ab822e24c8028ce653e3d
Release Tree         = 242c82f3a2ac90a53fe3ed2b908baf5c1bdf0528
Tag                  = UAP-V0.1.15-P16-AGENT-RUNTIME（annotated · object cb4ff8cc9e1603938c31480d52e0de9ed5eb75cc）
Tag Target           = 42a4f61c20fe119af77ab822e24c8028ce653e3d
Migration Head       = 0018_p16_agent_runtime（0017 → 0018 连续 · single head）
Version              = 0.1.15（pyproject.toml / config/settings.py / docker-compose.yml）
Payload              = 49 files（43 added · 6 modified · 0 deleted）
```

## Acceptance / Test 结果（release candidate tree 实测）

```text
P16 Acceptance        = PASSED（上一阶段）
R-1 / R-2 / R-3       = CLOSED / CLOSED / CLOSED
P16 Integration       = 6/6（+ R-1 durability 2/2）
P16 Unit/Arch/Security= 33/0
P15 Regression        = 65/0
Architecture Guards   = 37/0
Forbidden Tests       = 0 · OI-G-4 = 0 · 目录级 pytest = 0
Core → Domain         = 0
Production Event      = Allowlist EMPTY · Handlers 0
```

## Security / DB

```text
uap_runtime grants = 56 = 51（P14 baseline）+ 5（202610 分区：events_202610 3 + audit_logs_202610 2）
roles = 6 · default ACL = 0 · unexpected privilege expansion = 0
secret leakage = 0 · authorization bypass = 0
Formal DB uap = 0 表（prestate == poststate · 本轮只读）
Test DB = uap / uap_b1_test / uap_test（uap_p16_test 已删除）
```

## Fresh-clone 等价验证

```text
来源 = tag 对象导出的干净树（非 dirty working tree）
files = 499 · version = 0.1.15 · alembic heads = 0018_p16_agent_runtime
P16（33）· P16 integration + R-1（8）· P15（65）· guards（37）全部 PASS
⇒ committed tree = annotated tag = remote commit = fresh-clone 验证结果（四者一致）
```

## Remote

```text
origin/main          = 42a4f61c20fe119af77ab822e24c8028ce653e3d
remote refs/heads/main = 42a4f61c20fe119af77ab822e24c8028ce653e3d
remote tag object    = cb4ff8cc9e1603938c31480d52e0de9ed5eb75cc（与本地一致）
remote tag peeled    = 42a4f61c20fe119af77ab822e24c8028ce653e3d
push 方式            = fast-forward（1bc6083..42a4f61）· force push = 0
local tags           = 14
```

## 保留的历史事实（未改写）

```text
F-P16-I-06 = characterized environmental drift
  （month-partition manual maintenance：uap_b1_test 补齐 events_202610 / audit_logs_202610 后
    P15 由 11 failed 恢复 65/0；51 → 56 的增量全部来自新分区，不是新权限面）
R-2 = 曾发现 4 个真实缺陷（EchoAdapter NameError · ai_request_logs.id NOT NULL ·
      tool 查询缺少 tenant 谓词 · audit_logs.created_at NOT NULL）并已修复
R-1 = 曾 OPEN，后经 §19 审计注入与 §21 rowcount 两个专项测试关闭
历史 P15 记录（0.1.11 RELEASE-BLOCKED / 0.1.12 / 0.1.13 / 0.1.14）保持不变
```

**END OF UAP v0.1.15 P16 RELEASE FINAL RECORD**
