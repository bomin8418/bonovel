"use strict";

// vscode-bonovel：在集成终端中用 bo-novel 打开当前 .txt 小说。
// 自动定位 bonovel 可执行文件（不再依赖终端 PATH），找不到时回退到命令名。

const fs = require("fs");
const path = require("path");
const os = require("os");
const vscode = require("vscode");

function isAbsolutePath(cmd) {
  return path.isAbsolute(cmd) || /^[a-zA-Z]:[\\/]/.test(cmd);
}

function probeCandidates() {
  const cands = [];
  if (process.platform === "win32") {
    const localAppData = process.env.LOCALAPPDATA || "";
    const systemDrive = process.env.SystemDrive || "C:";
    if (localAppData) cands.push(path.join(localAppData, "bonovel", "bonovel.exe"));
    cands.push(path.join(systemDrive, "Python311", "Scripts", "bonovel.exe"));
    cands.push("C:\\Python311\\Scripts\\bonovel.exe");
  } else {
    cands.push(path.join(os.homedir(), ".local", "bin", "bonovel"));
    cands.push("/usr/local/bin/bonovel");
  }
  return cands;
}

function resolveBonovelCommand(cfg) {
  const configured = cfg.get("command", "bonovel");
  if (isAbsolutePath(configured)) {
    return { command: configured, source: "config" };
  }
  for (const cand of probeCandidates()) {
    try {
      if (fs.existsSync(cand)) {
        return { command: cand, source: "probe" };
      }
    } catch (_e) {
      /* ignore */
    }
  }
  return { command: configured, source: "path" };
}

function activate(context) {
  let warned = false;

  context.subscriptions.push(
    vscode.commands.registerCommand("bonovel.open", async (uri) => {
      let file = null;
      if (uri && uri.fsPath) {
        file = uri.fsPath;
      } else if (vscode.window.activeTextEditor) {
        file = vscode.window.activeTextEditor.document.fileName;
      }
      if (!file) {
        vscode.window.showWarningMessage("bo-novel：请先打开一个 .txt 小说文件。");
        return;
      }
      if (!/\.txt$/i.test(file)) {
        vscode.window.showWarningMessage(
          "bo-novel：仅支持 .txt 小说文件（当前：" + file + "）。"
        );
        return;
      }
      const cfg = vscode.workspace.getConfiguration("bonovel");
      const { command, source } = resolveBonovelCommand(cfg);
      if (source === "path" && !warned) {
        warned = true;
        const pick = await vscode.window.showWarningMessage(
          "bo-novel：找不到 bonovel 可执行文件（终端 PATH 可能过期）。" +
            "请重启 VSCode，或在设置中把 bonovel.command 设为完整路径（如 C:\\python311\\Scripts\\bonovel.exe）。",
          "打开设置"
        );
        if (pick === "打开设置") {
          vscode.commands.executeCommand(
            "workbench.action.openSettings",
            "bonovel.command"
          );
        }
      }
      const dataDir = cfg.get("dataDir", "") || "";
      const esc = (s) => String(s).replace(/"/g, '\\"');
      const quoteIfNeeded = (s) =>
        /\s/.test(String(s)) && !/^"/.test(String(s))
          ? `"${String(s).replace(/"/g, '\\"')}"`
          : String(s);
      let line = `${quoteIfNeeded(command)} "${esc(file)}"`;
      if (dataDir) {
        line += ` -d "${esc(dataDir)}"`;
      }
      const term = vscode.window.createTerminal({ name: "bo-novel" });
      term.show();
      term.sendText(line);
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
