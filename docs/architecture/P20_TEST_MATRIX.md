# P20 TEST MATRIX

```text
性质 = P20 PREP 附件（测试矩阵提案 · 未执行 · 未冻结）
```

## 1. 平台回归基线（必须保持）

```text
P18 = 33/0 · P17 = 97/0 · P16 = 24/0 + 8/0 · P15 = 65/0 · architecture guards = 63/0
Core → Domain = 0 · forbidden tests = 0 · OI-G-4 = 0 · 正式库 uap 不得被测试触碰
```

## 2. 首模块实现时（未来轮次）必须新增的测试（提案）

```text
范围/边界
  T1 模块不新增 users/tenants/spaces/roles/membership/authorization 第二套实现（架构守卫）
  T2 所有业务读写在 tenant/space 上下文内（跨租户 = DENY）
  T3 未授权 actor ⇒ DENY 且零写入（canonical 授权路径）
数据
  T4 业务表若新增：迁移可重现（fresh DB → head）· 正式库不受影响
授权
  T5 业务操作映射到既有 permission/resource 语义（若需新 resource_type ⇒ 独立决策）
  T6 非 ACTIVE tenant/space 时业务操作 = DENY（对齐 P18-D14）
事件（仅当激活时）
  T7 与 P20_EVENT_CANDIDATE_MATRIX 的 D02–D18 逐项对应
  T8 producer 真实代码路径 · handler 四项资格 · 幂等证明 · payload 安全
  T9 复用 P15 kernel（retry/lease/终态）· 不新建投递机制
审计
  T10 业务敏感变更写 audit（actor = 真实主体）· append-only
```

## 3. 治理

```text
显式 allowlist（禁目录级 pytest）· 0 skipped/xfail/deselect · 一次性隔离测试库
```

**END OF P20 TEST MATRIX（提案 · 未执行；2026-10-01）**
