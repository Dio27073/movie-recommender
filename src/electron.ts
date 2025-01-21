// src/electron.ts
import { app, BrowserWindow } from 'electron';
import path from 'path';
import { spawn } from 'child_process';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: any = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    // In development, load from Vite dev server
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:5173');
    } else {
        // In production, load the built files
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }
}

function startPythonBackend() {
    if (process.env.NODE_ENV === 'development') {
        // In development, start the Python process directly
        pythonProcess = spawn('python', ['-m', 'uvicorn', 'app.main:app', '--port', '8000'], {
            cwd: path.join(__dirname, '../backend')
        });
    } else {
        // In production, start the bundled executable
        const executablePath = process.platform === 'win32' ? 'backend.exe' : 'backend';
        pythonProcess = spawn(path.join(__dirname, '../backend/dist', executablePath));
    }

    pythonProcess.stdout.on('data', (data: any) => {
        console.log(`Python Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data: any) => {
        console.error(`Python Backend Error: ${data}`);
    });
}

app.whenReady().then(() => {
    createWindow();
    startPythonBackend();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
