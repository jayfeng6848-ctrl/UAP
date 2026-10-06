# 03_COMPLETED_MILESTONES — 已完成里程碑（按时间序）

> 数值为各阶段验收报告/指令中的冻结记录；标签均为 annotated unsigned tag（无 GPG 环境恒 `no signature found`，非缺陷）。

## 里程碑链

```text
72ade9f  UAP-V0.1.0-INIT(-DB-VALIDATED)      初始化 + DB 验证
e9766fb  UAP-V0.1.4-B1-4-RESOURCE-ACL         B1-4 资源 ACL（0007；C2 首建于此）
d8c6cd2  UAP-V0.1.5-PLATFORM-TIMESTAMP-PRECISION  0009 timestamptz(3)（20 表/72 列）
964ea2c  recover migration baseline            恢复基线（Alembic 化 + testkit）
a64c06b  UAP-V0.1.6-B1-6-AI-GATEWAY            B1-6 AI Gateway（0010）
eb6d4cb  UAP-V0.1.7-GOVERNANCE-GATE            治理基线
71c36c1  UAP-V0.1.7-P09-AGENT-TOOL-PERMISSION  P09（0011）
034ee97  UAP-V0.1.8-AUTHORIZATION              ← HEAD（Stage 2 授权/ACL/Policy）
```

另有未 tag 提交 `e6276a5`（B1-5 tool registry）。

## B1-6 AI Gateway（0010_b1_6_ai_gateway · tag UAP-V0.1.6-B1-6-AI-GATEWAY · commit a64c06b）

验收要点：**73 columns · 8 FK · 2 UQ · 8 CK · 5 indexes · 4 triggers** · partitioning · timestamptz(3) · downgrade zero residue · canonical tests **38/38**。

## P09（0011_p09_agent_tool_permission · tag UAP-V0.1.7-P09-…）

4 表（agents / agent_versions / agent_permissions / tool_executions）· 54 列 · FK 16 · CK 8 · trigger 3 · function 2 · seed 0 · 不分区。已冻结语义：

```text
tool_executions 不分区 · tenant FK RESTRICT
partial unique 幂等索引 · permission/tool/resource_scope 约束 · effect allow/deny
agents → versions → current_version 尾部 ALTER（condeferrable=false）· tenant/space 一致性触发器
```

## P10 / P11 / P12（0012 / 0013 / 0014 / 0015_p12_indexes）

```text
0012_authz_enforcement    阶段 2 铺垫
0013_p10_event_audit      P10 events → audit_logs ✅（验收 12/12）
0014_p11_triggers         P11 G/H/I/J ✅（验收 20/20）
0015_p12_indexes          P12 indexes 19 ✅（验收 20/20）· 当前 migration head
```

全量回归（P12 收官时点）：**636 passed / 0 failed / 6 skipped**（542→596→623→636 无回归；此后 integration 套件因 BATCH-A ownership 保护被禁跑，见 Rule 9）。

## Authorization / ACL / Policy Stage 2（当前 HEAD）

```text
commit      = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e
tag         = UAP-V0.1.8-AUTHORIZATION
tag object  = e9c83330384bc1d7582b0ae8a3bf857470063161
状态        = 已接受（该阶段 WORK ACCEPTED）
```

## 本周 OPEN-P10-1 序列（未 commit · 工作树内）

```text
角色/所有权（BATCH-A PASS）→ 配置分离（BATCH-B FINAL PASS）→
0016 创建（未持久执行）→ BLOCKED（env.py P0 缺陷）→ 见 08
```
