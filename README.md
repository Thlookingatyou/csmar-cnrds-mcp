# Campus Data MCP

[中文](#中文介绍) · [English](#english)

## 中文介绍

**让 AI 智能体使用学校已有的 CSMAR（国泰安）和 CNRDS（中国研究数据服务平台）访问权限，检索并下载研究数据，无需向智能体提供数据库账号和密码。**

本项目在你的电脑上运行浏览器，通过校园网或学校支持的 VPN 使用机构授权。接入支持本地 MCP 的 AI 智能体后，可以让它搜索数据目录、选择数据表和筛选条件，并将导出文件保存到本地。智能体若具备本地文件读取工具，还可以继续读取和分析下载的数据。

使用前，学校需已订阅相应数据库，且当前网络具备访问权限。电脑需安装 Python 3.11+ 和 Chromium，并按[安装与配置指南](docs/setup.md)连接智能体。具备本地命令执行能力的智能体可协助完成安装；仅发送 GitHub 链接不会自动启用数据库访问。

**当前状态：实验性项目。** 已在一个获授权的校园网络中完成两个数据库的小规模真实下载验证，部分界面操作仍需要浏览器辅助。其他学校、专题数据库及完全无人值守的使用方式尚未验证。实际可用数据取决于学校订阅和平台权限，使用时请遵守相应的数据许可。

## English

**Let AI agents search and download research data through your institution’s existing CSMAR and CNRDS access, without sharing a database username or password with the agent.**

The project runs a browser on your computer and uses your campus network or institution-supported VPN. Connect it to an agent that supports local MCP servers to search catalogues, select tables and filters, and save exports locally. Agents with file-reading tools can also read and analyse the downloaded data.

Your institution must subscribe to the requested data, and your network must have access. Setup requires Python 3.11+, Chromium and a local MCP connection; follow the [setup guide](docs/setup.md). An agent with local command execution can help install it. Sharing the GitHub link alone does not enable database access.

**Status: experimental.** Small real downloads from both providers have been verified on one authorized campus network, with browser assistance needed for some controls. Other institutions, specialty databases and fully unattended operation remain unverified. Available data depends on institutional subscriptions and provider permissions; applicable data licences still apply.

## 文档 / Documentation

- [安装与配置 / Setup and usage](docs/setup.md)
- [智能体操作流程 / Agent workflow](docs/agent-workflow.md)
- [验证结果与已知限制 / Validation and limitations](docs/validation.md)
- [可行性评估 / Feasibility assessment](docs/feasibility.md)

本项目为非官方集成，代码采用 MIT 许可证；数据库内容及下载数据的权利归原权利人所有。

An unofficial integration. Original code is MIT-licensed; database content and downloaded data retain their owners’ rights.
