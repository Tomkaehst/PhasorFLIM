const ipc = require("electron").ipcMain;
const dialog = require("electron").dialog;


ipc.on("ptu-filepath", function (event) {
      dialog.showOpenDialog({
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


