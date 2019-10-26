module.exports = {
      decodePTU: function (filePath) {

            const fs = require("fs");
            const ipc = require("electron").ipcRenderer;

            var tagTypes = {
                  Empty8: 4294901768,
                  Bool8: 8,
                  Int8: 268435464,
                  Color8: 301989896,
                  Float8: 536870920,
                  DateTime: 553648136,
                  Float8Array: 537001983,
                  AnsiString: 1073872895,
                  WideString: 1073938431
            };

            // Not all record types are implemented here! We only have a HydraHarp2T3. To complement the missing record types, see https://github.com/PicoQuant/PicoQuant-Time-Tagged-File-Format-Demos
            var recordTypes = {
                  HydraHarp2T3: 16843524
            };


            // Loading the .ptu file in ./data into the buffer
            //var filePath = "./data/Convalaria_for_CC_6_1.ptu" // Small test file
            console.info("Decoding " + filePath + "\n");
            let data = fs.readFileSync(filePath); // Need to switch to asynchronous reading for larger files!


            // Check if file is a valid .ptu -> MAGIC = 'PQTTTR' and file version
            var offset = 0;
            var magic = data.slice(offset, offset + 6).toString("utf8");
            offset += 8;
            var version = data.slice(offset, offset + 6).toString();
            offset += 8;

            if (magic != "PQTTTR") {
                  ipc.send("loading-ptu-finished");
                  alert("Not a (valid) .ptu file!");
                  throw "Not a (valid) .ptu file.";
            };

            // Sending to main to start displaying progress bar to the user
            ipc.send("start-progressbar");


            // Decoding the header section
            const tag_HeaderEnd = "Header_End"; // Last Entry of the Header; terminates reading loop
            var offset_Header_End = data.indexOf("Header_End") + 48; // Used later to check whether the number of bytes without the header divived by 4 (because one record has 4 bytes) is equal to the numRec in the file header
            let reachedHeaderEnd = false;
            let entry = NaN; // empty variable to assign the tag entry to 

            let HeaderContents = {};

            /* Header Decoding .ptu files */

            while (reachedHeaderEnd == false) {

                  let tag_data = data.slice(offset, offset + 48);
                  offset += 48;
                  let tagId = tag_data.slice(0, 32).toString().replace(/\0/g, ""); // .replace() removes zero padding using regex!
                  //var tagIdx = tag_data.slice(32, 36).readInt32LE(); // What's the point of that?
                  let typeCode = tag_data.slice(36, 40).readUInt32LE();
                  let tagVal = tag_data.slice(40, 48);

                  if (typeCode == tagTypes.Empty8) {
                        if (tagId == tag_HeaderEnd) {
                              reachedHeaderEnd = true;
                        }
                        else {
                              HeaderContents[tagId] = tagVal.readUInt8();
                        }
                  }
                  else if (typeCode == tagTypes.Bool8) {
                        entry = tagVal.readInt8 > 0 ? true : false;
                        HeaderContents[tagId] = entry;
                  }
                  else if (typeCode == tagTypes.Int8) {
                        HeaderContents[tagId] = tagVal.readInt32LE();
                  }
                  else if (typeCode == tagTypes.Color8) {
                        HeaderContents[tagId] = tagVal.readInt8();
                  }
                  else if (typeCode == tagTypes.Float8) {
                        entry = tagVal;
                        HeaderContents[tagId] = tagVal.readDoubleLE();
                  }
                  else if (typeCode == tagTypes.DateTime) {
                        HeaderContents[tagId] = new Date(tagVal.readUInt32LE());
                  }
                  else if (typeCode == tagTypes.Float8Array) {
                        if (tagVal.readUInt32LE() % 8 == 0) {
                              entry = data.slice(offset, offset + tagVal.readUInt32LE());
                              offset += tagVal.readUInt32LE();
                        }
                        else {
                              throw "Error in Float8Array decoding in .ptu header.";
                        }
                        HeaderContents[tagId] = entry;
                  }
                  else if (typeCode == tagTypes.AnsiString) {
                        if (tagVal.readUInt32LE() % 8 == 0) {
                              entry = data.slice(offset, offset + tagVal.readUInt32LE()).toString('binary').replace(/\0/g, "");
                              offset += tagVal.readUInt32LE();
                        }
                        else {
                              throw "Error in AnsiString decoding in .ptu header.";
                        }
                        HeaderContents[tagId] = entry;
                  }
                  else if (typeCode == tagTypes.WideString) {
                        if (tagVal.readUInt32LE() % 8 == 0) {
                              entry = data.slice(offset, offset + tagVal.readUInt32LE()).toString('latin1').replace(/\0/g, "");
                              offset += tagVal.readUInt32LE();
                        }
                        else {
                              throw "Error in WideString decoding in .ptu header.";
                        }
                        HeaderContents[tagId] = entry;
                  }
                  else {
                        console.log("Error occured during header decoding.\n Typecode: " + typeCode + ", TagID: " + tagId + ", Value: " + tagVal + "\n");
                  }
            };

            let FLIMInfo = {
                  filename: HeaderContents.$Filename,
                  recType: HeaderContents.TTResultFormat_TTTRRecType,
                  bitsPerRecord: HeaderContents.TTResultFormat_BitsPerRecord,
                  pixelRes: HeaderContents.$ReqHdr_SpatialResolution,
                  pixelX: HeaderContents.ImgHdr_PixX,
                  pixelY: HeaderContents.ImgHdr_PixY,
                  globRes: HeaderContents.MeasDesc_GlobalResolution,
                  basRes: HeaderContents.HW_BaseResolution,
                  measRes: HeaderContents.MeasDesc_Resolution,
                  syncRate: HeaderContents.TTResult_SyncRate,
                  binFactor: HeaderContents.MeasDesc_BinningFactor,
                  numRec: HeaderContents.TTResult_NumberOfRecords,
                  fileinfo: HeaderContents.$Comment
            };



            // Checking if image is square, otherwise the rest of the code won't work

            if (FLIMInfo.pixelX != FLIMInfo.pixelY) {
                  throw "Image not square. Abort."
            }


            // Checking the record type; currently only HydraHarp 2 T3 is implemented!
            if (FLIMInfo.recType != recordTypes.HydraHarp2T3) {
                  throw "TTTR records of your .ptu not implemented yet!";
            }


            // Checking if remaining bytes in data (without header) matched FLIMInfo.numRec
            if (FLIMInfo.numRec != (data.byteLength - offset_Header_End) / 4) {
                  throw "Number of records specified in header does not match number of remaining bytes in currently accessed file. Check file validity.";
            }
            else {
                  console.log("Processing " + FLIMInfo.numRec + " records from " + filePath);
            }




            // Reading the records from the file into three arrays! (for now)
            var record;
            var macrotime = [];
            var nanotime = [];
            var markers = [];
            // var macrotime = new Array(FLIMInfo.numRec);
            // var nanotime = new Array(FLIMInfo.numRec);
            // var markers = new Array(FLIMInfo.numRec);
            const overflow_period = 1024;
            var overflow_corr = 0;
            var macroMultFactor = FLIMInfo.globRes // Multiply with truensync to get real experiment time in seconds
            var nanoMultFactor = FLIMInfo.measRes * 1e9;
            const bytesToFileEnd = data.byteLength - 4;

            offset = offset_Header_End;

            // Reading raw record data from file
            while (offset <= bytesToFileEnd) {
                  record = data.readInt32LE(offset);
                  markers.push((record >>> 25) & 2 ** 7 - 1);
                  nanotime.push(((record >>> 10) & 2 ** 15 - 1) * nanoMultFactor);

                  if (((record >>> 25) & 2 ** 7 - 1) == 127) {
                        overflow_corr += overflow_period * (record & (2 ** 10 - 1));
                  };
                  macrotime.push((overflow_corr + (record & (2 ** 10 - 1))) * macroMultFactor);


                  if (offset % 100000 == 0) {
                        ipc.send("update-progressbar", ["Decoding .ptu ...", Math.round((offset / bytesToFileEnd) * 100)]);
                  }

                  // Moving on to the next record
                  offset += 4;
            };

            var recordData = {
                  macrotime: macrotime, // in seconds
                  nanotime: nanotime, // in nanoseconds
                  markers: markers,
                  shortinfo: FLIMInfo,
                  fullinfo: HeaderContents
            };

            // Deleting the record arrays (I hope this "forces" JavaScript to free the memory)
            macrotime = null;
            nanotime = null;
            markers = null;

            // Getting number of lines to see if file is corrupted

            recordData.shortinfo.lines = this.getNumberOfLines(recordData);

            return (recordData);
      },

      getNumberOfLines(arr) {
            let counterStart = 0;
            let counterStop = 0;
            arr.markers.forEach(function (marker) {
                  if (marker == 65) { counterStart++; }
                  if (marker == 66) { counterStop++; }
            });

            if (counterStart != counterStop) {
                  alert("Number of line start and line stop markers do not match. Corrupted file?")
            };

            console.log(counterStart + " line start and " + counterStop + " line stop markers found.");
            console.log("Image dimensions: X = " + arr.shortinfo.pixelX + ", Y = " + arr.shortinfo.pixelY + "\n");
            console.log("FLIM Image with " + (counterStart / arr.shortinfo.pixelX) + "/" + (counterStop / arr.shortinfo.pixelX) + " scan repetitions.\n");
            console.log(arr.shortinfo.numRec + " events in decoded .ptu file.\n")

            return (counterStart);
      }
};