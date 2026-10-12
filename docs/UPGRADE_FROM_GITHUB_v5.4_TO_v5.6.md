# 从 GitHub main v5.4 升级到本地候选 v5.6 的说明

1. **先比较当前远端main提交。** 准备此包时GitHub `main` 为 `ae0f043f0e19ef49c8915fd2a53e324d10561245`，`SKILL.md`版本是v5.4.0。若已变化，请先进行实际代码差异合并，不要盲目覆盖。
2. v5.6 基于**未推送v5.5开发候选**继续实现。所以从GitHub main v5.4升级，必须同时包含 v5.5资金归属纠错和v5.6 Master Plan，不能只复制一个最新SKILL.md。
3. 推荐在单独分支上解压此完整仓库，保留 GitHub 上用户自定义的产品首页 `README.md`，并更新其版本与Master Plan入口；不要把技术型 README 覆盖成用户产品首页，除非自行决定。
4. 安装到 Codex/Claude Code仅需 `skills/personal-finance-planner` 整个文件夹，而不是全部GitHub仓库。执行 `SKILL.md` 的版本必须在宿主实际上已加载，不可从README版本猜测。
5. 在真实Git工作区运行：

```bash
python tools/check_architecture.py --strict
python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q
python -m unittest discover -s tests -p 'test_*.py' -q
python tools/manifest.py --write
python tools/manifest.py --verify
```

6. 检查 diff 和安全文件清单，只提交规范、脚本、模板和**合成案例**；不提交账号信息、密钥、私人记忆或客户真实财务报告。先发 PR，并填写 `docs/ARCHITECTURE_ALIGNMENT_v5.6.0.md` 的验收差异。
7. 本地资料不是实时金融法律事实；产物没有替用户GitHub自动推送，亦没有真的在Codex/Claude Code开展联网E2E测试。
