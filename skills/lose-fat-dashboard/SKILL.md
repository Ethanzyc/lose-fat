---
name: lose-fat-dashboard
description: 减脂数据可视化仪表盘，提供本地 Web 仪表盘和静态 HTML 报告生成
triggers:
  - dashboard
  - 仪表盘
  - 减脂数据
  - 数据可视化
---

# 减脂数据仪表盘

为减脂健康管理提供数据可视化，支持两种模式：

1. **本地仪表盘** — 启动 Python 本地服务，实时读取 `.lose-fat/profiles/` 中的用户档案，支持多用户切换
2. **静态 HTML 报告** — 生成自包含的 HTML 文件（数据内嵌 + Chart.js 图表），可分享存档

## 路径配置

- **用户档案目录**：基于当前工作目录的 `.lose-fat/profiles/`
- **导出文件目录**：基于当前工作目录的 `.lose-fat/output/`
- **服务脚本**：相对于本 SKILL.md 所在目录的 `server.py`
- **仪表盘页面**：相对于本 SKILL.md 所在目录的 `dashboard.html`
- **报告模板**：相对于本 SKILL.md 所在目录的 `templates/report.html`
- **PID 文件**：`.lose-fat/server.pid`（记录服务进程）

## 流程

### 第一步：前置检查

1. 确保目录存在：`mkdir -p .lose-fat/profiles .lose-fat/output`
2. 检查是否有用户档案：`ls .lose-fat/profiles/*.json 2>/dev/null`
3. 如果没有档案 → 告知用户「暂无用户档案，请先使用 /lose-fat 创建健康档案」，结束流程

### 第二步：选择操作

使用 AskUserQuestion 工具让用户选择：

- **启动仪表盘** — 启动本地 Web 服务，在浏览器中查看交互式数据面板
- **生成静态报告** — 生成 HTML 文件（可离线查看、分享给他人）
- **停止服务** — 停止正在运行的仪表盘服务
- **重启服务** — 重启仪表盘服务

### 第三步：启动仪表盘

1. 检查服务是否已在运行：
   ```
   if [ -f .lose-fat/server.pid ] && kill -0 $(cat .lose-fat/server.pid) 2>/dev/null; then
     echo "running"
   else
     echo "stopped"
   fi
   ```
2. 如果已在运行 → 告知用户访问地址 `http://localhost:8642`，并询问是否需要重启
3. 如果未运行：
   - 检查端口是否被占用：`lsof -i :8642`
   - 启动服务：`nohup python3 server.py > /dev/null 2>&1 & echo $!`
   - 将 PID 写入 `.lose-fat/server.pid`
   - 自动打开浏览器：`open http://localhost:8642`（macOS）或根据系统选择命令
   - 告知用户：「仪表盘已启动，访问 http://localhost:8642 。停止服务请使用 /dashboard 然后选择「停止服务」。」

**默认端口**：8642，可通过 `--port` 参数修改

### 第四步：生成静态报告

1. 列出所有用户档案，使用 AskUserQuestion 让用户选择要导出的用户
2. 读取该用户档案 JSON 文件
3. 读取模板文件 `templates/report.html`
4. 准备数据对象：
   ```json
   {
     "userName": "姓名",
     "reportDate": "2026-04-23",
     "profile": { ...完整用户档案... },
     "assessment": "最新健康评估的markdown文本（来自档案的 latest_assessment 字段）",
     "plan": "最新减脂计划的markdown文本（来自档案的 latest_plan 字段）"
   }
   ```
5. 将模板中的 `__DATA__` 替换为 `JSON.stringify(数据对象)`
6. 写入 `.lose-fat/output/{用户名}_{日期}_减脂方案.html`
7. 告知用户文件路径，双击即可在浏览器中打开

### 第五步：停止服务

1. 检查 PID 文件：`cat .lose-fat/server.pid 2>/dev/null`
2. 如果存在且进程在运行 → `kill $(cat .lose-fat/server.pid) && rm .lose-fat/server.pid`
3. 如果不存在或进程已停止 → 告知用户「服务未在运行」
4. 告知用户：「仪表盘服务已停止。」

### 第六步：重启服务

1. 先执行停止操作（第五步）
2. 再执行启动操作（第三步）
