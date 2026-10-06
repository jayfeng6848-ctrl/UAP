# P20 COMPANY SCHEMA TEST MATRIX

```text
性质 = P20 SCHEMA PREP 附件（测试矩阵提案 · 未执行 · 未冻结）
```

## 1. 平台回归基线（必须保持）

```text
P18 = 33/0 · P17 = 97/0 · P16 = 24/0 + 8/0 · P15 = 65/0 · architecture guards = 63/0
Core → Domain = 0 · forbidden tests = 0 · OI-G-4 = 0 · 正式库 uap 不得被测试触碰
```

## 2. 若采纳业务表（未来实现轮）必须覆盖

```text
Schema / constraint
  T1 迁移可重现（fresh DB → head）· 正式库不受影响 · 迁移不改 P13–P18 既有对象
  T2 UNIQUE(tenant_id, employee_no) 生效 · 重复工号被拒
  T3 UNIQUE(tenant_id, user_id) WHERE user_id IS NOT NULL 生效
  T4 UNIQUE(employee_id, space_id) WHERE ended_at IS NULL 生效（同一部门唯一有效分配）
  T5 CHECK：(terminated ⇔ terminated_at) · (ended ⇔ ended_at) 生效
  T6 FK 行为：tenant RESTRICT · users RESTRICT · spaces RESTRICT · employee CASCADE
租户/空间隔离
  T7 跨租户读取/写入 = DENY（应用层 + DB 双重证据）
  T8 assignment 的 space 必须属同一 tenant（GAP-P20S-3 的裁定方式对应验证）
授权
  T9 未授权 actor ⇒ DENY 且零写入（canonical 授权路径）
  T10 非 ACTIVE tenant/space ⇒ 业务操作 DENY（对齐 P18-D14）
  T11 员工身份本身不授予权限（owner/creator ↔ 无继承授权）
审计
  T12 员工/分配变更写 audit（actor = 真实用户 · correlation 复用）
  T13 audit 内容安全（无 secret/token/SQL/stack）
领域边界
  T14 `domains/company/` 不被 core 导入（Core → Domain = 0 守卫扩展）
  T15 不新增第二套 users/tenants/spaces/roles/membership/authorization
事件
  T16 本轮不激活事件；若未来激活 ⇒ 单独矩阵（P19-D02…D18）
```

## 3. 治理

```text
显式 allowlist（禁目录级 pytest）· 0 skipped/xfail/deselect · 一次性隔离测试库 · 净零清理
```

**END OF P20 COMPANY SCHEMA TEST MATRIX（提案 · 未执行；2026-10-01）**
