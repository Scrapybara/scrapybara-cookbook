const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const WebSocket = require("ws");
require("dotenv").config();

let mainWindow;
let ws = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 400,
    height: 80, // Start smaller initially
    frame: false,
    transparent: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      devTools: true,
    },
  });

  mainWindow.loadFile("index.html");
  mainWindow.setAlwaysOnTop(true);
  mainWindow.setVisibleOnAllWorkspaces(true);

  // Open DevTools automatically (optional)
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(createWindow);

// Handle websocket connection
ipcMain.handle("connect-websocket", async (event) => {
  try {
    ws = new WebSocket("wss://api.playground.scrapybara.com/ws/chat");

    ws.on("open", () => {
      console.log("WebSocket connected");
      ws.send(JSON.stringify({ api_key: process.env.SCRAPYBARA_API_KEY }));
    });

    ws.on("message", (data) => {
      const message = JSON.parse(data);
      console.log(message);
      mainWindow.webContents.send("websocket-message", message);

      // Modify this to create a larger window for better viewing
      if (message.type === "url") {
        mainWindow.setSize(800, 702);
      }
    });

    mainWindow.setSize(400, 110);
    return true;
  } catch (error) {
    console.error("WebSocket connection error:", error);
    return false;
  }
});

// Handle command execution
ipcMain.handle("send-command", async (event, command) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ message: command }));
    return true;
  }
  return false;
});

// Window controls
ipcMain.on("minimize-window", () => {
  mainWindow.minimize();
});
