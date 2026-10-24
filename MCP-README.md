# Salsmart: connect your coding agent

Use the free, read-only Salsmart MCP endpoint to search Israeli grocery prices
and check source freshness. No Salsmart account, API key, payment or local server
runtime is required. These files are configuration templates; this bundle does
not install packages, change editor settings or start a connection automatically.

Choose one configuration for your client. If your project already has MCP
settings, merge only the `salsmart` entry instead of replacing the file. Avoid
adding the same server in multiple scopes.

## Claude Code and the portable Copilot configuration

Copy `.mcp.json` to your project's root, or merge its `mcpServers.salsmart` entry.
The explicit `"type": "http"` is required for this remote server. Start Claude
Code from the project, review its workspace/server trust prompt, and use `/mcp`
to check Salsmart's connection and tools.

Alternatively, if you prefer Claude Code to write the project entry, run this
from your project directory instead of copying the file:

```sh
claude mcp add --transport http --scope project salsmart https://salsmart.com/mcp
claude mcp get salsmart
```

The portable `.mcp.json` format is also supported by compatible GitHub Copilot
harnesses. It uses `mcpServers`, unlike the VS Code-specific format below. Your
client's account, feature access and organization policy still determine whether
you can use MCP; the Salsmart endpoint itself remains free.

## VS Code-specific configuration

For the VS Code workspace configuration, copy `.vscode/mcp.json` into your
project, or merge `servers.salsmart` into your existing file. This format uses
`servers`. Open the file in VS Code and use the server's Start action, reviewing
the endpoint before approving any trust prompt. In Agent chat, enable Salsmart's
tools and inspect an actual tool result.

You can also use the Command Palette: **MCP: Add Server → HTTP**, enter
`https://salsmart.com/mcp`, name it `salsmart`, and choose your intended scope.
Current Copilot harnesses may offer the portable `.mcp.json` destination; choose
that instead when appropriate. Do not configure both files for the same active
harness just to connect one server.

## Verify your first useful result

Ask your agent:

> Use Salsmart's get_data_status to check current coverage. Then call
> search_products with q="חלב תנובה" and limit=5. Compare the returned branch
> offers in ILS, include source dates and links, and state any freshness limits.
> Do not infer live stock or claim the cheapest price across all of Israel.

Confirm that the agent actually called `get_data_status` and `search_products`.
An answer without a visible tool call is not proof of a working connection.
For a repeatable check, search one exact returned barcode as a string; preserve
leading zeros. A search with no matches should return no products, not substitute
an invented match. The optional embedded UI depends on client support; the text
and structured tool data are sufficient.

Free search returns up to 20 products and shares limits of 60 requests/minute and
500/day UTC per network address. Shared client/proxy addresses can share the
allowance. On a quota response, follow Retry-After and wait for reset; no purchase
is required to continue after reset. Coverage is partial and does not establish
inventory or a nationwide lowest price.

This is a direct custom connection. These templates do not assert that Salsmart
has been approved or publicly listed in ChatGPT, Claude or Grok marketplaces.

## Sources and help

- [Salsmart connection guide](https://salsmart.com/connect)
- [Salsmart privacy](https://salsmart.com/privacy) and [support](https://salsmart.com/support)
- [Claude Code: remote HTTP, project scope and server approval](https://code.claude.com/docs/en/mcp)
- [VS Code: configuration formats](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)
- [VS Code: add a server and verify a tool call](https://code.visualstudio.com/docs/agent-customization/mcp-servers)
