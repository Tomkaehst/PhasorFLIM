
const fs = require("fs");

module.exports = {

      readHeader: function (filePath, callback) {
            var dataStreamHeader = fs.createReadStream(filePath);
            var header, headerOffset, output;

            dataStreamHeader
                  .on("data", (chunk) => {
                        console.log("Starting header reading stream ... \n");
                        headerOffset = chunk.indexOf("Header_End") + 48;
                        if (headerOffset != -1) {
                              if (this.checkFileValidity(chunk.slice(0, 16)) != true) {
                                    dataStreamHeader.close();
                                    throw "Not a valid .ptu file!"
                              } else {
                                    header = this.decodeHeader(chunk.slice(16, headerOffset + 48));
                                    dataStreamHeader.close();
                              }
                        };
                  })
                  .on("error", (err) => {
                        throw err;
                  })
                  .on("close", () => {
                        console.log("\nClosing header reading stream ...\n")
                        output = {
                              header: header,
                              headerOffset: headerOffset
                        };
                        callback(output);
                  })

            return (output);

      },

      logHeader: function (header) {
            console.log(header);
      },

      checkFileValidity: function (buff) {
            let magic = buff.slice(0, 6).toString("utf8");
            let version = buff.slice(8, 14).toString();

            if (magic == "PQTTTR") {
                  return (true);
            } else {
                  return (false);
            };
      },

      decodeHeader: function (buff) {

            let data = buff;
            let offset = 0;

            // Header Tag Type definition
            let tagTypes = {
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


            let tag_HeaderEnd = "Header_End"; // Last Entry of the Header; terminates reading loop
            let reachedHeaderEnd = false;
            let entry = NaN; // empty variable to assign the tag entry to 

            let HeaderContents = {};

            /* Header Decoding loop */

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
                  numRec: HeaderContents.TTResult_NumberOfRecords
            };

            return (FLIMInfo);
      }
};