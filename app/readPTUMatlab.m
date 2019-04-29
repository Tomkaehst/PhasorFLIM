function [output, txtout]=Read_PTU_V1(filepath) % Read PicoQuant Unified TTTR Files
% Written by Omri Bar-Elli and Ron Tenne using a demo code from PicoQuant.
% this version works ~100x faster than the demo.
% Last update: 14.2.17
% this function reads a PTU file created by a HydraHarp and converts it to
% a matlab structure called output
% -- these are comments from the demo version.
% This is demo code. Use at your own risk. No warranties.
% Marcus Sackrow, PicoQUant GmbH, December 2013
% Note that marker events have a lower time resolution and may therefore appear 
% in the file slightly out of order with respect to regular (photon) event records.
% This is by design. Markers are designed only for relatively coarse 
% synchronization requirements such as image scanning. 
% T Mode data are written to an output file [filename].out 
% We do not keep it in memory because of the huge amout of memory
% this would take in case of large files. Of course you can change this, 
% e.g. if your files are not too big. 
% Otherwise it is best process the data on the fly and keep only the results.
% All HeaderData are introduced as Variable to Matlab and can directly be
% used for further analysis
    % Headers to save as fields in the output struct, all headers are
    % saved but some are more usful so add them to this list.
    Head_save={'TTResult_SyncRate';
               'MeasDesc_Resolution';
               'File_CreatingTime';
               'HWSync_Divider';
               'TTResult_StopAfter'};
    txtout=cell(5,1);
    % some constants
    tyEmpty8      = hex2dec('FFFF0008');
    tyBool8       = hex2dec('00000008');
    tyInt8        = hex2dec('10000008');
    tyBitSet64    = hex2dec('11000008');
    tyColor8      = hex2dec('12000008');
    tyFloat8      = hex2dec('20000008');
    tyTDateTime   = hex2dec('21000008');
    tyFloat8Array = hex2dec('2001FFFF');
    tyAnsiString  = hex2dec('4001FFFF');
    tyWideString  = hex2dec('4002FFFF');
    tyBinaryBlob  = hex2dec('FFFFFFFF');
    
    % RecordTypes
    rtHydraHarpT3    = hex2dec('00010304');% (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $03 (T3), HW: $04 (HydraHarp)
    rtHydraHarp2T3   = hex2dec('01010304');% (SubID = $01 ,RecFmt: $01) (V2), T-Mode: $03 (T3), HW: $04 (HydraHarp)
    
    TTResultFormat_TTTRRecType = 0;
    % start Main program
%     [filename, pathname]=uigetfile('*.ptu', 'T-Mode data:');
    fid=fopen(filepath);
    
    Magic = fread(fid, 8, '*char');
    if not(strcmp(Magic(Magic~=0)','PQTTTR'))
        error('Magic invalid, this is not an PTU file.');
    end;
    Version = fread(fid, 8, '*char');
    txtout{1}=sprintf('Tag Version: %s', Version);
    j=0;
    while 1 % read all headears
        j=j+1;
        % read Tag Head
        TagIdent = fread(fid, 32, '*char');    % TagHead.Ident
        TagIdent = (TagIdent(TagIdent ~= 0))'; % remove #0 and more more readable
        TagIdx = fread(fid, 1, 'int32');       % TagHead.Idx
        TagTyp = fread(fid, 1, 'uint32');      % TagHead.Typ
                                               % TagHead.Value will be read in the
                                               % right type function  
        if TagIdx > -1
          EvalName = [TagIdent '(' int2str(TagIdx + 1) ')'];
        else
          EvalName = TagIdent;
        end
        output.Headers{j,1}=EvalName;
        % check Typ of Header
        switch TagTyp
            case tyEmpty8
                fread(fid, 1, 'int64');   
                output.Headers{j,2}='<Empty>';
            case tyBool8
                TagInt = fread(fid, 1, 'int64');
                if TagInt==0
                    output.Headers{j,2}='FALSE';
                    eval([EvalName '=false;']);
                else
                    output.Headers{j,2}='TRUE';
                    eval([EvalName '=true;']);
                end            
            case tyInt8
                TagInt = fread(fid, 1, 'int64');
                output.Headers{j,2}=TagInt;
                eval([EvalName '=TagInt;']);
            case tyBitSet64
                TagInt = fread(fid, 1, 'int64');
                output.Headers{j,2}=TagInt;
                eval([EvalName '=TagInt;']);
            case tyColor8    
                TagInt = fread(fid, 1, 'int64');
                output.Headers{j,2}=TagInt;
                eval([EvalName '=TagInt;']);
            case tyFloat8
                TagFloat = fread(fid, 1, 'double');
                output.Headers{j,2}=TagFloat;
                eval([EvalName '=TagFloat;']);
            case tyFloat8Array
                TagInt = fread(fid, 1, 'int64');
                output.Headers{j,2}=['<Float array with %d Entries>', TagInt / 8];
                fseek(fid, TagInt, 'cof');
            case tyTDateTime
                TagFloat = fread(fid, 1, 'double');
                output.Headers{j,2}=datestr(datenum(1899,12,30)+TagFloat);
                eval([EvalName '=datenum(1899,12,30)+TagFloat;']); % but keep in memory as Matlab Date Number
            case tyAnsiString
                TagInt = fread(fid, 1, 'int64');
                TagString = fread(fid, TagInt, '*char');
                TagString = (TagString(TagString ~= 0))';
                output.Headers{j,2}=TagString;
                if TagIdx > -1
                   EvalName = [TagIdent '(' int2str(TagIdx + 1) ',:)'];
                end;   
                eval([EvalName '=TagString;']);
            case tyWideString 
                % Matlab does not support Widestrings at all, just read and
                % remove the 0's (up to current (2012))
                TagInt = fread(fid, 1, 'int64');
                TagString = fread(fid, TagInt, '*char');
                TagString = (TagString(TagString ~= 0))';
                output.Headers{j,2}=TagString;
                if TagIdx > -1
                   EvalName = [TagIdent '(' int2str(TagIdx + 1) ',:)'];
                end;
                eval([EvalName '=TagString;']);
            case tyBinaryBlob
                TagInt = fread(fid, 1, 'int64');
                output.Headers{j,2}=['<Binary Blob with %d Bytes>', TagInt];
                fseek(fid, TagInt, 'cof');    
            otherwise
                error('Illegal Type identifier found! Broken file?');
        end;
        if strcmp(TagIdent, 'Header_End')
            break
        end
    end
    
    % choose right decode function
    switch TTResultFormat_TTTRRecType
        case rtHydraHarpT3
            txtout{2}=sprintf('HydraHarp V1 T3 data');
            [output, cnt_ph, cnt_ov, cnt_ma] = ReadHT3(fid,1,output);
        case rtHydraHarp2T3
            txtout{2}=sprintf('HydraHarp V2 T3 data');
            [output, cnt_ph, cnt_ov, cnt_ma] = ReadHT3(fid,2,output);
        otherwise
            error('Illegal RecordType!');
    end;
    fclose(fid);
    
    % this takes the important headers (defined at the beginning of the
    % function) and puts them directly in the output structure.
    output.Headers(:,1) = strrep(output.Headers(:,1),'(','_');
    output.Headers(:,1) = strrep(output.Headers(:,1),')','');
    output.Headers=cell2struct(output.Headers(:,2),output.Headers(:,1),1);
    for i=1:length(Head_save)
       output.(Head_save{i}) = output.Headers.(Head_save{i});
    end
    
    %convert uint32 to double
    output.ph_sync=double(output.ph_sync);
    output.ph_dtime=double(output.ph_dtime);
    output.mark_dtime=double(output.mark_dtime);
    output.mark_sync=double(output.mark_sync);
    
    txtout{3}=sprintf('Statistics obtained from the data:');
    txtout{4}=sprintf('%i photons, %i overflows, %i markers.',cnt_ph, cnt_ov, cnt_ma);
end
%% Decoder functions
% Read HydraHarp/TimeHarp260 T3
function [output, cnt_ph, cnt_ov, cnt_ma]=ReadHT3(fid,Version,output)
    T3WRAPAROUND = 1024;
    T3Record = fread(fid, inf, 'uint32=>uint32', 'ieee-le');
    %   +-------------------------------+  +-------------------------------+
    %   |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|
    %   +-------------------------------+  +-------------------------------+
    nsync = mod(T3Record,2^10); % last 10 bits
    % this is 2 things:
    % a: for an overflow it's how many overflows since last
    % photon/marker
    % b: for photon/marker it's how many syncs since last overflow
    %   +-------------------------------+  +-------------------------------+
    %   | | | | | | | | | | | | | | | | |  | | | | | | |x|x|x|x|x|x|x|x|x|x|
    %   +-------------------------------+  +-------------------------------+
    dtime=mod(idivide(T3Record,2^10),2^15); % next 15 bits
    %   the dtime unit depends on "Resolution" that can be obtained from header
    %   DTime: Arrival time (units) of Photon after last Sync event
    %   DTime * Resolution = Real time arrival of Photon after last Sync event
    %   +-------------------------------+  +-------------------------------+
    %   | | | | | | | |x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x| | | | | | | | | | |
    %   +-------------------------------+  +-------------------------------+
    channel=mod(idivide(T3Record,2^25),2^6); % next 6 bits
    %   +-------------------------------+  +-------------------------------+
    %   | |x|x|x|x|x|x| | | | | | | | | |  | | | | | | | | | | | | | | | | |
    %   +-------------------------------+  +-------------------------------+
    
    special=idivide(T3Record,2^31); % first bit
    %   +-------------------------------+  +-------------------------------+
    %   |x| | | | | | | | | | | | | | | |  | | | | | | | | | | | | | | | | |
    %   +-------------------------------+  +-------------------------------+
    
    if Version == 1
        % empty for now, may be adapted for old files
        
    else
        % overflow is known by channel 63
        % for some reason nsync might be 0 even for an overflow (due to
        % old versions or something). in these cases the overflow is
        % eaual to 1.
        
        nsync2=nsync; % make a copy since we need the original nsync later.
        
        % Change all the 0 in nsync2 but only when there is an
        % overflow:
        nsync2(channel==63 & ~nsync)=1;
        
        % calculate the actual overflow:
        Overflow = T3WRAPAROUND * nsync2 .*uint32(channel==63);
        
        % create vector of the actual overflow for each entry:
        OverflowCorrection = cumsum(double(Overflow));
        
        % how many overflows in the file:
        cnt_ov = max(OverflowCorrection)/T3WRAPAROUND;
    end
    
    % calculate the actual sync of photons (special=0)
    % one nsync time unit equals to "syncperiod" which can be
    % calculated from "SyncRate"
    output.ph_sync = OverflowCorrection(special==0) + double( nsync(special==0) );
    
    % arrival bin of photons after sync
    output.ph_dtime = dtime(special==0);
    
    % channel of photons
    output.ph_channel = channel(special==0);
    
    cnt_ph = length(output.ph_dtime);
    
    % calculate the actual sync of markers
    % Markers: Bitfield of arrived Markers, different markers can arrive at same time (same record)
    output.mark_sync = OverflowCorrection(special==1 & channel>=1 & channel<=15) + double( nsync(special==1 & channel>=1 & channel<=15) );
    output.mark_chan = channel(special==1 & ~(channel==63));
    output.mark_dtime = dtime(special==1 & ~(channel==63));
    cnt_ma=length(output.mark_chan);
end