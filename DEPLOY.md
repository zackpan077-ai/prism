# Prism 部署指南：云端自动运行（GitHub Actions + Pages）

本方案解决「电脑关了就不跑」的问题：把仓库推到 GitHub，用 Actions 每天三次自动生成期刊并发布到 GitHub Pages。全程免费额度即可（每天 3 次运行，每次约 3-5 分钟，远低于免费上限）。

## 前置条件

- 一个 GitHub 账号
- 本地 git 已配置（项目已有 git 仓库）

## 第一步：把仓库推到 GitHub

### 方式 A：用 gh CLI（推荐，已装 gh 的话）

```powershell
cd C:\Users\zackp\Projects\prism
gh repo create prism --private --source=. --push
```

### 方式 B：网页创建 + 手动推送

1. 打开 https://github.com/new ，仓库名填 `prism`，选 **Private**（推荐，data/ 里有抓取数据），点 Create repository。
2. 按页面提示执行：

```powershell
cd C:\Users\zackp\Projects\prism
git remote add origin https://github.com/<你的用户名>/prism.git
git push -u origin master
```

> 注意：`.env` 已在 `.gitignore` 里，不会被推上去；API key 只通过 GitHub Secrets 注入（见下一步）。

## 第二步：配置 Secrets

打开仓库页面 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**，添加：

| Name | Value | 说明 |
|---|---|---|
| `PRISM_API_KEY` | 你的智谱 API key | 必填 |
| `PRISM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | 必填（或你实际用的端点，如 coding 计划端点）|
| `PRISM_MODEL` | `glm-5.3` | 建议填上 |

workflow 会把这三个值写进运行器上的 `.env`，跑完即销毁，不会进入 git 历史。

## 第三步：开启 GitHub Pages

用的是官方 **GitHub Actions 部署**方式（workflow 自带 `deploy-pages` 步骤，不需要 gh-pages 分支）：

1. 仓库 → **Settings** → **Pages**。
2. **Build and deployment** → **Source** 选 **GitHub Actions**（不是 Deploy from a branch），保存即可。
3. 首次成功运行 workflow 后，Pages 地址 `https://<用户名>.github.io/prism/` 即可访问。

> **注意**：免费账号的 GitHub Pages 只对 **Public** 仓库开放；Private 仓库要用 Pages 需要 GitHub Pro（$4/月）。如果不想公开仓库也不想付费，可以跳过本步——期刊 HTML 就存在仓库的 `site/` 目录里，随时下载本地打开，或以后再改公开。

## 第四步：手动触发一次验证

1. 仓库 → **Actions** 标签页 → 左侧选 `daily` workflow。
2. 右侧 **Run workflow** 按钮 → 分支选 `master`，`slot` 可以留空（自动按北京时间选档）或手动指定 `morning`/`noon`/`evening` → 点 **Run workflow**。
3. 点进运行记录，看 `publish` job 是否全绿。成功后：
   - `site/` 和 `data/` 的新文件被自动 commit 回 `master`（提交者是 `prism-bot`）。
   - Pages 地址刷新即可看到最新期刊。

## 定时说明（重要）

- workflow 里写了**三个 cron**：UTC `23:30`（北京 07:30 早刊）、`04:00`（北京 12:00 午刊）、`10:00`（北京 18:00 晚刊）。
- **GitHub Actions 的 cron 可能延迟几分钟到几十分钟**（高峰期更久），属正常现象；如果某次彻底没跑，可以手动 Run workflow 补上（档位选对应时段即可）。
- workflow 里**显式传 `--slot`**，避免 UTC→北京的转换偏差导致选错档。
- 免费额度：公开/私有仓库每月 2000 分钟（公开仓库无限），本项目每天 3 次 × ~5 分钟 ≈ 450 分钟/月，完全够用。

## 本地与云端并存（及清理）

本地 `PrismDaily` 任务（每天 7:30/12:00/18:00）和云端 Actions 可以并存，互不冲突——同一档位两边都跑会生成同样的文件，后跑的覆盖先跑的。只想留云端的话，删除本地任务：

```powershell
Unregister-ScheduledTask -TaskName "PrismDaily" -Confirm:$false
```

查看现有任务：

```powershell
Get-ScheduledTask -TaskName "PrismDaily" | Select-Object TaskName, State
```

## 常见问题

- **Actions 没跑**：先确认 `.github/workflows/daily.yml` 已经推到默认分支；schedule 只对默认分支生效。
- **跑失败**：进 Actions 看日志，最常见是 `PRISM_API_KEY` secret 没配或配错名字。
- **Pages 404**：确认 Settings → Pages 的 Source 已选 **GitHub Actions**，且 workflow 至少成功跑过一次。
- **想改触发时间**：编辑 `.github/workflows/daily.yml` 里的 `cron` 行（UTC 时间），注意北京 7:30 = UTC 前一天 23:30。