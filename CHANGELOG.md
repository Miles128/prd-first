# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-07-19

### Added
- `prd skill install [claude|cursor|codex|all]`：一键安装 AI 助手 Skill
- `prd edit` 无参数时列出可编辑字段与状态
- `prd show --section <key>`：只查看单个字段
- `prd --version` / `-V`
- 初始化时提示题目总数与必填数
- PyPI 发布工作流（GitHub Release + Trusted Publishing）
- `CHANGELOG.md` 与发布说明

### Changed
- web-app 将可选「认证方式」移到必填题之后，减少中途打断
- list 输入增加空行结束提示
- README 补充 Skill 一键接入与发版步骤

## [0.2.0] - 2026-07-19

### Added
- `prd new` / `prd edit` / `prd template list`
- 模板字段 `why` 引导文案
- backend-data 必填「监控告警」
- list 字段替换 / 追加 / 保持
- 更清晰的 `prd check` 输出

### Fixed
- 可选空字段不再误标「必填项未填写」
- 文档与模板字段不一致

## [0.1.0] - 2026-07

### Added
- 初始 CLI：`init` / `check` / `show`
- 四类项目模板与 Skill 文档

[0.3.0]: https://github.com/Miles128/prd-first/releases/tag/v0.3.0
[0.2.0]: https://github.com/Miles128/prd-first/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Miles128/prd-first/releases/tag/v0.1.0
