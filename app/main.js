// Modules to control application life and create native browser window
const { app, BrowserWindow } = require('electron')

const ipc = require("electron").ipcMain;
const dialog = require("electron").dialog;
const Progressbar = require("electron-progressbar");

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;
let progressbar;

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1280, height: 1280
  });

  // and load the index.html of the app.
  mainWindow.loadFile('index.html')

  // Open the DevTools.
  mainWindow.webContents.openDevTools()

  // Emitted when the window is closed.
  mainWindow.on('closed', function () {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null;
  })
};


// Adding code for displaying progress bar
function showProgressbar() {
  if (progressbar) {
    return
  };

  progressbar = new Progressbar({
    text: "Decoding .ptu file...",
    detail: "Please wait...",
    browserWindow: {
      parent: mainWindow
    }
  });

  progressbar
    .on("completed", function () {
      progressbar.detail = "Finished decoding."
      progressbar = null;
    });
};

function setProgressbarCompleted() {
  if (progressbar) {
    progressbar.setCompleted();
  }
}



// Increasing the max RAM available to electron
app.commandLine.appendSwitch('js-flags', '--max-old-space-size=4096');


// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', function () {
  createWindow();

  // Handling progress bar -> via IPC
  ipc.on("showProgressbar", showProgressbar);
  ipc.on("setProgressbarCompleted", setProgressbarCompleted);
});

// Quit when all windows are closed.
app.on('window-all-closed', function () {
  // On OS X it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', function () {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createWindow()
  }
})


// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.


// IPC receivers for processing fs tasks

ipc.on("ptu-filepath", function (event) {
  dialog.showOpenDialog(mainWindow, {
    title: "Select your .ptu file",
    defaultPath: "/Users/<username>/Documents/",
    buttonLabel: "Decode this .ptu file",
    properties: ["openFile"]
  }, function (file) {
    if (file) {
      event.sender.send("selectedptu", file);
    };
  })
});

