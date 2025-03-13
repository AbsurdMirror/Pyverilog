const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile('index.html');

  // 启用文件拖放
  mainWindow.webContents.on('will-navigate', (event) => {
    event.preventDefault();
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// IPC通信处理
ipcMain.handle('select-files', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [{ name: 'Verilog Files', extensions: ['v', 'h'] }]
  });
  return result.filePaths;
});

ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  
  if (!result.filePaths.length) return [];
  
  const dirPath = result.filePaths[0];
  const files = [];
  
  function scanDir(dir) {
    const entries = require('fs').readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        scanDir(fullPath);
      } else if (entry.isFile() && (entry.name.endsWith('.v') || entry.name.endsWith('.h'))) {
        files.push(fullPath);
      }
    }
  }
  
  scanDir(dirPath);
  return files;
});

ipcMain.handle('run-pyverilog', async (event, args) => {
  const { module, instance, top } = args;
  const scriptPath = path.join(__dirname, '..', 'myutils', 'gen_module_block_new.py');
  
  return new Promise((resolve, reject) => {
    const process = spawn('python', [
      scriptPath,
      module,
      instance,
      top
    ]);

    let output = '';
    let errorOutput = '';

    process.stdout.on('data', (data) => {
      output += data.toString();
    });

    process.stderr.on('data', (data) => {
      errorOutput += data.toString();
      console.error(`Error: ${data}`);
    });

    process.on('close', (code) => {
      if (code === 0) {
        resolve({ success: true, output });
      } else {
        reject(new Error(`Process exited with code ${code}\nError: ${errorOutput}`));
      }
    });

    process.on('error', (error) => {
      reject(new Error(`Failed to start process: ${error.message}`));
    });
  });
});

ipcMain.handle('analyze-module', async (event, args) => {
  const { files, moduleName, topModule } = args;
  const scriptPath = path.join(__dirname, '..', 'myutils', 'verilog_parser.py');
  
  return new Promise((resolve, reject) => {
    const process = spawn('python', [
      scriptPath,
      topModule,
      ...files
    ]);

    let output = '';
    let errorOutput = '';

    process.stdout.on('data', (data) => {
      output += data.toString();
    });

    process.stderr.on('data', (data) => {
      errorOutput += data.toString();
      console.error(`Error: ${data}`);
    });

    process.on('close', (code) => {
      if (code === 0) {
        try {
          console.log('解析成功，正在处理数据...', output);
          const result = JSON.parse(output);
          if (result.success) {
            // 只返回submodules数组，保持与之前代码的兼容性
            resolve(result.data.submodules);
          } else {
            // 处理解析成功但业务逻辑失败的情况
            reject(new Error(`解析失败: ${result.message || '未知错误'}`));
          }
        } catch (e) {
          reject(new Error(`解析JSON输出失败: ${e.message}\n原始输出: ${output}`));
        }
      } else {
        reject(new Error(`进程退出代码 ${code}\n错误: ${errorOutput}`));
      }
    });
  });
});

// 添加新的 IPC 处理程序用于生成图形
ipcMain.handle('generate-graph', async (event, args) => {
  const { files, moduleName, topModule } = args;
  const scriptPath = path.join(__dirname, '..', 'myutils', 'gen_module_block.py');
  
  return new Promise((resolve, reject) => {

    console.log('正在生成图形...', '命令行: python', scriptPath, "-t", topModule, "-i", moduleName, ...files);
    const process = spawn('python', [
      scriptPath,
      "-t", topModule,
      "-i", moduleName,
      ...files
    ]);

    let output = '';
    let errorOutput = '';

    process.stdout.on('data', (data) => {
      output += data.toString();
    });

    process.stderr.on('data', (data) => {
      errorOutput += data.toString();
      console.error(`Error: ${data}`);
    });

    process.on('close', (code) => {
      if (code === 0) {
        try {
          // 解析 Python 脚本返回的 JSON 输出
          const result = JSON.parse(output);
          if (result.success) {
            resolve(result);  // 直接返回解析后的结果对象
          } else {
            reject(new Error(result.error || '生成图形失败'));
          }
        } catch (e) {
          reject(new Error(`解析 JSON 输出失败: ${e.message}\n原始输出: ${output}`));
        }
      } else {
        reject(new Error(`生成图形失败，进程退出代码 ${code}\n错误: ${errorOutput}`));
      }
    });

    process.on('error', (error) => {
      reject(new Error(`启动图形生成进程失败: ${error.message}`));
    });
  });
});