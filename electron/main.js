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
  const { files, topModule } = args;
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
          const result = JSON.parse(output);
          resolve(result.submodules);
        } catch (e) {
          reject(new Error(`Failed to parse output: ${e.message}`));
        }
      } else {
        reject(new Error(`Process exited with code ${code}\nError: ${errorOutput}`));
      }
    });
  });
});