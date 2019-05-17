

const fs = require("fs");
const stream = require("stream");

let filepath = "./Convalaria_for_CC_6_1.ptu";




function openPTUStream(filepath) {
      const inputStream = new stream.Readable({
            objectMode: false
      });
      inputStream._read = () => { };


      var headerOffset;
      var gotHeader = false;
      var readingRecords = false;

      const fileInputStream = fs.createReadStream(filepath);

      fileInputStream.on("data", (chunk) => {

      });

      return (inputStream);
};

openPTUStream(filepath)
      .pipe(process.stdout)