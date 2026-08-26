"use strict";

// vscode-bonovel：在集成终端中用 bo-novel 打开当前 .txt 小说。

const vscode = require("vscode");

function activate(context) {
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
      const cmd = cfg.get("command", "bonovel");
      const dataDir = cfg.get("dataDir", "") || "";
      const esc = (s) => String(s).replace(/"/g, '\\"');
      let line = `${cmd} "${esc(file)}"`;
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
