
module.exports = {
      decodePTU: function (filePath) {

            const fs = require("fs");
            const bitwise = require("bitwise");
            const ipc = require("electron").ipcRenderer;

            // Sending to main to start displaying progress bar to the user
            ipc.send("started-loading-ptu");

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
            var testBuff = bitwise.buffer.read(data, 0, 48);
            offset += 8;
            var version = data.slice(offset, offset + 6).toString();
            offset += 8;

            if (magic != "PQTTTR") {
                  throw "Not a (valid) .ptu file.";
            }


            // Decoding the header section
            const tag_HeaderEnd = "Header_End"; // Last Entry of the Header; terminates reading loop
            var offset_Header_End = data.indexOf("Header_End") + 48; // Used later to check whether the number of bytes without the header divived by 4 (because one record has 4 bytes) is equal to the numRec in the file header
            let reachedHeaderEnd = false;
            let entry = NaN; // empty variable to assign the tag entry to 

            var HeaderContents = [
                  { FileMagic: magic },
                  { FileVersion: version }
            ];



            /* Header Decoding .ptu files */

            while (reachedHeaderEnd == false) {

                  var tag_data = data.slice(offset, offset + 48);
                  offset += 48;
                  var tagId = tag_data.slice(0, 32).toString().replace(/\0/g, ""); // .replace() removes zero padding using regex!
                  //var tagIdx = tag_data.slice(32, 36).readInt32LE(); // What's the point of that?
                  var typeCode = tag_data.slice(36, 40).readUInt32LE();
                  var tagVal = tag_data.slice(40, 48);



                  if (typeCode == tagTypes.Empty8) {
                        if (tagId == tag_HeaderEnd) {
                              reachedHeaderEnd = true;
                        }
                        else {
                              HeaderContents.push({ [tagId]: tagVal.readUInt8() });
                        }
                  }
                  else if (typeCode == tagTypes.Bool8) {
                        entry = tagVal.readInt8 > 0 ? true : false;
                        HeaderContents.push({ [tagId]: entry });
                  }
                  else if (typeCode == tagTypes.Int8) {
                        HeaderContents.push({ [tagId]: tagVal.readInt32LE() });
                  }
                  else if (typeCode == tagTypes.Color8) {
                        HeaderContents.push({ [tagId]: tagVal.readInt8() });
                  }
                  else if (typeCode == tagTypes.Float8) {
                        entry = tagVal;
                        HeaderContents.push({ [tagId]: tagVal.readDoubleLE() });
                  }
                  else if (typeCode == tagTypes.DateTime) {
                        HeaderContents.push({ [tagId]: tagVal.readInt32LE() });
                  }
                  else if (typeCode == tagTypes.Float8Array) {
                        if (tagVal.readUInt32LE() % 8 == 0) {
                              entry = data.slice(offset, offset + tagVal.readUInt32LE());
                              offset += tagVal.readUInt32LE();
                        }
                        else {
                              throw "Error in Float8Array decoding in .ptu header.";
                        }
                        HeaderContents.push({ [tagId]: entry });
                  }
                  else if (typeCode == tagTypes.AnsiString) {
                        if (tagVal.readUInt32LE() % 8 == 0) {
                              entry = data.slice(offset, offset + tagVal.readUInt32LE()).toString('latin1').replace(/\0/g, "");
                              offset += tagVal.readUInt32LE();
                        }
                        else {
                              throw "Error in AnsiString decoding in .ptu header.";
                        }
                        HeaderContents.push({ [tagId]: entry });
                  }
                  else if (typeCode == tagTypes.WideString) {
                        if (tagVal.readUInt32LE() % 8 == 0) {
                              entry = data.slice(offset, offset + tagVal.readUInt32LE()).toString('latin1').replace(/\0/g, "");
                              offset += tagVal.readUInt32LE();
                        }
                        else {
                              throw "Error in WideString decoding in .ptu header.";
                        }
                        HeaderContents.push({ [tagId]: entry });
                  }
                  else {
                        console.log("Error occured during header decoding.");
                  }
            }


            // Grabbing relevant infos out of header for record reading
            var FLIMInfo = {
                  globRes: HeaderContents[88].MeasDesc_GlobalResolution,
                  measRes: HeaderContents[57].MeasDesc_Resolution,
                  baseRes: HeaderContents[55].HW_BaseResolution,
                  binFactor: HeaderContents[56].MeasDesc_BinningFactor,
                  pixelRes: HeaderContents[26].ImgHdr_PixResol,
                  pixelX: HeaderContents[24].ImgHdr_PixX,
                  pixelY: HeaderContents[25].ImgHdr_PixY,
                  numRec: HeaderContents[89].TTResult_NumberOfRecords,
                  filename: HeaderContents[19].$Filename,
                  bitsPerRecord: HeaderContents[93].TTResultFormat_BitsPerRecord,
                  recType: HeaderContents[92].TTResultFormat_TTTRRecType,
                  syncRate: HeaderContents[83].TTResult_SyncRate
            };



            // Checking if image is square, otherwise the rest of the code won't work

            if (FLIMInfo.pixelX != FLIMInfo.pixelY) {
                  throw "Image not square. Abort."
            }


            // Decoding the TTTR records in the file
            /*A record is 4 byte = 32 bit long and, in the case of HydraHarp2T3 data, contains the following components:
             - special: 1 bit, if clear: regular record, if >= 1 its a special record: overflow or external marker
             - channel: 6 bits, either encodes channel ID of the photon event, or, if special is set, encodes which special case occured: if 111111 ( = 63), an overflow occured, 1 to 15 are (external) markers, such as line / frame start / stop (see header file)
             - dtime: 15 bits
             - nsync: 10 bits
            
             To recover the global arival time of a photon or marker in seconds, count overflows until the current position and multiply with overflow period (1024 for HydraHarp2T3). Then add nsync and multiply with MeasDesc_GlobalResolution (for T3, slightly different for T2!)
            */



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
            let macrotime = new Array(FLIMInfo.numRec);
            let nanotime = new Array(FLIMInfo.numRec);
            let markers = new Array(FLIMInfo.numRec);
            const overflow_period = 1024;
            let overflowCorr = 0;
            let truensync = 0;
            let macroMultFactor = FLIMInfo.globRes // Multiply with truensync to get real experiment time in seconds
            let nanoMultFactor = FLIMInfo.measRes * 1e9;
            const bytesToFileEnd = data.byteLength - 4;
            let i = 0; // Counts

            // need to add 3 for some reason; bytes and bits seem to be out of order after the header; not much valuable photon data at the beginning of the file anyway; I hope this is not different for other files
            offset += 0;

            while (offset <= bytesToFileEnd) {
                  let recordBytes = data.slice(offset, offset + 4).reverse(); // Endianess change here; buffer has to be reversed! Took me 5 hours to find out!!!
                  let recordBits = bitwise.buffer.read(recordBytes);

                  let special = parseInt(recordBits.slice(0, 1), 2);
                  let channel = parseInt(recordBits.slice(1, 7).join(""), 2);
                  let dtime = parseInt(recordBits.slice(7, 22).join(""), 2);
                  let nsync = parseInt(recordBits.slice(22, 33).join(""), 2);
                  //let channel = parseInt(recordBits.slice(1, 7).toString().replace(/\,/g, ""), 2);

                  if (special == 1) {
                        if (channel == 63) {
                              if (nsync == 0) {
                                    overflowCorr += overflow_period;
                              } else {
                                    overflowCorr += (overflow_period * nsync);
                              }
                        }
                        if (channel >= 1 & channel <= 15) {
                              truensync = overflowCorr + nsync;
                              // line start = 1 (from channel) + 5 -> 6; line stop = 2 (from channel) + 5 = 7; otherwise photon events could not be distinguished from marker events (in this code setup)
                              channel += 5;
                        }
                  }
                  else {
                        truensync = overflowCorr + nsync;
                  }

                  macrotime[i] = truensync * macroMultFactor;
                  markers[i] = channel;
                  nanotime[i] = dtime * nanoMultFactor;

                  offset += 4; // Incrementing offset counter to move on
                  i += 1;


                  if (offset % 25000 == 0) {
                        ipc.send("loading-ptu-progress", (offset / bytesToFileEnd));
                  }
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

            ipc.send("loading-ptu-finished");

            return (recordData);
      }
};